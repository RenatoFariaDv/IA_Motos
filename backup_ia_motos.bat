@echo off
REM Script de backup para IA_Motos - compatível com Windows 10/11
REM Nao usar acentos nas mensagens

REM 1. Criar pasta backup se nao existir
if not exist "backup" (
    mkdir "backup"
)

REM 2. Criar subpasta com data e hora
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    set YYYY=%%d
    set MM=%%b
    set DD=%%c
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set HH=%%a
    set MN=%%b
)
REM Ajustar formato de hora para evitar problemas com caracteres especiais
set HH=%HH: =0%
set MN=%MN: =0%
set BACKUP_FOLDER=backup\%YYYY%-%MM%-%DD%_%HH%-%MN%-%random%
mkdir "%BACKUP_FOLDER%"

REM 3. Copiar arquivos especificados

REM Função para copiar arquivo se existir, senão avisar
setlocal enabledelayedexpansion

call :copy_if_exists "interface\anuncios_encontrados.json"
call :copy_if_exists "interface\filtros.json"
call :copy_if_exists "interface\ml_enviados.json"
call :copy_if_exists "iniciar_ia_motos.bat"
call :copy_if_exists "parar_ia_motos.bat"
call :copy_if_exists "status_ia_motos.bat"
call :copy_if_exists "dashboard_ia_motos.bat"
call :copy_if_exists "IA_Motos.bat"
call :copy_if_exists "sincronizar_aws.ps1"

REM 4. Nao copiar pastas/arquivos proibidos (ja garantido por selecao manual)

REM 5. Mostrar caminho final do backup
echo.
echo Backup criado em: %BACKUP_FOLDER%
echo.
pause
exit /b

:copy_if_exists
set FILE=%~1
if exist "%FILE%" (
    copy "%FILE%" "%BACKUP_FOLDER%" >nul
    echo Copiado: %FILE%
) else (
    echo Aviso: %FILE% nao encontrado
)
exit /b