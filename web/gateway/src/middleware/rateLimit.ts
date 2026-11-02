import rateLimit from 'express-rate-limit';
import { config } from '../config';

export const apiLimiter = rateLimit({
  windowMs: config.rateLimitWindow,
  max: config.rateLimitMax,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please try again later' },
  // The backend emits ledger events server-to-server from the same host; do
  // not let those internal calls consume the shared browser IP budget.
  skip: (req) => req.path === '/api/ledger/emit',
});

export const authLimiter = rateLimit({
  windowMs: config.rateLimitWindow,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many login attempts, please try again later' },
});
