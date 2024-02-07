from typing import List
import subprocess

def run(command: List[str]):
    "Runs a command as a subprocess. Raises error if encounters an error code"
    subprocess.run(command, check=True)