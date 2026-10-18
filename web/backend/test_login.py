import asyncio, httpx

async def test():
    async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=30) as c:
        # Test login with detailed error
        r = await c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        print(f"Login status: {r.status_code}")
        print(f"Login body: {r.text[:500]}")
        
        if r.status_code == 200:
            token = r.json()["access_token"]
            h = {"Authorization": f"Bearer {token}"}
            # Test /me
            r2 = await c.get("/api/auth/me", headers=h)
            print(f"Me status: {r2.status_code}")
            print(f"Me body: {r2.text[:500]}")

asyncio.run(test())
