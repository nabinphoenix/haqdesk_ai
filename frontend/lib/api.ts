// frontend/lib/api.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const NETWORK_RETRY_DELAY_MS = 400;

function wait(ms: number) {
  return new Promise<void>((resolve) => window.setTimeout(resolve, ms));
}

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
  
  // Strip the Next.js-only "no-store" cache value — it is not a valid
  // browser RequestCache value and causes fetch() to throw a TypeError.
  // Cache-busting is handled via ?t=Date.now() query params instead.
  const { cache: _cache, ...restOptions } = options;
  const requestOptions = { ...restOptions, headers };
  const method = (options.method || "GET").toUpperCase();
  let response: Response;

  try {
    response = await fetch(url, requestOptions);
  } catch (error) {
    // Next/FastAPI development servers briefly drop connections while
    // reloading. Retry read-only requests once, but never repeat a mutation.
    const isAbort = error instanceof DOMException && error.name === "AbortError";
    if (method !== "GET" || isAbort) throw error;

    await wait(NETWORK_RETRY_DELAY_MS);
    try {
      response = await fetch(url, requestOptions);
    } catch (retryError) {
      throw new TypeError(
        `Cannot reach the backend API at ${API_URL}. Make sure the FastAPI server is running.`,
        { cause: retryError },
      );
    }
  }
  
  // Optional: Add global 401 handling to auto-logout
  if (response.status === 401) {
    // We could clear localStorage and redirect to login, but let components handle their own logic or we can do it here.
    console.warn("Unauthorized request, token may be expired.");
  }
  
  return response;
}
