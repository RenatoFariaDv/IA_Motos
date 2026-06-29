@echo off
REM ==========================================
REM  IA_Motos - Inicializacao Automatica
REM  Este script inicia todos os servicos do projeto IA_Motos
REM  Compatível com Windows 10/11
REM ==========================================

REM Garante execução a partir da raiz do projeto
cd /d "%~dp0"

echo ==========================================
echo   INICIANDO IA_MOTOS
echo ==========================================
echo.

REM 1. Inicia main.py (Robo OLX + Mercado Livre) em nova janela CMD
echo [1/4] Abrindo janela CMD para Robo OLX + Mercado Livre...
start "Robo OLX + Mercado Livre" cmd /k "python main.py"
echo   >> Janela 1: Robo OLX + Mercado Livre iniciada.
echo.
timeout /t 5 /nobreak >nul

REM 2. Inicia sincronizar_aws.ps1 em nova janela PowerShell
echo [2/4] Abrindo janela PowerShell para sincronizacao AWS...
start "Sincronizacao AWS" powershell -NoExit -ExecutionPolicy Bypass -File sincronizar_aws.ps1
echo   >> Janela 2: Sincronizacao AWS iniciada.
echo.
timeout /t 3 /nobreak >nul

REM 3. Inicia interface/app.py (Painel Flask) em nova janela CMD
echo [3/4] Abrindo janela CMD para Painel Flask...
start "Painel Flask" cmd /k "python interface\app.py"
echo   >> Janela 3: Painel Flask iniciada.
echo.
timeout /t 5 /nobreak >nul

REM 4. Abre navegador padrão no painel Flask
echo [4/4] Abrindo navegador em http://127.0.0.1:5000 ...
start "" "http://127.0.0.1:5000"
echo.

REM Resumo final
echo ==========================================
echo   RESUMO DAS JANELAS ABERTAS:
echo.
echo   Janela 1 = Robo OLX + Mercado Livre
echo   Janela 2 = Sincronizacao AWS
echo   Janela 3 = Painel Flask (http://127.0.0.1:5000)
echo.
echo ==========================================
echo Todos os servicos foram inicializados!
echo.
echo Para encerrar, feche manualmente as janelas abertas.
echo Esta janela principal pode ser fechada a qualquer momento.
echo.
pause