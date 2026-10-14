#!/usr/bin/env python3
"""Image-to-video with LTX-2.5 on halo's ComfyUI (through the http://127.0.0.1:8188 tunnel).

The graph is the official "LTX-2.5: Image to Video" template (workflows/_templates/video_ltx2_5_i2v.json),
flattened to API format without the optional prompt enhancer: a half-resolution pass, the x2 latent
upscaler, a short refine pass, tiled decode. LTX-2.5 also generates audio; the player keeps clips muted.

  python3 scripts/ltx_i2v.py --image ~/halo-images/halo_klein_00620_.png --prompt "..." --out clip.mp4 \
      [--seconds 5] [--fps 24] [--width 1280] [--height 720] [--seed 42] [--draft] [--last-frame END.png]

--draft is the preview preset: first pass 480x272 and the input image scaled to 1152x648 (output ~960x544).
Without it, the first pass is half the output size and the input image is 1536 wide (output 1280x704).

Prints the output path, the wall-clock time and the ComfyUI execution time. --last-frame selects the
first-and-last-frame variant: one pass with both keyframes as guides (frame 0 and the last frame).
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, uuid

COMFY = os.environ.get('COMFY_URL', 'http://127.0.0.1:8188')
NEG = ('text, letters, legible writing, captions, subtitles, watermark, logo, modern objects, cartoon, '
       'illustration, painting, deformed hands, extra fingers, duplicate faces, morphing, flicker')


def upload(path):
    boundary = uuid.uuid4().hex
    name = os.path.basename(path)
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{name}"\r\n'
            f'Content-Type: image/png\r\n\r\n').encode() + open(path, 'rb').read() + f'\r\n--{boundary}--\r\n'.encode()
    req = urllib.request.Request(f'{COMFY}/upload/image', body, {'Content-Type': f'multipart/form-data; boundary={boundary}'})
    return json.load(urllib.request.urlopen(req))['name']


DRAFT = {'first': (480, 272), 'scale': (1152, 648)}   # preview preset (Brian, 2026-10-13): smaller first pass and input image


def graph(image, prompt, negative, seconds, fps, width, height, seed, draft=False):
    length = int(seconds * fps) + 1
    if draft:
        (fw, fh), (sw, sh) = DRAFT['first'], DRAFT['scale']
    else:
        fw, fh, sw, sh = width // 2, height // 2, 1536, round(1536 * height / width / 32) * 32
    g = {
        'img': ('LoadImage', {'image': image}),
        'scale': ('ImageScale', {'image': ['img', 0], 'upscale_method': 'lanczos', 'width': sw, 'height': sh, 'crop': 'center'}),
        'pre': ('LTXVPreprocess', {'image': ['scale', 0], 'img_compression': 18}),
        'unet': ('UNETLoader', {'unet_name': 'ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors',
                                'weight_dtype': 'default'}),
        'vae': ('VAELoader', {'vae_name': 'ltx-2.5-video-vae-bf16.safetensors'}),
        'avae': ('VAELoader', {'vae_name': 'ltx-2.5-audio-vae-bf16.safetensors'}),
        'clip': ('CLIPLoader', {'clip_name': 'gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors',
                                'type': 'ltxv', 'device': 'default'}),
        'up': ('LatentUpscaleModelLoader', {'model_name': 'ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors'}),
        'pos': ('CLIPTextEncode', {'clip': ['clip', 0], 'text': prompt}),
        'neg': ('CLIPTextEncode', {'clip': ['clip', 0], 'text': negative}),
        'cond': ('LTXVConditioning', {'positive': ['pos', 0], 'negative': ['neg', 0], 'frame_rate': float(fps)}),
        # pass 1, half resolution
        'empty': ('EmptyLTXVLatentVideo', {'width': fw, 'height': fh, 'length': length, 'batch_size': 1}),
        'i2v1': ('LTXVImgToVideoInplace', {'vae': ['vae', 0], 'image': ['pre', 0], 'latent': ['empty', 0],
                                          'strength': 0.7, 'bypass': False}),
        'aud': ('LTXVEmptyLatentAudio', {'frames_number': length, 'frame_rate': fps, 'batch_size': 1, 'audio_vae': ['avae', 0]}),
        'av1': ('LTXVConcatAVLatent', {'video_latent': ['i2v1', 0], 'audio_latent': ['aud', 0]}),
        'g1': ('LTXVDualCFGGuider', {'model': ['unet', 0], 'positive': ['cond', 0], 'negative': ['cond', 1],
                                     'video_cfg': 1.0, 'audio_cfg': 1.0}),
        'n1': ('RandomNoise', {'noise_seed': seed}),
        's1': ('KSamplerSelect', {'sampler_name': 'euler_ancestral'}),
        'sig1': ('ManualSigmas', {'sigmas': '1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0'}),
        'run1': ('SamplerCustomAdvanced', {'noise': ['n1', 0], 'guider': ['g1', 0], 'sampler': ['s1', 0],
                                           'sigmas': ['sig1', 0], 'latent_image': ['av1', 0]}),
        'sep1': ('LTXVSeparateAVLatent', {'av_latent': ['run1', 0]}),
        # x2 latent upscale, then refine
        'ups': ('LTXVLatentUpsampler', {'samples': ['sep1', 0], 'upscale_model': ['up', 0], 'vae': ['vae', 0]}),
        'i2v2': ('LTXVImgToVideoInplace', {'vae': ['vae', 0], 'image': ['pre', 0], 'latent': ['ups', 0],
                                          'strength': 1.0, 'bypass': False}),
        'av2': ('LTXVConcatAVLatent', {'video_latent': ['i2v2', 0], 'audio_latent': ['sep1', 1]}),
        'g2': ('LTXVDualCFGGuider', {'model': ['unet', 0], 'positive': ['cond', 0], 'negative': ['cond', 1],
                                     'video_cfg': 1.0, 'audio_cfg': 1.0}),
        'n2': ('RandomNoise', {'noise_seed': 42}),
        's2': ('KSamplerSelect', {'sampler_name': 'euler_ancestral'}),
        'sig2': ('ManualSigmas', {'sigmas': '0.85, 0.7250, 0.4219, 0.0'}),
        'run2': ('SamplerCustomAdvanced', {'noise': ['n2', 0], 'guider': ['g2', 0], 'sampler': ['s2', 0],
                                           'sigmas': ['sig2', 0], 'latent_image': ['av2', 0]}),
        'sep2': ('LTXVSeparateAVLatent', {'av_latent': ['run2', 0]}),
        'dec': ('VAEDecodeTiled', {'samples': ['sep2', 0], 'vae': ['vae', 0], 'tile_size': 512, 'overlap': 64,
                                   'temporal_size': 64, 'temporal_overlap': 16}),
        'adec': ('LTXVAudioVAEDecode', {'samples': ['sep2', 1], 'audio_vae': ['avae', 0]}),
        'vid': ('CreateVideo', {'images': ['dec', 0], 'audio': ['adec', 0], 'fps': float(fps)}),
        'save': ('SaveVideo', {'video': ['vid', 0], 'filename_prefix': 'video/vb_ltx25_i2v', 'format': 'auto', 'codec': 'auto'}),
    }
    return {k: {'class_type': c, 'inputs': i} for k, (c, i) in g.items()}


def graph_flf(first, last, prompt, negative, seconds, fps, width, height, seed, draft=False, strength=0.7):
    """First and last frame (the official "LTX-2.5: FLF2V" template, flattened): both keyframes are guides on one latent
    (frame 0 and frame -1), one sampling pass at the output size, then the guides are cropped off before decoding."""
    length = int(seconds * fps) + 1
    w, h = (960, 544) if draft else (width, height)
    g = {
        'img1': ('LoadImage', {'image': first}), 'img2': ('LoadImage', {'image': last}),
        's1': ('ImageScale', {'image': ['img1', 0], 'upscale_method': 'lanczos', 'width': w, 'height': h, 'crop': 'center'}),
        's2': ('ImageScale', {'image': ['img2', 0], 'upscale_method': 'lanczos', 'width': w, 'height': h, 'crop': 'center'}),
        'p1': ('LTXVPreprocess', {'image': ['s1', 0], 'img_compression': 18}),
        'p2': ('LTXVPreprocess', {'image': ['s2', 0], 'img_compression': 18}),
        'unet': ('UNETLoader', {'unet_name': 'ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors', 'weight_dtype': 'default'}),
        'vae': ('VAELoader', {'vae_name': 'ltx-2.5-video-vae-bf16.safetensors'}),
        'avae': ('VAELoader', {'vae_name': 'ltx-2.5-audio-vae-bf16.safetensors'}),
        'clip': ('CLIPLoader', {'clip_name': 'gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors', 'type': 'ltxv', 'device': 'default'}),
        'pos': ('CLIPTextEncode', {'clip': ['clip', 0], 'text': prompt}),
        'neg': ('CLIPTextEncode', {'clip': ['clip', 0], 'text': negative}),
        'cond': ('LTXVConditioning', {'positive': ['pos', 0], 'negative': ['neg', 0], 'frame_rate': float(fps)}),
        'empty': ('EmptyLTXVLatentVideo', {'width': w, 'height': h, 'length': length, 'batch_size': 1}),
        'g1': ('LTXVAddGuide', {'positive': ['cond', 0], 'negative': ['cond', 1], 'vae': ['vae', 0], 'latent': ['empty', 0],
                                'image': ['p1', 0], 'frame_idx': 0, 'strength': strength}),
        'g2': ('LTXVAddGuide', {'positive': ['g1', 0], 'negative': ['g1', 1], 'vae': ['vae', 0], 'latent': ['g1', 2],
                                'image': ['p2', 0], 'frame_idx': -1, 'strength': strength}),
        'aud': ('LTXVEmptyLatentAudio', {'frames_number': length, 'frame_rate': fps, 'batch_size': 1, 'audio_vae': ['avae', 0]}),
        'av': ('LTXVConcatAVLatent', {'video_latent': ['g2', 2], 'audio_latent': ['aud', 0]}),
        'gd': ('LTXVDualCFGGuider', {'model': ['unet', 0], 'positive': ['g2', 0], 'negative': ['g2', 1], 'video_cfg': 1.0, 'audio_cfg': 1.0}),
        'n': ('RandomNoise', {'noise_seed': seed}),
        'smp': ('SamplerEulerAncestral', {'eta': 1.0, 's_noise': 1.0}),
        'sig': ('ManualSigmas', {'sigmas': '1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0'}),
        'run': ('SamplerCustomAdvanced', {'noise': ['n', 0], 'guider': ['gd', 0], 'sampler': ['smp', 0], 'sigmas': ['sig', 0], 'latent_image': ['av', 0]}),
        'sep': ('LTXVSeparateAVLatent', {'av_latent': ['run', 1]}),
        'crop': ('LTXVCropGuides', {'positive': ['g2', 0], 'negative': ['g2', 1], 'latent': ['sep', 0]}),
        'dec': ('VAEDecodeTiled', {'samples': ['crop', 2], 'vae': ['vae', 0], 'tile_size': 512, 'overlap': 64, 'temporal_size': 64, 'temporal_overlap': 16}),
        'adec': ('LTXVAudioVAEDecode', {'samples': ['sep', 1], 'audio_vae': ['avae', 0]}),
        'vid': ('CreateVideo', {'images': ['dec', 0], 'audio': ['adec', 0], 'fps': float(fps)}),
        'save': ('SaveVideo', {'video': ['vid', 0], 'filename_prefix': 'video/vb_ltx25_flf', 'format': 'auto', 'codec': 'auto'}),
    }
    return {k: {'class_type': c, 'inputs': i} for k, (c, i) in g.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', required=True); ap.add_argument('--prompt', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--negative', default=NEG); ap.add_argument('--seconds', type=float, default=5)
    ap.add_argument('--fps', type=int, default=24); ap.add_argument('--width', type=int, default=1280)
    ap.add_argument('--height', type=int, default=720); ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--last-frame', help='end keyframe: first-and-last-frame mode (the clip must end on this image)')
    ap.add_argument('--draft', action='store_true', help=f'fast preview: first pass {DRAFT["first"]}, input image {DRAFT["scale"]}')
    a = ap.parse_args()
    t0 = time.time()
    name = upload(os.path.expanduser(a.image))
    if a.last_frame:
        wf = graph_flf(name, upload(os.path.expanduser(a.last_frame)), a.prompt, a.negative, a.seconds, a.fps,
                       a.width, a.height, a.seed, a.draft)
    else:
        wf = graph(name, a.prompt, a.negative, a.seconds, a.fps, a.width, a.height, a.seed, a.draft)
    req = urllib.request.Request(f'{COMFY}/prompt', json.dumps({'prompt': wf, 'client_id': uuid.uuid4().hex}).encode(),
                                 {'Content-Type': 'application/json'})
    try:
        pid = json.load(urllib.request.urlopen(req))['prompt_id']
    except urllib.error.HTTPError as e:
        sys.exit(f'ComfyUI refused the workflow: {e.read().decode()[:2000]}')
    print('queued', pid, flush=True)
    while True:
        h = json.load(urllib.request.urlopen(f'{COMFY}/history/{pid}'))
        if pid in h and h[pid].get('status', {}).get('completed') is not None:
            break
        time.sleep(5)
    st = h[pid]['status']
    if st.get('status_str') != 'success':
        sys.exit(f'failed: {json.dumps(st)[:2000]}')
    msgs = {m[0]: m[1].get('timestamp') for m in st.get('messages', [])}
    exec_s = (msgs.get('execution_success', 0) - msgs.get('execution_start', 0)) / 1000
    files = [o for n in h[pid]['outputs'].values() for k in ('videos', 'gifs', 'images') for o in n.get(k, [])]
    f = files[0]
    q = urllib.parse.urlencode({'filename': f['filename'], 'subfolder': f.get('subfolder', ''), 'type': f.get('type', 'output')})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, 'wb').write(urllib.request.urlopen(f'{COMFY}/view?{q}').read())
    print(json.dumps({'out': a.out, 'comfy_file': f['filename'], 'prompt_id': pid, 'seed': a.seed,
                      'draft': a.draft, 'flf': bool(a.last_frame), 'wall_s': round(time.time() - t0, 1), 'exec_s': round(exec_s, 1),
                      'size_mb': round(os.path.getsize(a.out) / 1e6, 2)}))


if __name__ == '__main__':
    main()
