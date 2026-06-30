@echo off
setlocal enabledelayedexpansion

REM Verificar se a pasta backup existe
if not exist "backup" (
    echo Pasta backup nao encontrada.
    pause
    exit /b
)

REM Listar subpastas de backup
echo Subpastas de backup disponiveis:
set "has_subfolder=0"
for /d %%D in ("backup\*") do (
    echo   %%~nxD
    set "has_subfolder=1"
)
if "!has_subfolder!"=="0" (
    echo Nenhuma subpasta encontrada em backup.
    pause
    exit /b
)

REM Solicitar nome da pasta de backup para restaurar
set /p BACKUP_FOLDER=Digite o nome da pasta de backup para restaurar: 

REM Verificar se a pasta escolhida existe
if not exist "backup\%BACKUP_FOLDER%\" (
    echo Pasta de backup nao encontrada.
    pause
    exit /b
)

REM Lista de arquivos a restaurar
set FILES_TO_RESTORE=interface\anuncios_encontrados.json interface\filtros.json interface\ml_enviados.json iniciar_ia_motos.bat parar_ia_motos.bat status_ia_motos.bat dashboard_ia_motos.bat IA_Motos.bat sincronizar_aws.ps1

REM Restaurar arquivos
for %%F in (%FILES_TO_RESTORE%) do (
    set "SRC=backup\%BACKUP_FOLDER%\%%F"
    set "DST=%%F"
    if exist "!SRC!" (
        if exist "!DST!" (
            set /p CONFIRM=Arquivo %%F existe. Confirmar restauracao? (S/N): 
            if /i "!CONFIRM!" neq "S" (
                echo Pulando arquivo %%F.
                goto :CONTINUE_LOOP
            )
        )
        REM Restaurar arquivo
        copy /Y "!SRC!" "!DST!" >nul
        echo Restaurado: %%F
    ) else (
        REM Se for ml_enviados.json, apenas ignorar se nao existir
        if /i "%%F"=="interface\ml_enviados.json" (
            REM Ignorar se nao existir
        ) else (
            echo Arquivo nao encontrado no backup: %%F
        )
    )
    :CONTINUE_LOOP
)

echo Restauracao concluida.
pause