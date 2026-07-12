import numpy as np


FEATURE_VERSION = "wrist_scale_shape_angles_v2"
EXPECTED_LANDMARKS = 21

FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_MCPS = [2, 5, 9, 13, 17]
FINGER_CHAINS = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12],
    [13, 14, 15, 16],
    [17, 18, 19, 20],
]


def _point_xyz(point):
    return [float(point.x), float(point.y), float(point.z)]


def _joint_angle(a, b, c):
    ba = a - b
    bc = c - b
    denom = float(np.linalg.norm(ba) * np.linalg.norm(bc))
    if denom < 1e-6:
        return 0.0
    cosine = float(np.dot(ba, bc) / denom)
    return float(np.clip(cosine, -1.0, 1.0))


def landmarks_to_feature_vector(landmarks):
    points = np.asarray([_point_xyz(point) for point in landmarks], dtype=np.float32)
    if points.shape != (EXPECTED_LANDMARKS, 3):
        raise ValueError(f"Expected 21 hand landmarks, got shape {points.shape}")

    centered = points - points[0]
    scale = float(np.max(np.linalg.norm(centered[1:], axis=1)))
    if scale < 1e-6:
        scale = 1.0

    normalized = centered / scale
    features = normalized.reshape(-1).tolist()

    for i, tip_a in enumerate(FINGER_TIPS):
        for tip_b in FINGER_TIPS[i + 1:]:
            features.append(float(np.linalg.norm(normalized[tip_a] - normalized[tip_b])))

    for tip, mcp in zip(FINGER_TIPS, FINGER_MCPS):
        features.append(float(np.linalg.norm(normalized[tip] - normalized[mcp])))

    for chain in FINGER_CHAINS:
        for i in range(1, len(chain) - 1):
            features.append(_joint_angle(normalized[chain[i - 1]], normalized[chain[i]], normalized[chain[i + 1]]))

    palm_a = normalized[5] - normalized[0]
    palm_b = normalized[17] - normalized[0]
    palm_normal = np.cross(palm_a, palm_b)
    normal_scale = float(np.linalg.norm(palm_normal))
    if normal_scale >= 1e-6:
        palm_normal = palm_normal / normal_scale
    features.extend(palm_normal.tolist())

    return features


def feature_length():
    angle_count = sum(len(chain) - 2 for chain in FINGER_CHAINS)
    return EXPECTED_LANDMARKS * 3 + 10 + 5 + angle_count + 3
