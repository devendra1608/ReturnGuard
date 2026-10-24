
import { getToken } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL;

async function proxyRequest(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const token = await getToken({
    req: request,
    secret: process.env.AUTH_SECRET,
  });

  if (!token) {
  return NextResponse.json(
    { detail: "Auth.js session token could not be decoded." },
    { status: 401 }
  );
}

if (!token.accessToken) {
  return NextResponse.json(
    {
      detail: "Session exists, but its accessToken field is missing.",
      tokenFields: Object.keys(token),
    },
    { status: 401 }
  );
}

  if (!BACKEND_URL) {
    return NextResponse.json(
      { detail: "Backend URL is not configured." },
      { status: 500 }
    );
  }

  const { path } = await context.params;

  // Restrict this proxy to the returns API.
  if (path[0] !== "returns") {
    return NextResponse.json(
      { detail: "This backend path is not allowed." },
      { status: 404 }
    );
  }

  const targetUrl = new URL(
    `${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`,
    `${BACKEND_URL.replace(/\/+$/, "")}/`
  );

  const headers = new Headers();
  headers.set("Authorization", `Bearer ${token.accessToken}`);

  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  try {
    const backendResponse = await fetch(targetUrl, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
    });

    return new Response(backendResponse.body, {
      status: backendResponse.status,
      headers: {
        "Content-Type":
          backendResponse.headers.get("content-type") ??
          "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend service." },
      { status: 502 }
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
