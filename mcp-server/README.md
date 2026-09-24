# halo-imagegen MCP server

A small [MCP](https://modelcontextprotocol.io) server (Python, `FastMCP`) that lets Claude
generate and edit images on a ComfyUI instance: here, a Ryzen AI Halo box reached through an
SSH tunnel. Images come back into the chat inline (JPEG), and full-resolution PNGs are saved
locally.

## Tools

| Tool | What it does |
|---|---|
| `halo_list_models()` | Lists the model registry: each model's kind, defaults, whether its files are installed in ComfyUI, and whether it supports reference images or LoRA training; plus any trained LoRAs |
| `halo_generate_image(prompt, model="", width=0, height=0, steps=0, cfg=0, seed=-1, reference_image="", lora="", lora_strength=1.0)` | Text-to-image. `0` means "use the model's tuned default". `reference_image` switches to the model's reference workflow (FLUX.2 klein by default) to put the same person/object in a new scene. `lora` applies a trained LoRA and prepends its trigger word |
| `halo_edit_image(instruction, image="", reference_image="", ...)` | Instruction edit with Qwen-Image-Edit 2511. `image` is a local path or a filename in `HALO_OUT_DIR`; blank = the most recent image, so edits chain |
| `halo_train_lora(name, images_folder, trigger="", base_model="z-image-turbo", ...)` | Uploads a folder of photos and queues ComfyUI's built-in `TrainLoraNode`; returns immediately |
| `halo_training_status(name="")` | Step progress (peeks ComfyUI's websocket), ETA, and the loss graph when done |
| `halo_cancel_training(name)` | Interrupts or dequeues a training job |

## How it talks to ComfyUI

1. **Build**: load the model's API-format workflow from `../workflows/`, substitute the
   `{{PROMPT}}`, `{{SEED}}`, `{{WIDTH}}` … placeholders, and drop the optional second
   `LoadImage` node if there's no second image.
2. **Upload** (reference/edit): `POST /upload/image` puts the local file into ComfyUI's input folder.
3. **Queue**: `POST /prompt` with the graph → `prompt_id`.
4. **Poll**: `GET /history/{prompt_id}` every 1.5 s until outputs appear (with MCP progress
   notifications so clients don't time out during slow model loads).
5. **Fetch**: `GET /view?filename=…` for the PNG, save it to `HALO_OUT_DIR`, return a JPEG
   copy to Claude plus a line with model, seed, size, steps, and timing.

`models.json` is re-read on every call, so you can change defaults or add a model without
restarting Claude.

## Environment

| Variable | Default | Meaning |
|---|---|---|
| `COMFY_URL` | `http://127.0.0.1:8188` | ComfyUI base URL (the local end of the SSH tunnel) |
| `HALO_MODELS` | `models.json` beside the script | Model registry |
| `HALO_OUT_DIR` | `~/halo-images` | Where PNGs are saved |

## Files

- `halo_imagegen.py`: the server
- `models.json`: model registry (paths point at `../workflows/`)
- `requirements.txt`: `mcp[cli]<2`, `pillow` (JPEG previews), `websockets` (training progress)

LoRA training writes to ComfyUI's `output/loras`; on the ComfyUI machine,
`models/loras/trained` must be a symlink to it so loaders can find the result:
`ln -s ../../output/loras ~/.local/share/ComfyUI/models/loras/trained`.
