def calculate_head_pose(face):

    if not face:
        return {
            "direction": "no_face",
            "score": 0
        }


    # Nose tip landmark
    nose_x = face.landmark[1].x
    nose_y = face.landmark[1].y


    if nose_x < 0.40:
        direction = "left"
        score = 60

    elif nose_x > 0.60:
        direction = "right"
        score = 60

    elif nose_y > 0.60:
        direction = "down"
        score = 50

    else:
        direction = "center"
        score = 90


    return {
        "direction": direction,
        "score": score
    }