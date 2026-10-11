/**
 * The `API.md` section 3 error envelope, and the two things every form does with it.
 *
 * Both are shared because both fail quietly when they are wrong:
 *
 * 1. **Reading the envelope.** `details` is what lets a form point at the field the API rejected —
 *    which is the difference between "your postal code is too long" beside the input and a shrug at
 *    the top of the page. The shape is narrowed rather than asserted, because not everything that
 *    answers a request is the API: a proxy or a cold start can return HTML, and a form that crashes
 *    on that is a worse failure than one that says it could not reach the server.
 * 2. **Mapping the field names.** Errors arrive in two shapes and nothing in the payload says which
 *    is which. A pydantic failure carries the parameter source (`body.postal_code`, which
 *    `core/errors.py` deliberately reduces to bare `body.` for all of them), while an error the
 *    endpoint raises itself is bare (`email`, as `API.md` section 3 shows for an address that is
 *    already registered). A mapper that understands one shape drops the other in silence, which is
 *    how a duplicate address would have shown nothing beside the input. The shape a *pydantic* body
 *    error arrives in was itself wrong until `M2.6` sent it as `body.payload.country` — the view
 *    parameter's name, which no client has a field for — and `core/errors.py` now drops it. So the
 *    form-facing rule is: take everything after the source prefix and use that as the field name.
 *
 * These lived in `lib/auth-form.ts` until a second form needed them. Nothing here is about signing
 * in, so they moved rather than being imported across, and the tests moved beside them.
 */

export type FieldIssue = { field: string; issue: string };

/** The envelope as a caller sees it: a value, never an exception. */
export type ApiFailure = {
  ok: false;
  code: string;
  message: string;
  details: FieldIssue[];
  /** The HTTP status, so a caller can recognise the states it handles specially (`401`, `429`). */
  status: number;
};

export const GENERIC_FAILURE = "Something went wrong. Please try again.";

export function asFailure(error: unknown, response: Response): ApiFailure {
  const envelope = (error as { error?: unknown } | undefined)?.error;
  const body =
    typeof envelope === "object" && envelope !== null ? (envelope as Record<string, unknown>) : {};

  return {
    ok: false,
    code: typeof body.code === "string" ? body.code : "ERROR",
    message: typeof body.message === "string" ? body.message : GENERIC_FAILURE,
    details: Array.isArray(body.details) ? (body.details as FieldIssue[]) : [],
    status: response.status,
  };
}

/** The prefixes Ninja puts in front of a pydantic error location. */
const SOURCE_PREFIXES = ["body.", "query.", "path.", "header.", "cookie."];

/** `body.email` and `email` both mean the field called `email`. */
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

/**
 * What to show when the request itself failed.
 *
 * The API's own message is used wherever there is one, because it knows more than the client does.
 * The rate limit is the exception: `Too many requests.` states the fact and not what to do about
 * it, and `UX.md` flow D asks for that state to be handled rather than merely reported.
 */
export function messageForFailure(status: number, message: string): string {
  if (status === 429) {
    return "Too many attempts. Please wait a moment and try again.";
  }
  return message;
}
