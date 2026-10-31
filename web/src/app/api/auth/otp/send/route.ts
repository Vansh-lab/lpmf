import { NextResponse } from "next/server";
import { createOtp, OtpRateLimitError, OTP_TTL_MINUTES } from "@/lib/otp";
import { getMailTransport } from "@/lib/mail/transport";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const email = (body as { email?: string })?.email?.trim().toLowerCase();
  if (!email || !EMAIL_RE.test(email)) {
    return NextResponse.json({ error: "Enter a valid email address." }, { status: 400 });
  }

  try {
    const code = await createOtp(email);

    const transport = await getMailTransport();
    await transport.send({
      to: email,
      subject: "Your LPMF sign-in code",
      text: `Your LPMF sign-in code is ${code}. It expires in ${OTP_TTL_MINUTES} minutes.`,
      html: `<p>Your LPMF sign-in code is <strong style="font-size:1.25em;letter-spacing:0.1em">${code}</strong>.</p><p>It expires in ${OTP_TTL_MINUTES} minutes.</p>`,
    });

    return NextResponse.json({ ok: true });
  } catch (err) {
    if (err instanceof OtpRateLimitError) {
      return NextResponse.json({ error: err.message }, { status: 429 });
    }
    console.error("otp/send failed:", err);
    return NextResponse.json({ error: "Could not send the code. Try again." }, { status: 500 });
  }
}
