import API_URL from "@/lib/api";

export type ClientProduct = {
  product_key: string;
  product_name: string;
  url: string;
};

export async function getClientProducts(): Promise<ClientProduct[]> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/client/products`, {
      cache: "no-store",
    });
  } catch (reason) {
    const detail = reason instanceof Error ? ` (${reason.message})` : "";
    throw new Error(`Unable to connect to the backend${detail}.`);
  }
  if (!response.ok) {
    throw new Error(`Unable to load product catalog (${response.status}).`);
  }
  const data: { products: ClientProduct[] } = await response.json();
  return data.products;
}
