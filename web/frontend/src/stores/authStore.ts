import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  fiscalYearId: number | null;
  branchId: number | null;
  login: (user: User, accessToken: string, refreshToken: string) => void;
  setSessionContext: (fiscalYearId: number | null, branchId: number | null) => void;
  logout: () => void;
  updateUser: (user: User) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      fiscalYearId: null,
      branchId: null,
      login: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken, isAuthenticated: true }),
      setSessionContext: (fiscalYearId, branchId) =>
        set({ fiscalYearId, branchId }),
      logout: () => {
        // Revoke the refresh token server-side (best effort, never blocks UI).
        const token = get().refreshToken;
        if (token) {
          void fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: token, refreshToken: token }),
            keepalive: true,
          }).catch(() => undefined);
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          fiscalYearId: null,
          branchId: null,
        });
      },
      updateUser: (user) => set({ user }),
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
    }),
    { name: 'erp-auth' }
  )
);
