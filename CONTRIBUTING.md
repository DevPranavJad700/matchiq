# Contributing to MatchIQ

Thank you for your interest in contributing to MatchIQ!

## Development Setup

1. **Fork and Clone the Repository:**
   ```bash
   git clone https://github.com/DevPranavJad700/matchiq.git
   cd matchiq
   ```

2. **Environment & Backend:**
   ```bash
   cp .env.example .env
   pip install -r backend/requirements.txt
   ```

3. **Running Database & Boot:**
   ```bash
   python scripts/bootstrap.py
   python -m alembic upgrade head
   ```

4. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   ```

---

## Testing Guidelines

Before opening a pull request, ensure all tests pass cleanly:

```bash
# Backend pytest suite
$env:DATABASE_URL="sqlite:///./matchiq.db"; python -m pytest backend/tests/ -v

# Frontend Vitest suite & TypeScript compilation
cd frontend
npm run test -- --run
npx tsc -b
```

---

## Pull Request Process

1. Create a feature branch (`git checkout -b feat/your-feature-name`).
2. Commit clear, descriptive messages (`git commit -m "feat(ml): add calibration curve computation"`).
3. Ensure no data leakage occurs in feature engineering logic (all rolling features must use `.shift(1)`).
4. Submit a Pull Request targeting the `main` branch.
