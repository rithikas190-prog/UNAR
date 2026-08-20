# Eye landmark points
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145

RIGHT_EYE_TOP = 386
RIGHT_EYE_BOTTOM = 374


def calculate_blink(face):

    if not face:
        return {
            "blink_detected": False,
            "eye_status": "no_face",
            "score": 0
        }



    left_eye_open = abs(
        face.landmark[LEFT_EYE_TOP].y -
        face.landmark[LEFT_EYE_BOTTOM].y
    )

    right_eye_open = abs(
        face.landmark[RIGHT_EYE_TOP].y -
        face.landmark[RIGHT_EYE_BOTTOM].y
    )


    eye_ratio = (left_eye_open + right_eye_open) / 2


    if eye_ratio < 0.015:
        return {
            "blink_detected": True,
            "eye_status": "closed",
            "ear": round(eye_ratio, 4),
            "score": 100
        }

    else:
        return {
            "blink_detected": False,
            "eye_status": "open",
            "ear": round(eye_ratio, 4),
            "score": 100
        }