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
    adminRequest<{ items: AdminPayment[] }>("/api/admin/payments"),
    adminRequest<{ items: AdminSubscription[] }>("/api/admin/subscriptions"),
    adminRequest<AdminAuditLog[]>("/api/admin/audit-logs"),
  ]);
  return {
    clients: clients.clients,
    payments: payments.items,
    subscriptions: subscriptions.items,
    auditLogs,
  };
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
