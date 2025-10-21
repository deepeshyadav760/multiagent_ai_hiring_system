# main.py

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import shutil
import os
import tempfile
import asyncio
from datetime import datetime

# Your existing imports
from config.settings import settings
from utils.logger import log
from database.mongodb_client import mongodb
from mcp.mcp_server import initialize_mcp_server
from api.routes import upload, jobs, candidates, interviews
from agents.orchestrator_agent import orchestrator

# Import the new AI Interviewer Agent
from agents.interview_agent import interview_agent
from tools.database_tool import database_tool

from fastapi import WebSocket, WebSocketDisconnect
from agents.interview_agent import interview_agent
import tempfile

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    log.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await mongodb.connect()
    initialize_mcp_server()
    log.info("Application startup complete")
    yield
    log.info("Shutting down application")
    await mongodb.close()
    log.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Recruiting & Talent Screening System with Multi-Agent Architecture",
    lifespan=lifespan
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://127.0.0.1:5500", "null"],
    # allow_origins=["*"], # Allow all origins for testing purposes; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Your Custom Middlewares (No changes needed) ---
# ...

# --- Include Routers (No changes needed) ---
app.include_router(upload.router)
app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(interviews.router)

# --- File Upload Endpoint (No changes needed) ---
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)
@app.post("/upload-resume/", tags=["Resume"])
async def handle_resume_upload(file: UploadFile = File(...)):
    # ... (code for this endpoint remains the same)
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
        file_path = os.path.join(UPLOADS_DIR, safe_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        log.info(f"Resume uploaded and saved to: {file_path}")

        result = orchestrator.process_candidate_application(file_path)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to process resume."))

        return {
            "success": True,
            "message": result.get("message", "Resume processed successfully."),
        }
    except Exception as e:
        log.error(f"Error during resume upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()


### NEW: AI Interview WebSocket Endpoint to prevent the RuntimeError ###
@app.websocket("/ws/interview/{interview_id}")
async def interview_websocket(websocket: WebSocket, interview_id: str):
    await websocket.accept()
    log.info(f"WebSocket connection established for AI interview: {interview_id}")
    
    connection_closed = False
    try:
        # 1. Fetch the interview from the database
        interview = database_tool.get_interview_by_id(interview_id)
        
        # 2. Check the status of the interview
        if not interview or interview.get("status") != "pending_ai_interview":
            # If the interview doesn't exist OR its status is something else
            # (like "completed_ai_interview"), then do this:
            await websocket.send_json({"type": "error", "text": "This interview link is invalid or has already been completed."})
            await websocket.close()
            return

        # 1. Start session, get the opening question
        start_data = interview_agent.get_opening_question(interview['job_id'])
        if not start_data.get("success"):
            await websocket.send_json({"type": "error", "text": start_data.get("error")})
            await websocket.close()
            connection_closed = True
            return

        job_details = start_data['job_details']
        first_question = start_data['question']
        await websocket.send_json({"type": "question", "text": first_question})
        
        conversation_history = [{"speaker": "AI", "text": first_question}]
        
        # 2. Main interview loop
        for _ in range(5):
            audio_bytes = await websocket.receive_bytes()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                tmp_audio.write(audio_bytes)
                audio_file_path = tmp_audio.name
            
            candidate_text = interview_agent.transcribe_audio(audio_file_path)
            os.remove(audio_file_path)
            
            log.info(f"Candidate said: {candidate_text}")
            conversation_history.append({"speaker": "Candidate", "text": candidate_text})
            
            next_question = interview_agent.get_next_question(conversation_history, job_details)
            conversation_history.append({"speaker": "AI", "text": next_question})
            
            await websocket.send_json({"type": "question", "text": next_question})

        # 3. Conclude and evaluate
        await websocket.send_json({"type": "status", "text": "Thank you. The interview is now complete. Please wait while I evaluate your answers..."})
        evaluation = interview_agent.evaluate_interview(conversation_history, job_details)
        
        # 4. Update the database
        database_tool._run(action="update", collection="interviews", query={"_id": interview_id}, data={"status": "completed_ai_interview", "evaluation": evaluation, "interview_score": evaluation.get("score", 0), "updated_at": datetime.utcnow()})
        log.info(f"Interview {interview_id} evaluation complete. Score: {evaluation.get('score')}")
        
        # 5. Trigger post-interview decision
        orchestrator.process_post_interview_decision(interview_id)

        # 6. Send final "thank you" message and wait
        await websocket.send_json({"type": "thank_you", "text": "Evaluation complete. Thank you for your time. The hiring team will be in touch via email."})
        await asyncio.sleep(2)

    except WebSocketDisconnect:
        log.warning(f"Interview {interview_id} disconnected by client.")
        connection_closed = True # Set flag to prevent double-close
    except Exception as e:
        # Improved logging to capture the full error traceback
        import traceback
        log.error(f"Critical error in interview websocket for {interview_id}: {traceback.format_exc()}")
        if not connection_closed:
            try:
                await websocket.send_json({"type": "error", "text": "A critical server error occurred."})
            except RuntimeError:
                pass
    finally:
        if not connection_closed:
            await websocket.close()



@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await mongodb.client.admin.command('ping')
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": settings.APP_VERSION
    }


### FIX: Updated the /stats endpoint to correctly report the vector count ###
@app.get("/stats")
async def get_stats():
    """Get high-level system statistics for the dashboard."""
    try:
        # Get counts from MongoDB collections
        candidates_count = await mongodb.db.candidates.count_documents({})
        jobs_count = await mongodb.db.jobs.count_documents({})
        interviews_count = await mongodb.db.interviews.count_documents({})
        
        # Import the vector_store instance directly
        from database.vector_store import vector_store
        
        # --- The Fix ---
        # Instead of calling get_stats(), we directly access the `ntotal` property
        # of the FAISS index object, which is guaranteed to be correct.
        vector_count = 0
        if vector_store.index:
            vector_count = vector_store.index.ntotal
        
        log.info(f"Fetching stats: Candidates={candidates_count}, Jobs={jobs_count}, Interviews={interviews_count}, Vectors={vector_count}")

        return {
            "success": True,
            "stats": {
                "total_candidates": candidates_count,
                "active_jobs": jobs_count,
                "interviews_scheduled": interviews_count,
                "vector_count": vector_count # Pass the correct number to the frontend
            }
        }
    except Exception as e:
        log.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch system statistics.")


@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    from crew.crew_config import recruiting_crew
    agents = recruiting_crew.get_all_agents()
    return {
        "success": True,
        "agents": {
            name: {"role": agent.agent.role, "goal": agent.agent.goal, "status": "active"}
            for name, agent in agents.items()
        }
    }


@app.get("/mcp/tools")
async def get_mcp_tools():
    """Get list of registered MCP tools"""
    from mcp.mcp_server import mcp_server
    tools = mcp_server.list_tools()
    tools_info = [mcp_server.get_tool_info(tool) for tool in tools]
    return {
        "success": True,
        "total_tools": len(tools),
        "tools": tools_info
    }


if __name__ == "__main__":
    import uvicorn
    log.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG, log_level="info")