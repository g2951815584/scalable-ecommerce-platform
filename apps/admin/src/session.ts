import { create } from "zustand";
import { persist } from "zustand/middleware";
import { adminRoles, type AuthTokens } from "@ecommerce/frontend-shared";

interface AdminAuthState extends Partial<AuthTokens> {
  user_id?: string;
  nickname?: string;
  roles: string[];
  setSession: (session: AuthTokens & { user_id?: string; nickname?: string; roles?: string[] }) => void;
  clearSession: () => void;
}

export const useAdminAuthStore = create<AdminAuthState>()(
  persist(
    (set) => ({
      roles: [],
      setSession: (session) =>
        set({
          access_token: session.access_token,
          refresh_token: session.refresh_token,
          user_id: session.user_id,
          nickname: session.nickname,
          roles: session.roles ?? [],
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
    { name: "ecommerce-admin-auth" },
  ),
);

interface AdminLoginResult extends AuthTokens {
  user: { user_id: string; nickname: string; roles: string[] };
}

/** Normalise a login response (tokens + nested `user`) into the auth store. */
export function applyAdminLogin(result: AdminLoginResult): void {
  useAdminAuthStore.getState().setSession({
    access_token: result.access_token,
    refresh_token: result.refresh_token,
    user_id: result.user.user_id,
    nickname: result.user.nickname,
    roles: result.user.roles,
  });
}

export const adminSession = {
  getAccessToken: () => useAdminAuthStore.getState().access_token ?? null,
  refresh: async () => {
    const refreshToken = useAdminAuthStore.getState().refresh_token;
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
      useAdminAuthStore.setState(envelope.data);
      return envelope.data.access_token;
    } catch {
      return null;
    }
  },
  clear: () => useAdminAuthStore.getState().clearSession(),
  redirectToLogin: () => window.location.assign("/admin/login"),
};

export function hasAdminRole(roles: readonly string[]): boolean {
  return adminRoles.some((role) => roles.includes(role));
}
