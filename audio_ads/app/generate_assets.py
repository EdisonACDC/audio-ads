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


def make_style_music(name, style, bpm=80, key=220.0, duration=28.0):
    target = MUSIC / f"{name}.mp3"
    if target.exists():
        return

    n = int(SR * duration)
    out = np.zeros(n, dtype=np.float32)
    beat = 60.0 / bpm
    rng = np.random.default_rng(abs(hash(name)) % (2**32))

    def add_tone(onset, length, freq, amp=.08, harmonics=(1.0,.25,.08), decay=3.0):
        a = int(onset * SR)
        L = min(int(length * SR), n-a)
        if L <= 0:
            return
        t = np.arange(L) / SR
        env = np.exp(-decay*t)
        sig = np.zeros(L, dtype=np.float32)
        for h,weight in enumerate(harmonics, start=1):
            sig += weight*np.sin(2*np.pi*freq*h*t)
        out[a:a+L] += amp*sig*env

    def add_noise_hit(onset, amp=.03, length=.15, decay=28):
        a = int(onset * SR)
        L = min(int(length*SR), n-a)
        if L <= 0:
            return
        t = np.arange(L)/SR
        out[a:a+L] += amp*rng.normal(0,1,L)*np.exp(-decay*t)

    # shared harmonic map
    roots = [key, key*0.84, key*0.75, key*0.89]

    if style == "piano":
        for bar,onset in enumerate(np.arange(0,duration,beat*4)):
            root = roots[bar % len(roots)]
            chord = [root, root*1.2599, root*1.4983]
            for i,f in enumerate(chord):
                add_tone(onset+i*.22, 2.8, f, .075, (1,.18,.04), 2.0)
            add_tone(onset+beat*2, 1.8, chord[1]*2, .03, (1,.1), 2.8)

    elif style == "jazz":
        for bar,onset in enumerate(np.arange(0,duration,beat*4)):
            root = roots[bar % len(roots)]*.75
            chord=[root,root*1.1892,root*1.4142,root*1.6818]
            for f in chord:
                add_tone(onset,.9,f,.035,(1,.32,.10),4.2)
                add_tone(onset+beat*2,.9,f,.028,(1,.28,.08),4.0)
            for b in [0,2]:
                add_tone(onset+b*beat, .35, root/2, .08,(1,.08),7)
            for b in [1,3]:
                add_noise_hit(onset+b*beat,.018,.09,40)

    elif style == "bossa":
        for bar,onset in enumerate(np.arange(0,duration,beat*4)):
            root=roots[bar%len(roots)]
            chord=[root,root*1.2599,root*1.4983]
            for b in [0,1.5,2.5]:
                for f in chord:
                    add_tone(onset+b*beat,.45,f,.024,(1,.2),6)
            for b in [0,2]:
                add_tone(onset+b*beat,.25,root/2,.075,(1,.05),9)
            for b in [1,3]:
                add_noise_hit(onset+b*beat,.014,.07,45)

    elif style == "pop":
        for i,onset in enumerate(np.arange(0,duration,beat)):
            root=roots[(i//4)%len(roots)]
            add_tone(onset,.30,root/2,.07,(1,.10),8)
            if i%2==1: add_noise_hit(onset,.025,.11,30)
            add_tone(onset,.45,root*2,.018,(1,.12),5)
        for onset in np.arange(0,duration,beat/2):
            add_noise_hit(onset,.005,.035,65)

    elif style == "cinematic":
        for bar,onset in enumerate(np.arange(0,duration,beat*4)):
            root=roots[bar%len(roots)]/2
            for f in [root,root*1.2599,root*1.4983]:
                a=int(onset*SR); L=min(int(beat*4*SR),n-a)
                if L>0:
                    t=np.arange(L)/SR
                    env=np.sin(np.pi*np.clip(t/(beat*4),0,1))**.7
                    out[a:a+L] += .035*np.sin(2*np.pi*f*t)*env
            add_tone(onset,1.2,root/2,.10,(1,.05),3.2)
            add_tone(onset+beat*3,1.0,root*2,.025,(1,.25),4)

    elif style == "acoustic":
        for bar,onset in enumerate(np.arange(0,duration,beat*4)):
            root=roots[bar%len(roots)]
            chord=[root,root*1.2599,root*1.4983]
            pattern=[0,2,1,2,0,2,1,2]
            for i,p in enumerate(pattern):
                add_tone(onset+i*(beat/2),.5,chord[p],.045,(1,.30,.12),7.5)

    elif style == "ambient":
        for bar,onset in enumerate(np.arange(0,duration,beat*6)):
            root=roots[bar%len(roots)]/2
            L=min(int(beat*6*SR),n-int(onset*SR))
            if L<=0: continue
            t=np.arange(L)/SR
            env=np.sin(np.pi*np.clip(t/(beat*6),0,1))
            shimmer=(np.sin(2*np.pi*root*t)+.5*np.sin(2*np.pi*root*1.5*t)+.25*np.sin(2*np.pi*root*2*t))
            out[int(onset*SR):int(onset*SR)+L] += .028*shimmer*env
            add_tone(onset+beat*2.5,2.0,root*4,.018,(1,.15),1.8)

    elif style == "festive":
        for i,onset in enumerate(np.arange(0,duration,beat)):
            root=roots[(i//4)%len(roots)]
            add_tone(onset,.35,root/2,.075,(1,.12),8)
            add_tone(onset,.55,root*2,.028,(1,.22),5)
            if i%2==1:add_noise_hit(onset,.022,.1,35)
        for onset in np.arange(.25,duration,beat):
            add_tone(onset,.35,key*3,.020,(1,.4),10)

    elif style == "bells":
        notes=[key*2,key*2.2449,key*2.5198,key*2.9966,key*3.1748]
        for i,onset in enumerate(np.arange(0,duration,beat)):
            add_tone(onset,1.0,notes[i%len(notes)],.035,(1,.55,.18),4.8)
            if i%4==0:
                add_tone(onset,2.0,roots[(i//4)%len(roots)]/2,.045,(1,.06),2)

    # fade in/out and gentle limiter prep
    fi=min(int(.45*SR),n)
    fo=min(int(.9*SR),n)
    out[:fi]*=np.linspace(0,1,fi)
    out[-fo:]*=np.linspace(1,0,fo)

    wav = MUSIC / f"{name}.wav"
    write_wav(wav,out)
    subprocess.run([
        "ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(wav),
        "-codec:a","libmp3lame","-b:a","160k",str(target)
    ],check=True)
    wav.unlink(missing_ok=True)

DISTINCT_TRACKS = [
    ("Piano_Romance_01","piano",66,220.0),
    ("Jazz_Lounge_01","jazz",84,196.0),
    ("Bossa_Restaurant_01","bossa",102,196.0),
    ("Modern_Pop_01","pop",112,220.0),
    ("Cinematic_Premium_01","cinematic",72,174.61),
    ("Acoustic_Warm_01","acoustic",88,196.0),
    ("Ambient_Elegant_01","ambient",58,164.81),
    ("Party_Promo_01","festive",118,220.0),
    ("Christmas_Bells_01","bells",92,196.0),
    ("Piano_Classy_02","piano",72,246.94),
    ("Jazz_Dinner_02","jazz",78,174.61),
    ("Bossa_Summer_02","bossa",108,220.0),
    ("Modern_Radio_02","pop",124,246.94),
    ("Cinematic_Event_02","cinematic",80,196.0),
    ("Acoustic_Family_02","acoustic",96,220.0),
    ("Ambient_Spa_02","ambient",52,146.83),
    ("Festive_Celebration_02","festive",126,246.94),
]

for name,style,bpm,key in DISTINCT_TRACKS:
    make_style_music(name,style,bpm,key)

