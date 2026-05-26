import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const { userId } = await params;
  const matchday = request.nextUrl.searchParams.get("matchday") || "1";
  const response = await fetch(`${API_URL}/lineup/${userId}?matchday=${matchday}`);
  const data = await response.json();
  return NextResponse.json(data);
}