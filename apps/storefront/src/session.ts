import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthTokens } from "@ecommerce/frontend-shared";
import type { LoginResult } from "./types";

interface AuthState extends Partial<AuthTokens> {
  user_id?: string;
  nickname?: string;
  roles: string[];
  setSession: (session: AuthTokens & { user_id?: string; nickname?: string; roles?: string[] }) => void;
  clearSession: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      roles: [],
      setSession: (session) =>
        set({
          access_token: session.access_token,
          refresh_token: session.refresh_token,
          user_id: session.user_id,
          nickname: session.nickname,
          roles: session.roles ?? ["BUYER"],
        }),
      clearSession: () =>
        set({
          access_token: undefined,
          refresh_token: undefined,
          user_id: undefined,
          nickname: undefined,
          roles: [],
        }),
    }),
    { name: "ecommerce-storefront-auth" },
  ),
);

/** Normalise the login response (tokens + nested `user`) into the auth store. */
export function applyLogin(result: LoginResult): void {
  useAuthStore.getState().setSession({
    access_token: result.access_token,
    refresh_token: result.refresh_token,
    user_id: result.user.user_id,
    nickname: result.user.nickname,
    roles: result.user.roles,
  });
}

export const authSession = {
  getAccessToken: () => useAuthStore.getState().access_token ?? null,
  refresh: async () => {
    const refreshToken = useAuthStore.getState().refresh_token;
    if (!refreshToken) return null;
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? "/api/v1"}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) return null;
      const envelope = (await response.json()) as { data?: AuthTokens };
      if (!envelope.data?.access_token) return null;
      useAuthStore.setState(envelope.data);
      return envelope.data.access_token;
    } catch {
      return null;
    }
  },
  clear: () => useAuthStore.getState().clearSession(),
  redirectToLogin: () => {
    const redirect = `${window.location.pathname}${window.location.search}`;
    window.location.assign(`/login?redirect=${encodeURIComponent(redirect)}`);
  },
};
