import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { config } from '../config';
import { UserPayload } from '../types';

export function authenticate(req: Request, res: Response, next: NextFunction): void {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({ error: 'Missing or invalid Authorization header' });
    return;
  }

  const token = authHeader.split(' ')[1];

  try {
    const decoded = jwt.verify(token, config.jwtSecret, {
      algorithms: [config.jwtAlgorithm as jwt.Algorithm],
    }) as UserPayload & { sub?: string | number; type?: string };

    // A refresh token must never be accepted as an access token.
    if (decoded.type !== 'access') {
      res.status(401).json({ error: 'Invalid token type' });
      return;
    }

    // Backend-issued tokens carry the user id in `sub`; normalize it to `id`
    // so downstream handlers can rely on req.user.id consistently.
    req.user = {
      ...decoded,
      id: (decoded.id as number) ?? Number(decoded.sub),
    };
    next();
  } catch (err: any) {
    if (err.name === 'TokenExpiredError') {
      res.status(401).json({ error: 'Token expired' });
      return;
    }
    res.status(401).json({ error: 'Invalid token' });
  }
}
