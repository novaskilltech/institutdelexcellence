#!/usr/bin/env python3
"""Ingère les nouveaux PDF validés depuis nouveaux-livres/a-publier/ vers le catalogue.

Conçu pour s'exécuter dans GitHub Actions (ou localement si pymupdf/Pillow sont installés)
sans jamais modifier le site public en cas de PDF corrompu.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INBOX_DIR = ROOT / "nouveaux-livres" / "a-publier"
ERROR_DIR = ROOT / "nouveaux-livres" / "erreurs"
BACKUP_DIR = ROOT / "backups"
PDFS_DIR = ROOT / "pdfs"
COVERS_DIR = ROOT / "assets" / "img" / "couvertures"
CATALOG_PATH = ROOT / "livres.json"
LOG_PATH = ROOT / "publications.log.json"

CATEGORIES = {
    "histoires": "Histoire & biographies",
    "priere": "Prière & spiritualité",
    "education": "Éducation",
    "coran": "Sciences du Coran",
    "fiqh": "Jurisprudence",
    "payants": "Livres payants",
}
MONTHS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def slugify(value: str) -> str:
    """Convertit un titre ou nom de fichier en slug URL sûr."""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "ouvrage"


def current_month_fr() -> str:
    """Retourne le mois et l'année courants en français."""
    now = datetime.now(timezone.utc)
    return f"{MONTHS_FR[now.month - 1]} {now.year}"


def append_log(entry: dict) -> None:
    """Ajoute une entrée horodatée au journal des publications."""
    logs = []
    if LOG_PATH.is_file():
        try:
            logs = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logs = []
    logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), **entry})
    LOG_PATH.write_text(json.dumps(logs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def inspect_pdf(pdf_path: Path) -> tuple[int, dict]:
    """Vérifie l'intégrité d'un PDF et lit ses métadonnées existantes sans rien inventer."""
    import fitz

    if pdf_path.stat().st_size == 0:
        raise ValueError("Fichier PDF vide (0 octet).")
    with fitz.open(pdf_path) as doc:
        if doc.is_encrypted:
            raise ValueError("Le PDF est protégé par mot de passe et ne peut pas être traité.")
        page_count = len(doc)
        if page_count <= 0:
            raise ValueError("Le PDF ne contient aucune page.")
        meta = doc.metadata or {}
    return page_count, {k: (v or "").strip() for k, v in meta.items()}


def save_custom_cover(stem: str, slug: str) -> bool:
    """Convertit une couverture fournie (.webp/.png/.jpg) au format WebP si présente."""
    from PIL import Image

    for ext in (".webp", ".png", ".jpg", ".jpeg"):
        candidate = INBOX_DIR / f"{stem}{ext}"
        if candidate.is_file():
            COVERS_DIR.mkdir(parents=True, exist_ok=True)
            dest = COVERS_DIR / f"{slug}.webp"
            with Image.open(candidate) as im:
                im.convert("RGB").save(dest, format="WEBP", quality=88, method=6)
            candidate.unlink()
            return True
    return False


def backup_existing(slug: str) -> None:
    """Sauvegarde le PDF et le catalogue existants avant toute mise à jour d'un ouvrage."""
    existing_pdf = PDFS_DIR / f"{slug}.pdf"
    if not existing_pdf.is_file():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"{stamp}_{slug}"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(existing_pdf, target / f"{slug}.pdf")
    if CATALOG_PATH.is_file():
        shutil.copy2(CATALOG_PATH, target / "livres.json")


def build_entry(pdf_path: Path, page_count: int, pdf_meta: dict, sidecar: dict) -> dict:
    """Construit l'entrée catalogue à partir des données vérifiées du sidecar et du PDF."""
    raw_slug = sidecar.get("slug") or pdf_path.stem
    slug = slugify(raw_slug)
    title = (sidecar.get("titre") or pdf_meta.get("title") or pdf_path.stem.replace("-", " ").replace("_", " ").title()).strip()
    cat_id = sidecar.get("categorie_id", "education")
    if cat_id not in CATEGORIES:
        cat_id = "education"

    entry = {
        "slug": slug,
        "titre": title,
        "accroche": (sidecar.get("accroche") or f"Ouvrage de {page_count} pages au format PDF").strip(),
        "description": (sidecar.get("description") or f"{title} — ouvrage de {page_count} pages proposé en lecture et téléchargement gratuits par l’Institut de l’Excellence.").strip(),
        "collection": (sidecar.get("collection") or "Éditions de l’Institut").strip(),
        "categorie": (sidecar.get("categorie") or CATEGORIES[cat_id]).strip(),
        "categorie_id": cat_id,
        "pages": page_count,
        "date": (sidecar.get("date") or current_month_fr()).strip(),
        "pdf": f"pdfs/{slug}.pdf",
    }
    author = (sidecar.get("auteur") or pdf_meta.get("author") or "").strip()
    if author:
        entry["auteur"] = author
    if sidecar.get("langue"):
        entry["langue"] = sidecar["langue"].strip()
    return entry


def process_inbox() -> int:
    """Traite tous les PDF présents dans nouveaux-livres/a-publier/."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ERROR_DIR.mkdir(parents=True, exist_ok=True)
    PDFS_DIR.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(INBOX_DIR.glob("*.pdf"))
    if not pdfs:
        print("Aucun nouveau PDF dans nouveaux-livres/a-publier/.")
        return 0

    books = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    by_slug = {b["slug"]: i for i, b in enumerate(books)}
    had_error = False

    for pdf_path in pdfs:
        meta_path = INBOX_DIR / f"{pdf_path.stem}.meta.json"
        alt_meta_path = INBOX_DIR / f"{pdf_path.stem}.json"
        sidecar_path = meta_path if meta_path.is_file() else alt_meta_path
        sidecar = {}
        if sidecar_path.is_file():
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))

        try:
            page_count, pdf_meta = inspect_pdf(pdf_path)
        except Exception as exc:
            had_error = True
            ERROR_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(pdf_path), str(ERROR_DIR / pdf_path.name))
            (ERROR_DIR / f"{pdf_path.stem}.error.txt").write_text(str(exc) + "\n", encoding="utf-8")
            append_log({"action": "error", "file": pdf_path.name, "error": str(exc)})
            print(f"[ERREUR] {pdf_path.name} rejeté : {exc}", file=sys.stderr)
            continue

        entry = build_entry(pdf_path, page_count, pdf_meta, sidecar)
        slug = entry["slug"]
        is_update = slug in by_slug

        if is_update:
            backup_existing(slug)
            books[by_slug[slug]] = entry
        else:
            by_slug[slug] = len(books)
            books.append(entry)

        shutil.move(str(pdf_path), str(PDFS_DIR / f"{slug}.pdf"))
        if sidecar_path.is_file():
            sidecar_path.unlink()
        save_custom_cover(pdf_path.stem, slug)

        # Sauvegarde immédiate du catalogue pour préserver la cohérence en cas d'erreur sur le fichier suivant.
        CATALOG_PATH.write_text(json.dumps(books, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        append_log({"action": "updated" if is_update else "added", "slug": slug, "titre": entry["titre"], "pages": page_count})
        print(f"[OK] {'Mis à jour' if is_update else 'Ajouté'} : {entry['titre']} ({slug}, {page_count} pages)")

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(process_inbox())
