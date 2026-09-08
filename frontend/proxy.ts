import { NextResponse, type NextRequest } from "next/server";


const SESSION_COOKIE = "clinicflow_session";

const AUTH_ROUTES = ["/login", "/register"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
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
    "/dashboard/:path*",
    "/patients/:path*",
    "/appointments/:path*",
    "/follow-ups/:path*",
    "/login",
    "/register",
  ],
};
