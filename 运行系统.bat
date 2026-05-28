@echo off
chcp 65001 >nul
title 3D 打印资产管理系统 v0.6.2.0 便携版运维看板

echo ==================================================
echo        3D 打印资产管理系统 v0.6.2.0 (Windows 便携版)
echo        启动时间: %date% %time%
echo ==================================================
echo.
echo 使用说明:
echo 1. 系统将在系统默认浏览器中自动打开管理界面
echo 2. 本地访问地址: http://127.0.0.1:9055
echo 3. 【重要】使用完毕后，直接关闭本窗口或按 Ctrl+C 即可退出系统
echo ==================================================
echo.

echo [防灾检查] 正在检测并收尾上一次的运行状态...
:: 强行强杀上一次因暴毙、闪退、异常关闭而残留的后台进程，确保 9055 端口不被占用
taskkill /f /im server.exe >nul 2>&1

echo [系统信息]
echo 应用根目录: %~dp0
echo 数据库路径: %~dp0data\database\filament_inventory.db
echo 静态资源路径: %~dp0static
echo --------------------------------------------------
echo 正在启动本地服务器并挂载数据引擎...

:: 延迟 2 秒后自动唤醒默认浏览器打开网页（在后台异步执行唤醒命令）
start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:9055"

:: 正式在前台阻塞运行 Flask 后端服务（可执行文件存放在 backend 子目录下）
:: 这样 Flask 的实时 HTTP 访问请求日志会直接在此 CMD 窗口中回显滚动
"%~dp0backend\server.exe"

echo.
echo 后台服务已安全下机。
timeout /t 3 >nul
exit
