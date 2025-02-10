import subprocess
import os

def install_uv_and_run_datagen(user_email: str):
    subprocess.run(["pip", "install", "--user", "uv"], check=True)
    subprocess.run(["python", "datagen.py", user_email], check=True)

def format_markdown():
    subprocess.run(["npx", "prettier@3.4.2", "--write", "/data/format.md"], check=True)
