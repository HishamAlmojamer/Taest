import { Router, Request, Response } from 'express';
import jwt from 'jsonwebtoken';
import { config } from '../config';
import { authenticate } from '../middleware/auth';
import { authLimiter } from '../middleware/rateLimit';
import { validate } from '../middleware/validate';
import { z } from 'zod';
import { logger } from '../services/logger';

const router = Router();

const loginSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
});

const refreshSchema = z.object({
  refreshToken: z.string().min(1),
});

router.post('/login', authLimiter, validate(loginSchema), async (req: Request, res: Response) => {
  try {
    const { username, password } = req.body;

    const backendRes = await fetch(`${config.pythonBackendUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!backendRes.ok) {
      const errData: any = await backendRes.json().catch(() => ({}));
      res.status(backendRes.status).json({ error: errData.detail || errData.error || 'Invalid credentials' });
      return;
    }

    const backendData: any = await backendRes.json();

    const user = backendData.user || backendData;

    logger.info(`User ${username} logged in successfully`);

    res.json({
      accessToken: backendData.access_token,
      refreshToken: backendData.refresh_token || '',
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role,
        permissions: user.permissions || [],
      },
    });
  } catch (err: any) {
    logger.error(`Login error: ${err.message}`);
    if (err.cause?.code === 'ECONNREFUSED') {
      res.status(502).json({ error: 'Authentication service unavailable' });
      return;
    }
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/refresh', validate(refreshSchema), (req: Request, res: Response) => {
  try {
    const { refreshToken } = req.body;

    const decoded = jwt.verify(refreshToken, config.jwtSecret, {
      algorithms: [config.jwtAlgorithm as jwt.Algorithm],
    }) as { id: number; type: string };

    if (decoded.type !== 'refresh') {
      res.status(401).json({ error: 'Invalid token type' });
      return;
    }

    const accessToken = jwt.sign(
      { id: decoded.id, tokenType: 'access' },
      config.jwtSecret,
      { algorithm: config.jwtAlgorithm as jwt.Algorithm, expiresIn: '1h' }
    );

    const newRefreshToken = jwt.sign(
      { id: decoded.id, type: 'refresh' },
      config.jwtSecret,
      { algorithm: config.jwtAlgorithm as jwt.Algorithm, expiresIn: '7d' }
    );

    res.json({ accessToken, refreshToken: newRefreshToken });
  } catch (err: any) {
    if (err.name === 'TokenExpiredError') {
      res.status(401).json({ error: 'Refresh token expired' });
      return;
    }
    res.status(401).json({ error: 'Invalid refresh token' });
  }
});

router.get('/me', async (req: Request, res: Response) => {
  try {
    const backendRes = await fetch(`${config.pythonBackendUrl}/api/auth/me`, {
      headers: { Authorization: req.headers.authorization || '' },
    });

    if (!backendRes.ok) {
      res.status(backendRes.status).json({ error: 'Failed to fetch user info' });
      return;
    }

    const userData = await backendRes.json();
    res.json(userData);
  } catch {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }
    const resp = await fetch(`${config.pythonBackendUrl}/api/auth/me`, {
      headers: { Authorization: authHeader },
    });
    if (!resp.ok) { res.status(401).json({ error: 'Invalid token' }); return; }
    res.json(await resp.json());
  }
});

router.post('/logout', async (req: Request, res: Response) => {
  try {
    await fetch(`${config.pythonBackendUrl}/api/auth/logout`, {
      method: 'POST',
      headers: { Authorization: req.headers.authorization || '' },
    });
  } catch {
    // Logout even if backend is down
  }

  logger.info(`User ${req.user?.username} logged out`);
  res.json({ message: 'Logged out successfully' });
});

export default router;
