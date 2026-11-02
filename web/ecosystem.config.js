const path = require('path');

const ROOT = __dirname;

module.exports = {
  apps: [
    {
      name: 'backend',
      cwd: path.join(ROOT, 'backend'),
      // Use the project virtualenv so PM2 does not depend on a machine-specific
      // global Python installation.
      script: path.join(ROOT, 'backend', '.venv', 'Scripts', 'python.exe'),
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8001',
      interpreter: 'none',
      watch: false,
      env: {
        PYTHONPATH: '.',
        DEBUG: 'false',
        CACHE_ENABLED: 'false',
      },
      max_restarts: 10,
      restart_delay: 3000,
      exp_backoff_restart_delay: 100,
    },
    {
      name: 'gateway',
      cwd: path.join(ROOT, 'gateway'),
      // Run the TypeScript entrypoint via tsx so PM2 never serves a stale
      // `dist/` build that was not compiled after a code change.
      script: path.join(ROOT, 'gateway', 'node_modules', 'tsx', 'dist', 'cli.mjs'),
      args: 'src/index.ts',
      interpreter: 'none',
      watch: false,
      max_restarts: 5,
      restart_delay: 5000,
      min_uptime: 10000,
    },
    {
      name: 'frontend',
      cwd: path.join(ROOT, 'frontend'),
      // Vite's preview server does not apply `server.proxy`; use the dev
      // server (which proxies /api and /api/ledger to the right services).
      script: 'node',
      args: 'node_modules/vite/bin/vite.js --port 5173 --host 0.0.0.0',
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      exp_backoff_restart_delay: 100,
    },
  ],
};
