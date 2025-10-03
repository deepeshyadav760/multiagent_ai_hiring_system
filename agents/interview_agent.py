# agents/interview_agent.py

from crewai import Agent
from langchain_groq import ChatGroq
from config.settings import settings
from tools.database_tool import database_tool
from faster_whisper import WhisperModel
from utils.logger import log

class InterviewAgent:
    def __init__(self):
        self.llm = ChatGroq(api_key=settings.GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
        # Use a tiny, fast model for STT. For better accuracy, use "base" or "medium".
        self.stt_model = WhisperModel("base.en", device="cpu", compute_type="int8")
        self.agent = Agent(
            role="Senior Technical Interviewer",
            goal="Fairly and accurately assess a candidate's skills for a specific job role through a series of relevant questions.",
            backstory="Your name is PrashnaAI. You are an expert AI hiring manager, designed to conduct effective and unbiased technical interviews. You adapt your questions based on the candidate's responses.",
            verbose=True,
            llm=self.llm,
        )

    def transcribe_audio(self, audio_file_path: str) -> str:
        """Converts audio file to text."""
        segments, _ = self.stt_model.transcribe(audio_file_path, beam_size=5)
        return " ".join([segment.text for segment in segments])

    def get_opening_question(self, job_id: str) -> dict:
        """Prepares the first question for the interview."""
        job = database_tool.get_job_by_id(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}

        prompt = f"""You are an AI Interviewer. Start an interview for a '{job['title']}' role. 
        The required skills are {job.get('required_skills', [])}.
        Greet the candidate, introduce yourself, and ask your first opening question related to a key skill. Keep it concise."""
        
        question = self.llm.invoke(prompt).content
        return {"success": True, "question": question, "job_details": job}

    def get_next_question(self, conversation_history: list, job_details: dict) -> str:
        """Generates the next question based on the conversation."""
        history_str = "\n".join([f"{entry['speaker']}: {entry['text']}" for entry in conversation_history])
        
        prompt = f"""You are an AI Interviewer for a '{job_details['title']}' role.
        Conversation History:
        {history_str}
        
        Based on the candidate's last answer, ask the next logical follow-up question.
        Ensure you cover the required skills: {job_details.get('required_skills', [])}. Do not repeat questions."""
        
        return self.llm.invoke(prompt).content

    def evaluate_interview(self, conversation_history: list, job_details: dict) -> dict:
        """Evaluates the full transcript and provides a score and summary."""
        transcript = "\n".join([f"{entry['speaker']}: {entry['text']}" for entry in conversation_history])
        
        ### FIX: Made the prompt much stricter to ensure valid JSON output ###
        prompt = f"""
        As an expert technical recruiter, evaluate the following interview transcript for a '{job_details['title']}' role.
        The required skills are: {job_details.get('required_skills', [])}.
        
        Transcript:
        {transcript}

        Your Task is to analyze the transcript and provide a final score and summary.
        
        IMPORTANT: Your response MUST be a single, valid JSON object and nothing else. Do not add any introductory text, explanations, or markdown formatting like ```json.

        The JSON object must have the following keys: "summary", "strengths", "weaknesses", and "score".
        - summary: A brief, 2-sentence overview of the candidate's performance.
        - strengths: A list of 2-3 key strengths demonstrated.
        - weaknesses: A list of 1-2 areas for improvement.
        - score: A final integer score from 0 to 100.
        
        Example of a valid response:
        {{"summary": "The candidate shows strong foundational knowledge but struggles with advanced concepts.", "strengths": ["Clear communication", "Solid understanding of core Python"], "weaknesses": ["Lacked depth on database optimization"], "score": 65}}
        """
        
        evaluation_text = self.llm.invoke(prompt).content.strip()
        
        try:
            # Clean up potential markdown backticks just in case
            if evaluation_text.startswith("```json"):
                evaluation_text = evaluation_text[7:]
            if evaluation_text.endswith("```"):
                evaluation_text = evaluation_text[:-3]

            import json
            eval_data = json.loads(evaluation_text)
            eval_data['transcript'] = transcript
            log.info(f"Successfully parsed interview evaluation. Score: {eval_data.get('score')}")
            return eval_data
        except Exception as e:
            log.error(f"Failed to parse interview evaluation JSON. Raw response: '{evaluation_text}'. Error: {e}")
            return {"summary": "Failed to parse evaluation from LLM.", "strengths": [], "weaknesses": [], "score": 0, "transcript": transcript}

interview_agent = InterviewAgent()