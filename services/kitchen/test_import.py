import sys
import os
sys.path.append(os.getcwd())
print(f"Path: {sys.path}")
try:
    import src.db.engine
    print("Success")
except ImportError as e:
    print(f"Failed: {e}")
