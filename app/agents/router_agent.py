"""Router Agent - Coordinates the screening workflow."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.agents.screening_agent import screening_agent, ScreeningAgent
from app.agents.matching_agent import matching_agent, MatchingAgent
from app.agents.ranking_agent import ranking_agent, RankingAgent
from app.models.candidate import Candidate
from app.models.job import JobDescription
from app.models.matching import ScreeningResult, MatchResult, RankingResult, PipelineResult
from app.services.rag_pipeline import rag_pipeline

logger = logging.getLogger(__name__)


class RouterAgent(BaseAgent):
    """
    Agent responsible for coordinating the entire screening workflow.
    
    Routes candidates through the pipeline:
    1. Screening - Filter candidates by minimum requirements
    2. Matching - Detailed semantic matching for passed candidates
    3. Ranking - Final ranking and recommendations
    """
    
    def __init__(self):
        super().__init__(
            name="RouterAgent",
            description="Coordinates the HR screening workflow and routes candidates through agents"
        )
        self.screening_agent = screening_agent
        self.matching_agent = matching_agent
        self.ranking_agent = ranking_agent
        self.rag_pipeline = rag_pipeline
    
    async def execute(
        self,
        candidates: List[Candidate],
        job: JobDescription,
        skip_screening: bool = False,
        strict_screening: bool = False
    ) -> Dict[str, Any]:
        """
        Execute the full screening pipeline for candidates.
        
        Args:
            candidates: List of candidates to process
            job: Job description
            skip_screening: If True, skip initial screening
            strict_screening: If True, use strict screening mode
            
        Returns:
            Complete pipeline results
        """
        self.log_action("Starting pipeline", {
            "job_id": job.id,
            "candidates_count": len(candidates),
            "skip_screening": skip_screening
        })
        
        pipeline_start = datetime.now()
        results = {
            "job_id": job.id,
            "job_title": job.title,
            "total_candidates": len(candidates),
            "pipeline_start": pipeline_start.isoformat(),
            "screening_results": [],
            "matching_results": [],
            "ranking_result": None,
            "summary": {}
        }
        
        if not candidates:
            results["summary"] = {"error": "No candidates provided"}
            return results
        
        # Index candidates and job in vector store
        await self._index_data(candidates, job)
        
        # Step 1: Screening
        passed_candidates = []
        if skip_screening:
            passed_candidates = candidates
            self.log_action("Screening skipped", {"passed": len(candidates)})
        else:
            screening_results = await self.screening_agent.batch_screen(
                candidates, job, strict_screening
            )
            results["screening_results"] = [r.model_dump() for r in screening_results]
            
            # Filter passed candidates
            passed_ids = {r.candidate_id for r in screening_results if r.passed}
            passed_candidates = [c for c in candidates if c.id in passed_ids]
            
            self.log_action("Screening complete", {
                "total": len(candidates),
                "passed": len(passed_candidates),
                "failed": len(candidates) - len(passed_candidates)
            })
        
        # Step 2: Matching
        if passed_candidates:
            matching_results = await self.matching_agent.batch_match(
                passed_candidates, job
            )
            results["matching_results"] = [r.model_dump() for r in matching_results]
            
            self.log_action("Matching complete", {
                "matched": len(matching_results)
            })
            
            # Step 3: Ranking
            candidates_dict = {c.id: c for c in passed_candidates}
            ranking_result = await self.ranking_agent.execute(
                matching_results, candidates_dict, job
            )
            results["ranking_result"] = ranking_result.model_dump()
            
            self.log_action("Ranking complete", {
                "ranked": ranking_result.total_candidates
            })
        
        # Generate summary
        pipeline_end = datetime.now()
        results["pipeline_end"] = pipeline_end.isoformat()
        results["processing_time_seconds"] = (pipeline_end - pipeline_start).total_seconds()
        
        results["summary"] = await self._generate_pipeline_summary(results, job)
        
        self.log_action("Pipeline complete", {
            "processing_time": results["processing_time_seconds"]
        })
        
        return results
    
    async def _index_data(self, candidates: List[Candidate], job: JobDescription):
        """Index candidates and job in vector store."""
        # Index job
        await self.rag_pipeline.index_job(job)
        
        # Index candidates
        for candidate in candidates:
            await self.rag_pipeline.index_candidate(candidate)
    
    async def _generate_pipeline_summary(
        self,
        results: Dict[str, Any],
        job: JobDescription
    ) -> Dict[str, Any]:
        """Generate summary of pipeline results."""
        total = results["total_candidates"]
        screening_results = results.get("screening_results", [])
        matching_results = results.get("matching_results", [])
        ranking_result = results.get("ranking_result")
        
        passed_screening = sum(1 for r in screening_results if r.get("passed", True))
        
        # Calculate score distributions
        scores = [r.get("overall_score", 0) for r in matching_results]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Count recommendations
        recommendations = {}
        if ranking_result and ranking_result.get("rankings"):
            for r in ranking_result["rankings"]:
                rec = r.get("recommendation", "unknown")
                recommendations[rec] = recommendations.get(rec, 0) + 1
        
        summary = {
            "total_candidates": total,
            "passed_screening": passed_screening,
            "failed_screening": total - passed_screening if screening_results else 0,
            "matched_candidates": len(matching_results),
            "average_match_score": round(avg_score, 1),
            "recommendation_distribution": recommendations,
            "processing_time_seconds": results.get("processing_time_seconds", 0)
        }
        
        # Get top candidates
        if ranking_result and ranking_result.get("rankings"):
            top_3 = ranking_result["rankings"][:3]
            summary["top_candidates"] = [
                {
                    "rank": r["rank"],
                    "name": r.get("candidate_name", "Unknown"),
                    "score": r.get("overall_score", 0),
                    "recommendation": r.get("recommendation", "unknown")
                }
                for r in top_3
            ]
        
        return summary
    
    async def process_single_candidate(
        self,
        candidate: Candidate,
        job: JobDescription,
        skip_screening: bool = False
    ) -> PipelineResult:
        """
        Process a single candidate through the pipeline.
        
        Args:
            candidate: Candidate to process
            job: Job description
            skip_screening: If True, skip screening step
            
        Returns:
            PipelineResult for the candidate
        """
        self.log_action("Processing single candidate", {
            "candidate_id": candidate.id,
            "job_id": job.id
        })
        
        # Screening
        if skip_screening:
            screening_result = ScreeningResult(
                candidate_id=candidate.id,
                job_id=job.id,
                passed=True,
                reasons=["Screening skipped"],
                screening_notes="Screening step was bypassed"
            )
        else:
            screening_result = await self.screening_agent.execute(candidate, job)
        
        # Matching (only if passed screening)
        matching_result = None
        if screening_result.passed:
            matching_result = await self.matching_agent.execute(candidate, job)
        
        # Determine final recommendation
        if not screening_result.passed:
            final_recommendation = "Not Recommended - Did not pass initial screening"
        elif matching_result:
            if matching_result.overall_score >= 80:
                final_recommendation = "Highly Recommended - Strong candidate"
            elif matching_result.overall_score >= 65:
                final_recommendation = "Recommended - Good match"
            elif matching_result.overall_score >= 50:
                final_recommendation = "Consider - Moderate match"
            else:
                final_recommendation = "Not Recommended - Low match score"
        else:
            final_recommendation = "Unable to determine - Matching not completed"
        
        return PipelineResult(
            candidate_id=candidate.id,
            job_id=job.id,
            screening=screening_result,
            matching=matching_result,
            final_recommendation=final_recommendation
        )
    
    async def find_candidates_for_job(
        self,
        job: JobDescription,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Use RAG to find candidates matching a job from the vector store.
        
        Args:
            job: Job description to match
            top_k: Number of candidates to return
            
        Returns:
            List of matching candidates from vector store
        """
        return await self.rag_pipeline.find_matching_candidates(job, top_k)
    
    async def find_jobs_for_candidate(
        self,
        candidate: Candidate,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Use RAG to find jobs matching a candidate from the vector store.
        
        Args:
            candidate: Candidate to match
            top_k: Number of jobs to return
            
        Returns:
            List of matching jobs from vector store
        """
        return await self.rag_pipeline.find_matching_jobs(candidate, top_k)


# Global router agent instance
router_agent = RouterAgent()
