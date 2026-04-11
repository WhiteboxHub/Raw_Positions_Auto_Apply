"""Email prompt builder."""

import json
import logging
from typing import Optional
from src.models.resume import ResumeData

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Build email generation prompts for LLM."""
    
    def __init__(self, resume_data: ResumeData, user_name: str):
        """
        Initialize prompt builder.
        
        Args:
            resume_data: Candidate resume data
            user_name: Candidate name
        """
        self.resume_data = resume_data
        self.user_name = user_name
        self.companies_in_resume = self._extract_companies_from_resume()
    
    def _extract_social_networks(self) -> dict:
        """
        Extract LinkedIn and GitHub URLs from resume.
        
        Returns:
            Dict with 'linkedin_url' and 'github_url' if present
        """
        social_networks = {}
        try:
            raw_data = self.resume_data.raw_data or {}
            cv = raw_data.get("cv", {})
            networks = cv.get("social_networks", [])
            
            if isinstance(networks, list):
                for network in networks:
                    if isinstance(network, dict):
                        network_name = network.get("network", "").lower()
                        username = network.get("username", "")
                        
                        if network_name == "linkedin" and username:
                            social_networks["linkedin_url"] = f"https://linkedin.com/in/{username}"
                        elif network_name == "github" and username:
                            social_networks["github_url"] = f"https://github.com/{username}"
            
            if social_networks:
                logger.info(f"Extracted social networks: {list(social_networks.keys())}")
        except Exception as e:
            logger.warning(f"Could not extract social networks: {e}")
        
        return social_networks
    
    def _extract_company_experiences(self) -> dict:
        """
        Extract company experiences with specific technologies and responsibilities.
        
        Returns:
            Dict mapping company name to {position, highlights, years}
        """
        experiences = {}
        try:
            raw_data = self.resume_data.raw_data or {}
            cv = raw_data.get("cv", {})
            sections = cv.get("sections", {})
            experience = sections.get("experience", [])
            
            if isinstance(experience, list):
                for exp in experience:
                    if isinstance(exp, dict):
                        company = exp.get("company")
                        if company:
                            position = exp.get("position", "")
                            highlights = exp.get("highlights", [])
                            date_info = exp.get("date", {})
                            
                            end_date = date_info.get("end_date")
                            is_current = end_date is None or str(end_date).strip().lower() == "present"
                            
                            experiences[company] = {
                                "position": position,
                                "highlights": highlights,
                                "start_date": date_info.get("start_date", ""),
                                "end_date": end_date,
                                "is_current": is_current
                            }
            
            logger.info(f"Extracted {len(experiences)} company experiences from resume")
        except Exception as e:
            logger.warning(f"Could not extract company experiences: {e}")
        
        return experiences
    
    def _extract_companies_from_resume(self) -> list:
        """
        Extract company names from resume dynamically.
        
        Returns:
            List of company names from most recent to oldest
        """
        companies = []
        try:
            experiences = self._extract_company_experiences()
            companies = list(experiences.keys())
            logger.info(f"Extracted companies from resume (in order): {companies}")
        except Exception as e:
            logger.warning(f"Could not extract companies from resume: {e}")
        
        return companies
    
    def build_prompt(
        self,
        job_description: str,
        recruiter_name: Optional[str] = None,
        company_from_email: Optional[str] = None
    ) -> str:
        """
        Build bulletproof prompt for LLM email generation.
        
        Args:
            job_description: Job posting from CSV
            recruiter_name: Extracted recruiter name (optional)
            company_from_email: Company extracted from email domain (fallback)
            
        Returns:
            Complete prompt for LLM
        """
        # Build dynamic technology mapping from actual resume (1 highlight per company to save tokens)
        company_experiences = self._extract_company_experiences()
        tech_mapping = ""
        if company_experiences:
            tech_mapping = "CANDIDATE EXPERIENCE OPTIONS:\n"
            for company, details in company_experiences.items():
                status = "CURRENT ROLE" if details.get("is_current") else "PAST ROLE"
                highlight = details['highlights'][0] if details['highlights'] else ""
                tech_mapping += f"- {company} [{status}]: {details['position']}. Key work: {highlight}\n"
        
        # Extract social network URLs
        social_networks = self._extract_social_networks()
        linkedin_url = social_networks.get("linkedin_url", "")
        github_url = social_networks.get("github_url", "")
        
        # Build social links section for email - MANDATORY if present
        social_links_for_email = ""
        if linkedin_url or github_url:
            social_links_for_email = "Social Media Links (MANDATORY - must include in email):\n"
            if linkedin_url:
                social_links_for_email += f"{linkedin_url}\n"
            if github_url:
                social_links_for_email += f"{github_url}\n"
        
        resume_str = json.dumps(self.resume_data.raw_data, indent=2) if self.resume_data.raw_data else "Resume data not available"
        greeting = f"Dear {recruiter_name}," if recruiter_name else "Dear Hiring Manager,"

        prompt = f"""Task: Draft a professional job application email based strictly on the provided candidate data and job description.

REQUIRED PERSONA: Professional Email Drafter. Use a direct, polite, and factual tone.

INSTRUCTIONS:
1. BREVITY: Keep the entire email body under 75 words.
2. SOURCE MATERIAL: Use only the candidate's verified experience provided below. Do not invent skills or history.
3. CONTEXT: Focus on the matching technologies between the candidate and the job posting.
4. TARGET: Direct the application to {company_from_email if company_from_email else 'the company'}.
5. GREETING: Use the greeting exactly as provided below.
6. EXPERIENCE: If mentioning total years of experience, you MUST state exactly "{self.resume_data.total_experience}" as provided in the resume. Never mirror the job posting's required years.

JOB POSTING:
{job_description}

{tech_mapping}

REQUIRED EMAIL FORMAT:
Output strictly in this format:

SUBJECT: Application for [Job Title] at [Company Name] (MANDATORY: you must include 'at [Company Name]')

BODY:
{greeting}

[Para 1: Express interest. Mention 1 or 2 matching technologies. (Max 2 sentences)]

[Para 2: State factual history. 
If [CURRENT ROLE]: "In my current role at [COMPANY NAME]..." 
If [PAST ROLE]: "During my time at [COMPANY NAME]..." 
(Max 2 sentences)]

[Para 3: Close professionally. (1 sentence ONLY)]

I have attached my resume for your reference.

Regards,
{self.user_name}

FINAL CONSTRAINTS:
- No placeholders like [Job Title] in the final output.
- Total body word count < 75.
- Output the labels "SUBJECT:" and "BODY:"!

NOW DRAFT THE EMAIL:"""

        return prompt

    def build_simple_prompt(
        self,
        job_description: str,
        recruiter_name: Optional[str] = None,
        company_from_email: Optional[str] = None
    ) -> str:
        """
        Build a shorter, simpler prompt for LLM retry attempt 2.
        Fewer instructions = less to confuse the model.
        """
        greeting = f"Dear {recruiter_name}," if recruiter_name else "Dear Hiring Manager,"
        company = company_from_email or "the company"

        # Get top 3 skills only
        skills = []
        if self.resume_data.skills:
            skills = self.resume_data.skills[:3]
        skills_str = ", ".join(skills) if skills else "software development"

        prompt = f"""Task: Write a short generalized professional job application email.

STRATEGY: Focus on the candidate's core profile and top skills. Keep it brief. If a direct match is complex, focus on the profile's strongest overlap with the role.

Recruiter greeting: {greeting}
Company: {company}
Candidate name: {self.user_name}
Candidate total experience: {self.resume_data.total_experience} (Use this exact value if mentioning years of experience)
Candidate top skills: {skills_str}

Job posting context:
{job_description[:500]}

REQUIRED FORMAT:
SUBJECT: Application for [Job Title] at {company} (MANDATORY: must include 'at {company}')
BODY:
{greeting}

<2-3 sentence email body emphasizing core profile and interest in {company}>

I have attached my resume for your reference.

Regards,
{self.user_name}

WRITE THE EMAIL NOW:"""

        return prompt

    def build_minimal_prompt(
        self,
        job_description: str,
        company_from_email: Optional[str] = None
    ) -> str:
        """
        Build a bare-bones prompt for LLM retry attempt 3.
        Absolute minimum — hardest to fail structurally.
        """
        company = company_from_email or "the company"
        name = self.user_name

        prompt = f"""Task: Generate a 3-sentence job application email.

Draft from: {name}
Total Experience: {self.resume_data.total_experience}
To: {company}

Job snippet: {job_description[:200]}

Required Output format (use these exact labels):
SUBJECT: Application for [Job Title] from {name} at {company} (MANDATORY: must include 'at {company}')
BODY:
Dear Hiring Manager,

<3 sentences expressing interest and skills>

Regards,
{name}"""

        return prompt
