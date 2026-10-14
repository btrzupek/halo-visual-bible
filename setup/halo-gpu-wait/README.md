# Wait for the GPU at boot (halo)

On a reboot, `halo-tts` started about 8 s after boot, before the Radeon 8060S was usable, and fell back to the
CPU; ComfyUI has also crashed with "No CUDA GPUs are available" when it started too early. These user-level
systemd drop-ins make both services wait until ROCm sees gfx1151 and the box has been up 45 s. No sudo; the
installed unit files are not touched (drop-ins only). Install from the Mac:

    cd ~/code/halo-visual-bible/setup/halo-gpu-wait
    ssh -o ClearAllForwardings=yes halo 'mkdir -p ~/.local/bin ~/.config/systemd/user/halo-tts.service.d ~/.config/systemd/user/comfyui@.service.d'
    scp -o ClearAllForwardings=yes wait-for-gpu.sh halo:.local/bin/
    scp -o ClearAllForwardings=yes halo-tts-wait-for-gpu.conf halo:.config/systemd/user/halo-tts.service.d/wait-for-gpu.conf
    scp -o ClearAllForwardings=yes comfyui-wait-for-gpu.conf halo:.config/systemd/user/comfyui@.service.d/wait-for-gpu.conf
    ssh -o ClearAllForwardings=yes halo 'systemctl --user daemon-reload'

It takes effect at the next boot (running services are not restarted). To undo, delete the two `.conf` files and
run `systemctl --user daemon-reload`.
