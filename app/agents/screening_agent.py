"""Screening Agent - Filters candidates based on minimum requirements."""

import logging
from typing import List, Optional

from app.agents.base_agent import BaseAgent
from app.models.candidate import Candidate
from app.models.job import JobDescription
from app.models.matching import ScreeningResult

logger = logging.getLogger(__name__)


class ScreeningAgent(BaseAgent):
    """
    Agent responsible for initial screening of candidates.
    
    Filters candidates based on:
    - Minimum experience requirements
    - Required skills presence
    - Education requirements
    - Certification requirements
    """
    
    def __init__(self):
        super().__init__(
            name="ScreeningAgent",
            description="Filters candidates based on minimum job requirements"
        )
    
    async def execute(
        self,
        candidate: Candidate,
        job: JobDescription,
        strict_mode: bool = False
    ) -> ScreeningResult:
        """
        Screen a candidate against job requirements.
        
        Args:
            candidate: Candidate to screen
            job: Job description with requirements
            strict_mode: If True, candidate must meet ALL requirements
            
        Returns:
            ScreeningResult with pass/fail status and reasons
        """
        self.log_action("Starting screening", {
            "candidate_id": candidate.id,
            "job_id": job.id
        })
        
        resume = candidate.resume_data
        met_requirements = []
        missing_requirements = []
        reasons = []
        
        # Check experience requirement
        candidate_exp = resume.get_total_experience_years()
        if candidate_exp >= job.min_experience_years:
            met_requirements.append(f"Experience: {candidate_exp:.1f} years (required: {job.min_experience_years}+)")
        else:
            missing_requirements.append(
                f"Experience: {candidate_exp:.1f} years (required: {job.min_experience_years}+)"
            )
            reasons.append(f"Insufficient experience: {candidate_exp:.1f} years vs {job.min_experience_years} required")
        
        # Check required skills
        candidate_skills = set(s.lower() for s in resume.skills)
        required_skills = set(job.get_all_required_skills())
        
        matched_skills = candidate_skills & required_skills
        missing_skills = required_skills - candidate_skills
        
        skill_match_ratio = len(matched_skills) / len(required_skills) if required_skills else 1.0
        
        if skill_match_ratio >= 0.6:  # 60% skill match threshold
            met_requirements.append(
                f"Skills: {len(matched_skills)}/{len(required_skills)} required skills"
            )
        else:
            missing_requirements.append(
                f"Skills: Only {len(matched_skills)}/{len(required_skills)} required skills"
            )
            if missing_skills:
                reasons.append(f"Missing required skills: {', '.join(list(missing_skills)[:5])}")
        
        # Check education requirement
        if job.required_education:
            education_met = self._check_education(resume, job.required_education)
            if education_met:
                met_requirements.append(f"Education: Meets requirement ({job.required_education})")
            else:
                missing_requirements.append(f"Education: {job.required_education} required")
                reasons.append(f"Education requirement not met: {job.required_education}")
        
        # Check certifications
        if job.required_certifications:
            candidate_certs = set(c.lower() for c in resume.certifications)
            required_certs = set(c.lower() for c in job.required_certifications)
            matched_certs = candidate_certs & required_certs
            
            if len(matched_certs) >= len(required_certs) * 0.5:  # 50% cert match
                met_requirements.append(
                    f"Certifications: {len(matched_certs)}/{len(required_certs)}"
                )
            else:
                missing_certs = required_certs - candidate_certs
                missing_requirements.append(
                    f"Certifications: Missing {', '.join(list(missing_certs)[:3])}"
                )
        
        # Determine pass/fail
        if strict_mode:
            passed = len(missing_requirements) == 0
        else:
            # Lenient mode: pass if experience is sufficient and at least 50% skills match
            experience_ok = candidate_exp >= job.min_experience_years * 0.8  # 80% of required
            skills_ok = skill_match_ratio >= 0.5
            passed = experience_ok and skills_ok
        
        # Generate screening notes using LLM
        screening_notes = await self._generate_screening_notes(
            candidate, job, met_requirements, missing_requirements, passed
        )
        
        result = ScreeningResult(
            candidate_id=candidate.id,
            job_id=job.id,
            passed=passed,
            reasons=reasons,
            missing_requirements=missing_requirements,
            met_requirements=met_requirements,
            screening_notes=screening_notes
        )
        
        self.log_action("Screening complete", {
            "candidate_id": candidate.id,
            "passed": passed,
            "met": len(met_requirements),
            "missing": len(missing_requirements)
        })
        
        return result
    
    def _check_education(self, resume, required_education: str) -> bool:
        """Check if candidate meets education requirements."""
        if not resume.education:
            return False
        
        required_lower = required_education.lower()
        
        # Define education hierarchy
        education_levels = {
            "high school": 1,
            "associate": 2,
            "bachelor": 3,
            "master": 4,
            "phd": 5,
            "doctorate": 5
        }
        
        # Determine required level
        required_level = 0
        for level, value in education_levels.items():
            if level in required_lower:
                required_level = value
                break
        
        # Check candidate's education
        for edu in resume.education:
            degree = (edu.degree or "").lower()
            for level, value in education_levels.items():
                if level in degree and value >= required_level:
                    return True
        
        return False
    
    async def _generate_screening_notes(
        self,
        candidate: Candidate,
        job: JobDescription,
        met: List[str],
        missing: List[str],
        passed: bool
    ) -> str:
        """Generate AI-powered screening notes."""
        prompt = f"""Generate brief screening notes for this candidate evaluation.

Candidate: {candidate.resume_data.name or 'Unknown'}
Position: {job.title}
Screening Result: {'PASSED' if passed else 'FAILED'}

Requirements Met:
{chr(10).join('- ' + m for m in met) if met else '- None'}

Requirements Missing:
{chr(10).join('- ' + m for m in missing) if missing else '- None'}

Write 2-3 sentences summarizing the screening decision. Be objective and professional."""

        notes = await self.think(
            prompt=prompt,
            system_prompt="You are an HR screening assistant providing brief, professional candidate assessments.",
            temperature=0.3
        )
        
        return notes or "Screening completed based on job requirements."
    
    async def batch_screen(
        self,
        candidates: List[Candidate],
        job: JobDescription,
        strict_mode: bool = False
    ) -> List[ScreeningResult]:
        """
        Screen multiple candidates against a job.
        
        Args:
            candidates: List of candidates to screen
            job: Job description
            strict_mode: If True, require all requirements
            
        Returns:
            List of screening results
        """
        results = []
        for candidate in candidates:
            result = await self.execute(candidate, job, strict_mode)
            results.append(result)
        return results


# Global screening agent instance
screening_agent = ScreeningAgent()
