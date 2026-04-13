"""Matching Agent - Compares candidates to job descriptions using semantic similarity."""

import logging
import asyncio
from typing import List, Dict, Any

from app.agents.base_agent import BaseAgent
from app.models.candidate import Candidate
from app.models.job import JobDescription
from app.models.matching import MatchResult
from app.services.rag_pipeline import rag_pipeline

logger = logging.getLogger(__name__)


class MatchingAgent(BaseAgent):
    """
    Agent responsible for detailed candidate-job matching.
    
    Uses semantic similarity and skill matching to produce
    comprehensive match scores and analysis.
    """
    
    def __init__(self):
        super().__init__(
            name="MatchingAgent",
            description="Matches candidates to jobs using semantic similarity and skill analysis"
        )
        self.rag_pipeline = rag_pipeline
    
    async def execute(
        self,
        candidate: Candidate,
        job: JobDescription
    ) -> MatchResult:
        """
        Perform detailed matching between a candidate and job.
        
        Args:
            candidate: Candidate to match
            job: Job description to match against
            
        Returns:
            MatchResult with detailed scores and analysis
        """
        self.log_action("Starting matching", {
            "candidate_id": candidate.id,
            "job_id": job.id
        })
        
        resume = candidate.resume_data
        
        # Get detailed analysis from RAG pipeline
        analysis = await self.rag_pipeline.analyze_candidate_job_fit(candidate, job)
        
        # Get AI-generated insights
        insights = await self.rag_pipeline.generate_match_insights(candidate, job, analysis)
        
        # Determine recommendation based on overall score
        recommendation = self._get_recommendation(analysis["overall_score"])
        
        result = MatchResult(
            candidate_id=candidate.id,
            job_id=job.id,
            overall_score=analysis["overall_score"],
            skill_score=analysis["skill_score"],
            experience_score=analysis["experience_score"],
            education_score=analysis["education_score"],
            semantic_similarity=analysis["semantic_similarity"],
            matched_skills=analysis["matched_required_skills"] + analysis["matched_preferred_skills"],
            missing_required_skills=analysis["missing_required_skills"],
            missing_preferred_skills=analysis["missing_preferred_skills"],
            additional_skills=analysis["additional_skills"],
            experience_years=analysis["experience_years"],
            experience_gap=analysis["experience_gap"],
            strengths=insights.get("strengths", []),
            concerns=insights.get("concerns", []),
            recommendation=recommendation
        )
        
        self.log_action("Matching complete", {
            "candidate_id": candidate.id,
            "overall_score": result.overall_score
        })
        
        return result
    
    def _get_recommendation(self, score: float) -> str:
        """Generate recommendation based on overall score."""
        if score >= 80:
            return "Highly Recommended - Strong match for this position. Proceed to interview."
        elif score >= 65:
            return "Recommended - Good match with some gaps. Consider for interview."
        elif score >= 50:
            return "Consider - Moderate match. Review specific requirements before proceeding."
        else:
            return "Not Recommended - Significant gaps in requirements. May not be suitable."
    
    async def batch_match(
        self,
        candidates: List[Candidate],
        job: JobDescription
    ) -> List[MatchResult]:
        """
        Match multiple candidates against a job IN PARALLEL.
        
        Args:
            candidates: List of candidates to match
            job: Job description
            
        Returns:
            List of match results
        """
        # Process all candidates in parallel
        tasks = [self.execute(candidate, job) for candidate in candidates]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error matching candidate {candidates[i].id}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def find_best_matches(
        self,
        candidates: List[Candidate],
        job: JobDescription,
        top_k: int = 10
    ) -> List[MatchResult]:
        """
        Find the best matching candidates for a job.
        
        Args:
            candidates: List of candidates to evaluate
            job: Job description
            top_k: Number of top matches to return
            
        Returns:
            Top k match results sorted by score
        """
        all_results = await self.batch_match(candidates, job)
        
        # Sort by overall score descending
        sorted_results = sorted(
            all_results,
            key=lambda x: x.overall_score,
            reverse=True
        )
        
        return sorted_results[:top_k]
    
    async def compare_candidates(
        self,
        candidates: List[Candidate],
        job: JobDescription
    ) -> Dict[str, Any]:
        """
        Generate a comparative analysis of multiple candidates.
        
        Args:
            candidates: Candidates to compare
            job: Job description
            
        Returns:
            Comparative analysis with rankings and insights
        """
        if not candidates:
            return {"error": "No candidates to compare"}
        
        # Get match results for all candidates
        match_results = await self.batch_match(candidates, job)
        
        # Build comparison prompt
        candidate_summaries = []
        for i, (candidate, result) in enumerate(zip(candidates, match_results)):
            resume = candidate.resume_data
            summary = f"""
Candidate {i+1}: {resume.name or 'Unknown'}
- Overall Score: {result.overall_score:.1f}/100
- Skills Matched: {len(result.matched_skills)} skills
- Experience: {result.experience_years:.1f} years
- Key Strengths: {', '.join(result.strengths[:2]) if result.strengths else 'N/A'}
- Key Concerns: {', '.join(result.concerns[:2]) if result.concerns else 'N/A'}
"""
            candidate_summaries.append(summary)
        
        prompt = f"""Compare these candidates for the {job.title} position and provide a comparative analysis.

{chr(10).join(candidate_summaries)}

Provide:
1. Ranking of candidates from best to worst fit
2. Key differentiators between candidates
3. Final recommendation on which candidate(s) to interview

Be concise and professional."""

        comparison = await self.think(
            prompt=prompt,
            system_prompt="You are an expert HR analyst providing objective candidate comparisons.",
            temperature=0.3
        )
        
        return {
            "match_results": match_results,
            "comparison_analysis": comparison,
            "rankings": sorted(
                [{"candidate_id": r.candidate_id, "score": r.overall_score} 
                 for r in match_results],
                key=lambda x: x["score"],
                reverse=True
            )
        }


# Global matching agent instance
matching_agent = MatchingAgent()
