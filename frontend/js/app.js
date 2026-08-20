// --- App Shell Core Elements ---
const API_BASE_URL = window.UNAR_API_URL || "https://unar-backend.onrender.com";
const WS_BASE_URL = window.UNAR_API_URL 
    ? window.UNAR_API_URL.replace(/^http/, 'ws') 
    : "wss://unar-backend.onrender.com";

const appTitle = document.getElementById('app-title');
const btnBack = document.getElementById('btn-back');
const bottomNav = document.getElementById('app-bottom-nav');

// --- Main Screens ---
const viewHome = document.getElementById('view-home');
const viewRegistration = document.getElementById('view-registration');
const viewPrecheck = document.getElementById('view-precheck');
const viewInterview = document.getElementById('view-interview');
const viewError = document.getElementById('view-error');
const viewCompletion = document.getElementById('view-completion');
const viewResults = document.getElementById('view-results');
const viewProfile = document.getElementById('view-profile');

const screens = [viewHome, viewRegistration, viewPrecheck, viewInterview, viewError, viewCompletion, viewResults, viewProfile];

// --- Results Sub-Screens ---
const resOverview = document.getElementById('res-overview');
const resBehavior = document.getElementById('res-behavior');
const resVoice = document.getElementById('res-voice');
const resAnswers = document.getElementById('res-answers');
const resQuestions = document.getElementById('res-questions');
const resSummary = document.getElementById('res-summary');
const resultsScreens = [resOverview, resBehavior, resVoice, resAnswers, resQuestions, resSummary];

// --- Precheck elements ---
const precheckVideo = document.getElementById('precheck-webcam');
const checkCamera = document.getElementById('check-camera');
const checkMic = document.getElementById('check-mic');
const checkFace = document.getElementById('check-face');
const btnStartInterview = document.getElementById('btn-start-interview');

// --- Interview elements ---
const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d', { willReadFrequently: true });
const micStatus = document.getElementById('mic-status-indicator');

// --- State ---
let stream = null;
let ws = null;
let intervalId = null;
let currentSessionId = null;
let currentQuestionIndex = 0;
let currentQuestionText = "";
let mediaRecorder = null;
let audioChunks = [];
let isProcessingAnswer = false;
let isFinalizing = false;
let interviewCompleted = false;

// Precheck state
let isCameraReady = false;
let isMicrophoneReady = false;
let isFaceDetectionReady = false;
const FRAME_RATE = 100; // ms

// --- Navigation State ---
let historyStack = [];
let activeScreenId = 'view-home';
let savedAssessment = null;
let lastScore = null;
let lastDivision = null;

// --- INITIALIZATION ---
function initApp() {
    // Setup initial state
    updateHeaderAndNav('view-home');
    
    // Bottom Nav Listeners
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.tab;
            if (target === 'home') switchAppView('view-home', true, true);
            else if (target === 'interview') {
                if (currentSessionId && !interviewCompleted && activeScreenId !== 'view-registration' && activeScreenId !== 'view-precheck') {
                     switchAppView('view-interview', true, true);
                } else if (!currentSessionId) {
                     switchAppView('view-registration', true, true);
                }
            }
            else if (target === 'results') {
                if (savedAssessment) {
                    switchAppView('view-results', true, true);
                } else {
                    alert("Complete an assessment first.");
                }
            }
            else if (target === 'profile') switchAppView('view-profile', true, true);
        });
    });

    // Back Button
    btnBack.addEventListener('click', () => {
        if (historyStack.length > 0) {
            const previousViewId = historyStack.pop();
            switchAppView(previousViewId, false, false, true); // isBack = true
        }
    });

    // Results Sub-Screen Navigation (Mobile Bottom Nav)
    document.querySelectorAll('.btn-nav-results').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const target = e.target.dataset.target;
            if (target) switchResultsScreen(`res-${target}`);
        });
    });

    // Desktop Sidebar Navigation
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener('click', (e) => {
            const tab = e.target.dataset.tab;
            const target = e.target.dataset.target;

            // Handle main app views
            if (tab) {
                if (tab === 'home') switchAppView('view-home', true, true);
                else if (tab === 'interview') {
                    if (currentSessionId && !interviewCompleted && activeScreenId !== 'view-registration' && activeScreenId !== 'view-precheck') {
                         switchAppView('view-interview', true, true);
                    } else if (!currentSessionId) {
                         switchAppView('view-registration', true, true);
                    }
                }
                else if (tab === 'profile') switchAppView('view-profile', true, true);
            }
            // Handle results sub-screens
            else if (target) {
                if (savedAssessment) {
                    switchAppView('view-results', true, true);
                    switchResultsScreen(`res-${target}`);
                } else {
                    alert("Complete an assessment first.");
                }
            }
        });
    });

    // Home Start Button
    document.getElementById('btn-home-start').addEventListener('click', () => {
        switchAppView('view-registration', true, false);
    });
}

// --- APP NAVIGATION LOGIC ---
function switchAppView(targetId, clearHistory = false, fromNav = false, isBack = false) {
    if (activeScreenId === targetId) return;

    const currentScreen = document.getElementById(activeScreenId);
    const targetScreen = document.getElementById(targetId);

    if (!targetScreen) return;

    if (!clearHistory && !isBack && !fromNav) {
        historyStack.push(activeScreenId);
    } else if (clearHistory) {
        historyStack = [];
    }

    const isDesktop = window.innerWidth >= 768;

    // Determine animation direction
    let outClass = 'fade-out';
    let inClass = 'fade-in';
    
    if (!fromNav && !isDesktop) {
        outClass = isBack ? 'slide-right-out' : 'slide-left-out';
        inClass = isBack ? 'slide-right-in' : 'slide-left-in';
    }

    // Prepare target
    targetScreen.classList.remove('hidden', 'slide-left-in', 'slide-right-in', 'slide-left-out', 'slide-right-out', 'fade-out');
    if (!isDesktop || inClass === 'fade-in') {
        targetScreen.classList.add(inClass);
    }

    // Animate out current
    if (currentScreen) {
        if (!isDesktop || outClass === 'fade-out') {
            currentScreen.classList.add(outClass);
        }
    }

    // Force reflow
    void targetScreen.offsetWidth;

    // Execute transition
    targetScreen.classList.remove(inClass);
    
    setTimeout(() => {
        if (currentScreen) {
            currentScreen.classList.add('hidden');
            currentScreen.classList.remove(outClass);
        }
        activeScreenId = targetId;
        updateHeaderAndNav(targetId);
    }, isDesktop ? 50 : 300); // Faster transition on desktop or just let CSS handle fade
}

function updateHeaderAndNav(viewId) {
    // Show/Hide Back button
    if (historyStack.length > 0 && viewId !== 'view-home' && viewId !== 'view-interview' && viewId !== 'view-results') {
        btnBack.style.visibility = 'visible';
    } else {
        btnBack.style.visibility = 'hidden';
    }

    // Update Title
    const titles = {
        'view-home': 'UNAR',
        'view-registration': 'Setup',
        'view-precheck': 'System Check',
        'view-interview': 'Interview',
        'view-error': 'Error',
        'view-completion': 'Finalizing',
        'view-results': 'Results',
        'view-profile': 'Profile'
    };
    appTitle.textContent = titles[viewId] || 'UNAR';

    // Update Bottom Nav state
    document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
    if (viewId === 'view-home') document.querySelector('.nav-tab[data-tab="home"]').classList.add('active');
    else if (viewId === 'view-interview' || viewId === 'view-registration' || viewId === 'view-precheck') document.querySelector('.nav-tab[data-tab="interview"]').classList.add('active');
    else if (viewId === 'view-results') document.querySelector('.nav-tab[data-tab="results"]').classList.add('active');
    else if (viewId === 'view-profile') document.querySelector('.nav-tab[data-tab="profile"]').classList.add('active');

    // Update Desktop Sidebar Navigation
    document.querySelectorAll('.sidebar-link').forEach(link => link.classList.remove('active'));
    if (viewId === 'view-home') document.querySelector('.sidebar-link[data-tab="home"]')?.classList.add('active');
    else if (viewId === 'view-interview' || viewId === 'view-registration' || viewId === 'view-precheck') document.querySelector('.sidebar-link[data-tab="interview"]')?.classList.add('active');
    else if (viewId === 'view-profile') document.querySelector('.sidebar-link[data-tab="profile"]')?.classList.add('active');

    // Hide bottom nav in critical screens to maximize space
    if (viewId === 'view-interview' || viewId === 'view-precheck' || viewId === 'view-completion' || viewId === 'view-error') {
        bottomNav.classList.add('hidden-down');
    } else {
        bottomNav.classList.remove('hidden-down');
    }
}

function switchResultsScreen(targetId) {
    resultsScreens.forEach(s => {
        if (s.id === targetId) {
            s.classList.remove('hidden');
        } else {
            s.classList.add('hidden');
        }
    });

    // Update Desktop sidebar active state
    const reportNavId = targetId.replace('res-', '');
    document.querySelectorAll('.sidebar-report-nav .sidebar-link').forEach(link => {
        if (link.dataset.target === reportNavId) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

function generateSessionId() {
    return 'sess_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
}

function setIndicator(element, ready) {
    const icon = element.querySelector('.indicator');
    if (ready) {
        icon.className = 'indicator green';
    } else {
        icon.className = 'indicator red';
    }
}

function checkPrecheckStatus() {
    if (isCameraReady && isMicrophoneReady && isFaceDetectionReady) {
        btnStartInterview.disabled = false;
        document.getElementById('precheck-status').classList.add('hidden');
    }
}

// --- Registration Logic ---
document.getElementById('registration-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    currentSessionId = generateSessionId();
    const typeVal = document.getElementById('reg-type').value;
    const payload = {
        session_id: currentSessionId,
        name: document.getElementById('reg-name').value,
        id: document.getElementById('reg-id').value,
        email: document.getElementById('reg-email').value,
        department: document.getElementById('reg-dept').value,
        education: document.getElementById('reg-edu').value,
        type: typeVal,
        division: typeVal
    };
    
    try {
        const res = await fetch(`${API_BASE_URL}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            setupPrecheck();
        } else {
            alert("Failed to register session.");
        }
    } catch (err) {
        console.error(err);
        alert("Server error during registration.");
    }
});

// --- Precheck Logic ---
async function setupPrecheck() {
    switchAppView('view-precheck', false, false);
    
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: true });
        precheckVideo.srcObject = stream;
        
        isCameraReady = true;
        setIndicator(checkCamera, true);
        
        isMicrophoneReady = true;
        setIndicator(checkMic, true);
        
        precheckVideo.addEventListener('loadedmetadata', () => {
            canvas.width = precheckVideo.videoWidth;
            canvas.height = precheckVideo.videoHeight;
        });

        connectWebSocket(precheckVideo, true);
        intervalId = setInterval(() => sendFrame(precheckVideo), FRAME_RATE);
        
    } catch (err) {
        console.error("Error accessing camera/mic:", err);
        document.getElementById('precheck-status').textContent = 'Camera/Microphone access denied. Please allow permissions.';
    }
}

btnStartInterview.addEventListener('click', () => {
    if (!isCameraReady || !isMicrophoneReady || !isFaceDetectionReady) return;
    
    video.srcObject = stream;
    
    if (ws) ws.close();
    if (intervalId) clearInterval(intervalId);
    
    switchAppView('view-interview', true, false);
    
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
    };
    mediaRecorder.onstart = () => { micStatus.textContent = 'Microphone: Recording (Red)'; micStatus.style.color = '#ef4444'; };
    mediaRecorder.onstop = processAndUploadAudio;
    
    connectWebSocket(video, false);
    intervalId = setInterval(() => sendFrame(video), FRAME_RATE);
    
    currentQuestionIndex = 0;
    updateQuestionUI();
});

// --- Interview Logic ---
function setStatus(state) {
    const statusBadge = document.getElementById('interview-status');
    const btnSubmit = document.getElementById('btn-submit-answer');
    
    statusBadge.className = 'status-badge mb-1';
    
    if (state === 'speaking') {
        statusBadge.textContent = 'AI is speaking...';
        statusBadge.classList.add('status-speaking');
        btnSubmit.disabled = true;
    } else if (state === 'listening') {
        statusBadge.textContent = 'Listening to your answer...';
        statusBadge.classList.add('status-listening');
        btnSubmit.disabled = false;
    } else if (state === 'processing') {
        statusBadge.textContent = 'Analyzing your answer...';
        statusBadge.classList.add('status-processing');
        btnSubmit.disabled = true;
    } else if (state === 'finalizing') {
        statusBadge.textContent = 'Generating assessment...';
        statusBadge.classList.add('status-processing');
        btnSubmit.disabled = true;
    }
}

async function updateQuestionUI() {
    if (interviewCompleted) return;
    
    document.getElementById('question-number-display').textContent = `Question ${currentQuestionIndex + 1} of 10`;
    document.getElementById('current-question-text').textContent = "Loading question...";
    setStatus('processing');
    
    try {
        const res = await fetch(`${API_BASE_URL}/api/sessions/${currentSessionId}/next_question?index=${currentQuestionIndex}`);
        if (!res.ok) throw new Error("Failed to fetch next question");
        const data = await res.json();
        currentQuestionText = data.question;
        
        document.getElementById('current-question-text').textContent = currentQuestionText;
        
        const progress = ((currentQuestionIndex) / 10) * 100;
        document.getElementById('question-progress').style.width = `${progress}%`;
        
        setStatus('speaking');
        
        const synth = window.speechSynthesis;
        const msg = new SpeechSynthesisUtterance(currentQuestionText);
        msg.rate = 0.95;
        
        msg.onend = () => {
            audioChunks = [];
            mediaRecorder.start();
            setStatus('listening');
        };
        
        synth.speak(msg);
    } catch (e) {
        console.error(e);
        alert("Failed to load question. Please refresh.");
    }
}

document.getElementById('btn-submit-answer').addEventListener('click', () => {
    if (isProcessingAnswer || isFinalizing || interviewCompleted) return;
    
    isProcessingAnswer = true;
    setStatus('processing');
    
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        micStatus.textContent = 'Microphone: Stopped';
        micStatus.style.color = 'inherit';
    }
});

async function processAndUploadAudio() {
    const webmBlob = new Blob(audioChunks, { type: 'audio/webm' });
    audioChunks = [];
    
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const arrayBuffer = await webmBlob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        const wavBlob = encodeWAV(audioBuffer.getChannelData(0), audioBuffer.sampleRate);
        
        const formData = new FormData();
        formData.append('question_index', currentQuestionIndex + 1);
        formData.append('question_text', currentQuestionText);
        formData.append('audio', wavBlob, 'answer.wav');
        
        const res = await fetch(`${API_BASE_URL}/api/sessions/${currentSessionId}/answer_audio`, {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) throw new Error("Upload failed");
        
        isProcessingAnswer = false;
        
        if (currentQuestionIndex === 9) {
            await triggerFinalization();
        } else {
            currentQuestionIndex++;
            updateQuestionUI();
        }
    } catch (err) {
        console.error(err);
        alert("Failed to process and upload answer. Retrying question.");
        isProcessingAnswer = false;
        setStatus('listening');
        audioChunks = [];
        mediaRecorder.start();
    }
}

async function triggerFinalization() {
    isFinalizing = true;
    interviewCompleted = true;
    setStatus('finalizing');
    
    try {
        const res = await fetch(`${API_BASE_URL}/api/results/${currentSessionId}`, { method: 'POST' });
        const data = await res.json();
        
        if (data.status === 'completed') {
            stopCamera();
            showCompletionTransitionAndReport(data.assessment);
        } else if (data.status === 'failed') {
            stopCamera();
            switchAppView('view-error', true, false);
        } else {
            setTimeout(checkFinalizationStatus, 2000);
        }
    } catch (e) {
        stopCamera();
        switchAppView('view-error', true, false);
    }
}

async function checkFinalizationStatus() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/results/${currentSessionId}`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'completed') {
            showCompletionTransitionAndReport(data.assessment);
        } else if (data.status === 'failed') {
            switchAppView('view-error', true, false);
        } else {
            setTimeout(checkFinalizationStatus, 2000);
        }
    } catch (e) {
        switchAppView('view-error', true, false);
    }
}

function showCompletionTransitionAndReport(assessment) {
    switchAppView('view-completion', true, false);
    setTimeout(() => {
        // Show report nav in desktop sidebar
        document.getElementById('desktop-report-nav').classList.remove('hidden');

        renderReport(assessment);
        switchResultsScreen('res-overview');
        switchAppView('view-results', true, false);
        
        // Update Home Screen with latest
        if (assessment && assessment.finalAssessment) {
            lastScore = assessment.finalAssessment.overallScore;
            lastDivision = assessment.interview.division;
            document.getElementById('home-last-score').textContent = `${Math.round(lastScore)}%`;
            document.getElementById('home-last-div').textContent = lastDivision.toUpperCase();
        }

        setTimeout(() => animateScoreRing(assessment.finalAssessment.overallScore), 300);
    }, 2500);
}

document.getElementById('btn-retry-assessment').addEventListener('click', () => {
    switchAppView('view-interview', true, false);
    setStatus('finalizing');
    checkFinalizationStatus();
});

document.getElementById('btn-error-home').addEventListener('click', () => {
    switchAppView('view-home', true, false);
});

function encodeWAV(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    const writeString = (view, offset, string) => {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    };
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);
    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
        let s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Blob([view], { type: 'audio/wav' });
}

// --- Report Rendering (App Style) ---
function animateScoreRing(score) {
    const circle = document.getElementById('score-ring-progress');
    if(!circle) return;
    const radius = circle.r.baseVal.value;
    const circumference = radius * 2 * Math.PI;
    
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    const offset = circumference - (score / 100) * circumference;
    
    requestAnimationFrame(() => {
        circle.style.strokeDashoffset = offset;
    });

    const scoreVal = document.getElementById('res-overall-score');
    let current = 0;
    const inc = score / 50;
    const int = setInterval(() => {
        current += inc;
        if (current >= score) {
            current = score;
            clearInterval(int);
        }
        scoreVal.textContent = Math.round(current);
    }, 20);
}

function formatVal(val, suffix='') {
    if (val === undefined || val === null || isNaN(val)) return 'Unavailable';
    return Math.round(val) + suffix;
}

function setWidth(id, percent) {
    const el = document.getElementById(id);
    if(el && percent !== undefined && !isNaN(percent)) {
        setTimeout(() => el.style.width = `${Math.min(100, Math.max(0, percent))}%`, 300);
    }
}

function setMetricStatus(id, value, thresholdHigh, thresholdLow) {
    const el = document.getElementById(id);
    if (!el || value === undefined || isNaN(value)) return;
    
    if (value >= thresholdHigh) {
        el.textContent = "STRONG";
        el.className = "tile-status good";
    } else if (value >= thresholdLow) {
        el.textContent = "AVERAGE";
        el.className = "tile-status warn";
    } else {
        el.textContent = "NEEDS WORK";
        el.className = "tile-status error";
    }
}

function renderReport(dataset) {
    savedAssessment = dataset;
    const final = dataset.finalAssessment;
    
    // Overview
    const dynamicBarsContainer = document.getElementById('dynamic-category-bars');
    dynamicBarsContainer.innerHTML = ''; 
    if (final.categories && final.categories.length > 0) {
        final.categories.forEach((cat, index) => {
            const barId = `dyn-bar-${index}`;
            const html = `
                <div class="category-row">
                    <div class="category-label">
                        <span>${cat.name}</span>
                        <span id="dyn-val-${index}">${formatVal(cat.score, '%')}</span>
                    </div>
                    <div class="category-bar"><div class="category-fill" id="${barId}" style="width:0%"></div></div>
                </div>
            `;
            dynamicBarsContainer.insertAdjacentHTML('beforeend', html);
            setWidth(barId, cat.score);
        });
    }
    
    document.getElementById('res-list-strengths').innerHTML = final.topStrengths.map(s => `<li>${s}</li>`).join('');
    document.getElementById('res-list-improvements').innerHTML = final.topImprovements.map(i => `<li>${i}</li>`).join('');
    
    // Aggregates
    const qCount = dataset.questions.length;
    let avgEye = 0, avgHead = 0, avgFace = 0, avgBlink = 0;
    let avgWpm = 0, avgPauses = 0, avgFillers = 0, avgEnergy = 0;
    
    dataset.questions.forEach(q => {
        avgEye += q.cameraMetrics.eyeContact || 0;
        avgHead += q.cameraMetrics.headStability || 0;
        avgFace += q.cameraMetrics.facePresence || 0;
        avgBlink += q.cameraMetrics.blinkRate || 0;
        
        avgWpm += q.voiceMetrics.speechRate || 0;
        avgPauses += q.voiceMetrics.longPauseCount || 0;
        avgFillers += q.voiceMetrics.fillerWordCount || 0;
        avgEnergy += q.voiceMetrics.voiceEnergy || 0;
    });
    
    avgEye /= qCount; avgHead /= qCount; avgFace /= qCount; avgBlink /= qCount;
    avgWpm /= qCount; avgPauses /= qCount; avgFillers /= qCount; avgEnergy /= qCount;

    // Behavior
    document.getElementById('res-eye').textContent = formatVal(avgEye, '%');
    setMetricStatus('stat-eye', avgEye, 80, 50);
    setWidth('fill-eye', avgEye);
    document.getElementById('desc-eye').textContent = avgEye > 80 ? "Excellent eye contact maintained." : "Try to look at the camera more often.";

    document.getElementById('res-head').textContent = formatVal(avgHead, '%');
    setMetricStatus('stat-head', avgHead, 80, 50);
    setWidth('fill-head', avgHead);
    document.getElementById('desc-head').textContent = avgHead > 80 ? "Head posture was very stable." : "Avoid excessive head movement.";

    document.getElementById('res-face').textContent = formatVal(avgFace, '%');
    setMetricStatus('stat-face', avgFace, 90, 70);
    setWidth('fill-face', avgFace);
    document.getElementById('desc-face').textContent = avgFace > 90 ? "Face perfectly centered." : "Ensure your face is visible.";

    document.getElementById('res-blink').textContent = formatVal(avgBlink, '/min');
    setMetricStatus('stat-blink', (100 - Math.abs(20 - avgBlink)*2), 70, 40); 
    document.getElementById('desc-blink').textContent = avgBlink < 10 ? "Low blink rate (staring)." : (avgBlink > 30 ? "High blink rate (nervous)." : "Normal, relaxed blink rate.");

    // Voice
    document.getElementById('res-wpm').textContent = formatVal(avgWpm);
    document.getElementById('res-fillers').textContent = formatVal(avgFillers);
    
    const pStat = document.getElementById('stat-pauses');
    pStat.textContent = avgPauses > 2 ? "HIGH" : (avgPauses > 0 ? "MODERATE" : "LOW");
    pStat.className = avgPauses > 2 ? "tile-status error text-large" : "tile-status good text-large";
    
    const eStat = document.getElementById('stat-energy');
    eStat.textContent = avgEnergy > 70 ? "HIGH" : (avgEnergy > 40 ? "STABLE" : "LOW");
    eStat.className = avgEnergy > 40 ? "tile-status good text-large" : "tile-status warn text-large";
    
    setWidth('fill-voice-perf', final.voiceScore);
    document.getElementById('val-voice-perf').textContent = formatVal(final.voiceScore, '%');

    // Answers (Chart)
    const chart = document.getElementById('answer-chart');
    const chartLabels = document.getElementById('answer-chart-labels');
    chart.innerHTML = '';
    chartLabels.innerHTML = '';
    
    dataset.questions.forEach(q => {
        const wrap = document.createElement('div');
        wrap.className = 'chart-bar-wrapper';
        
        const bar = document.createElement('div');
        bar.className = 'chart-bar';
        setTimeout(() => { bar.style.height = `${Math.max(5, q.answerScore)}%`; }, 600);
        
        wrap.appendChild(bar);
        chart.appendChild(wrap);
        
        const lbl = document.createElement('div');
        lbl.className = 'chart-label';
        lbl.textContent = `Q${q.questionNumber}`;
        chartLabels.appendChild(lbl);
    });

    // Questions Grid
    const qwList = document.getElementById('qw-list');
    qwList.innerHTML = '';
    dataset.questions.forEach((q, idx) => {
        const btn = document.createElement('button');
        btn.className = 'qw-grid-btn';
        if (idx === 0) btn.classList.add('active');
        btn.textContent = `Q${q.questionNumber}`;
        btn.onclick = () => selectQuestionDetails(idx);
        qwList.appendChild(btn);
    });
    selectQuestionDetails(0);

    // Summary
    document.getElementById('res-summary-text').textContent = final.summary;
    const recs = document.getElementById('res-recommendations');
    recs.innerHTML = '';
    if (final.recommendation) {
        const parts = final.recommendation.split(/\d+\.\s/).filter(x => x.trim().length > 0);
        if (parts.length > 0) {
            parts.forEach(p => {
                const li = document.createElement('li');
                li.textContent = p.trim();
                recs.appendChild(li);
            });
        } else {
            recs.innerHTML = `<li>${final.recommendation}</li>`;
        }
    }
}

function selectQuestionDetails(idx) {
    if (!savedAssessment) return;
    
    const items = document.getElementById('qw-list').querySelectorAll('.qw-grid-btn');
    items.forEach((item, i) => {
        if (i === idx) item.classList.add('active');
        else item.classList.remove('active');
    });

    const q = savedAssessment.questions[idx];
    document.getElementById('qw-title').textContent = `QUESTION ${q.questionNumber}`;
    document.getElementById('qw-question').textContent = q.question;
    document.getElementById('qw-transcript').textContent = q.transcript || '(No response recorded)';
    document.getElementById('qw-score').textContent = q.answerScore;
    
    document.getElementById('qw-strengths').innerHTML = q.strengths && q.strengths.length ? q.strengths.map(s => `<li>${s}</li>`).join('') : '<li>None identified</li>';
    document.getElementById('qw-improvements').innerHTML = q.improvements && q.improvements.length ? q.improvements.map(i => `<li>${i}</li>`).join('') : '<li>None identified</li>';
}

// Download Logic
let isDownloading = false;
document.getElementById('btn-download-report').addEventListener('click', async function() {
    if (isDownloading) return;
    isDownloading = true;
    
    const btn = this;
    const originalText = btn.textContent;
    btn.textContent = "GENERATING...";
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/report/${currentSessionId}`, { method: 'GET' });
        if (!response.ok) throw new Error("Failed to generate PDF");
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `UNAR_${lastDivision}_Assessment.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        btn.textContent = "DOWNLOAD COMPLETE";
        setTimeout(() => { btn.textContent = originalText; isDownloading = false; }, 3000);
        
    } catch (err) {
        console.error(err);
        btn.textContent = "FAILED [ TRY AGAIN ]";
        setTimeout(() => { btn.textContent = originalText; isDownloading = false; }, 4000);
    }
});

// --- WebSocket & Camera Capture ---
function connectWebSocket(sourceVideo, isPrecheck) {
    const wsUrl = `${WS_BASE_URL}/ws/interview/${currentSessionId}`;
    ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (isPrecheck) {
                if (data.face_detected && !isFaceDetectionReady) {
                    isFaceDetectionReady = true;
                    setIndicator(checkFace, true);
                    checkPrecheckStatus();
                }
            }
        } catch (e) {}
    };
}

function sendFrame(sourceVideo) {
    if (ws && ws.readyState === WebSocket.OPEN && sourceVideo.readyState === sourceVideo.HAVE_ENOUGH_DATA) {
        ctx.drawImage(sourceVideo, 0, 0, canvas.width, canvas.height);
        const base64Data = canvas.toDataURL('image/jpeg', 0.8);
        ws.send(base64Data);
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    if (ws) ws.close();
    if (intervalId) clearInterval(intervalId);
}

// Bootstrap
document.addEventListener('DOMContentLoaded', () => {
    initApp();
    
    // Register Service Worker for PWA
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('sw.js')
                .then(registration => {
                    console.log('ServiceWorker registration successful with scope: ', registration.scope);
                })
                .catch(err => {
                    console.error('ServiceWorker registration failed: ', err);
                });
        });
    }
});
