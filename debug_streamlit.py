#!/usr/bin/env python3
"""
Debug script for Streamlit Cloud deployment issues
"""

import os
import sys
from pathlib import Path

import streamlit as st

# Debug information
st.title("🔍 Debug Streamlit Deployment")

st.write("### System Information")
st.write(f"- Python version: {sys.version}")
st.write(f"- Current working directory: {os.getcwd()}")
st.write(f"- Python path: {sys.path}")

st.write("### File System Check")
current_dir = Path(__file__).parent
st.write(f"- Current script directory: {current_dir}")
st.write(f"- Dashboard directory exists: {(current_dir / 'dashboard').exists()}")
st.write(f"- App.py exists: {(current_dir / 'dashboard' / 'app.py').exists()}")
st.write(f"- Streamlit config exists: {(current_dir / '.streamlit').exists()}")

if (current_dir / "dashboard").exists():
    st.write("### Dashboard Directory Contents")
    dashboard_files = list((current_dir / "dashboard").glob("*"))
    for f in dashboard_files:
        st.write(f"- {f.name}")

st.write("### Import Test")
try:
    sys.path.insert(0, str(current_dir / "dashboard"))
    from app import main

    st.success("✅ Successfully imported dashboard app")
except Exception as e:
    st.error(f"❌ Import failed: {e}")

try:
    import plotly

    st.success("✅ Plotly available")
except Exception as e:
    st.error(f"❌ Plotly import failed: {e}")

try:
    import pandas

    st.success("✅ Pandas available")
except Exception as e:
    st.error(f"❌ Pandas import failed: {e}")

st.write("### Environment Variables")
env_vars = [
    "STREAMLIT_SHARING_MODE",
    "STREAMLIT_SERVER_PORT",
    "STREAMLIT_SERVER_BASE_URL_PATH",
]
for var in env_vars:
    value = os.getenv(var, "Not set")
    st.write(f"- {var}: {value}")

st.write("### Recommendations")
st.info(
    """
If you see this page instead of the main dashboard, the issue is likely:
1. Entry point configuration in Streamlit Cloud
2. Missing dependencies in requirements.txt
3. Import path issues

**Solution**: Check Streamlit Cloud app configuration and ensure entry point is set correctly.
"""
)

# Try to load the actual app
if st.button("🚀 Try to load main app"):
    try:
        sys.path.insert(0, str(current_dir / "dashboard"))
        from app import main as app_main

        st.success("✅ Main app loaded successfully")
        # Don't call main() here to avoid conflicts
    except Exception as e:
        st.error(f"❌ Failed to load main app: {e}")
        st.code(str(e), language="python")
