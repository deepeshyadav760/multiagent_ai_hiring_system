
# from crewai import Agent, Crew, Task, Process
# from agents.resume_parsing_agent import resume_parsing_agent
# from agents.matching_agent import matching_agent
# from agents.scheduling_agent import scheduling_agent
# from agents.communication_agent import communication_agent
# from agents.compliance_agent import compliance_agent
# from utils.logger import log
# from langchain_groq import ChatGroq
# from config.settings import settings
# from typing import Dict, List


# class OrchestratorAgent:
#     """Hierarchical orchestrator that coordinates all other agents"""
    
#     def __init__(self):
#         self.llm = ChatGroq(
#             api_key=settings.GROQ_API_KEY,
#             model_name=settings.LLM_MODEL,
#             temperature=0.5
#         )
        
#         self.agent = Agent(
#             role="Recruitment Process Orchestrator",
#             goal="Coordinate the entire recruitment workflow efficiently and ensure all steps are completed correctly",
#             backstory="""You are the master coordinator of the AI recruitment system. You 
#             oversee the entire hiring process from resume submission to interview scheduling. 
#             You delegate tasks to specialized agents, monitor their progress, and ensure 
#             smooth workflow execution. You make high-level decisions about the recruitment 
#             pipeline and optimize the process for efficiency and candidate experience.""",
#             verbose=True,
#             allow_delegation=True,
#             llm=self.llm
#         )
        
#         # Reference to sub-agents
#         self.resume_agent = resume_parsing_agent
#         self.matching_agent = matching_agent
#         self.scheduling_agent = scheduling_agent
#         self.communication_agent = communication_agent
#         self.compliance_agent = compliance_agent
    
#     def process_candidate_application(self, resume_file_path: str) -> Dict:
#         """Complete end-to-end processing of a candidate application
        
#         Args:
#             resume_file_path: Path to resume file
            
#         Returns:
#             Processing results
#         """
#         try:
#             log.info(f"Orchestrator: Starting candidate application processing")
            
#             workflow_result = {
#                 "success": True,
#                 "steps": [],
#                 "errors": [],
#                 "decision": None
#             }
            
#             # Step 1: Parse Resume
#             log.info("Step 1: Parsing resume")
#             parse_result = self.resume_agent.process_resume(resume_file_path)
#             workflow_result["steps"].append({
#                 "step": "resume_parsing",
#                 "status": "success" if parse_result.get("success") else "failed",
#                 "result": parse_result
#             })
            
#             if not parse_result.get("success"):
#                 workflow_result["success"] = False
#                 workflow_result["errors"].append(f"Resume parsing failed: {parse_result.get('error')}")
#                 return workflow_result
            
#             candidate_email = parse_result["candidate_email"]
#             candidate_name = parse_result.get("candidate_name", "")
            
#             # Step 2: Send Confirmation
#             log.info("Step 2: Sending confirmation email")
#             confirm_result = self.communication_agent.send_application_confirmation(candidate_email)
#             workflow_result["steps"].append({
#                 "step": "confirmation_email",
#                 "status": "success" if confirm_result.get("success") else "failed",
#                 "result": confirm_result
#             })
            
#             # Step 3: Compliance Scan
#             log.info("Step 3: Running compliance scan")
#             bias_scan_result = self.compliance_agent.scan_for_bias(candidate_email)
#             workflow_result["steps"].append({
#                 "step": "compliance_scan",
#                 "status": "success" if bias_scan_result.get("success") else "failed",
#                 "result": bias_scan_result
#             })
            
#             # Step 4: Match to Jobs
#             log.info("Step 4: Matching candidate to jobs")
#             match_result = self.matching_agent.match_candidate_to_jobs(candidate_email)
#             workflow_result["steps"].append({
#                 "step": "job_matching",
#                 "status": "success" if match_result.get("success") else "failed",
#                 "result": match_result
#             })
            
#             overall_score = match_result.get("overall_score", 0)
#             matched_jobs = match_result.get("matched_jobs", [])
            
#             # Step 5: Automatic Decision Based on Score
#             log.info(f"Step 5: Making decision based on score: {overall_score}")
            
#             if overall_score >= 40 and matched_jobs:
#                 # SHORTLIST: Score >= 40
#                 workflow_result["decision"] = "shortlisted"
#                 top_job_id = matched_jobs[0]["job_id"]
                
#                 log.info(f"AUTO-SHORTLIST: Score {overall_score} >= 40. Scheduling interview for job {top_job_id}")
                
#                 # Schedule interview automatically
#                 shortlist_result = self.process_candidate_shortlisting(
#                     candidate_email=candidate_email,
#                     job_id=top_job_id,
#                     recruiter_email="deepesh.y@atriauniversity.edu.in"
#                 )
                
#                 workflow_result["steps"].append({
#                     "step": "auto_shortlist",
#                     "status": "success" if shortlist_result.get("success") else "failed",
#                     "result": shortlist_result
#                 })
                
#                 workflow_result["message"] = f"✅ SHORTLISTED! Score: {overall_score:.2f}. Interview scheduled with Google Meet link sent."
#                 workflow_result["interview_scheduled"] = shortlist_result.get("success", False)
#                 workflow_result["meeting_link"] = shortlist_result.get("interview_details", {}).get("meeting_link", "")
                
#             else:
#                 # REJECT: Score < 40
#                 workflow_result["decision"] = "rejected"
                
#                 log.info(f"AUTO-REJECT: Score {overall_score} < 40. Sending rejection email")
                
#                 # Send rejection email
#                 if matched_jobs:
#                     rejection_result = self.reject_candidate(candidate_email, matched_jobs[0]["job_id"])
#                 else:
#                     # No jobs matched, send generic rejection
#                     rejection_result = self.communication_agent.send_rejection_notice(
#                         candidate_email=candidate_email,
#                         job_id="GENERAL"
#                     )
                
#                 workflow_result["steps"].append({
#                     "step": "auto_reject",
#                     "status": "success" if rejection_result.get("success") else "failed",
#                     "result": rejection_result
#                 })
                
#                 workflow_result["message"] = f"❌ REJECTED. Score: {overall_score:.2f} (below threshold of 50). Rejection email sent."
            
#             workflow_result["candidate_email"] = candidate_email
#             workflow_result["candidate_name"] = candidate_name
#             workflow_result["overall_score"] = overall_score
#             workflow_result["matched_jobs_count"] = len(matched_jobs)
            
#             log.info(f"Orchestrator: Completed processing for {candidate_email} - Decision: {workflow_result['decision']}")
            
#             return workflow_result
            
#         except Exception as e:
#             log.error(f"Orchestrator error in application processing: {e}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "steps": workflow_result.get("steps", [])
#             }
    
#     def process_candidate_shortlisting(
#         self,
#         candidate_email: str,
#         job_id: str,
#         recruiter_email: str = "recruiter@company.com"
#     ) -> Dict:
#         """Process candidate shortlisting and schedule interview
        
#         Args:
#             candidate_email: Candidate's email
#             job_id: Job ID
#             recruiter_email: Recruiter's email
            
#         Returns:
#             Shortlisting results
#         """
#         try:
#             log.info(f"Orchestrator: Processing shortlisting for {candidate_email}")
            
#             workflow_result = {
#                 "success": True,
#                 "steps": [],
#                 "errors": []
#             }
            
#             # Step 1: Schedule Interview
#             log.info("Step 1: Scheduling interview")
#             schedule_result = self.scheduling_agent.schedule_interview(
#                 candidate_email=candidate_email,
#                 job_id=job_id,
#                 recruiter_email=recruiter_email
#             )
#             workflow_result["steps"].append({
#                 "step": "interview_scheduling",
#                 "status": "success" if schedule_result.get("success") else "failed",
#                 "result": schedule_result
#             })
            
#             if not schedule_result.get("success"):
#                 workflow_result["success"] = False
#                 workflow_result["errors"].append(f"Scheduling failed: {schedule_result.get('error')}")
#                 return workflow_result
            
#             # Step 2: Send Interview Invitation
#             log.info("Step 2: Sending interview invitation")
#             invite_result = self.communication_agent.send_interview_invitation(
#                 candidate_email=candidate_email,
#                 job_id=job_id,
#                 interview_time=schedule_result.get("scheduled_time", ""),
#                 meeting_link=schedule_result.get("meeting_link", "")
#             )
#             workflow_result["steps"].append({
#                 "step": "interview_invitation",
#                 "status": "success" if invite_result.get("success") else "failed",
#                 "result": invite_result
#             })
            
#             workflow_result["message"] = "Candidate shortlisted and interview scheduled successfully"
#             workflow_result["interview_details"] = {
#                 "scheduled_time": schedule_result.get("scheduled_time"),
#                 "meeting_link": schedule_result.get("meeting_link"),
#                 "job_title": schedule_result.get("job_title")
#             }
            
#             log.info(f"Orchestrator: Completed shortlisting process for {candidate_email}")
            
#             return workflow_result
            
#         except Exception as e:
#             log.error(f"Orchestrator error in shortlisting: {e}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "steps": workflow_result.get("steps", [])
#             }
    
#     def reject_candidate(self, candidate_email: str, job_id: str) -> Dict:
#         """Process candidate rejection
        
#         Args:
#             candidate_email: Candidate's email
#             job_id: Job ID
            
#         Returns:
#             Rejection results
#         """
#         try:
#             log.info(f"Orchestrator: Processing rejection for {candidate_email}")
            
#             # Send rejection notice
#             rejection_result = self.communication_agent.send_rejection_notice(
#                 candidate_email=candidate_email,
#                 job_id=job_id
#             )
            
#             # Log compliance action
#             self.compliance_agent.log_action(
#                 action_type="candidate_rejected",
#                 details={
#                     "candidate_email": candidate_email,
#                     "job_id": job_id
#                 }
#             )
            
#             return rejection_result
            
#         except Exception as e:
#             log.error(f"Orchestrator error in rejection: {e}")
#             return {"success": False, "error": str(e)}
    
#     def create_crew_workflow(self, workflow_type: str, **kwargs) -> Dict:
#         """Create and execute a CrewAI workflow with hierarchical process
        
#         Args:
#             workflow_type: Type of workflow to execute
#             **kwargs: Workflow parameters
            
#         Returns:
#             Workflow results
#         """
#         try:
#             if workflow_type == "full_application_process":
#                 return self.process_candidate_application(kwargs.get("resume_file_path"))
            
#             elif workflow_type == "shortlist_and_schedule":
#                 return self.process_candidate_shortlisting(
#                     candidate_email=kwargs.get("candidate_email"),
#                     job_id=kwargs.get("job_id"),
#                     recruiter_email=kwargs.get("recruiter_email", "recruiter@company.com")
#                 )
            
#             elif workflow_type == "reject_candidate":
#                 return self.reject_candidate(
#                     candidate_email=kwargs.get("candidate_email"),
#                     job_id=kwargs.get("job_id")
#                 )
            
#             else:
#                 return {"success": False, "error": f"Unknown workflow type: {workflow_type}"}
                
#         except Exception as e:
#             log.error(f"Crew workflow error: {e}")
#             return {"success": False, "error": str(e)}


# # Create orchestrator instance
# orchestrator = OrchestratorAgent()





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
        and sending an invitation email.
        """
        try:
            log.info(f"Orchestrator: Processing AI interview shortlisting for {candidate_email} for job {job_id}")
            
            # Step 1: Generate a unique ID and the interview link
            unique_interview_id = str(ObjectId())
            # IMPORTANT: This URL should point to where your frontend is served.
            # If you open index.html directly, this path needs to be correct.
            ai_interview_link = f"http://127.0.0.1:5500/frontend/interview.html?interview_id={unique_interview_id}"

            # Step 2: Save the interview record to the database
            database_tool._run(
                action="insert",
                collection="interviews",
                data={
                    "_id": unique_interview_id,
                    "job_id": job_id,
                    "candidate_id": candidate_email,
                    "status": "pending_ai_interview",
                    "meeting_link": ai_interview_link, # Re-using this field for the link
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
            log.info(f"Successfully created AI interview record {unique_interview_id} in database.")

            # Step 3: Send the interview invitation email with the new link
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