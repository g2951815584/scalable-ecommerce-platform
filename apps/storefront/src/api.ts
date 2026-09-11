import { createApiClient } from "@ecommerce/frontend-shared";
import { authSession } from "./session";

export const api = createApiClient({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  auth: authSession,
});
