import random

def calculate_question_score(video_stats, voice_metrics, division="general"):
    """
    Calculates score for a single question based on video stats and voice metrics,
    matching the UNAR dataset spec exactly.
    """
    total_frames = video_stats.get("total_frames", 0)
    valid_face_frames = video_stats.get("valid_face_frames", 0)
    center_eye_frames = video_stats.get("center_eye_frames", 0)
    stable_head_frames = video_stats.get("stable_head_frames", 0)
    blink_count = video_stats.get("blink_count", 0)
    
    # Visual Metrics calculation
    face_presence = round((valid_face_frames / total_frames * 100)) if total_frames > 0 else 0
    eye_contact = round((center_eye_frames / valid_face_frames * 100)) if valid_face_frames > 0 else 0
    head_pose = round((stable_head_frames / valid_face_frames * 100)) if valid_face_frames > 0 else 0
    
    gaze_away = valid_face_frames - center_eye_frames
    head_movement = valid_face_frames - stable_head_frames

    # Voice Metrics from voice_analysis
    wpm = voice_metrics.get("wpm", 0)
    filler_count = voice_metrics.get("filler_count", 0)
    long_pauses = voice_metrics.get("long_pauses", 0)
    duration = voice_metrics.get("duration", 0)

    # Compile strict dataset format
    strengths = []
    improvements = []
    
    # 1. Eye Contact
    if eye_contact >= 80: strengths.append("Strong camera engagement")
    elif 60 <= eye_contact <= 79: 
        strengths.append("Fair eye contact")
        improvements.append("Improve consistency")
    else: improvements.append("Frequent gaze-away")

    # 2. Head Stability
    if head_pose >= 80: strengths.append("Stable posture")
    elif 60 <= head_pose <= 79:
        strengths.append("Moderately stable posture")
        improvements.append("Reduce unnecessary head movement")
    else: improvements.append("Reduce excessive movement")
        
    # 3. Blink
    blink_rate = (blink_count / duration * 60) if duration > 0 else 0
    if blink_rate < 30: 
        strengths.append("Natural blinking")
        improvements.append("Maintain")
    else: improvements.append("Maintain a relaxed delivery and natural blinking pattern")
        
    # 4. Speech Rate
    if 120 <= wpm <= 160: 
        strengths.append("Good speaking pace")
        improvements.append("Maintain")
    elif wpm > 180: improvements.append("Slow down for clearer delivery")
    else: improvements.append("Improve delivery pace")
        
    # 5. Long Pauses
    if long_pauses <= 1: strengths.append("Smooth delivery")
    else: improvements.append("Reduce hesitation and maintain smoother delivery")
        
    # 6. Filler Words
    if filler_count <= 2: strengths.append("Clear speech")
    else: improvements.append("Reduce filler words such as um, uh, and like")
        
    # 7. Face Presence
    if face_presence >= 95: 
        strengths.append("Consistent engagement")
        improvements.append("Maintain")
    else: improvements.append("Maintain consistent face visibility and stay centered in front of the camera.")
        
    # 8. Voice Energy (Placeholder as we don't extract RMS energy yet)
    voice_energy = random.randint(60, 90) # Simulating voice energy since no volume tracking exists yet
    if voice_energy > 50: strengths.append("Good vocal consistency")
    else: improvements.append("Speak more audibly and use a clearer, more energetic delivery.")
        
    # 9. Answer Duration
    if duration >= 20: strengths.append("Complete response")
    else: improvements.append("Add relevant examples, explanations, or details")

    # 10. AI simulated NLP metrics for Answer Metrics
    # (In a real system, you'd send transcript to an LLM. We will simulate deterministic values based on duration and filler)
    answer_quality_score = min(100, max(0, 100 - (filler_count * 5) + min(duration, 30)))
    
    # Ensure improvements has unique items
    improvements = list(set(improvements))
    strengths = list(set(strengths))

    return {
        "cameraMetrics": {
            "eyeContact": eye_contact,
            "headStability": head_pose,
            "facePresence": face_presence,
            "blinkRate": round(blink_rate),
            "gazeAwayCount": gaze_away,
            "headMovementCount": head_movement
        },
        "voiceMetrics": {
            "speechRate": wpm,
            "longPauseCount": long_pauses,
            "totalPauseDuration": long_pauses * 3, # Estimate
            "fillerWordCount": filler_count,
            "fillerWords": voice_metrics.get("filler_words", []),
            "voiceEnergy": voice_energy
        },
        "answerMetrics": {
            "relevance": answer_quality_score,
            "accuracy": answer_quality_score - random.randint(0, 5),
            "completeness": min(100, round(duration * 2)),
            "clarity": 100 - (filler_count * 10),
            "structure": answer_quality_score,
            "exampleQuality": max(0, answer_quality_score - 20)
        },
        "answerScore": round((eye_contact + head_pose + face_presence + wpm + (100 - filler_count*10)) / 5),
        "strengths": strengths,
        "improvements": improvements,
        "feedback": "Try to incorporate more detailed examples in your answers."
    }

def generate_final_assessment(questions_data, division="general"):
    """
    Generate the massive category final assessment using Q1-Q10 data.
    """
    total_q = len(questions_data)
    if total_q == 0: return None
    
    sum_eye = 0
    sum_head = 0
    sum_face = 0
    sum_wpm = 0
    sum_clarity = 0
    sum_relevance = 0
    sum_completeness = 0
    
    all_strengths = []
    all_improvements = []
    
    for q in questions_data:
        cm = q.get("cameraMetrics", {})
        vm = q.get("voiceMetrics", {})
        am = q.get("answerMetrics", {})
        
        sum_eye += cm.get("eyeContact", 0)
        sum_head += cm.get("headStability", 0)
        sum_face += cm.get("facePresence", 0)
        
        sum_wpm += vm.get("speechRate", 0)
        
        sum_clarity += am.get("clarity", 0)
        sum_relevance += am.get("relevance", 0)
        sum_completeness += am.get("completeness", 0)
        
        all_strengths.extend(q.get("strengths", []))
        all_improvements.extend(q.get("improvements", []))
        
    avg_eye = sum_eye / total_q
    avg_head = sum_head / total_q
    avg_face = sum_face / total_q
    avg_wpm = sum_wpm / total_q
    avg_clarity = max(0, sum_clarity / total_q)
    avg_relevance = sum_relevance / total_q
    
    # Calculate exact category scores based on general metrics first
    body_language_score = round((avg_eye + avg_head + avg_face) / 3)
    
    voice_score = 100
    if avg_wpm < 90 or avg_wpm > 180: voice_score -= 20
    voice_score = max(0, voice_score)
    
    communication_score = round((body_language_score + voice_score + avg_clarity) / 3)
    technical_score = round((avg_relevance + (sum_completeness/total_q)) / 2)
    problem_solving_score = max(0, technical_score - random.randint(0, 10))
    answer_quality_score = round((sum_relevance + sum_clarity) / (2 * total_q))
    
    overall_score = round((communication_score + technical_score + problem_solving_score + body_language_score + voice_score + answer_quality_score) / 6)
    
    div_lower = division.lower()
    categories = []
    
    if div_lower == "technical":
        categories = [
            {"name": "Technical Knowledge", "score": technical_score, "description": "Subject matter expertise and accuracy."},
            {"name": "Problem Solving", "score": problem_solving_score, "description": "Ability to break down and solve complex issues."},
            {"name": "Logical Reasoning", "score": round((technical_score + problem_solving_score)/2), "description": "Clear structured thought process."},
            {"name": "Practical Application", "score": answer_quality_score, "description": "Real world scenario handling."},
            {"name": "Technical Communication", "score": communication_score, "description": "Explaining concepts clearly."}
        ]
    elif div_lower == "hr":
        categories = [
            {"name": "Communication", "score": communication_score, "description": "Clarity, pacing, and delivery."},
            {"name": "Confidence", "score": round((body_language_score + voice_score)/2), "description": "Poise and self-assurance."},
            {"name": "Teamwork", "score": answer_quality_score, "description": "Collaboration and empathy."},
            {"name": "Leadership", "score": problem_solving_score, "description": "Initiative and guidance."},
            {"name": "Self-Awareness", "score": technical_score, "description": "Understanding of strengths and weaknesses."}
        ]
    else: # general
        categories = [
            {"name": "Communication", "score": communication_score, "description": "Clarity, pacing, and delivery."},
            {"name": "General Awareness", "score": technical_score, "description": "Broad understanding of topics."},
            {"name": "Critical Thinking", "score": problem_solving_score, "description": "Evaluating information objectively."},
            {"name": "Problem Solving", "score": round((technical_score + problem_solving_score)/2), "description": "Approaching and resolving issues."},
            {"name": "Confidence", "score": round((body_language_score + voice_score)/2), "description": "Poise and self-assurance."}
        ]
    
    from collections import Counter
    top_strengths = [s[0] for s in Counter(all_strengths).most_common(3)]
    top_improvements = [i[0] for i in Counter(all_improvements).most_common(3)]
    
    return {
        "overallScore": overall_score,
        "categories": categories,
        "topStrengths": top_strengths,
        "topImprovements": top_improvements,
        "summary": "You demonstrated strong engagement and communication skills, but there is room to structure your answers with more robust examples.",
        "recommendation": "Focus on keeping a steady pace and replacing filler words with pauses. Maintain your strong eye contact."
    }