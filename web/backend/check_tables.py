import asyncio, asyncpg

async def t():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/warehouse_management')
    for table in ['suppliers', 'customers', 'banks']:
        rows = await conn.fetch(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}' AND table_schema='public' ORDER BY ordinal_position")
        print(f"\n{table}:")
        for r in rows:
            print(f"  {r['column_name']:30s} {r['data_type']}")
    await conn.close()

asyncio.run(t())
