import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
    const body = await request.json();

    const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message: body.message,
            user_id: body.user_id || "default_user",
        })
    })

    const data = await response.json();
    return NextResponse.json(data);
}