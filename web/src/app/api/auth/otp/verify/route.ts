import { NextResponse } from "next/server";
import { AuthError } from "next-auth";
import { signIn } from "@/lib/auth";

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const email = (body as { email?: string })?.email?.trim().toLowerCase();
  const code = (body as { code?: string })?.code?.trim();

  if (!email || !code) {
    return NextResponse.json({ error: "Email and code are required." }, { status: 400 });
  }

  try {
    // Delegates to the "email-otp" Credentials provider (see lib/auth.ts),
    // which calls verifyOtp() and, on success, creates the session cookie
    // on this same response.
    await signIn("email-otp", { email, code, redirect: false });
    return NextResponse.json({ ok: true });
  } catch (err) {
    if (err instanceof AuthError) {
      return NextResponse.json({ error: "Incorrect or expired code." }, { status: 401 });
    }
    console.error("otp/verify failed:", err);
    return NextResponse.json({ error: "Could not verify the code. Try again." }, { status: 500 });
  }
}
