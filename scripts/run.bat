@echo off
REM Helper: create venv, install deps, and run server using venv python (Windows cmd)
SET projectRoot=%~dp0..\
SET venvPath=%projectRoot%\.venv
IF NOT EXIST "%venvPath%\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv "%venvPath%"
)
"%venvPath%\Scripts\python.exe" -m pip install --upgrade pip
"%venvPath%\Scripts\python.exe" -m pip install -r "%projectRoot%\requirements.txt"
"%venvPath%\Scripts\python.exe" -m pip install -e "%projectRoot%"
"%venvPath%\Scripts\python.exe" -m uvicorn genai_project.api:app --reload --port 8000
pause