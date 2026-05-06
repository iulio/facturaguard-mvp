export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000").replace(/\/+$/, "");

export function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("fg_token") || "";
}

export function setToken(token: string) {
  localStorage.setItem("fg_token", token);
}

export function clearToken() {
  localStorage.removeItem("fg_token");
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const headers = new Headers(options.headers || {});
  const token = getToken();

  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE}${normalizedPath}`, { ...options, headers });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "A apărut o eroare.");
  }

  return response.json();
}
