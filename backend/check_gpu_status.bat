@echo off
echo ============================================================
echo GPU Status Check for Ollama
echo ============================================================
echo.

echo [1/3] Checking if Ollama is running...
ollama ps
echo.

echo [2/3] Checking NVIDIA GPU...
nvidia-smi
echo.

echo [3/3] GPU Environment Variables:
echo OLLAMA_NUM_GPU = %OLLAMA_NUM_GPU%
echo OLLAMA_GPU_LAYERS = %OLLAMA_GPU_LAYERS%
echo CUDA_VISIBLE_DEVICES = %CUDA_VISIBLE_DEVICES%
echo.

echo ============================================================
echo IF YOU SEE:
echo  - Model loaded with VRAM usage ~3.8GB = GPU is working!
echo  - VRAM = 0 MB = GPU NOT configured, run configure_ollama_gpu.bat
echo ============================================================
pause
