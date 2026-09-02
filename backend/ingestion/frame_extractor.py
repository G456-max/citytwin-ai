import os
import cv2
import json
from pathlib import Path
from typing import List, Dict, Any

class DroneVideoExtractor:
    """Handles drone video keyframe extraction with Laplacian variance blur filtering."""

    @staticmethod
    def extract_keyframes(
        video_path: str, 
        output_dir: str, 
        frame_interval: int = 15, 
        blur_threshold: float = 100.0
    ) -> List[str]:
        """
        Iterates through frames of a drone video, computes Laplacian variance,
        discards blurry frames, and saves the sharp ones.

        Args:
            video_path: Path to raw drone video (.mp4, .mov, etc.)
            output_dir: Directory to save extracted sharp frames
            frame_interval: Number of frames to skip between checks
            blur_threshold: Laplacian variance threshold (below this is blurry)

        Returns:
            List of absolute paths to saved keyframe images.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Failed to open video file: {video_path}")
            
        saved_paths = []
        metadata_log = []
        frame_idx = 0
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Sample frames based on interval
            if frame_idx % frame_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Compute Laplacian variance for blur checking
                laplacian_score = cv2.Laplacian(gray, cv2.CV_64F).var()
                timestamp_sec = frame_idx / fps
                
                is_sharp = laplacian_score >= blur_threshold
                
                if is_sharp:
                    filename = f"frame_{frame_idx:06d}.jpg"
                    file_path = output_path / filename
                    # Save frame
                    cv2.imwrite(str(file_path), frame)
                    saved_paths.append(str(file_path.resolve()))
                    
                    metadata_log.append({
                        "frame_index": frame_idx,
                        "timestamp_sec": round(timestamp_sec, 2),
                        "laplacian_score": round(laplacian_score, 2),
                        "saved_as": filename,
                        "status": "extracted"
                    })
                else:
                    metadata_log.append({
                        "frame_index": frame_idx,
                        "timestamp_sec": round(timestamp_sec, 2),
                        "laplacian_score": round(laplacian_score, 2),
                        "status": "discarded_blurry"
                    })
                    
            frame_idx += 1
            
        cap.release()
        
        # Save metadata log
        log_file = output_path / "extraction_metadata.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(metadata_log, f, indent=4)
            
        return saved_paths
