"""UltraSafe API client for chat, embeddings, and reranking."""

import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional
import logging

from app.config import settings
from app.services.cache import embedding_cache, chat_cache

logger = logging.getLogger(__name__)


class USFClient:
    """Client for UltraSafe API interactions."""
    
    def __init__(self):
        self.base_url = settings.usf_base_url
        self.api_key = settings.usf_api_key
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        self.timeout = 60.0
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to USF API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (defaults to usf-mini)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            tools: Optional list of tools for function calling
            
        Returns:
            API response dict
        """
        model = model or settings.chat_model
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            "web_search": True
        }
        
        if tools:
            payload["tools"] = tools
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Chat API response keys: {result.keys()}")
                
                # Handle nested response format
                if "result" in result:
                    return result["result"]
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in chat completion: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    async def _get_single_embedding(
        self,
        text: str,
        model: str,
        client: httpx.AsyncClient
    ) -> List[float]:
        """Get embedding for a single text (helper for parallel processing)."""
        # Check cache first
        cache_key = {"text": text[:500], "model": model}
        cached = embedding_cache.get(cache_key)
        if cached:
            logger.info("Using cached embedding")
            return cached
        
        payload = {
            "model": model,
            "input": text
        }
        
        response = await client.post(
            f"{self.base_url}/embed/embeddings",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract embedding from response
        embedding = None
        if "result" in result and "data" in result["result"]:
            embedding = result["result"]["data"][0]["embedding"]
        elif "data" in result and len(result["data"]) > 0:
            embedding = result["data"][0]["embedding"]
        
        if embedding:
            # Cache the result
            embedding_cache.set(cache_key, embedding)
            return embedding
        else:
            logger.warning(f"Could not extract embedding from: {list(result.keys())}")
            return []
    
    async def get_embeddings(
        self,
        texts: List[str],
        model: str = None
    ) -> List[List[float]]:
        """
        Get embeddings for a list of texts IN PARALLEL.
        
        Args:
            texts: List of texts to embed
            model: Embedding model name
            
        Returns:
            List of embedding vectors
        """
        model = model or settings.embed_model
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Process all texts in parallel using asyncio.gather
                tasks = [
                    self._get_single_embedding(text, model, client)
                    for text in texts
                ]
                embeddings = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle any exceptions
                result_embeddings = []
                for i, emb in enumerate(embeddings):
                    if isinstance(emb, Exception):
                        logger.error(f"Error getting embedding for text {i}: {emb}")
                        result_embeddings.append([])
                    else:
                        result_embeddings.append(emb)
                
                return result_embeddings
                
        except Exception as e:
            logger.error(f"Error in get_embeddings: {e}")
            raise
    
    async def get_embedding(self, text: str, model: str = None) -> List[float]:
        """Get embedding for a single text."""
        embeddings = await self.get_embeddings([text], model)
        return embeddings[0] if embeddings else []
    
    async def rerank(
        self,
        query: str,
        texts: List[str],
        model: str = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank texts based on relevance to query.
        
        Args:
            query: Query text
            texts: List of texts to rerank
            model: Rerank model name
            top_k: Number of top results to return
            
        Returns:
            List of dicts with index, text, and score
        """
        model = model or settings.rerank_model
        
        payload = {
            "model": model,
            "query": query,
            "texts": texts
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/embed/reranker",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract reranked results
                if "result" in result and "data" in result["result"]:
                    data = result["result"]["data"]
                    # Sort by score descending
                    sorted_data = sorted(data, key=lambda x: x.get("score", 0), reverse=True)
                    if top_k:
                        sorted_data = sorted_data[:top_k]
                    return sorted_data
                else:
                    logger.warning(f"Unexpected rerank response format: {result}")
                    return []
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in rerank: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in rerank: {e}")
            raise
    
    async def extract_resume_info(self, resume_text: str) -> Dict[str, Any]:
        """
        Use LLM to extract structured information from resume text.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Structured resume data dict
        """
        # Truncate resume text to save tokens and speed up response
        truncated_text = resume_text[:3000]  # Reduced from 4000
        
        # Shorter, more direct prompt
        system_prompt = """Extract resume info as JSON:
{"name":"","email":"","phone":"","skills":[],"education":[{"degree":"","institution":"","field_of_study":"","graduation_year":""}],"experience":[{"job_title":"","company":"","start_date":"YYYY-MM","end_date":"YYYY-MM","is_current":false}],"certifications":[],"summary":""}
Extract ALL skills. Return ONLY JSON."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": truncated_text}
        ]
        
        try:
            response = await self.chat_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=1500  # Increased to prevent truncation
            )
            
            # Extract content from response
            logger.info(f"Resume extraction response: {response}")
            
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                finish_reason = response["choices"][0].get("finish_reason", "")
                
                # Check if response was truncated
                if finish_reason == "length":
                    logger.warning("LLM response was truncated due to token limit")
                
                # Check for empty content
                if not content or not content.strip():
                    logger.error("Empty content from LLM extraction API")
                    return {}
                
                logger.info(f"LLM content: {content[:500]}...")
                
                # Parse JSON from content
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                result = json.loads(content)
                logger.info(f"Parsed result keys: {result.keys()}")
                return result
            else:
                logger.warning(f"No choices in chat response: {response}")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse resume extraction JSON: {e}, content: {content[:200]}")
            return {}
        except Exception as e:
            logger.error(f"Error extracting resume info: {e}")
            return {}


# Global client instance
usf_client = USFClient()
