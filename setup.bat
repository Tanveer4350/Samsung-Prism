@echo off
setlocal
where py >nul 2>&1
if errorlevel 1 (
  echo Python 3 was not found. Install Python 3.10+ and enable "Add python.exe to PATH".
  exit /b 1
)
py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
where blender >nul 2>&1
if errorlevel 1 echo [WARNING] Blender was not found in PATH. Install Blender 4.0+ and add blender.exe to PATH.
where ffmpeg >nul 2>&1
if errorlevel 1 echo [WARNING] FFmpeg was not found in PATH. Add FFmpeg bin to PATH for MP4 rendering.
echo Setup complete.
