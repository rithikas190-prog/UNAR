import speech_recognition as sr
import os
import time

def analyze_audio(file_path):
    """
    Analyzes a WAV audio file.
    Returns transcript and metrics.
    """
    recognizer = sr.Recognizer()
    
    transcript = ""
    success = False
    
    try:
        with sr.AudioFile(file_path) as source:
            # Record the duration of the audio
            duration = source.DURATION
            audio_data = recognizer.record(source)
            
            # Use Google Web Speech API for transcription
            try:
                transcript = recognizer.recognize_google(audio_data)
                success = True
            except sr.UnknownValueError:
                transcript = ""
                success = True # Successfully processed, just nothing recognized
            except sr.RequestError as e:
                transcript = f"[Transcription Error: {e}]"
                success = False
    except Exception as e:
        print(f"Error processing audio file: {e}")
        return {
            "transcript": "Audio processing failed",
            "duration": 0,
            "word_count": 0,
            "wpm": 0,
            "filler_count": 0,
            "filler_rate": 0,
            "long_pauses": 0
        }

    # Voice Metrics Analysis
    words = transcript.lower().split()
    word_count = len(words)
    
    # Calculate WPM
    wpm = 0
    if duration > 0:
        wpm = (word_count / duration) * 60
        
    # Filler Words
    filler_words_list = ["um", "uh", "like", "basically", "actually", "you know"]
    filler_count = 0
    for word in words:
        if word in filler_words_list:
            filler_count += 1
            
    filler_rate = 0
    if word_count > 0:
        filler_rate = (filler_count / word_count) * 100
        
    # Basic Pause Analysis (estimated since we don't use heavy audio analysis)
    # Average speaking rate is ~150 words per minute, or 2.5 words per second.
    # Expected duration = word_count / 2.5
    # If actual duration is much longer than expected, we assume there were pauses.
    expected_duration = word_count / 2.5
    extra_time = max(0, duration - expected_duration)
    
    # Estimate 1 long pause for every 3 seconds of extra unaccounted time
    long_pauses = int(extra_time / 3.0)
    
    return {
        "transcript": transcript if transcript else "[No speech detected]",
        "duration": duration,
        "word_count": word_count,
        "wpm": round(wpm, 1),
        "filler_count": filler_count,
        "filler_rate": round(filler_rate, 1),
        "long_pauses": long_pauses
    }