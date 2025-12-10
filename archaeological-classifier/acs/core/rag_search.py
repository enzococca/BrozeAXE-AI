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

        # Add cache type with expanded labels for better search
        if 'cache_type' in item:
            type_labels = {
                'savignano_interpretation': 'interpretazione savignano analisi tipologia',
                'tech_analysis': 'analisi tecnologica produzione fabbricazione',
                'hammering_analysis': 'analisi martellatura lavorazione metallurgica',
                'casting_analysis': 'analisi fusione colata stampo matrice',
                'comprehensive_report': 'report comprensivo completo sommario',
                'pca_analysis': 'analisi PCA componenti principali morfometria varianza',
                'clustering_analysis': 'clustering raggruppamento cluster dendrogramma gruppi simili'
            }
            parts.append(type_labels.get(item['cache_type'], item['cache_type']))

        # Add content with enhanced extraction
        content = item.get('content', '')
        if isinstance(content, dict):
            # Flatten dict to text with better formatting
            parts.extend(self._extract_dict_text(content))
        elif isinstance(content, str):
            parts.append(content)

        return ' '.join(parts)

    def _extract_dict_text(self, d: Dict[str, Any], prefix: str = '') -> List[str]:
        """Recursively extract text from nested dictionaries."""
        parts = []
        for key, value in d.items():
            full_key = f"{prefix}{key}" if prefix else key

            if isinstance(value, str):
                parts.append(f"{full_key}: {value}")
            elif isinstance(value, (int, float)):
                # Add measurement context for numeric values
                parts.append(f"{full_key}: {value}")
                # Add unit hints for common measurements
                if any(k in key.lower() for k in ['volume', 'area', 'length', 'width', 'height', 'depth']):
                    parts.append(f"misura {key} {value}")
                if any(k in key.lower() for k in ['angle', 'angolo']):
                    parts.append(f"angolo {value} gradi")
            elif isinstance(value, list):
                if value and isinstance(value[0], (int, float)):
                    # Numeric array (PCA components, cluster assignments, etc.)
                    parts.append(f"{full_key}: {', '.join(str(v) for v in value[:10])}")
                elif value and isinstance(value[0], str):
                    parts.append(f"{full_key}: {', '.join(value[:10])}")
                elif value and isinstance(value[0], dict):
                    # List of objects (like cluster members)
                    for i, item in enumerate(value[:5]):
                        parts.extend(self._extract_dict_text(item, f"{full_key}[{i}]."))
            elif isinstance(value, dict):
                parts.extend(self._extract_dict_text(value, f"{full_key}."))
        return parts

    def _extract_features_text(self, artifact_id: str, features: Dict[str, Any]) -> str:
        """Extract searchable text from morphometric features."""
        parts = [f"artefatto {artifact_id} misure morfometriche 3D mesh"]

        # Common feature labels
        feature_labels = {
            'volume': 'volume mm3 millimetri cubi',
            'surface_area': 'superficie area mm2 millimetri quadrati',
            'length': 'lunghezza mm',
            'width': 'larghezza mm',
            'height': 'altezza mm',
            'depth': 'profondità mm',
            'n_vertices': 'vertici mesh 3D',
            'n_faces': 'facce triangoli mesh 3D',
            'centroid': 'centroide baricentro',
            'bounding_box': 'bounding box dimensioni',
            'edge_angle': 'angolo lama taglio',
            'socket_depth': 'profondità immanicatura',
            'is_watertight': 'mesh chiuso watertight',
        }

        for key, value in features.items():
            if isinstance(value, (int, float)):
                label = feature_labels.get(key, key)
                parts.append(f"{label}: {value}")
            elif isinstance(value, dict):
                # Nested features (e.g., savignano features)
                parts.extend(self._extract_dict_text(value, f"{key}."))

        return ' '.join(parts)

    def _extract_analysis_text(self, analysis: Dict[str, Any]) -> str:
        """Extract searchable text from PCA/clustering analysis results."""
        parts = []

        analysis_type = analysis.get('analysis_type', '')
        if 'pca' in analysis_type.lower():
            parts.append('analisi PCA componenti principali varianza spiegata morfometria')
        elif 'cluster' in analysis_type.lower():
            parts.append('clustering raggruppamento cluster dendrogramma gruppi matrici')

        # Extract artifact IDs
        artifact_ids = analysis.get('artifact_ids', [])
        if artifact_ids:
            parts.append(f"artefatti analizzati: {', '.join(artifact_ids[:20])}")

        # Extract results
        results = analysis.get('results', {})
        if isinstance(results, dict):
            parts.extend(self._extract_dict_text(results))
        elif isinstance(results, str):
            parts.append(results)

        return ' '.join(parts)

    def _format_features_for_context(self, features: Dict[str, Any]) -> str:
        """Format features for human-readable context in AI prompts."""
        parts = []

        # Mapping for human-readable labels
        labels = {
            'volume': 'Volume',
            'surface_area': 'Area superficiale',
            'length': 'Lunghezza',
            'width': 'Larghezza',
            'height': 'Altezza',
            'depth': 'Profondità',
            'edge_angle': 'Angolo lama',
            'socket_depth': 'Profondità immanicatura',
            'n_vertices': 'Vertici',
            'n_faces': 'Facce',
        }

        for key, value in features.items():
            if isinstance(value, (int, float)):
                label = labels.get(key, key)
                if isinstance(value, float):
                    parts.append(f"{label}: {value:.2f}")
                else:
                    parts.append(f"{label}: {value}")
            elif isinstance(value, dict) and key == 'savignano':
                # Special handling for Savignano typology features
                sav_parts = []
                for skey, sval in value.items():
                    if isinstance(sval, (int, float)):
                        sav_parts.append(f"{skey}: {sval:.2f}" if isinstance(sval, float) else f"{skey}: {sval}")
                if sav_parts:
                    parts.append(f"Tipologia Savignano: {', '.join(sav_parts)}")

        return ', '.join(parts) if parts else 'N/A'

    def index_documents(self, cache_items: List[Dict[str, Any]],
                       comparisons: List[Dict[str, Any]] = None,
                       features: Dict[str, Dict[str, Any]] = None,
                       analysis_results: List[Dict[str, Any]] = None,
                       artifacts: List[Dict[str, Any]] = None):
        """
        Index documents for search.

        Args:
            cache_items: List of AI cache entries
            comparisons: List of comparison entries
            features: Dict mapping artifact_id to features
            analysis_results: List of PCA/clustering analysis results
            artifacts: List of artifact records (with 3D mesh info)
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

        # Index morphometric features (3D measurements)
        if features:
            for artifact_id, feature_data in features.items():
                text = self._extract_features_text(artifact_id, feature_data)
                if text.strip():
                    self.documents.append({
                        'type': 'features',
                        'artifact_id': artifact_id,
                        'features': feature_data,
                        'text': text
                    })
                    texts.append(text)

        # Index analysis results (PCA, clustering)
        if analysis_results:
            for analysis in analysis_results:
                text = self._extract_analysis_text(analysis)
                if text.strip():
                    self.documents.append({
                        'type': 'analysis',
                        'analysis_type': analysis.get('analysis_type', ''),
                        'artifact_ids': analysis.get('artifact_ids', []),
                        'results': analysis.get('results', {}),
                        'date': analysis.get('analysis_date', ''),
                        'text': text
                    })
                    texts.append(text)

        # Index artifact metadata (3D mesh info)
        if artifacts:
            for artifact in artifacts:
                artifact_id = artifact.get('artifact_id', '')
                text = (
                    f"artefatto {artifact_id} "
                    f"mesh 3D file {artifact.get('mesh_path', '')} "
                    f"vertici {artifact.get('n_vertices', 0)} "
                    f"facce {artifact.get('n_faces', 0)} "
                    f"{'watertight chiuso' if artifact.get('is_watertight') else 'aperto'} "
                    f"caricato {artifact.get('upload_date', '')}"
                )
                self.documents.append({
                    'type': 'artifact',
                    'artifact_id': artifact_id,
                    'mesh_path': artifact.get('mesh_path', ''),
                    'n_vertices': artifact.get('n_vertices', 0),
                    'n_faces': artifact.get('n_faces', 0),
                    'is_watertight': artifact.get('is_watertight', False),
                    'date': artifact.get('upload_date', ''),
                    'text': text
                })
                texts.append(text)

        if texts:
            try:
                self.document_vectors = self.vectorizer.fit_transform(texts)
                self.is_indexed = True
                self._last_index_time = datetime.now()
                logger.info(f"RAG: Indexed {len(texts)} documents "
                           f"(cache: {len(cache_items)}, comparisons: {len(comparisons or [])}, "
                           f"features: {len(features or {})}, analyses: {len(analysis_results or [])}, "
                           f"artifacts: {len(artifacts or [])})")
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
        for i, result in enumerate(results[:7], 1):  # Increased to 7 for richer context
            doc_type = result.get('type', 'unknown')

            if doc_type == 'ai_cache':
                content = result.get('content', '')
                if isinstance(content, dict):
                    content = json.dumps(content, ensure_ascii=False, indent=2)[:1500]
                elif isinstance(content, str):
                    content = content[:1500]
                context_parts.append(
                    f"[Documento {i} - Interpretazione AI]\n"
                    f"Artefatto: {result['artifact_id']}\n"
                    f"Tipo analisi: {result['cache_type']}\n"
                    f"Contenuto: {content}"
                )
            elif doc_type == 'comparison':
                context_parts.append(
                    f"[Documento {i} - Confronto]\n"
                    f"Artefatti: {result['artifact1_id']} ↔ {result['artifact2_id']}\n"
                    f"Similarità: {result['similarity_score']*100:.1f}%"
                )
            elif doc_type == 'features':
                # Morphometric features
                features = result.get('features', {})
                feature_text = self._format_features_for_context(features)
                context_parts.append(
                    f"[Documento {i} - Misure Morfometriche 3D]\n"
                    f"Artefatto: {result['artifact_id']}\n"
                    f"Misure: {feature_text}"
                )
            elif doc_type == 'analysis':
                # PCA/Clustering results
                analysis_type = result.get('analysis_type', '')
                artifact_ids = result.get('artifact_ids', [])
                results_data = result.get('results', {})
                context_parts.append(
                    f"[Documento {i} - Analisi {analysis_type.upper()}]\n"
                    f"Artefatti analizzati: {', '.join(artifact_ids[:10])}\n"
                    f"Risultati: {json.dumps(results_data, ensure_ascii=False)[:800]}"
                )
            elif doc_type == 'artifact':
                # 3D mesh metadata
                context_parts.append(
                    f"[Documento {i} - Dati 3D Mesh]\n"
                    f"Artefatto: {result['artifact_id']}\n"
                    f"File: {result.get('mesh_path', 'N/A')}\n"
                    f"Vertici: {result.get('n_vertices', 0):,}, Facce: {result.get('n_faces', 0):,}\n"
                    f"Mesh chiuso: {'Sì' if result.get('is_watertight') else 'No'}"
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
