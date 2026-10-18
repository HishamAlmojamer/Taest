import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/warehouse_management')
cur = conn.cursor()
cur.execute("SELECT id, username, password, full_name, role, is_active FROM users")
for row in cur.fetchall():
    print(f"ID={row[0]} user={row[1]} pass_len={len(row[2]) if row[2] else 0} name={row[3]} role={row[4]} active={row[5]}")
conn.close()
