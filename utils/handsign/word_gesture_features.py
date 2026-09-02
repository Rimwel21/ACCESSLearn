import numpy as np


FEATURE_VERSION = "holistic_pose_hands_sequence_v1"

POSE_LANDMARK_INDICES = [0, 9, 10, 11, 12, 13, 14, 15, 16]
HAND_LANDMARK_COUNT = 21
VALUES_PER_LANDMARK = 4

FRAME_FEATURE_LENGTH = (
    len(POSE_LANDMARK_INDICES) * VALUES_PER_LANDMARK
    + HAND_LANDMARK_COUNT * VALUES_PER_LANDMARK * 2
)


def _landmark_xy(point):
    return np.asarray([float(point.x), float(point.y)], dtype=np.float32)


def _origin_and_scale(result):
    pose = result.pose_landmarks.landmark if result.pose_landmarks else None
    if pose is not None:
        left_shoulder = _landmark_xy(pose[11])
        right_shoulder = _landmark_xy(pose[12])
        shoulder_width = float(np.linalg.norm(left_shoulder - right_shoulder))
        if shoulder_width >= 1e-6:
            origin_xy = (left_shoulder + right_shoulder) / 2.0
            origin_z = float((pose[11].z + pose[12].z) / 2.0)
            return np.asarray([origin_xy[0], origin_xy[1], origin_z], dtype=np.float32), shoulder_width

    points = []
    for landmark_list in (result.left_hand_landmarks, result.right_hand_landmarks):
        if landmark_list is not None:
            points.extend([[float(p.x), float(p.y), float(p.z)] for p in landmark_list.landmark])

    if not points:
        return np.zeros(3, dtype=np.float32), 1.0

    points = np.asarray(points, dtype=np.float32)
    origin = np.mean(points, axis=0)
    scale = float(np.max(np.linalg.norm(points[:, :2] - origin[:2], axis=1)))
    if scale < 1e-6:
        scale = 1.0
    return origin, scale


def _normalized_landmark(point, origin, scale, visibility=1.0):
    return [
        float((point.x - origin[0]) / scale),
        float((point.y - origin[1]) / scale),
        float((point.z - origin[2]) / scale),
        float(visibility),
    ]


def _pose_features(result, origin, scale):
    if result.pose_landmarks is None:
        return [0.0] * (len(POSE_LANDMARK_INDICES) * VALUES_PER_LANDMARK)

    landmarks = result.pose_landmarks.landmark
    features = []
    for index in POSE_LANDMARK_INDICES:
        point = landmarks[index]
        features.extend(_normalized_landmark(point, origin, scale, getattr(point, "visibility", 1.0)))
    return features


def _hand_features(landmark_list, origin, scale):
    if landmark_list is None:
        return [0.0] * (HAND_LANDMARK_COUNT * VALUES_PER_LANDMARK)

    features = []
    for point in landmark_list.landmark:
        features.extend(_normalized_landmark(point, origin, scale, 1.0))
    return features


def holistic_result_to_feature_vector(result):
    origin, scale = _origin_and_scale(result)
    features = []
    features.extend(_pose_features(result, origin, scale))
    features.extend(_hand_features(result.left_hand_landmarks, origin, scale))
    features.extend(_hand_features(result.right_hand_landmarks, origin, scale))
    return np.asarray(features, dtype=np.float32)


def resample_sequence(sequence, target_length):
    sequence = np.asarray(sequence, dtype=np.float32)
    if sequence.ndim != 2:
        raise ValueError(f"Expected sequence shape (frames, features), got {sequence.shape}")
    if sequence.shape[1] != FRAME_FEATURE_LENGTH:
        raise ValueError(f"Expected {FRAME_FEATURE_LENGTH} frame features, got {sequence.shape[1]}")
    if len(sequence) == target_length:
        return sequence
    if len(sequence) == 0:
        return np.zeros((target_length, FRAME_FEATURE_LENGTH), dtype=np.float32)
    if len(sequence) == 1:
        return np.repeat(sequence, target_length, axis=0)

    old_positions = np.linspace(0.0, 1.0, len(sequence), dtype=np.float32)
    new_positions = np.linspace(0.0, 1.0, target_length, dtype=np.float32)
    resampled = np.empty((target_length, sequence.shape[1]), dtype=np.float32)
    for feature_index in range(sequence.shape[1]):
        resampled[:, feature_index] = np.interp(new_positions, old_positions, sequence[:, feature_index])
    return resampled


def sequence_to_model_input(sequence, target_length):
    return resample_sequence(sequence, target_length).reshape(1, -1)
