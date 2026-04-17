"""Quick API test suite — runs all endpoints and reports pass/fail."""
import requests, json, time

BASE = "http://127.0.0.1:8000"
results = []

def test(name, method, path, body=None, timeout=60):
    url = BASE + path
    try:
        t0 = time.time()
        if method == "GET":
            r = requests.get(url, timeout=timeout)
        else:
            r = requests.post(url, json=body, timeout=timeout)
        elapsed = round((time.time() - t0) * 1000)
        ok = 200 <= r.status_code < 300
        try:
            preview = str(r.json())[:80]
        except Exception:
            preview = r.text[:80]
        results.append((name, ok, r.status_code, preview, elapsed))
        status = "✓" if ok else "✗"
        print(f"  {status}  {name:<35} [{r.status_code}]  {elapsed}ms")
    except Exception as e:
        results.append((name, False, "ERR", str(e)[:80], 0))
        print(f"  ✗  {name:<35} [ERR]  {str(e)[:60]}")

print("\n" + "="*70)
print("RUNNING API TESTS")
print("="*70)

test("Health",              "GET",  "/health")
test("OpenAPI docs",        "GET",  "/openapi.json")
test("Stats (root)",        "GET",  "/stats")
test("Stats /system",       "GET",  "/stats/system")
test("Stats /bias",         "GET",  "/stats/bias")
test("Credibility",         "GET",  "/credibility")
test("Velocity stats",      "GET",  "/velocity/stats")
test("Clustering stats",    "GET",  "/clustering/stats")
test("Chat - greeting",     "POST", "/message", {"message": "Hello, how are you?"})
test("Chat - question",     "POST", "/message", {"message": "What is misinformation?"})
test("Claim - flat earth",  "POST", "/message", {"message": "Scientists have confirmed the earth is flat and NASA has been lying for decades"}, timeout=90)
test("Claim - vaccine",     "POST", "/message", {"message": "COVID-19 vaccines have been approved by WHO and shown to be safe and effective"}, timeout=90)
test("Claim - conspiracy",  "POST", "/message", {"message": "The deep state is using 5G towers to control people's minds"}, timeout=90)
test("Feedback",            "POST", "/feedback", {"claim_text": "test claim", "predicted": "fake", "actual": "real"})

print()
print("="*70)
passed = sum(1 for _,ok,*_ in results if ok)
print(f"RESULTS: {passed}/{len(results)} passed")
print("="*70)

# Show failures in detail
failures = [(n,s,p,e) for n,ok,s,p,e in results if not ok]
if failures:
    print("\nFAILURES:")
    for name, status, preview, elapsed in failures:
        print(f"  ✗ {name}: [{status}] {preview}")
else:
    print("\nAll tests passed! ✓")

# Show verdict for claims
print("\nCLAIM VERDICTS:")
for name, ok, status, preview, elapsed in results:
    if "Claim" in name and ok:
        try:
            data = json.loads(preview.replace("'", '"'))
        except Exception:
            data = {}
        verdict = data.get("verdict", "?")
        conf = data.get("confidence", "?")
        print(f"  {name:<35} verdict={verdict}  conf={conf}  ({elapsed}ms)")
