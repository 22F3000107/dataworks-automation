from fastapi import FastAPI, HTTPException, Query
import json
from pathlib import Path
from typing import List, Dict
import logging
from app.task_executor import execute_step
from app.llm_handler import call_llm
from app.utils import is_safe_path, validate_step
from app.celery_worker import process_task

app = FastAPI()

DATA_DIR = "/data"
ALLOWED_ACTIONS = {
    'run_script', 'format_file', 'count_weekdays', 'sort_json',
    'extract_email', 'extract_credit_card', 'similar_comments',
    'query_sql', 'fetch_api', 'clone_repo', 'scrape_website',
    'compress_image', 'transcribe_audio', 'markdown_to_html', 'filter_csv'
}

logging.basicConfig(level=logging.INFO)

def parse_task(task: str) -> List[Dict]:
    """Use LLM to parse task into structured steps."""
    prompt = f"""
    Parse the task into JSON steps. Use actions: {ALLOWED_ACTIONS}. Paths must be in /data.
    No deletions. Example:
    {{"action":"count_weekdays", "input_path":"/data/dates.txt", "output_path":"/data/output.txt", "weekday":"Wednesday"}}
    Task: {task}
    """
    try:
        llm_response = call_llm(prompt)
        steps = json.loads(llm_response)
        if not isinstance(steps, list):
            steps = [steps]
        return steps
    except Exception as e:
        logging.error(f"LLM parsing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="LLM parsing failed")

@app.get("/")
def read_root():
    return {"message": "DataWorks Automation API is running"}

@app.post("/run")
async def run_task(task: str = Query(..., alias="task")):
    """API Endpoint to parse and execute automation tasks using Celery."""
    try:
        steps = parse_task(task)
    except HTTPException as e:
        return {"status": "error", "detail": e.detail}
    
    for step in steps:
        if not validate_step(step):
            return {"status": "error", "detail": "Invalid step"}
        process_task.delay(step)  # Celery async task execution

    return {"status": "success", "message": "Task execution started in Celery"}

@app.get("/read")
async def read_file(path: str = Query(...)):
    """API Endpoint to read file contents safely."""
    if not is_safe_path(path):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return {"status": "success", "content": file_path.read_text()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
