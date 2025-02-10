from fastapi import FastAPI, HTTPException
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "DataWorks Automation API"}

@app.post("/run")
def run_task(task: str):
    return {"status": "Task received", "task": task}

@app.get("/read")
def read_file(path: str):
    file_path = f"/data/{path}"  # Ensure it only reads from /data
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(file_path, "r") as f:
        return f.read()
