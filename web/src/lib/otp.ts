import { randomInt } from "crypto";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/prisma";

export const OTP_TTL_MINUTES = 10;
export const OTP_MAX_ATTEMPTS = 5;
export const OTP_RATE_LIMIT_SENDS = 3;
export const OTP_RATE_LIMIT_WINDOW_MINUTES = 15;

const BCRYPT_ROUNDS = 10;

/** A cryptographically random 6-digit code, zero-padded. */
export function generateOtpCode(): string {
  return randomInt(0, 1_000_000).toString().padStart(6, "0");
}

export async function hashOtpCode(code: string): Promise<string> {
  return bcrypt.hash(code, BCRYPT_ROUNDS);
}

export async function compareOtpCode(code: string, hash: string): Promise<boolean> {
  return bcrypt.compare(code, hash);
}

export class OtpRateLimitError extends Error {}
export class OtpInvalidError extends Error {}
export class OtpExpiredError extends Error {}
export class OtpTooManyAttemptsError extends Error {}

/**
 * Create and persist a new OTP for `email`, enforcing the send rate limit
 * (3 sends per email per 15 min). Returns the plaintext code so the caller
 * can email it — it is never stored in plaintext.
 */
export async function createOtp(email: string): Promise<string> {
  const windowStart = new Date(Date.now() - OTP_RATE_LIMIT_WINDOW_MINUTES * 60_000);
  const recentSends = await prisma.verificationOtp.count({
    where: { email, createdAt: { gte: windowStart } },
  });
  if (recentSends >= OTP_RATE_LIMIT_SENDS) {
    throw new OtpRateLimitError(
      `Too many OTP requests for this email. Try again in ${OTP_RATE_LIMIT_WINDOW_MINUTES} minutes.`,
    );
  }

  const code = generateOtpCode();
  const codeHash = await hashOtpCode(code);
  const expiresAt = new Date(Date.now() + OTP_TTL_MINUTES * 60_000);

  await prisma.verificationOtp.create({
    data: { email, codeHash, expiresAt },
  });

  return code;
}

/**
 * Verify `code` against the most recent unconsumed OTP for `email`.
 * On success the row is consumed (deleted) and this returns normally.
 * On failure it increments `attempts` and throws a typed error.
 */
export async function verifyOtp(email: string, code: string): Promise<void> {
  const otp = await prisma.verificationOtp.findFirst({
    where: { email, consumedAt: null },
    orderBy: { createdAt: "desc" },
  });

  if (!otp) {
    throw new OtpInvalidError("No pending verification code for this email.");
  }

  if (otp.expiresAt < new Date()) {
    throw new OtpExpiredError("This verification code has expired. Request a new one.");
  }

  if (otp.attempts >= OTP_MAX_ATTEMPTS) {
    throw new OtpTooManyAttemptsError("Too many incorrect attempts. Request a new code.");
  }

  const matches = await compareOtpCode(code, otp.codeHash);
  if (!matches) {
    await prisma.verificationOtp.update({
      where: { id: otp.id },
      data: { attempts: { increment: 1 } },
    });
    throw new OtpInvalidError("Incorrect verification code.");
  }

  // Delete/consume the OTP row on success (spec: "Delete/consume the OTP
  // row on success"). A soft `consumedAt` stamp first would also work, but
  // deleting is the simplest reading of that requirement.
  await prisma.verificationOtp.delete({ where: { id: otp.id } });
}
