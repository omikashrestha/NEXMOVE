from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "sample_benchmarks"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/nexmove.db")
DEFAULT_CURRENCY = "INR"
DEFAULT_CURRENCY_SYMBOL = "₹"
