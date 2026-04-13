"""RAG Pipeline for intelligent resume-job matching."""

import logging
from typing import List, Dict, Any, Optional

from app.services.usf_client import usf_client
from app.services.vector_store import vector_store
from app.models.candidate import Candidate, ResumeData
from app.models.job import JobDescription

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG-based pipeline for semantic matching and analysis."""
    
    def __init__(self):
        self.usf_client = usf_client
        self.vector_store = vector_store
    
    async def index_candidate(self, candidate: Candidate) -> bool:
        """
        Index a candidate in the vector store for semantic search.
        
        Args:
            candidate: Candidate to index
            
        Returns:
            Success status
        """
        resume = candidate.resume_data
        
        # Create rich text representation for embedding
        text_parts = []
        
        if resume.name:
            text_parts.append(f"Name: {resume.name}")
        
        if resume.summary:
            text_parts.append(f"Summary: {resume.summary}")
        
        if resume.skills:
            text_parts.append(f"Skills: {', '.join(resume.skills)}")
        
        for exp in resume.experience:
            exp_text = f"Experience: {exp.job_title or ''} at {exp.company or ''}"
            if exp.description:
                exp_text += f" - {exp.description}"
            text_parts.append(exp_text)
        
        for edu in resume.education:
            edu_text = f"Education: {edu.degree or ''} in {edu.field_of_study or ''} from {edu.institution or ''}"
            text_parts.append(edu_text)
        
        if resume.certifications:
            text_parts.append(f"Certifications: {', '.join(resume.certifications)}")
        
        # Add raw text as fallback
        if resume.raw_text:
            text_parts.append(resume.raw_text[:2000])  # Limit raw text length
        
        full_text = "\n".join(text_parts)
        
        # Prepare metadata
        metadata = {
            "name": resume.name or "",
            "email": resume.email or "",
            "skills_count": len(resume.skills),
            "experience_years": resume.get_total_experience_years(),
            "has_education": len(resume.education) > 0,
            "file_name": candidate.file_name or ""
        }
        
        # Get or compute embedding
        embedding = candidate.embedding
        if not embedding:
            logger.info(f"Computing new embedding for candidate {candidate.id}")
            embeddings = await self.usf_client.get_embeddings([full_text[:2000]])
            embedding = embeddings[0] if embeddings else None
            # Cache it in the candidate object
            candidate.embedding = embedding
        else:
            logger.info(f"Using cached embedding for candidate {candidate.id}")
        
        # Add to vector store with embedding
        success = await self.vector_store.add_candidate(
            candidate_id=candidate.id,
            resume_text=full_text,
            metadata=metadata,
            embedding=embedding
        )
        
        # Also index skills
        if resume.skills:
            await self.vector_store.add_skills(resume.skills)
        
        return success
    
    async def index_job(self, job: JobDescription) -> bool:
        """
        Index a job description in the vector store.
        
        Args:
            job: Job description to index
            
        Returns:
            Success status
        """
        # Create rich text representation
        text_parts = [
            f"Job Title: {job.title}",
            f"Description: {job.description}"
        ]
        
        if job.department:
            text_parts.append(f"Department: {job.department}")
        
        if job.responsibilities:
            text_parts.append(f"Responsibilities: {', '.join(job.responsibilities)}")
        
        required_skills = job.get_all_required_skills()
        if required_skills:
            text_parts.append(f"Required Skills: {', '.join(required_skills)}")
        
        preferred_skills = job.get_all_preferred_skills()
        if preferred_skills:
            text_parts.append(f"Preferred Skills: {', '.join(preferred_skills)}")
        
        if job.required_education:
            text_parts.append(f"Required Education: {job.required_education}")
        
        text_parts.append(f"Experience Required: {job.min_experience_years}+ years")
        
        full_text = "\n".join(text_parts)
        
        # Prepare metadata
        metadata = {
            "title": job.title,
            "department": job.department or "",
            "location": job.location or "",
            "employment_type": job.employment_type,
            "min_experience_years": job.min_experience_years,
            "is_active": job.is_active
        }
        
        # Add to vector store
        success = await self.vector_store.add_job(
            job_id=job.id,
            job_text=full_text,
            metadata=metadata
        )
        
        # Index required and preferred skills
        all_skills = required_skills + preferred_skills
        if all_skills:
            await self.vector_store.add_skills(all_skills)
        
        return success
    
    async def find_matching_candidates(
        self,
        job: JobDescription,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find candidates that match a job description.
        
        Args:
            job: Job description to match against
            top_k: Number of candidates to return
            
        Returns:
            List of matching candidates with relevance scores
        """
        # Build search query from job requirements
        query_parts = [
            f"Looking for {job.title}",
            job.description
        ]
        
        required_skills = job.get_all_required_skills()
        if required_skills:
            query_parts.append(f"Must have skills: {', '.join(required_skills)}")
        
        preferred_skills = job.get_all_preferred_skills()
        if preferred_skills:
            query_parts.append(f"Nice to have skills: {', '.join(preferred_skills)}")
        
        if job.min_experience_years > 0:
            query_parts.append(f"At least {job.min_experience_years} years of experience")
        
        query = " ".join(query_parts)
        
        # Search vector store
        candidates = await self.vector_store.search_candidates(
            query=query,
            n_results=top_k * 2  # Get more for reranking
        )
        
        if not candidates:
            return []
        
        # Rerank using USF API
        candidate_texts = [c.get("document", "") for c in candidates]
        reranked = await self.usf_client.rerank(
            query=query,
            texts=candidate_texts,
            top_k=top_k
        )
        
        # Map reranked results back to candidates
        results = []
        for item in reranked:
            idx = item.get("index", 0)
            if idx < len(candidates):
                candidate = candidates[idx]
                candidate["rerank_score"] = item.get("score", 0)
                results.append(candidate)
        
        return results
    
    async def find_matching_jobs(
        self,
        candidate: Candidate,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find jobs that match a candidate's profile.
        
        Args:
            candidate: Candidate to match
            top_k: Number of jobs to return
            
        Returns:
            List of matching jobs with relevance scores
        """
        resume = candidate.resume_data
        
        # Build search query from candidate profile
        query_parts = []
        
        if resume.summary:
            query_parts.append(resume.summary)
        
        if resume.skills:
            query_parts.append(f"Skills: {', '.join(resume.skills)}")
        
        for exp in resume.experience[:3]:  # Last 3 jobs
            if exp.job_title:
                query_parts.append(f"Experience as {exp.job_title}")
        
        if resume.education:
            edu = resume.education[0]
            query_parts.append(f"Education: {edu.degree} in {edu.field_of_study}")
        
        query = " ".join(query_parts) if query_parts else resume.raw_text[:1000]
        
        # Search vector store
        jobs = await self.vector_store.search_jobs(
            query=query,
            n_results=top_k * 2
        )
        
        if not jobs:
            return []
        
        # Rerank using USF API
        job_texts = [j.get("document", "") for j in jobs]
        reranked = await self.usf_client.rerank(
            query=query,
            texts=job_texts,
            top_k=top_k
        )
        
        # Map reranked results back to jobs
        results = []
        for item in reranked:
            idx = item.get("index", 0)
            if idx < len(jobs):
                job = jobs[idx]
                job["rerank_score"] = item.get("score", 0)
                results.append(job)
        
        return results
    
    async def analyze_candidate_job_fit(
        self,
        candidate: Candidate,
        job: JobDescription
    ) -> Dict[str, Any]:
        """
        Perform detailed analysis of candidate-job fit.
        
        Args:
            candidate: Candidate to analyze
            job: Job to match against
            
        Returns:
            Detailed fit analysis
        """
        resume = candidate.resume_data
        
        # Quick skill-based pre-screening to avoid expensive API calls
        candidate_skills = set(s.lower() for s in resume.skills)
        required_skills = set(job.get_all_required_skills())
        
        # If candidate has < 30% required skills, skip semantic similarity (save API call)
        quick_skill_ratio = len(candidate_skills & required_skills) / len(required_skills) if required_skills else 1.0
        
        if quick_skill_ratio < 0.3:
            # Low skill match - use fallback similarity to save time
            semantic_similarity = 0.3
            logger.info(f"Skipping semantic API call for low-skill candidate (ratio: {quick_skill_ratio:.2f})")
        else:
            # Calculate semantic similarity (expensive API call)
            candidate_text = self._create_candidate_text(resume)
            job_text = self._create_job_text(job)
            
            semantic_similarity = await self.vector_store.get_semantic_similarity(
                candidate_text, job_text
            )
        
        # Skill matching
        candidate_skills = set(s.lower() for s in resume.skills)
        required_skills = set(job.get_all_required_skills())
        preferred_skills = set(job.get_all_preferred_skills())
        
        matched_required = candidate_skills & required_skills
        missing_required = required_skills - candidate_skills
        matched_preferred = candidate_skills & preferred_skills
        missing_preferred = preferred_skills - candidate_skills
        additional_skills = candidate_skills - required_skills - preferred_skills
        
        # Experience analysis
        candidate_exp_years = resume.get_total_experience_years()
        exp_gap = candidate_exp_years - job.min_experience_years
        
        # Calculate scores
        skill_score = 0
        if required_skills:
            # Base score from required skills (70% weight)
            required_match_ratio = len(matched_required) / len(required_skills)
            skill_score = required_match_ratio * 70
        else:
            # No required skills specified, give base score
            skill_score = 50
        
        if preferred_skills:
            # Bonus from preferred skills (30% weight)
            preferred_match_ratio = len(matched_preferred) / len(preferred_skills)
            skill_score += preferred_match_ratio * 30
        elif not required_skills:
            # No skills requirements at all
            skill_score = 70 if len(candidate_skills) > 3 else 50
        
        # Experience score - more forgiving calculation
        if job.min_experience_years == 0:
            exp_score = 80  # No experience required
        elif candidate_exp_years >= job.min_experience_years:
            # Meets or exceeds requirement
            exp_score = min(100, 80 + (exp_gap * 5))
        else:
            # Below requirement - partial credit
            ratio = candidate_exp_years / job.min_experience_years if job.min_experience_years > 0 else 1
            exp_score = max(30, ratio * 80)
        
        # Education score - check for degree presence
        education_score = 50  # Default score
        if resume.education:
            edu = resume.education[0]
            edu_degree = (edu.degree or "").lower()
            edu_field = (edu.field or edu.field_of_study or "").lower()
            edu_text = f"{edu_degree} {edu_field}"
            
            # Higher degree = higher score
            if "phd" in edu_text or "doctorate" in edu_text:
                education_score = 100
            elif "master" in edu_text or "mba" in edu_text:
                education_score = 90
            elif "bachelor" in edu_text:
                education_score = 80
            else:
                education_score = 60
            
            # Check if job requires specific education
            if job.required_education:
                if job.required_education.lower() in edu_text:
                    education_score = min(100, education_score + 10)
        
        # Weighted overall score
        overall_score = (
            skill_score * job.skill_weight +
            exp_score * job.experience_weight +
            education_score * job.education_weight +
            semantic_similarity * 100 * 0.2  # Add semantic similarity weight
        )
        
        return {
            "semantic_similarity": semantic_similarity,
            "skill_score": skill_score,
            "experience_score": exp_score,
            "education_score": education_score,
            "overall_score": overall_score,
            "matched_required_skills": list(matched_required),
            "missing_required_skills": list(missing_required),
            "matched_preferred_skills": list(matched_preferred),
            "missing_preferred_skills": list(missing_preferred),
            "additional_skills": list(additional_skills),
            "experience_years": candidate_exp_years,
            "experience_gap": exp_gap
        }
    
    async def generate_match_insights(
        self,
        candidate: Candidate,
        job: JobDescription,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AI-powered insights about a candidate-job match.
        
        Args:
            candidate: Candidate
            job: Job description
            analysis: Previous analysis results
            
        Returns:
            AI-generated insights
        """
        # Generate data-driven insights directly (skip slow AI API call)
        resume = candidate.resume_data
        matched = analysis.get('matched_required_skills', [])
        missing = analysis.get('missing_required_skills', [])
        score = analysis.get('overall_score', 0)
        
        strengths = []
        concerns = []
        
        # Build strengths based on actual data
        if matched:
            strengths.append(f"Matches key skills: {', '.join(matched[:3])}")
        if analysis.get('experience_score', 0) >= 80:
            strengths.append(f"Excellent experience level ({resume.get_total_experience_years()} years)")
        elif analysis.get('experience_score', 0) >= 70:
            strengths.append(f"Good experience level ({resume.get_total_experience_years()} years)")
        if analysis.get('education_score', 0) >= 70:
            strengths.append("Meets education requirements")
        if analysis.get('semantic_similarity', 0) >= 0.7:
            strengths.append("Strong semantic match with job requirements")
        
        # Build concerns based on actual data
        if missing:
            concerns.append(f"Missing required skills: {', '.join(missing[:3])}")
        if analysis.get('experience_score', 0) < 70:
            concerns.append("Experience level below requirements")
        if analysis.get('skill_score', 0) < 60:
            concerns.append("Significant skill gaps identified")
        if analysis.get('education_score', 0) < 50:
            concerns.append("Education requirements not fully met")
        
        # Ensure we have exactly 3 items
        if not strengths:
            strengths.append("Some relevant qualifications")
        while len(strengths) < 3:
            strengths.append("Relevant background for this role")
        
        if not concerns:
            concerns.append("Minor areas for development")
        while len(concerns) < 3:
            concerns.append("Further evaluation recommended")
        
        # Generate recommendation based on score
        if score >= 85:
            recommendation = "Highly recommended - excellent match"
        elif score >= 75:
            recommendation = "Recommended - strong match"
        elif score >= 60:
            recommendation = "Good candidate - review detailed profile"
        elif score >= 40:
            recommendation = "Consider with reservations - has some gaps"
        else:
            recommendation = "Does not meet minimum requirements"
        
        logger.info(f"Generated data-driven insights (score: {score:.1f})")
        return {
            "strengths": strengths[:3],
            "concerns": concerns[:3],
            "recommendation": recommendation
        }
    
    def _create_candidate_text(self, resume: ResumeData) -> str:
        """Create searchable text from resume."""
        parts = []
        if resume.summary:
            parts.append(resume.summary)
        if resume.skills:
            parts.append(f"Skills: {', '.join(resume.skills)}")
        for exp in resume.experience:
            parts.append(f"{exp.job_title} at {exp.company}: {exp.description or ''}")
        return " ".join(parts) or resume.raw_text[:1000]
    
    def _create_job_text(self, job: JobDescription) -> str:
        """Create searchable text from job description."""
        parts = [
            job.title,
            job.description,
            f"Required skills: {', '.join(job.get_all_required_skills())}",
            f"Preferred skills: {', '.join(job.get_all_preferred_skills())}"
        ]
        if job.responsibilities:
            parts.append(f"Responsibilities: {', '.join(job.responsibilities)}")
        return " ".join(parts)


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()
