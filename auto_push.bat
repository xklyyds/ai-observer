@echo off
chcp 65001 >nul
title 自动推送脚本

echo ============================================
echo        AI前沿观察者 - 自动推送脚本
echo ============================================
echo.

cd /d "%~dp0"

echo [1/3] 清理残留的swap文件...
if exist ".git\.COMMIT_EDITMSG.swp" (
    del ".git\.COMMIT_EDITMSG.swp"
    echo 已删除: .git/.COMMIT_EDITMSG.swp
)
echo.

echo [2/3] 检查Git状态...
git status
echo.

echo [3/3] 检查是否有未提交的修改...
git diff --quiet >nul 2>&1
if %errorlevel% equ 0 (
    git diff --cached --quiet >nul 2>&1
    if %errorlevel% equ 0 (
        echo 没有未提交的修改。
    ) else (
        echo 有暂存的修改，准备提交...
        goto DO_COMMIT
    )
) else (
    echo 发现未暂存的修改，准备添加并提交...
    git add .
    echo 已执行: git add .
    :DO_COMMIT
    set commit_msg=更新
    git commit -m "%commit_msg%"
    if %errorlevel% neq 0 (
        echo ✗ 提交失败，请手动处理。
        pause
        exit /b 1
    )
    echo 已执行: git commit -m "%commit_msg%"
)
echo.

echo [4/4] 开始推送...
set max_retries=20
set retry_delay=15
set retry_count=0

:RETRY_LOOP
set /a retry_count+=1
echo ============================================
echo 第 %retry_count%/%max_retries% 次尝试推送...
echo ============================================

git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo           ✓ 推送成功！
    echo ============================================
    echo 已成功将代码推送到 GitHub。
    echo 等待 GitHub Pages 部署完成（约1-5分钟）。
    echo.
    pause
    exit /b 0
)

echo ✗ 推送失败，等待 %retry_delay% 秒后重试...
echo.
timeout /t %retry_delay% /nobreak >nul

if %retry_count% lss %max_retries% (
    goto RETRY_LOOP
)

echo ============================================
echo           ✗ 推送失败（已重试 %max_retries% 次）
echo ============================================
echo 网络问题持续存在，请检查网络连接后手动重试。
echo.
pause
exit /b 1