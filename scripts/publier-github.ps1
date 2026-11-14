# Publie l'intégralité du site dans le dépôt GitHub existant.
# Prérequis : Git installé, compte GitHub autorisé à écrire dans le dépôt.
$ErrorActionPreference = "Stop"
$remote = "https://github.com/novaskilltech/institutdelexcellence.git"
$site = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git est introuvable. Installez Git for Windows : https://git-scm.com/downloads/win"
}
Push-Location $site
try {
    if (-not (Test-Path ".git")) {
        git init
        if ($LASTEXITCODE -ne 0) { throw "git init a échoué" }
    }
    git branch -M main
    git remote get-url origin *> $null
    if ($LASTEXITCODE -ne 0) { git remote add origin $remote }
    else { git remote set-url origin $remote }
    git add -A
    if ($LASTEXITCODE -ne 0) { throw "git add a échoué" }
    git -c user.name="Institut de l'Excellence" -c user.email="edition@users.noreply.github.com" commit -m "Publication initiale du catalogue et des cinq ouvrages gratuits"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Aucun changement à committer (ou commit impossible)." -ForegroundColor Yellow
    }
    git push -u origin main
    if ($LASTEXITCODE -ne 0) { throw "Échec du push. Connectez votre compte GitHub avec Git Credential Manager." }
    Write-Host "Site publié sur GitHub : https://github.com/novaskilltech/institutdelexcellence" -ForegroundColor Green
}
finally { Pop-Location }
