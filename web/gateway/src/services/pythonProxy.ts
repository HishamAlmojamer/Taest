import proxy from 'express-http-proxy';
import { Request, Response, NextFunction } from 'express';
import { config } from '../config';
import { logger } from './logger';

export function createBackendProxy() {
  const targetUrl = config.pythonBackendUrl;
  return proxy(targetUrl, {
    proxyReqPathResolver: (req: Request) => {
      const fullPath = req.originalUrl || req.url;
      logger.debug(`Proxying ${req.method} ${fullPath} -> ${targetUrl}${fullPath}`);
      return fullPath;
    },
    proxyErrorHandler: (err: any, res: Response, next: NextFunction) => {
      logger.error(`Proxy error: ${err.message}`);
      if (!res.headersSent) {
        res.status(502).json({ error: 'Backend service unavailable' });
      }
    },
  });
}
