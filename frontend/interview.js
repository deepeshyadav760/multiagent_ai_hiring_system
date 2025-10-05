// frontend/interview.js

// --- DOM Elements ---
const statusEl = document.getElementById('status');
const webcamEl = document.getElementById('webcam');
const indicatorEl = document.getElementById('indicator');
const welcomeUI = document.getElementById('welcome-ui');
const interviewUI = document.getElementById('interview-ui');
const startBtn = document.getElementById('start-interview-btn');
const timerDisplay = document.getElementById('timer-display');
const overlayCanvas = document.getElementById('overlay');

// --- State Variables ---
const interviewId = new URLSearchParams(window.location.search).get('interview_id');
let mediaRecorder;
let audioChunks = [];
let socket;
let proctoringInterval;
let interviewTimer;
let isDetecting = false;

// --- Event Listeners ---
startBtn.addEventListener('click', initializeInterview);

// --- Main Initialization Function ---
async function initializeInterview() {
    startBtn.disabled = true;
    startBtn.textContent = "Setting up, please wait...";

    // 1. Setup camera and load all AI proctoring models
    const stream = await setupCameraAndProctoring();
    
    if (stream) {
        // 2. If setup is successful, switch the UI views
        welcomeUI.style.display = 'none';
        interviewUI.style.display = 'block';
        timerDisplay.style.display = 'inline-block';

        // 3. Connect to the backend WebSocket to start the interview
        setupWebSocket(stream);
        startInterviewTimer(600); // 10 minutes = 600 seconds
    } else {
        // If setup failed (e.g., user denied permissions), re-enable the button
        startBtn.disabled = false;
        startBtn.textContent = "Retry Setup";
    }
}

// --- Feature 1: Camera & AI Proctoring Setup ---
async function setupCameraAndProctoring() {
    try {
        statusEl.textContent = "Loading AI models...";
        await Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri('models'),
            faceapi.nets.faceLandmark68Net.loadFromUri('models'),
            faceapi.nets.faceExpressionNet.loadFromUri('models') 
        ]);

        statusEl.textContent = "Please grant camera and microphone access when prompted...";
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        webcamEl.srcObject = stream;
        
        await new Promise(resolve => webcamEl.onloadedmetadata = resolve);
        
        startProctoring();
        return stream;
    } catch (err) {
        // This is the improved error handling block
        console.error("Camera/Mic Error:", err.name, err.message);

        let userMessage = "An unknown error occurred while trying to access your camera.";
        if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
            userMessage = "Access to camera and microphone was denied. Please click the padlock icon in your address bar to allow permissions and then refresh the page.";
        } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
            userMessage = "No camera or microphone was found on your device. Please ensure they are connected and enabled.";
        } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
             userMessage = "Your camera or microphone is already in use by another application. Please close other apps (like Zoom, Teams, etc.) and try again.";
        }
        
        alert("Error: " + userMessage); // Use an alert to make sure the user sees it
        statusEl.textContent = userMessage; // Also display it on the page
        return null;
    }
}


// --- Feature 2: AI Proctoring Logic ---
function startProctoring() {
    const displaySize = { width: webcamEl.width, height: webcamEl.height };
    faceapi.matchDimensions(overlayCanvas, displaySize);

    proctoringInterval = setInterval(async () => {
        // Use the flag to prevent overlapping detections
        if (isDetecting || !webcamEl.srcObject) {
            return;
        }
        isDetecting = true; // Set the flag

        try {
            const detections = await faceapi.detectAllFaces(webcamEl, new faceapi.TinyFaceDetectorOptions());
            
            // --- Proctoring Rules ---
            if (detections.length === 0) {
                // To avoid flickering, only update the status if it's different
                if (!statusEl.innerHTML.includes("No person detected")) {
                    statusEl.innerHTML = "<strong style='color: red;'>Warning: No person detected. Please stay in frame.</strong>";
                }
            } else if (detections.length > 1) {
                if (!statusEl.innerHTML.includes("Multiple people detected")) {
                    statusEl.innerHTML = "<strong style='color: red;'>Warning: Multiple people detected. Please ensure you are alone.</strong>";
                }
            }
            // If all is well, the status will be updated by handleServerMessage,
            // so we don't need an 'else' block here.

        } catch (error) {
            console.error("Error during face detection:", error);
        } finally {
            isDetecting = false; // Release the flag, allowing the next run
        }
        
    }, 2500); // Increased interval to 2.5 seconds for better performance
}


// --- Feature 3: Interview Timer ---
function startInterviewTimer(duration) {
    let timer = duration;
    interviewTimer = setInterval(() => {
        let minutes = parseInt(timer / 60, 10);
        let seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        timerDisplay.textContent = minutes + ":" + seconds;

        if (--timer < 0) {
            clearInterval(interviewTimer);
            statusEl.textContent = "Time is up! Finalizing interview...";
            if (socket && socket.readyState === WebSocket.OPEN) socket.close();
        }
    }, 1000);
}

// --- WebSocket & Recording Logic ---
function setupWebSocket(stream) {
    // IMPORTANT: Replace this with your LOCALHOST, NGROK, or deployed RENDER URL
    const socketUrl = `ws://localhost:8000/ws/interview/${interviewId}`;
    // const socketUrl = `wss://your-backend-url.onrender.com/ws/interview/${interviewId}`;

    socket = new WebSocket(socketUrl);
    
    socket.onopen = () => statusEl.textContent = "Connection established. The interview will begin shortly.";
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleServerMessage(data, stream);
    };
    socket.onclose = () => {
        statusEl.textContent = "Interview session has ended. You may now close this window.";
        stopEverything();
    };
    socket.onerror = () => {
        statusEl.textContent = "A connection error occurred. Please refresh the page.";
        stopEverything();
    };
}

function handleServerMessage(data, stream) {
    statusEl.innerHTML = `<strong>AI:</strong> ${data.text}`;

    switch(data.type) {
        case "question":
        case "status":
            const utterance = new SpeechSynthesisUtterance(data.text);
            window.speechSynthesis.speak(utterance);
            
            utterance.onend = () => {
                if (data.type === "question") {
                    startRecording(stream);
                }
            };
            break;
        
        case "thank_you":
            const thankYouUtterance = new SpeechSynthesisUtterance(data.text);
            window.speechSynthesis.speak(thankYouUtterance);
            thankYouUtterance.onend = () => {
                setTimeout(() => {
                    if (socket && socket.readyState === WebSocket.OPEN) socket.close();
                }, 4000);
            };
            break;

        case "complete":
        case "error":
            stopEverything();
            break;
    }
}

function startRecording(stream) {
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
    mediaRecorder.onstart = () => {
        statusEl.textContent = "Listening for your answer...";
        indicatorEl.style.display = 'block';
    };
    mediaRecorder.onstop = () => {
        indicatorEl.style.display = 'none';
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(audioBlob);
            statusEl.textContent = "Answer sent. Please wait for the next question...";
        }
    };
    mediaRecorder.start();
    setTimeout(() => {
        if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
    }, 30000); // Stop recording after 30 seconds of speaking time
}

// --- Cleanup Function ---
function stopEverything() {
    window.speechSynthesis.cancel();
    if (webcamEl.srcObject) {
        webcamEl.srcObject.getTracks().forEach(track => track.stop());
        webcamEl.srcObject = null;
    }
    if (proctoringInterval) clearInterval(proctoringInterval);
    if (interviewTimer) clearInterval(interviewTimer);
    if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
}