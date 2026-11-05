# Database Setup

The application uses PostgreSQL 16+ through SQLAlchemy 2 async and asyncpg.
Local development currently runs PostgreSQL 18; Neon's managed PostgreSQL is
compatible.

## Neon project

1. Create a project at <https://console.neon.tech>.
2. Choose a region close to the API, for example `eu-central-1` (Frankfurt).
3. Keep the default database (`neondb`) and role, or create a dedicated role.
4. From **Connect**, copy:
   - the **pooled** connection string for the application (`-pooler` host);
   - the **direct** connection string for backups and manual administration.
5. Ensure the URL ends with `sslmode=require`.

Example shape (not a real credential):

```text
postgresql://USER:PASSWORD@ep-xxxx-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

Store it as `DATABASE_URL` in Render. Do not write it to the repository.

## Connection handling in code

`web/backend/app/database.py`:

- accepts `postgresql://` and `postgresql+asyncpg://`;
- strips libpq-only parameters such as `channel_binding`, `gssencmode`,
  `target_session_attrs`, `options`, and `application_name`;
- maps `sslmode=require` to an asyncpg SSL context;
- sets `statement_cache_size=0` when the host contains `-pooler`, because
  PgBouncer transaction pooling is incompatible with asyncpg prepared-statement
  caching;
- applies `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, and
  `DB_POOL_RECYCLE`.

The gateway uses its own `pg` pool sized by `PG_POOL_MAX`; it connects to the
same Neon URL.

## Migrations

Alembic lives in `web/backend` and uses the current baseline:

```text
alembic/versions/0001_baseline.py
```

The API container runs `alembic upgrade head` on every start. To run manually:

```bash
cd web/backend
alembic current
alembic upgrade head
```

Rules:

- never edit an applied migration; add a new revision;
- back up before a schema change that rewrites or drops data;
- test migrations on a copy of the database first;
- do not run `alembic downgrade` in production without a verified backup.

## First-run seed

Bootstrap is idempotent and only inserts missing data:

- company and main branch;
- current fiscal year and 12 monthly periods;
- standard chart of accounts;
- administrator user when `BOOTSTRAP_ADMIN_USERNAME` and
  `BOOTSTRAP_ADMIN_PASSWORD` are set.

Existing rows are not duplicated or overwritten. After the first login, remove
`BOOTSTRAP_ADMIN_PASSWORD` from Render and redeploy.

## Validation queries

Read-only checks after deployment:

```sql
select current_database(), current_user, version();

select count(*) from information_schema.tables
where table_schema = 'public' and table_type = 'BASE TABLE';

select count(*) from pg_indexes where schemaname = 'public';

select version_num from alembic_version;

select count(*) from accounts;
select count(*) from accounts a
where a.parent_id is not null
  and not exists (select 1 from accounts p where p.id = a.parent_id);

select count(*) from companies;
select count(*) from branches;
select count(*) from fiscal_years;
select count(*) from fiscal_periods;
```

Expected after a fresh bootstrap: the baseline revision, 114 accounts, no
orphan parent accounts, one company, one branch, one fiscal year, and 12
periods. Additional data may exist after testing.

Balance checks:

```sql
select sum(debit), sum(credit)
from journal_entry_lines
where entry_id in (select id from journal_entries where is_posted = true);
```

Debit and credit totals must be equal.

## Backups

Neon Free includes a limited restore window; verify the current window in the
console. Before entering real accounting data:

1. Take a manual branch/snapshot in Neon if available.
2. Run a logical backup from the **direct** endpoint:

```bash
pg_dump "postgresql://USER:PASSWORD@ep-xxxx.eu-central-1.aws.neon.tech/neondb?sslmode=require" \
  --no-owner --no-privileges --format=custom --file=erp-backup.dump
```

3. Store the dump encrypted outside the repository.
4. Test a restore into a separate database:

```bash
createdb erp_restore_test
pg_restore --no-owner --no-privileges --dbname=erp_restore_test erp-backup.dump
```

Never commit dumps, `.env` files, or database credentials.

## Local database

The development default is:

```text
postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/warehouse_management
```

Production validation rejects localhost URLs when `ENVIRONMENT=production`.
