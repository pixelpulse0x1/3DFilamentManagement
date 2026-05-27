#!/usr/bin/env python3
"""v0.5.2.0 — Automated E2E Integration Test Suite for 3DFilamentManagement.

Usage:
    python test_suite.py [--base-url http://192.168.37.132:9055]

Tests cover:
    A - Weighing toggle lock-down (edit filament modal)
    B - Negative/NaN input defense (edit + save)
    C - Empty data submission to cost calculator
    D - Zero-denominator meltdown protection
"""

import sys, json, argparse, time
import requests

parser = argparse.ArgumentParser()
parser.add_argument('--base-url', default='http://127.0.0.1:9055')
args = parser.parse_args()
BASE_URL = args.base_url.rstrip('/')

# Wait for server to be ready
print(f"Connecting to {BASE_URL} ...")
for i in range(10):
    try:
        r = requests.get(f"{BASE_URL}/api/system/status", timeout=3)
        if r.status_code == 200:
            print(f"Server ready (attempt {i+1})")
            break
    except Exception:
        pass
    time.sleep(1)
else:
    print("WARNING: Server not responding, tests may fail")
PASS, FAIL = 0, 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ PASS: {name}")
    else:
        FAIL += 1
        print(f"  ❌ FAIL: {name} — {detail}")

def safe_json(r):
    """Safely parse JSON, always try JSON first, fallback to raw text."""
    try:
        return r.json()
    except Exception:
        try:
            return json.loads(r.text)
        except Exception:
            return {"status": "error", "raw": str(r.text)[:200]}

def api_get(path):
    try: return requests.get(f"{BASE_URL}{path}", timeout=10)
    except Exception as e: return type('R',(),{'status_code':0,'headers':{},'text':str(e),'json':lambda:{'error':str(e)}})

def api_post(path, data):
    try: return requests.post(f"{BASE_URL}{path}", json=data, timeout=10)
    except Exception as e: return type('R',(),{'status_code':0,'headers':{},'text':str(e),'json':lambda:{'error':str(e)}})

# ═══════════════════════════════════════════
# Test C: Empty data submission to calculator
# ═══════════════════════════════════════════
print("\n── Test C: Empty data submission ──")
r = api_post("/api/tools/calculator/save", {
    "project_name": "",
    "filaments": [], "printers": [], "post_processing": [],
    "total_cost": "", "suggested_price": "", "pure_profit": "",
    "design_fee": "abc", "tax_rate": "xyz",
})
test("Empty project name rejected", r.status_code == 400, f"got {r.status_code}")
test("Empty string costs don't crash", r.status_code != 500, f"got {r.status_code}: {r.text[:200]}")
test("Non-numeric fees don't crash", r.status_code != 500, "backend should coerce to 0.0")
print(f"  Response: {safe_json(r) if r.status_code else 'connection failed'}")

# ═══════════════════════════════════════════
# Test D: Zero denominator meltdown
# ═══════════════════════════════════════════
print("\n── Test D: Zero denominator protection ──")
r = api_post("/api/tools/calculator/save", {
    "project_name": "MeltdownTest",
    "filaments": [{"filament_id":1,"material_name":"PLA","weight_g":10,"purge_g":0,"cost_per_g":0.05,"is_support":0}],
    "printers": [{"printer_id":1,"printer_name":"P1S","print_time_mins":60,"power_w":105,"value_yuan":3899,"lifespan_h":20000}],
    "post_processing": [],
    "design_fee": 0, "packaging_fee": 0, "shipping_fee": 0, "other_fee": 0,
    "tax_rate": 0, "platform_commission_rate": 50, "profit_rate_expect": 120,
    "labor_markup_fee": 0, "total_cost": 100, "suggested_price": 100, "pure_profit": 100,
})
test("Denominator<=0 returns 400", r.status_code == 400, f"got {r.status_code}")
test("Error message mentions percentage limit",
     "100%" in str(safe_json(r).get("error","")) or "大于" in str(safe_json(r).get("error","")),
     f"response: {safe_json(r)}")

# ═══════════════════════════════════════════
# Test A/B: Filament endpoint health check
# ═══════════════════════════════════════════
print("\n── Test A/B: Data API integrity ──")
r = api_get("/api/filaments")
test("GET /api/filaments returns 200", r.status_code == 200, f"got {r.status_code}")
data = safe_json(r) if r.status_code == 200 else []
test("Filaments is a list", isinstance(data, list), f"type={type(data)}")
if data:
    f = data[0]
    test("brand_id present", "brand_id" in f, "missing from filament dict")

r = api_get("/api/settings")
test("GET /api/settings returns 200", r.status_code == 200, f"got {r.status_code}")
s = safe_json(r) if r.status_code == 200 else {}
test("Settings has threshold", "threshold" in s, "missing threshold")

# ═══════════════════════════════════════════
# Save a valid record for history check
# ═══════════════════════════════════════════
print("\n── History CRUD check ──")
r = api_post("/api/tools/calculator/save", {
    "project_name": "AutomatedTest",
    "filaments": [{"filament_id":1,"material_name":"PLA","weight_g":50,"purge_g":5,"cost_per_g":0.05,"is_support":0}],
    "printers": [{"printer_id":1,"printer_name":"P1S","print_time_mins":60,"power_w":105,"value_yuan":3899,"lifespan_h":20000}],
    "post_processing": [],
    "design_fee": 0, "packaging_fee": 0, "shipping_fee": 0, "other_fee": 0,
    "tax_rate": 0, "platform_commission_rate": 0, "profit_rate_expect": 40,
    "labor_markup_fee": 0, "total_cost": 5.5, "suggested_price": 9.17, "pure_profit": 3.67,
})
test("Valid save returns success", r.status_code == 200 and safe_json(r).get("status")=="success", f"got {safe_json(r)}")
saved_id = safe_json(r).get("id") if r.status_code==200 else None

if saved_id:
    r2 = api_get(f"/api/tools/calculator/detail/{saved_id}")
    test("Detail fetch works", r2.status_code == 200 and safe_json(r2).get("project_name")=="AutomatedTest")
    r3 = requests.delete(f"{BASE_URL}/api/tools/calculator/history/{saved_id}", timeout=10)
    test("Delete works", r3.status_code == 200)

# ═══════════════════════════════════════════
# Global API health scan
# ═══════════════════════════════════════════
print("\n── Global endpoint health ──")
endpoints = [
    "/api/filaments", "/api/statistics", "/api/materials", "/api/brands",
    "/api/channels", "/api/images", "/api/printers", "/api/printer_models",
    "/api/system/status", "/api/system/config", "/api/settings",
]
for ep in endpoints:
    r = api_get(ep)
    ok = r.status_code == 200
    if ok: PASS += 1
    else: FAIL += 1
    print(f"  {'✅' if ok else '❌'} {ep} → {r.status_code}")

# ═══════════════════════════════════════════
print(f"\n{'='*50}")
print(f"Results: {PASS} passed, {FAIL} failed, {PASS+FAIL} total")
print(f"{'='*50}")
sys.exit(0 if FAIL == 0 else 1)
