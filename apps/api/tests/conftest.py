# Ensure "apps/api" package can be imported as "aurora"
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
API_ROOT = THIS_DIR.parent  # apps/api
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
