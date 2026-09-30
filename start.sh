#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Mentora – Local Development Startup Script
# Usage:  chmod +x start.sh && ./start.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}"
echo "  ███╗   ███╗███████╗███╗   ██╗████████╗ ██████╗ ██████╗  █████╗ "
echo "  ████╗ ████║██╔════╝████╗  ██║╚══██╔══╝██╔═══██╗██╔══██╗██╔══██╗"
echo "  ██╔████╔██║█████╗  ██╔██╗ ██║   ██║   ██║   ██║██████╔╝███████║"
echo "  ██║╚██╔╝██║██╔══╝  ██║╚██╗██║   ██║   ██║   ██║██╔══██╗██╔══██║"
echo "  ██║ ╚═╝ ██║███████╗██║ ╚████║   ██║   ╚██████╔╝██║  ██║██║  ██║"
echo "  ╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${GREEN}  Cognitive Fatigue & Well-Being Tracker${NC}\n"

# ── Prerequisites check ───────────────────────────────────────────────────────
check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    echo -e "${RED}✗ $1 is required but not installed.${NC}"
    exit 1
  fi
}

check_cmd python3
check_cmd node
check_cmd npm

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
NODE_VER=$(node --version | tr -d 'v' | cut -d. -f1)

if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
  echo -e "${GREEN}✓ Python $PYTHON_VER${NC}"
else
  echo -e "${YELLOW}⚠ Python $PYTHON_VER detected (3.11+ recommended)${NC}"
fi

if [ "$NODE_VER" -ge 18 ]; then
  echo -e "${GREEN}✓ Node v$(node --version | tr -d 'v')${NC}"
else
  echo -e "${YELLOW}⚠ Node v$(node --version | tr -d 'v') (v18+ recommended)${NC}"
fi

# ── Environment files ─────────────────────────────────────────────────────────
if [ ! -f "backend/.env" ]; then
  echo -e "\n${YELLOW}⚠  backend/.env not found – copying from example…${NC}"
  cp backend/.env.example backend/.env
  echo -e "${YELLOW}   Edit backend/.env and add your Supabase + OpenAI credentials.${NC}"
fi

if [ ! -f "frontend/.env" ]; then
  echo -e "${YELLOW}⚠  frontend/.env not found – copying from example…${NC}"
  cp frontend/.env.example frontend/.env
  echo -e "${YELLOW}   Edit frontend/.env and add your Supabase web configuration.${NC}"
fi

# ── Backend setup ─────────────────────────────────────────────────────────────
echo -e "\n${BLUE}[Backend]${NC} Setting up Python environment…"
cd backend

if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Start backend in background
echo -e "${BLUE}[Backend]${NC} Starting FastAPI on http://localhost:8000 …"
uvicorn main:app --reload --port 8000 --log-level warning &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID $BACKEND_PID)${NC}"

cd ..

# ── Frontend setup ────────────────────────────────────────────────────────────
echo -e "\n${BLUE}[Frontend]${NC} Installing Node dependencies…"
cd frontend

if [ ! -d "node_modules" ]; then
  npm install --legacy-peer-deps --silent
fi
echo -e "${GREEN}✓ Frontend dependencies ready${NC}"

echo -e "${BLUE}[Frontend]${NC} Starting React dev server on http://localhost:3000 …\n"

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}Frontend:${NC}  http://localhost:3000"
echo -e "  ${GREEN}API:${NC}       http://localhost:8000"
echo -e "  ${GREEN}API Docs:${NC}  http://localhost:8000/docs"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
echo -e "Press ${YELLOW}Ctrl+C${NC} to stop both servers.\n"

# Cleanup on exit
trap "echo -e '\n${YELLOW}Stopping servers…${NC}'; kill $BACKEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

npm start

