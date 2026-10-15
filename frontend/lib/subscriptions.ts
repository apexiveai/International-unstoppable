import API_URL from "@/lib/api";

export type SubscriptionPlan = {

  id: number;

  code: string;

  product_key: string;

  name: string;

  description: string;

  monthly_price: string;

  currency: string;

  billing_cycle: string;

  is_active: boolean;

  minimum_contract_months: number | null;

};

export type Subscription = {

  id: number;

  tenant_id: number;

  plan_id: number;

  status: string;

  price: string;

  currency: string;

  billing_cycle: string;

  start_date: string;

  current_period_end: string | null;

  cancelled_at: string | null;

  external_subscription_id: string | null;

  contract_months: number | null;

  contract_end: string | null;

  plan: SubscriptionPlan;

};

export type SubscriptionAccess = {

  product_key: string;

  entitlement_code: string;

  tenant_id: number;

  has_access: boolean;

  source: "subscription" | "enterprise_grant" | null;

  grant_id: number | null;

  access_type: "trial" | "complimentary" | null;

  starts_at: string | null;

  expires_at: string | null;

  is_permanent: boolean;

  subscription_id: number | null;

  status: string | null;

  current_period_end: string | null;

};

export async function createProductLaunch(productKey: string) {
  return apiRequest<{ url: string; expires_at: string }>(
    `/api/subscriptions/products/${encodeURIComponent(productKey)}/launch`,
    { method: "POST" },
  );
}

async function apiRequest<T>(

  path: string,

  options: RequestInit = {},

): Promise<T> {

  const token =

    typeof window !== "undefined"

      ? localStorage.getItem("apexive_token")

      : null;

  const headers = new Headers(options.headers);

  headers.set("Content-Type", "application/json");

  if (token) {

    headers.set("Authorization", `Bearer ${token}`);

  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    });
  } catch (reason) {
    const detail = reason instanceof Error ? ` (${reason.message})` : "";
    throw new Error(
      `Unable to connect to the backend at ${API_URL}${detail}. Verify the backend deployment and NEXT_PUBLIC_API_URL.`,
    );
  }

  if (!response.ok) {

    let message = "Request failed";

    try {

      const data = await response.json();

      if (typeof data?.detail === "string") {

        message = data.detail;

      }

    } catch {

      // Ignore invalid error body.

    }

    throw new Error(message);

  }

  return response.json();

}

export function getSubscriptionPlans() {

  return apiRequest<SubscriptionPlan[]>(

    "/api/subscriptions/plans",

  );

}

export function getMySubscriptions() {

  return apiRequest<Subscription[]>(

    "/api/subscriptions/me",

  );

}

export function getProductAccess(productKey: string) {

  return apiRequest<SubscriptionAccess>(

    `/api/subscriptions/access/${encodeURIComponent(productKey)}`,

  );

}