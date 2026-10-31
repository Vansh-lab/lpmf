import NextAuth from "next-auth";
import { NextResponse } from "next/server";
import { authConfig } from "@/lib/auth.config";

// Middleware runs in the Edge runtime, so it builds its own lightweight
// `auth()` straight from the edge-safe `authConfig` (no Prisma adapter, no
// Credentials provider / bcryptjs) rather than importing the full config
// in lib/auth.ts. It only needs to read the session JWT, not run any
// provider logic.
const { auth } = NextAuth(authConfig);

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const isLoggedIn = !!req.auth;
  const isLoginPage = pathname === "/login";

  if (!isLoggedIn && !isLoginPage) {
    const loginUrl = new URL("/login", req.nextUrl.origin);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (isLoggedIn && isLoginPage) {
    return NextResponse.redirect(new URL("/dashboard", req.nextUrl.origin));
  }

  return NextResponse.next();
});

export const config = {
  // Protect every route except /login, static assets, Next.js internals,
  // and the Auth.js / OTP API routes (which must themselves be reachable
  // while signed out).
  matcher: ["/((?!api/auth|_next/static|_next/image|favicon.ico).*)"],
};
