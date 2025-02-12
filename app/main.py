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


logging.info("Environment variables loaded successfully")


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

# main.py
def parse_task(task: str) -> List[Dict]:
    """Enhanced prompt with examples"""
    prompt = f"""Convert this task into JSON steps using only these actions: {ALLOWED_ACTIONS}.
All files must be within {DATA_DIR}. Never delete files. Example responses:

Example 1: {{"action":"count_weekdays", "input_path":"data/dates.txt", "output_path":"data/result.txt", "day":"Wednesday"}}
Example 2: [{{"action":"format_file", "input_path":"data/file.md"}}, {{"action":"run_script", "script":"prettier@3.4.2"}}]

Task: {task}
JSON:"""
    
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


@app.post("/run")
async def run_task(request: TaskRequest):
    try:
        steps = parse_task(request.task)
        for step in steps:
            if 'input_path' in step and not Path(step['input_path']).exists():
                raise HTTPException(400, f"Input file not found: {step['input_path']}")
            
            if not validate_step(step):
                raise HTTPException(400, f"Invalid step: {step}")
            
            process_task.delay(step)
            
        return {"status": "success"}
    
    except HTTPException as e:
        raise
    except Exception as e:
        logging.error(f"Task failed: {str(e)}")
        raise HTTPException(500, "Internal server error")

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
