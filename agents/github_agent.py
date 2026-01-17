# agents/github_agent.py

from crewai import Agent
from crewai_tools import ScrapeWebsiteTool
from langchain_groq import ChatGroq
from config.settings import settings
from utils.logger import log

class GitHubAgent:
    def __init__(self):
        self.llm = ChatGroq(api_key=settings.GROQ_API_KEY, model_name=settings.LLM_MODEL)
        # In a real app, you'd use a dedicated GitHub tool with API access.
        # For simplicity, we use a web scraper to "read" the public profile page.
        self.scraper_tool = ScrapeWebsiteTool()
        self.agent = Agent(
            role="GitHub Profile Analyst",
            goal="Analyze a candidate's GitHub profile to assess their primary programming languages, project quality, and contribution activity.",
            backstory="You are a senior engineering manager who is an expert at evaluating developer talent by looking at their code. You can quickly understand a developer's strengths and weaknesses by analyzing their public repositories.",
            verbose=True,
            llm=self.llm,
            tools=[self.scraper_tool],
            allow_delegation=False
        )

    def analyze_profile(self, github_url: str) -> str:
        """
        Scrapes a GitHub profile URL and uses an LLM to analyze its content.
        """
        log.info(f"GitHub Agent: Analyzing profile at {github_url}")
        
        if not github_url or "github.com" not in github_url:
            return "No valid GitHub URL was provided."
            
        try:
            # Scrape the content of the GitHub profile page
            scraped_content = self.scraper_tool.run(website_url=github_url)
            
            if not scraped_content:
                return "Could not retrieve content from the provided GitHub URL."

            # Use an LLM to analyze the scraped content
            prompt = f"""
            Based on the following scraped content from a GitHub profile page, please provide a brief analysis of the user.

            Your analysis should include:
            1.  **Primary Languages:** Identify the top 2-3 programming languages based on the repositories shown.
            2.  **Key Projects:** List 1-2 interesting or popular projects mentioned.
            3.  **Activity Level:** Comment on their general contribution activity (e.g., "active," "infrequent").
            4.  **Overall Impression:** A one-sentence summary of the developer's profile (e.g., "Appears to be a skilled Python developer focused on machine learning.").

            Scraped Content (first 4000 characters):
            {scraped_content[:4000]}

            Analysis Report:
            """
            
            analysis = self.llm.invoke(prompt).content
            log.info(f"GitHub Agent: Successfully analyzed profile at {github_url}")
            return analysis

        except Exception as e:
            log.error(f"GitHub Agent failed for URL {github_url}: {e}")
            return "An error occurred during GitHub profile analysis."

# Create a singleton instance
github_agent = GitHubAgent()