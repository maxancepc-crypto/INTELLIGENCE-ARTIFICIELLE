"""Boucle autonome : planifier -> agir -> observer -> recommencer, jusqu'à 'finish' ou MAX_STEPS."""
import json
import os
import re

import llm
import tools

SYSTEM = """Tu es un agent autonome. Tu poursuis l'objectif de l'utilisateur étape par étape.
À chaque tour, réponds UNIQUEMENT par un objet JSON :
{"thought": "raisonnement bref", "action": "<outil ou finish>", "args": {...}}
Outils disponibles :
%s
Quand l'objectif est atteint, utilise l'action "finish" avec args {"answer": "résultat final"}.
Règles : une seule action par tour, pas de texte hors JSON, sauvegarde les livrables avec write_file,
et n'invente jamais de faits : appuie-toi sur la recherche web."""


def _parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("Pas de JSON dans la réponse")
    return json.loads(m.group(0))


def run(goal: str, on_step=print, history=None) -> str:
    max_steps = int(os.getenv("MAX_STEPS", "15"))
    catalog = "\n".join(f"- {n}: {d}" for n, (_, d) in tools.TOOLS.items())
    mem = ""
    try:
        mem = tools.read_file("memory.md")
    except Exception:
        pass
    hist = "\n".join(
        f"{'Utilisateur' if h.get('role') == 'user' else 'Assistant'} : {str(h.get('content', ''))[:1500]}"
        for h in (history or [])[-10:]
    )
    msgs = [
        {"role": "system", "content": SYSTEM % catalog},
        {"role": "user", "content": f"Objectif : {goal}\n\nHistorique de la conversation :\n{hist or '(aucun)'}\n\nMémoire :\n{mem or '(vide)'}"},
    ]
    for step in range(1, max_steps + 1):
        raw = llm.chat(msgs)
        msgs.append({"role": "assistant", "content": raw})
        try:
            act = _parse(raw)
            name, args = act.get("action"), act.get("args", {}) or {}
        except Exception as e:
            msgs.append({"role": "user", "content": f"Réponse invalide ({e}). Réponds en JSON uniquement."})
            continue
        on_step(f"[{step}] {act.get('thought', '')} -> {name}")
        if name == "finish":
            return str(args.get("answer", ""))
        if name not in tools.TOOLS:
            obs = f"Outil inconnu : {name}"
        else:
            try:
                obs = tools.TOOLS[name][0](**args)
            except Exception as e:
                obs = f"Erreur : {e}"
        msgs.append({"role": "user", "content": f"Résultat de {name} :\n{str(obs)[:tools.MAX_OUT]}"})
        msgs = msgs[:2] + msgs[-12:]  # fenêtre glissante pour rester dans le contexte
    return "Arrêt : nombre maximal d'étapes atteint."
