"""
Input Validators Placeholder
"""
import re

def validate_project_path(path: str) -> bool:
    if not path or not path.strip():
        return False
    return "/" in path or "\\" in path
