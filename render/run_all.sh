#!/bin/bash
# Render semua: 4 foto + 2 video, satu proses Blender per shot (RAM rendah). SAMPLES default 48.
BL="/c/Program Files/Blender Foundation/Blender 4.5/blender.exe"
cd "$(dirname "$0")"
for s in hero pad kit arena inside padinside spin match; do
  start=$(date +%s)
  "$BL" -b -P blender_kodykick.py -- --shot "$s" --samples ${SAMPLES:-48} 2>&1 | grep -E "RENDERED|Error|Traceback"
  echo "DONE $s $(( $(date +%s) - start ))s"
done
