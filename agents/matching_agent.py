# # Job-Candidate Matching Agent
# from crewai import Agent
# from tools.database_tool import database_tool
# from tools.vector_search_tool import vector_search_tool
# from llm.groq_client import groq_client
# from utils.logger import log
# from langchain_groq import ChatGroq
# from config.settings import settings
# from typing import List, Dict


# class MatchingAgent:
#     """Agent responsible for matching candidates to jobs using RAG"""
    
#     def __init__(self):
#         self.llm = ChatGroq(
#             api_key=settings.GROQ_API_KEY,
#             model_name=settings.LLM_MODEL,
#             temperature=0.5
#         )
        
#         self.agent = Agent(
#             role="Job-Candidate Matching Specialist",
#             goal="Match candidates to the most suitable job positions using semantic understanding",
#             backstory="""You are an expert recruiter with deep understanding of job requirements 
#             and candidate profiles. You use AI-powered semantic matching to find the best 
#             candidates for each position, considering skills, experience, and job requirements. 
#             You provide accurate matching scores and justifications.""",
#             verbose=True,
#             allow_delegation=False,
#             llm=self.llm,
#             tools=[database_tool, vector_search_tool]
#         )
    
#     def match_candidate_to_jobs(self, candidate_email: str) -> Dict:
#         """Match a candidate to available jobs
        
#         Args:
#             candidate_email: Candidate email
            
#         Returns:
#             Matching results with scores
#         """
#         try:
#             log.info(f"Matching candidate: {candidate_email}")
            
#             # Get candidate data
#             candidate_result = database_tool._run(
#                 action="find_one",
#                 collection="candidates",
#                 query={"email": candidate_email}
#             )
            
#             candidate = candidate_result.get("document")
#             if not candidate:
#                 return {"success": False, "error": "Candidate not found"}
            
#             # Use vector search to find matching jobs
#             match_result = vector_search_tool._run(
#                 action="match_jobs",
#                 candidate_text=candidate.get("resume_text", ""),
#                 skills=candidate.get("skills", []),
#                 k=10
#             )
            
#             matched_jobs = match_result.get("matched_jobs", [])
            
#             if not matched_jobs:
#                 log.warning(f"No matching jobs found for {candidate_email}")
#                 return {
#                     "success": True,
#                     "candidate_email": candidate_email,
#                     "matched_jobs": [],
#                     "message": "No matching jobs found"
#                 }
            
#             # Use LLM to refine matching and provide reasoning
#             refined_matches = self._refine_matches_with_llm(candidate, matched_jobs)
            
#             # Calculate overall score (average of top 3 matches)
#             top_matches = refined_matches[:3]
#             overall_score = sum(m["final_score"] for m in top_matches) / len(top_matches) if top_matches else 0
            
#             # Update candidate with matches and score
#             matched_job_ids = [m["job_id"] for m in refined_matches]
#             database_tool.update_candidate_score(
#                 email=candidate_email,
#                 score=overall_score,
#                 matched_jobs=matched_job_ids
#             )
            
#             log.info(f"Matched {len(refined_matches)} jobs for {candidate_email}, score: {overall_score:.2f}")
            
#             return {
#                 "success": True,
#                 "candidate_email": candidate_email,
#                 "overall_score": overall_score,
#                 "matched_jobs": refined_matches,
#                 "match_count": len(refined_matches)
#             }
            
#         except Exception as e:
#             log.error(f"Error matching candidate: {e}")
#             return {"success": False, "error": str(e)}
    
#     def _refine_matches_with_llm(self, candidate: Dict, matched_jobs: List[Dict]) -> List[Dict]:
#         """Use LLM to refine job matches and provide reasoning
        
#         Args:
#             candidate: Candidate data
#             matched_jobs: Initial matched jobs from vector search
            
#         Returns:
#             Refined matches with scores and reasoning
#         """
#         refined_matches = []
        
#         for job_match in matched_jobs:
#             # Get full job details
#             job = database_tool.get_job_by_id(job_match["job_id"])
            
#             if not job:
#                 continue
            
#             # Create prompt for LLM evaluation
#             prompt = f"""Evaluate how well this candidate matches the job requirements.

# Candidate Profile:
# - Skills: {', '.join(candidate.get('skills', []))}
# - Experience: {candidate.get('experience_years', 0)} years
# - Education: {candidate.get('education', [])}

# Job Requirements:
# - Title: {job.get('title', '')}
# - Required Skills: {', '.join(job.get('required_skills', []))}
# - Experience Required: {job.get('experience_required', 0)} years
# - Description: {job.get('description', '')[:300]}

# Vector Similarity Score: {job_match['match_score']:.2f}

# Provide:
# 1. A matching score from 0-100
# 2. Brief reasoning (max 100 words)
# 3. Key matching factors
# 4. Any gaps or concerns

# Return as JSON with fields: score, reasoning, matching_factors, concerns"""

#             try:
#                 llm_result = groq_client.extract_json(prompt)
                
#                 # Combine vector score and LLM score
#                 vector_score = job_match['match_score'] * 100
#                 llm_score = llm_result.get('score', 50)
#                 final_score = (vector_score * 0.4 + llm_score * 0.6)  # Weighted average
                
#                 refined_matches.append({
#                     "job_id": job_match["job_id"],
#                     "job_title": job.get("title", ""),
#                     "vector_score": vector_score,
#                     "llm_score": llm_score,
#                     "final_score": final_score,
#                     "reasoning": llm_result.get("reasoning", ""),
#                     "matching_factors": llm_result.get("matching_factors", []),
#                     "concerns": llm_result.get("concerns", [])
#                 })
                
#             except Exception as e:
#                 log.error(f"LLM refinement error for job {job_match['job_id']}: {e}")
#                 # Fallback to vector score only
#                 refined_matches.append({
#                     "job_id": job_match["job_id"],
#                     "job_title": job.get("title", ""),
#                     "final_score": job_match['match_score'] * 100,
#                     "reasoning": "Based on semantic similarity"
#                 })
        
#         # Sort by final score
#         refined_matches.sort(key=lambda x: x["final_score"], reverse=True)
        
#         return refined_matches


# # Create agent instance
# matching_agent = MatchingAgent()







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