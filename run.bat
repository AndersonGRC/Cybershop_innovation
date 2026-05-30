@echo off
setlocal

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
  echo Creando venv por primera vez...
  python -m venv venv
  call ".\venv\Scripts\activate.bat"
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
) else (
  call ".\venv\Scripts\activate.bat"
)

if not exist ".cybershop.conf" (
  echo.
  echo ERROR: falta .cybershop.conf
  echo Copia .cybershop.conf.example a .cybershop.conf y llena los valores.
  exit /b 1
)

echo.
echo CyberShopAdmin levantando en http://localhost:5002
echo.
python app.py
