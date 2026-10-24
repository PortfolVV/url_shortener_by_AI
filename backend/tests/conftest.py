import sys
from pathlib import Path

# Allow `pytest` to import the `src` package when run from ./backend.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
