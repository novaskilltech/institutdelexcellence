# Installe une tâche planifiée Windows (toutes les 5 min) pour publier nouveaux-livres/a-publier/.
$ErrorActionPreference = "Stop"
$taskName = "InstitutExcellence-AutoPublish"
$scriptPath = (Resolve-Path (Join-Path $PSScriptRoot "sync-nouveaux-livres.ps1")).Path

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Surveille nouveaux-livres/a-publier et pousse vers GitHub" -Force | Out-Null
Write-Host "Tâche planifiée '$taskName' installée (exécution toutes les 5 minutes, même éditeur fermé)." -ForegroundColor Green
