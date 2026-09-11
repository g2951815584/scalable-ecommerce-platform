import { createApiClient } from "@ecommerce/frontend-shared";
import { adminSession } from "./session";

export const adminApi = createApiClient({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  auth: adminSession,
});
