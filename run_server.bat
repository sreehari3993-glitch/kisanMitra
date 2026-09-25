@echo off
title KrishiMitra Server - localhost:8000
echo ===================================================
echo   KrishiMitra Precision Agriculture Platform
echo   Local Server: http://localhost:8000
echo   Direct IP:    http://127.0.0.1:8000
echo ===================================================
if exist "%~dp0\.venv\Scripts\python.exe" (
    "%~dp0\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    "C:\Users\sreeh\.gemini\antigravity-ide\scratch\krishimitra\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
)
pause
