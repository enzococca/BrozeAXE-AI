"""
RAG (Retrieval-Augmented Generation) Search System
===================================================

Provides semantic search over cached AI interpretations and analysis results.
Uses TF-IDF for vector search with optional Anthropic re-ranking.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
               min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Search for documents matching the query.

        Args:
            query: Search query (natural language)
            top_k: Maximum number of results
            min_score: Minimum similarity score (0-1)

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

            logger.debug(f"RAG: Query '{query[:50]}...' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"RAG: Search failed: {e}")
            return []

    def generate_answer(self, query: str, results: List[Dict[str, Any]],
                       anthropic_client=None) -> Optional[str]:
        """
        Generate a natural language answer based on search results.

        Args:
            query: Original query
            results: Search results
            anthropic_client: Optional Anthropic client for AI generation

        Returns:
            Generated answer or None
        """
        if not results:
            return None

        # Build context from top results
        context_parts = []
        for i, result in enumerate(results[:5], 1):
            if result['type'] == 'ai_cache':
                content = result.get('content', '')
                if isinstance(content, dict):
                    content = json.dumps(content, ensure_ascii=False, indent=2)[:500]
                elif isinstance(content, str):
                    content = content[:500]
                context_parts.append(
                    f"[{i}] {result['artifact_id']} ({result['cache_type']}): {content}"
                )
            elif result['type'] == 'comparison':
                context_parts.append(
                    f"[{i}] Comparazione {result['artifact1_id']} ↔ {result['artifact2_id']}: "
                    f"Similarità {result['similarity_score']*100:.1f}%"
                )

        context = '\n\n'.join(context_parts)

        # If no Anthropic client, return formatted context
        if not anthropic_client:
            return f"Risultati trovati per '{query}':\n\n{context}"

        # Generate AI answer
        try:
            prompt = f"""Basandoti sui seguenti dati archeologici cached, rispondi alla domanda dell'utente in modo conciso e informativo.

DOMANDA: {query}

DATI DISPONIBILI:
{context}

Rispondi in italiano, citando gli artefatti specifici quando rilevante. Se i dati non sono sufficienti per rispondere, indicalo."""

            response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"RAG: AI answer generation failed: {e}")
            return f"Risultati trovati per '{query}':\n\n{context}"

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
