from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from semedia_shared.video_service import SceneSpan, _get_adaptive_threshold, detect_scenes, extract_scene_keyframes

from .conftest import make_test_settings


class TestAdaptiveThreshold:
    """Test adaptive threshold calculation based on video duration."""

    def test_short_video_uses_lower_threshold(self):
        """Videos under 30s should use threshold 20.0"""
        result = _get_adaptive_threshold(duration=25.0, base_threshold=27.0)
        assert result == 20.0

    def test_long_video_uses_higher_threshold(self):
        """Videos over 10 minutes should use threshold 35.0"""
        result = _get_adaptive_threshold(duration=650.0, base_threshold=27.0)
        assert result == 35.0

    def test_normal_video_uses_base_threshold(self):
        """Videos between 30s and 10min should use base threshold"""
        result = _get_adaptive_threshold(duration=120.0, base_threshold=27.0)
        assert result == 27.0

    def test_boundary_at_30_seconds(self):
        """Exactly 30s should use base threshold"""
        result = _get_adaptive_threshold(duration=30.0, base_threshold=27.0)
        assert result == 27.0

    def test_boundary_at_600_seconds(self):
        """Exactly 600s (10min) should use base threshold"""
        result = _get_adaptive_threshold(duration=600.0, base_threshold=27.0)
        assert result == 27.0


class TestDetectScenesWithAdaptiveThreshold:
    """Test that detect_scenes uses adaptive threshold based on duration."""

    def test_short_video_uses_threshold_20(self, tmp_path, monkeypatch):
        """Short video (<30s) should use threshold 20.0"""
        settings = make_test_settings("test", tmp_path)

        # Mock scenedetect module
        mock_scenedetect = types.ModuleType('scenedetect')
        mock_detectors = types.ModuleType('scenedetect.detectors')

        mock_video = MagicMock()
        mock_scenedetect.open_video = MagicMock(return_value=mock_video)

        mock_manager = MagicMock()
        mock_manager.get_scene_list.return_value = []
        mock_scenedetect.SceneManager = MagicMock(return_value=mock_manager)

        mock_detector_instance = MagicMock()
        mock_detectors.ContentDetector = MagicMock(return_value=mock_detector_instance)

        sys.modules['scenedetect'] = mock_scenedetect
        sys.modules['scenedetect.detectors'] = mock_detectors

        import semedia_shared.video_service as video_service
        monkeypatch.setattr(video_service, 'get_video_duration', lambda path: 25.0)

        detect_scenes(settings, "/fake/video.mp4")

        mock_detectors.ContentDetector.assert_called_once_with(threshold=20.0)

    def test_long_video_uses_threshold_35(self, tmp_path, monkeypatch):
        """Long video (>10min) should use threshold 35.0"""
        settings = make_test_settings("test", tmp_path)

        # Mock scenedetect module
        mock_scenedetect = types.ModuleType('scenedetect')
        mock_detectors = types.ModuleType('scenedetect.detectors')

        mock_video = MagicMock()
        mock_scenedetect.open_video = MagicMock(return_value=mock_video)

        mock_manager = MagicMock()
        mock_manager.get_scene_list.return_value = []
        mock_scenedetect.SceneManager = MagicMock(return_value=mock_manager)

        mock_detector_instance = MagicMock()
        mock_detectors.ContentDetector = MagicMock(return_value=mock_detector_instance)

        sys.modules['scenedetect'] = mock_scenedetect
        sys.modules['scenedetect.detectors'] = mock_detectors

        import semedia_shared.video_service as video_service
        monkeypatch.setattr(video_service, 'get_video_duration', lambda path: 650.0)

        detect_scenes(settings, "/fake/video.mp4")

        mock_detectors.ContentDetector.assert_called_once_with(threshold=35.0)

    def test_normal_video_uses_base_threshold(self, tmp_path, monkeypatch):
        """Normal video (30s-10min) should use configured base threshold"""
        settings = make_test_settings("test", tmp_path)

        # Mock scenedetect module
        mock_scenedetect = types.ModuleType('scenedetect')
        mock_detectors = types.ModuleType('scenedetect.detectors')

        mock_video = MagicMock()
        mock_scenedetect.open_video = MagicMock(return_value=mock_video)

        mock_manager = MagicMock()
        mock_manager.get_scene_list.return_value = []
        mock_scenedetect.SceneManager = MagicMock(return_value=mock_manager)

        mock_detector_instance = MagicMock()
        mock_detectors.ContentDetector = MagicMock(return_value=mock_detector_instance)

        sys.modules['scenedetect'] = mock_scenedetect
        sys.modules['scenedetect.detectors'] = mock_detectors

        import semedia_shared.video_service as video_service
        monkeypatch.setattr(video_service, 'get_video_duration', lambda path: 120.0)

        detect_scenes(settings, "/fake/video.mp4")

        mock_detectors.ContentDetector.assert_called_once_with(threshold=27.0)


class TestExtractSceneKeyframes:
    """Test multi-frame extraction from video scenes."""

    def _install_fake_cv2(self, monkeypatch, capture):
        fake_cv2 = types.SimpleNamespace(
            CAP_PROP_FPS=5,
            CAP_PROP_POS_FRAMES=1,
            VideoCapture=lambda path: capture,
            imwrite=MagicMock(return_value=True),
        )
        monkeypatch.setitem(sys.modules, 'cv2', fake_cv2)
        return fake_cv2

    def test_extracts_three_frames_per_scene(self, tmp_path, monkeypatch):
        """Should extract exactly 3 frames at 10%, 50%, 90% of scene duration"""
        settings = make_test_settings("test", tmp_path)
        scene = SceneSpan(scene_index=0, start_time=0.0, end_time=10.0)

        mock_capture = MagicMock()
        mock_capture.get.return_value = 30.0
        mock_capture.read.side_effect = [(True, object()), (True, object()), (True, object())]
        self._install_fake_cv2(monkeypatch, mock_capture)

        keyframe_paths, thumbnail_paths = extract_scene_keyframes(
            settings, "/fake/video.mp4", media_id=1, scene=scene
        )

        assert len(keyframe_paths) == 3
        assert len(thumbnail_paths) == 3
        actual_calls = [args[1] for args, _kwargs in mock_capture.set.call_args_list]
        assert actual_calls == [30, 150, 270]

    def test_deterministic_filenames(self, tmp_path, monkeypatch):
        """Filenames should be deterministic and sortable"""
        settings = make_test_settings("test", tmp_path)
        scene = SceneSpan(scene_index=5, start_time=10.0, end_time=20.0)

        mock_capture = MagicMock()
        mock_capture.get.return_value = 30.0
        mock_capture.read.side_effect = [(True, object()), (True, object()), (True, object())]
        self._install_fake_cv2(monkeypatch, mock_capture)

        keyframe_paths, thumbnail_paths = extract_scene_keyframes(
            settings, "/fake/video.mp4", media_id=1, scene=scene
        )

        assert keyframe_paths[0].endswith("scene_0005_frame_00.jpg")
        assert keyframe_paths[1].endswith("scene_0005_frame_01.jpg")
        assert keyframe_paths[2].endswith("scene_0005_frame_02.jpg")
        assert thumbnail_paths[0].endswith("scene_0005_frame_00.jpg")
        assert thumbnail_paths[1].endswith("scene_0005_frame_01.jpg")
        assert thumbnail_paths[2].endswith("scene_0005_frame_02.jpg")

    def test_midpoint_frame_is_index_01(self, tmp_path, monkeypatch):
        """The midpoint frame (50%) should be at index 01"""
        settings = make_test_settings("test", tmp_path)
        scene = SceneSpan(scene_index=0, start_time=0.0, end_time=10.0)

        mock_capture = MagicMock()
        mock_capture.get.return_value = 30.0
        mock_capture.read.side_effect = [(True, object()), (True, object()), (True, object())]
        self._install_fake_cv2(monkeypatch, mock_capture)

        keyframe_paths, thumbnail_paths = extract_scene_keyframes(
            settings, "/fake/video.mp4", media_id=1, scene=scene
        )

        assert keyframe_paths[1].endswith("frame_01.jpg")
        assert thumbnail_paths[1].endswith("frame_01.jpg")

    def test_creates_keyframe_and_thumbnail_directories(self, tmp_path, monkeypatch):
        """Should create keyframes/{media_id} and thumbnails/{media_id} directories"""
        settings = make_test_settings("test", tmp_path)
        scene = SceneSpan(scene_index=0, start_time=0.0, end_time=10.0)

        mock_capture = MagicMock()
        mock_capture.get.return_value = 30.0
        mock_capture.read.side_effect = [(True, object()), (True, object()), (True, object())]
        self._install_fake_cv2(monkeypatch, mock_capture)

        extract_scene_keyframes(settings, "/fake/video.mp4", media_id=42, scene=scene)

        assert (tmp_path / "media" / "keyframes" / "42").exists()
        assert (tmp_path / "media" / "thumbnails" / "42").exists()

    def test_raises_error_when_frame_extraction_fails(self, tmp_path, monkeypatch):
        """Should raise ValueError if any frame cannot be extracted"""
        settings = make_test_settings("test", tmp_path)
        scene = SceneSpan(scene_index=0, start_time=0.0, end_time=10.0)

        mock_capture = MagicMock()
        mock_capture.get.return_value = 30.0
        mock_capture.read.side_effect = [(False, None)]
        self._install_fake_cv2(monkeypatch, mock_capture)

        with pytest.raises(ValueError, match="Could not extract keyframe"):
            extract_scene_keyframes(settings, "/fake/video.mp4", media_id=1, scene=scene)

        mock_capture.release.assert_called_once()
