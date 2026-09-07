import { NextResponse } from "next/server";

import { callBackend } from "@/lib/backend";
import { clearSessionCookie, getSessionToken } from "@/lib/session";


const MUTATING_METHODS = new Set(["POST", "PATCH", "PUT", "DELETE"]);


function isSameOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) {
    return false;
  }
  return origin === new URL(request.url).origin;
}

async function handle(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;

  if (MUTATING_METHODS.has(request.method) && !isSameOrigin(request)) {
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
