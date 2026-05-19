import json
import re
from pathlib import Path


def to_wsl_path(path_str: str) -> str:
    """Converts a Windows style path (e.g. D:\\SaaS\\...) to a WSL mount path (/mnt/d/SaaS/...)."""
    path_str = str(path_str)
    
    # Check if path contains Windows backslashes or a drive letter (e.g., C:\ or D:\\)
    if '\\' in path_str or re.match(r'^[A-Za-z]:', path_str):
        # Normalize all backslashes to forward slashes
        path_str = path_str.replace('\\', '/')
        
        # Replace drive letters (D:/path -> /mnt/d/path)
        path_str = re.sub(
            r'^([A-Za-z]):', 
            lambda m: f"/mnt/{m.group(1).lower()}", 
            path_str
        )
        
    return path_str


def load_json(path: str):
    wsl_compliant_path = to_wsl_path(path)
    return json.loads(
        Path(wsl_compliant_path).read_text(encoding="utf-8")
    )


def save_json(path: str, data):
    wsl_compliant_path = to_wsl_path(path)
    path_obj = Path(wsl_compliant_path)
    
    path_obj.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    path_obj.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )