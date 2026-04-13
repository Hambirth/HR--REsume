"""Script to run the Streamlit web interface."""

import subprocess
import sys

if __name__ == "__main__":
    subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.port=8501"])
