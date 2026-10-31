import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";
import { PrismaAdapter } from "@auth/prisma-adapter";
import { prisma } from "@/lib/prisma";
import { verifyOtp, OtpInvalidError, OtpExpiredError, OtpTooManyAttemptsError } from "@/lib/otp";
import { authConfig } from "@/lib/auth.config";

// Full Auth.js config: Prisma adapter + both providers. This file uses
// Node.js APIs (bcryptjs, Prisma) and must only be imported from Node.js
// runtime code (route handlers, server components) — never from
// middleware.ts, which imports the edge-safe `authConfig` directly instead.
export const { handlers, signIn, signOut, auth } = NextAuth({
  ...authConfig,
  adapter: PrismaAdapter(prisma),
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
    Credentials({
      id: "email-otp",
      name: "Email code",
      credentials: {
        email: { label: "Email", type: "email" },
        code: { label: "Code", type: "text" },
      },
      async authorize(credentials) {
        const email = credentials?.email as string | undefined;
        const code = credentials?.code as string | undefined;
        if (!email || !code) return null;

        try {
          await verifyOtp(email, code);
        } catch (err) {
          if (
            err instanceof OtpInvalidError ||
            err instanceof OtpExpiredError ||
            err instanceof OtpTooManyAttemptsError
          ) {
            // Returning null surfaces as a generic "CredentialsSignin"
            // error to the client; the OTP route itself returns the
            // specific reason for UI messaging before this is ever hit.
            return null;
          }
          throw err;
        }

        const user = await prisma.user.upsert({
          where: { email },
          update: { emailVerified: new Date() },
          create: { email, emailVerified: new Date() },
        });

        return { id: user.id, email: user.email };
      },
    }),
  ],
});
