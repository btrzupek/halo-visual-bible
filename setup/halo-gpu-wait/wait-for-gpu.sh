#!/bin/sh
# Used by halo-tts and comfyui@ (ExecStartPre): at boot the containers can start before the GPU is usable and then
# fall back to the CPU (halo-tts) or crash with "No CUDA GPUs are available" (ComfyUI). Wait until ROCm sees the
# Radeon 8060S (gfx1151) and the box has been up at least 45 s, then 5 s more. Gives up after 3 minutes.
i=0
while [ $i -lt 90 ]; do
  up=$(cut -d. -f1 /proc/uptime)
  if [ "$up" -ge 45 ] && /usr/bin/rocminfo 2>/dev/null | grep -q gfx1151; then sleep 5; exit 0; fi
  i=$((i + 1)); sleep 2
done
echo "wait-for-gpu: GPU not ready after 3 minutes" >&2
exit 1
