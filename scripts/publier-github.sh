#!/bin/sh
# Prérequis : Git et droits GitHub pour novaskilltech/institutdelexcellence
set -eu
cd "$(dirname "$0")/.."
if [ ! -d .git ]; then git init; fi
git branch -M main
git remote get-url origin >/dev/null 2>&1 && git remote set-url origin https://github.com/novaskilltech/institutdelexcellence.git || git remote add origin https://github.com/novaskilltech/institutdelexcellence.git
git add -A
git -c user.name="Institut de l'Excellence" -c user.email="edition@users.noreply.github.com" commit -m "Publication initiale du catalogue et des cinq ouvrages gratuits" || true
git push -u origin main
printf 'Dépôt : https://github.com/novaskilltech/institutdelexcellence\n'
