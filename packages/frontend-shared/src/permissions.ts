import type { Role } from "./contracts";

/** Returns true when the active role set intersects the required role set. */
export function hasAnyRole(activeRoles: readonly Role[], requiredRoles: readonly Role[]): boolean {
  return requiredRoles.some((role) => activeRoles.includes(role));
}

export const adminRoles: readonly Role[] = [
  "PRODUCT_OPS",
  "ORDER_OPS",
  "WAREHOUSE",
  "CS",
  "FINANCE",
  "ADMIN",
];
