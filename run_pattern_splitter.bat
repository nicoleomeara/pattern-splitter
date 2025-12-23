@echo off
REM Pattern Splitter - Easy Runner Script (Windows)
REM Double-click this file to easily split PDF patterns

title Pattern Splitter - Easy Runner
color 0B

echo.
echo  ####################################
echo  #  Pattern Splitter - Easy Runner  #
echo  ####################################
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if pattern_splitter_fixed.py exists
if not exist "pattern_splitter_fixed.py" (
    echo [ERROR] pattern_splitter_fixed.py not found!
    pause
    exit /b 1
)

echo [OK] Environment ready!
echo.

REM Prompt for PDF file path
echo Please enter the path to your PDF file:
echo (You can drag and drop the file here, or type/paste the path)
echo.
set /p pdf_path="PDF Path: "

REM Remove quotes if user added them
set pdf_path=%pdf_path:"=%

REM Check if file exists
if not exist "%pdf_path%" (
    echo [ERROR] File not found: %pdf_path%
    pause
    exit /b 1
)

echo.
echo Processing PDF...
echo.

REM Run the pattern splitter
.venv\Scripts\python pattern_splitter_fixed.py "%pdf_path%"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Pattern splitting completed successfully!
) else (
    echo.
    echo [ERROR] An error occurred during processing.
)

echo.
pause