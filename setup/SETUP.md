# Setup: Claude on a Mac → ComfyUI on a Ryzen AI Halo box

Four pieces: an SSH key, a launchd tunnel, a Python venv for the MCP server, and a Claude
Desktop registration. Placeholders: `<halo-host>` (your ssh alias), `<halo-ip-or-dns>`,
`<user>` (your login on each machine), `<key-file>`.

## 0. On the halo box

ComfyUI must be running and listening on `127.0.0.1:8188`. On the AMD Ryzen AI Halo developer
image it is preinstalled as a socket-activated rootless Podman service
(`systemctl --user status comfyui@8188.socket`), so the first request starts it. It needs a
logged-in desktop session (the unit requires `graphical-session.target`).

Install the models you want (see `../workflows/README.md` for the file list) under
`~/.local/share/ComfyUI/models/{diffusion_models,text_encoders,vae,loras}`.

## 1. SSH key + Keychain (Mac)

```bash
ssh-keygen -t ed25519 -f ~/.ssh/<key-file> -C "mac-to-halo"
ssh-copy-id -i ~/.ssh/<key-file>.pub <user>@<halo-ip-or-dns>
ssh-add --apple-use-keychain ~/.ssh/<key-file>
```

Append `ssh_config.example` to `~/.ssh/config` and fill in the placeholders. `UseKeychain yes`
lets launchd use the key without a prompt. Test non-interactively:

```bash
ssh -o BatchMode=yes halo-tunnel true && echo ok
```

## 2. The tunnel (Mac)

```bash
sed "s/__USER__/$(whoami)/" com.halo.comfy-tunnel.plist > ~/Library/LaunchAgents/com.halo.comfy-tunnel.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.halo.comfy-tunnel.plist
curl -s http://127.0.0.1:8188/system_stats | head -c 200
```

Why socket activation instead of `ssh -N -L … ` with `KeepAlive`: on recent macOS, launchd
defers "speculative" and KeepAlive respawns of background agents, so a dropped long-lived tunnel
may not come back until you `launchctl kickstart` it. With `Sockets` + `inetdCompatibility`,
launchd itself owns 127.0.0.1:8188 and runs one `ssh -W 127.0.0.1:8188 halo-tunnel` per TCP
connection; `ControlMaster` in the ssh config keeps that at ~50 ms per request. Nothing is
exposed beyond localhost on either machine.

Restart / debug:

```bash
launchctl kickstart -k gui/$(id -u)/com.halo.comfy-tunnel
ssh -O exit halo-tunnel          # drop a stale shared connection
tail ~/Library/Logs/halo-comfy-tunnel.log
```

## 3. The MCP server venv (Mac)

```bash
cd mcp-server
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
COMFY_URL=http://127.0.0.1:8188 .venv/bin/python -c "import halo_imagegen as h; print(h.halo_list_models())"
```

`mcp` is pinned below 2.0 because the server uses the v1 `FastMCP` API (renamed in 2.x).

## 4. Register with Claude Desktop

Merge `claude_desktop_config.snippet.json` into
`~/Library/Application Support/Claude/claude_desktop_config.json` (back it up first; keep your
other `mcpServers`), using absolute paths. Quit Claude Desktop with ⌘Q and reopen it.
Claude Code in the desktop app picks the server up from the same file.

Try: *"What image models are on halo?"* then *"Generate an image of a fishing boat on the Sea of
Galilee at dawn."*

## 5. Narration (optional): Kokoro TTS and the halo-tts MCP server

The `/read/<book>` pages can play a narrator generated on halo. The speech server is a small
Podman container; install steps, and what was and wasn't verified on gfx1151, are in
[`../tts/README.md`](../tts/README.md). On the Mac, `com.halo.tts-tunnel.plist` exposes it at
`127.0.0.1:8880` exactly as the ComfyUI tunnel does for 8188.

Register the MCP server next to `halo-imagegen` (any venv with `mcp[cli]<2` works):

```json
"halo-tts": {
  "command": "/Users/<user>/halo-visual-bible/mcp-server/.venv/bin/python",
  "args": ["/Users/<user>/halo-visual-bible/mcp-server/halo_tts.py"],
  "env": { "TTS_URL": "http://127.0.0.1:8880", "HALO_AUDIO_DIR": "/Users/<user>/halo-audio" }
}
```

Try: *"Is the halo speech server on the GPU?"* then *"Read John 11:35 in bm_george and bm_lewis."*
