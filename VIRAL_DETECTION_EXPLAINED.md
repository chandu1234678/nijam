# HOW VIRAL DETECTION CHECKS WORK

## Step-by-Step Process

### 1. **User Submits Claim**
```
User types: "Breaking: Scientists confirm earth is flat"
```

### 2. **Generate Hash (SHA256)**
```python
# Normalize text: lowercase, strip whitespace
normalized = "breaking: scientists confirm earth is flat"

# Generate SHA256 hash
claim_hash = "445d918b9c29e9f0a8b7c6d5e4f3a2b1..."
```
**Why?** Same claim = same hash, even if typed differently

---

### 3. **Track in Time Windows**

The system maintains a **deque** (double-ended queue) of timestamps for each claim:

```python
claims = {
    "445d918b9c29e9f0...": deque([
        1713394800.123,  # timestamp 1
        1713394801.456,  # timestamp 2
        1713394802.789,  # timestamp 3
        ...
    ])
}
```

**Every time someone checks this claim, we add current timestamp**

---

### 4. **Count in Each Window**

For each window, count how many timestamps fall within it:

#### **5-Minute Window (300 seconds)**
```python
current_time = 1713395100.0
cutoff_time = current_time - 300  # 5 minutes ago

# Count timestamps >= cutoff_time
count_5min = 0
for timestamp in timestamps:
    if timestamp >= cutoff_time:
        count_5min += 1

# Result: count_5min = 51
```

#### **1-Hour Window (3600 seconds)**
```python
cutoff_time = current_time - 3600  # 1 hour ago
count_1hr = 51  # (all timestamps in last hour)
```

#### **24-Hour Window (86400 seconds)**
```python
cutoff_time = current_time - 86400  # 24 hours ago
count_24hr = 51  # (all timestamps in last 24 hours)
```

---

### 5. **Check Thresholds**

#### **Viral Detection (5-min window)**
```python
BASELINE_5MIN = 5        # Normal: 5 checks in 5 minutes
VIRAL_MULTIPLIER = 10    # Viral: 10x normal

viral_threshold = 5 * 10 = 50

if count_5min > 50:
    is_viral = True  # 🚨 VIRAL ALERT!
```

**Real Example:**
- Check #1-50: count_5min = 1-50 → Normal
- Check #51: count_5min = 51 → **VIRAL!** (51 > 50)

#### **Trending Detection (1-hr window)**
```python
BASELINE_1HR = 50
TRENDING_MULTIPLIER = 3

trending_threshold = 50 * 3 = 150

if count_1hr > 150:
    is_trending = True  # ⚠️ TRENDING!
```

---

### 6. **Calculate Velocity Score**

Normalize each window's count to 0-1 scale:

```python
# 5-min velocity (0-1)
velocity_5min = count_5min / (5 * 10)  # 51 / 50 = 1.02 → capped at 1.0
velocity_5min = min(1.0, 1.02) = 1.0

# 1-hr velocity (0-1)
velocity_1hr = count_1hr / (50 * 10)  # 51 / 500 = 0.102

# 24-hr velocity (0-1)
velocity_24hr = count_24hr / (500 * 10)  # 51 / 5000 = 0.010

# Weighted average (emphasize recent activity)
velocity_score = (
    velocity_5min * 0.5 +    # 50% weight on last 5 minutes
    velocity_1hr * 0.3 +      # 30% weight on last hour
    velocity_24hr * 0.2       # 20% weight on last 24 hours
)

velocity_score = (1.0 * 0.5) + (0.102 * 0.3) + (0.010 * 0.2)
velocity_score = 0.5 + 0.031 + 0.002 = 0.533
```

---

### 7. **Trigger Friction UX**

Based on velocity + other factors, calculate cooldown score:

```python
cooldown_score = (
    fake_probability^0.40 *      # 40% weight
    velocity_score^0.30 *         # 30% weight
    emotional_intensity^0.15 *    # 15% weight
    evidence_conflict^0.15        # 15% weight
)

# Example:
cooldown_score = (0.85^0.40) * (0.533^0.30) * (0.60^0.15) * (0.40^0.15)
cooldown_score = 0.936 * 0.851 * 0.926 * 0.897 = 0.662
```

**Friction Levels:**
- `cooldown_score > 0.80` → **VIRAL_PANIC** (10s countdown, full-screen)
- `cooldown_score > 0.55` → **HIGH_CONCERN** (5s countdown, friction card)
- `cooldown_score > 0.35` → **CAUTION** (warning banner)
- `cooldown_score ≤ 0.35` → **NORMAL** (no friction)

---

## Real-World Example

### Scenario: Fake news goes viral

**Timeline:**
```
10:00:00 - User 1 checks claim → count_5min=1, velocity=0.011, NORMAL
10:00:05 - User 2 checks claim → count_5min=2, velocity=0.022, NORMAL
10:00:10 - User 3 checks claim → count_5min=3, velocity=0.032, NORMAL
...
10:04:00 - User 50 checks claim → count_5min=50, velocity=0.530, NORMAL
10:04:05 - User 51 checks claim → count_5min=51, velocity=0.533, VIRAL! 🚨
```

**What happens at 10:04:05:**
1. System detects: 51 checks in last 5 minutes
2. Threshold exceeded: 51 > 50
3. Marks as VIRAL
4. Calculates cooldown score: 0.662
5. Triggers HIGH_CONCERN friction
6. User sees: **5-second countdown** before viewing result

---

## Why This Works

### **Sliding Windows**
- Old timestamps automatically expire
- At 10:05:01, the 10:00:00 timestamp is removed (>5 min old)
- Count drops back down if spread slows

### **Multiple Windows**
- **5-min**: Catches sudden viral spikes
- **1-hr**: Identifies sustained trending
- **24-hr**: Provides baseline context

### **Weighted Score**
- Recent activity (5-min) matters most (50% weight)
- Prevents false positives from old viral content
- Adapts to changing spread patterns

---

## Data Structure

### In-Memory (Development)
```python
{
    "claim_hash_1": deque([timestamp1, timestamp2, ...]),
    "claim_hash_2": deque([timestamp1, timestamp2, ...]),
    ...
}
```

### Database (Production)
```sql
CREATE TABLE velocity_records (
    id SERIAL PRIMARY KEY,
    claim_hash VARCHAR(64),
    claim_text TEXT,
    velocity_score FLOAT,
    count_5min INTEGER,
    count_1hr INTEGER,
    count_24hr INTEGER,
    is_viral BOOLEAN,
    is_trending BOOLEAN,
    cooldown_score FLOAT,
    cooldown_level VARCHAR(20),
    timestamp TIMESTAMP
);
```

---

## Key Insights

1. **Hash-based tracking**: Same claim = same hash, regardless of wording
2. **Time-based windows**: Sliding windows automatically expire old data
3. **Threshold detection**: Simple count comparison (count > threshold)
4. **Weighted scoring**: Recent activity weighted higher
5. **Multi-factor friction**: Combines velocity with ML confidence, emotion, evidence

**The system is REAL-TIME and AUTOMATIC** - no manual intervention needed!
