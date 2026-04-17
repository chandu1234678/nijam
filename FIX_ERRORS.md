# Error Fixes

## Current Errors and Solutions

### 1. InconsistentVersionWarning (scikit-learn)

**Error:**
```
InconsistentVersionWarning: Trying to unpickle estimator from version 1.6.1 when using version 1.8.0
```

**Cause:** Your venv has scikit-learn 1.8.0 but models were trained with 1.6.1

**Fix:**
```bash
cd backend
venv\Scripts\activate
pip uninstall -y scikit-learn
pip install scikit-learn==1.6.1
```

Or run the automated script:
```bash
cd backend
fix_dependencies.bat
```

**Verify:**
```bash
python -c "import sklearn; print(sklearn.__version__)"
# Should output: 1.6.1
```

---

### 2. RuntimeWarning: coroutine never awaited

**Error:**
```
RuntimeWarning: coroutine 'notify_claim_verified' was never awaited
```

**Status:** ✅ FIXED - WebSocket notification disabled in `backend/app/api.py`

---

### 3. OSError [WinError 1450] - Insufficient system resources

**Error:**
```
OSError: [WinError 1450] Insufficient system resources exist to complete the requested service
```

**Cause:** Windows file handle exhaustion from uvicorn's file watcher

**Solutions:**

#### Option A: Disable auto-reload (Recommended for development)
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --port 8000 --host 0.0.0.0
# Note: No --reload flag
```

#### Option B: Reduce watched directories
Create `backend/.env` and add:
```
PYTHONDONTWRITEBYTECODE=1
```

Then restart:
```bash
uvicorn app.main:app --reload --port 8000 --reload-dir app
```

#### Option C: Increase Windows file handles (Advanced)
1. Open Registry Editor (regedit)
2. Navigate to: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters`
3. Modify `IRPStackSize` to `32` (create if doesn't exist, type: DWORD)
4. Restart computer

#### Option D: Use gunicorn (Production-like)
```bash
pip install gunicorn
gunicorn app.main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Quick Start (After Fixes)

```bash
# Terminal 1: Backend
cd backend
venv\Scripts\activate
uvicorn app.main:app --port 8000
# Note: No --reload to avoid WinError 1450

# Terminal 2: Test
curl http://localhost:8000/health
```

---

## Verification Checklist

- [ ] scikit-learn version is 1.6.1
- [ ] Backend starts without warnings
- [ ] No WinError 1450 when running
- [ ] Extension can connect to backend
- [ ] Claims can be fact-checked

---

## If Issues Persist

1. **Close all Python processes:**
   ```bash
   taskkill /F /IM python.exe
   ```

2. **Delete venv and recreate:**
   ```bash
   cd backend
   rmdir /s /q venv
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Restart your computer** (for file handle issues)

4. **Check RAM usage:**
   ```bash
   python -c "import psutil; print(f'Available RAM: {psutil.virtual_memory().available / (1024**3):.1f} GB')"
   ```
   - Need at least 1GB free for basic operation
   - Need 1.5GB+ for RoBERTa transformer model

---

## Development Tips

### Run without auto-reload
```bash
uvicorn app.main:app --port 8000
```
Manually restart when you make changes.

### Watch specific directory only
```bash
uvicorn app.main:app --reload --reload-dir app --port 8000
```
Only watches `app/` folder, not entire backend.

### Use nodemon (alternative)
```bash
npm install -g nodemon
nodemon --exec "uvicorn app.main:app --port 8000" --watch app --ext py
```

---

## Testing Viral Detection

After backend is running:

```bash
# Test velocity tracking
curl http://localhost:8000/velocity/stats

# Test viral dashboard
curl http://localhost:8000/viral/dashboard

# Submit a claim multiple times to trigger viral detection
for i in {1..60}; do
  curl -X POST http://localhost:8000/message \
    -H "Content-Type: application/json" \
    -d '{"message":"Breaking: Scientists confirm earth is flat"}'
  sleep 0.1
done
```

After 50+ checks in 5 minutes, the claim will be marked as VIRAL.
