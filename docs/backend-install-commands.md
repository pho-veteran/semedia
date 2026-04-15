# Backend Install Commands

These commands provision the active Semedia microservice backend. For MVP delivery, prefer Docker Compose first.

## Docker Compose First

```bash
cd Semedia
docker compose up --build gateway-api frontend
curl http://127.0.0.1:8000/api/v1/runtime/
docker compose --profile test run --rm --build service-tests
python testing/smoke_stack.py
```

This starts PostgreSQL, the GPU-backed `media-worker`, `search-api`, `gateway-api`, and the frontend. The default worker requests `gpus: all`, installs CUDA-enabled PyTorch `2.10.0`, runs with `ML_DEVICE=cuda` and `ML_STRICT_CUDA=1`, and exposes runtime diagnostics through `gateway-api`.

## Windows PowerShell

```powershell
cd C:\Users\thanh\Desktop\workspace\semantic-media-search
winget install Python.Python.3.11
winget install ffmpeg

cd Semedia\services\gateway_api
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

cd ..\media_worker
pip install -r requirements.txt
pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.gpu.txt

cd ..\search_api
pip install -r requirements.txt

cd ..\..\testing\services
pip install pytest httpx
```

## WSL2 / Ubuntu

```bash
cd /mnt/c/Users/thanh/Desktop/workspace/semantic-media-search
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip ffmpeg libgl1 libglib2.0-0

cd Semedia/services/gateway_api
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

cd ../media_worker
pip install -r requirements.txt
pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.gpu.txt

cd ../search_api
pip install -r requirements.txt

cd ../../testing/services
pip install pytest httpx
```

## Notes

- The current Compose GPU image uses the official CUDA `13.0` PyTorch wheel index: `https://download.pytorch.org/whl/cu130`.
- If `cu130` does not match your installed NVIDIA stack, replace it with the CUDA build recommended by the current PyTorch selector.
- The current MVP caption default is `Salesforce/blip-image-captioning-base` because it is much more realistic on a 6 GB RTX 3060 than BLIP-2.
- Strict CUDA mode is enabled in the default worker container. If GPU inference cannot run, processing fails loudly instead of falling back to CPU.
- Shared Python imports resolve through `Semedia/services/shared/`, so keep `PYTHONPATH` aligned if you run the services directly outside Docker.
