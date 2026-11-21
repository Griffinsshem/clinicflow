/**
 * Cross-site request protection for the app's own /api routes.
 *
 * The session cookie is sameSite=lax, which stops the browser *sending*
 * it on cross-site POSTs. That protects authenticated calls, but not the
 * routes that *set* the cookie. Another site could auto-submit a hidden
 * form to /api/auth/login and sign a visitor into an attacker's account
 * ("login CSRF"), start a demo session for them, or sign them out. A
 * form can even smuggle a JSON body by posting it as text/plain.
 *
 * Browsers always send an Origin header on POST, PATCH, PUT and DELETE,
 * and a page cannot forge it. So every state-changing request must carry
 * an Origin equal to our own; anything else, including a missing or
 * "null" Origin, is refused.
 */

export const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/**
 * Compares the Origin's host with the host the browser addressed.
 *
 * Deliberately not `new URL(request.url).origin`: the server rebuilds
 * request.url from its own idea of its hostname (often "localhost"),
 * not from what the browser used, so a legitimate request to
 * 127.0.0.1 or via a proxied domain would be refused. The Host header
 * (or x-forwarded-host, which Vercel sets from the real request) is
 * what the browser actually sent, and a cross-site page cannot make
 * the browser send an Origin that matches it.
 */
export function isSameOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) {
    return false;
  }

  let originHost: string;
  try {
    originHost = new URL(origin).host;
  } catch {
    return false; // includes the opaque "null" origin
  }

  const requestHost =
    request.headers.get("x-forwarded-host")?.split(",")[0]?.trim() ||
    request.headers.get("host");

  return Boolean(requestHost) && originHost === requestHost;
}

/** True when the request changes state and did not come from this site. */
export function isCrossSiteMutation(request: Request): boolean {
  return MUTATING_METHODS.has(request.method) && !isSameOrigin(request);
}
