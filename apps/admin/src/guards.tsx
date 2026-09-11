import { Result } from "antd";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import type { Role } from "@ecommerce/frontend-shared";
import { hasAdminRole, useAdminAuthStore } from "./session";

export function AdminAuthGuard() {
  const token = useAdminAuthStore((state) => state.access_token);
  const roles = useAdminAuthStore((state) => state.roles);
  const location = useLocation();
  if (!token) {
    return <Navigate replace to={`/login?redirect=${encodeURIComponent(`${location.pathname}${location.search}`)}`} />;
  }
  if (!hasAdminRole(roles)) {
    return <Result status="403" title="无后台访问权限" subTitle="当前账户不包含运营后台角色。" />;
  }
  return <Outlet />;
}

export function RoleGuard({ roles: requiredRoles, children }: { roles: readonly Role[]; children: React.ReactNode }) {
  const activeRoles = useAdminAuthStore((state) => state.roles);
  const allowed = requiredRoles.some((role) => activeRoles.includes(role));
  if (!allowed) {
    return <Result status="403" title="无权限执行此操作" subTitle="请联系管理员分配对应角色。" />;
  }
  return <>{children}</>;
}

export function usePermission(requiredRoles: readonly Role[]) {
  const roles = useAdminAuthStore((state) => state.roles);
  return { canAccess: requiredRoles.some((role) => roles.includes(role)) };
}
