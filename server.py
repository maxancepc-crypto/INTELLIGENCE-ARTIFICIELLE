"""API + interface web (déployable sur Render).
GET /  -> page web | POST /run {goal} -> id | GET /runs/{id} -> état"""
import os
import threading
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

load_dotenv()
from core import run  # noqa: E402

app = FastAPI(title="IA autonome gratuite")
RUNS = {}

PAGE = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IA autonome</title>
<style>
:root{--bg:#faf9f6;--fg:#1f1e1c;--mut:#6b6860;--card:#fff;--bd:#e4e1d9;--ac:#c4572b}
@media (prefers-color-scheme:dark){:root{--bg:#1b1a18;--fg:#f0eee8;--mut:#a09c92;--card:#252421;--bd:#3a3834;--ac:#e0764a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}
main{max-width:680px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:24px;margin:0 0 4px}.mut{color:var(--mut);font-size:14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:16px;margin:16px 0}
input,textarea{width:100%;font:inherit;color:var(--fg);background:var(--bg);border:1px solid var(--bd);border-radius:10px;padding:10px;margin:6px 0 12px}
textarea{min-height:90px;resize:vertical}
button{font:inherit;background:var(--ac);color:#fff;border:0;border-radius:10px;padding:10px 16px;cursor:pointer}
button:disabled{opacity:.5;cursor:default}
.step{font-size:14px;padding:6px 0;border-top:1px solid var(--bd);color:var(--mut);white-space:pre-wrap}
.step:first-child{border-top:0}
#result{white-space:pre-wrap}.err{color:var(--ac)}
</style></head><body><main>
<h1>IA autonome</h1>
<p class="mut">Donnez un objectif : l’agent cherche, réfléchit et écrit sa réponse étape par étape.</p>
<div class="card">
<label>Mot de passe (APP_TOKEN)</label>
<input id="tok" type="password" autocomplete="off">
<label>Objectif</label>
<textarea id="goal" placeholder="Ex. : Résume les 3 dernières actualités sur l’énergie solaire."></textarea>
<button id="go">Lancer l’agent</button>
<p class="mut" id="status"></p>
</div>
<div class="card" id="stepsCard" hidden><b>Étapes</b><div id="steps"></div></div>
<div class="card" id="resCard" hidden><b>Résultat</b><div id="result"></div></div>
</main>
<script>
const $=s=>document.querySelector(s);
let timer=null;
function setStatus(t,err){const s=$('#status');s.textContent=t;s.className=err?'mut err':'mut';}
$('#go').addEventListener('click',async()=>{
  const token=$('#tok').value.trim(), goal=$('#goal').value.trim();
  if(!token||!goal){setStatus('Renseignez le mot de passe et l’objectif.',true);return;}
  clearInterval(timer);
  $('#go').disabled=true;$('#steps').textContent='';$('#result').textContent='';
  $('#stepsCard').hidden=false;$('#resCard').hidden=true;
  setStatus('Démarrage… (la première requête peut prendre ~50 s si le service dormait)');
  try{
    const r=await fetch('/run',{method:'POST',headers:{'x-token':token,'content-type':'application/json'},body:JSON.stringify({goal})});
    if(r.status===401){throw new Error('Mot de passe incorrect.');}
    if(!r.ok){throw new Error('Erreur serveur ('+r.status+').');}
    const {id}=await r.json();
    setStatus('L’agent travaille…');
    timer=setInterval(async()=>{
      try{
        const p=await fetch('/runs/'+id,{headers:{'x-token':token}});
        const d=await p.json();
        $('#steps').replaceChildren(...d.steps.map(t=>{const e=document.createElement('div');e.className='step';e.textContent=t;return e;}));
        if(d.status!=='running'){
          clearInterval(timer);$('#go').disabled=false;
          $('#resCard').hidden=false;$('#result').textContent=d.result||'';
          setStatus(d.status==='done'?'Terminé.':'Erreur pendant l’exécution.',d.status!=='done');
        }
      }catch(e){clearInterval(timer);$('#go').disabled=false;setStatus('Connexion perdue.',true);}
    },2000);
  }catch(e){$('#go').disabled=false;setStatus(e.message,true);}
});
</script></body></html>"""


class Goal(BaseModel):
    goal: str


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
            RUNS[rid]["result"] = run(body.goal, on_step=RUNS[rid]["steps"].append)
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
