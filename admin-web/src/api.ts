import type { AdminProductWriteResponse, OpsSummary, Product, ProductListResponse, ProductPayload } from "./types";

const TOKEN_KEY = "buywise_admin_token";

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export async function login(username: string, password: string): Promise<string> {
  const payload = await request<{ access_token: string }>("/api/v1/admin/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password })
  });
  setToken(payload.access_token);
  return payload.access_token;
}

export async function listProducts(params: URLSearchParams): Promise<ProductListResponse> {
  return request<ProductListResponse>(`/api/v1/admin/products?${params.toString()}`);
}

export async function getProduct(productId: number): Promise<Product> {
  return request<Product>(`/api/v1/admin/products/${productId}`);
}

export async function createProduct(payload: ProductPayload): Promise<AdminProductWriteResponse> {
  return request<AdminProductWriteResponse>("/api/v1/admin/products", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateProduct(productId: number, payload: ProductPayload): Promise<AdminProductWriteResponse> {
  return request<AdminProductWriteResponse>(`/api/v1/admin/products/${productId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function deleteProduct(productId: number): Promise<AdminProductWriteResponse> {
  return request<AdminProductWriteResponse>(`/api/v1/admin/products/${productId}`, {
    method: "DELETE"
  });
}

export async function uploadImage(file: File): Promise<{ url: string; filename: string }> {
  const form = new FormData();
  form.append("file", file);
  return request<{ url: string; filename: string }>("/api/v1/admin/upload", {
    method: "POST",
    body: form
  });
}

export async function getOpsSummary(): Promise<OpsSummary> {
  return request<OpsSummary>("/api/v1/admin/ops/summary");
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...init, headers });
  if (!response.ok) {
    const message = await errorMessage(response);
    if (response.status === 401) {
      clearToken();
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string; code?: string };
    return payload.detail || payload.code || `Request failed with ${response.status}`;
  } catch {
    return `Request failed with ${response.status}`;
  }
}
