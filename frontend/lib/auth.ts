import API_URL from "@/lib/api";

export type AuthenticatedUser = {
  id: number;
  username: string;
  email: string;
  display_name: string;
  bio: string;
  is_active: boolean;
  is_admin: boolean;
  is_super_admin: boolean;
  tenant_id: number | null;
  account_status: string;
  role: string;
};

export async function getCurrentUser(
  token: string,
): Promise<AuthenticatedUser | null> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
  } catch (reason) {
    const detail = reason instanceof Error ? ` (${reason.message})` : "";
    throw new Error(`Unable to verify your account with the backend${detail}.`);
  }

  if (response.status === 401 || response.status === 403) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Unable to verify your account (${response.status}).`);
  }

  return (await response.json()) as AuthenticatedUser;
}
