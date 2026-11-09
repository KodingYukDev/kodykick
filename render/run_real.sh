#!/bin/bash
# Render realistis semua (Cycles CPU). Foto 100% 64 sampel, video 75% 32 sampel. Satu proses per shot.
BL="/c/Program Files/Blender Foundation/Blender 4.5/blender.exe"
cd "$(dirname "$0")"
for s in hero inside arena; do
  st=$(date +%s); "$BL" -b -P blender_real.py -- --shot "$s" --samples ${SAMPLES:-64} 2>&1 | grep -E "RENDERED|Error|Traceback"; echo "DONE $s $(( $(date +%s)-st ))s"
done
for s in breakdown match; do
  st=$(date +%s); "$BL" -b -P blender_real.py -- --shot "$s" --samples ${VSAMPLES:-32} --pct ${VPCT:-75} 2>&1 | grep -E "RENDERED|Error|Traceback"; echo "DONE $s $(( $(date +%s)-st ))s"
done
