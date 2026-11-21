import { NextResponse } from "next/server";

import { callBackend } from "@/lib/backend";
import { clientIp } from "@/lib/client-ip";
import { MUTATING_METHODS, isCrossSiteMutation } from "@/lib/origin";
import { clearSessionCookie, getSessionToken } from "@/lib/session";

async function handle(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;

  // Also enforced for all /api routes in proxy.ts; kept here as a second
  // layer because this route forwards the session token.
  if (isCrossSiteMutation(request)) {
    return NextResponse.json(
      { success: false, message: "Request blocked." },
      { status: 403 },
    );
  }

  const token = await getSessionToken();
  if (!token) {
    return NextResponse.json(
      { success: false, message: "Please sign in to continue." },
      { status: 401 },
    );
  }

  const search = new URL(request.url).search;
  const target = `/${path.join("/")}${search}`;

  const body = MUTATING_METHODS.has(request.method)
    ? await request.text()
    : undefined;

  const result = await callBackend(
    target,
    { method: request.method, body: body || undefined },
    token,
    clientIp(request),
  );

  const response = NextResponse.json(result.body, { status: result.status });

  if (result.status === 401) {
    await clearSessionCookie();
  }

  return response;
}

export const GET = handle;
export const POST = handle;
export const PATCH = handle;
export const DELETE = handle;
