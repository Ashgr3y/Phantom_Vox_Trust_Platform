from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.bootstrap import initialize_database


if __name__ == "__main__":
    initialize_database()
    print("Phantom Vox database initialized with fictional demonstration records.")
