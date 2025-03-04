@echo off
echo WinCommander - Building executable...
echo.

REM Check if PyInstaller is installed
pip show pyinstaller > nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo Failed to install PyInstaller. Please check your internet connection and try again.
        pause
        exit /b 1
    )
)

REM Clean previous build directories if they exist
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Create the executable using PyInstaller
echo.
echo Building executable with PyInstaller...
pyinstaller --noconfirm ^
    --clean ^
    --name="WinCommander" ^
    --windowed ^
    --icon="wincommander.ico" ^
    --add-data="wincommander.ico;." ^
    --hidden-import="PyQt5.QtPrintSupport" ^
    --hidden-import="PyQt5.QtNetwork" ^
    --log-level=INFO ^
    wincommander.py

if %errorlevel% neq 0 (
    echo.
    echo Build failed. Please check the errors above.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable created at: dist\WinCommander\WinCommander.exe
echo.

REM Create shortcut on desktop (optional)
echo Would you like to create a shortcut on the desktop? (Y/N)
set /p create_shortcut=

if /i "%create_shortcut%"=="Y" (
    echo Creating shortcut on desktop...
    
    REM Get the full path of the executable
    for %%i in (dist\WinCommander\WinCommander.exe) do set "exe_path=%%~fi"
    
    REM Create a PowerShell command to create the shortcut
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\WinCommander.lnk'); $Shortcut.TargetPath = '%exe_path%'; $Shortcut.IconLocation = '%exe_path%,0'; $Shortcut.Save()"
    
    echo Shortcut created on desktop.
)

echo.
echo Process completed! Press any key to exit...
pause > nul 