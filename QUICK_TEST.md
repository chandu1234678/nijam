# Quick Test Guide

## Step 1: Fix scikit-learn version

Open terminal in `backend` folder:

```bash
cd backend
venv\Scripts\activate
pip uninstall -y scikit-learn
pip install scikit-learn==1.6.1
```

## Step 2: Start Backend (WITHOUT --reload)

```bash
# Still in backend folder with venv activated
uvicorn app.main:app --port 8000
```

**Important:** No `--reload` flag to avoid WinError 1450

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Step 3: Run Test (New Terminal)

Open a NEW terminal in the project root:

```bash
python test_claim_simple.py
```

Or double-click: `RUN_TEST.bat`

## Expected Output

```
============================================================
TEST 1: Health Check
============================================================
✓ Backend is running: 200

============================================================
TEST 2: Velocity Stats Endpoint
============================================================
✓ Velocity tracking working

============================================================
TEST 3: Simple Claim Check
============================================================
Testing claim: 'The Earth is flat'
✓ Claim analyzed successfully

  Verdict: FAKE
  Confidence: 85.0%
  ML Score: 92.0%
  AI Score: 88.0%

  Velocity Tracking:
    - 5min checks: 1
    - 1hr checks: 1
    - Velocity score: 0.010
    - Is viral: False
    - Is trending: False

  Cooldown/Friction:
    - Level: NORMAL
    - Score: 0.000
    - Friction: none
```

## If Test Fails

### Backend not running
```
✗ Backend not running: Connection refused
```
**Fix:** Start backend in Step 2

### Timeout on first request
```
✗ Request timed out (>120s)
```
**Fix:** This is normal for first request (loading models). Run test again.

### scikit-learn version warning
```
InconsistentVersionWarning: Trying to unpickle estimator...
```
**Fix:** Run Step 1 again to fix version

### WinError 1450
```
OSError: [WinError 1450] Insufficient system resources
```
**Fix:** 
1. Stop backend (Ctrl+C)
2. Close other programs
3. Restart backend WITHOUT --reload:
   ```bash
   uvicorn app.main:app --port 8000
   ```

## Test Viral Detection

After basic tests pass, you can test viral detection:

```bash
python test_claim_simple.py
# When prompted, type 'y' to run viral test
```

This will submit the same claim 55 times. After ~50 checks, you should see:

```
✓ VIRAL ALERT TRIGGERED at check 51!
  5-min count: 51
  Velocity score: 1.020
  Cooldown level: VIRAL_PANIC
  Friction type: full_screen_interstitial
```

## Next Steps

Once tests pass:

1. **Load extension in browser:**
   - Chrome → Extensions → Load unpacked → Select `extension` folder
   - Click extension icon
   - Login (or skip)
   - Test a claim in the chat

2. **Check viral dashboard:**
   - After submitting claims, check: http://localhost:8000/viral/dashboard
   - Or open `extension/popup/viral.html` in the extension

3. **Monitor in real-time:**
   - Submit same claim multiple times in extension
   - Watch for viral/trending badges
   - See friction UX (countdown timers) when viral

## Troubleshooting

### Models not loading
Check RAM:
```bash
python -c "import psutil; print(f'Available: {psutil.virtual_memory().available/(1024**3):.1f}GB')"
```
Need at least 1GB free.

### Extension can't connect
Check `extension/popup/config.js`:
```javascript
const API = "http://localhost:8000";  // Should match backend
```

### Database errors
Reset database:
```bash
cd backend
del fake_news.db
alembic upgrade head
```
