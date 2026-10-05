const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const base=location.pathname.endsWith("/")?location.pathname:location.pathname+"/";
const api=p=>base+p.replace(/^\//,"");

function setTab(id){
  $$(".tab,.panel").forEach(x=>x.classList.remove("active"));
  const btn=document.querySelector(`.tab[data-tab="${id}"]`);
  const panel=$("#"+id);
  if(btn)btn.classList.add("active");
  if(panel)panel.classList.add("active");
  if(id==="archiveTab")loadProjects();
}
$$(".tab").forEach(b=>b.addEventListener("click",()=>setTab(b.dataset.tab)));

function bindRange(id,out,suffix){
  const el=$("#"+id), target=$("#"+out);
  if(el&&target) el.addEventListener("input",e=>target.textContent=e.target.value+suffix);
}
bindRange("rate","rateV","%");
bindRange("pitch","pitchV"," Hz");
bindRange("ttsVolume","ttsV","%");
bindRange("musicGain","musicV","%");

async function loadVoices(){
  const voice=$("#voice");
  if(!voice)return;
  voice.innerHTML="<option>Caricamento...</option>";
  try{
    const r=await fetch(api(`api/voices?locale=${$("#language").value}&gender=${$("#gender").value}`));
    const d=await r.json();
    if(!r.ok||d.error)throw new Error(d.error||"Errore voci");
    voice.innerHTML=d.map(v=>`<option value="${v.short}">${v.short.replace(v.locale+"-","")} — ${v.gender}</option>`).join("");
  }catch(e){
    voice.innerHTML=`<option>Errore: ${e.message}</option>`;
  }
}
$("#language")?.addEventListener("change",loadVoices);
$("#gender")?.addEventListener("change",loadVoices);

function jsString(s){
  return String(s).replace(/\\/g,"\\\\").replace(/'/g,"\\'");
}

async function loadLibrary(){
  try{
    const r=await fetch(api("api/library"));
    const d=await r.json();
    if(!r.ok)throw new Error(d.error||"Errore libreria");
    const opt=x=>`<option value="${x.name}">${x.name}</option>`;
    $("#music").innerHTML='<option value="">Nessuna</option>'+d.music.map(opt).join("");
    $("#intro").innerHTML='<option value="">Nessuno</option>'+d.sfx.map(opt).join("");
    $("#outro").innerHTML='<option value="">Nessuno</option>'+d.sfx.map(opt).join("");

    $("#musicList").innerHTML=d.music.map(x=>`
      <div class="item mediaItem">
        <div class="mediaName">🎵 ${x.name}</div>
        <div class="mediaActions">
          <button type="button" onclick="previewMedia('music','${encodeURIComponent(x.name)}')">▶ Ascolta</button>
          <button type="button" class="useBtn" onclick="chooseMusic('${jsString(x.name)}')">Usa questa</button>
        </div>
      </div>`).join("") || '<div class="item">Nessuna musica locale.</div>';

    $("#fxList").innerHTML=d.sfx.map(x=>`
      <div class="item mediaItem">
        <div class="mediaName">✨ ${x.name}</div>
        <div class="mediaActions">
          <button type="button" onclick="previewMedia('sfx','${encodeURIComponent(x.name)}')">▶ Ascolta</button>
          <button type="button" onclick="chooseIntro('${jsString(x.name)}')">Intro</button>
          <button type="button" onclick="chooseOutro('${jsString(x.name)}')">Outro</button>
        </div>
      </div>`).join("") || '<div class="item">Nessun effetto disponibile.</div>';
  }catch(e){
    $("#musicList").innerHTML=`<div class="item">Errore: ${e.message}</div>`;
    $("#fxList").innerHTML=`<div class="item">Errore: ${e.message}</div>`;
  }
}

window.previewMedia=(kind,name)=>{
  const player=kind==="music"?$("#musicPreview"):$("#fxPreview");
  player.src=api(`api/media/${kind}/${name}`);
  player.play().catch(()=>{});
};
window.chooseMusic=name=>{$("#music").value=name;};
window.chooseIntro=name=>{$("#intro").value=name;};
window.chooseOutro=name=>{$("#outro").value=name;};

async function upload(kind,input){
  const f=$(input)?.files?.[0];
  if(!f)return alert("Seleziona un file");
  const fd=new FormData();
  fd.append("file",f);
  try{
    const r=await fetch(api(`api/upload/${kind}`),{method:"POST",body:fd});
    const d=await r.json();
    if(!r.ok)throw new Error(d.error||"Errore upload");
    await loadLibrary();
  }catch(e){ alert(e.message); }
}
$("#uploadMusic")?.addEventListener("click",()=>upload("music","#musicFile"));
$("#uploadFx")?.addEventListener("click",()=>upload("sfx","#fxFile"));

$("#preview")?.addEventListener("click",async()=>{
  const text=$("#text").value.trim();
  if(!text)return alert("Inserisci il testo");
  const btn=$("#preview");
  btn.disabled=true;
  btn.textContent="Generazione...";
  try{
    const r=await fetch(api("api/preview"),{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        text,
        voice:$("#voice").value,
        rate:+$("#rate").value,
        pitch:+$("#pitch").value,
        tts_volume:+$("#ttsVolume").value
      })
    });
    const d=await r.json();
    if(!r.ok)throw new Error(d.error||"Errore TTS");
    $("#previewPlayer").src=api(d.url);
    await $("#previewPlayer").play().catch(()=>{});
  }catch(e){ alert(e.message); }
  finally{
    btn.disabled=false;
    btn.textContent="▶ Anteprima voce";
  }
});

const AD_PRESETS={
  restaurant_elegant:{name:"Ristorante elegante",desc:"Voce calda, ritmo rilassato, musica romantica o jazz lounge, effetti minimi.",rate:-5,musicGain:32,master:"sonos",category:"Romantico"},
  wedding_event:{name:"Matrimonio / Evento",desc:"Apertura emozionale, voce elegante, musica romantica o cinematica e chiusura calorosa.",rate:-7,musicGain:34,master:"sonos",category:"Romantico"},
  radio_30:{name:"Radio classico 30s",desc:"Hook rapido, messaggio centrale chiaro e CTA finale.",rate:3,musicGain:30,master:"broadcast",category:"Upbeat"},
  promo_energy:{name:"Promo energica",desc:"Ritmo più veloce, musica brillante e stacco iniziale deciso.",rate:10,musicGain:40,master:"streaming",category:"Upbeat"},
  premium_luxury:{name:"Premium / Lusso",desc:"Voce lenta e autorevole, musica elegante e spazio tra le frasi.",rate:-10,musicGain:28,master:"sonos",category:"Romantico"},
  family_warm:{name:"Family / Caldo",desc:"Voce amichevole, tono positivo, musica morbida e luminosa.",rate:-2,musicGain:34,master:"sonos",category:"Upbeat"},
  corporate_clean:{name:"Corporate / Pulito",desc:"Voce chiara, ritmo regolare, musica moderna discreta.",rate:0,musicGain:26,master:"streaming",category:"Elettronico"},
  cinematic_story:{name:"Cinematico / Storytelling",desc:"Apertura atmosferica, ritmo più lento e crescendo musicale.",rate:-8,musicGain:36,master:"streaming",category:"World"}
};
function applyAdPreset(){
  const p=AD_PRESETS[$("#adPreset")?.value];
  if(!p)return;
  $("#rate").value=p.rate;
  $("#rateV").textContent=p.rate+"%";
  $("#musicGain").value=p.musicGain;
  $("#musicV").textContent=p.musicGain+"%";
  $("#mastering").value=p.master;
  $("#presetInfo").innerHTML="<b>"+p.name+"</b><span>"+p.desc+"</span>";
  if($("#onlineCategory"))$("#onlineCategory").value=p.category;
  if(onlineTracks.length)renderOnlineMusic();
}
$("#adPreset")?.addEventListener("change",applyAdPreset);

let onlineTracks=[];

async function loadOnlineMusic(){
  $("#onlineMusicList").innerHTML='<div class="item">Caricamento libreria online...</div>';
  try{
    const r=await fetch(api("api/online/freepd"));
    const d=await r.json();
    if(!r.ok)throw new Error(d.error||"Errore caricamento");
    onlineTracks=d;
    renderOnlineMusic();
  }catch(e){
    $("#onlineMusicList").innerHTML=`<div class="item">Errore: ${e.message}</div>`;
  }
}
function renderOnlineMusic(){
  const cat=$("#onlineCategory")?.value||"";
  const q=($("#onlineSearch")?.value||"").trim().toLowerCase();
  const items=onlineTracks.filter(x=>(!cat||x.category===cat)&&(!q||x.title.toLowerCase().includes(q)));
  $("#onlineMusicList").innerHTML=items.map(x=>`
    <div class="item mediaItem">
      <div class="mediaName">
        <b>🎼 ${x.title}</b>
        <small>${x.category} • ${x.license}</small>
      </div>
      <div class="mediaActions">
        <button type="button" onclick="previewOnline('${x.id}')">▶ Ascolta</button>
        <button type="button" class="useBtn" onclick="importOnline('${x.id}',this)">⬇ Importa</button>
      </div>
    </div>`).join("") || '<div class="item">Nessun brano trovato.</div>';
}
window.previewOnline=id=>{
  $("#musicPreview").src=api("api/online/freepd/preview/"+id);
  $("#musicPreview").play().catch(()=>{});
};
window.importOnline=async(id,btn)=>{
  if(btn){btn.disabled=true;btn.textContent="Importazione...";}
  try{
    const r=await fetch(api("api/online/freepd/import/"+id),{method:"POST"});
    const d=await r.json();
    if(!r.ok)throw new Error(d.error||"Errore importazione");
    await loadLibrary();
    $("#music").value=d.name;
    alert("Brano importato e selezionato: "+d.name);
  }catch(e){ alert(e.message); }
  finally{
    if(btn){btn.disabled=false;btn.textContent="⬇ Importa";}
  }
};

$("#showLocal")?.addEventListener("click",()=>{
  $("#localMusicArea").classList.remove("hidden");
  $("#onlineMusicArea").classList.add("hidden");
  $("#showLocal").classList.add("active");
  $("#showOnline").classList.remove("active");
});
$("#showOnline")?.addEventListener("click",()=>{
  $("#localMusicArea").classList.add("hidden");
  $("#onlineMusicArea").classList.remove("hidden");
  $("#showOnline").classList.add("active");
  $("#showLocal").classList.remove("active");
  if(!onlineTracks.length)loadOnlineMusic();
});
$("#onlineCategory")?.addEventListener("change",renderOnlineMusic);
$("#onlineSearch")?.addEventListener("input",renderOnlineMusic);

$("#generate")?.addEventListener("click",async()=>{
  const data={
    title:$("#title").value,
    text:$("#text").value,
    voice:$("#voice").value,
    rate:+$("#rate").value,
    pitch:+$("#pitch").value,
    tts_volume:+$("#ttsVolume").value,
    music:$("#music").value,
    music_gain:+$("#musicGain").value/100,
    intro:$("#intro").value,
    outro:$("#outro").value,
    voice_gain:+$("#voiceGain").value/100,
    mastering:$("#mastering").value
  };
  if(!data.text.trim())return alert("Inserisci il testo");

  const btn=$("#generate");
  btn.disabled=true;
  $("#status").textContent="🎙️ Generazione in corso...";
  $("#result").classList.add("hidden");
  try{
    const r=await fetch(api("api/generate"),{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(data)
    });
    const d=await r.json();
    if(!r.ok)throw new Error(d.error||"Errore");
    $("#finalPlayer").src=api(d.mp3_url);
    $("#mp3").href=api(d.mp3_url);
    $("#wav").href=api(d.wav_url);
    $("#result").classList.remove("hidden");
    $("#status").textContent=`✅ Spot pronto • ${d.project.duration}s`;
  }catch(e){
    $("#status").textContent="❌ "+e.message;
  }finally{
    btn.disabled=false;
  }
});

async function loadProjects(){
  try{
    const r=await fetch(api("api/projects"));
    const d=await r.json();
    $("#projects").innerHTML=d.length?d.map(p=>`
      <div class="item">
        <b>${p.title}</b><br>
        <small>${p.duration}s • ${new Date(p.created*1000).toLocaleString()}</small>
      </div>`).join(""):'<div class="item">Nessuno spot salvato.</div>';
  }catch(e){
    $("#projects").innerHTML=`<div class="item">Errore: ${e.message}</div>`;
  }
}
$("#refresh")?.addEventListener("click",loadProjects);

applyAdPreset();
loadVoices();
loadLibrary();
