import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

if __name__ == "__main__":
    uvicorn.run(
        "src.a2a_adk.server.app:app",
        host="0.0.0.0",
        port=8100,
        reload=True
    )
