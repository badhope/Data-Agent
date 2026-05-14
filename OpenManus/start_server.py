#!/usr/bin/env python3
"""
DATA-AI Server Startup Script
"""
import sys
from pathlib import Path

if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent
    sys.path.insert(0, str(BASE_DIR))

    print("🚀 Starting DATA-AI Server...")
    print(f"📦 Version: 2.0.0")
    print(f"📍 Working Dir: {BASE_DIR}")
    print("="*60)

    try:
        import uvicorn
        uvicorn.run(
            "web.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
