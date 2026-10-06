import API_URL from "@/lib/api";

export type AdminClient = {
  id: number;
  tenant_id: number | null;
  username: string;
  email: string;
  display_name: string;
  company_name: string | null;
  is_active: boolean;
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
  plan: { name: string; product_key: string };
  current_period_end: string | null;
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

export async function getAdminDashboard() {
  const [clients, payments, subscriptions, auditLogs] = await Promise.all([
    adminRequest<{ clients: AdminClient[] }>("/api/admin/clients"),
    adminRequest<{ items: AdminPayment[] }>("/api/admin/payments?limit=500"),
    adminRequest<{ items: AdminSubscription[] }>("/api/admin/subscriptions?limit=500"),
    adminRequest<AdminAuditLog[]>("/api/admin/audit-logs?limit=500"),
  ]);
  return {
    clients: clients.clients,
    payments: payments.items,
    subscriptions: subscriptions.items,
    auditLogs,
  };
}

export function getAdminAccounts() {
  return adminRequest<AdminAccount[]>("/api/admin/accounts");
}

export function createAdminAccount(payload: {
  username: string;
  email: string;
  display_name: string;
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
) {
  return adminRequest<AdminSubscription>(
    `/api/admin/subscriptions/${subscriptionId}/${action}`,
    {
      method: "POST",
      ...(action === "activate"
        ? { body: JSON.stringify({ duration_days: 30 }) }
        : {}),
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
