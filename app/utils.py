from pathlib import Path
from typing import Dict

DATA_DIR = "data"
ALLOWED_ACTIONS = {'read', 'write', 'delete'}  # Define allowed actions

def is_safe_path(path: str) -> bool:
    """Ensure file operations remain within /data."""
    resolved_path = Path(path).resolve()
    data_path = Path(DATA_DIR).resolve()
    return resolved_path.is_relative_to(data_path)

def validate_step(step: Dict) -> bool:
    """Validate step structure."""
    required_keys = {"action", "input_path", "output_path"}
    if not all(key in step for key in required_keys):
        return False  # ❌ Missing required keys

    if step["action"] not in ALLOWED_ACTIONS:
        return False  # ❌ Invalid action

    if not step["input_path"].startswith(DATA_DIR) or not step["output_path"].startswith(DATA_DIR):
        return False  # ❌ Path outside allowed directory

    return True  # ✅ Step is valid
