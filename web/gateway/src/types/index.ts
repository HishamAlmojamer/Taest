import { Request } from 'express';

export interface UserPayload {
  id: number;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  iat?: number;
  exp?: number;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface ApiError extends Error {
  statusCode: number;
  code?: string;
  details?: unknown;
}

declare global {
  namespace Express {
    interface Request {
      user?: UserPayload;
    }
  }
}
