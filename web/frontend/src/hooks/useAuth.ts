import { useAuthStore } from '@/stores/authStore';

export function useAuth() {
  const { user, isAuthenticated, login, logout, updateUser } = useAuthStore();
  return { user, isAuthenticated, login, logout, updateUser };
}
