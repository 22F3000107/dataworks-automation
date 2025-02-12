from pathlib import Path
from typing import Dict

DATA_DIR = Path("data").resolve()

ALLOWED_ACTIONS = {
    'run_script', 'format_file', 'count_weekdays', 'sort_json',
    'extract_email', 'extract_credit_card', 'similar_comments',
    'query_sql', 'fetch_api', 'clone_repo', 'scrape_website',
    'compress_image', 'transcribe_audio', 'markdown_to_html', 'filter_csv'
}
def is_safe_path(path: str) -> bool:
    """Ensure file operations remain within DATA_DIR"""
    try:
        requested_path = (DATA_DIR / path).resolve()
        return requested_path.is_relative_to(DATA_DIR)
    except Exception:
        return False

def validate_step(step: dict) -> bool:
    """Validate step structure with dynamic requirements"""
    if 'action' not in step or step['action'] not in ALLOWED_ACTIONS:
        return False
    
    # Check input/output paths based on action requirements
    if 'input_path' in step:
        input_path = str(step['input_path'])
        if not input_path.startswith(str(DATA_DIR)):
            return False
    
    if 'output_path' in step:
        output_path = str(step['output_path'])
        if not output_path.startswith(str(DATA_DIR)):
            return False
    
    return True
def sanitize_filename(path: str) -> Path:
    """Ensure filename stays within DATA_DIR"""
    safe_path = Path(path).name
    return DATA_DIR / safe_path