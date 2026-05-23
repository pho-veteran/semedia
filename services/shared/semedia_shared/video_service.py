from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SceneSpan:
    scene_index: int
    start_time: float
    end_time: float


def get_video_duration(video_path: str) -> float:
    import cv2

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        return 0.0
    fps = capture.get(cv2.CAP_PROP_FPS) or 0
    frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    capture.release()
    if fps <= 0:
        return 0.0
    return round(float(frame_count / fps), 2)


def detect_scenes(settings, video_path: str) -> list[SceneSpan]:
    from scenedetect import SceneManager, open_video
    from scenedetect.detectors import ContentDetector

    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=settings.scene_detection_threshold))
    scene_manager.detect_scenes(video)
    scenes = scene_manager.get_scene_list()

    if not scenes:
        duration = get_video_duration(video_path)
        if duration <= 0:
            return []
        return [SceneSpan(scene_index=0, start_time=0.0, end_time=duration)]

    return [
        SceneSpan(
            scene_index=index,
            start_time=round(start.get_seconds(), 3),
            end_time=round(end.get_seconds(), 3),
        )
        for index, (start, end) in enumerate(scenes)
    ]


def extract_scene_keyframe(settings, video_path: str, media_id: int, scene: SceneSpan) -> tuple[str, str]:
    import cv2

    capture = cv2.VideoCapture(video_path)
    fps = capture.get(cv2.CAP_PROP_FPS) or 0
    midpoint = (scene.start_time + scene.end_time) / 2 if scene.end_time > scene.start_time else scene.start_time
    frame_number = int(math.floor(midpoint * fps)) if fps > 0 else 0
    capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise ValueError(f"Could not extract keyframe for scene {scene.scene_index} from {video_path}")

    keyframe_dir = settings.media_root / "keyframes" / str(media_id)
    thumbnail_dir = settings.media_root / "thumbnails" / str(media_id)
    keyframe_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_dir.mkdir(parents=True, exist_ok=True)

    keyframe_path = keyframe_dir / f"scene_{scene.scene_index:04d}.jpg"
    thumbnail_path = thumbnail_dir / f"scene_{scene.scene_index:04d}.jpg"
    cv2.imwrite(str(keyframe_path), frame)
    cv2.imwrite(str(thumbnail_path), frame)
    return str(keyframe_path), str(thumbnail_path)
