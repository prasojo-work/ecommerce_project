/**
 * The auth forms' rules, kept out of the components so they can be tested directly (`US-2.1`,
 * `US-2.2`, `UX.md` flow D).
 *
 * What this checks before the request, and what it deliberately does not: it does not re-implement
 * the server's password policy — the server owns that (`AUTH_PASSWORD_VALIDATORS`, `ADR-0011`) and
 * its answer is authoritative. It checks the one rule it is allowed to duplicate, the 8-character
 * minimum, and only because a round trip to be told "too short" is a worse experience than knowing
 * immediately.
 *
 * Reading the API's answer — the envelope, and the two shapes a field name arrives in — moved to
 * `lib/api-failure.ts`, because the address form needs exactly the same two things and a copy per
 * form is a copy that can drift.
 */

export type AuthMode = "login" | "register";

export type AuthValues = {
  email: string;
  password: string;
  displayName: string;
};

export type AuthField = keyof AuthValues;

export type FieldMessages = Partial<Record<AuthField, string>>;

/** Django's `MinimumLengthValidator` default, which `config/settings/base.py` relies on. */
export const MIN_PASSWORD_LENGTH = 8;

const EMAIL_SHAPE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validate(mode: AuthMode, values: AuthValues): FieldMessages {
  const messages: FieldMessages = {};

  const email = values.email.trim();
  if (email === "") {
    messages.email = "Enter your email address.";
  } else if (!EMAIL_SHAPE.test(email)) {
    messages.email = "That does not look like an email address.";
  }

  if (values.password === "") {
    messages.password = "Enter your password.";
  } else if (mode === "register" && values.password.length < MIN_PASSWORD_LENGTH) {
    // The server would say the same thing; saying it without a round trip is the whole point.
    messages.password = `Use at least ${MIN_PASSWORD_LENGTH} characters.`;
  }

  // `display_name` is not checked: the API defaults it to empty, so requiring it here would reject
  // registrations the server would have accepted.
  return messages;
}
