// frontend/lib/api.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * A wrapper around fetch that automatically appends the Authorization Bearer token.
 */
export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem("token");
  
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  // Ensure the URL starts with a slash if not a full URL
  const url = endpoint.startsWith("http") ? endpoint : `${API_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  // Optional: Add global 401 handling to auto-logout
  if (response.status === 401) {
    // We could clear localStorage and redirect to login, but let components handle their own logic or we can do it here.
    console.warn("Unauthorized request, token may be expired.");
  }
  
  return response;
}
