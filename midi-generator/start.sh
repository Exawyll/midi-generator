#!/usr/bin/env bash
# start.sh — Lance backend (FastAPI) + frontend (Vite) avec logs unifiés
# Usage: ./start.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_UVICORN="$SCRIPT_DIR/../venv/bin/uvicorn"

# ── Couleurs ────────────────────────────────────────────────────────────────
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;90m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

log_info()  { echo -e "${GRAY}[start]${RESET}  $*"; }
log_ok()    { echo -e "${CYAN}[start]${RESET}  $*"; }
log_error() { echo -e "${RED}[start]${RESET}  $*" >&2; }

# ── Nettoyage à la sortie ────────────────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  log_info "Arrêt en cours..."
  [ -n "$BACKEND_PID"  ] && kill "$BACKEND_PID"  2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  log_info "Terminé."
}
trap cleanup EXIT INT TERM

# ── Header ──────────────────────────────────────────────────────────────────
echo -e ""
echo -e "${CYAN}${BOLD}  ╔══════════════════════════════╗${RESET}"
echo -e "${CYAN}${BOLD}  ║       MIDI.GEN  DEV          ║${RESET}"
echo -e "${CYAN}${BOLD}  ╚══════════════════════════════╝${RESET}"
echo -e ""

# ── Vérifications ────────────────────────────────────────────────────────────
if [ ! -f "$VENV_UVICORN" ]; then
  log_error "uvicorn introuvable : $VENV_UVICORN"
  log_error "Lance : ../venv/bin/pip install fastapi uvicorn anthropic midiutil pydantic"
  exit 1
fi

if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
  log_info "node_modules absent — installation npm..."
  ( cd "$SCRIPT_DIR/frontend" && npm install --silent )
  log_ok "npm install OK"
fi

# Charger .env si présent
if [ -f "$SCRIPT_DIR/backend/.env" ]; then
  log_info "Chargement de backend/.env"
  set -a; source "$SCRIPT_DIR/backend/.env"; set +a
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  log_error "ANTHROPIC_API_KEY non définie. Crée backend/.env (voir .env.example)"
  exit 1
fi

# ── Backend ──────────────────────────────────────────────────────────────────
log_info "Démarrage backend  → http://localhost:8000"
(
  cd "$SCRIPT_DIR/backend"
  "$VENV_UVICORN" main:app --reload --port 8000 2>&1
) | while IFS= read -r line; do
  echo -e "${CYAN}[backend] ${RESET} $line"
done &
BACKEND_PID=$!

# ── Frontend ─────────────────────────────────────────────────────────────────
log_info "Démarrage frontend → http://localhost:5173"
(
  cd "$SCRIPT_DIR/frontend"
  npm run dev 2>&1
) | while IFS= read -r line; do
  echo -e "${MAGENTA}[frontend]${RESET} $line"
done &
FRONTEND_PID=$!

echo ""
log_ok "Les deux services sont lancés. ${BOLD}Ctrl+C${RESET}${CYAN} pour arrêter."
echo ""

# Attendre que l'un des deux process se termine (compatible bash 3.2 macOS)
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done

# Identifier lequel a crashé
if ! kill -0 "$BACKEND_PID"  2>/dev/null; then
  log_error "Backend s'est arrêté de manière inattendue."
fi
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  log_error "Frontend s'est arrêté de manière inattendue."
fi
