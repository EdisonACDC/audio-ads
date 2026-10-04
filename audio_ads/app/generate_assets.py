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

def chime(name, notes, duration=1.8):
    target = SFX / f"{name}.wav"
    if target.exists():
        return
    n = int(SR*duration)
    out = np.zeros(n, dtype=np.float32)
    for i,f in enumerate(notes):
        a = int(.18*i*SR)
        t = np.arange(n-a)/SR
        env = np.exp(-3.1*t)
        out[a:] += .15*(np.sin(2*np.pi*f*t)+.25*np.sin(2*np.pi*2*f*t))*env
    write_wav(target, out)

def impact(name, freq=72, duration=1.15):
    target = SFX / f"{name}.wav"
    if target.exists():
        return
    n = int(SR*duration)
    t = np.arange(n)/SR
    rng = np.random.default_rng(abs(hash(name)) % (2**32))
    noise = rng.normal(0,1,n)
    env = np.exp(-5.5*t)
    body = np.sin(2*np.pi*freq*t) * np.exp(-4.2*t)
    click = np.sin(2*np.pi*880*t) * np.exp(-28*t)
    out = .18*body + .035*noise*env + .045*click
    write_wav(target, out)

def sparkle(name, duration=1.6):
    target = SFX / f"{name}.wav"
    if target.exists():
        return
    n = int(SR*duration)
    out = np.zeros(n, dtype=np.float32)
    tones = [987.77,1174.66,1318.51,1567.98]
    for i,f in enumerate(tones):
        a = int((.08 + i*.12)*SR)
        t = np.arange(n-a)/SR
        env = np.exp(-5.0*t)
        out[a:] += .075*(np.sin(2*np.pi*f*t)+.2*np.sin(2*np.pi*2*f*t))*env
    write_wav(target, out)

def pulse(name, freq=180, duration=.55):
    target = SFX / f"{name}.wav"
    if target.exists():
        return
    n = int(SR*duration)
    t = np.arange(n)/SR
    env = np.exp(-8*t)
    out = .14*np.sin(2*np.pi*freq*t)*env + .05*np.sin(2*np.pi*freq*2*t)*env
    write_wav(target, out)

def applause(name, duration=2.3):
    target = SFX / f"{name}.wav"
    if target.exists():
        return
    n = int(SR*duration)
    rng = np.random.default_rng(31415)
    out = np.zeros(n, dtype=np.float32)
    for onset in np.arange(0.05, duration, .075):
        a = int(onset*SR)
        L = min(int(.09*SR), n-a)
        if L <= 0:
            continue
        t = np.arange(L)/SR
        burst = rng.normal(0,1,L) * np.exp(-35*t)
        out[a:a+L] += .025*burst
    envelope = np.sin(np.pi*np.clip(np.arange(n)/(n-1),0,1))**.45
    out *= envelope
    write_wav(target, out)

TRACKS = {
    "Elegant_Lounge": ([[146.83,185,220],[123.47,146.83,185],[98,123.47,146.83],[110,138.59,164.81]],74,.90),
    "Wedding_Warm": ([[130.81,164.81,196],[110,130.81,164.81],[87.31,110,130.81],[98,123.47,146.83]],68,.85),
    "Corporate_Clean": ([[146.83,185,220],[110,138.59,164.81],[123.47,155.56,185],[98,123.47,146.83]],88,1.0),
    "Restaurant_Evening": ([[110,138.59,164.81],[98,123.47,146.83],[82.41,110,130.81],[92.5,116.54,138.59]],72,.78),
    "Celebration_Light": ([[164.81,207.65,246.94],[130.81,164.81,196],[146.83,185,220],[123.47,155.56,185]],96,1.05),

    "Luxury_Dinner": ([[130.81,164.81,196],[123.47,155.56,185],[110,138.59,164.81],[98,123.47,146.83]],64,.76),
    "Romantic_Piano": ([[130.81,164.81,196],[98,130.81,164.81],[110,138.59,164.81],[87.31,110,130.81]],62,.72),
    "Family_Friendly": ([[146.83,185,220],[164.81,207.65,246.94],[123.47,155.56,185],[146.83,185,220]],92,.94),
    "Modern_Promo": ([[146.83,185,220],[123.47,155.56,185],[110,138.59,164.81],[130.81,164.81,196]],104,1.08),
    "Radio_Energy": ([[164.81,207.65,246.94],[146.83,185,220],[123.47,155.56,185],[110,138.59,164.81]],112,1.10),
    "Soft_Acoustic": ([[130.81,164.81,196],[110,138.59,164.81],[98,123.47,146.83],[116.54,146.83,174.61]],70,.78),
    "Italian_Evening": ([[146.83,174.61,220],[130.81,164.81,196],[110,138.59,164.81],[123.47,155.56,185]],76,.84),
    "Business_Event": ([[146.83,185,220],[123.47,155.56,185],[138.59,174.61,207.65],[110,138.59,164.81]],94,.98),
    "Festive_Event": ([[164.81,207.65,246.94],[146.83,185,220],[185,220,277.18],[130.81,164.81,196]],108,1.06),
    "Calm_Ambience": ([[110,138.59,164.81],[98,123.47,146.83],[92.5,116.54,138.59],[82.41,103.83,123.47]],58,.65),
    "Premium_Brand": ([[123.47,155.56,185],[146.83,185,220],[110,138.59,164.81],[130.81,164.81,196]],82,.88),
    "Christmas_Warm": ([[130.81,164.81,196],[98,123.47,146.83],[110,138.59,164.81],[146.83,185,220]],78,.92),
    "Summer_Fresh": ([[164.81,207.65,246.94],[146.83,185,220],[130.81,164.81,196],[123.47,155.56,185]],102,1.00),
}
for name,(chords,bpm,brightness) in TRACKS.items():
    make_music(name,chords,bpm,brightness)

whoosh("Whoosh_Intro",1.1,False)
whoosh("Whoosh_Outro",1.0,True)
whoosh("Whoosh_Soft",.75,False)
whoosh("Whoosh_Fast",.45,False)

chime("Elegant_Chime",(523.25,659.25,783.99))
chime("Celebration_Chime",(659.25,830.61,987.77))
chime("Warm_Dinner_Chime",(392.00,523.25,659.25),2.0)
chime("Luxury_Chime",(783.99,987.77,1174.66),1.5)
chime("Notification_Chime",(659.25,783.99),1.0)

impact("Radio_Impact",72,1.1)
impact("Soft_Impact",96,.85)
impact("Deep_Impact",55,1.4)

sparkle("Sparkle_Logo",1.5)
sparkle("Sparkle_Wedding",2.0)

pulse("Transition_Pulse",180,.55)
pulse("Promo_Pulse",240,.45)
pulse("Soft_Click",520,.28)

applause("Applause_Short",2.3)
