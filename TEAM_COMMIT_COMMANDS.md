# 🚀 Team Commit Commands - NIjam Project

Repository: https://github.com/chandu1234678/NIjam.git

## Team Members:
1. **You (Chandu - bc833498@gmail.com)** - Project Lead
2. **Kaushik (kaushikram51@gmail.com)** - Frontend Developer
3. **Abhinav (sb346@gmail.com)** - Backend Developer

---

## 📋 SETUP (Everyone does this FIRST)

```bash
# Navigate to your project folder
cd C:\Users\bc833\Downloads\fake-news-extension

# Initialize git (if not already done)
git init

# Add the remote repository
git remote add origin https://github.com/chandu1234678/NIjam.git

# Verify remote
git remote -v
```

---

## 👤 PERSON 1: You (Chandu - bc833498@gmail.com) - FIRST COMMIT

### Configure your git identity:
```bash
git config user.name "Chandu"
git config user.email "bc833498@gmail.com"
```

### Add and commit README:
```bash
# Stage files
git add README.md
git add LICENSE
git add .gitignore

# Commit with co-authors
git commit -m "docs: Initialize NIjam - AI-Powered Fact Checker

Initial project setup with README, LICENSE, and gitignore.

Co-authored-by: kaushikram51 <kaushikram51@gmail.com>
Co-authored-by: sb346 <sb346@gmail.com>"

# Push to GitHub
git push -u origin main
```

**⏰ Wait for confirmation, then tell Person 2 to start**

---

## 👤 PERSON 2: Kaushik (kaushikram51@gmail.com) - SECOND COMMIT (Extension UI)

### Configure your git identity:
```bash
git config user.name "Kaushik"
git config user.email "kaushikram51@gmail.com"
```

### Pull latest changes and add extension:
```bash
# Pull the latest code
git pull origin main

# Stage all extension files
git add extension/

# Commit
git commit -m "feat: Add Chrome extension UI and functionality

- Add extension manifest and popup UI
- Implement login, dashboard, history, and settings pages
- Add content script for page interaction
- Add background service worker with ONNX inference
- Implement fact-checking UI with verdict display
- Add WebSocket support for real-time updates

Features:
- User authentication and session management
- Claim verification with ML analysis
- Evidence display and source credibility
- Manipulation detection and highlighting
- History tracking and saved claims
- Offline inference capability

Co-authored-by: Chandu <bc833498@gmail.com>
Co-authored-by: Abhinav <sb346@gmail.com>"

# Push to GitHub
git push origin main
```

**⏰ Wait for confirmation, then tell Person 3 to start**

---

## 👤 PERSON 3: Abhinav (sb346@gmail.com) - THIRD COMMIT (Backend API)

### Configure your git identity:
```bash
git config user.name "Abhinav"
git config user.email "sb346@gmail.com"
```

### Pull latest changes and add backend:
```bash
# Pull the latest code
git pull origin main

# Stage backend files
git add backend/
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
- Domain-specific models
- Multilingual support
- ONNX export for browser inference

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
- /health - Health check

Co-authored-by: Chandu <bc833498@gmail.com>
Co-authored-by: Kaushik <kaushikram51@gmail.com>"

# Push to GitHub
git push origin main
```

**⏰ Wait for confirmation, then tell Person 1 to do final commit**

---

## 👤 PERSON 1: You (Chandu - bc833498@gmail.com) - FOURTH COMMIT (Documentation)

### Pull latest changes and add documentation:
```bash
# Pull the latest code
git pull origin main

# Stage documentation files
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
git add GIT_COMMIT_STRATEGY.md
git add QUICK_GIT_COMMANDS.txt
git add CONTRIBUTION_PLAN.md

# Commit
git commit -m "docs: Add comprehensive project documentation

- Add TODO roadmap with 280+ tasks across 9 phases
- Add executive summary and comprehensive review
- Add deployment guides for Render and production
- Add training guide for ML models
- Add project structure documentation
- Add VS Code settings and Kiro specs
- Add git contribution guides

Documentation includes:
- Complete feature roadmap
- ML model training instructions
- Deployment procedures
- API documentation
- Architecture overview
- Development guidelines

Co-authored-by: kaushikram51 <kaushikram51@gmail.com>
Co-authored-by: sb346 <sb346@gmail.com>"

# Push to GitHub
git push origin main
```

---

## ✅ VERIFICATION (Everyone can run this)

```bash
# Check commit history
git log --oneline

# Check contributors
git shortlog -sn

# Check total files
git ls-files | wc -l

# Check status
git status
```

### Expected Output:
```
4 commits total
3 contributors:
  - chandu1234678 (2 commits)
  - kaushikram51 (1 commit)
  - sb346 (1 commit)
```

---

## 🎯 Timeline

```
Time    Person              Action
─────────────────────────────────────────────────
0:00    chandu1234678      Push README + LICENSE
0:02    kaushikram51       Pull, push extension/
0:07    sb346              Pull, push backend/
0:12    chandu1234678      Pull, push docs
0:15    ✅ DONE!
```

---

## 🆘 Troubleshooting

### Problem: "fatal: remote origin already exists"
```bash
# Solution: Remove and re-add
git remote remove origin
git remote add origin https://github.com/chandu1234678/NIjam.git
```

### Problem: "Permission denied"
```bash
# Solution: Check if you're a collaborator
# Go to: https://github.com/chandu1234678/NIjam/settings/access
# Make sure kaushikram51 and sb346 are added
```

### Problem: "Merge conflict"
```bash
# Solution: Always pull before pushing
git pull origin main
# Then try push again
git push origin main
```

### Problem: "Nothing to commit"
```bash
# Solution: Check what's staged
git status
# Make sure you ran git add
```

---

## 📱 Communication Plan

1. **Use VS Code Live Share** for real-time collaboration
2. **Use WhatsApp/Discord** for coordination
3. **Announce before pushing**: "I'm pushing now!"
4. **Confirm after pushing**: "Done! Next person can go!"

---

## 🎉 After All Commits

Visit your repository:
https://github.com/chandu1234678/NIjam

You should see:
- ✅ 4 commits in history
- ✅ All 3 contributors in the graph
- ✅ ~220 files committed
- ✅ Professional commit messages
- ✅ Complete project structure

---

## 💡 Pro Tips

1. **Copy-paste the commands** - Don't type manually
2. **Wait for confirmation** - Don't rush
3. **Check git status** - Before and after each command
4. **Use git log** - To verify commits
5. **Communicate clearly** - "I'm done, next person go!"

---

Good luck team! 🚀
