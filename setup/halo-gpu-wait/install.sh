#!/usr/bin/env bash
# Run on the Mac: installs the wait-for-GPU boot fix on halo over ssh, then checks it.
#   bash ~/code/halo-visual-bible/setup/halo-gpu-wait/install.sh
# Nothing running is restarted; it takes effect at the next boot. Undo: bash install.sh --undo
set -euo pipefail
HOST="${HALO_HOST:-halo}"
SSH=(ssh -o ClearAllForwardings=yes -o ConnectTimeout=10 "$HOST")
SCP=(scp -q -o ClearAllForwardings=yes -o ConnectTimeout=10)
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "${1:-}" = "--undo" ]; then
  "${SSH[@]}" 'rm -f ~/.config/systemd/user/halo-tts.service.d/wait-for-gpu.conf ~/.config/systemd/user/comfyui@.service.d/wait-for-gpu.conf ~/.local/bin/wait-for-gpu.sh && systemctl --user daemon-reload && echo "removed; back to the old start-up at the next boot"'
  exit 0
fi

echo "1/4 making folders on $HOST"
"${SSH[@]}" 'mkdir -p ~/.local/bin ~/.config/systemd/user/halo-tts.service.d ~/.config/systemd/user/comfyui@.service.d'

echo "2/4 copying the script and the two drop-ins"
"${SCP[@]}" "$DIR/wait-for-gpu.sh" "$HOST:.local/bin/wait-for-gpu.sh"
"${SCP[@]}" "$DIR/halo-tts-wait-for-gpu.conf" "$HOST:.config/systemd/user/halo-tts.service.d/wait-for-gpu.conf"
"${SCP[@]}" "$DIR/comfyui-wait-for-gpu.conf" "$HOST:.config/systemd/user/comfyui@.service.d/wait-for-gpu.conf"

echo "3/4 reloading systemd (user)"
"${SSH[@]}" 'chmod +x ~/.local/bin/wait-for-gpu.sh && systemctl --user daemon-reload'

echo "4/4 checking"
"${SSH[@]}" '
  ok=1
  ~/.local/bin/wait-for-gpu.sh && echo "  wait-for-gpu.sh: GPU seen now (gfx1151)" || { echo "  wait-for-gpu.sh: FAILED"; ok=0; }
  for u in halo-tts comfyui@8188; do
    if systemctl --user show "$u" -p ExecStartPre --no-pager | grep -q wait-for-gpu; then
      echo "  $u: will wait for the GPU at boot ($(systemctl --user is-active "$u") now)"
    else
      echo "  $u: drop-in NOT picked up"; ok=0
    fi
  done
  [ $ok = 1 ] && echo "done: takes effect at the next boot" || exit 1'
