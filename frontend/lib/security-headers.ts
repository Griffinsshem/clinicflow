/**
 * Security headers for every page and API route.
 *
 * Two kinds:
 *  - STATIC_SECURITY_HEADERS are the same on every response and are set
 *    in next.config.ts.
 *  - The Content-Security-Policy carries a fresh nonce per request, so it
 *    is built here and set in proxy.ts.
 *
 * The CSP is strict because ClinicFlow shows patient records: a script
 * that slipped into a page (from a compromised dependency, or a name
 * field that ever escaped React's escaping) could read and send them.
 * With this policy only scripts carrying the request's nonce run, and the
 * page can only talk to its own origin.
 */

export const STATIC_SECURITY_HEADERS = [
  // HTTPS only, for two years, including subdomains. Ignored over plain
  // HTTP, so local development is unaffected.
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains",
  },
  // Never guess a content type; a JSON or text response is never run.
  { key: "X-Content-Type-Options", value: "nosniff" },
  // No site may frame ClinicFlow (clickjacking). frame-ancestors in the
  // CSP says the same for modern browsers; this covers older ones.
  { key: "X-Frame-Options", value: "DENY" },
  // Other sites see at most our origin, never a path like /patients/42.
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  // The app needs none of these device features; deny them outright so
  // nothing on the page can ask for them.
  {
    key: "Permissions-Policy",
    value:
      "camera=(), microphone=(), geolocation=(), payment=(), usb=(), " +
      "serial=(), hid=(), browsing-topics=()",
  },
  // A page opened from ClinicFlow can't reach back into it via
  // window.opener, and vice versa.
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
] as const;

export function createNonce(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes));
}

export function buildContentSecurityPolicy({
  nonce,
  isDev,
  isHttps,
}: {
  nonce: string;
  isDev: boolean;
  isHttps: boolean;
}): string {
  const directives = [
    "default-src 'self'",
    // Only scripts carrying this request's nonce, and the scripts they
    // load ('strict-dynamic'). Development needs eval for React's error
    // overlay; production never does.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ""}`,
    // <style> elements need the nonce. Inline style *attributes* are
    // allowed: the dashboard chart sizes its bars with them, and an
    // attribute can't run code.
    `style-src 'self' 'nonce-${nonce}'`,
    "style-src-attr 'unsafe-inline'",
    "img-src 'self' blob: data:",
    // next/font serves the fonts from this origin.
    "font-src 'self'",
    // The browser only ever calls this app's own /api routes; the Flask
    // API is reached server-side. So nothing else is needed, and stolen
    // data has nowhere to be sent.
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ];

  // Only over HTTPS: on http://localhost it would break local testing.
  if (isHttps) {
    directives.push("upgrade-insecure-requests");
  }

  return directives.join("; ");
}
