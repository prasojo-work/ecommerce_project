import type { FieldIssue } from "@/api/auth";

/**
 * The auth forms' rules, kept out of the components so they can be tested directly (`US-2.1`,
 * `US-2.2`, `UX.md` flow D).
 *
 * Two jobs, both of which are easy to get subtly wrong:
 *
 * 1. **Check what can be checked before the request.** Cheap, and it stops an avoidable round trip.
 *    What it deliberately does *not* do is re-implement the server's password policy — the server
 *    owns that (`AUTH_PASSWORD_VALIDATORS`, `ADR-0011`) and its answer is authoritative. This checks
 *    the one rule it is allowed to duplicate, the 8-character minimum, and only because a round trip
 *    to be told "too short" is a worse experience than knowing immediately.
 * 2. **Map the API's field errors onto the inputs.** `details` arrives in two different shapes and
 *    the difference is not obvious: pydantic failures come back with the parameter source prefixed
 *    (`body.email`, which `core/errors.py` documents as deliberate), while errors the endpoint
 *    raises itself are bare (`email`, as `API.md` section 3 shows). A mapping that only understands
 *    one of the two silently drops the other — so `email` for an address that is already registered
 *    would never reach the form, which is precisely the state `UX.md` flow D calls out.
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

/** The prefixes Ninja puts in front of a pydantic error location. */
const SOURCE_PREFIXES = ["body.", "query.", "path.", "header.", "cookie."];

/** `body.email` and `email` both mean the input called `email`. */
export function fieldOf(reported: string): string {
  const prefix = SOURCE_PREFIXES.find((candidate) => reported.startsWith(candidate));
  return prefix === undefined ? reported : reported.slice(prefix.length);
}

/** The first issue reported per field, which is the one worth showing. */
export function fieldMessages(details: FieldIssue[]): Record<string, string> {
  const messages: Record<string, string> = {};
  for (const detail of details) {
    const field = fieldOf(detail.field);
    if (field !== "" && messages[field] === undefined) {
      messages[field] = detail.issue;
    }
  }
  return messages;
}

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

/**
 * What to show when the request itself failed.
 *
 * The API's own message is used wherever there is one, because it knows more than this layer does.
 * The rate limit is the exception: `Too many requests.` states the fact but not what to do about it,
 * and `UX.md` flow D asks for that state to be handled rather than merely reported.
 */
export function messageForFailure(status: number, message: string): string {
  if (status === 429) {
    return "Too many attempts. Please wait a moment and try again.";
  }
  return message;
}
