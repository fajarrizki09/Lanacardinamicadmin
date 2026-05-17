@echo off
setlocal

set "PYTHON=.venv\Scripts\python.exe"
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
set "PROTECTED_SRC=build\protected_src"
set "SECURITY_OBF=build\security_obf"

if not exist "%PYTHON%" (
  echo Python virtualenv tidak ditemukan: %PYTHON%
  exit /b 1
)

echo Checking for PyArmor...
"%PYTHON%" -m pyarmor.cli --version >nul 2>&1
if errorlevel 1 (
  echo PyArmor tidak ditemukan. Menginstal...
  "%PYTHON%" -m pip install pyarmor
  if errorlevel 1 (
    echo Gagal menginstal PyArmor.
    exit /b 1
  )
)

echo Cleaning previous protected build...
if exist "dist\LancarDinamicAdmin" rmdir /S /Q "dist\LancarDinamicAdmin"
if exist "%PROTECTED_SRC%" rmdir /S /Q "%PROTECTED_SRC%"
if exist "%SECURITY_OBF%" rmdir /S /Q "%SECURITY_OBF%"
if exist "build\obfuscated_test" rmdir /S /Q "build\obfuscated_test"

echo Preparing protected source tree...
mkdir "%PROTECTED_SRC%"
robocopy . "%PROTECTED_SRC%" /E ^
  /XD .git .venv build dist __pycache__ .pytest_cache backups invoices logs exports attached_assets .local .config .codex ^
  /XF settings.json *.db *.db-shm *.db-wal *.zip *.pdf pyarmor.bug.log git_status.txt status.txt exe_out.txt exe_out_2.txt >nul
if errorlevel 8 (
  echo Gagal menyalin source untuk build.
  exit /b 1
)

echo Obfuscating security-sensitive modules with PyArmor...
"%PYTHON%" -m pyarmor.cli gen --output "%SECURITY_OBF%" ^
  helpers\license.py ^
  helpers\local_token.py ^
  helpers\secure_settings.py ^
  api\license_guard.py ^
  api\admin_pin.py ^
  settings.py

if errorlevel 1 (
  echo PyArmor gagal melakukan obfuscation.
  echo Catatan: PyArmor trial sering membatasi full-project obfuscation. Gunakan lisensi PyArmor untuk proteksi penuh.
  exit /b 1
)

echo Applying obfuscated modules...
copy /Y "%SECURITY_OBF%\license.py" "%PROTECTED_SRC%\helpers\license.py" >nul
copy /Y "%SECURITY_OBF%\local_token.py" "%PROTECTED_SRC%\helpers\local_token.py" >nul
copy /Y "%SECURITY_OBF%\secure_settings.py" "%PROTECTED_SRC%\helpers\secure_settings.py" >nul
copy /Y "%SECURITY_OBF%\license_guard.py" "%PROTECTED_SRC%\api\license_guard.py" >nul
copy /Y "%SECURITY_OBF%\admin_pin.py" "%PROTECTED_SRC%\api\admin_pin.py" >nul
copy /Y "%SECURITY_OBF%\settings.py" "%PROTECTED_SRC%\settings.py" >nul
xcopy /E /I /Y "%SECURITY_OBF%\pyarmor_runtime_000000" "%PROTECTED_SRC%\pyarmor_runtime_000000" >nul

echo Bumping patch version...
for /f "usebackq delims=" %%v in (`"%PYTHON%" scripts\bump_version.py`) do set "APP_VERSION=%%v"
if "%APP_VERSION%"=="" (
  echo Gagal menaikkan versi aplikasi.
  exit /b 1
)
echo Version: %APP_VERSION%

echo Building executable with PyInstaller from protected source...
cd "%PROTECTED_SRC%"
..\..\.venv\Scripts\python.exe -m PyInstaller ^
  --noconfirm ^
  --onedir ^
  --windowed ^
  --icon=icon.ico ^
  --name "LancarDinamicAdmin" ^
  --add-data "api/templates;api/templates" ^
  --add-data "api/static;api/static" ^
  --copy-metadata fastapi ^
  --copy-metadata starlette ^
  --copy-metadata pydantic ^
  --copy-metadata uvicorn ^
  --exclude-module "legacy_ui" ^
  --exclude-module "main_window" ^
  --exclude-module "components" ^
  --exclude-module "dialogs" ^
  --exclude-module "viewmodels" ^
  --exclude-module "threads" ^
  --hidden-import "uvicorn.logging" ^
  --hidden-import "uvicorn.loops" ^
  --hidden-import "uvicorn.loops.auto" ^
  --hidden-import "uvicorn.protocols" ^
  --hidden-import "uvicorn.protocols.http" ^
  --hidden-import "uvicorn.protocols.http.auto" ^
  --hidden-import "uvicorn.protocols.websockets" ^
  --hidden-import "uvicorn.protocols.websockets.auto" ^
  --hidden-import "uvicorn.lifespan" ^
  --hidden-import "uvicorn.lifespan.on" ^
  --hidden-import "uvicorn.lifespan.off" ^
  --hidden-import "sqlalchemy.sql.default_comparator" ^
  --hidden-import "pyarmor_runtime_000000" ^
  --hidden-import "helpers.license" ^
  --hidden-import "helpers.local_token" ^
  --hidden-import "helpers.secure_settings" ^
  --hidden-import "api.license_guard" ^
  --hidden-import "api.admin_pin" ^
  --hidden-import "helpers.payment_providers.mock" ^
  --hidden-import "helpers.payment_providers.midtrans" ^
  main.py

if errorlevel 1 (
  echo PyInstaller build gagal.
  cd ..\..
  exit /b 1
)

cd ..\..
echo Moving output back to dist...
if exist "dist\LancarDinamicAdmin" rmdir /S /Q "dist\LancarDinamicAdmin"
move "%PROTECTED_SRC%\dist\LancarDinamicAdmin" "dist\" >nul

if not exist "%ISCC%" (
  echo Inno Setup Compiler tidak ditemukan.
  echo Exe terproteksi berhasil dibuat di dist\LancarDinamicAdmin\LancarDinamicAdmin.exe
  exit /b 0
)

echo Building installer with Inno Setup...
"%ISCC%" RumahSehatInstaller.iss
if errorlevel 1 (
  echo Build installer gagal.
  exit /b 1
)

echo Build finished with PyArmor protection!
echo Executable: dist\LancarDinamicAdmin\LancarDinamicAdmin.exe
echo Installer: dist\LancarDinamicAdmin_Setup_v%APP_VERSION%.exe
exit /b 0
