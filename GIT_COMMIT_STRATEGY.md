# Git Commit Strategy - 3 Contributors

This guide splits the initial commits into 3 parts so each team member can contribute to the repository.

## Prerequisites (Do this ONCE before starting)

```bash
# Initialize git repository (if not already done)
git init

# Add your new remote repository
git remote add origin <YOUR_NEW_REPO_URL>

# Configure git (each person should use their own name/email)
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

---

## 👤 CONTRIBUTOR 1: Project Setup & Documentation

**What you'll commit:** README, documentation files, configuration, and project structure

### Commands for Contributor 1:

```bash
# Stage documentation and config files
git add README.md
git add LICENSE
git add .gitignore
git add TODO.md
git add EXECUTIVE_SUMMARY.md
git add COMPREHENSIVE_REVIEW.md
git add DEPLOYMENT.md
git add DEPLOYMENT_GUIDE.md
git add TRAINING_GUIDE.md
git add PROJECT_STRUCTURE.md
git add commands.txt
git add render.yaml
git add .vscode/
git add .kiro/

# Commit
git commit -m "docs: Add project documentation and configuration

- Add comprehensive README with project overview
- Add LICENSE file
- Add TODO roadmap with 280+ tasks
- Add deployment guides and training documentation
- Add project structure and configuration files
- Configure VS Code settings and Kiro specs

Co-authored-by: Contributor 2 <contributor2@email.com>
Co-authored-by: Contributor 3 <contributor3@email.com>"

# Push to main branch
git push -u origin main
```

---

## 👤 CONTRIBUTOR 2: Frontend/Extension

**What you'll commit:** Chrome extension UI, popup pages, content scripts, and frontend assets

### Commands for Contributor 2:

```bash
# Pull the latest changes
git pull origin main

# Create a new branch
git checkout -b feat/extension-ui

# Stage all extension files
git add extension/

# Commit
git commit -m "feat: Add Chrome extension UI and functionality

- Add extension manifest and configuration
- Add popup UI (login, dashboard, history, settings, detail pages)
- Add content script for page interaction
- Add background service worker with ONNX inference
- Add Tailwind CSS configuration and shared styles
- Implement fact-checking UI with verdict display
- Add WebSocket support for real-time updates

Features:
- User authentication and session management
- Claim verification with ML analysis
- Evidence display and source credibility
- Manipulation detection and highlighting
- History tracking and saved claims
- Settings and user preferences
- Offline inference capability (ONNX)

Co-authored-by: Contributor 1 <contributor1@email.com>
Co-authored-by: Contributor 3 <contributor3@email.com>"

# Push branch
git push -u origin feat/extension-ui

# Merge to main (or create PR)
git checkout main
git merge feat/extension-ui
git push origin main
```

---

## 👤 CONTRIBUTOR 3: Backend API & ML Models

**What you'll commit:** FastAPI backend, ML models, database, and training scripts

### Commands for Contributor 3:

```bash
# Pull the latest changes
git pull origin main

# Create a new branch
git checkout -b feat/backend-api

# Stage backend files
git add backend/

# Stage database file
git add database.py

# Commit
git commit -m "feat: Add FastAPI backend with ML pipeline

Backend API:
- FastAPI application with 20+ endpoints
- JWT authentication and user management
- PostgreSQL database with Alembic migrations
- WebSocket support for real-time notifications
- Rate limiting and caching (Redis)
- Prometheus metrics and monitoring
- Email notifications (Brevo API)

ML Pipeline:
- TF-IDF + Logistic Regression (96.63% accuracy)
- DeBERTa transformer model support
- Evidence search (Tavily API)
- AI analysis (Gemini, Groq, Cerebras)
- Image verification (Gemini Vision)
- Manipulation detection
- SHAP explainability
- Velocity tracking for viral detection
- Semantic clustering
- Domain classification
- Wikidata entity verification

Training Scripts:
- Multi-dataset training (273k+ samples)
- Calibrated classifier with isotonic regression
- Adversarial testing
- Ablation studies
- Domain-specific models
- Multilingual support
- ONNX export for browser inference

Database Models:
- Users, ChatSessions, ChatMessages
- ClaimRecords, VelocityRecords
- UserFeedback, PasswordResetOTP
- ABTest, ABTestAssignment, ABTestEvent

API Routes:
- /auth - Authentication (signup, login, Google OAuth)
- /message - Claim verification
- /history - User history
- /stats - System statistics
- /explain - Explainability
- /review - Review queue
- /ab - A/B testing
- /metrics - Prometheus metrics
- /ws - WebSocket connections
- /cache - Cache management
- /quota - Usage quotas
- /analytics - Analytics dashboard
- /health - Health check

Co-authored-by: Contributor 1 <contributor1@email.com>
Co-authored-by: Contributor 2 <contributor2@email.com>"

# Push branch
git push -u origin feat/backend-api

# Merge to main (or create PR)
git checkout main
git merge feat/backend-api
git push origin main
```

---

## Alternative: All Contributors Push Simultaneously

If you want all three contributors to push at the same time (for equal contribution), use this approach:

### Setup (All contributors do this first):

```bash
# Clone the empty repository
git clone <YOUR_NEW_REPO_URL>
cd <repo-name>

# Copy all project files into the cloned directory
# (Copy from your current project folder)

# Configure git with your name
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Contributor 1 - Initial Commit:

```bash
git add README.md LICENSE .gitignore
git commit -m "docs: Initialize project with README and license"
git push origin main
```

### Contributor 2 - Extension (wait for Contributor 1):

```bash
git pull origin main
git add extension/
git commit -m "feat: Add Chrome extension UI

Co-authored-by: Contributor 1 <contributor1@email.com>
Co-authored-by: Contributor 3 <contributor3@email.com>"
git push origin main
```

### Contributor 3 - Backend (wait for Contributor 2):

```bash
git pull origin main
git add backend/ database.py
git commit -m "feat: Add backend API and ML models

Co-authored-by: Contributor 1 <contributor1@email.com>
Co-authored-by: Contributor 2 <contributor2@email.com>"
git push origin main
```

### Contributor 1 - Documentation (wait for Contributor 3):

```bash
git pull origin main
git add TODO.md EXECUTIVE_SUMMARY.md COMPREHENSIVE_REVIEW.md DEPLOYMENT.md DEPLOYMENT_GUIDE.md TRAINING_GUIDE.md PROJECT_STRUCTURE.md commands.txt render.yaml .vscode/ .kiro/
git commit -m "docs: Add comprehensive documentation

Co-authored-by: Contributor 2 <contributor2@email.com>
Co-authored-by: Contributor 3 <contributor3@email.com>"
git push origin main
```

---

## Important Notes:

1. **Replace placeholders:**
   - `<YOUR_NEW_REPO_URL>` with your actual GitHub/GitLab repository URL
   - `<contributor1@email.com>` with actual email addresses

2. **Co-authored-by format:**
   - Use the format: `Co-authored-by: Name <email@example.com>`
   - This gives credit to all contributors in GitHub's contribution graph

3. **Before pushing:**
   - Make sure `.env` and `.env.local` are in `.gitignore` (they already are)
   - Check that `backend/fake_news.db` is ignored (it is)
   - Verify no sensitive API keys are committed

4. **Branch strategy:**
   - Option 1: Each person creates a branch and merges (cleaner)
   - Option 2: Push directly to main sequentially (faster)

5. **GitHub contribution graph:**
   - All commits will show up on each contributor's profile
   - Co-authored commits count for all listed contributors

---

## Quick Reference - File Distribution:

**Contributor 1 (Docs):**
- README.md, LICENSE, .gitignore
- TODO.md, EXECUTIVE_SUMMARY.md, COMPREHENSIVE_REVIEW.md
- DEPLOYMENT.md, DEPLOYMENT_GUIDE.md, TRAINING_GUIDE.md
- PROJECT_STRUCTURE.md, commands.txt
- render.yaml, .vscode/, .kiro/

**Contributor 2 (Frontend):**
- extension/ (all files)
  - manifest.json, content.js
  - popup/ (HTML, JS, CSS)
  - background/ (service workers)
  - icons/

**Contributor 3 (Backend):**
- backend/ (all files)
  - app/ (API routes, models, analysis)
  - training/ (ML training scripts)
  - alembic/ (database migrations)
  - tests/
  - data/ (models)
  - requirements.txt, runtime.txt, Procfile
- database.py

---

## Verification:

After all commits, verify with:

```bash
# Check commit history
git log --oneline --graph --all

# Check contributors
git shortlog -sn

# Check file distribution
git ls-files | wc -l
```

Good luck with your collaborative project! 🚀
