from pathlib import Path
import subprocess
import wave
import numpy as np

ROOT = Path("/data/audio_ads")
MUSIC = ROOT / "music"
SFX = ROOT / "sfx"
MUSIC.mkdir(parents=True, exist_ok=True)
SFX.mkdir(parents=True, exist_ok=True)
SR = 44100

def write_wav(path, signal):
    signal = np.asarray(signal, dtype=np.float32)
    peak = max(float(np.max(np.abs(signal))), 1e-6)
    if peak > 0.95:
        signal *= 0.95 / peak
    stereo = np.column_stack((signal, signal))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((stereo * 32767).astype(np.int16).tobytes())

def make_music(name, chords, bpm, brightness=1.0):
    target = MUSIC / f"{name}.mp3"
    if target.exists():
        return
    duration = 24.0
    n = int(SR * duration)
    out = np.zeros(n, dtype=np.float32)
    section = duration / len(chords)

    for i, chord in enumerate(chords):
        a = int(i * section * SR)
        b = min(n, int((i + 1) * section * SR))
        t = np.arange(b-a) / SR
        env = np.ones(b-a, dtype=np.float32)
        fade = min(int(.7*SR), len(env)//2)
        if fade:
            env[:fade] = np.linspace(0,1,fade)
            env[-fade:] = np.linspace(1,0,fade)
        pad = np.zeros_like(t)
        for f in chord:
            pad += (
                .62*np.sin(2*np.pi*f*t)
                + .20*np.sin(2*np.pi*2*f*t+.2)
                + .07*np.sin(2*np.pi*3*f*t+.5)
            )
        pad /= len(chord)
        out[a:b] += .16 * brightness * pad * env

    beat = 60 / bpm
    notes = [293.66, 369.99, 440.0, 493.88, 440.0, 369.99]
    for k, onset in enumerate(np.arange(.5, duration, beat*2)):
        a = int(onset * SR)
        L = min(int(1.1*SR), n-a)
        if L <= 0:
            continue
        t = np.arange(L)/SR
        env = np.exp(-3.2*t)
        f = notes[k % len(notes)]
        out[a:a+L] += .035 * (
            np.sin(2*np.pi*f*t) + .25*np.sin(2*np.pi*2*f*t)
        ) * env

    out[:int(.5*SR)] *= np.linspace(0,1,int(.5*SR))
    out[-int(.8*SR):] *= np.linspace(1,0,int(.8*SR))

    wav = MUSIC / f"{name}.wav"
    write_wav(wav, out)
    subprocess.run([
        "ffmpeg","-y","-hide_banner","-loglevel","error",
        "-i",str(wav),"-codec:a","libmp3lame","-b:a","128k",str(target)
    ], check=True)
    wav.unlink(missing_ok=True)

def whoosh(name, duration, reverse=False):
    target = SFX / f"{name}.wav"
    if target.exists():
        return
    n = int(SR*duration)
    t = np.arange(n)/SR
    rng = np.random.default_rng(42 if not reverse else 84)
    noise = rng.normal(0,1,n)
    smooth = np.convolve(noise, np.ones(180)/180, mode="same")
    sweep = np.sin(2*np.pi*(100*t + (1700/(2*duration))*t*t))
    if reverse:
        sweep = sweep[::-1]
    env = np.sin(np.pi*np.clip(t/duration,0,1))**2
    write_wav(target, .22*smooth*env + .09*sweep*env)

def chime(name, notes):
    target = SFX / f"{name}.wav"
    if target.exists():
        return
    duration = 1.8
    n = int(SR*duration)
    out = np.zeros(n, dtype=np.float32)
    for i,f in enumerate(notes):
        a = int(.18*i*SR)
        t = np.arange(n-a)/SR
        env = np.exp(-3.1*t)
        out[a:] += .15*(np.sin(2*np.pi*f*t)+.25*np.sin(2*np.pi*2*f*t))*env
    write_wav(target, out)

TRACKS = {
    "Elegant_Lounge": ([[146.83,185,220],[123.47,146.83,185],[98,123.47,146.83],[110,138.59,164.81]],74,.90),
    "Wedding_Warm": ([[130.81,164.81,196],[110,130.81,164.81],[87.31,110,130.81],[98,123.47,146.83]],68,.85),
    "Corporate_Clean": ([[146.83,185,220],[110,138.59,164.81],[123.47,155.56,185],[98,123.47,146.83]],88,1.0),
    "Restaurant_Evening": ([[110,138.59,164.81],[98,123.47,146.83],[82.41,110,130.81],[92.5,116.54,138.59]],72,.78),
    "Celebration_Light": ([[164.81,207.65,246.94],[130.81,164.81,196],[146.83,185,220],[123.47,155.56,185]],96,1.05),
}
for name,(chords,bpm,brightness) in TRACKS.items():
    make_music(name,chords,bpm,brightness)

whoosh("Whoosh_Intro",1.1,False)
whoosh("Whoosh_Outro",1.0,True)
chime("Elegant_Chime",(523.25,659.25,783.99))
chime("Celebration_Chime",(659.25,830.61,987.77))
