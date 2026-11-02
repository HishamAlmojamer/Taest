import { Router, Request, Response } from 'express';
import { config } from '../config';
import { authLimiter } from '../middleware/rateLimit';
import { validate } from '../middleware/validate';
import { z } from 'zod';
import { logger } from '../services/logger';

const router = Router();

const loginSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
});

// Accept both camelCase (frontend) and snake_case (backend/FastAPI) payloads.
const refreshSchema = z
  .object({
    refreshToken: z.string().min(1).optional(),
    refresh_token: z.string().min(1).optional(),
  })
  .refine((v) => Boolean(v.refreshToken || v.refresh_token), {
    message: 'refreshToken is required',
  });

router.get('/context', async (_req: Request, res: Response) => {
  try {
    const backendRes = await fetch(`${config.pythonBackendUrl}/api/auth/context`);

    if (!backendRes.ok) {
      const errData: any = await backendRes.json().catch(() => ({}));
      res.status(backendRes.status).json({ error: errData.detail || 'Failed to load login context' });
      return;
    }

    res.json(await backendRes.json());
  } catch (err: any) {
    logger.error(`Login context error: ${err.message}`);
    res.status(502).json({ error: 'Authentication service unavailable' });
  }
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

    logger.info(`User ${username} logged in successfully`);

    res.json({
      accessToken: backendData.access_token,
      refreshToken: backendData.refresh_token || '',
      user: backendData.user || {},
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

router.post('/refresh', validate(refreshSchema), async (req: Request, res: Response) => {
  // Refresh MUST go through the backend: it owns token rotation and the
  // server-side registry used for revocation. Signing a new token here would
  // bypass both (and keep a stolen token usable).
  const refreshToken = req.body.refreshToken || req.body.refresh_token;

  try {
    const backendRes = await fetch(`${config.pythonBackendUrl}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const data: any = await backendRes.json().catch(() => ({}));

    if (!backendRes.ok) {
      res.status(backendRes.status).json({ error: data.detail || 'Invalid refresh token' });
      return;
    }

    res.json({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user: data.user,
    });
  } catch (err: any) {
    logger.error(`Refresh error: ${err.message}`);
    res.status(502).json({ error: 'Authentication service unavailable' });
  }
});

router.get('/me', async (req: Request, res: Response) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const backendRes = await fetch(`${config.pythonBackendUrl}/api/auth/me`, {
      headers: { Authorization: authHeader },
    });

    if (!backendRes.ok) {
      const errData: any = await backendRes.json().catch(() => ({}));
      res.status(backendRes.status).json({ error: errData.detail || 'Failed to fetch user info' });
      return;
    }

    const userData = await backendRes.json();
    res.json(userData);
  } catch (err: any) {
    logger.error(`Get user error: ${err.message}`);
    if (err.cause?.code === 'ECONNREFUSED') {
      res.status(502).json({ error: 'Authentication service unavailable' });
      return;
    }
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/logout', async (req: Request, res: Response) => {
  const refreshToken = req.body?.refreshToken || req.body?.refresh_token;
  try {
    if (refreshToken) {
      await fetch(`${config.pythonBackendUrl}/api/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    }
  } catch {
    // Logout is best effort: the client clears its session regardless.
  }

  logger.info('User logged out');
  res.json({ message: 'Logged out successfully' });
});

export default router;
