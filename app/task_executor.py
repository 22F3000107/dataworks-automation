import os
import subprocess
import json
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from app.llm_handler import call_llm

DATA_DIR = "/data"

def execute_step(step: dict):
    """Executes an automation step based on action type."""
    action = step['action']
    try:
        if action == 'run_script':
            script_url = step['script_url']
            args = [os.path.expandvars(arg) for arg in step.get('args', [])]
            script_path = Path(DATA_DIR) / "script.py"
            response = requests.get(script_url)
            script_path.write_bytes(response.content)
            subprocess.run(['python', str(script_path)] + args, check=True)
            script_path.unlink()

        elif action == 'count_weekdays':
            input_path = step['input_path']
            output_path = step['output_path']
            weekday = step['weekday']
            with open(input_path) as f:
                dates = [line.strip() for line in f if line.strip()]
            count = sum(1 for date_str in dates if datetime.strptime(date_str, '%Y-%m-%d').strftime('%A') == weekday)
            Path(output_path).write_text(str(count))

        elif action == 'sort_json':
            input_path = step['input_path']
            output_path = step['output_path']
            with open(input_path) as f:
                data = json.load(f)
            data.sort(key=lambda x: (x['last_name'], x['first_name']))
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)

        elif action == 'query_sql':
            db_path = step['db_path']
            query = step['query']
            output_path = step['output_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            Path(output_path).write_text(json.dumps(result))

        else:
            raise ValueError(f"Unsupported action: {action}")

    except Exception as e:
        raise RuntimeError(f"Error executing {action}: {e}")
