# agents/orchestrator_agent.py

from crewai import Agent
from utils.logger import log
from langchain_groq import ChatGroq
from config.settings import settings
from typing import Dict
from bson import ObjectId
from datetime import datetime

# Import other agents
from agents.resume_parsing_agent import resume_parsing_agent
from agents.matching_agent import matching_agent
from agents.communication_agent import communication_agent
from agents.compliance_agent import compliance_agent
# Import database tool directly if needed for updates
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
        
        # Reference to sub-agents
        self.resume_agent = resume_parsing_agent
        self.matching_agent = matching_agent
        self.communication_agent = communication_agent
        self.compliance_agent = compliance_agent
    
    def process_candidate_application(self, resume_file_path: str) -> Dict:
        """Complete end-to-end processing of a candidate application"""
        try:
            log.info(f"Orchestrator: Starting candidate application processing for {resume_file_path}")
            
            workflow_result = {"success": True, "steps": [], "errors": [], "decision": None}
            
            # Step 1: Parse Resume
            parse_result = self.resume_agent.process_resume(resume_file_path)
            workflow_result["steps"].append({"step": "resume_parsing", "result": parse_result})
            if not parse_result.get("success"):
                raise ValueError(f"Resume parsing failed: {parse_result.get('error')}")
            
            candidate_email = parse_result["candidate_email"]
            
            # Step 2: Send Confirmation
            self.communication_agent.send_application_confirmation(candidate_email)
            
            # Step 3: Compliance Scan & Job Matching
            self.compliance_agent.scan_for_bias(candidate_email)
            match_result = self.matching_agent.match_candidate_to_jobs(candidate_email)
            
            overall_score = match_result.get("overall_score", 0)
            matched_jobs = match_result.get("matched_jobs", [])
            
            # Step 4: Automatic Decision Based on Score
            if overall_score >= 40 and matched_jobs:
                workflow_result["decision"] = "shortlisted_for_ai_interview"
                top_job_id = matched_jobs[0]["job_id"]
                
                log.info(f"AUTO-SHORTLIST: Score {overall_score} >= 40. Scheduling AI interview for job {top_job_id}")
                
                ### MODIFICATION: Trigger AI interview instead of human one ###
                shortlist_result = self.process_candidate_shortlisting(
                    candidate_email=candidate_email,
                    job_id=top_job_id
                )
                
                workflow_result["message"] = f"✅ SHORTLISTED! Score: {overall_score:.2f}. AI interview link sent."
                workflow_result["ai_interview_link"] = shortlist_result.get("ai_interview_link", "")
            else:
                workflow_result["decision"] = "rejected"
                log.info(f"AUTO-REJECT: Score {overall_score} < 40. Sending rejection email")
                job_id_for_rejection = matched_jobs[0]["job_id"] if matched_jobs else "GENERAL"
                self.reject_candidate(candidate_email, job_id_for_rejection)
                workflow_result["message"] = f"❌ REJECTED. Score: {overall_score:.2f}. Rejection email sent."
            
            return workflow_result
            
        except Exception as e:
            log.error(f"Orchestrator error in application processing: {e}")
            return {"success": False, "error": str(e)}
    

    def process_candidate_shortlisting(self, candidate_email: str, job_id: str) -> Dict:
        """
        Process candidate shortlisting by creating an AI interview record
        and sending an invitation email with the correct public link.
        """
        try:
            log.info(f"Orchestrator: Processing AI interview shortlisting for {candidate_email} for job {job_id}")
            
            unique_interview_id = str(ObjectId())
            
            ### FIX: Use the configurable frontend URL from settings ###
            # This generates the correct public link for the email.
            base_url = settings.FRONTEND_URL.strip('/')
            ai_interview_link = f"{base_url}/frontend/interview.html?interview_id={unique_interview_id}"

            # Step 2: Save the interview record to the database (no changes here)
            database_tool._run(
                action="insert",
                collection="interviews",
                data={
                    "_id": unique_interview_id,
                    "job_id": job_id,
                    "candidate_id": candidate_email,
                    "status": "pending_ai_interview",
                    "meeting_link": ai_interview_link,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
            log.info(f"Successfully created AI interview record {unique_interview_id} in database.")

            # Step 3: Send the interview invitation email (no changes here)
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
        After an AI interview is complete, this function is called to make a final
        hiring decision and notify the candidate.
        """
        try:
            log.info(f"Orchestrator: Processing post-interview decision for {interview_id}")
            interview = database_tool.get_interview_by_id(interview_id)
            if not interview:
                raise ValueError("Interview not found")

            score = interview.get("interview_score", 0)
            candidate_email = interview["candidate_id"]
            job_id = interview["job_id"]

            # Decision threshold
            if score >= 70:
                log.info(f"HIRE DECISION: Score {score} >= 70. Sending offer/next steps email.")
                # In a real system, this would trigger a different email template
                self.communication_agent.send_rejection_notice(candidate_email, job_id, is_rejection=False)
            else:
                log.info(f"REJECT DECISION: Score {score} < 70. Sending rejection email.")
                self.communication_agent.send_rejection_notice(candidate_email, job_id)

            return {"success": True, "decision": "hire" if score >= 70 else "reject"}
            
        except Exception as e:
            log.error(f"Orchestrator error in post-interview decision: {e}")
            return {"success": False, "error": str(e)}

    def reject_candidate(self, candidate_email: str, job_id: str) -> Dict:
        """Process candidate rejection"""
        try:
            log.info(f"Orchestrator: Processing rejection for {candidate_email}")
            return self.communication_agent.send_rejection_notice(candidate_email, job_id)
        except Exception as e:
            log.error(f"Orchestrator error in rejection: {e}")
            return {"success": False, "error": str(e)}

# Create orchestrator instance
orchestrator = OrchestratorAgent()