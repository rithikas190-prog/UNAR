def calculate_eye_contact(face):

    if not face:
        return {
            "score": 0,
            "looking": False,
            "direction": "no_face"
        }

    left_eye = (
        face.landmark[33].x +
        face.landmark[133].x
    ) / 2

    right_eye = (
        face.landmark[362].x +
        face.landmark[263].x
    ) / 2

    eye_center = (left_eye + right_eye) / 2


    if 0.35 < eye_center < 0.65:
        return {
            "score": 90,
            "looking": True,
            "direction": "center"
        }

    elif eye_center <= 0.35:
        return {
            "score": 50,
            "looking": False,
            "direction": "left"
        }

    else:
        return {
            "score": 50,
            "looking": False,
            "direction": "right"
        }