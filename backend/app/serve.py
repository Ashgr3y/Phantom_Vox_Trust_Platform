"""Single-process entrypoint for the in-process demo and WebSocket hub."""
import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), workers=1)
