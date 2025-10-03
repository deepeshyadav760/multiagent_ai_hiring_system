# 🚀 Quick Start Guide - AI Recruiting System

Get up and running in 5 minutes!

## Prerequisites

- Python 3.10+
- MongoDB
- Groq API Key ([Get one here](https://console.groq.com))

## Step 1: Install Dependencies (2 min)

```bash
# Clone/download the project
cd ai-recruiting-system

# Install Python packages
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

## Step 2: Setup MongoDB (1 min)

**Option A: Using Docker (Recommended)**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Option B: Local MongoDB**
```bash
# Start MongoDB
mongod --dbpath /path/to/data/db
```

## Step 3: Configure Environment (1 min)

```bash
# Run setup script
python setup.py
```

This will:
- Create necessary directories
- Generate `.env` file
- Check dependencies
- Verify MongoDB connection

**Edit `.env` and add your Groq API key:**
```bash
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

## Step 4: Start the Server (30 seconds)

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 5: Verify Installation (30 seconds)

Open your browser to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **System Stats**: http://localhost:8000/stats

Or run the test script:
```bash
python test_system.py
```

## 🎯 Your First Workflow

### 1. Create a Job Posting

**Using API Docs** (http://localhost:8000/docs):
- Click on `POST /jobs/`
- Click "Try it out"
- Use this sample data:

```json
{
  "job_id": "JOB-001",
  "title": "Senior Python Developer",
  "description": "Looking for an experienced Python developer",
  "required_skills": ["Python", "FastAPI", "MongoDB", "AI/ML"],
  "experience_required": 5,
  "location": "Remote",
  "employment_type": "full-time"
}
```

**Or use cURL:**
```bash
curl -X POST "http://localhost:8000/jobs/" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "JOB-001",
    "title": "Senior Python Developer",
    "description": "Looking for an experienced Python developer",
    "required_skills": ["Python", "FastAPI", "MongoDB"],
    "experience_required": 5,
    "location": "Remote",
    "employment_type": "full-time"
  }'
```

### 2. Upload a Resume

**Using API Docs**:
- Click on `POST /upload/resume`
- Click "Try it out"
- Choose a PDF or DOCX resume file
- Click "Execute"

**Or use cURL:**
```bash
curl -X POST "http://localhost:8000/upload/resume" \
  -F "file=@/path/to/resume.pdf"
```

**What happens automatically:**
1. ✅ Resume is parsed
2. ✅ Candidate profile created in database
3. ✅ Confirmation email prepared
4. ✅ Compliance/bias scan performed
5. ✅ Jobs are matched using AI/RAG
6. ✅ Candidate scored and ranked

### 3. View Top Candidates for a Job

```bash
curl "http://localhost:8000/jobs/JOB-001/candidates?top_n=10"
```

### 4. Shortlist a Candidate (Auto-Schedule Interview)

```bash
curl -X POST "http://localhost:8000/candidates/john@example.com/shortlist/JOB-001"
```

**This automatically:**
1. ✅ Finds available interview slots
2. ✅ Books the interview
3. ✅ Sends interview invitation email
4. ✅ Generates meeting link

### 5. View All Interviews

```bash
curl "http://localhost:8000/interviews/"
```

## 📊 Monitor Your System

### Check Agent Status
```bash
curl "http://localhost:8000/agents/status"
```

Shows all 6 agents:
- Orchestrator Agent (Manager)
- Resume Parsing Agent
- Job-Candidate Matching Agent
- Interview Scheduling Agent
- Communication Agent
- Compliance Agent

### Check MCP Tools
```bash
curl "http://localhost:8000/mcp/tools"
```

Shows all 5 tools:
- Resume Parser
- Database Operations
- Vector Search (RAG)
- Email Communication
- Calendar Management

### View System Statistics
```bash
curl "http://localhost:8000/stats"
```

## 🎨 API Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload/resume` | POST | Upload and process resume |
| `/jobs/` | POST | Create job posting |
| `/jobs/` | GET | List all jobs |
| `/jobs/{job_id}` | GET | Get job details |
| `/jobs/{job_id}/candidates` | GET | Get top candidates for job |
| `/candidates/` | GET | List all candidates |
| `/candidates/{email}` | GET | Get candidate details |
| `/candidates/{email}/shortlist/{job_id}` | POST | Shortlist candidate |
| `/candidates/{email}/reject/{job_id}` | POST | Reject candidate |
| `/interviews/` | GET | List all interviews |
| `/interviews/available-slots/` | GET | Get available time slots |
| `/health` | GET | System health check |
| `/stats` | GET | System statistics |
| `/agents/status` | GET | Agent status |

## 🔧 Common Issues & Solutions

### Issue: MongoDB connection failed
**Solution:**
```bash
# Check if MongoDB is running
docker ps  # for Docker
# OR
pgrep mongod  # for local MongoDB

# Start MongoDB if not running
docker start mongodb
# OR
mongod --dbpath /path/to/data
```

### Issue: Groq API error
**Solution:**
- Verify your API key in `.env`
- Check API key is valid at https://console.groq.com
- Ensure no extra spaces in the key

### Issue: Import errors
**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Issue: Port 8000 already in use
**Solution:**
Edit `.env`:
```bash
PORT=8001  # Change to any available port
```

## 🎓 Next Steps

1. **Add Email Notifications**: Configure SMTP settings in `.env`
2. **Integrate Calendar**: Add Google Calendar OAuth credentials
3. **Customize Agents**: Modify agent behaviors in `agents/` directory
4. **Add More Tools**: Create custom tools in `tools/` directory
5. **Scale Up**: Deploy with Docker/Kubernetes

## 📚 Additional Resources

- **Full Documentation**: See `README.md`
- **API Documentation**: http://localhost:8000/docs (when running)
- **Test System**: Run `python test_system.py`
- **Directory Structure**: See main `README.md`

## 🆘 Need Help?

1. Check logs in `logs/` directory
2. Run `python test_system.py` to diagnose issues
3. Verify `.env` configuration
4. Ensure MongoDB is accessible at localhost:27017

## 🎉 Success!

You now have a fully functional AI-powered recruiting system with:
- ✅ 6 intelligent agents working together
- ✅ 5 specialized tools
- ✅ RAG-based candidate matching
- ✅ Automated workflow orchestration
- ✅ REST API for integration
- ✅ MCP for standardized tool access

**Upload a resume and watch the magic happen!** 🚀