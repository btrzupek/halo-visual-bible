#!/usr/bin/env python3
"""Instrumental music with ACE-Step 1.5 (turbo, all-in-one checkpoint) on halo's ComfyUI.

The graph is the official "ACE-Step 1.5 Music Generation AIO" template (workflows/_templates/
audio_ace_step_1_5_checkpoint.json) in API form, with lyrics set to [Instrumental].

  python3 scripts/ace_music.py --tags "sparse ancient Mediterranean, solo lyre, low drone, no drums" \
      --seconds 30 --bpm 60 --key "D minor" --out sketch.mp3 [--seed 7]
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, uuid

COMFY = os.environ.get('COMFY_URL', 'http://127.0.0.1:8188')


def graph(tags, seconds, bpm, key, seed, timesig):
    g = {
        'ckpt': ('CheckpointLoaderSimple', {'ckpt_name': 'ace_step_1.5_turbo_aio.safetensors'}),
        'shift': ('ModelSamplingAuraFlow', {'model': ['ckpt', 0], 'shift': 3.0}),
        'text': ('TextEncodeAceStepAudio1.5', {'clip': ['ckpt', 1], 'tags': tags, 'lyrics': '[Instrumental]', 'seed': seed,
                                               'bpm': bpm, 'duration': float(seconds), 'timesignature': timesig,
                                               'language': 'en', 'keyscale': key, 'generate_audio_codes': True,
                                               'cfg_scale': 2.0, 'temperature': 0.85, 'top_p': 0.9, 'top_k': 0, 'min_p': 0.0}),
        'neg': ('ConditioningZeroOut', {'conditioning': ['text', 0]}),
        'empty': ('EmptyAceStep1.5LatentAudio', {'seconds': float(seconds), 'batch_size': 1}),
        'ks': ('KSampler', {'model': ['shift', 0], 'positive': ['text', 0], 'negative': ['neg', 0], 'latent_image': ['empty', 0],
                            'seed': seed, 'steps': 8, 'cfg': 1.0, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 1.0}),
        'dec': ('VAEDecodeAudio', {'samples': ['ks', 0], 'vae': ['ckpt', 2]}),
        'save': ('SaveAudioMP3', {'audio': ['dec', 0], 'filename_prefix': 'audio/vb_ace15', 'quality': 'V0'}),
    }
    return {k: {'class_type': c, 'inputs': i} for k, (c, i) in g.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tags', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--seconds', type=float, default=30); ap.add_argument('--bpm', type=int, default=60)
    ap.add_argument('--key', default='D minor'); ap.add_argument('--timesig', default='4'); ap.add_argument('--seed', type=int, default=7)
    a = ap.parse_args()
    t0 = time.time()
    wf = graph(a.tags, a.seconds, a.bpm, a.key, a.seed, a.timesig)
    req = urllib.request.Request(f'{COMFY}/prompt', json.dumps({'prompt': wf, 'client_id': uuid.uuid4().hex}).encode(),
                                 {'Content-Type': 'application/json'})
    try:
        pid = json.load(urllib.request.urlopen(req))['prompt_id']
    except urllib.error.HTTPError as e:
        sys.exit(f'ComfyUI refused the workflow: {e.read().decode()[:2000]}')
    while True:
        h = json.load(urllib.request.urlopen(f'{COMFY}/history/{pid}'))
        if pid in h and h[pid].get('status', {}).get('completed') is not None:
            break
        time.sleep(3)
    st = h[pid]['status']
    if st.get('status_str') != 'success':
        sys.exit(f'failed: {json.dumps(st)[:2000]}')
    f = [o for n in h[pid]['outputs'].values() for k in ('audio', 'audios') for o in n.get(k, [])][0]
    q = urllib.parse.urlencode({'filename': f['filename'], 'subfolder': f.get('subfolder', ''), 'type': f.get('type', 'output')})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, 'wb').write(urllib.request.urlopen(f'{COMFY}/view?{q}').read())
    msgs = {m[0]: m[1].get('timestamp') for m in st.get('messages', [])}
    print(json.dumps({'out': a.out, 'seed': a.seed, 'wall_s': round(time.time() - t0, 1),
                      'exec_s': round((msgs.get('execution_success', 0) - msgs.get('execution_start', 0)) / 1000, 1)}))


if __name__ == '__main__':
    main()
