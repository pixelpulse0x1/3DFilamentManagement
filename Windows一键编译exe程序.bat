@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title 3D 打印资产管理系统 — 一键编译打包工具

set VERSION=v0.6.2.2
set OUTPUT_NAME=3D_Inventory_Management_%VERSION%

echo ============================================================
echo     3D 打印资产管理系统 — 一键编译打包工具
echo     目标版本: %VERSION%
echo     启动时间: %date% %time%
echo ============================================================
echo.
echo 本脚本将自动完成以下步骤:
echo   1. 创建 Python 虚拟环境
echo   2. 安装编译依赖 (flask, pyinstaller, openpyxl, requests)
echo   3. PyInstaller 编译 server.exe
echo   4. 组装最终绿色便携版发布包
echo.
echo   输出目录: %~dp0..\%OUTPUT_NAME%
echo ============================================================
echo.

:: ─── Step 0: 环境预检 ───
echo [预检] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 并加入系统 PATH
    pause
    exit /b 1
)
python --version

echo [预检] 检查 Git 环境...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未检测到 Git，将跳过代码拉取步骤，使用当前目录代码编译
    set SKIP_GIT=1
) else (
    set SKIP_GIT=0
)

:: ─── Step 1: 代码同步（可选） ───
if %SKIP_GIT% equ 0 (
    echo.
    echo [Git] 拉取最新代码...
    cd /d "%~dp0"
    git checkout main >nul 2>&1
    git pull origin main 2>&1
    if %errorlevel% neq 0 (
        echo [警告] Git 拉取失败，将使用当前本地代码继续编译
    ) else (
        echo [Git] 代码已同步至最新
    )
)

:: ─── Step 2: 创建/激活虚拟环境 ───
echo.
echo [环境] 创建纯净 Python 虚拟沙盒...

:: 切换到 workspace 所在目录
cd /d "%~dp0"

set VENV_DIR=%~dp0venv_build

if exist "%VENV_DIR%" (
    echo [环境] 检测到已有虚拟环境，正在清理...
    rmdir /s /q "%VENV_DIR%" >nul 2>&1
)

python -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境创建失败
    pause
    exit /b 1
)
echo [环境] 虚拟环境创建成功

:: 激活虚拟环境
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)
echo [环境] 虚拟环境已激活

:: ─── Step 3: 安装依赖 ───
echo.
echo [依赖] 升级 pip...
python -m pip install --upgrade pip --quiet
echo [依赖] 安装编译所需包...
pip install flask pyinstaller openpyxl requests --quiet
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    call deactivate
    pause
    exit /b 1
)
echo [依赖] 安装完成: flask, pyinstaller, openpyxl, requests

:: ─── Step 4: 清理旧编译产物 ───
echo.
echo [清理] 清除旧编译缓存...

if exist "%~dp0build" (
    rmdir /s /q "%~dp0build" >nul 2>&1
    echo [清理] 已删除 build/ 目录
)
if exist "%~dp0backend" (
    rmdir /s /q "%~dp0backend" >nul 2>&1
    echo [清理] 已删除 backend/ 目录
)
if exist "%~dp0*.spec" (
    del /q "%~dp0*.spec" >nul 2>&1
    echo [清理] 已删除 .spec 文件
)

:: ─── Step 5: PyInstaller 编译 ───
echo.
echo ============================================================
echo [编译] 开始 PyInstaller 编译 (预计 2-5 分钟，请耐心等待)...
echo ============================================================

cd /d "%~dp0"

pyinstaller ^
    --onedir ^
    --name server ^
    --clean ^
    --hidden-import=openpyxl ^
    --distpath "%~dp0backend" ^
    --workpath "%~dp0build" ^
    --specpath "%~dp0build" ^
    app.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] PyInstaller 编译失败！请检查上方的错误信息
    call deactivate
    pause
    exit /b 1
)
echo [编译] PyInstaller 编译成功！

:: ─── Step 6: 扁平化 backend 目录 ───
echo.
echo [组装] 扁平化 backend 目录结构...

set BACKEND_DIR=%~dp0backend\server

if exist "%BACKEND_DIR%" (
    :: 将 backend/server/ 下所有内容提取到 backend/ 根
    move "%BACKEND_DIR%\*" "%~dp0backend\" >nul 2>&1
    :: 删除空壳 server/ 目录
    rmdir /s /q "%BACKEND_DIR%" >nul 2>&1
    echo [组装] backend 目录已扁平化 (server/ 内文件提取至 backend/ 根)
) else (
    echo [警告] 未找到 backend\server\ 目录，跳过扁平化
)

:: ─── Step 7: 组装最终发布包 ───
echo.
echo [组装] 组装最终发布包...

set RELEASE_DIR=%~dp0..\%OUTPUT_NAME%

:: 若已有同名输出目录，先清理
if exist "%RELEASE_DIR%" (
    echo [组装] 检测到已有输出目录，正在覆盖...
    rmdir /s /q "%RELEASE_DIR%" >nul 2>&1
)

mkdir "%RELEASE_DIR%"
if %errorlevel% neq 0 (
    echo [错误] 无法创建输出目录: %RELEASE_DIR%
    call deactivate
    pause
    exit /b 1
)

:: 复制 backend/ 目录
echo [组装] 复制 backend/ (编译产物)...
xcopy "%~dp0backend" "%RELEASE_DIR%\backend\" /e /i /q /y >nul
if %errorlevel% neq 0 (
    echo [警告] backend/ 复制异常，请手动检查
)

:: 复制 static/ 目录
echo [组装] 复制 static/ (前端静态资源)...
xcopy "%~dp0static" "%RELEASE_DIR%\static\" /e /i /q /y >nul

:: 复制 templates/ 目录
echo [组装] 复制 templates/ (HTML 模板)...
xcopy "%~dp0templates" "%RELEASE_DIR%\templates\" /e /i /q /y >nul

:: 复制运行系统.bat
echo [组装] 复制 运行系统.bat (启动脚本)...
copy "%~dp0运行系统.bat" "%RELEASE_DIR%\运行系统.bat" /y >nul

:: 复制 LICENSE (可选)
if exist "%~dp0LICENSE" (
    copy "%~dp0LICENSE" "%RELEASE_DIR%\LICENSE" /y >nul
    echo [组装] 已复制 LICENSE
)

:: ─── Step 8: 清理临时编译产物 ───
echo.
echo [清理] 删除临时编译缓存...
if exist "%~dp0build" (
    rmdir /s /q "%~dp0build" >nul 2>&1
)
if exist "%~dp0*.spec" (
    del /q "%~dp0*.spec" >nul 2>&1
)

:: 退出虚拟环境
call deactivate

:: 删除临时虚拟环境
echo [清理] 删除临时虚拟环境...
rmdir /s /q "%VENV_DIR%" >nul 2>&1

:: ─── 完成 ───
echo.
echo ============================================================
echo     编译打包完成！
echo.
echo     输出目录: %RELEASE_DIR%
echo.
echo     目录结构:
echo     %OUTPUT_NAME%\
echo       ├── 运行系统.bat
echo       ├── static\
echo       ├── templates\
echo       └── backend\
echo           ├── server.exe
echo           └── _internal\
echo.
echo     双击 %OUTPUT_NAME%\运行系统.bat 即可启动系统
echo     将 %OUTPUT_NAME% 文件夹压缩为 ZIP 即可发布
echo ============================================================
echo.
pause
exit /b 0
