"""
RAG (Retrieval-Augmented Generation) Search System
===================================================

Provides semantic search over cached AI interpretations and analysis results.
Uses TF-IDF for vector search with optional Anthropic re-ranking.
Features connection resilience with automatic retry on network errors.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from acs.core.resilient_ai import (
    ResilientAnthropicClient,
    RetryConfig,
    get_resilient_client
)

logger = logging.getLogger(__name__)


class RAGSearchEngine:
    """
    Semantic search engine for archaeological analysis cache.

    Uses TF-IDF vectorization for efficient similarity search,
    with optional AI-powered re-ranking and answer generation.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words=None,  # Keep Italian/English terms
            ngram_range=(1, 2),  # Unigrams and bigrams
            min_df=1,
            max_df=0.95
        )
        self.documents: List[Dict[str, Any]] = []
        self.document_vectors = None
        self.is_indexed = False
        self._last_index_time = None

    def _extract_text(self, item: Dict[str, Any]) -> str:
        """Extract searchable text from a cache item."""
        parts = []

        # Add artifact ID
        if 'artifact_id' in item:
            parts.append(f"artefatto {item['artifact_id']}")

        # Add cache type
        if 'cache_type' in item:
            type_labels = {
                'savignano_interpretation': 'interpretazione savignano analisi',
                'tech_analysis': 'analisi tecnologica',
                'hammering_analysis': 'analisi martellatura',
                'casting_analysis': 'analisi fusione',
                'comprehensive_report': 'report comprensivo completo',
                'pca_analysis': 'analisi PCA componenti principali',
                'clustering_analysis': 'clustering raggruppamento cluster'
            }
            parts.append(type_labels.get(item['cache_type'], item['cache_type']))

        # Add content
        content = item.get('content', '')
        if isinstance(content, dict):
            # Flatten dict to text
            for key, value in content.items():
                if isinstance(value, str):
                    parts.append(f"{key}: {value}")
                elif isinstance(value, (int, float)):
                    parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    parts.append(f"{key}: {', '.join(str(v) for v in value[:10])}")
        elif isinstance(content, str):
            parts.append(content)

        return ' '.join(parts)

    def index_documents(self, cache_items: List[Dict[str, Any]],
                       comparisons: List[Dict[str, Any]] = None):
        """
        Index documents for search.

        Args:
            cache_items: List of AI cache entries
            comparisons: List of comparison entries
        """
        self.documents = []
        texts = []

        # Index AI cache items
        for item in cache_items:
            text = self._extract_text(item)
            if text.strip():
                self.documents.append({
                    'type': 'ai_cache',
                    'artifact_id': item.get('artifact_id', ''),
                    'cache_type': item.get('cache_type', ''),
                    'content': item.get('content', ''),
                    'date': item.get('created_date', ''),
                    'text': text
                })
                texts.append(text)

        # Index comparisons
        if comparisons:
            for comp in comparisons:
                text = f"comparazione {comp.get('artifact1_id', '')} {comp.get('artifact2_id', '')} similarità {comp.get('similarity_score', 0) * 100:.1f}%"
                self.documents.append({
                    'type': 'comparison',
                    'artifact1_id': comp.get('artifact1_id', ''),
                    'artifact2_id': comp.get('artifact2_id', ''),
                    'similarity_score': comp.get('similarity_score', 0),
                    'date': comp.get('comparison_date', ''),
                    'text': text
                })
                texts.append(text)

        if texts:
            try:
                self.document_vectors = self.vectorizer.fit_transform(texts)
                self.is_indexed = True
                self._last_index_time = datetime.now()
                logger.info(f"RAG: Indexed {len(texts)} documents")
            except Exception as e:
                logger.error(f"RAG: Indexing failed: {e}")
                self.is_indexed = False
        else:
            self.is_indexed = False
            logger.warning("RAG: No documents to index")

    def search(self, query: str, top_k: int = 10,
               min_score: float = 0.01) -> List[Dict[str, Any]]:
        """
        Search for documents matching the query.

        Args:
            query: Search query (natural language)
            top_k: Maximum number of results
            min_score: Minimum similarity score (0-1). Default lowered to 0.01
                       because TF-IDF with sparse vectors produces low scores.

        Returns:
            List of matching documents with scores
        """
        if not self.is_indexed or not self.documents:
            return []

        try:
            # Vectorize query
            query_vector = self.vectorizer.transform([query])

            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.document_vectors)[0]

            # Get top results
            top_indices = np.argsort(similarities)[::-1][:top_k * 2]  # Get extra for filtering

            # Debug: log top similarity scores
            top_scores = [(int(idx), float(similarities[idx])) for idx in top_indices[:5]]
            logger.debug(f"RAG: Top 5 similarities for '{query[:30]}': {top_scores}")

            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score >= min_score:
                    doc = self.documents[idx].copy()
                    doc['score'] = score
                    doc['score_pct'] = f"{score * 100:.1f}%"
                    results.append(doc)

                    if len(results) >= top_k:
                        break

            # Fallback: if no results with threshold, return top results anyway with warning
            if not results and len(top_indices) > 0:
                # Get top results regardless of threshold
                for idx in top_indices[:min(3, top_k)]:
                    score = float(similarities[idx])
                    if score > 0:  # Only include if there's any similarity
                        doc = self.documents[idx].copy()
                        doc['score'] = score
                        doc['score_pct'] = f"{score * 100:.1f}%"
                        doc['low_confidence'] = True
                        results.append(doc)
                if results:
                    logger.info(f"RAG: Low confidence results for '{query[:30]}' (best score: {results[0]['score']:.4f})")

            logger.debug(f"RAG: Query '{query[:50]}...' returned {len(results)} results (threshold: {min_score})")
            return results

        except Exception as e:
            logger.error(f"RAG: Search failed: {e}")
            return []

    def generate_answer(self, query: str, results: List[Dict[str, Any]],
                       anthropic_client=None) -> Optional[Dict[str, Any]]:
        """
        Generate a structured, discursive answer based on search results.
        Uses resilient client with automatic retry on connection errors.

        Args:
            query: Original query
            results: Search results
            anthropic_client: Optional Anthropic client for AI generation (can be raw or resilient)

        Returns:
            Dict with answer, structured sections, and optional visualization suggestions
        """
        if not results:
            return None

        # Build context from top results
        context_parts = []
        for i, result in enumerate(results[:5], 1):
            if result['type'] == 'ai_cache':
                content = result.get('content', '')
                if isinstance(content, dict):
                    content = json.dumps(content, ensure_ascii=False, indent=2)[:1500]
                elif isinstance(content, str):
                    content = content[:1500]
                context_parts.append(
                    f"[Documento {i}] Artefatto: {result['artifact_id']}\n"
                    f"Tipo analisi: {result['cache_type']}\n"
                    f"Contenuto: {content}"
                )
            elif result['type'] == 'comparison':
                context_parts.append(
                    f"[Documento {i}] Comparazione: {result['artifact1_id']} ↔ {result['artifact2_id']}\n"
                    f"Similarità: {result['similarity_score']*100:.1f}%"
                )

        context = '\n\n---\n\n'.join(context_parts)

        # If no Anthropic client, return basic formatted response
        if not anthropic_client:
            return {
                'answer': f"Risultati trovati per '{query}':\n\n{context}",
                'sections': [],
                'needs_visualization': False,
                'visualization_type': None
            }

        # Generate structured AI answer with temperature 0.1 for factual responses
        try:
            prompt = f"""Sei un esperto archeologo specializzato in analisi di artefatti dell'Età del Bronzo.
Basandoti sui dati archeologici forniti, rispondi alla domanda dell'utente in modo STRUTTURATO e DISCORSIVO.

DOMANDA DELL'UTENTE: {query}

DATI DISPONIBILI DAL DATABASE:
{context}

ISTRUZIONI PER LA RISPOSTA:
1. Fornisci una risposta STRUTTURATA con sezioni chiare
2. Sii DISCORSIVO e ESPLICATIVO - non limitarti a elencare dati, ma spiegali
3. Cita sempre gli artefatti specifici (es. SAV_001, SAV_002) quando rilevante
4. Usa un linguaggio tecnico ma accessibile
5. Se i dati non sono sufficienti, indicalo chiaramente
6. Aggiungi interpretazioni archeologiche quando possibile

FORMATO RISPOSTA (JSON):
{{
    "sintesi": "Breve sintesi della risposta (2-3 frasi)",
    "risposta_dettagliata": "Risposta completa e discorsiva con spiegazioni approfondite",
    "punti_chiave": ["punto 1", "punto 2", ...],
    "artefatti_citati": ["SAV_001", "SAV_002", ...],
    "suggerimento_visualizzazione": {{
        "necessaria": true/false,
        "tipo": "grafico_comparativo|tabella|dendrogramma|pca|istogramma|nessuno",
        "descrizione": "Descrizione di cosa mostrerebbe la visualizzazione"
    }},
    "nota_metodologica": "Eventuale nota sulla metodologia o limiti dei dati"
}}

Rispondi SOLO con il JSON valido, senza altro testo."""

            # Use resilient client if available, otherwise use raw client
            if isinstance(anthropic_client, ResilientAnthropicClient):
                response = anthropic_client.create_message(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
            else:
                # Try to use resilient wrapper for raw client
                try:
                    resilient = get_resilient_client()
                    response = resilient.create_message(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2000,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                except Exception:
                    # Fallback to raw client if resilient fails
                    response = anthropic_client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2000,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )

            response_text = response.content[0].text.strip()

            # Try to parse JSON response
            try:
                # Clean potential markdown code blocks
                if response_text.startswith('```'):
                    response_text = response_text.split('```')[1]
                    if response_text.startswith('json'):
                        response_text = response_text[4:]
                    response_text = response_text.strip()

                parsed = json.loads(response_text)

                # Build formatted answer
                formatted_answer = f"## Sintesi\n{parsed.get('sintesi', '')}\n\n"
                formatted_answer += f"## Analisi Dettagliata\n{parsed.get('risposta_dettagliata', '')}\n\n"

                punti = parsed.get('punti_chiave', [])
                if punti:
                    formatted_answer += "## Punti Chiave\n"
                    for punto in punti:
                        formatted_answer += f"• {punto}\n"
                    formatted_answer += "\n"

                artefatti = parsed.get('artefatti_citati', [])
                if artefatti:
                    formatted_answer += f"## Artefatti Analizzati\n{', '.join(artefatti)}\n\n"

                nota = parsed.get('nota_metodologica', '')
                if nota:
                    formatted_answer += f"## Nota Metodologica\n_{nota}_\n"

                viz = parsed.get('suggerimento_visualizzazione', {})

                return {
                    'answer': formatted_answer,
                    'sections': {
                        'sintesi': parsed.get('sintesi', ''),
                        'dettaglio': parsed.get('risposta_dettagliata', ''),
                        'punti_chiave': punti,
                        'artefatti': artefatti,
                        'nota': nota
                    },
                    'needs_visualization': viz.get('necessaria', False),
                    'visualization_type': viz.get('tipo', 'nessuno'),
                    'visualization_description': viz.get('descrizione', '')
                }

            except json.JSONDecodeError:
                # If JSON parsing fails, return raw response
                return {
                    'answer': response_text,
                    'sections': {},
                    'needs_visualization': False,
                    'visualization_type': None
                }

        except Exception as e:
            logger.error(f"RAG: AI answer generation failed: {e}")
            return {
                'answer': f"Risultati trovati per '{query}':\n\n{context}",
                'sections': {},
                'needs_visualization': False,
                'visualization_type': None,
                'error': str(e)
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return {
            'is_indexed': self.is_indexed,
            'document_count': len(self.documents),
            'last_index_time': self._last_index_time.isoformat() if self._last_index_time else None,
            'vocabulary_size': len(self.vectorizer.vocabulary_) if self.is_indexed else 0
        }


# Global instance
_rag_engine: Optional[RAGSearchEngine] = None


def get_rag_engine() -> RAGSearchEngine:
    """Get or create the global RAG engine instance."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGSearchEngine()
    return _rag_engine
