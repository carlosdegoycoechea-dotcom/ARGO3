"""
ARGO - Unified RAG Engine
Complete RAG implementation with project + library search
Includes: HyDE, reranking, semantic cache, library boost
"""
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import numpy as np

from langchain.schema import HumanMessage

from core.config import get_config
from core.logger import get_logger

logger = get_logger("RAGEngine")


@dataclass
class SearchResult:
    """Enhanced search result with full metadata"""
    content: str
    metadata: Dict
    score: float
    rerank_score: Optional[float] = None
    source_query: str = ""
    is_library: bool = False
    library_category: Optional[str] = None
    boost_factor: float = 1.0


class SemanticCache:
    """Semantic cache for search queries"""
    
    def __init__(self, embeddings, ttl_hours: int = 24, similarity_threshold: float = 0.95):
        self.cache = {}  # {hash: (results, timestamp, query)}
        self.embeddings = embeddings
        self.ttl = timedelta(hours=ttl_hours)
        self.threshold = similarity_threshold
        logger.debug(f"Semantic cache initialized (TTL: {ttl_hours}h, threshold: {similarity_threshold})")
    
    def _get_embedding_hash(self, text: str) -> str:
        """Generate hash from embedding"""
        try:
            emb = self.embeddings.embed_query(text)
            return hashlib.md5(str(emb[:10]).encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating embedding hash: {e}")
            return hashlib.md5(text.encode()).hexdigest()
    
    def _is_similar(self, query1: str, query2: str) -> bool:
        """Check if two queries are similar"""
        try:
            emb1 = self.embeddings.embed_query(query1)
            emb2 = self.embeddings.embed_query(query2)
            
            # Cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            return similarity >= self.threshold
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return False
    
    def get(self, query: str) -> Optional[List[SearchResult]]:
        """Get from cache if exists"""
        # Clean expired entries
        now = datetime.now()
        self.cache = {k: v for k, v in self.cache.items() 
                      if now - v[1] < self.ttl}
        
        # Find similar query
        for hash_key, (results, timestamp, cached_query) in self.cache.items():
            if self._is_similar(query, cached_query):
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return results
        
        return None
    
    def set(self, query: str, results: List[SearchResult]):
        """Store in cache"""
        hash_key = self._get_embedding_hash(query)
        self.cache[hash_key] = (results, datetime.now(), query)
        logger.debug(f"Cached {len(results)} results for query: {query[:50]}...")


class HyDE:
    """Hypothetical Document Embeddings"""
    
    def __init__(self, model_router, project_id: str):
        self.router = model_router
        self.project_id = project_id
    
    def generate_hypothetical_answer(self, query: str) -> str:
        """Generate hypothetical answer for better document retrieval"""
        
        prompt = f"""You are a project management expert.

User question: "{query}"

Generate a brief hypothetical answer (2-3 sentences) that would answer this question,
using technical terminology typical of PMO documents.

Do NOT say "according to documents" or "based on". 
Write as if it were an excerpt from an actual project document.

Hypothetical answer:"""
        
        try:
            response = self.router.run(
                task_type="summary",
                project_id=self.project_id,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content.strip()
        except Exception as e:
            logger.error(f"HyDE generation failed: {e}")
            return query


class UnifiedRAGEngine:
    """
    Unified RAG Engine with complete functionality
    
    Features:
    - Project + Library search
    - HyDE for better retrieval
    - Semantic caching
    - Score normalization
    - Library boost
    - Re-ranking
    """
    
    def __init__(
        self,
        project_vectorstore,
        library_vectorstore,
        embeddings,
        model_router,
        config,
        project_id: str
    ):
        """
        Initialize unified RAG engine
        
        Args:
            project_vectorstore: Chroma vectorstore for project documents
            library_vectorstore: Chroma vectorstore for library documents
            embeddings: Embeddings model
            model_router: ModelRouter instance for LLM calls
            config: Configuration object
            project_id: Current project ID
        """
        self.project_db = project_vectorstore
        self.library_db = library_vectorstore
        self.embeddings = embeddings
        self.router = model_router
        self.config = config
        self.project_id = project_id
        
        # Initialize components
        cache_enabled = config.get("rag.search.enable_semantic_cache", True)
        cache_ttl = config.get("rag.search.cache_ttl_seconds", 3600) // 3600
        
        self.cache = SemanticCache(
            embeddings=embeddings,
            ttl_hours=cache_ttl,
            similarity_threshold=0.95
        ) if cache_enabled else None
        
        self.hyde = HyDE(model_router, project_id)
        
        logger.info(f"Unified RAG Engine initialized for project: {project_id}")
    
    def search(
        self,
        query: str,
        top_k: int = None,
        include_library: bool = True,
        library_ratio: float = 0.3,
        use_hyde: bool = None,
        use_reranker: bool = None,
        use_cache: bool = True,
        **kwargs
    ) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """
        Unified search across project + library
        
        Args:
            query: Search query
            top_k: Number of results to return
            include_library: Whether to search library
            library_ratio: Proportion of library results (0.0-1.0)
            use_hyde: Use HyDE for better retrieval
            use_reranker: Use LLM for reranking
            use_cache: Use semantic cache
            **kwargs: Additional parameters
        
        Returns:
            (results, metadata)
        """
        # Get defaults from config
        if top_k is None:
            top_k = self.config.get("rag.search.default_top_k", 5)
        if use_hyde is None:
            use_hyde = self.config.get("rag.search.use_hyde", True)
        if use_reranker is None:
            use_reranker = self.config.get("rag.search.use_reranker", True)
        
        metadata = {
            "query": query,
            "top_k": top_k,
            "include_library": include_library,
            "use_hyde": use_hyde,
            "use_reranker": use_reranker,
            "cached": False
        }
        
        # Check cache
        if use_cache and self.cache:
            cached_results = self.cache.get(query)
            if cached_results:
                metadata["cached"] = True
                return cached_results[:top_k], metadata
        
        # Generate HyDE query if enabled
        search_query = query
        if use_hyde:
            try:
                hyde_answer = self.hyde.generate_hypothetical_answer(query)
                search_query = hyde_answer
                metadata["hyde_query"] = hyde_answer
                logger.debug(f"HyDE query: {hyde_answer[:100]}...")
            except Exception as e:
                logger.warning(f"HyDE failed, using original query: {e}")
        
        # Determine search strategy
        if not include_library or self.library_db is None:
            # Project only
            results = self._search_project(search_query, top_k * 2)
            metadata["library_used"] = False
        else:
            # Combined search
            k_library = max(1, int(top_k * library_ratio))
            k_project = top_k - k_library
            
            project_results = self._search_project(search_query, k_project * 2)
            library_results = self._search_library(search_query, k_library * 2)
            
            # Combine and deduplicate
            results = self._combine_results(project_results, library_results)
            metadata["library_used"] = True
            metadata["library_ratio"] = library_ratio
        
        # Normalize scores
        results = self._normalize_scores(results)
        
        # Re-rank if enabled
        if use_reranker and len(results) > top_k:
            results = self._rerank_results(results, query, top_k)
            metadata["reranked"] = True
        
        # Take top_k
        results = results[:top_k]
        
        # Update metadata
        metadata["project_results"] = sum(1 for r in results if not r.is_library)
        metadata["library_results"] = sum(1 for r in results if r.is_library)
        metadata["total_results"] = len(results)
        
        # Cache results
        if use_cache and self.cache:
            self.cache.set(query, results)
        
        return results, metadata
    
    def _search_project(self, query: str, k: int) -> List[SearchResult]:
        """Search project vectorstore"""
        if self.project_db is None:
            return []
        
        try:
            docs_with_scores = self.project_db.similarity_search_with_score(query, k=k)
            
            results = []
            for doc, score in docs_with_scores:
                result = SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata.copy(),
                    score=1 / (1 + score),  # Convert distance to similarity
                    source_query=query,
                    is_library=False
                )
                results.append(result)
            
            logger.debug(f"Found {len(results)} project results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching project: {e}")
            return []
    
    def _search_library(self, query: str, k: int) -> List[SearchResult]:
        """Search library vectorstore"""
        if self.library_db is None:
            return []
        
        try:
            docs_with_scores = self.library_db.similarity_search_with_score(query, k=k)
            
            results = []
            for doc, score in docs_with_scores:
                metadata = doc.metadata.copy()
                metadata['is_library'] = True
                
                # Detect category
                category = self._detect_library_category(metadata)
                
                # Apply boost
                boost = self._get_library_boost(category)
                
                result = SearchResult(
                    content=doc.page_content,
                    metadata=metadata,
                    score=(1 / (1 + score)) * boost,
                    source_query=query,
                    is_library=True,
                    library_category=category,
                    boost_factor=boost
                )
                results.append(result)
            
            logger.debug(f"Found {len(results)} library results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching library: {e}")
            return []
    
    def _detect_library_category(self, metadata: Dict) -> Optional[str]:
        """Detect library category from metadata"""
        file_path = metadata.get('file_path', '').lower()
        source = metadata.get('source', '').lower()
        
        categories = self.config.get("library.categories", [])
        
        for cat_config in categories:
            cat_name = cat_config.get('name', '')
            patterns = cat_config.get('patterns', [])
            
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if pattern_lower in file_path or pattern_lower in source:
                    return cat_name
        
        return "General"
    
    def _get_library_boost(self, category: Optional[str]) -> float:
        """Get boost factor for library category"""
        # Boost factors by category
        boosts = {
            "PMI": 1.2,
            "AACE": 1.2,
            "ED_STO": 1.3,
            "DCMA": 1.2,
            "General": 1.0
        }
        return boosts.get(category, 1.0)
    
    def _combine_results(
        self,
        project_results: List[SearchResult],
        library_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Combine and deduplicate results"""
        combined = project_results + library_results
        
        # Deduplicate by content hash
        seen_hashes = set()
        unique = []
        
        for result in sorted(combined, key=lambda x: x.score, reverse=True):
            content_hash = hashlib.md5(result.content[:100].encode()).hexdigest()
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique.append(result)
        
        return unique
    
    def _normalize_scores(self, results: List[SearchResult]) -> List[SearchResult]:
        """Normalize scores to 0-1 range"""
        if not results:
            return results
        
        scores = [r.score for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores equal
            for r in results:
                r.score = 1.0
        else:
            # Normalize
            for r in results:
                r.score = (r.score - min_score) / (max_score - min_score)
        
        return results
    
    def _rerank_results(
        self,
        results: List[SearchResult],
        query: str,
        top_k: int
    ) -> List[SearchResult]:
        """Re-rank results using LLM"""
        if len(results) <= top_k:
            return results
        
        # Create ranking prompt
        docs_text = "\n\n".join([
            f"Document {i+1}:\n{r.content[:300]}..."
            for i, r in enumerate(results)
        ])
        
        prompt = f"""Given this query: "{query}"

Rank the following documents by relevance. Return ONLY a comma-separated list of document numbers in order of relevance (most relevant first).

{docs_text}

Ranking (e.g., "3,1,5,2,4"):"""
        
        try:
            response = self.router.run(
                task_type="analysis",
                project_id=self.project_id,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse ranking
            ranking_text = response.content.strip()
            rankings = [int(x.strip()) - 1 for x in ranking_text.split(",") if x.strip().isdigit()]
            
            # Apply ranking
            reranked = []
            for rank, idx in enumerate(rankings[:top_k]):
                if 0 <= idx < len(results):
                    result = results[idx]
                    result.rerank_score = 1.0 - (rank / len(rankings))
                    reranked.append(result)
            
            logger.debug(f"Re-ranked {len(reranked)} results")
            return reranked
            
        except Exception as e:
            logger.warning(f"Re-ranking failed, using original order: {e}")
            return results
    
    def format_context(
        self,
        results: List[SearchResult],
        max_tokens: int = 8000
    ) -> str:
        """Format results as context for LLM"""
        context_parts = []
        
        # Separate library and project
        library_results = [r for r in results if r.is_library]
        project_results = [r for r in results if not r.is_library]
        
        # Library context first
        if library_results:
            context_parts.append(
                "LIBRARY CONTEXT (Industry Standards and Best Practices):\n"
            )
            
            for i, result in enumerate(library_results, 1):
                source = result.metadata.get('source', 'Library Document')
                category = result.library_category or 'General'
                
                context_parts.append(
                    f"[{i}] {category} - {source}\n"
                    f"{result.content}\n"
                )
        
        # Project context
        if project_results:
            context_parts.append(
                "\nPROJECT CONTEXT (Current Project Documents):\n"
            )
            
            start_idx = len(library_results) + 1
            for i, result in enumerate(project_results, start_idx):
                source = result.metadata.get('source', 'Project Document')
                
                context_parts.append(
                    f"[{i}] {source}\n"
                    f"{result.content}\n"
                )
        
        context = "\n".join(context_parts)
        
        # Truncate if too long (rough estimation)
        if len(context) > max_tokens * 4:  # ~4 chars per token
            context = context[:max_tokens * 4] + "\n\n[Context truncated...]"
        
        return context
    
    def get_sources_summary(self, results: List[SearchResult]) -> Dict:
        """Generate summary of sources used"""
        summary = {
            "total": len(results),
            "project": sum(1 for r in results if not r.is_library),
            "library": sum(1 for r in results if r.is_library),
            "library_categories": {},
            "avg_score": sum(r.score for r in results) / len(results) if results else 0,
            "boost_applied": any(r.boost_factor != 1.0 for r in results)
        }
        
        # Count by category
        for result in results:
            if result.is_library and result.library_category:
                cat = result.library_category
                summary["library_categories"][cat] = summary["library_categories"].get(cat, 0) + 1
        
        return summary
