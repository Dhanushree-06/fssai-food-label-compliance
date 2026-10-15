"""
Application Entrypoint
AI-Based Food Label Compliance Verification Platform
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("DEBUG", "True").lower() in ["true", "1", "yes"]
    print(f"\n=======================================================")
    print(f" Starting AI-Based Food Label Compliance Verification Platform")
    print(f" URL: http://127.0.0.1:{port}")
    print(f" Debug mode: {debug_mode}")
    print(f"=======================================================\n")
    app.run(host="127.0.0.1", port=port, debug=debug_mode)
