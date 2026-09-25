@echo off
setlocal
set "CONSOLE_DIR=%~dp0"
powershell.exe -NoProfile -Command "$script = Join-Path $env:CONSOLE_DIR 'server.py'; Start-Process -FilePath 'python.exe' -ArgumentList @('-u', ('"' + $script + '"')) -WindowStyle Hidden"
if errorlevel 1 exit /b 1
rem Edge is rarely on PATH; look in its install folders (found at review, 2026-09-24).
powershell.exe -NoProfile -Command "Start-Sleep -Milliseconds 700; $edge = @((Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'), (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe')) | Where-Object { Test-Path $_ } | Select-Object -First 1; if ($edge) { Start-Process -FilePath $edge -ArgumentList '--app=http://127.0.0.1:8098' } else { Start-Process 'http://127.0.0.1:8098' }"
endlocal
