import httpx, json, sys

BASE = "http://localhost:8001"

# 1. Health
try:
    r = httpx.get(f"{BASE}/api/health", timeout=5)
    print(f"[OK] Health: {r.json()}")
except Exception as e:
    print(f"[ERR] Health: {e}")
    sys.exit(1)

# 2. Login
try:
    r = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
    print(f"[{'OK' if r.status_code==200 else 'ERR'}] Login: {r.status_code}")
    if r.status_code != 200:
        print(f"  Body: {r.text[:300]}")
        sys.exit(1)
    token = r.json()["access_token"]
except Exception as e:
    print(f"[ERR] Login: {e}")
    sys.exit(1)

h = {"Authorization": f"Bearer {token}"}

# 3. All GET endpoints
endpoints = [
    "/api/auth/me",
    "/api/inventory/products",
    "/api/inventory/categories",
    "/api/inventory/warehouses",
    "/api/inventory/stock-movements",
    "/api/inventory/transfers",
    "/api/crm/customers",
    "/api/crm/suppliers",
    "/api/sales",
    "/api/sales/1",
    "/api/purchases",
    "/api/purchases/1",
    "/api/hr/employees",
    "/api/hr/attendance",
    "/api/hr/departments",
    "/api/hr/positions",
    "/api/hr/leaves",
    "/api/hr/payroll",
    "/api/accounting/accounts",
    "/api/accounting/journal-entries",
    "/api/accounting/trial-balance",
    "/api/accounting/fiscal-periods",
    "/api/accounting/cost-centers",
    "/api/projects",
    "/api/payments/banks",
    "/api/payments/customers",
    "/api/payments/suppliers",
    "/api/reports/sales-summary",
    "/api/reports/purchases-summary",
    "/api/reports/financial-summary",
    "/api/settings/users",
    "/api/settings/companies",
    "/api/settings/branches",
]

ok = err = 0
for ep in endpoints:
    try:
        r = httpx.get(f"{BASE}{ep}", headers=h, timeout=10)
        if r.status_code == 200:
            ok += 1
            data = r.json()
            if isinstance(data, list):
                print(f"  [OK] {ep}: {len(data)} items")
            elif isinstance(data, dict):
                if 'total' in data:
                    print(f"  [OK] {ep}: paginated({data['total']} total)")
                elif 'accounts' in data:
                    print(f"  [OK] {ep}: trial-balance({len(data['accounts'])} accounts)")
                elif 'items' in data:
                    print(f"  [OK] {ep}: {len(data['items'])} items")
                else:
                    print(f"  [OK] {ep}: {list(data.keys())[:4]}")
            else:
                print(f"  [OK] {ep}")
        else:
            err += 1
            print(f"  [ERR:{r.status_code}] {ep}: {r.text[:150]}")
    except Exception as e:
        err += 1
        print(f"  [EXC] {ep}: {e}")

print(f"\n{'='*50}")
print(f"  TOTAL: {ok} OK, {err} ERR / {len(endpoints)} endpoints")
print(f"{'='*50}")
