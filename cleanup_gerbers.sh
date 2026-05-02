#!/bin/bash
# ==============================================================
# cleanup_gerbers.sh — EcoSynTech V6.3
# Removes duplicate Gerber files from repo root.
# Canonical Gerber set lives in /gerber/ subfolder only.
# Run from repo root: bash cleanup_gerbers.sh
# ==============================================================

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

echo "=== EcoSynTech PCB V6.3 — Gerber Cleanup ==="
echo "Working directory: $REPO_ROOT"
echo ""

# List of duplicate Gerber files at root that should only live in /gerber/
DUPS=(
  "EcoSynTech_V6_3-Cmts_User.gbr"
  "EcoSynTech_V6_3-Dwgs_User.gbr"
  "EcoSynTech_V6_3-Edge_Cuts.gbr"
  "EcoSynTech_V6_3-Plated.Txt"
  "EcoSynTech_V6_3.gbrjob"
  "EcoSynTech_V6_3_B.Cu.gbr"
  "EcoSynTech_V6_3_B.Mask.gbr"
  "EcoSynTech_V6_3_B.Paste.gbr"
  "EcoSynTech_V6_3_B.SilkS.gbr"
  "EcoSynTech_V6_3_F.Cu.gbr"
  "EcoSynTech_V6_3_F.Mask.gbr"
  "EcoSynTech_V6_3_F.Paste.gbr"
  "EcoSynTech_V6_3_F.SilkS.gbr"
)

echo "Checking canonical Gerber set in /gerber/ ..."
MISSING=0
for f in "${DUPS[@]}"; do
  if [ ! -f "gerber/$f" ]; then
    echo "  WARNING: gerber/$f not found — skipping removal of root copy"
    MISSING=1
  fi
done

if [ "$MISSING" -eq 1 ]; then
  echo ""
  echo "ERROR: Some files missing from /gerber/. Aborting cleanup."
  echo "Please copy canonical Gerbers to /gerber/ first."
  exit 1
fi

echo "All canonical files confirmed in /gerber/. Removing root duplicates..."
echo ""

for f in "${DUPS[@]}"; do
  if [ -f "$f" ]; then
    git rm "$f" && echo "  Removed: $f"
  else
    echo "  Already gone: $f"
  fi
done

echo ""
echo "=== Cleanup complete. Commit with: ==="
echo "  git commit -m 'chore: remove duplicate Gerber files from root (canonical in /gerber/)'"
echo "  git push"
echo ""
echo "After push, tag release with:"
echo "  git tag v6.3-release && git push --tags"
