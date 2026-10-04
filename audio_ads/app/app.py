import asyncio
import json
import re
import subprocess
import time
import uuid
from pathlib import Path

import edge_tts
from flask import Flask, abort, jsonify, render_template, request, send_file

app = Flask(__name__)
ROOT = Path("/data/audio_ads")
MUSIC = ROOT / "music"
SFX = ROOT / "sfx"
OUT = ROOT / "outputs"
PROJECTS = ROOT / "projects"
for folder in (MUSIC,SFX,OUT,PROJECTS):
    folder.mkdir(parents=True, exist_ok=True)

ALLOWED = {".mp3",".wav",".m4a",".aac",".ogg",".flac"}
LANGUAGES = {
    "de-DE":"Deutsch","it-IT":"Italiano","en-US":"English",
    "ro-RO":"Română","fr-FR":"Français","es-ES":"Español"
}
MASTERING = {
    "streaming":{"name":"Streaming / Web","lufs":-16,"tp":-1.0,"lra":7},
    "broadcast":{"name":"Radio EBU R128","lufs":-23,"tp":-1.0,"lra":7},
    "sonos":{"name":"Sonos / Locale","lufs":-18,"tp":-1.0,"lra":8}
}

def safe(value):
    value = re.sub(r"[^A-Za-z0-9._ -]+","_",value or "").strip()
    return value[:120] or uuid.uuid4().hex[:8]

def run(cmd):
    p = subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-3000:])
    return p

def duration(path):
    p = run(["ffprobe","-v","error","-show_entries","format=duration","-of",
             "default=noprint_wrappers=1:nokey=1",str(path)])
    try: return float(p.stdout.strip())
    except: return 0.0

def library(folder):
    return [{"name":p.name,"size":p.stat().st_size}
            for p in sorted(folder.iterdir(),key=lambda x:x.name.lower())
            if p.is_file() and p.suffix.lower() in ALLOWED]

async def get_voices(locale,gender):
    voices = await edge_tts.list_voices()
    return [{
        "short":v.get("ShortName"),
        "friendly":v.get("FriendlyName"),
        "gender":v.get("Gender"),
        "locale":v.get("Locale")
    } for v in voices
      if (not locale or v.get("Locale")==locale)
      and (not gender or v.get("Gender","").lower()==gender.lower())]

async def make_voice(text,voice,rate,pitch,volume,target):
    tts = edge_tts.Communicate(
        text=text,voice=voice,rate=f"{rate:+d}%",
        pitch=f"{pitch:+d}Hz",volume=f"{volume:+d}%"
    )
    await tts.save(str(target))

@app.get("/")
def index():
    return render_template("index.html",languages=LANGUAGES,mastering=MASTERING)

@app.get("/api/health")
def health():
    return jsonify({"ok":True,"service":"audio-ads","version":"1.0.3"})

@app.get("/api/voices")
def voices():
    try:
        return jsonify(asyncio.run(get_voices(
            request.args.get("locale","de-DE"),
            request.args.get("gender","female")
        )))
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.get("/api/library")
def media_library():
    return jsonify({"music":library(MUSIC),"sfx":library(SFX)})

@app.post("/api/upload/<kind>")
def upload(kind):
    folder = MUSIC if kind=="music" else SFX if kind=="sfx" else None
    if folder is None: abort(404)
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error":"Nessun file selezionato"}),400
    name = safe(f.filename)
    if Path(name).suffix.lower() not in ALLOWED:
        return jsonify({"error":"Formato audio non supportato"}),400
    f.save(folder/name)
    return jsonify({"ok":True,"name":name})

@app.get("/api/media/<kind>/<path:name>")
def media(kind,name):
    folder = MUSIC if kind=="music" else SFX if kind=="sfx" else None
    if folder is None:
        abort(404)
    p = folder/safe(name)
    if not p.exists() or not p.is_file():
        abort(404)
    return send_file(p,conditional=True)

@app.post("/api/preview")
def preview():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    if not text: return jsonify({"error":"Testo vuoto"}),400
    target = OUT/f"preview_{uuid.uuid4().hex[:8]}.mp3"
    try:
        asyncio.run(make_voice(
            text[:400],data["voice"],int(data.get("rate",0)),
            int(data.get("pitch",0)),int(data.get("tts_volume",0)),target
        ))
        return jsonify({"ok":True,"url":f"api/output/{target.name}"})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.post("/api/generate")
def generate():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    voice = data.get("voice")
    if not text: return jsonify({"error":"Inserisci il testo dello spot"}),400
    if not voice: return jsonify({"error":"Seleziona una voce"}),400

    uid = uuid.uuid4().hex[:10]
    title = safe(data.get("title") or "Spot")
    speech = OUT/f"{uid}_speech.mp3"
    master_wav = OUT/f"{uid}_master.wav"
    master_mp3 = OUT/f"{title}_{uid}.mp3"

    try:
        asyncio.run(make_voice(
            text,voice,int(data.get("rate",0)),int(data.get("pitch",0)),
            int(data.get("tts_volume",0)),speech
        ))
        speech_len = duration(speech)
        total_len = speech_len + 0.8
        inputs = ["-i",str(speech)]
        filters = [
            f"[0:a]volume={float(data.get('voice_gain',1.0))},adelay=250|250[voice_src]"
        ]
        labels = []
        voice_mix_label = "[voice_src]"
        idx = 1

        music = data.get("music")
        music_path = MUSIC/safe(music) if music else None
        if music_path and music_path.exists():
            inputs += ["-stream_loop","-1","-i",str(music_path)]
            music_gain = float(data.get("music_gain",.38))
            filters += [
                "[voice_src]asplit=2[voice_mix][voice_sc]",
                f"[{idx}:a]atrim=0:{total_len:.2f},asetpts=N/SR/TB,"
                f"volume={music_gain},highpass=f=45,lowpass=f=18000[music]",
                "[music][voice_sc]sidechaincompress="
                "threshold=.06:ratio=4:attack=15:release=350:makeup=1[duck]"
            ]
            voice_mix_label = "[voice_mix]"
            labels.append("[duck]")
            idx += 1

        intro = data.get("intro")
        if intro and (SFX/safe(intro)).exists():
            inputs += ["-i",str(SFX/safe(intro))]
            filters.append(f"[{idx}:a]volume=.55[intro]")
            labels.append("[intro]")
            idx += 1

        outro = data.get("outro")
        if outro and (SFX/safe(outro)).exists():
            delay = max(0,int((speech_len-1.8)*1000))
            inputs += ["-i",str(SFX/safe(outro))]
            filters.append(f"[{idx}:a]volume=.55,adelay={delay}|{delay}[outro]")
            labels.append("[outro]")

        labels.insert(0, voice_mix_label)

        preset = MASTERING.get(data.get("mastering"),MASTERING["sonos"])
        filters += [
            f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:dropout_transition=2[mix]",
            f"[mix]loudnorm=I={preset['lufs']}:TP={preset['tp']}:LRA={preset['lra']},alimiter=limit=.95[out]"
        ]

        run(["ffmpeg","-y",*inputs,"-filter_complex",";".join(filters),
             "-map","[out]","-t",f"{total_len:.2f}",
             "-ar","48000","-ac","2",str(master_wav)])
        run(["ffmpeg","-y","-i",str(master_wav),"-codec:a","libmp3lame",
             "-b:a","192k",str(master_mp3)])

        project = {
            "id":uid,"title":title,"created":int(time.time()),
            "duration":round(duration(master_mp3),2),
            "mp3":master_mp3.name,"wav":master_wav.name,
            "music_used":music if music_path and music_path.exists() else None,
            "settings":data
        }
        (PROJECTS/f"{uid}.json").write_text(
            json.dumps(project,ensure_ascii=False,indent=2),encoding="utf-8"
        )
        return jsonify({
            "ok":True,"project":project,
            "mp3_url":f"api/output/{master_mp3.name}",
            "wav_url":f"api/output/{master_wav.name}"
        })
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.get("/api/projects")
def projects():
    data=[]
    for p in PROJECTS.glob("*.json"):
        try: data.append(json.loads(p.read_text(encoding="utf-8")))
        except: pass
    data.sort(key=lambda x:x.get("created",0),reverse=True)
    return jsonify(data)

@app.get("/api/output/<path:name>")
def output(name):
    p = OUT/safe(name)
    if not p.exists(): abort(404)
    return send_file(p,conditional=True)

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8099,threaded=True)
