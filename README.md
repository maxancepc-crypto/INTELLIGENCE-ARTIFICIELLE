# IA autonome gratuite

Un agent qui reçoit un objectif, planifie, cherche sur le web, lit et écrit des fichiers, puis s'arrête de lui-même.
Il fonctionne sans abonnement : modèle local (Ollama) ou API gratuite (Groq, OpenRouter, Gemini).

## Fonctionnement
`planifier → agir (outil) → observer → recommencer` jusqu'à `finish` ou `MAX_STEPS`.

Outils : `web_search`, `fetch_url`, `list_files`, `read_file`, `write_file`, `remember`.
Sécurité : pas de shell, fichiers confinés à `workspace/`, accès réseau interne bloqué, nombre d'étapes limité.

## Démarrage local (100 % gratuit)
```bash
# 1. Installer Ollama (https://ollama.com) puis :
ollama pull llama3.2
# 2. Installer le projet
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 3. Lancer
python main.py "Résume les 3 dernières actualités sur l'énergie solaire et écris-les dans veille.md"
```
Les résultats sont dans `workspace/`.

## Hébergement gratuit
- **GitHub Actions** : ajoutez le secret `LLM_API_KEY` (clé Groq gratuite) puis lancez le workflow « Agent autonome » (manuel ou planifié). Le dossier `workspace/` est récupérable en artefact.
- **Render (offre gratuite)** : déployez depuis ce dépôt (`render.yaml` inclus), renseignez `LLM_API_KEY` et `APP_TOKEN`.
  ```bash
  curl -X POST $URL/run -H "x-token: $APP_TOKEN" -H "content-type: application/json" -d '{"goal":"..."}'
  curl $URL/runs/<id> -H "x-token: $APP_TOKEN"
  ```
  L'offre gratuite se met en veille et efface les fichiers à chaque redémarrage : adaptée aux tests.

## Limites honnêtes
- « Gratuit » dépend des quotas des fournisseurs ; un petit modèle local est moins fiable qu'un grand modèle.
- L'autonomie est bornée volontairement : ne retirez pas `MAX_STEPS`.
