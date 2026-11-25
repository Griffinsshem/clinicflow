import { NextResponse, type NextRequest } from "next/server";

import { isCrossSiteMutation } from "@/lib/origin";
import { buildContentSecurityPolicy, createNonce } from "@/lib/security-headers";


const SESSION_COOKIE = "clinicflow_session";

const AUTH_ROUTES = ["/login", "/register"];

// Pages that need a signed-in user. Everything else (landing page,
// 404s) is public.
const PROTECTED_PREFIXES = ["/dashboard", "/patients", "/appointments", "/follow-ups"];

function isProtected(pathname: string): boolean {
  return PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

/**
 * Let the page render, with a fresh CSP nonce.
 *
 * The policy goes on the request too: Next.js reads the nonce from it and
 * stamps it onto its own scripts and styles while rendering. See
 * lib/security-headers.ts for what the policy allows.
 */
function renderWithCsp(request: NextRequest): NextResponse {
  const nonce = createNonce();
  const policy = buildContentSecurityPolicy({
    nonce,
    isDev: process.env.NODE_ENV === "development",
    isHttps: request.nextUrl.protocol === "https:",
  });

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", policy);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", policy);
  return response;
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Every state-changing call to our own API must come from this site.
  // Checked here, once, so a route handler added later cannot forget it.
  // See lib/origin.ts for why sameSite=lax alone is not enough.
  if (pathname.startsWith("/api/")) {
    if (isCrossSiteMutation(request)) {
      return NextResponse.json(
        { success: false, message: "Request blocked." },
        { status: 403 },
      );
    }
    return NextResponse.next();
  }
  const hasSession = request.cookies.has(SESSION_COOKIE);

  const isAuthRoute = AUTH_ROUTES.some((route) => pathname.startsWith(route));

  if (isAuthRoute) {
    if (hasSession) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
    return renderWithCsp(request);
  }

  if (!isProtected(pathname)) {
    return renderWithCsp(request);
  }

  if (!hasSession) {
    const loginUrl = new URL("/login", request.url);

    if (pathname !== "/dashboard") {
      loginUrl.searchParams.set("next", pathname);
    }
    return NextResponse.redirect(loginUrl);
  }

  return renderWithCsp(request);
}

export const config = {
  // Every page and API route, so every page gets a CSP. Built assets
  // (_next/static, _next/image) and files with an extension (favicon,
  // images) are skipped: they are not pages and need no policy.
  matcher: ["/((?!_next/static|_next/image|.*\\.[a-zA-Z0-9]+$).*)"],
};
