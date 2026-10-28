#!/usr/bin/env python3
"""
Convenience launcher to run DB/import_tasks_batch.py from root or Misc directory.
"""
import sys
from pathlib import Path

# Add DB directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
db_dir = root_dir / "DB"
sys.path.insert(0, str(db_dir))

from import_tasks_batch import main

if __name__ == "__main__":
    main()

