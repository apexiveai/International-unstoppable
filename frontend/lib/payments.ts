const API_URL =

  process.env.NEXT_PUBLIC_API_URL ||

  "https://api.apexiveai.com";

export type PaymentMethod =

  | "card"

  | "kbzpay"

  | "cbpay"

  | "ayapay"

  | "mpu";

export type PaymentStatus =

  | "pending"

  | "processing"

  | "paid"

  | "failed"

  | "cancelled"

  | "refunded";

export type CreatePaymentResponse = {

  id: number;

  tenant_id: number;

  plan_id: number;

  subscription_id: number | null;

  provider: string;

  payment_method: string;

  status: PaymentStatus;

  amount: string;

  currency: string;

  checkout_reference: string | null;

  external_payment_id: string | null;

  failure_reason: string | null;

  paid_at: string | null;

  created_at: string;

};

type ApiErrorResponse = {

  detail?: string;

};

function getAuthToken(): string | null {

  if (typeof window === "undefined") {

    return null;

  }

  return localStorage.getItem("apexive_token");

}

async function apiRequest<T>(

  path: string,

  options: RequestInit = {},

): Promise<T> {

  const token = getAuthToken();

  const headers = new Headers(options.headers);

  headers.set("Accept", "application/json");

  if (options.body) {

    headers.set("Content-Type", "application/json");

  }

  if (token) {

    headers.set(

      "Authorization",

      `Bearer ${token}`,

    );

  }

  const response = await fetch(

    `${API_URL}${path}`,

    {

      ...options,

      headers,

      cache: "no-store",

    },

  );

  if (!response.ok) {

    let message =

      `Payment request failed (${response.status})`;

    try {

      const data =

        (await response.json()) as ApiErrorResponse;

      if (

        data &&

        typeof data.detail === "string" &&

        data.detail.trim()

      ) {

        message = data.detail;

      }

    } catch {

      // Keep default error message.

    }

    throw new Error(message);

  }

  return response.json() as Promise<T>;

}

/**

 * Create a pending payment session.

 *

 * IMPORTANT:

 * This endpoint only creates the internal Apexive

 * payment record. It does NOT mark the subscription as paid.

 *

 * Actual payment gateway processing must happen after

 * this step.

 */

export async function createPayment(

  planId: number,

  paymentMethod: PaymentMethod,

): Promise<CreatePaymentResponse> {

  if (!Number.isInteger(planId) || planId <= 0) {

    throw new Error("Invalid subscription plan.");

  }

  if (!paymentMethod) {

    throw new Error("Payment method is required.");

  }

  return apiRequest<CreatePaymentResponse>(

    "/api/payments/create",

    {

      method: "POST",

      body: JSON.stringify({

        plan_id: planId,

        payment_method: paymentMethod,

      }),

    },

  );

}

/**

 * Retrieve one payment.

 */

export async function getPayment(

  paymentId: number,

): Promise<CreatePaymentResponse> {

  if (!Number.isInteger(paymentId) || paymentId <= 0) {

    throw new Error("Invalid payment ID.");

  }

  return apiRequest<CreatePaymentResponse>(

    `/api/payments/${paymentId}`,

    {

      method: "GET",

    },

  );

}

/**

 * Get the current payment status.

 */

export async function getPaymentStatus(

  paymentId: number,

): Promise<PaymentStatus> {

  const payment =

    await getPayment(paymentId);

  return payment.status;

}