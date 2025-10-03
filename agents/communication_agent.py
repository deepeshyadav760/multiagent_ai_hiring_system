from crewai import Agent
from tools.email_tool import email_tool
from tools.database_tool import database_tool
from utils.logger import log
from langchain_groq import ChatGroq
from config.settings import settings
from typing import Dict


class CommunicationAgent:
    """Agent responsible for candidate communication"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL,
            temperature=0.7
        )
        
        self.agent = Agent(
            role="Candidate Communication Specialist",
            goal="Communicate effectively with candidates throughout the recruitment process",
            backstory="""You are a professional communicator who handles all candidate 
            interactions with empathy and clarity. You send timely notifications, interview 
            invitations, follow-ups, and maintain positive candidate experience throughout 
            the recruitment journey.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[email_tool, database_tool]
        )
    
    def send_application_confirmation(self, candidate_email: str) -> Dict:
        """Send application received confirmation
        
        Args:
            candidate_email: Candidate's email
            
        Returns:
            Email sending result
        """
        try:
            # Get candidate info
            candidate_result = database_tool._run(
                action="find_one",
                collection="candidates",
                query={"email": candidate_email}
            )
            
            candidate = candidate_result.get("document")
            if not candidate:
                return {"success": False, "error": "Candidate not found"}
            
            # Send confirmation email
            result = email_tool._run(
                action="send_confirmation",
                to_email=candidate_email,
                candidate_name=candidate.get("name", "Candidate")
            )
            
            log.info(f"Sent confirmation email to {candidate_email}")
            return result
            
        except Exception as e:
            log.error(f"Error sending confirmation: {e}")
            return {"success": False, "error": str(e)}
    
    def send_interview_invitation(
        self,
        candidate_email: str,
        job_id: str,
        interview_time: str,
        meeting_link: str = None
    ) -> Dict:
        """Send interview invitation
        
        Args:
            candidate_email: Candidate's email
            job_id: Job ID
            interview_time: Interview time
            meeting_link: Meeting link (optional)
            
        Returns:
            Email sending result
        """
        try:
            # Get candidate info
            candidate_result = database_tool._run(
                action="find_one",
                collection="candidates",
                query={"email": candidate_email}
            )
            candidate = candidate_result.get("document")
            
            # Get job info
            job = database_tool.get_job_by_id(job_id)
            
            if not candidate or not job:
                return {"success": False, "error": "Candidate or job not found"}
            
            # Send invitation email
            result = email_tool._run(
                action="send_interview_invitation",
                to_email=candidate_email,
                candidate_name=candidate.get("name", "Candidate"),
                job_title=job.get("title", "Position"),
                interview_time=interview_time,
                meeting_link=meeting_link or ""
            )
            
            log.info(f"Sent interview invitation to {candidate_email} for {job.get('title')}")
            return result
            
        except Exception as e:
            log.error(f"Error sending interview invitation: {e}")
            return {"success": False, "error": str(e)}
    
    def send_rejection_notice(self, candidate_email: str, job_id: str) -> Dict:
        """Send rejection notification
        
        Args:
            candidate_email: Candidate's email
            job_id: Job ID
            
        Returns:
            Email sending result
        """
        try:
            # Get candidate info
            candidate_result = database_tool._run(
                action="find_one",
                collection="candidates",
                query={"email": candidate_email}
            )
            candidate = candidate_result.get("document")
            
            # Get job info if not GENERAL
            job_title = "Position"
            if job_id != "GENERAL":
                job = database_tool.get_job_by_id(job_id)
                if job:
                    job_title = job.get("title", "Position")
            
            if not candidate:
                return {"success": False, "error": "Candidate not found"}
            
            # Update candidate status to rejected
            database_tool._run(
                action="update",
                collection="candidates",
                query={"email": candidate_email},
                data={"status": "rejected"}
            )
            
            # Send rejection email
            result = email_tool._run(
                action="send_rejection",
                to_email=candidate_email,
                candidate_name=candidate.get("name", "Candidate"),
                job_title=job_title
            )
            
            log.info(f"Sent rejection notice to {candidate_email} for {job_title}")
            return result
            
        except Exception as e:
            log.error(f"Error sending rejection: {e}")
            return {"success": False, "error": str(e)}
    
    def send_follow_up(self, candidate_email: str, message: str) -> Dict:
        """Send follow-up message
        
        Args:
            candidate_email: Candidate's email
            message: Follow-up message
            
        Returns:
            Email sending result
        """
        try:
            # Get candidate info
            candidate_result = database_tool._run(
                action="find_one",
                collection="candidates",
                query={"email": candidate_email}
            )
            candidate = candidate_result.get("document")
            
            if not candidate:
                return {"success": False, "error": "Candidate not found"}
            
            # Send follow-up email
            result = email_tool._run(
                action="send_follow_up",
                to_email=candidate_email,
                candidate_name=candidate.get("name", "Candidate"),
                message=message
            )
            
            log.info(f"Sent follow-up to {candidate_email}")
            return result
            
        except Exception as e:
            log.error(f"Error sending follow-up: {e}")
            return {"success": False, "error": str(e)}
    
    def send_interview_reminder(
        self,
        candidate_email: str,
        interview_time: str,
        meeting_link: str = None
    ) -> Dict:
        """Send interview reminder
        
        Args:
            candidate_email: Candidate's email
            interview_time: Interview time
            meeting_link: Meeting link (optional)
            
        Returns:
            Email sending result
        """
        try:
            # Get candidate info
            candidate_result = database_tool._run(
                action="find_one",
                collection="candidates",
                query={"email": candidate_email}
            )
            candidate = candidate_result.get("document")
            
            if not candidate:
                return {"success": False, "error": "Candidate not found"}
            
            # Send reminder email
            result = email_tool._run(
                action="send_reminder",
                to_email=candidate_email,
                candidate_name=candidate.get("name", "Candidate"),
                interview_time=interview_time,
                meeting_link=meeting_link or ""
            )
            
            log.info(f"Sent interview reminder to {candidate_email}")
            return result
            
        except Exception as e:
            log.error(f"Error sending reminder: {e}")
            return {"success": False, "error": str(e)}


# Create agent instance
communication_agent = CommunicationAgent()