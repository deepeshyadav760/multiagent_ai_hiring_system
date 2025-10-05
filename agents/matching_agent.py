# agents/matching_agent.py

from crewai import Agent
from langchain_groq import ChatGroq
from config.settings import settings
from tools.database_tool import database_tool
from utils.logger import log
import json

class MatchingAgent:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile", # Use a powerful model for evaluation
            temperature=0.2
        )
        self.agent = Agent(
            role="Candidate-Job Matching Specialist",
            goal="Accurately assess a candidate's resume against all available job postings and calculate a precise match score.",
            backstory="You are an expert AI recruiter with a deep understanding of technical skills and job requirements. You meticulously analyze every detail of a candidate's profile and compare it to the specific needs of each job role to find the best possible fit.",
            verbose=True,
            llm=self.llm,
        )

    def match_candidate_to_jobs(self, candidate_email: str) -> dict:
        """
        Fetches a candidate and all jobs, then uses an LLM to calculate the best match.
        """
        log.info(f"Matching agent starting process for candidate: {candidate_email}")
        
        try:
            # 1. Fetch Candidate Data
            candidate_result = database_tool._run("find_one", "candidates", query={"email": candidate_email})
            candidate = candidate_result.get("document")
            if not candidate:
                return {"success": False, "error": "Candidate not found."}

            # 2. Fetch ALL Job Postings using the corrected method
            all_jobs = database_tool.get_active_jobs() # This now fetches all jobs
            if not all_jobs:
                return {"success": False, "error": "No job postings found in the database to match against."}

            log.info(f"Found {len(all_jobs)} jobs to match against.")

            # 3. Construct a detailed prompt for the LLM
            candidate_summary = f"""
            Candidate Skills: {', '.join(candidate.get('skills', []))}
            Candidate Resume Text: {candidate.get('resume_text', '')[:2000]}
            """

            jobs_summary = json.dumps([{
                "job_id": job["job_id"],
                "title": job["title"],
                "required_skills": job.get("required_skills", []),
                "description": job.get("description", "")[:500]
            } for job in all_jobs], indent=2)

            prompt = f"""
            As an expert AI recruiter, your task is to evaluate the following candidate against a list of available jobs.

            **Candidate Profile:**
            {candidate_summary}

            **Available Jobs:**
            {jobs_summary}

            **Instructions:**
            1.  Review the candidate's skills and resume text carefully.
            2.  For EACH job in the list, calculate a match score from 0 to 100 based on how well the candidate's experience and skills align with the job's required skills and description.
            3.  Consider both direct keyword matches (e.g., "Python") and conceptual matches (e.g., experience with "RAG" matches a "Generative AI" requirement).
            4.  Identify the single job with the HIGHEST match score.
            5.  Provide your response ONLY in the following JSON format. Do not add any other text or explanations before or after the JSON block.

            {{
              "best_match_job_id": "The job_id of the top-scoring job",
              "best_match_score": "The highest score (as a number)",
              "reasoning": "A brief, 2-sentence explanation for why this job is the best match.",
              "all_scores": [
                {{"job_id": "JOB-ID-001", "score": 75}},
                {{"job_id": "JOB-ID-002", "score": 88}}
              ]
            }}
            """
            
            # 4. Get Evaluation from LLM
            response_text = self.llm.invoke(prompt).content
            log.info(f"LLM matching response: {response_text}")
            
            # Clean up the response to ensure it's valid JSON
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            match_data = json.loads(cleaned_response)

            top_score = match_data.get("best_match_score", 0)
            best_job_id = match_data.get("best_match_job_id")
            
            # 5. Update the candidate's record in the database
            database_tool.update_candidate_score(
                email=candidate_email,
                score=top_score,
                matched_jobs=[best_job_id] if best_job_id else []
            )
            log.info(f"Successfully updated candidate {candidate_email} with score {top_score} for job {best_job_id}")

            return {
                "success": True,
                "overall_score": top_score,
                "matched_jobs": [{"job_id": best_job_id, "score": top_score}] if best_job_id else []
            }

        except Exception as e:
            log.error(f"Error in matching agent: {e}")
            return {"success": False, "error": str(e)}

# Create a singleton instance
matching_agent = MatchingAgent()