@echo off
chcp 65001 >nul
echo ========================================
echo 微信自动登录保持在线监控程序
echo 作者: 李祥光
echo 创建时间: 2025-06-24
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查是否在正确的目录
if not exist "wechat_monitor_enhanced.py" (
    echo 错误: 未找到主程序文件，请确保在正确的目录下运行此脚本
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖包...
python -c "import wxautox, psutil, plyer" >nul 2>&1
if errorlevel 1 (
    echo 警告: 部分依赖包未安装，正在尝试安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖包安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo 依赖检查完成，启动监控程序...
echo.

REM 启动监控程序
python wechat_monitor_enhanced.py

echo.
echo 程序已退出
pause