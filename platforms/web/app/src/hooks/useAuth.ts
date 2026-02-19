import { useCallback } from "react";
import { useAuthStore } from "../store/auth";
import { api } from "../lib/api";

export function useAuth() {
  const { user, token, isAuthenticated, setAuth, clearAuth, updateToken } = useAuthStore();

  const login = useCallback(async (email: string, password: string) => {
    const resp = await api.login(email, password);
    setAuth(resp.user as any, resp.access_token, resp.refresh_token);
  }, [setAuth]);

  const signup = useCallback(async (email: string, password: string) => {
    const resp = await api.signup(email, password);
    setAuth(resp.user as any, resp.access_token, resp.refresh_token);
  }, [setAuth]);

  const logout = useCallback(() => {
    clearAuth();
  }, [clearAuth]);

  const refresh = useCallback(async () => {
    const { refreshToken } = useAuthStore.getState();
    if (!refreshToken) return;
    try {
      const resp = await api.refresh(refreshToken);
      updateToken(resp.access_token);
    } catch {
      clearAuth();
    }
  }, [updateToken, clearAuth]);

  return { user, token, isAuthenticated, login, signup, logout, refresh };
}
