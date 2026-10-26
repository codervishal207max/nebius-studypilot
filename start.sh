#!/bin/sh
# Run the API (8000) and the UI (8501) together
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
sleep 2
exec streamlit run ui.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
