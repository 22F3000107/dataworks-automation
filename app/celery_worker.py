from celery import Celery
from app.task_executor import execute_step

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def process_task(step: dict):
    """Background execution of tasks."""
    try:
        execute_step(step)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    return {"status": "success"}
