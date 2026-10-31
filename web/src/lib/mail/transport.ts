/**
 * Pluggable mail transport. The OTP route only talks to this interface, so
 * swapping Gmail SMTP for Resend (or anything else) later is a one-file
 * change — see `resendTransport` below for the shape a future
 * implementation would take.
 */

export interface SendMailParams {
  to: string;
  subject: string;
  text: string;
  html?: string;
}

export interface MailTransport {
  send(params: SendMailParams): Promise<void>;
}

let cachedTransport: MailTransport | null = null;

export async function getMailTransport(): Promise<MailTransport> {
  if (cachedTransport) return cachedTransport;
  cachedTransport = await createGmailSmtpTransport();
  return cachedTransport;
}

async function createGmailSmtpTransport(): Promise<MailTransport> {
  // Imported lazily (dynamic import) so this module has no hard nodemailer
  // dependency at module-load time for environments (tests) that stub
  // `getMailTransport`.
  const { default: nodemailer } = await import("nodemailer");

  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_APP_PASSWORD;

  if (!user || !pass) {
    throw new Error(
      "SMTP_USER / SMTP_APP_PASSWORD are not set. Copy .env.example to .env and fill them in " +
        "(a Gmail address + an App Password from https://myaccount.google.com/apppasswords).",
    );
  }

  const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: { user, pass },
  });

  return {
    async send({ to, subject, text, html }: SendMailParams) {
      await transporter.sendMail({ from: user, to, subject, text, html });
    },
  };
}

// --- Future swap-in target -------------------------------------------------
// When ready to move off Gmail SMTP:
//
//   function createResendTransport(): MailTransport {
//     const { Resend } = require("resend");
//     const resend = new Resend(process.env.RESEND_API_KEY);
//     return {
//       async send({ to, subject, text, html }) {
//         await resend.emails.send({ from: "LPMF <noreply@yourdomain>", to, subject, text, html });
//       },
//     };
//   }
//
// ...and change `createGmailSmtpTransport()` to `createResendTransport()`
// in `getMailTransport` above. No other file needs to change.
