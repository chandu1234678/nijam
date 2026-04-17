# VIRAL CHECK MECHANISM - DETAILED

## How Each Check Works

### Check #1 (First User)
```
Time: 10:00:00
Claim: "Earth is flat"
Hash: 445d918b...

Step 1: Generate hash
  └─ SHA256("earth is flat") = 445d918b...

Step 2: Add timestamp
  └─ claims["445d918b..."] = [1713394800.0]

Step 3: Count in windows
  └─ 5-min: 1 timestamp in last 300s = 1
  └─ 1-hr:  1 timestamp in last 3600s = 1
  └─ 24-hr: 1 timestamp in last 86400s = 1

Step 4: Check thresholds
  └─ 1 > 50? NO → Not viral
  └─ 1 > 150? NO → Not trending

Step 5: Calculate velocity
  └─ velocity_5min = 1/50 = 0.020
  └─ velocity_1hr = 1/500 = 0.002
  └─ velocity_24hr = 1/5000 = 0.0002
  └─ velocity_score = (0.020*0.5) + (0.002*0.3) + (0.0002*0.2) = 0.011

Result: ✓ NORMAL
```

---

### Check #25 (25th User)
```
Time: 10:02:00 (2 minutes later)
Same claim

Step 1: Hash matches existing
  └─ 445d918b... already tracked

Step 2: Add timestamp
  └─ claims["445d918b..."] = [
      1713394800.0,  # Check #1
      1713394805.0,  # Check #2
      ...
      1713394920.0   # Check #25 (current)
  ]

Step 3: Count in windows
  Current time: 1713394920.0
  5-min cutoff: 1713394620.0 (300s ago)
  
  Count timestamps >= cutoff:
  └─ 1713394800.0 >= 1713394620.0? YES ✓
  └─ 1713394805.0 >= 1713394620.0? YES ✓
  └─ ...
  └─ 1713394920.0 >= 1713394620.0? YES ✓
  
  Result: 25 timestamps in 5-min window

Step 4: Check thresholds
  └─ 25 > 50? NO → Not viral yet
  └─ 25 > 150? NO → Not trending yet

Step 5: Calculate velocity
  └─ velocity_score = 0.265

Result: ✓ NORMAL (but rising...)
```

---

### Check #51 (VIRAL TRIGGER!)
```
Time: 10:04:05 (4 minutes 5 seconds later)
Same claim

Step 1: Hash matches
  └─ 445d918b... (same claim)

Step 2: Add timestamp
  └─ claims["445d918b..."] = [
      1713394800.0,  # Check #1
      ...
      1713395045.0   # Check #51 (current)
  ]

Step 3: Count in windows
  Current time: 1713395045.0
  5-min cutoff: 1713394745.0 (300s ago)
  
  Count timestamps >= cutoff:
  └─ 1713394800.0 >= 1713394745.0? YES ✓
  └─ 1713394805.0 >= 1713394745.0? YES ✓
  └─ ...
  └─ 1713395045.0 >= 1713394745.0? YES ✓
  
  Result: 51 timestamps in 5-min window

Step 4: Check thresholds
  └─ 51 > 50? YES! 🚨 VIRAL DETECTED!
  └─ Log: "VIRAL CLAIM DETECTED: 445d918b... (51 in 5min)"

Step 5: Calculate velocity
  └─ velocity_5min = 51/50 = 1.02 → capped at 1.0
  └─ velocity_score = 0.533

Step 6: Calculate cooldown
  └─ fake_prob = 0.85 (from ML model)
  └─ velocity = 0.533
  └─ emotional = 0.60
  └─ evidence_conflict = 0.40
  
  └─ cooldown_score = (0.85^0.40) * (0.533^0.30) * (0.60^0.15) * (0.40^0.15)
  └─ cooldown_score = 0.662

Step 7: Determine friction
  └─ 0.662 > 0.55? YES → HIGH_CONCERN
  └─ Friction: 5-second countdown card

Result: 🚨 VIRAL ALERT! (5s friction)
```

---

### Check #52 (Still Viral)
```
Time: 10:04:10 (5 seconds later)
Same claim

Step 3: Count in windows
  Current time: 1713395050.0
  5-min cutoff: 1713394750.0
  
  Count: 52 timestamps in window
  
Step 4: Check thresholds
  └─ 52 > 50? YES! Still viral

Result: 🚨 VIRAL ALERT! (5s friction)
```

---

### Check #100 (6 minutes later)
```
Time: 10:10:00 (10 minutes total)
Same claim

Step 3: Count in windows
  Current time: 1713395400.0
  5-min cutoff: 1713395100.0 (only last 5 minutes)
  
  Count timestamps >= cutoff:
  └─ 1713394800.0 >= 1713395100.0? NO ✗ (too old, expired)
  └─ 1713394805.0 >= 1713395100.0? NO ✗ (too old, expired)
  └─ ...
  └─ 1713395045.0 >= 1713395100.0? NO ✗ (too old, expired)
  └─ 1713395050.0 >= 1713395100.0? NO ✗ (too old, expired)
  └─ ...
  └─ 1713395400.0 >= 1713395100.0? YES ✓ (recent)
  
  Result: Only recent checks count (spread has slowed)

Step 4: Check thresholds
  └─ If count < 50 → No longer viral

Result: ✓ NORMAL (spread slowed down)
```

---

## Visual Timeline

```
Time →
|-------|-------|-------|-------|-------|-------|
0min    1min    2min    3min    4min    5min    6min

Checks:
●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●
1  5  10 15 20 25 30 35 40 45 50 51 52 53 54 55 ...

                                    ↑
                                VIRAL!
                            (51st check)

5-min window at check #51:
[--------------------------------]
 All 51 checks fall within this window
 
5-min window at check #100 (6 min later):
                              [--------------------------------]
                               Only recent checks count
                               Old checks expired
```

---

## Key Mechanisms

### 1. **Sliding Window**
```python
def _count_in_window(claim_hash, window_seconds, current_time):
    cutoff_time = current_time - window_seconds
    
    count = 0
    for timestamp in claims[claim_hash]:
        if timestamp >= cutoff_time:  # Only count recent
            count += 1
    
    return count
```

### 2. **Automatic Cleanup**
```python
def _cleanup_old_entries(current_time):
    cutoff_time = current_time - 86400  # 24 hours
    
    for claim_hash in claims:
        # Remove timestamps older than 24 hours
        while timestamps[0] < cutoff_time:
            timestamps.popleft()  # Remove oldest
```

### 3. **Threshold Detection**
```python
is_viral = (count_5min > BASELINE_5MIN * VIRAL_MULTIPLIER)
is_viral = (count_5min > 5 * 10)
is_viral = (count_5min > 50)
```

---

## Real Data Example

From our test:
```
Check #1:  count_5min=1,  velocity=0.011, NORMAL
Check #11: count_5min=11, velocity=0.117, NORMAL
Check #21: count_5min=21, velocity=0.223, NORMAL
Check #31: count_5min=31, velocity=0.330, NORMAL
Check #41: count_5min=41, velocity=0.436, NORMAL
Check #51: count_5min=51, velocity=0.533, VIRAL! 🚨
Check #52: count_5min=52, velocity=0.533, VIRAL! 🚨
Check #53: count_5min=53, velocity=0.534, VIRAL! 🚨
```

**Exactly as expected!** Threshold crossed at check #51.

---

## Why It's Effective

1. **Real-time**: Detects viral spread as it happens
2. **Automatic**: No manual monitoring needed
3. **Adaptive**: Windows slide, old data expires
4. **Accurate**: Multiple windows prevent false positives
5. **Scalable**: Hash-based, O(n) complexity per check
6. **Persistent**: Stores in database for analysis

**This is production-grade viral detection!**
