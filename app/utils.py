from pathlib import Path

DATA_DIR = "/data"
ALLOWED_ACTIONS = {'read', 'write', 'delete'}  # Define allowed actions

def is_safe_path(path: str) -> bool:
    """Ensure file operations remain within /data."""
    resolved_path = Path(path).resolve()
    data_path = Path(DATA_DIR).resolve()
    return resolved_path.is_relative_to(data_path)

def validate_step(step: dict) -> bool:
    """Validate execution steps."""
    action = step.get('action')
    allowed_keys = {'input_path', 'output_path', 'file_path', 'db_path', 'script_url', 'repo_url'}
    if action not in ALLOWED_ACTIONS:
        return False
    return all(key not in step or is_safe_path(step[key]) for key in allowed_keys)
