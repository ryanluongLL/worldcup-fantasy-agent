import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const maxDuration = 60;

export async function POST(request: NextRequest) {
  const body = await request.json();
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: body.message,
      user_id: body.user_id || "default_user",
    }),
    signal: AbortSignal.timeout(55000),
  });
  const data = await response.json();
  return NextResponse.json(data);
}