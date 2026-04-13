"""Candidate data models."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class Education(BaseModel):
    """Education information."""
    degree: Optional[str] = None
    institution: Optional[str] = None
    field: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[float] = None


class Experience(BaseModel):
    """Work experience information."""
    title: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    duration_months: int = 0
    is_current: bool = False


class ResumeData(BaseModel):
    """Extracted resume data."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = None
    
    def get_total_experience_years(self) -> float:
        """Calculate total years of experience."""
        total_years = 0.0
        for exp in self.experience:
            # First check duration_months (set by our parser)
            if exp.duration_months > 0:
                total_years += exp.duration_months / 12.0
            elif exp.start_date:
                try:
                    start = datetime.strptime(exp.start_date, "%Y-%m")
                    if exp.is_current or not exp.end_date:
                        end = datetime.now()
                    else:
                        end = datetime.strptime(exp.end_date, "%Y-%m")
                    years = (end - start).days / 365.25
                    total_years += max(0, years)
                except:
                    pass
        return round(total_years, 1)


class Candidate(BaseModel):
    """Complete candidate model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resume_data: ResumeData
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None  # Cache embedding to avoid recalculation
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CandidateCreate(BaseModel):
    """Model for creating a new candidate."""
    file_name: str
    file_content: Optional[bytes] = None


class CandidateResponse(BaseModel):
    """API response model for candidate."""
    id: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    skills: List[str]
    total_experience_years: float
    education_summary: str
    created_at: datetime
    
    @classmethod
    def from_candidate(cls, candidate: Candidate) -> "CandidateResponse":
        """Create response from candidate model."""
        resume = candidate.resume_data
        
        # Create education summary
        edu_summary = ""
        if resume.education:
            latest_edu = resume.education[0]
            degree = latest_edu.degree or ""
            field = latest_edu.field or latest_edu.field_of_study or ""
            institution = latest_edu.institution or ""
            
            if degree and field:
                edu_summary = f"{degree} in {field}"
            elif degree:
                edu_summary = degree
            if institution:
                edu_summary += f" from {institution}" if edu_summary else institution
        
        return cls(
            id=candidate.id,
            name=resume.name,
            email=resume.email,
            phone=resume.phone,
            skills=resume.skills,
            total_experience_years=resume.get_total_experience_years(),
            education_summary=edu_summary,
            created_at=candidate.created_at
        )
