import "server-only";

/**
 * The visitor's IP address, for the API's rate limits.
 *
 * Every API call is made by this Next.js server, so Flask only ever sees
 * Vercel's outbound addresses. Without forwarding the real one, all
 * visitors share a few rate-limit buckets and one person can use up the
 * demo or login limit for everyone.
 *
 * On Vercel, x-real-ip and x-forwarded-for are set by the platform's edge
 * and overwrite anything the client sent, so they can be trusted here.
 * Locally they are usually absent, and the API falls back to the
 * connecting address.
 */
export function clientIp(request: Request): string | null {
  const realIp = request.headers.get("x-real-ip")?.trim();
  if (realIp) {
    return realIp;
  }

  const forwardedFor = request.headers.get("x-forwarded-for");
  const first = forwardedFor?.split(",")[0]?.trim();
  return first || null;
}
