import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const { userId } = await params;
  const matchday = request.nextUrl.searchParams.get("matchday") || "1";
  const response = await fetch(
    `http://localhost:8000/lineup/${userId}?matchday=${matchday}`
  );
  const data = await response.json();
  return NextResponse.json(data);
}