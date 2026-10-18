import { createProxyMiddleware } from 'http-proxy-middleware';
import { config } from '../config';
import { logger } from './logger';

export function createWsProxy() {
  return createProxyMiddleware({
    target: config.pythonBackendUrl,
    changeOrigin: true,
    ws: true,
    on: {
      error: (err: Error, req: any) => {
        logger.error(`WS Proxy error for ${req.url}: ${err.message}`);
      },
    },
  });
}
