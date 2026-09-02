import cv2

from services.handsign.word_gesture_service import is_word_trained
from services.handsign.word_scoring_service import score_sequence
from utils.handsign.image import decode_base64_image
from utils.handsign.science_vocabulary import canonical_word
from utils.handsign.word_gesture_features import holistic_result_to_feature_vector


def score_frame_sequence(word: str, images: list[str]) -> dict:
    if not images:
        raise ValueError("At least one frame is required.")

    target_word = canonical_word(word)
    if not is_word_trained(target_word):
        raise RuntimeError(f"{target_word} is not available in the trained word model yet.")

    import mediapipe as mp

    mp_holistic = mp.solutions.holistic
    sequence = []
    detected_frames = 0

    with mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.4,
    ) as holistic:
        for image in images:
            frame = decode_base64_image(image)
            result = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if result.pose_landmarks or result.left_hand_landmarks or result.right_hand_landmarks:
                detected_frames += 1
            sequence.append(holistic_result_to_feature_vector(result))

    if detected_frames == 0:
        raise ValueError("No body or hand landmarks were detected in the captured attempt.")

    return score_sequence(target_word, sequence)
