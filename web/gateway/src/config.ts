import dotenv from 'dotenv';
dotenv.config();

const INSECURE_DEFAULT_SECRET = 'e0436fceff1e125dd44e02f7862ada50fb3e4539408a337a89c18ef56dd876e8';

const environment = process.env.ENVIRONMENT || process.env.NODE_ENV || 'development';
const isProduction = ['production', 'prod'].includes(environment.toLowerCase());

const jwtSecret = process.env.JWT_SECRET;
if (!jwtSecret || jwtSecret.length < 32) {
  throw new Error('JWT_SECRET must be set and at least 32 characters long');
}
if (isProduction && jwtSecret === INSECURE_DEFAULT_SECRET) {
  throw new Error('JWT_SECRET is the insecure default value; generate a unique secret for production');
}
if (isProduction && /^(change_me|changeme|replace-|replace_with)/i.test(jwtSecret)) {
  throw new Error('JWT_SECRET is still a placeholder value');
}

function normalizeUrl(value: string): string {
  return /^https?:\/\//i.test(value) ? value : `http://${value}`;
}

export const config = {
  environment,
  isProduction,
  port: parseInt(process.env.PORT || '3001', 10),
  jwtSecret,
  jwtAlgorithm: (process.env.JWT_ALGORITHM || 'HS256') as 'HS256' | 'HS384' | 'HS512',
  pythonBackendUrl: normalizeUrl(process.env.PYTHON_BACKEND_URL || 'http://localhost:8001'),
  corsOrigins: (process.env.CORS_ORIGINS || 'http://localhost:5173')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean),
  frontendUrl: process.env.FRONTEND_URL || 'http://localhost:5173',
  serveFrontendDir: process.env.SERVE_FRONTEND_DIR || '',
  // Allow any Cloudflare Pages deployment/preview origin while the project
  // URL is not final. Disable once CORS_ORIGINS contains the exact URL.
  allowPagesDev: ['1', 'true', 'yes'].includes(
    (process.env.ALLOW_PAGES_DEV || '').toLowerCase(),
  ),
  rateLimitWindow: 60 * 1000,
  rateLimitMax: 100,
};
