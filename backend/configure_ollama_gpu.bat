:: Ollama GPU Configuration Script for GTX 1650 (4GB VRAM)
:: Run this script as Administrator to configure Ollama for optimal GPU usage

@echo off
echo ============================================================
echo Ollama GPU Configuration for GTX 1650 (4GB VRAM)
echo ============================================================
echo.

:: Set environment variables for GPU acceleration
echo [1/4] Setting environment variables...
setx OLLAMA_NUM_GPU "1" /M
setx OLLAMA_GPU_LAYERS "33" /M
setx CUDA_VISIBLE_DEVICES "0" /M
echo    - OLLAMA_NUM_GPU = 1
echo    - OLLAMA_GPU_LAYERS = 33 (optimized for 4GB VRAM)
echo    - CUDA_VISIBLE_DEVICES = 0
echo.

:: Check if Ollama service exists
echo [2/4] Checking Ollama service...
sc query Ollama >nul 2>&1
if %errorlevel% == 0 (
    echo    Ollama service found
    echo.
    echo [3/4] Restarting Ollama service...
    net stop Ollama
    timeout /t 2 >nul
    net start Ollama
    echo    Ollama service restarted
) else (
    echo    Ollama service not found
    echo    You may need to restart Ollama manually
)
echo.

:: Keep model loaded
echo [4/4] Preloading model with GPU...
echo    Running: ollama run qwen2.5:7b-instruct --keepalive=-1
echo    This will keep the model loaded in GPU memory
echo.
echo    Close the Ollama window AFTER you see model is ready
echo.
start cmd /k "ollama run qwen2.5:7b-instruct"

echo.
echo ============================================================
echo Configuration Complete!
echo ============================================================
echo.
echo NEXT STEPS:
echo 1. Verify GPU is detected: ollama ps
echo 2. Check NVIDIA GPU: nvidia-smi
echo 3. Restart your backend server
echo.
echo Expected VRAM usage: ~3.8 GB (out of 4 GB)
echo Expected speedup: 5-10x faster than CPU
echo.
pause
