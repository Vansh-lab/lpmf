import type { NextAuthConfig } from "next-auth";

/**
 * Edge-safe subset of the Auth.js config: no Prisma adapter, no
 * Credentials provider (which pulls in bcryptjs/crypto). This is the only
 * config middleware.ts may import, since middleware runs in the Edge
 * runtime. The full config (lib/auth.ts) extends this with the adapter and
 * both providers, and is only ever imported from Node.js-runtime code
 * (route handlers, server components).
 */
export const authConfig: NextAuthConfig = {
  session: { strategy: "jwt" },
  pages: {
    signIn: "/login",
  },
  providers: [],
};
