import sys
from pathlib import Path
import asyncio

import dotenv

ROOT_DIR = Path(__file__).resolve().parent
if ROOT_DIR not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

dotenv.load_dotenv()
from helpers.notifier import *

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(app_queue.run_worker())
