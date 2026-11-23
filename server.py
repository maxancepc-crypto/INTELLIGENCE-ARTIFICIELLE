"""API + interface de chat (déployable sur Render).
GET /  -> interface | POST /run {goal, history} -> id | GET /runs/{id} -> état"""
import os
import threading
import uuid
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

load_dotenv()
from core import run  # noqa: E402

app = FastAPI(title="IA autonome gratuite")
RUNS = {}

PAGE = r"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>IA autonome</title>
<style>
:root{--bg:#f7f6f3;--fg:#1f1e1c;--mut:#7a766d;--card:#ffffff;--bd:#e4e1d9;--ac:#c4572b;--user:#ece8df}
@media (prefers-color-scheme:dark){:root{--bg:#212121;--fg:#ececec;--mut:#9a9a9a;--card:#2b2b2b;--bd:#3a3a3a;--ac:#e0764a;--user:#2f2f2f}}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;display:flex;flex-direction:column;height:100dvh}
header{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;padding-top:max(10px,env(safe-area-inset-top));border-bottom:1px solid var(--bd)}
header b{font-size:17px}
.hbtn{background:transparent;color:var(--mut);border:1px solid var(--bd);border-radius:10px;padding:6px 12px;font:inherit;font-size:14px;cursor:pointer}
#chat{flex:1;overflow-y:auto;padding:16px}
.wrap{max-width:760px;margin:0 auto}
.msg{display:flex;margin:14px 0}
.msg.user{justify-content:flex-end}
.bubble{max-width:88%;white-space:pre-wrap;word-wrap:break-word;overflow-wrap:anywhere}
.user .bubble{background:var(--user);padding:10px 14px;border-radius:18px}
.bot .bubble{padding:2px 0}
.bubble pre{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:10px;overflow-x:auto;margin:8px 0;white-space:pre}
.bubble code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:14px}
.bubble :not(pre)>code{background:var(--card);border:1px solid var(--bd);border-radius:6px;padding:1px 5px}
.err{color:var(--ac)}
details{margin-top:8px;color:var(--mut);font-size:13px;white-space:pre-wrap}
summary{cursor:pointer}
.think{display:flex;align-items:center;gap:10px;color:var(--mut);font-size:14px}
.pulse{flex:none;width:14px;height:14px;border-radius:50%;background:#e0482b;animation:pulse 1.2s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(.6);opacity:.55}50%{transform:scale(1.15);opacity:1;box-shadow:0 0 14px rgba(224,72,43,.7)}}
#welcome{text-align:center;margin-top:12vh}
#welcome h1{font-size:28px;margin:0 0 6px}
.chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:18px}
.chip{background:var(--card);border:1px solid var(--bd);border-radius:99px;padding:8px 14px;font:inherit;font-size:14px;color:var(--fg);cursor:pointer}
footer{padding:10px 16px;padding-bottom:max(12px,env(safe-area-inset-bottom))}
.composer{max-width:760px;margin:0 auto;display:flex;align-items:flex-end;gap:8px;background:var(--card);border:1px solid var(--bd);border-radius:24px;padding:8px 8px 8px 16px}
textarea{flex:1;border:0;outline:0;resize:none;background:transparent;color:var(--fg);font:inherit;max-height:180px;padding:6px 0}
#send{width:38px;height:38px;border-radius:50%;border:0;background:var(--ac);color:#fff;font-size:18px;cursor:pointer}
#send:disabled{opacity:.4;cursor:default}
.note{text-align:center;color:var(--mut);font-size:12px;margin-top:6px}
dialog{background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:16px;padding:20px;width:min(92vw,360px)}
dialog::backdrop{background:rgba(0,0,0,.5)}
dialog input{width:100%;font:inherit;color:var(--fg);background:var(--bg);border:1px solid var(--bd);border-radius:10px;padding:10px;margin:10px 0}
dialog button{font:inherit;background:var(--ac);color:#fff;border:0;border-radius:10px;padding:9px 16px;cursor:pointer}
</style></head><body>
<header><b>IA autonome</b><div><button class="hbtn" id="lock">Mot de passe</button> <button class="hbtn" id="new">Nouvelle conversation</button></div></header>
<div id="chat"><div class="wrap" id="msgs"></div></div>
<footer>
<div class="composer"><textarea id="in" rows="1" placeholder="Écrivez votre message…"></textarea><button id="send" title="Envoyer">↑</button></div>
<div class="note">L’agent peut se tromper. Vérifiez les informations importantes.</div>
</footer>
<dialog id="dlg"><form method="dialog" id="dform"><b>Mot de passe</b><p style="margin:6px 0;color:var(--mut);font-size:14px">Saisissez votre APP_TOKEN. Il reste seulement dans cet onglet.</p><input id="tok" type="password" autocomplete="off"><button>Valider</button></form></dialog>
<script>
const $=s=>document.querySelector(s);
const msgs=$('#msgs'),chat=$('#chat'),input=$('#in'),sendBtn=$('#send'),dlg=$('#dlg');
let history=[];try{history=JSON.parse(localStorage.getItem('chat')||'[]')}catch(e){}
let busy=false,timer=null;
const SUGGEST=['Cherche la capitale de l’Australie','Résume l’actualité sur l’énergie solaire','Explique-moi comment fonctionne une batterie'];

function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function thinking(t){return '<span class="think"><span class="pulse"></span><span>'+esc(t)+'</span></span>';}
function md(s){
  let h=esc(s);
  h=h.replace(/```([\s\S]*?)```/g,(m,c)=>'<pre><code>'+c.replace(/^\w*\n/,'')+'</code></pre>');
  h=h.replace(/`([^`\n]+)`/g,'<code>$1</code>');
  h=h.replace(/\*\*([^*\n]+)\*\*/g,'<strong>$1</strong>');
  return h;
}
function scroll(){chat.scrollTop=chat.scrollHeight;}
function addMsg(role,html){
  const m=document.createElement('div');m.className='msg '+role;
  const b=document.createElement('div');b.className='bubble';b.innerHTML=html;
  m.append(b);msgs.append(m);scroll();return b;
}
function save(){try{localStorage.setItem('chat',JSON.stringify(history.slice(-40)))}catch(e){}}
function welcome(){
  msgs.innerHTML='';
  const w=document.createElement('div');w.id='welcome';
  w.innerHTML='<h1>Comment puis-je aider ?</h1><div class="mut" style="color:var(--mut)">Un agent gratuit qui cherche et réfléchit pour vous.</div>';
  const c=document.createElement('div');c.className='chips';
  SUGGEST.forEach(t=>{const b=document.createElement('button');b.className='chip';b.textContent=t;b.onclick=()=>{input.value=t;send();};c.append(b);});
  w.append(c);msgs.append(w);
}
function render(){
  msgs.innerHTML='';
  if(!history.length){welcome();return;}
  history.forEach(h=>addMsg(h.role==='user'?'user':'bot',md(h.content)));
}
function getToken(){return sessionStorage.getItem('tok')||'';}
function askToken(){return new Promise(res=>{
  $('#tok').value='';dlg.showModal();
  dlg.addEventListener('close',()=>{const t=$('#tok').value.trim();if(t)sessionStorage.setItem('tok',t);res(t);},{once:true});
});}
$('#lock').onclick=()=>askToken();
$('#new').onclick=()=>{if(busy)return;history=[];save();render();};
input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,180)+'px';});
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
sendBtn.onclick=send;

async function send(){
  const text=input.value.trim();
  if(!text||busy)return;
  let token=getToken();if(!token)token=await askToken();if(!token)return;
  if(!history.length)msgs.innerHTML='';
  const prior=history.slice();
  history.push({role:'user',content:text});save();
  addMsg('user',esc(text));
  input.value='';input.style.height='auto';
  busy=true;sendBtn.disabled=true;
  const bot=addMsg('bot',thinking('Réflexion…'));
  const fail=m=>{bot.innerHTML='<span class="err">'+esc(m)+'</span>';busy=false;sendBtn.disabled=false;};
  try{
    const r=await fetch('/run',{method:'POST',headers:{'x-token':token,'content-type':'application/json'},body:JSON.stringify({goal:text,history:prior})});
    if(r.status===401){sessionStorage.removeItem('tok');history.pop();save();return fail('Mot de passe incorrect. Cliquez sur « Mot de passe » pour le ressaisir.');}
    if(!r.ok)return fail('Erreur serveur ('+r.status+').');
    const {id}=await r.json();
    timer=setInterval(async()=>{
      try{
        const d=await (await fetch('/runs/'+id,{headers:{'x-token':token}})).json();
        if(d.status==='running'){
          const last=d.steps.length?d.steps[d.steps.length-1]:'';
          bot.innerHTML=thinking(last?last.slice(0,140):'Réflexion…');
          scroll();return;
        }
        clearInterval(timer);
        const ans=d.result||'(réponse vide)';
        if(d.status==='done'){
          history.push({role:'assistant',content:ans});save();
          bot.innerHTML=md(ans);
          if(d.steps.length){const det=document.createElement('details');const sm=document.createElement('summary');sm.textContent='Voir les '+d.steps.length+' étapes';det.append(sm,document.createTextNode('\n'+d.steps.join('\n')));bot.append(det);}
          busy=false;sendBtn.disabled=false;scroll();
        }else{fail('Erreur : '+ans);}
      }catch(e){clearInterval(timer);fail('Connexion perdue.');}
    },1800);
  }catch(e){fail('Impossible de joindre le serveur.');}
}
render();
</script></body></html>"""


class Goal(BaseModel):
    goal: str
    history: List[dict] = []


def _auth(token):
    if token != os.getenv("APP_TOKEN", "changez-moi"):
        raise HTTPException(401, "Jeton invalide")


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def start(body: Goal, x_token: str = Header(None)):
    _auth(x_token)
    rid = uuid.uuid4().hex[:8]
    RUNS[rid] = {"status": "running", "steps": [], "result": None}

    def job():
        try:
            RUNS[rid]["result"] = run(body.goal, on_step=RUNS[rid]["steps"].append, history=body.history)
            RUNS[rid]["status"] = "done"
        except Exception as e:
            RUNS[rid].update(status="error", result=str(e))

    threading.Thread(target=job, daemon=True).start()
    return {"id": rid}


@app.get("/runs/{rid}")
def get(rid: str, x_token: str = Header(None)):
    _auth(x_token)
    if rid not in RUNS:
        raise HTTPException(404)
    return RUNS[rid]
