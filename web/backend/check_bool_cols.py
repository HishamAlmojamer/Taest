import asyncio, asyncpg

async def t():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/warehouse_management')
    rows = await conn.fetch('''
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE (column_name LIKE 'is_%' OR column_name LIKE '%active%')
        AND table_schema = 'public'
        ORDER BY table_name, column_name
    ''')
    for r in rows:
        print(r['table_name'], r['column_name'], r['data_type'])
    await conn.close()

asyncio.run(t())
