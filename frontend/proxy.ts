import { NextResponse, type NextRequest } from "next/server";

import { isCrossSiteMutation } from "@/lib/origin";


const SESSION_COOKIE = "clinicflow_session";

const AUTH_ROUTES = ["/login", "/register"];

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
    return NextResponse.next();
  }

  if (!hasSession) {
    const loginUrl = new URL("/login", request.url);

    if (pathname !== "/dashboard") {
      loginUrl.searchParams.set("next", pathname);
    }
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  
  matcher: [
    "/api/:path*",
    "/dashboard/:path*",
    "/patients/:path*",
    "/appointments/:path*",
    "/follow-ups/:path*",
    "/login",
    "/register",
  ],
};
