import os
import subprocess

def run_automation():
    # Run automation script in the background
    subprocess.Popen(['python', 'automation.py'])

if __name__ == "__main__":
    run_automation()