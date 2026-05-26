import { NextResponse } from "next/server";

export async function GET() {
    const response = await fetch("http://localhost:8000/top-performers?limit=10");
    const data = await response.json();
    return NextResponse.json(data);
}

