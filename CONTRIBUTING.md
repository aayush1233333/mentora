# Contributing to Mentora

Thank you for your interest in contributing! This guide covers everything you need to get started.

---

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- A webcam (for AI testing)
- Supabase project

### Quick start
```bash
git clone https://github.com/your-org/mentora.git
cd mentora
./start.sh   # Mac/Linux
start.bat    # Windows
```

---

## Project Structure

```
mentora/
├── ai_model/       Python: MediaPipe + EAR/MAR + CNN-LSTM
├── backend/        FastAPI: REST + WebSocket + Supabase
└── frontend/       React 18 + Tailwind CSS
```

---

## Branching Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production – protected, CI required |
| `develop` | Integration branch |
| `feature/*` | New features |
| `fix/*` | Bug fixes |
| `chore/*` | Deps, tooling, docs |

```bash
git checkout develop
git checkout -b feature/my-feature
# ... commit work ...
git push origin feature/my-feature
# Open PR → develop
```

---

## Coding Standards

### Python (backend + ai_model)

- **Formatter**: `ruff format .`
- **Linter**: `ruff check .`
- **Type hints**: Required on all public functions
- **Docstrings**: Google style for public modules and classes
- Max line length: 100

```bash
cd backend
pip install ruff
ruff check . --fix
ruff format .
```

### TypeScript/JavaScript (frontend)

- **Linter**: ESLint (see `.eslintrc.json`)
- **Formatter**: Prettier (optional, configure per team)
- Component props: Always destructure in the function signature
- Hooks: Prefix with `use`, place in `src/hooks/`

```bash
cd frontend
npm run lint
```

---

## Testing

### Backend
```bash
cd backend
pip install pytest pytest-cov
pytest tests/ -v --cov=. --cov-report=term-missing
```

All new backend features must include at least one test in `backend/tests/test_mentora.py`.

### Frontend
```bash
cd frontend
npm test -- --watchAll=false
```

---

## AI Model Changes

When modifying `ai_model/`:

1. Run the existing detector tests (`pytest` as above)
2. Test with a real webcam: `python data_collector.py --label normal --duration 30`
3. If adding new features to the detector, update `FEATURE_DIM` in `cnn_lstm_model.py` accordingly
4. Re-run `python train.py` if the feature vector shape changes — old weights are incompatible

---

## Pull Request Checklist

- [ ] Tests pass locally (`pytest` + `npm test`)
- [ ] Lint passes (`ruff check .` + `npm run lint`)
- [ ] New features have at least one test
- [ ] `.env.example` updated if new env vars added
- [ ] `API_DOCS.md` updated if API surface changed
- [ ] `README.md` updated if setup steps changed
- [ ] PR description explains *why*, not just *what*

---

## Reporting Issues

Please include:
- OS and Python/Node versions
- Steps to reproduce
- Expected vs actual behaviour
- Relevant log output (from `uvicorn` or browser console)

---

## Areas Most Needing Contributions

- More breathing exercise techniques
- PyTorch model variant (alternative to TensorFlow)
- Mobile-responsive improvements on small screens
- i18n / internationalisation
- Additional wellness tip categories
- Offline mode (Service Worker caching)
- VS Code extension for break reminders

---

## Code of Conduct

Be respectful, constructive, and inclusive. Harassment of any kind will not be tolerated.

