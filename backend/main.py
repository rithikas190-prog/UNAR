import base64
import cv2
import numpy as np
import mediapipe as mp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
import shutil
import uuid
import datetime

from face_detection import detect_face
from blink_detection import calculate_blink
from eye_contact import calculate_eye_contact
from head_pose import calculate_head_pose
from scoring import calculate_question_score, generate_final_assessment
from voice_analysis import analyze_audio
from ai_engine import generate_next_question
import database

app = FastAPI(
    title="UNAR",
    description="Know. Refine. Become. - AI Interview Analysis System"
)

frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5500")
allowed_origins = [url.strip() for url in frontend_url.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "UNAR backend is running"}

DATA_DIR = os.environ.get("RENDER_DATA_DIR", os.path.dirname(__file__))

# Still need an in-memory store for active websocket frames and temp state
# But the final dataset is persisted to SQLite
ACTIVE_SESSIONS = {}

mp_face_mesh = mp.solutions.face_mesh
face_mesh_instance = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

class RegistrationRequest(BaseModel):
    session_id: str
    name: str
    id: str
    email: str
    department: str
    education: str
    type: str # we can keep this for UI backward compatibility, but we will also use it as division or expect division
    division: str

def init_question_stats():
    return {
        "total_frames": 0,
        "valid_face_frames": 0,
        "center_eye_frames": 0,
        "stable_head_frames": 0,
        "blink_count": 0,
        "was_blinking_last_frame": False,
    }

@app.post("/api/register")
async def register_candidate(req: RegistrationRequest):
    division_lower = req.division.lower()
    if division_lower not in ["technical", "hr", "general"]:
        raise HTTPException(status_code=400, detail="Invalid division. Must be technical, hr, or general.")

    session_id = req.session_id
    start_time = datetime.datetime.now().isoformat()
    
    # Save to SQLite
    database.create_interview(
        interview_id=session_id,
        candidate_name=req.name,
        candidate_role=req.type,
        start_time=start_time
    )
    
    # Initialize the base dataset structure
    dataset = {
        "interview": {
            "interviewId": session_id,
            "candidateId": req.id,
            "startTime": start_time,
            "endTime": None,
            "division": division_lower,
            "totalQuestions": 10,
            "completedQuestions": 0,
            "status": "active"
        },
        "candidate": {
            "name": req.name,
            "role": req.type
        },
        "questions": [],
        "finalAssessment": None
    }
    database.save_assessment(session_id, dataset)
    
    # Init active memory for websocket frames
    ACTIVE_SESSIONS[session_id] = {
        "current_question_stats": init_question_stats()
    }
    
    return {"message": "Session created", "session_id": session_id}

@app.get("/api/sessions/{session_id}/next_question")
async def get_next_question(session_id: str, index: int):
    dataset = database.get_assessment(session_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Session not found")
        
    division = dataset["interview"].get("division", "general")
    previous_questions = [q["question"] for q in dataset.get("questions", [])]
    
    question_text = generate_next_question(
        division=division,
        question_number=index + 1,
        previous_questions=previous_questions,
        candidate_profile=dataset.get("candidate", {})
    )
    
    return {"question": question_text, "question_index": index}

@app.post("/api/sessions/{session_id}/answer_audio")
async def save_answer_audio(
    session_id: str,
    question_index: int = Form(...),
    question_text: str = Form(...),
    audio: UploadFile = File(...)
):
    dataset = database.get_assessment(session_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session_id not in ACTIVE_SESSIONS:
        # Rehydrate if server restarted
        ACTIVE_SESSIONS[session_id] = {"current_question_stats": init_question_stats()}
        
    session = ACTIVE_SESSIONS[session_id]
    division = dataset["interview"].get("division", "general")
    
    # Save audio to temp file
    temp_dir = os.path.join(DATA_DIR, "temp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{session_id}_q{question_index}.wav")
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
        
    # Analyze Audio
    voice_metrics = analyze_audio(temp_path)
    
    # Combine with video stats
    video_stats = session["current_question_stats"]
    
    # Calculate score returning the exact structure
    question_result = calculate_question_score(video_stats, voice_metrics, division=division)
    
    # Format the strict question structure
    q_data = {
        "questionNumber": question_index,
        "question": question_text,
        "category": "General", # Could be dynamic
        "audioReference": temp_path,
        "transcript": voice_metrics.get("transcript", ""),
        "answerDuration": voice_metrics.get("duration", 0),
        "cameraMetrics": question_result["cameraMetrics"],
        "voiceMetrics": question_result["voiceMetrics"],
        "answerMetrics": question_result["answerMetrics"],
        "answerScore": question_result["answerScore"],
        "strengths": question_result["strengths"],
        "improvements": question_result["improvements"],
        "feedback": question_result["feedback"]
    }
    
    # Save Answer to Dataset
    dataset["questions"].append(q_data)
    dataset["interview"]["completedQuestions"] += 1
    database.save_assessment(session_id, dataset)
    
    # Reset video stats for next question
    session["current_question_stats"] = init_question_stats()
    
    return {"message": "Answer processed", "result": question_result}

@app.post("/api/results/{session_id}")
async def finalize_results(session_id: str):
    dataset = database.get_assessment(session_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Session not found")
        
    status = dataset["interview"]["status"]
    division = dataset["interview"].get("division", "general")
    
    # Idempotency
    if status == "processing":
        return {"status": "processing", "message": "Assessment is already generating"}
    if status == "completed":
        return {"status": "completed", "assessment": dataset}
        
    if len(dataset["questions"]) < 10:
        raise HTTPException(status_code=400, detail="Cannot finalize before all 10 questions are answered")
        
    # Lock for processing
    dataset["interview"]["status"] = "processing"
    database.save_assessment(session_id, dataset)
    database.update_interview_status(session_id, "processing")
    
    try:
        # Generate Final Assessment
        final_assessment = generate_final_assessment(dataset["questions"], division=division)
        final_assessment["generatedAt"] = datetime.datetime.now().isoformat()
        
        dataset["finalAssessment"] = final_assessment
        dataset["interview"]["status"] = "completed"
        dataset["interview"]["endTime"] = datetime.datetime.now().isoformat()
        
        # Persist complete
        database.save_assessment(session_id, dataset)
        database.update_interview_status(session_id, "completed", dataset["interview"]["endTime"])
        
        return {"status": "completed", "assessment": dataset}
        
    except Exception as e:
        dataset["interview"]["status"] = "failed"
        database.save_assessment(session_id, dataset)
        database.update_interview_status(session_id, "failed")
        print(f"Error generating assessment: {e}")
        return {"status": "failed", "error": {"code": "ASSESSMENT_GENERATION_FAILED", "message": "Assessment generation failed. Please retry."}}

@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    dataset = database.get_assessment(session_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Session not found")
    return dataset

@app.get("/api/report/{session_id}")
async def get_report_pdf(session_id: str):
    dataset = database.get_assessment(session_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Session not found")
    
    from report_generator import generate_pdf_report
    temp_dir = os.path.join(DATA_DIR, "temp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    pdf_path = os.path.join(temp_dir, f"{session_id}_report.pdf")
    
    generate_pdf_report(dataset, pdf_path)
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="PDF generation failed")
        
    return FileResponse(pdf_path, media_type='application/pdf', filename=f"UNAR_Report_{dataset['candidate']['name']}.pdf")

@app.websocket("/ws/interview/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if session_id not in ACTIVE_SESSIONS:
        # Ensure session exists even if server restarted
        db_session = database.get_interview(session_id)
        if not db_session:
            await websocket.close(code=1008, reason="Invalid session")
            return
        ACTIVE_SESSIONS[session_id] = {"current_question_stats": init_question_stats()}
        
    session = ACTIVE_SESSIONS[session_id]
    
    try:
        while True:
            data = await websocket.receive_text()
            
            if "," in data:
                header, encoded = data.split(",", 1)
            else:
                encoded = data

            img_data = base64.b64decode(encoded)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                continue

            stats = session["current_question_stats"]
            stats["total_frames"] += 1
            is_face = detect_face(frame)
            
            result_json = {
                "face_detected": is_face,
                "blink": {"blink_detected": False, "eye_status": "no_face", "ear": 0, "score": 0},
                "eye_contact": {"looking": False, "direction": "no_face", "score": 0},
                "head_pose": {"direction": "no_face", "score": 0},
            }
            
            if is_face:
                stats["valid_face_frames"] += 1
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                fm_result = face_mesh_instance.process(rgb_frame)
                
                if fm_result.multi_face_landmarks:
                    face = fm_result.multi_face_landmarks[0]
                    
                    blink_data = calculate_blink(face)
                    eye_data = calculate_eye_contact(face)
                    head_data = calculate_head_pose(face)
                    
                    # Accumulate
                    if eye_data.get("looking", False) or eye_data.get("direction") == "Center":
                        stats["center_eye_frames"] += 1
                        
                    if head_data.get("direction") == "Forward":
                        stats["stable_head_frames"] += 1
                        
                    is_blinking = blink_data.get("blink_detected", False)
                    if is_blinking and not stats["was_blinking_last_frame"]:
                        stats["blink_count"] += 1
                    stats["was_blinking_last_frame"] = is_blinking
                    
                    result_json["blink"] = blink_data
                    result_json["eye_contact"] = eye_data
                    result_json["head_pose"] = head_data
                    
            await websocket.send_json(result_json)
            
    except WebSocketDisconnect:
        print(f"Client disconnected for session {session_id}")
    except Exception as e:
        print(f"Error in websocket for session {session_id}: {e}")

# Mount frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")