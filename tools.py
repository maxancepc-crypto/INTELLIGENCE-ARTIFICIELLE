"""Outils de l'agent. Tout est confiné au dossier workspace/ : pas de shell, pas d'exécution de code."""
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

WORKSPACE = (Path(__file__).resolve().parent.parent / "workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)
MAX_OUT = 6000


def _safe_path(name: str) -> Path:
    p = (WORKSPACE / name).resolve()
    if WORKSPACE not in p.parents and p != WORKSPACE:
        raise ValueError("Chemin hors du workspace refusé.")
    return p


def web_search(query: str, max_results: int = 5) -> str:
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
    with DDGS() as d:
        res = list(d.text(query, max_results=int(max_results)))
    return "\n".join(f"- {r.get('title')} | {r.get('href')}\n  {r.get('body')}" for r in res) or "Aucun résultat."


def fetch_url(url: str) -> str:
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        return "URL invalide."
    try:  # bloque le réseau interne (SSRF)
        ip = ipaddress.ip_address(socket.gethostbyname(u.hostname))
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return "Adresse interne refusée."
    except Exception:
        return "Hôte introuvable."
    r = requests.get(url, timeout=15, headers={"User-Agent": "ia-autonome/1.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style", "nav", "footer"]):
        t.decompose()
    return " ".join(soup.get_text(" ").split())[:MAX_OUT]


def list_files() -> str:
    return "\n".join(sorted(str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob("*") if p.is_file())) or "(vide)"


def read_file(path: str) -> str:
    return _safe_path(path).read_text(encoding="utf-8")[:MAX_OUT]


def write_file(path: str, content: str) -> str:
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Écrit : {path} ({len(content)} caractères)"


def remember(note: str) -> str:
    with open(_safe_path("memory.md"), "a", encoding="utf-8") as f:
        f.write(f"- {note}\n")
    return "Noté dans la mémoire."


TOOLS = {
    "web_search": (web_search, "query, max_results(optionnel) : recherche web"),
    "fetch_url": (fetch_url, "url : lit le texte d'une page web"),
    "list_files": (list_files, "aucun argument : liste les fichiers du workspace"),
    "read_file": (read_file, "path : lit un fichier du workspace"),
    "write_file": (write_file, "path, content : écrit un fichier du workspace"),
    "remember": (remember, "note : ajoute une note à la mémoire persistante"),
}
