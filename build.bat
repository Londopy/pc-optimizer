@echo off
setlocal EnableDelayedExpansion
title PC Optimizer Pro - Build Script
color 0A

echo.
echo  ===============================================
echo   PC OPTIMIZER PRO -- BUILD PIPELINE
echo   github.com/Londopy/pc-optimizer
echo  ===============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERR] Python not found. Install Python 3.11+
    pause & exit /b 1
)

for /f "tokens=2" %%v in ('python --version') do set PY_VER=%%v
echo  [OK] Python %PY_VER%

:: Check pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERR] pip not found.
    pause & exit /b 1
)

:: Install requirements
echo.
echo  [>>] Installing requirements...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo  [ERR] Failed to install requirements.
    pause & exit /b 1
)
echo  [OK] Requirements installed

:: Create assets dir if missing
if not exist "assets" mkdir assets
if not exist "assets\icon.ico" (
    echo  [!!] No icon.ico found in assets\. Using default.
    :: Generate a placeholder - real builds should have a proper icon
    python -c "
from PIL import Image, ImageDraw
img = Image.new('RGBA', (256, 256), (10, 14, 20, 255))
d = ImageDraw.Draw(img)
d.ellipse([20, 20, 236, 236], outline=(0, 212, 170), width=8)
d.polygon([(128, 60), (196, 196), (60, 196)], fill=(0, 212, 170))
img.save('assets/icon.png')
print('Generated assets/icon.png')
" 2>nul
    python -c "
try:
    from PIL import Image
    img = Image.open('assets/icon.png')
    img.save('assets/icon.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    print('Generated assets/icon.ico')
except Exception as e:
    print(f'Could not generate ico: {e}')
" 2>nul
)

:: Clean old build
echo.
echo  [>>] Cleaning old build artifacts...
if exist "dist\PCOptimizerPro" rmdir /s /q "dist\PCOptimizerPro"
if exist "build\PCOptimizerPro" rmdir /s /q "build\PCOptimizerPro"
echo  [OK] Clean complete

:: Run PyInstaller
echo.
echo  [>>] Building with PyInstaller...
pyinstaller pc_optimizer.spec --noconfirm
if %errorlevel% neq 0 (
    echo  [ERR] PyInstaller build failed.
    pause & exit /b 1
)
echo  [OK] PyInstaller build complete

:: Check output
if not exist "dist\PCOptimizerPro\PCOptimizerPro.exe" (
    echo  [ERR] Build output not found at dist\PCOptimizerPro\PCOptimizerPro.exe
    pause & exit /b 1
)

:: Build size
for /f "tokens=3" %%s in ('dir "dist\PCOptimizerPro" /-c /s ^| findstr "File(s)"') do set BUILD_SIZE=%%s
echo  [OK] Build size: %BUILD_SIZE% bytes

:: Try Inno Setup if available
echo.
set ISCC_PATH=""
if exist "%PROGRAMFILES(X86)%\Inno Setup 6\ISCC.exe" set ISCC_PATH="%PROGRAMFILES(X86)%\Inno Setup 6\ISCC.exe"
if exist "%PROGRAMFILES%\Inno Setup 6\ISCC.exe" set ISCC_PATH="%PROGRAMFILES%\Inno Setup 6\ISCC.exe"

if not %ISCC_PATH%=="" (
    echo  [>>] Building installer with Inno Setup...
    if not exist "installer\output" mkdir "installer\output"
    %ISCC_PATH% installer\setup.iss
    if %errorlevel% equ 0 (
        echo  [OK] Installer built: installer\output\
    ) else (
        echo  [!!] Inno Setup failed - .exe is still usable from dist\PCOptimizerPro\
    )
) else (
    echo  [--] Inno Setup not found - skipping installer packaging
    echo       Install from: https://jrsoftware.org/isdl.php
    echo       Then re-run this script to get a setup .exe
)

echo.
echo  ===============================================
echo   BUILD COMPLETE
echo  ===============================================
echo.
echo   Portable exe: dist\PCOptimizerPro\PCOptimizerPro.exe
if not %ISCC_PATH%=="" echo   Installer:    installer\output\PCOptimizerPro_Setup_v1.0.0.exe
echo.
echo   Ready to upload to github.com/Londopy/pc-optimizer
echo.
pause
