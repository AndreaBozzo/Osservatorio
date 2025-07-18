#!/usr/bin/env python3
"""
Streamlit Cloud Entry Point
This file is required for Streamlit Cloud deployment
"""

import sys
from pathlib import Path

# Add dashboard directory to path
dashboard_dir = Path(__file__).parent / "dashboard"
sys.path.insert(0, str(dashboard_dir))

# Import and run the main app
from app import main

if __name__ == "__main__":
    main()
