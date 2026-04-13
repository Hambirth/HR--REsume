"""Ranking Agent - Scores and ranks candidates by overall fit."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.models.candidate import Candidate
from app.models.job import JobDescription
from app.models.matching import MatchResult, RankingResult, CandidateRanking

logger = logging.getLogger(__name__)


class RankingAgent(BaseAgent):
    """
    Agent responsible for ranking candidates.
    
    Takes match results and produces final rankings
    with detailed reasoning and recommendations.
    """
    
    def __init__(self):
        super().__init__(
            name="RankingAgent",
            description="Ranks candidates based on match scores and generates final recommendations"
        )
    
    async def execute(
        self,
        match_results: List[MatchResult],
        candidates: Dict[str, Candidate],
        job: JobDescription,
        weights: Optional[Dict[str, float]] = None
    ) -> RankingResult:
        """
        Rank candidates based on match results.
        
        Args:
            match_results: List of match results from MatchingAgent
            candidates: Dict mapping candidate_id to Candidate
            job: Job description
            weights: Optional custom weights for ranking criteria
            
        Returns:
            RankingResult with ordered rankings and analysis
        """
        self.log_action("Starting ranking", {
            "job_id": job.id,
            "candidates_count": len(match_results)
        })
        
        # Use custom weights or job-defined weights
        ranking_weights = weights or {
            "skill": job.skill_weight,
            "experience": job.experience_weight,
            "education": job.education_weight,
            "semantic": 0.2
        }
        
        # Calculate weighted scores and create rankings
        scored_candidates = []
        for result in match_results:
            weighted_score = (
                result.skill_score * ranking_weights["skill"] +
                result.experience_score * ranking_weights["experience"] +
                result.education_score * ranking_weights["education"] +
                result.semantic_similarity * 100 * ranking_weights["semantic"]
            )
            
            candidate = candidates.get(result.candidate_id)
            candidate_name = candidate.resume_data.name if candidate else "Unknown"
            
            # Determine recommendation category
            recommendation = self._categorize_candidate(weighted_score, result)
            
            scored_candidates.append({
                "candidate_id": result.candidate_id,
                "candidate_name": candidate_name,
                "weighted_score": weighted_score,
                "match_result": result,
                "recommendation": recommendation
            })
        
        # Sort by weighted score descending
        scored_candidates.sort(key=lambda x: x["weighted_score"], reverse=True)
        
        # Create ranking entries
        rankings = []
        for rank, entry in enumerate(scored_candidates, 1):
            result = entry["match_result"]
            
            ranking = CandidateRanking(
                rank=rank,
                candidate_id=entry["candidate_id"],
                candidate_name=entry["candidate_name"],
                overall_score=entry["weighted_score"],
                skill_score=result.skill_score,
                experience_score=result.experience_score,
                education_score=result.education_score,
                semantic_similarity=result.semantic_similarity,
                recommendation=entry["recommendation"],
                key_strengths=result.strengths[:3],
                key_concerns=result.concerns[:3]
            )
            rankings.append(ranking.model_dump())
        
        # Generate summary
        summary = await self._generate_ranking_summary(rankings, job)
        
        result = RankingResult(
            job_id=job.id,
            rankings=rankings,
            total_candidates=len(match_results),
            ranking_criteria=ranking_weights,
            summary=summary
        )
        
        self.log_action("Ranking complete", {
            "job_id": job.id,
            "total_ranked": len(rankings)
        })
        
        return result
    
    def _categorize_candidate(self, score: float, match_result: MatchResult) -> str:
        """Categorize candidate based on score and match details."""
        if score >= 80 and len(match_result.missing_required_skills) == 0:
            return "highly_recommended"
        elif score >= 70 or (score >= 60 and len(match_result.missing_required_skills) <= 1):
            return "recommended"
        elif score >= 50:
            return "consider"
        else:
            return "not_recommended"
    
    async def _generate_ranking_summary(
        self,
        rankings: List[Dict[str, Any]],
        job: JobDescription
    ) -> str:
        """Generate AI-powered summary of rankings."""
        if not rankings:
            return "No candidates to rank."
        
        # Quick summary for small candidate pools (skip AI call)
        if len(rankings) <= 3:
            top = rankings[0]
            return f"{top['candidate_name']} is the top candidate with a score of {top['overall_score']:.1f}. " + \
                   f"Total {len(rankings)} candidate(s) evaluated."
        
        # Build summary prompt
        top_candidates = rankings[:5]
        candidate_lines = []
        for r in top_candidates:
            line = f"#{r['rank']} {r['candidate_name']}: Score {r['overall_score']:.1f} - {r['recommendation']}"
            candidate_lines.append(line)
        
        prompt = f"""Generate a brief executive summary of these candidate rankings for the {job.title} position.

Total Candidates Evaluated: {len(rankings)}

Top Candidates:
{chr(10).join(candidate_lines)}

Highly Recommended: {sum(1 for r in rankings if r['recommendation'] == 'highly_recommended')}
Recommended: {sum(1 for r in rankings if r['recommendation'] == 'recommended')}
Consider: {sum(1 for r in rankings if r['recommendation'] == 'consider')}
Not Recommended: {sum(1 for r in rankings if r['recommendation'] == 'not_recommended')}

Write a 2-3 sentence executive summary highlighting:
1. Overall candidate pool quality
2. Top recommendation(s)
3. Any notable observations"""

        summary = await self.think(
            prompt=prompt,
            system_prompt="You are an executive HR advisor providing concise recruitment summaries.",
            temperature=0.3
        )
        
        return summary or "Ranking completed. Review individual candidate scores for details."
    
    async def get_top_candidates(
        self,
        ranking_result: RankingResult,
        top_k: int = 5,
        min_score: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Get top candidates from a ranking result.
        
        Args:
            ranking_result: RankingResult to filter
            top_k: Maximum number of candidates to return
            min_score: Minimum score threshold
            
        Returns:
            List of top candidate rankings
        """
        filtered = [
            r for r in ranking_result.rankings
            if r["overall_score"] >= min_score
        ]
        return filtered[:top_k]
    
    async def generate_candidate_report(
        self,
        candidate: Candidate,
        match_result: MatchResult,
        ranking: Dict[str, Any],
        job: JobDescription
    ) -> str:
        """
        Generate a detailed candidate report.
        
        Args:
            candidate: Candidate data
            match_result: Match result for the candidate
            ranking: Ranking data for the candidate
            job: Job description
            
        Returns:
            Formatted candidate report
        """
        resume = candidate.resume_data
        
        prompt = f"""Generate a professional candidate evaluation report.

CANDIDATE INFORMATION:
Name: {resume.name or 'Unknown'}
Email: {resume.email or 'Not provided'}
Phone: {resume.phone or 'Not provided'}
Total Experience: {resume.get_total_experience_years():.1f} years

POSITION: {job.title}

EVALUATION SCORES:
- Overall Rank: #{ranking['rank']} of {ranking.get('total', 'N/A')} candidates
- Overall Score: {match_result.overall_score:.1f}/100
- Skills Match: {match_result.skill_score:.1f}/100
- Experience Match: {match_result.experience_score:.1f}/100
- Education Match: {match_result.education_score:.1f}/100

SKILLS ANALYSIS:
Matched Skills: {', '.join(match_result.matched_skills[:10]) or 'None'}
Missing Required: {', '.join(match_result.missing_required_skills) or 'None'}
Additional Skills: {', '.join(match_result.additional_skills[:5]) or 'None'}

STRENGTHS: {', '.join(match_result.strengths) if match_result.strengths else 'N/A'}
CONCERNS: {', '.join(match_result.concerns) if match_result.concerns else 'N/A'}

RECOMMENDATION: {ranking['recommendation'].replace('_', ' ').title()}

Write a professional 1-paragraph evaluation summary suitable for hiring managers."""

        report = await self.think(
            prompt=prompt,
            system_prompt="You are an HR professional writing formal candidate evaluations.",
            temperature=0.3
        )
        
        # Build full report
        full_report = f"""
═══════════════════════════════════════════════════════════════
                    CANDIDATE EVALUATION REPORT
═══════════════════════════════════════════════════════════════

CANDIDATE: {resume.name or 'Unknown'}
POSITION:  {job.title}
DATE:      {datetime.now().strftime('%Y-%m-%d')}

───────────────────────────────────────────────────────────────
                         SCORES
───────────────────────────────────────────────────────────────
Overall Score:     {match_result.overall_score:.1f}/100
Skills Score:      {match_result.skill_score:.1f}/100
Experience Score:  {match_result.experience_score:.1f}/100
Education Score:   {match_result.education_score:.1f}/100
Semantic Match:    {match_result.semantic_similarity * 100:.1f}%

───────────────────────────────────────────────────────────────
                         RANKING
───────────────────────────────────────────────────────────────
Rank: #{ranking['rank']}
Recommendation: {ranking['recommendation'].replace('_', ' ').upper()}

───────────────────────────────────────────────────────────────
                         ANALYSIS
───────────────────────────────────────────────────────────────
{report}

───────────────────────────────────────────────────────────────
                     DETAILED BREAKDOWN
───────────────────────────────────────────────────────────────

MATCHED SKILLS ({len(match_result.matched_skills)}):
{chr(10).join('  • ' + s for s in match_result.matched_skills[:10]) or '  None'}

MISSING REQUIRED SKILLS ({len(match_result.missing_required_skills)}):
{chr(10).join('  • ' + s for s in match_result.missing_required_skills) or '  None'}

KEY STRENGTHS:
{chr(10).join('  • ' + s for s in match_result.strengths) if match_result.strengths else '  N/A'}

KEY CONCERNS:
{chr(10).join('  • ' + s for s in match_result.concerns) if match_result.concerns else '  None identified'}

═══════════════════════════════════════════════════════════════
"""
        
        return full_report


# Global ranking agent instance
ranking_agent = RankingAgent()
