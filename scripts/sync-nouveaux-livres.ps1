# Synchronise automatiquement nouveaux-livres/a-publier/ vers GitHub (zéro dépendance hors Git).
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$inbox = Join-Path $root "nouveaux-livres\a-publier"
$logDir = Join-Path $root "nouveaux-livres\logs"
$logFile = Join-Path $logDir "sync.log"
$lockFile = Join-Path $root "nouveaux-livres\.lock"

New-Item -ItemType Directory -Force -Path $inbox, $logDir | Out-Null

function Write-Log([string]$msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $logFile -Value $line -Encoding UTF8
}

if (Test-Path $lockFile) {
    $age = (Get-Date) - (Get-Item $lockFile).LastWriteTime
    if ($age.TotalMinutes -lt 15) {
        exit 0
    }
    Remove-Item $lockFile -Force
}

$files = Get-ChildItem -Path $inbox -File | Where-Object { $_.Name -ne ".gitkeep" }
if (-not $files) {
    exit 0
}

Set-Content -Path $lockFile -Value $PID -Encoding ASCII
Push-Location $root
try {
    # Vérifie que la copie des fichiers est terminée (taille stable sur 2 secondes).
    $sizesBefore = @{}
    foreach ($f in $files) { $sizesBefore[$f.FullName] = $f.Length }
    Start-Sleep -Seconds 2
    foreach ($f in $files) {
        $f.Refresh()
        if ($f.Length -ne $sizesBefore[$f.FullName] -or $f.Length -eq 0) {
            Write-Log "Fichier en cours d'écriture ou vide ignoré : $($f.Name)"
            exit 0
        }
    }

    $prevErr = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    git pull --rebase --autostash origin main 2>&1 | Out-Null
    $pullExit = $LASTEXITCODE
    $ErrorActionPreference = $prevErr
    if ($pullExit -ne 0) {
        Write-Log "ERREUR: git pull --rebase a échoué. Résolution manuelle requise."
        exit 1
    }

    git add "nouveaux-livres/a-publier"
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        exit 0
    }

    $names = ($files | ForEach-Object { $_.Name }) -join ", "
    $prevErr = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    git commit -m "Dépôt automatique : $names" 2>&1 | Out-Null
    $commitExit = $LASTEXITCODE
    $ErrorActionPreference = $prevErr
    if ($commitExit -ne 0) {
        Write-Log "ERREUR: git commit a échoué."
        exit 1
    }

    $prevErr = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    git push origin main 2>&1 | Out-Null
    $pushExit = $LASTEXITCODE
    $ErrorActionPreference = $prevErr
    if ($pushExit -ne 0) {
        Write-Log "ERREUR: git push a échoué."
        exit 1
    }

    Write-Log "OK: envoyé vers GitHub ($names). GitHub Actions va générer et publier."
}
finally {
    Pop-Location
    if (Test-Path $lockFile) { Remove-Item $lockFile -Force }
}
