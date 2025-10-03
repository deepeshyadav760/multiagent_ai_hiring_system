# AI-Powered Recruiting & Talent Screening System

A fully functional, production-ready AI recruiting system powered by multi-agent architecture, featuring automated resume parsing, intelligent candidate matching, interview scheduling, and compliance monitoring.

## 🏗️ Architecture

### Multi-Agent System (Hierarchical Pattern)

This system implements a **hierarchical agent architecture** with 6 specialized agents:

1. **Orchestrator Agent** (Manager) - Coordinates all other agents and manages workflow
2. **Resume Parsing Agent** - Extracts structured data from resumes
3. **Job-Candidate Matching Agent** - Uses RAG for semantic job matching
4. **Interview Scheduling Agent** - Manages calendar and schedules interviews
5. **Communication Agent** - Handles all candidate communications
6. **Compliance Agent** - Ensures fair, unbiased, and compliant recruitment

### Technology Stack

- **Framework**: FastAPI
- **Agent Framework**: CrewAI (with hierarchical process)
- **LLM**: Groq API (Llama3 70B)
- **Embeddings**: sentence-transformers (MiniLM-L6-v2)
- **Vector Store**: FAISS
- **Database**: MongoDB (localhost:27017)
- **MCP**: Model Context Protocol for tool standardization
- **LlamaIndex**: For document processing and RAG

## 🚀 Features

### Core Capabilities

✅ **Automated Resume Processing**
- Parse PDF/DOCX resumes
- Extract skills, experience, education
- Natural language understanding via LLM

✅ **Intelligent Job Matching (RAG)**
- Semantic search using embeddings
- LLM-powered candidate ranking
- Contextual job-candidate alignment

✅ **Interview Automation**
- Calendar integration
- Automatic scheduling
- Meeting link generation

✅ **Communication Management**
- Application confirmations
- Interview invitations
- Follow-up reminders
- Rejection notices

✅ **Compliance & Diversity**
- Bias detection in resumes
- Audit trail logging
- Fair evaluation standards

## 📦 Installation

### Prerequisites

- Python 3.10+
- MongoDB running on localhost:27017
- Groq API key

### Setup

1. **Clone and install dependencies**

```bash
git clone <repository>
cd ai-recruiting-system
pip install -r requirements.txt
```

2. **Download spaCy model**

```bash
python -m spacy download en_core_web_sm
```

3. **Configure environment**

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```
GROQ_API_KEY=your_groq_api_key_here
MONGODB_URL=mongodb://localhost:27017
```

4. **Create necessary directories**

```bash
mkdir -p uploads logs data
```

5. **Start MongoDB**

```bash
# If using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or start your local MongoDB instance
mongod --dbpath /path/to/data
```

## 🎯 Usage

### Start the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### API Endpoints

#### 1. Upload Resume

```bash
curl -X POST "http://localhost:8000/upload/resume" \
  -F "file=@resume.pdf"
```

**What happens:**
1. Resume is parsed
2. Candidate profile created
3. Confirmation email sent
4. Compliance scan performed
5. Jobs matched automatically
6. Scores calculated

#### 2. Create Job Posting

```bash
curl -X POST "http://localhost:8000/jobs/" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "JOB-001",
    "title": "Senior Python Developer",
    "description": "We are looking for an experienced Python developer...",
    "required_skills": ["Python", "FastAPI", "MongoDB", "AI/ML"],
    "experience_required": 5,
    "location": "Remote",
    "employment_type": "full-time"
  }'
```

#### 3. Get Top Candidates for Job

```bash
curl -X GET "http://localhost:8000/jobs/JOB-001/candidates?top_n=10"
```

#### 4. Shortlist Candidate (Schedule Interview)

```bash
curl -X POST "http://localhost:8000/candidates/john@example.com/shortlist/JOB-001"
```

**What happens:**
1. Interview time slot found
2. Calendar booking created
3. Interview invitation sent
4. Meeting link generated

#### 5. Get All Candidates

```bash
curl -X GET "http://localhost:8000/candidates/?status=pending&min_score=70"
```

#### 6. Check System Health

```bash
curl -X GET "http://localhost:8000/health"
```

#### 7. View Agent Status

```bash
curl -X GET "http://localhost:8000/agents/status"
```

## 🔧 Configuration

### LLM Configuration

Edit `config/settings.py`:

```python
LLM_MODEL = "llama3-70b-8192"  # Groq model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

### Email Configuration (Optional)

For email notifications, configure SMTP in `.env`:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Calendar Integration (Optional)

For Google Calendar integration, add OAuth credentials:

```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

## 📊 System Workflow

```
Resume Upload → Parse Resume → Store in DB
                    ↓
              Compliance Scan
                    ↓
              Job Matching (RAG)
                    ↓
              Rank Candidates
                    ↓
              Recruiter Review
                    ↓
              ┌─────┴─────┐
         Shortlist     Reject
              ↓             ↓
      Schedule Interview  Send Rejection
              ↓
      Send Invitation
              ↓
      Interview Reminder
```

## 🤖 Agent Details

### 1. Orchestrator Agent (Hierarchical Manager)
- **Role**: Master coordinator
- **Tools**: All sub-agents
- **Pattern**: Hierarchical delegation
- **Responsibility**: End-to-end workflow management

### 2. Resume Parsing Agent
- **Role**: Document processor
- **Tools**: Resume Parser, Database, Vector Search
- **Responsibility**: Extract and structure resume data

### 3. Matching Agent
- **Role**: Intelligent matcher
- **Tools**: Database, Vector Search, RAG
- **Responsibility**: Semantic job-candidate matching

### 4. Scheduling Agent
- **Role**: Interview coordinator
- **Tools**: Calendar, Database
- **Responsibility**: Find slots and book interviews

### 5. Communication Agent
- **Role**: Candidate liaison
- **Tools**: Email, Database
- **Responsibility**: All candidate communications

### 6. Compliance Agent
- **Role**: Ethics officer
- **Tools**: Database, LLM
- **Responsibility**: Bias detection and audit trails

## 🛠️ Tools (MCP-Compliant)

1. **Resume Parser Tool** - Extract text from PDF/DOCX
2. **Database Tool** - MongoDB CRUD operations
3. **Vector Search Tool** - FAISS semantic search
4. **Email Tool** - SMTP email sending
5. **Calendar Tool** - Schedule management

All tools are registered with the MCP server for standardized access.

## 📈 Testing

### Test Resume Upload

```python
import requests

files = {'file': open('sample_resume.pdf', 'rb')}
response = requests.post('http://localhost:8000/upload/resume', files=files)
print(response.json())
```

### Test Job Creation and Matching

```python
# Create job
job_data = {
    "job_id": "TEST-001",
    "title": "AI Engineer",
    "description": "Build AI systems",
    "required_skills": ["Python", "TensorFlow", "NLP"],
    "experience_required": 3
}
response = requests.post('http://localhost:8000/jobs/', json=job_data)

# Upload resume (will auto-match)
files = {'file': open('ai_engineer_resume.pdf', 'rb')}
response = requests.post('http://localhost:8000/upload/resume', files=files)

# Check matches
response = requests.get('http://localhost:8000/jobs/TEST-001/candidates')
print(response.json())
```

## 🔒 Security & Compliance

- Bias detection in candidate evaluation
- Audit logging for all actions
- GDPR-compliant data handling
- Secure file uploads with validation
- MongoDB access control

## 📝 Database Schema

### Collections

**candidates**
- name, email, phone
- skills, experience_years, education
- resume_text, score
- matched_jobs, status

**jobs**
- job_id, title, description
- required_skills, experience_required
- status, matched_candidates

**interviews**
- candidate_id, job_id, recruiter_id
- scheduled_time, status
- meeting_link, notes

**compliance_logs**
- action_type, timestamp
- bias_scan results
- audit trails

## 🚦 Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### Environment Variables for Production

```bash
DEBUG=False
MONGODB_URL=mongodb://mongo:27017
GROQ_API_KEY=<production-key>
```

## 📊 Monitoring & Logs

Logs are stored in `logs/` directory with rotation:
- Application logs
- Agent interactions
- Tool executions
- Error traces

## 🤝 Contributing

This is a complete, production-ready system. Key extension points:

1. Add more tools via MCP
2. Create new specialized agents
3. Implement additional LLM providers
4. Add more communication channels (Slack, SMS)
5. Enhance compliance rules

## 📄 License

MIT License

## 🆘 Support

For issues or questions:
1. Check API docs at `/docs`
2. Review logs in `logs/` directory
3. Check MongoDB connection
4. Verify Groq API key

---

**Built with**: CrewAI, FastAPI, Groq, MongoDB, FAISS, LlamaIndex

**Architecture**: Hierarchical Multi-Agent System with MCP

**Status**: Production Ready ✅