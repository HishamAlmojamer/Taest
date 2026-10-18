import asyncio, httpx, traceback
from app.main import app
from httpx import ASGITransport

async def t():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
        r = await c.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
        token = r.json()['access_token']
        h = {'Authorization': f'Bearer {token}'}
        endpoints = [
            '/api/inventory/products', '/api/inventory/categories', '/api/inventory/warehouses',
            '/api/inventory/stock-movements', '/api/inventory/transfers',
            '/api/crm/customers', '/api/crm/suppliers',
            '/api/sales', '/api/sales/1',
            '/api/purchases', '/api/purchases/1',
            '/api/hr/employees', '/api/hr/attendance', '/api/hr/departments', '/api/hr/positions',
            '/api/hr/leaves', '/api/hr/payroll',
            '/api/accounting/accounts', '/api/accounting/journal-entries',
            '/api/accounting/trial-balance', '/api/accounting/fiscal-periods', '/api/accounting/cost-centers',
            '/api/projects',
            '/api/payments/banks', '/api/payments/customers', '/api/payments/suppliers',
            '/api/reports/sales-summary',
            '/api/settings/users',
        ]
        ok = err = 0
        for ep in endpoints:
            try:
                r2 = await c.get(ep, headers=h)
                if r2.status_code == 200:
                    ok += 1
                    data = r2.json()
                    if isinstance(data, dict) and 'total' in data:
                        print(f'  [OK] {ep}: paginated ({data["total"]} total)')
                    elif isinstance(data, list):
                        print(f'  [OK] {ep}: {len(data)} items')
                    elif isinstance(data, dict) and 'items' in data:
                        print(f'  [OK] {ep}: {len(data["items"])} items')
                    elif isinstance(data, dict) and 'accounts' in data:
                        print(f'  [OK] {ep}: trial balance ({len(data["accounts"])} accounts)')
                    else:
                        print(f'  [OK] {ep}')
                else:
                    err += 1
                    print(f'  [ERR:{r2.status_code}] {ep}')
                    print(f'    {r2.text[:200]}')
            except Exception as e:
                err += 1
                print(f'  [EXC] {ep}: {e}')
        print(f'\n  Results: {ok} OK, {err} ERR')

asyncio.run(t())
