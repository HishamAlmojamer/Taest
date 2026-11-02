import asyncio
import asyncpg

async def main():
    c = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/warehouse_management')
    cols = await c.fetch(
        "SELECT column_name, is_nullable, data_type, column_default "
        "FROM information_schema.columns WHERE table_name = 'permissions' ORDER BY ordinal_position"
    )
    print("=== permissions columns ===")
    for r in cols:
        print(f"  {r['column_name']:20s}  nullable={r['is_nullable']}  type={r['data_type']}  default={r['column_default']}")
    
    cols2 = await c.fetch(
        "SELECT column_name, is_nullable, data_type, column_default "
        "FROM information_schema.columns WHERE table_name = 'roles' ORDER BY ordinal_position"
    )
    print("\n=== roles columns ===")
    for r in cols2:
        print(f"  {r['column_name']:20s}  nullable={r['is_nullable']}  type={r['data_type']}  default={r['column_default']}")
    
    await c.close()

asyncio.run(main())
