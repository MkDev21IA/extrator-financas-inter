@echo off
title Gerenciador de Parcelamentos - Finanças
color 0A

echo ===================================================
echo   INICIANDO GERENCIADOR DE PARCELAMENTOS (WSL)...
echo ===================================================
echo.

REM Descobre o diretório atual do script no formato WSL e executa o script de parcelas
wsl bash -c "cd $(wslpath '%~dp0..') && source venv/bin/activate && python manage_portions.py"

pause >nul