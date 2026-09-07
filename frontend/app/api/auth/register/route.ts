import { NextResponse } from "next/server";

import { callBackend } from "@/lib/backend";
import { setSessionCookie } from "@/lib/session";
import type { AuthPayload } from "@/types/api";

export async function POST(request: Request) {
  const payload = await request.json().catch(() => null);

  const { status, body } = await callBackend<AuthPayload>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!body.success) {
    return NextResponse.json(body, { status });
  }

  await setSessionCookie(body.data.access_token, body.data.expires_in);

  return NextResponse.json(
    {
      success: true,
      data: { user: body.data.user, clinic: body.data.clinic },
    },
    { status: 201 },
  );
}
