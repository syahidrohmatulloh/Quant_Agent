
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MODE = os.getenv("QUANT_MODE", "paper")
    BROKER = os.getenv("QUANT_BROKER", "paper")
    SQLITE_PATH = os.getenv("QUANT_SQLITE_PATH", "./data/quant_platform.db")
    AUDIT_PATH = os.getenv("AUDIT_JSONL_PATH", "./data/audit.jsonl")

    PAPER_INITIAL_BALANCE = float(os.getenv("PAPER_INITIAL_BALANCE", "100000.0"))
    PAPER_COMMISSION_PER_LOT = float(os.getenv("PAPER_COMMISSION_PER_LOT", "7.0"))
    PAPER_SLIPPAGE_PIPS = float(os.getenv("PAPER_SLIPPAGE_PIPS", "0.5"))
    PAPER_LEVERAGE = float(os.getenv("PAPER_LEVERAGE", "100.0"))
