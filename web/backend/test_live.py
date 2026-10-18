import httpx

BASE = "http://localhost:8001"

def main():
    # 1. Health check
    r = httpx.get(f"{BASE}/api/health")
    print(f"[{'OK' if r.status_code==200 else 'ERR'}] GET /api/health => {r.json()}")

    # 2. Login
    r = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"})
    if r.status_code != 200:
        print(f"[ERR] Login failed: {r.status_code} {r.text[:200]}")
        return
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    print(f"[OK] POST /api/auth/login => token received")

    # 3. Test all GET endpoints
    endpoints = [
        ("GET", "/api/auth/me"),
        ("GET", "/api/inventory/products"),
        ("GET", "/api/inventory/categories"),
        ("GET", "/api/inventory/warehouses"),
        ("GET", "/api/inventory/stock-movements"),
        ("GET", "/api/inventory/transfers"),
        ("GET", "/api/crm/customers"),
        ("GET", "/api/crm/suppliers"),
        ("GET", "/api/sales"),
        ("GET", "/api/purchases"),
        ("GET", "/api/hr/employees"),
        ("GET", "/api/hr/attendance"),
        ("GET", "/api/hr/departments"),
        ("GET", "/api/hr/positions"),
        ("GET", "/api/hr/leaves"),
        ("GET", "/api/hr/payroll"),
        ("GET", "/api/accounting/accounts"),
        ("GET", "/api/accounting/journal-entries"),
        ("GET", "/api/accounting/trial-balance"),
        ("GET", "/api/accounting/fiscal-periods"),
        ("GET", "/api/accounting/cost-centers"),
        ("GET", "/api/projects"),
        ("GET", "/api/payments/banks"),
        ("GET", "/api/payments/customers"),
        ("GET", "/api/payments/suppliers"),
        ("GET", "/api/reports/sales-summary"),
        ("GET", "/api/reports/purchases-summary"),
        ("GET", "/api/reports/financial-summary"),
        ("GET", "/api/settings/users"),
        ("GET", "/api/settings/companies"),
        ("GET", "/api/settings/branches"),
    ]

    ok = err = 0
    for method, ep in endpoints:
        try:
            r = httpx.get(f"{BASE}{ep}", headers=h, timeout=10)
            if r.status_code == 200:
                ok += 1
                data = r.json()
                if isinstance(data, list):
                    print(f"  [OK] {ep}: {len(data)} items")
                elif isinstance(data, dict):
                    keys = list(data.keys())
                    print(f"  [OK] {ep}: keys={keys}")
                else:
                    print(f"  [OK] {ep}")
            else:
                err += 1
                print(f"  [ERR:{r.status_code}] {ep}: {r.text[:150]}")
        except Exception as e:
            err += 1
            print(f"  [EXC] {ep}: {e}")

    # 4. Test individual resource
    try:
        r = httpx.get(f"{BASE}/api/sales/1", headers=h, timeout=10)
        print(f"  [{'OK' if r.status_code==200 else 'ERR'}] GET /api/sales/1 => {r.status_code}")
    except Exception as e:
        print(f"  [EXC] GET /api/sales/1: {e}")

    try:
        r = httpx.get(f"{BASE}/api/purchases/1", headers=h, timeout=10)
        print(f"  [{'OK' if r.status_code==200 else 'ERR'}] GET /api/purchases/1 => {r.status_code}")
    except Exception as e:
        print(f"  [EXC] GET /api/purchases/1: {e}")

    print(f"\n  TOTAL: {ok} OK, {err} ERR out of {len(endpoints)} endpoints")

if __name__ == "__main__":
    main()
