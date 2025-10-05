// script.js

const API_BASE = 'http://localhost:8000';
// const API_BASE = 'https://0f26c1f1e980.ngrok-free.app'

// State
let currentTab = 'dashboard';

// DOM Elements
const loadingEl = document.getElementById('loading');
const notificationEl = document.getElementById('notification');
const fileUploadEl = document.getElementById('file-upload');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    setupDynamicEventListeners();
    loadData();
});

// --- EVENT LISTENERS ---
function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });

    // File upload
    fileUploadEl.addEventListener('change', handleFileUpload);
}

function setupDynamicEventListeners() {
    const mainContent = document.querySelector('.main-content');
    mainContent.addEventListener('click', (event) => {
        const deleteButton = event.target.closest('.delete-btn');
        if (deleteButton) {
            const jobId = deleteButton.dataset.jobId;
            if (jobId) {
                handleDeleteJob(jobId);
            }
        }
    });
}

// --- CORE LOGIC ---
function switchTab(tabName) {
    if (currentTab === tabName) return;
    currentTab = tabName;
    
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    loadData();
}

async function loadData() {
    loadingEl.classList.remove('hidden');
    try {
        let data;
        switch (currentTab) {
            case 'dashboard':
                data = await fetchData('/stats');
                renderDashboard(data.stats || data);
                break;
            case 'jobs':
                data = await fetchData('/jobs/');
                renderJobs(data.jobs || []);
                break;
            case 'candidates':
                data = await fetchData('/candidates/');
                renderCandidates(data.candidates || []);
                break;
            case 'interviews':
                data = await fetchData('/interviews/');
                renderInterviews(data.interviews || []);
                break;
        }
    } catch (error) {
        showNotification(`Error loading data: ${error.message}`, 'error');
    } finally {
        loadingEl.classList.add('hidden');
    }
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    showNotification('Uploading and processing resume...', 'success');
    loadingEl.classList.remove('hidden');
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/upload-resume/`, {
            method: 'POST',
            body: formData,
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.detail || 'Upload failed.');
        }
        showNotification(result.message || 'Resume processed!', 'success');
        switchTab('candidates');
    } catch (error) {
        showNotification(`Upload failed: ${error.message}`, 'error');
    } finally {
        fileUploadEl.value = '';
        loadingEl.classList.add('hidden');
    }
}

async function handleDeleteJob(jobId) {
    if (!confirm(`Are you sure you want to delete job posting ${jobId}?`)) return;

    showNotification(`Deleting job ${jobId}...`, 'success');
    loadingEl.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}`, { method: 'DELETE' });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.detail || 'Failed to delete job.');
        }
        showNotification(result.message || 'Job deleted successfully!', 'success');
        await loadData(); // Refresh list
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        loadingEl.classList.add('hidden');
    }
}

// --- API HELPER ---
async function fetchData(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`);
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Server returned status ${response.status}`);
    }
    return response.json();
}

// --- UI RENDERING ---

function renderDashboard(statsData) {
    // ... (no changes needed here)
    if (!statsData) return;
    document.getElementById('stat-candidates').textContent = statsData.total_candidates ?? '0';
    document.getElementById('stat-jobs').textContent = statsData.active_jobs ?? '0';
    document.getElementById('stat-interviews').textContent = statsData.interviews_scheduled ?? '0';
    document.getElementById('stat-vectors').textContent = statsData.vector_count ?? '0';
}

function renderJobs(jobs) {
    // ... (no changes needed here)
    const container = document.getElementById('jobs-container');
    document.getElementById('jobs-count').textContent = `${jobs.length} total`;
    if (jobs.length === 0) {
        container.innerHTML = createEmptyState('No job postings found.', 'New jobs will appear here once they are added.');
        return;
    }
    container.innerHTML = jobs.map(job => `
        <div class="card">
            <div class="card-header">
                <div>
                    <h3 class="card-title">${job.title || 'No Title'}</h3>
                    <p class="card-subtitle">${job.location || 'N/A'} | ${job.employment_type || 'N/A'}</p>
                </div>
                <div class="card-actions">
                    <span class="badge badge-green">Active</span>
                    <button class="delete-btn" data-job-id="${job.job_id}" title="Delete Job Posting">
                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
                    </button>
                </div>
            </div>
            <p class="card-description">${job.description || 'No description available.'}</p>
            <div class="skills-tags">${(job.required_skills || []).map(skill => `<span class="skill-tag">${skill}</span>`).join('')}</div>
        </div>
    `).join('');
}


function renderCandidates(candidates) {
    // ... (no changes needed here)
    const container = document.getElementById('candidates-container');
    document.getElementById('candidates-count').textContent = `${candidates.length} total`;
    if (candidates.length === 0) {
        container.innerHTML = createEmptyState('No candidates found.', 'Upload a resume to get started.');
        return;
    }
    container.innerHTML = candidates.map(candidate => `
        <div class="card">
            <div class="card-header">
                <div>
                    <h3 class="card-title">${candidate.name || 'Unnamed Candidate'}</h3>
                    <p class="card-subtitle">Matched Jobs: ${(candidate.matched_jobs || []).join(', ') || 'N/A'}</p>
                </div>
                <div class="score-display">
                    <p class="score-value ${candidate.score > 75 ? 'score-green' : 'score-red'}">${candidate.score || 0}%</p>
                    <p class="score-label">Match Score</p>
                </div>
            </div>
            <div class="skills-tags">${(candidate.skills || []).map(skill => `<span class="skill-tag-purple">${skill}</span>`).join('')}</div>
        </div>
    `).join('');
}


function renderInterviews(interviews) {
    const container = document.getElementById('interviews-container');
    document.getElementById('interviews-count').textContent = `${interviews.length} total`;

    if (interviews.length === 0) {
        container.innerHTML = createEmptyState('No interviews scheduled.', 'Qualified candidates will be scheduled for interviews automatically.');
        return;
    }

    container.innerHTML = interviews.map(interview => {
        let isAiInterview = interview.status.includes('ai_interview');
        let cardContent = '';

        // Generate card content based on interview type
        if (isAiInterview) {
            let statusBadge = `<span class="badge badge-purple">AI Interview</span>`;
            let footerText = `Status: ${interview.status.replace(/_/g, ' ')}`;
            let meetingBox = '';

            if (interview.status === 'pending_ai_interview') {
                meetingBox = `<div class="meeting-box">
                                <div class="meeting-info">
                                    <p class="meeting-title">AI Interview Room</p>
                                    <p class="meeting-subtitle">Candidate has been invited.</p>
                                </div>
                                <a href="${interview.meeting_link}" target="_blank" class="join-btn" style="background-color: #7c3aed;">Go to Room</a>
                              </div>`;
            } else if (interview.status === 'completed_ai_interview') {
                meetingBox = `<div class="alert alert-success">
                                <strong>Interview Complete!</strong> Final Score: <strong>${interview.interview_score ?? 'N/A'}</strong>
                              </div>`;
            }
            
            cardContent = `
                <div class="card-header">
                    <div>
                        <h3 class="card-title">Candidate: ${interview.candidate_id.split('@')[0]}</h3>
                        <p class="card-subtitle">For Job: ${interview.job_id}</p>
                    </div>
                    ${statusBadge}
                </div>
                <div class="card-footer">
                    <span>${footerText}</span>
                </div>
                ${meetingBox}`;
        } else {
            // This is the original logic for human-scheduled interviews
            cardContent = `
                <div class="card-header">
                    <div>
                        <h3 class="card-title">Candidate: ${interview.candidate_id.split('@')[0]}</h3>
                        <p class="card-subtitle">For Job: ${interview.job_id}</p>
                    </div>
                    <span class="badge badge-blue">${interview.status}</span>
                </div>
                <div class="card-footer">
                    <span>Scheduled for: ${new Date(interview.scheduled_time).toLocaleString()}</span>
                </div>
                <div class="meeting-box">
                    <div class="meeting-info">
                        <p class="meeting-title">Virtual Interview Room</p>
                        <p class="meeting-subtitle">Ready to join the call</p>
                    </div>
                    <a href="${interview.meeting_link}" target="_blank" class="join-btn">Join Now</a>
                </div>`;
        }
        
        return `<div class="card">${cardContent}</div>`;
    }).join('');
}


// --- UI HELPERS ---
function showNotification(message, type = 'success') {
    // ... (no changes needed here)
    notificationEl.textContent = message;
    notificationEl.className = 'notification';
    notificationEl.classList.add(type);
    notificationEl.classList.remove('hidden');
    setTimeout(() => {
        notificationEl.classList.add('hidden');
    }, 5000);
}

function createEmptyState(title, subtitle) {
    // ... (no changes needed here)
    return `
        <div class="empty-state">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 64px; height: 64px; color: #cbd5e1; margin: 0 auto 1rem;">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            </svg>
            <p style="color: #64748b; margin-bottom: 0.5rem;">${title}</p>
            <p style="font-size: 0.875rem; color: #94a3b8;">${subtitle}</p>
        </div>
    `;
}