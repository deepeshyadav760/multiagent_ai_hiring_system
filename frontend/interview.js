// frontend/interview.js

const statusEl = document.getElementById('status');
const webcamEl = document.getElementById('webcam');
const indicatorEl = document.getElementById('indicator');

const interviewId = new URLSearchParams(window.location.search).get('interview_id');
let mediaRecorder;
let audioChunks = [];
let socket;
let faceApiInterval; // To hold the interval ID

// 1. Setup Webcam and Face Detection
async function setupCamera() {
    try {
        await faceapi.nets.tinyFaceDetector.loadFromUri('models');
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        webcamEl.srcObject = stream;
        
        faceApiInterval = setInterval(async () => {
            if (!webcamEl.srcObject) return;
            const detections = await faceapi.detectAllFaces(webcamEl, new faceapi.TinyFaceDetectorOptions());
            if (detections.length === 0) {
                // You can add visual feedback if desired
            }
        }, 3000);

        return stream;
    } catch (err) {
        statusEl.textContent = "Error: Could not access camera or microphone. Please check permissions.";
        console.error(err);
    }
}

// 2. Setup WebSocket
function setupWebSocket(stream) {
    // socket = new WebSocket(`ws://localhost:8000/ws/interview/${interviewId}`);

    socket = new WebSocket(`wss://0f26c1f1e980.ngrok-free.app/ws/interview/${interviewId}`);

    socket.onopen = () => statusEl.textContent = "Connection established. The interview will begin shortly.";

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleServerMessage(data, stream);
    };

    socket.onclose = () => {
        statusEl.textContent = "Interview session has ended. You may now close this window.";
        stopEverything(); // Call the cleanup function
    };
    
    socket.onerror = () => {
        statusEl.textContent = "A connection error occurred. Please refresh the page.";
        stopEverything(); // Call the cleanup function
    };
}

// 3. Handle incoming messages from the server
function handleServerMessage(data, stream) {
    statusEl.innerHTML = `<strong>AI:</strong> ${data.text}`;

    switch(data.type) {
        case "question":
        case "status":
        case "thank_you":
            const utterance = new SpeechSynthesisUtterance(data.text);
            window.speechSynthesis.speak(utterance);
            
            utterance.onend = () => {
                if (data.type === "question") {
                    startRecording(stream);
                } else if (data.type === "thank_you") {
                    setTimeout(() => {
                        if (socket && socket.readyState === WebSocket.OPEN) socket.close();
                    }, 4000); // Wait 4 seconds for user to hear the message
                }
            };
            break;

        case "complete":
        case "error":
            stopEverything();
            break;
    }
}

// 4. Handle Audio Recording
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
    }, 30000);
}

// 5. Cleanup function to stop everything
function stopEverything() {
    // Stop the AI from speaking immediately
    window.speechSynthesis.cancel();
    
    // Stop the camera and microphone
    if (webcamEl.srcObject) {
        webcamEl.srcObject.getTracks().forEach(track => track.stop());
        webcamEl.srcObject = null;
    }
    // Stop face detection
    if (faceApiInterval) {
        clearInterval(faceApiInterval);
    }
    // Stop any recording
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
}

// --- Main Execution ---
async function main() {
    const stream = await setupCamera();
    if (stream) {
        setupWebSocket(stream);
    }
}

main();