@echo off
echo Building RF CAD Application...

REM Install requirements
echo Installing requirements...
pip install -r ..\requirements.txt

REM Create executable with PyInstaller
echo Creating executable with PyInstaller...
pyinstaller --clean ..\rf_cad.spec

REM Check if NSIS is installed
where makensis >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo NSIS is not installed or not in PATH.
    echo Please install NSIS from https://nsis.sourceforge.io/Download
    echo and add it to your PATH.
    echo.
    echo Skipping installer creation.
) else (
    REM Create installer with NSIS
    echo Creating installer with NSIS...
    makensis installer.nsi
)

echo Build process completed.
echo.
echo If successful, you can find:
echo - The executable at: dist\RF_CAD.exe
echo - The installer at: RF_CAD_Setup_1.0.0.exe
echo.
pause 