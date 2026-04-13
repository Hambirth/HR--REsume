"""Vector store service using ChromaDB for semantic search."""

import logging
from typing import List, Dict, Any, Optional
import chromadb

from app.config import settings
from app.services.usf_client import usf_client

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-based vector store for resumes and job descriptions."""
    
    CANDIDATE_COLLECTION = "candidates"
    JOB_COLLECTION = "jobs"
    SKILLS_COLLECTION = "skills"
    
    def __init__(self):
        # Use the new ChromaDB PersistentClient API
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir
        )
        self.usf_client = usf_client
        
        # Initialize collections
        self._init_collections()
    
    def _init_collections(self):
        """Initialize or get existing collections."""
        self.candidates = self.client.get_or_create_collection(
            name=self.CANDIDATE_COLLECTION,
            metadata={"description": "Resume embeddings for candidates"}
        )
        
        self.jobs = self.client.get_or_create_collection(
            name=self.JOB_COLLECTION,
            metadata={"description": "Job description embeddings"}
        )
        
        self.skills = self.client.get_or_create_collection(
            name=self.SKILLS_COLLECTION,
            metadata={"description": "Skills taxonomy embeddings"}
        )
    
    async def add_candidate(
        self,
        candidate_id: str,
        resume_text: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Add a candidate resume to the vector store.
        
        Args:
            candidate_id: Unique candidate identifier
            resume_text: Full resume text for embedding
            metadata: Additional metadata to store
            embedding: Pre-computed embedding (to avoid API call)
            
        Returns:
            Success status
        """
        try:
            # Ensure metadata values are serializable
            clean_metadata = {
                k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                for k, v in metadata.items()
            }
            
            # Use provided embedding or let ChromaDB compute it
            if embedding:
                self.candidates.add(
                    ids=[candidate_id],
                    documents=[resume_text],
                    metadatas=[clean_metadata],
                    embeddings=[embedding]
                )
                logger.info(f"Added candidate {candidate_id} with pre-computed embedding")
            else:
                self.candidates.add(
                    ids=[candidate_id],
                    documents=[resume_text],
                    metadatas=[clean_metadata]
                )
                logger.info(f"Added candidate {candidate_id} to vector store")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding candidate to vector store: {e}")
            return False
    
    async def add_job(
        self,
        job_id: str,
        job_text: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add a job description to the vector store.
        
        Args:
            job_id: Unique job identifier
            job_text: Full job description text for embedding
            metadata: Additional metadata to store
            
        Returns:
            Success status
        """
        try:
            # Ensure metadata values are serializable
            clean_metadata = {
                k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                for k, v in metadata.items()
            }
            
            # Add to collection without embeddings (ChromaDB will use default)
            self.jobs.add(
                ids=[job_id],
                documents=[job_text],
                metadatas=[clean_metadata]
            )
            
            logger.info(f"Added job {job_id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding job to vector store: {e}")
            return False
    
    async def add_skills(self, skills: List[str]) -> bool:
        """
        Add skills to the skills taxonomy collection.
        
        Args:
            skills: List of skill names
            
        Returns:
            Success status
        """
        try:
            # Filter out existing skills
            existing = self.skills.get()
            existing_skills = set(existing.get("documents", []))
            new_skills = [s for s in skills if s.lower() not in existing_skills]
            
            if not new_skills:
                return True
            
            # Generate IDs for skills
            skill_ids = [f"skill_{hash(s) % 10000000}" for s in new_skills]
            
            # Add to collection without embeddings
            self.skills.add(
                ids=skill_ids,
                documents=new_skills,
                metadatas=[{"skill": s} for s in new_skills]
            )
            
            logger.info(f"Added {len(new_skills)} new skills to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding skills to vector store: {e}")
            return False
    
    async def search_candidates(
        self,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for candidates similar to a query.
        
        Args:
            query: Search query (job description or requirements)
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of matching candidates with scores
        """
        try:
            # Use ChromaDB's default embedding for search
            results = self.candidates.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            candidates = []
            if results and results.get("ids"):
                for i, candidate_id in enumerate(results["ids"][0]):
                    candidates.append({
                        "id": candidate_id,
                        "document": results["documents"][0][i] if results.get("documents") else None,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0
                    })
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error searching candidates: {e}")
            return []
    
    async def search_jobs(
        self,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs similar to a query.
        
        Args:
            query: Search query (resume text or skills)
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of matching jobs with scores
        """
        try:
            # Use ChromaDB's default embedding for search
            results = self.jobs.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            jobs = []
            if results and results.get("ids"):
                for i, job_id in enumerate(results["ids"][0]):
                    jobs.append({
                        "id": job_id,
                        "document": results["documents"][0][i] if results.get("documents") else None,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0
                    })
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            return []
    
    async def find_similar_skills(
        self,
        skill: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find skills similar to a given skill.
        
        Args:
            skill: Skill to find similar skills for
            n_results: Number of results to return
            
        Returns:
            List of similar skills with scores
        """
        try:
            results = self.skills.query(
                query_texts=[skill],
                n_results=n_results
            )
            
            similar = []
            if results and results.get("ids"):
                for i, skill_id in enumerate(results["ids"][0]):
                    similar.append({
                        "skill": results["documents"][0][i] if results.get("documents") else "",
                        "distance": results["distances"][0][i] if results.get("distances") else 0
                    })
            
            return similar
            
        except Exception as e:
            logger.error(f"Error finding similar skills: {e}")
            return []
    
    async def get_semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate semantic similarity between two texts using embeddings.
        Falls back to keyword overlap if embeddings fail.
        
        Args:
            text1: First text (candidate profile)
            text2: Second text (job description)
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        try:
            # Try embedding-based similarity first
            embeddings = await self.usf_client.get_embeddings([text1[:2000], text2[:2000]])
            
            if embeddings and len(embeddings) == 2 and embeddings[0] and embeddings[1]:
                # Calculate cosine similarity
                import numpy as np
                vec1 = np.array(embeddings[0])
                vec2 = np.array(embeddings[1])
                
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                
                if norm1 > 0 and norm2 > 0:
                    similarity = dot_product / (norm1 * norm2)
                    return float(max(0, min(1, similarity)))
            
            # Fallback to keyword overlap
            return self._keyword_similarity(text1, text2)
            
        except Exception as e:
            logger.warning(f"Embedding similarity failed, using keyword fallback: {e}")
            return self._keyword_similarity(text1, text2)
    
    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """Fallback keyword-based similarity."""
        import re
        
        def extract_keywords(text):
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 
                        'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
                        'have', 'been', 'were', 'they', 'this', 'that', 'with',
                        'from', 'will', 'would', 'there', 'their', 'what', 'about'}
            return set(w for w in words if w not in stopwords)
        
        kw1, kw2 = extract_keywords(text1), extract_keywords(text2)
        if not kw1 or not kw2:
            return 0.0
        
        intersection = len(kw1 & kw2)
        min_size = min(len(kw1), len(kw2))
        return intersection / min_size if min_size > 0 else 0.0
    
    def delete_candidate(self, candidate_id: str) -> bool:
        """Delete a candidate from the vector store."""
        try:
            self.candidates.delete(ids=[candidate_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting candidate: {e}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from the vector store."""
        try:
            self.jobs.delete(ids=[job_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting job: {e}")
            return False
    
    def get_all_candidates(self) -> List[Dict[str, Any]]:
        """Get all candidates from the vector store."""
        try:
            results = self.candidates.get()
            candidates = []
            if results and results.get("ids"):
                for i, candidate_id in enumerate(results["ids"]):
                    candidates.append({
                        "id": candidate_id,
                        "document": results["documents"][i] if results.get("documents") else None,
                        "metadata": results["metadatas"][i] if results.get("metadatas") else {}
                    })
            return candidates
        except Exception as e:
            logger.error(f"Error getting all candidates: {e}")
            return []
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs from the vector store."""
        try:
            results = self.jobs.get()
            jobs = []
            if results and results.get("ids"):
                for i, job_id in enumerate(results["ids"]):
                    jobs.append({
                        "id": job_id,
                        "document": results["documents"][i] if results.get("documents") else None,
                        "metadata": results["metadatas"][i] if results.get("metadatas") else {}
                    })
            return jobs
        except Exception as e:
            logger.error(f"Error getting all jobs: {e}")
            return []


# Global vector store instance
vector_store = VectorStore()
