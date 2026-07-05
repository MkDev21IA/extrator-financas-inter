@echo off
title Pipeline Financeiro - Banco Inter
color 0A

echo ===================================================
echo   INICIANDO AMBIENTE LINUX (WSL) E PIPELINE...
echo ===================================================
echo.

REM Descobre o diretorio atual do script no formato WSL e executa o orquestrador
wsl bash -c "cd $(wslpath '%~dp0..') && source venv/bin/activate && python main.py"

pause >nul