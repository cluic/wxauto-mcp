@echo off
REM 发布脚本 - 构建并发布 wxauto-mcp (Windows)

echo ===================================
echo wxauto-mcp 发布脚本
echo ===================================
echo.

REM 检查版本
for /f "tokens=2 delims==" %%a in ('findstr "^version" pyproject.toml') do set VERSION=%%~a
set VERSION=%VERSION:"=%
echo 当前版本: %VERSION%
echo.

REM 清理旧的构建文件
echo 1. 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%d in (*.egg-info) do rmdir /s /q "%%d"
echo √ 清理完成
echo.

REM 构建包
echo 2. 构建包...
python -m build --outdir dist/
echo √ 构建完成
echo.

REM 检查构建结果
echo 3. 检查构建结果...
dir dist\
echo.

REM 创建Git标签
echo 4. 创建Git标签...
git tag -l "v%VERSION%" >nul 2>&1
if %errorlevel% equ 0 (
    echo √ 标签 v%VERSION% 已存在
    set /p RECREATE="是否删除旧标签并创建新标签? (y/N): "
    if /i "%RECREATE%"=="y" (
        git tag -d "v%VERSION%"
        git tag "v%VERSION%"
        echo √ 新标签已创建
    )
) else (
    git tag "v%VERSION%"
    echo √ 标签 v%VERSION% 已创建
)
echo.

REM 提示发布步骤
echo ===================================
echo 构建完成！
echo ===================================
echo.
echo 接下来的步骤：
echo.
echo 1. 推送代码到 GitHub:
echo    git push origin main
echo    git push origin v%VERSION%
echo.
echo 2. GitHub Actions 将自动:
echo    - 运行 CI 测试
echo    - 创建 Release
echo    - 上传 whl 和 tar.gz 到 Release
echo.
echo 3. 手动发布到 PyPI (可选):
echo    twine upload dist/*
echo.
echo ===================================
pause