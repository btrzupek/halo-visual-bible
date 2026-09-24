# ComfyUI workflows (API format)

Each file is a ComfyUI graph in API format ("Export (API)"), adapted from ComfyUI's bundled
official templates, with `{{PLACEHOLDER}}` strings that the MCP server and the benchmark script
fill in. Numeric placeholders (`"{{SEED}}"`, `"{{WIDTH}}"`, `"{{HEIGHT}}"`, `"{{STEPS}}"`,
`"{{CFG}}"`) are replaced including their quotes, so the result is valid JSON numbers.

| File | Model | What it does | Defaults |
|---|---|---|---|
| `flux2-klein.json` | FLUX.2 [klein] 4B (distilled, BF16) + Qwen3-4B text encoder + FLUX.2 VAE | Text-to-image via `SamplerCustomAdvanced` + `Flux2Scheduler`, negative = `ConditioningZeroOut` | 1024², 4 steps, cfg 1 (the book used 1344×768 and 896×1152) |
| `flux2-klein-ref.json` | same | Reference image → `ImageScaleToTotalPixels` (1 MP) → `VAEEncode` → `ReferenceLatent` on both conditionings; output size is independent of the reference | 4 steps, cfg 1 |
| `qwen-image-edit.json` | Qwen-Image-Edit 2511 (FP8 mixed) + Qwen2.5-VL 7B + Lightning 4-step LoRA | Instruction edit: `TextEncodeQwenImageEditPlus` with image 1 (and optional image 2), `CFGNorm`, `ModelSamplingAuraFlow` shift 3.1, latent from the input image | 4 steps, cfg 1, ~1 MP |
| `qwen-image-ref.json` | same | Reference-guided *new* image with the edit model (empty latent of the requested size) | 4 steps, cfg 1 |
| `qwen-image.json` | Qwen-Image 2512 (FP8) + Lightning 4-step LoRA | Best text rendering in images | 1328², 4 steps, cfg 1 |
| `z-image-turbo.json` | Z-Image Turbo (BF16) + Qwen3-4B + FLUX.1 AE | Fast photoreal | 1024², 8 steps, cfg 1, `res_multistep` |

Model files (all from Apache-2.0-tagged Hugging Face repos):

| Folder | File | Repo |
|---|---|---|
| diffusion_models | `flux-2-klein-4b.safetensors` | Comfy-Org/flux2-klein |
| text_encoders | `qwen_3_4b.safetensors` | Comfy-Org/flux2-klein (identical to Comfy-Org/z_image_turbo's) |
| vae | `flux2-vae.safetensors` | Comfy-Org/flux2-klein |
| diffusion_models | `qwen_image_edit_2511_fp8mixed.safetensors` | Comfy-Org/Qwen-Image-Edit_ComfyUI |
| diffusion_models | `qwen_image_2512_fp8_e4m3fn.safetensors` | Comfy-Org/Qwen-Image_ComfyUI |
| text_encoders | `qwen_2.5_vl_7b_fp8_scaled.safetensors` | Comfy-Org/Qwen-Image_ComfyUI |
| vae | `qwen_image_vae.safetensors` | Comfy-Org/Qwen-Image_ComfyUI |
| loras | `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` | lightx2v/Qwen-Image-Edit-2511-Lightning |
| loras | `Qwen-Image-2512-Lightning-4steps-V1.0-bf16.safetensors` | lightx2v/Qwen-Image-2512-Lightning |
| diffusion_models | `z_image_turbo_bf16.safetensors` | Comfy-Org/z_image_turbo |
| vae | `ae.safetensors` | Comfy-Org/z_image_turbo |

The negative prompt has no effect in these graphs at cfg 1.0, which is where the distilled and
Lightning models are meant to run.
