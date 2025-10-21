# agents/orchestrator_agent.py

from crewai import Agent
from utils.logger import log
from langchain_groq import ChatGroq
from config.settings import settings
from typing import Dict
from bson import ObjectId
from datetime import datetime

# Import other agents and tools
from agents.resume_parsing_agent import resume_parsing_agent
from agents.matching_agent import matching_agent
from agents.communication_agent import communication_agent
from agents.compliance_agent import compliance_agent
from tools.database_tool import database_tool


class OrchestratorAgent:
    """Hierarchical orchestrator that coordinates all other agents"""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL,
            temperature=0.5
        )
        self.agent = Agent(
            role="Recruitment Process Orchestrator",
            goal="Coordinate the entire recruitment workflow efficiently and ensure all steps are completed correctly",
            backstory="You are the master coordinator of the AI recruitment system. You oversee the entire hiring process from resume submission to interview scheduling. You delegate tasks to specialized agents and ensure smooth workflow execution.",
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        self.resume_agent = resume_parsing_agent
        self.matching_agent = matching_agent
        self.communication_agent = communication_agent
        self.compliance_agent = compliance_agent
    
    def process_candidate_application(self, resume_file_path: str) -> Dict:
        """Complete end-to-end processing of a candidate application"""
        try:
            log.info(f"Orchestrator: Starting candidate application processing for {resume_file_path}")
            
            workflow_result = {"success": True, "steps": [], "errors": [], "decision": None}
            
            parse_result = self.resume_agent.process_resume(resume_file_path)
            if not parse_result.get("success"):
                raise ValueError(f"Resume parsing failed: {parse_result.get('error')}")
            
            candidate_email = parse_result["candidate_email"]
            
            self.communication_agent.send_application_confirmation(candidate_email)
            self.compliance_agent.scan_for_bias(candidate_email)
            match_result = self.matching_agent.match_candidate_to_jobs(candidate_email)
            
            overall_score = match_result.get("overall_score", 0)
            matched_jobs = match_result.get("matched_jobs", [])
            
            if overall_score >= 50 and matched_jobs: # Using a threshold of 50
                workflow_result["decision"] = "shortlisted_for_ai_interview"
                top_job_id = matched_jobs[0]["job_id"]
                
                log.info(f"AUTO-SHORTLIST: Score {overall_score} >= 50. Scheduling AI interview for job {top_job_id}")
                
                shortlist_result = self.process_candidate_shortlisting(
                    candidate_email=candidate_email,
                    job_id=top_job_id
                )
                
                workflow_result["message"] = f"SHORTLISTED! Score: {overall_score:.2f}. AI interview link sent."
                workflow_result["ai_interview_link"] = shortlist_result.get("ai_interview_link", "")
            else:
                workflow_result["decision"] = "rejected"
                log.info(f"AUTO-REJECT: Score {overall_score} < 50. Sending rejection email")
                job_id_for_rejection = matched_jobs[0]["job_id"] if matched_jobs else "GENERAL"
                self.reject_candidate(candidate_email, job_id_for_rejection)
                workflow_result["message"] = f"REJECTED. Score: {overall_score:.2f}. Rejection email sent."
            
            return workflow_result
            
        except Exception as e:
            log.error(f"Orchestrator error in application processing: {e}")
            return {"success": False, "error": str(e)}
    
    def process_candidate_shortlisting(self, candidate_email: str, job_id: str) -> Dict:
        """
        Processes shortlisting by creating an AI interview record with the CORRECT status.
        """
        try:
            log.info(f"Orchestrator: Processing AI interview shortlisting for {candidate_email} for job {job_id}")
            
            unique_interview_id = str(ObjectId())
            base_url = settings.FRONTEND_URL.strip('/')
            ai_interview_link = f"{base_url}/frontend/interview.html?interview_id={unique_interview_id}"

            ### FIX: Using the generic _run method to save the interview ###
            # This ensures that we have full control over the data being inserted and
            # that the 'status' is correctly set to 'pending_ai_interview'.
            database_tool._run(
                action="insert",
                collection="interviews",
                data={
                    "_id": unique_interview_id,
                    "job_id": job_id,
                    "candidate_id": candidate_email,
                    "status": "pending_ai_interview", # The correct status
                    "meeting_link": ai_interview_link,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
            log.info(f"Successfully created AI interview record {unique_interview_id} in database.")

            self.communication_agent.send_interview_invitation(
                candidate_email=candidate_email,
                job_id=job_id,
                interview_time="at your convenience within the next 48 hours",
                meeting_link=ai_interview_link
            )
            
            return {
                "success": True,
                "message": "AI interview scheduled and invitation sent.",
                "ai_interview_link": ai_interview_link
            }
            
        except Exception as e:
            log.error(f"Orchestrator error in AI interview shortlisting: {e}")
            return {"success": False, "error": str(e)}
    
    def process_post_interview_decision(self, interview_id: str):
        """
        Makes a final hiring decision after an AI interview is complete.
        """
        try:
            log.info(f"Orchestrator: Processing post-interview decision for {interview_id}")
            interview = database_tool.get_interview_by_id(interview_id)
            if not interview:
                raise ValueError("Interview not found")

            score = interview.get("interview_score", 0)
            candidate_email = interview["candidate_id"]
            job_id = interview["job_id"]

            if score >= 70: # Decision threshold
                log.info(f"HIRE DECISION: Score {score} >= 70. Sending offer/next steps email.")
                self.communication_agent.send_rejection_notice(candidate_email, job_id, is_rejection=False)
            else:
                log.info(f"REJECT DECISION: Score {score} < 70. Sending rejection email.")
                self.communication_agent.send_rejection_notice(candidate_email, job_id, is_rejection=True)

            return {"success": True, "decision": "hire" if score >= 70 else "reject"}
            
        except Exception as e:
            log.error(f"Orchestrator error in post-interview decision: {e}")
            return {"success": False, "error": str(e)}

    def reject_candidate(self, candidate_email: str, job_id: str) -> Dict:
        """Processes an immediate candidate rejection."""
        try:
            log.info(f"Orchestrator: Processing rejection for {candidate_email}")
            return self.communication_agent.send_rejection_notice(candidate_email, job_id)
        except Exception as e:
            log.error(f"Orchestrator error in rejection: {e}")
            return {"success": False, "error": str(e)}

# Create a singleton instance
orchestrator = OrchestratorAgent()