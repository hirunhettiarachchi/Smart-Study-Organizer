@echo off
title Smart Study Organizer Launcher
start "" "chrome.exe" --app=http://localhost:8501
python -m streamlit run app.py --server.headless true