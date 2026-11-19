@echo off
setlocal

set "PYTHON=.venv\Scripts\python.exe"
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
set "BUNDLED_NODE_EXE=%CD%\tools\node\node.exe"
set "BUNDLED_NPM_CMD=%CD%\tools\node\npm.cmd"

if not exist "%PYTHON%" (
  echo Python virtualenv tidak ditemukan: %PYTHON%
  exit /b 1
)

echo Bumping patch version for this installer...
for /f "usebackq delims=" %%v in (`"%PYTHON%" scripts\bump_version.py`) do set "APP_VERSION=%%v"
if "%APP_VERSION%"=="" (
  echo Gagal menaikkan versi aplikasi.
  exit /b 1
)
echo Version: %APP_VERSION%

if not exist "%BUNDLED_NODE_EXE%" (
  echo Node portable tidak ditemukan di tools\node\node.exe.
  echo Salin folder hasil ekstrak Node.js Windows x64 ke tools\node sebelum build installer.
  echo Contoh: tools\node\node.exe, tools\node\npm.cmd, tools\node\node_modules\npm\...
  exit /b 1
)
if not exist "%BUNDLED_NPM_CMD%" (
  echo npm portable tidak ditemukan di tools\node\npm.cmd.
  echo Pastikan folder Node.js yang disalin lengkap, termasuk npm.cmd dan node_modules\npm.
  exit /b 1
)
set "PATH=%CD%\tools\node;%PATH%"

echo Cleaning previous builds...
if exist "dist\LancarDinamicAdmin" rmdir /S /Q "dist\LancarDinamicAdmin"
if exist "build\LancarDinamicAdmin" rmdir /S /Q "build\LancarDinamicAdmin"

echo Building executable with PyInstaller...
"%PYTHON%" -m PyInstaller ^
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
  main.py

if errorlevel 1 (
  echo PyInstaller build gagal.
  exit /b 1
)

echo Bundling WhatsApp Gateway server...
if not exist "dist\LancarDinamicAdmin\openwa_server" mkdir "dist\LancarDinamicAdmin\openwa_server"
robocopy "openwa_server" "dist\LancarDinamicAdmin\openwa_server" /E ^
  /XD data logs __pycache__ .cache ^
  /XF *.log >nul
if errorlevel 8 (
  echo Gagal menyalin openwa_server ke output build.
  exit /b 1
)

if not exist "dist\LancarDinamicAdmin\openwa_server\node_modules" (
  echo Dependency openwa_server belum ada. Menjalankan npm install...
  pushd "openwa_server"
  call "%BUNDLED_NPM_CMD%" install
  if errorlevel 1 (
    popd
    echo npm install openwa_server gagal.
    exit /b 1
  )
  popd
  robocopy "openwa_server\node_modules" "dist\LancarDinamicAdmin\openwa_server\node_modules" /E >nul
  if errorlevel 8 (
    echo Gagal menyalin node_modules openwa_server.
    exit /b 1
  )
)

echo Bundling Node.js runtime...
if exist "dist\LancarDinamicAdmin\node" rmdir /S /Q "dist\LancarDinamicAdmin\node"
mkdir "dist\LancarDinamicAdmin\node"
robocopy "tools\node" "dist\LancarDinamicAdmin\node" /E >nul
if errorlevel 8 (
  echo Gagal menyalin Node.js runtime.
  exit /b 1
)

if exist "LancarDinamicAdmin.spec" del /F /Q "LancarDinamicAdmin.spec"

if not exist "%ISCC%" (
  echo Inno Setup Compiler tidak ditemukan.
  echo Exe berhasil dibuat di dist\LancarDinamicAdmin\LancarDinamicAdmin.exe
  echo Install Inno Setup 6 untuk membuat installer.
  exit /b 1
)

echo Building installer with Inno Setup...
"%ISCC%" RumahSehatInstaller.iss

if errorlevel 1 (
  echo Build installer gagal.
  exit /b 1
)

echo Build finished!
echo Executable: dist\LancarDinamicAdmin\LancarDinamicAdmin.exe
echo Installer: dist\LancarDinamicAdmin_Setup_v%APP_VERSION%.exe
exit /b 0
