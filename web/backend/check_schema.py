import psycopg2
conn = psycopg2.connect(host='localhost', dbname='warehouse_management', user='postgres', password='postgres')
cur = conn.cursor()
tables = ['products', 'sales', 'sale_items', 'purchases', 'purchase_items', 'customers', 'suppliers', 'categories', 'accounts', 'journal_entries', 'journal_entry_lines', 'stock_movements', 'hr_employees', 'hr_departments', 'hr_positions']
for t in tables:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", (t,))
    cols = cur.fetchall()
    print(f'\n=== {t} ({len(cols)} cols) ===')
    for c in cols:
        print(f'  {c[0]}: {c[1]}')
conn.close()
