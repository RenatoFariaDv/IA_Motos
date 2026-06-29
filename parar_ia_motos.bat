@echo off
chcp 65001 >nul

echo ============================
echo Parando robo...
echo ============================

REM Fecha apenas processos Python relacionados ao projeto IA_Motos
echo.
echo Fechando processos Python do projeto...
powershell -Command ^
    "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and ($_.CommandLine -match 'IA_Motos' -or $_.CommandLine -match '_internal' -or $_.CommandLine -match 'interface\\\\app.py' -or $_.CommandLine -match 'main.py') }; ^
    if ($procs) { $procs | ForEach-Object { Write-Host ('Matando PID ' + $_.ProcessId + ': ' + $_.CommandLine); Stop-Process -Id $_.ProcessId -Force } } ^
    else { Write-Host 'Nenhum processo Python do projeto encontrado.' }"

echo ============================
echo Limpando navegadores Playwright/Chromium do projeto...
echo ============================

REM Fecha apenas navegadores Playwright/Chromium relacionados ao projeto
powershell -Command ^
    "$procs = Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'chrome.exe' -or $_.Name -eq 'chromium.exe') -and ($_.CommandLine -match 'IA_Motos' -or $_.CommandLine -match '_internal' -or $_.CommandLine -match 'playwright' -or $_.CommandLine -match 'ml_profile_stealth') }; ^
    if ($procs) { $procs | ForEach-Object { Write-Host ('Matando PID ' + $_.ProcessId + ': ' + $_.CommandLine); Stop-Process -Id $_.ProcessId -Force } } ^
    else { Write-Host 'Nenhum navegador Playwright/Chromium do projeto encontrado.' }"

echo ============================
echo Parando sincronizacao AWS...
echo ============================

REM Fecha apenas PowerShell rodando sincronizar_aws.ps1
powershell -Command ^
    "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'powershell.exe' -and $_.CommandLine -match 'sincronizar_aws.ps1' }; ^
    if ($procs) { $procs | ForEach-Object { Write-Host ('Matando PID ' + $_.ProcessId + ': ' + $_.CommandLine); Stop-Process -Id $_.ProcessId -Force } } ^
    else { Write-Host 'Nenhum PowerShell de sincronizacao AWS encontrado.' }"

echo ============================
echo Parando painel do projeto...
echo ============================

REM Fecha apenas CMD rodando main.py ou interface\app.py
powershell -Command ^
    "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'cmd.exe' -and ($_.CommandLine -match 'main.py' -or $_.CommandLine -match 'interface\\\\app.py') }; ^
    if ($procs) { $procs | ForEach-Object { Write-Host ('Matando PID ' + $_.ProcessId + ': ' + $_.CommandLine); Stop-Process -Id $_.ProcessId -Force } } ^
    else { Write-Host 'Nenhum CMD do painel do projeto encontrado.' }"

echo ============================
echo Finalizado.
echo ============================
pause