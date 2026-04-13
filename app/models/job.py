"""Job description data models."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class SkillRequirement(BaseModel):
    """Skill requirement with importance level."""
    skill: str
    importance: str = "required"  # required, preferred, nice_to_have
    min_years: Optional[float] = None


class JobDescription(BaseModel):
    """Complete job description model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: str = "full-time"  # full-time, part-time, contract, internship
    remote_policy: str = "on-site"  # on-site, remote, hybrid
    
    # Requirements
    description: str
    responsibilities: List[str] = Field(default_factory=list)
    required_skills: List[SkillRequirement] = Field(default_factory=list)
    preferred_skills: List[SkillRequirement] = Field(default_factory=list)
    min_experience_years: float = 0.0
    max_experience_years: Optional[float] = None
    required_education: Optional[str] = None
    required_certifications: List[str] = Field(default_factory=list)
    
    # Compensation
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "USD"
    
    # Matching weights (for ranking algorithm)
    skill_weight: float = 0.4
    experience_weight: float = 0.3
    education_weight: float = 0.2
    certification_weight: float = 0.1
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None  # Cache embedding to avoid recalculation
    
    def get_all_required_skills(self) -> List[str]:
        """Get list of all required skill names."""
        return [s.skill.lower() for s in self.required_skills]
    
    def get_all_preferred_skills(self) -> List[str]:
        """Get list of all preferred skill names."""
        return [s.skill.lower() for s in self.preferred_skills]


class JobDescriptionCreate(BaseModel):
    """Model for creating a new job description."""
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: str = "full-time"
    remote_policy: str = "on-site"
    description: str
    responsibilities: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_experience_years: float = 0.0
    max_experience_years: Optional[float] = None
    required_education: Optional[str] = None
    required_certifications: List[str] = Field(default_factory=list)
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None


class JobDescriptionResponse(BaseModel):
    """API response model for job description."""
    id: str
    title: str
    department: Optional[str]
    location: Optional[str]
    employment_type: str
    remote_policy: str
    description: str
    required_skills: List[str]
    preferred_skills: List[str]
    min_experience_years: float
    required_education: Optional[str]
    is_active: bool
    created_at: datetime
    
    @classmethod
    def from_job(cls, job: JobDescription) -> "JobDescriptionResponse":
        """Create response from job description model."""
        return cls(
            id=job.id,
            title=job.title,
            department=job.department,
            location=job.location,
            employment_type=job.employment_type,
            remote_policy=job.remote_policy,
            description=job.description,
            required_skills=job.get_all_required_skills(),
            preferred_skills=job.get_all_preferred_skills(),
            min_experience_years=job.min_experience_years,
            required_education=job.required_education,
            is_active=job.is_active,
            created_at=job.created_at
        )
