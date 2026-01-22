@echo off
setlocal
cd /d "%~dp0\.."
call .venv\Scripts\activate.bat
python -m streamlit run dashboard\app.py --server.port 8501
endlocal
