"""Resume data loading and handling."""

import json
import logging
from pathlib import Path
from typing import Optional

from src.models.resume import Resume, ResumeData

logger = logging.getLogger(__name__)


class ResumeHandler:
    """Handle resume data loading and extraction."""
    
    @staticmethod
    def load_resume(json_path: str) -> Resume:
        """
        Load resume from JSON file.
        
        Args:
            json_path: Path to resume.json
            
        Returns:
            Resume object with data if loaded, empty if failed
        """
        resume_path = Path(json_path)
        resume = Resume(json_path=json_path)
        
        if not resume_path.exists():
            logger.warning(f"Resume file not found: {json_path}")
            return resume
        
        try:
            with open(resume_path, "r") as f:
                raw_data = json.load(f)
            
            name = ResumeHandler._extract_name(raw_data)
            email = ResumeHandler._extract_email(raw_data)
            skills = ResumeHandler._extract_skills(raw_data)
            industry = ResumeHandler._extract_industry(raw_data)
            total_experience = raw_data.get("cv", {}).get("total_experience", "")
            
            resume.data = ResumeData(
                name=name,
                email=email,
                total_experience=total_experience,
                industry=industry,
                skills=skills,
                raw_data=raw_data
            )
            
            logger.info(f"Loaded resume: {json_path} (Name: {name})")
            return resume
            
        except Exception as e:
            logger.error(f"Failed to load resume: {e}")
            return resume
    
    @staticmethod
    def _extract_name(resume_data: dict) -> str:
        """Extract candidate name from resume."""
        try:
            name = resume_data.get("cv", {}).get("name", "")
            if name:
                return name
        except Exception as e:
            logger.debug(f"Failed to extract name: {e}")
        
        return "Applicant"

    @staticmethod
    def _extract_email(resume_data: dict) -> str:
        """Extract candidate email from resume."""
        try:
            email = resume_data.get("cv", {}).get("email", "")
            if email:
                return email
        except Exception as e:
            logger.debug(f"Failed to extract email: {e}")
        
        return "Unknown"
    
    @staticmethod
    def _extract_skills(resume_data: dict) -> list[str]:
        """Extract skills list from resume."""
        try:
            skills = resume_data.get("skills", [])
            if isinstance(skills, list):
                return skills
        except Exception as e:
            logger.debug(f"Failed to extract skills: {e}")
        
        return []
    @staticmethod
    def _extract_industry(resume_data: dict) -> str:
        """Extract professional industry/field from resume."""
        try:
            cv = resume_data.get("cv", {})
            sections = cv.get("sections", {})
            
            # 1. Try most recent job position
            experience = sections.get("experience", [])
            if experience and isinstance(experience, list):
                # Assume first one is most recent
                most_recent = experience[0]
                position = most_recent.get("position", "")
                if position:
                    # Clean up position to get a "field"
                    # e.g., "Senior AI Engineer" -> "AI Engineering"
                    field = position.replace("Senior ", "").replace("Junior ", "").replace("Lead ", "")
                    if "Engineer" in field:
                        field = field.replace("Engineer", "Engineering")
                    elif "Developer" in field:
                        field = field.replace("Developer", "Development")
                    return field
            
            # 2. Try education area
            education = sections.get("education", [])
            if education and isinstance(education, list):
                area = education[0].get("area", "")
                if area:
                    return area
        except Exception as e:
            logger.debug(f"Failed to extract industry: {e}")
            
        return "Software Engineering"
