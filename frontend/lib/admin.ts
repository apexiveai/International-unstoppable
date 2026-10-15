import API_URL from "@/lib/api";

export type AdminClient = {
  id: number;
  tenant_id: number | null;
  username: string;
  email: string;
  display_name: string;
  company_name: string | null;
  is_active: boolean;
  account_status: string;
  is_admin: boolean;
  created_at: string;
};

export type AdminAccount = {
  id: number;
  username: string;
  email: string;
  display_name: string;
  is_active: boolean;
  is_admin: true;
  is_super_admin: boolean;
  role: "ADMIN" | "SUPPORT" | string;
  created_at: string;
};

export type AdminPlan = {
  id: number;
  product_key: string;
  name: string;
  description: string;
  monthly_price: string;
  currency: string;
  billing_cycle: string;
  is_active: boolean;
};

export type AdminPayment = {
  id: number;
  tenant_id: number;
  plan_id: number;
  subscription_id: number | null;
  status: string;
  amount: string;
  currency: string;
  payment_method: string;
  failure_reason: string | null;
  created_at: string;
};

export type AdminSubscription = {
  id: number;
  tenant_id: number;
  plan_id: number;
  status: string;
  price: string;
  currency: string;
  billing_cycle: string;
  tenant_name: string | null;
  start_date: string;
  current_period_end: string | null;
  cancelled_at: string | null;
  admin_access_reason?: string | null;
  plan: { id?: number; name: string; product_key: string };
};

export type AdminSubscriptionDetails = AdminSubscription & {
  remaining_days: number | null;
  payment_history: Array<{
    id: number;
    status: string;
    amount: string;
    currency: string;
    payment_method: string;
    paid_at: string | null;
    created_at: string;
  }>;
  activity_log: Array<{
    id: number;
    actor_user_id: number | null;
    actor_name: string;
    action: string;
    reason: string | null;
    created_at: string;
    old_value: string | null;
    new_value: string | null;
  }>;
};

export type AdminSubscriptionStatistics = {
  active_subscriptions: number;
  expired_subscriptions: number;
  monthly_revenue: string | null;
  currency: string | null;
  monthly_revenue_by_currency: Record<string, string>;
  pending_payment_requests: number;
  revenue_history: Array<{
    month: string;
    currency: string;
    amount: string;
  }>;
  expiring_soon_count: number;
  expiring_soon: Array<{
    id: number;
    tenant_name: string;
    plan_name: string;
    current_period_end: string;
  }>;
  email_enabled: boolean;
};

export type AdminSubscriptionClient = {
  id: number;
  tenant_id: number | null;
  username: string;
  email: string;
  display_name: string;
};

export type AdminAuditLog = {
  id: number;
  tenant_id: number;
  actor_user_id: number | null;
  action: string;
  target_type: string;
  target_id: string | null;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
};

export type AdminProductGrant = {
  id: number;
  tenant_id: number;
  product_key: string;
  access_type: "trial" | "complimentary";
  starts_at: string;
  expires_at: string | null;
  is_permanent: boolean;
  reason: string;
  granted_by_id: number;
  created_at: string;
  revoked_at: string | null;
  revoked_by_id: number | null;
};

async function adminRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token =
    typeof window === "undefined"
      ? null
      : localStorage.getItem("apexive_token");
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      cache: "no-store",
    });
  } catch (reason) {
    const detail = reason instanceof Error ? ` (${reason.message})` : "";
    throw new Error(`Unable to connect to the backend${detail}.`);
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data: { detail?: string } = await response.json();
      if (data.detail) {
        message = data.detail;
      }
    } catch {
      // Keep the HTTP status message when the error body is not JSON.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function getAdminDashboard(includeAuditLogs = true) {
  const [clients, payments, subscriptions, auditLogs] = await Promise.all([
    adminRequest<{ clients: AdminClient[] }>("/api/admin/clients"),
    adminRequest<{ items: AdminPayment[] }>("/api/admin/payments?limit=500"),
    adminRequest<{ items: AdminSubscription[] }>("/api/admin/subscriptions?limit=500"),
    includeAuditLogs
      ? adminRequest<AdminAuditLog[]>("/api/admin/audit-logs?limit=500")
      : Promise.resolve([]),
  ]);
  return {
    clients: clients.clients,
    payments: payments.items,
    subscriptions: subscriptions.items,
    auditLogs,
  };
}

export function getAdminSubscriptions(filters: {
  search?: string;
  status?: string;
  planId?: number;
} = {}) {
  const params = new URLSearchParams({ limit: "500" });
  if (filters.search?.trim()) params.set("search", filters.search.trim());
  if (filters.status) params.set("status", filters.status);
  if (filters.planId) params.set("plan_id", String(filters.planId));
  return adminRequest<{ items: AdminSubscription[] }>(
    `/api/admin/subscriptions?${params.toString()}`,
  );
}

export function getAdminSubscriptionStatistics() {
  return adminRequest<AdminSubscriptionStatistics>(
    "/api/admin/subscription-statistics",
  );
}

export function sendAdminSubscriptionReminders() {
  return adminRequest<{ processed: number; email_failures: number }>(
    "/api/admin/subscription-reminders",
    { method: "POST" },
  );
}

export function getAdminSubscriptionDetails(subscriptionId: number) {
  return adminRequest<AdminSubscriptionDetails>(
    `/api/admin/subscriptions/${subscriptionId}/details`,
  );
}

export function approveAdminManualSubscription(subscriptionId: number) {
  return adminRequest<AdminSubscription>(
    `/api/admin/subscriptions/${subscriptionId}/approve-manual`,
    { method: "POST" },
  );
}

export function bulkUpdateAdminSubscriptions(payload: {
  action: "extend" | "cancel";
  subscription_ids: number[];
  reason: string;
  duration_days?: number;
}) {
  return adminRequest<{
    action: string;
    count: number;
    subscription_ids: number[];
  }>("/api/admin/subscription-bulk-actions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function downloadAdminReport(path: string, filename: string) {
  const token =
    typeof window === "undefined"
      ? null
      : localStorage.getItem("apexive_token");
  const headers = new Headers({ Accept: "*/*" });
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, {
    headers,
    cache: "no-store",
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data: { detail?: string } = await response.json();
      if (data.detail) message = data.detail;
    } catch {
      // Retain the HTTP status when a download error is not JSON.
    }
    throw new Error(message);
  }
  const objectUrl = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}

export function getAdminSubscriptionPayments() {
  return adminRequest<{ items: AdminPayment[] }>(
    "/api/admin/payments?limit=500",
  );
}

export function getAdminSubscriptionClients() {
  return adminRequest<{ items: AdminSubscriptionClient[] }>(
    "/api/admin/subscription-clients",
  );
}

export function getAdminAccounts() {
  return adminRequest<AdminAccount[]>("/api/admin/accounts");
}

export function createAdminAccount(payload: {
  username: string;
  email: string;
  display_name: string;
  role?: "ADMIN" | "SUPPORT";
}) {
  return adminRequest<{
    admin: AdminAccount;
    temporary_password: string;
  }>("/api/admin/accounts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function setAdminAccountStatus(accountId: number, isActive: boolean) {
  return adminRequest<AdminAccount>(`/api/admin/accounts/${accountId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
}

export function getAdminPlanSettings() {
  return adminRequest<AdminPlan[]>("/api/admin/settings/plans");
}

export function getAdminProductGrants() {
  return adminRequest<{ items: AdminProductGrant[] }>("/api/admin/product-grants");
}

export function createAdminProductGrant(payload: {
  tenant_id: number;
  product_key: string;
  access_type: "trial" | "complimentary";
  starts_at: string;
  expires_at: string | null;
  is_permanent: boolean;
  reason: string;
}) {
  return adminRequest<AdminProductGrant>("/api/admin/product-grants", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function revokeAdminProductGrant(grantId: number) {
  return adminRequest<AdminProductGrant>(
    `/api/admin/product-grants/${grantId}/revoke`,
    { method: "POST" },
  );
}

export function createProductLaunch(productKey: string) {
  return adminRequest<{ url: string; expires_at: string }>(
    `/api/subscriptions/products/${encodeURIComponent(productKey)}/launch`,
    { method: "POST" },
  );
}

export function updateAdminPlanSettings(
  planId: number,
  payload: Partial<
    Pick<
      AdminPlan,
      "name" | "description" | "monthly_price" | "currency" | "billing_cycle" | "is_active"
    >
  >,
) {
  return adminRequest<AdminPlan>(`/api/admin/settings/plans/${planId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function createAdminClient(payload: {
  username: string;
  email: string;
  display_name: string;
  company_name: string;
}) {
  return adminRequest<{
    client: AdminClient;
    temporary_password: string;
  }>("/api/admin/clients", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function setAdminClientStatus(clientId: number, isActive: boolean) {
  return adminRequest(`/api/admin/clients/${clientId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
}

export function approveAdminClient(clientId: number) {
  return adminRequest<{ user_id: number; account_status: string }>(
    `/api/admin/users/${clientId}/approve`,
    { method: "POST" },
  );
}

export function resetAdminClientPassword(clientId: number) {
  return adminRequest<{ user_id: number; username: string; temporary_password: string }>(
    `/api/admin/clients/${clientId}/reset-password`,
    { method: "POST" },
  );
}

export function verifyAdminPayment(paymentId: number) {
  return adminRequest<AdminPayment>(
    `/api/admin/payments/${paymentId}/verify`,
    { method: "POST" },
  );
}

export function rejectAdminPayment(paymentId: number, reason: string) {
  return adminRequest<AdminPayment>(
    `/api/admin/payments/${paymentId}/reject`,
    {
      method: "POST",
      body: JSON.stringify({ reason }),
    },
  );
}

export function refundAdminPayment(paymentId: number) {
  return adminRequest<AdminPayment>(`/api/admin/payments/${paymentId}/refund`, {
    method: "POST",
  });
}

export function updateAdminSubscription(
  subscriptionId: number,
  action: "activate" | "suspend" | "cancel",
  override?: { reason: string },
) {
  return adminRequest<AdminSubscription>(
    `/api/admin/subscriptions/${subscriptionId}/${action}`,
    {
      method: "POST",
      ...(action === "activate"
        ? {
            body: JSON.stringify({
              duration_days: 30,
              ...(override
                ? {
                    override_verified_payment: true,
                    override_reason: override.reason,
                  }
                : {}),
            }),
          }
        : action === "cancel" && override
          ? { body: JSON.stringify({ reason: override.reason }) }
        : {}),
    },
  );
}

export function createAdminSubscription(payload: {
  tenant_id?: number;
  client_id?: number;
  plan_id: number;
  duration_days: number;
  reason: string;
}) {
  return adminRequest<AdminSubscription>("/api/admin/subscriptions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function renewAdminSubscription(
  subscriptionId: number,
  payload: { duration_days: number; reason: string },
) {
  return adminRequest<AdminSubscription>(
    `/api/admin/subscriptions/${subscriptionId}/renew`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function updateAdminSubscriptionPrice(
  subscriptionId: number,
  price: string,
) {
  return adminRequest<AdminSubscription>(
    `/api/admin/subscriptions/${subscriptionId}/price`,
    {
      method: "PATCH",
      body: JSON.stringify({ price }),
    },
  );
}
