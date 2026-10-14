# Wait for the GPU at boot (halo)

On a reboot, `halo-tts` started about 8 s after boot, before the Radeon 8060S was usable, and fell back to the
CPU; ComfyUI has also crashed with "No CUDA GPUs are available" when it started too early. These user-level
systemd drop-ins make both services wait until ROCm sees gfx1151 and the box has been up 45 s. No sudo; the
installed unit files are not touched (drop-ins only). Install from the Mac, all over ssh:

    bash ~/code/halo-visual-bible/setup/halo-gpu-wait/install.sh

It copies the files, reloads systemd and checks that both services picked up the wait. Nothing running is
restarted; it takes effect at the next boot. Undo with `install.sh --undo`.
