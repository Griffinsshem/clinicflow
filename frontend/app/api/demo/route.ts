import { NextResponse } from "next/server";

import { callBackend } from "@/lib/backend";
import { setSessionCookie } from "@/lib/session";
import type { AuthPayload } from "@/types/api";


export async function POST(request: Request) {
  const { searchParams } = new URL(request.url);
  const offset = searchParams.get("tz_offset") ?? "0";

  const { status, body } = await callBackend<AuthPayload>(
    `/demo?tz_offset=${encodeURIComponent(offset)}`,
    { method: "POST" },
  );

  if (!body.success) {
    return NextResponse.json(body, { status });
  }

  await setSessionCookie(body.data.access_token, body.data.expires_in);

  return NextResponse.json({ success: true, data: { clinic: body.data.clinic } });
}
