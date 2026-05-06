import os, sys

current_dir = os.path.abspath(os.path.dirname(__file__))
while current_dir != os.path.dirname(current_dir):
    if "vault" in os.listdir(current_dir):
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        break
    current_dir = os.path.dirname(current_dir)

from src.app import create_app

app = create_app()
