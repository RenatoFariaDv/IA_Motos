@echo off
cd /d "%~dp0"

:menu
cls
echo ========================================
echo               IA MOTOS
echo ========================================
echo.
echo 1 - Iniciar sistema
echo 2 - Ver status
echo 3 - Parar sistema
echo 4 - Abrir painel local
echo 5 - Abrir painel AWS
echo 6 - Sair
echo.
set /p op=Escolha uma opcao:

if "%op%"=="1" (
    if exist iniciar_ia_motos.bat call iniciar_ia_motos.bat
    goto menu
)

if "%op%"=="2" (
    if exist status_ia_motos.bat call status_ia_motos.bat
    goto menu
)

if "%op%"=="3" (
    if exist parar_ia_motos.bat call parar_ia_motos.bat
    goto menu
)

if "%op%"=="4" (
    start "" http://127.0.0.1:5000
    goto menu
)

if "%op%"=="5" (
    start "" http://54.233.146.58:5000/?origem=all&ordenacao=recentes
    goto menu
)

if "%op%"=="6" exit

echo Opcao invalida
pause
goto menu