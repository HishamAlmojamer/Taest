import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/warehouse_management')
    cur = conn.cursor()
    cur.execute('SELECT count(*) FROM products')
    print('Products:', cur.fetchone()[0])
    cur.execute('SELECT count(*) FROM auth_user')
    print('Users:', cur.fetchone()[0])
    conn.close()
    print('DB connection OK')
except Exception as e:
    print(f'DB error: {e}')
