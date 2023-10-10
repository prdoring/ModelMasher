@echo off

REM Check Python installation
python --version > NUL 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python and run this script again.
    exit /b
)

REM Check for missing dependencies and install them
echo Checking for required Python packages...

for %%i in (flask cv2 numpy os json PIL) do (
    python -c "import %%i" 2>NUL
    if errorlevel 1 (
        echo Installing missing package: %%i...
        python -m pip install %%i
    )
)

REM Run server.py in the background
start python server.py

REM Wait a moment to ensure the server has time to start
timeout /T 5

REM Open the browser
start http://127.0.0.1:5000