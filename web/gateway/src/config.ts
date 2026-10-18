import dotenv from 'dotenv';
dotenv.config();

export const config = {
  port: parseInt(process.env.PORT || '3001'),
  jwtSecret: process.env.JWT_SECRET || 'erp-super-secret-key-change-in-production',
  jwtAlgorithm: 'HS256',
  pythonBackendUrl: process.env.PYTHON_BACKEND_URL || 'http://localhost:8002',
  corsOrigins: (process.env.CORS_ORIGINS || 'http://localhost:5173').split(','),
  frontendUrl: process.env.FRONTEND_URL || 'http://localhost:5173',
  rateLimitWindow: 60 * 1000,
  rateLimitMax: 100,
};
