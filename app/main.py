from fastapi import FastAPI, HTTPException
import json
from pathlib import Path
from typing import List, Dict
import logging
from app.task_executor import execute_step
from app.llm_handler import call_llm
from app.utils import is_safe_path, validate_step
from app.celery_worker import process_task
from dotenv import load_dotenv
import os 
from pydantic import BaseModel

app = FastAPI()

# Load environment variables from .env file
load_dotenv()

# Access variables
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

# Check if the environment variables are loaded correctly
if not AIPROXY_TOKEN:
    raise ValueError("Missing AIPROXY_TOKEN in .env file")

if not REDIS_URL:
    raise ValueError("Missing REDIS_URL in .env file")


print("AIPROXY_TOKEN:", os.getenv("AIPROXY_TOKEN"))
print("REDIS_URL:", os.getenv("REDIS_URL"))


DATA_DIR = "data"
ALLOWED_ACTIONS = {
    'run_script', 'format_file', 'count_weekdays', 'sort_json',
    'extract_email', 'extract_credit_card', 'similar_comments',
    'query_sql', 'fetch_api', 'clone_repo', 'scrape_website',
    'compress_image', 'transcribe_audio', 'markdown_to_html', 'filter_csv'
}

logging.basicConfig(level=logging.INFO)

class TaskRequest(BaseModel):
    task: str

def parse_task(task: str) -> List[Dict]:
    """Use LLM to parse task into structured steps."""
    prompt = f"""
    Parse the task into JSON steps. Use actions: {ALLOWED_ACTIONS}. Paths must be in {DATA_DIR}.
    No deletions. Example:
    {{"action":"extract_email", "input_path":"{DATA_DIR}/sample.txt", "output_path":"{DATA_DIR}/emails.txt"}}
    Task: {task}
    """
    try:
        llm_response = call_llm(prompt)
        print("DEBUG: LLM Response ->", llm_response)  # 🔍 Print raw LLM response

        steps = json.loads(llm_response)
        if not isinstance(steps, list):
            steps = [steps]

        # ✅ Ensure paths are inside the allowed directory
        for step in steps:
            if "input_path" in step:
                step["input_path"] = step["input_path"].replace("/data", DATA_DIR)
            if "output_path" in step:
                step["output_path"] = step["output_path"].replace("/data", DATA_DIR)

        print("DEBUG: Parsed Steps ->", steps)  # 🔍 Print formatted steps
        return steps
    except Exception as e:
        logging.error(f"LLM parsing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="LLM parsing failed")

@app.get("/")
def read_root():
    return {"message": "DataWorks Automation API is running"}

from pathlib import Path

@app.post("/run")
async def run_task(request: TaskRequest):
    """API Endpoint to parse and execute automation tasks using Celery."""
    try:
        steps = parse_task(request.task)
    except HTTPException as e:
        return {"status": "error", "detail": e.detail}
    
    # ✅ Check if input files exist before processing  
    for step in steps:
        input_path = step.get("input_path")
        if input_path and not Path(input_path).exists():
            return {"status": "error", "detail": f"File not found: {input_path}"}

        if not validate_step(step):
            return {"status": "error", "detail": "Invalid step"}
        
        process_task.delay(step)  # Celery async task execution

    return {"status": "success", "message": "Task execution started in Celery"}

@app.get("/read")
async def read_file(path: str):
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
