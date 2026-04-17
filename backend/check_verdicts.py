import requests, time

BASE = "http://127.0.0.1:8000"
tests = [
    ("flat earth (expect: fake)", "Scientists have confirmed the earth is flat and NASA has been lying for decades"),
    ("vaccine    (expect: real)", "COVID-19 vaccines have been approved by WHO and shown to be safe and effective"),
    ("conspiracy (expect: fake)", "The deep state is using 5G towers to control peoples minds"),
    ("real news  (expect: real)", "The WHO declared COVID-19 a pandemic in March 2020"),
]

print("\n" + "="*75)
print("CLAIM VERDICT TESTS")
print("="*75)

all_pass = True
for name, msg in tests:
    t0 = time.time()
    r = requests.post(f"{BASE}/message", json={"message": msg}, timeout=90)
    d = r.json()
    ms = int((time.time() - t0) * 1000)
    verdict   = d.get("verdict", "?")
    conf      = d.get("confidence", "?")
    debunked  = d.get("previously_debunked", False)
    ai_score  = round(d.get("ai_score", 0), 3)
    ml_score  = round(d.get("ml_score", 0), 3)
    expected  = "fake" if "fake" in name else "real"
    ok        = verdict == expected
    icon      = "✓" if ok else "✗"
    if not ok:
        all_pass = False
    print(f"  {icon}  {name:<35} verdict={verdict:<10} conf={conf}  ai={ai_score}  ml={ml_score}  {ms}ms")
    if debunked:
        print(f"       ↳ previously_debunked=True")

print("="*75)
print("All verdicts correct ✓" if all_pass else "Some verdicts wrong ✗")
print("="*75)
