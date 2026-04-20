import os
from typing import Optional
from pathlib import Path

from config import settings


class PreviewManager:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or settings.output_dir)
    
    def get_model_viewer_html(self, model_path: str, width: int = 800, height: int = 600) -> str:
        if model_path.startswith("/"):
            model_path = model_path[1:]
        abs_path = self.output_dir / model_path
        if abs_path.exists():
            return self._generate_html(str(abs_path), width, height)
        return self._generate_placeholder_html(width, height)
    
    def _generate_html(self, model_path: str, width: int, height: int) -> str:
        return f"""
        <div style="width: {width}px; height: {height}px; border: 1px solid #ccc; position: relative;">
            <model-viewer 
                src="{model_path}"
                alt="3D Model"
                auto-camera-controls
                camera-controls
                touch-action="pan-y"
                style="width: 100%; height: 100%;"
                shadow-intensity="1"
                environment-image="neutral"
            ></model-viewer>
        </div>
        <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.0.1/model-viewer.min.js"></script>
        """
    
    def _generate_placeholder_html(self, width: int, height: int) -> str:
        return f"""
        <div style="width: {width}px; height: {height}px; border: 1px solid #ccc; 
                    display: flex; align-items: center; justify-content: center; 
                    background-color: #f5f5f5;">
            <p style="color: #666;">No model available</p>
        </div>
        """
    
    def get_streamlit_3d_viewer_config(self, model_path: str) -> dict:
        return {
            "path": model_path,
            "show_controls": True,
            "auto_rotate": False,
            "light_position": [1, 1, 1],
            "camera_position": [0, 0, 3],
        }
    
    def is_valid_model(self, model_path: str) -> bool:
        path = Path(model_path)
        if not path.exists():
            return False
        valid_extensions = [".glb", ".gltf", ".obj", ".fbx", ".stl"]
        return path.suffix.lower() in valid_extensions
    
    def get_model_info(self, model_path: str) -> dict:
        path = Path(model_path)
        if not path.exists():
            return {"exists": False}
        
        stat = path.stat()
        return {
            "exists": True,
            "size_mb": stat.st_size / (1024 * 1024),
            "format": path.suffix.lower(),
            "created_time": stat.st_ctime,
            "modified_time": stat.st_mtime,
        }