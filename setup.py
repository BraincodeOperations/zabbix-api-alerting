import subprocess
import sys

subprocess.run([sys.executable, "-m", "venv", "venv"])
subprocess.run(["venv\\Scripts\\python.exe", "-m", "pip", "install", "-r", "requirements.txt"])