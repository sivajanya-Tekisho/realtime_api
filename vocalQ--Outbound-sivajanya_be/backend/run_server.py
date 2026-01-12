import uvicorn
import traceback
import sys

import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly find .env
env_path = Path(__file__).parent / ".env"
print(f"--- SERVER STARTUP ---")
print(f"Looking for .env at: {env_path}")
print(f"File exists: {env_path.exists()}")

load_dotenv(dotenv_path=env_path, override=True)

if __name__ == "__main__":
    try:
        print("Starting server...")
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="debug", reload=True)
    except BaseException as e:
        print(f"EXCEPTION CAUGHT ({type(e).__name__}): {e}")
        traceback.print_exc()
        sys.exit(1)
