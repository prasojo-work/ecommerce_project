/**
 * The licence codes the catalog ships, mapped to their Creative Commons deed.
 *
 * `ADR-0012` settles for a credits page that "demonstrates licence awareness", and CC's own
 * attribution guidance asks for the licence to be *linked* to its deed wherever the medium allows.
 * Printing the code alone tells a reader which terms apply but not what they say, which is most of
 * the point of an attribution page.
 *
 * Only the four codes in the shipped set are mapped. An unrecognised code returns `null` and is
 * rendered as plain text, because a guessed deed URL would be worse than no link at all — it would
 * claim a licence the image does not have.
 */
const DEEDS: Record<string, string> = {
  "BY-2.0": "https://creativecommons.org/licenses/by/2.0/",
  "BY-SA-2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
  "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
  "PDM-1.0": "https://creativecommons.org/publicdomain/mark/1.0/",
};

export function licenceUrl(code: string): string | null {
  return DEEDS[code] ?? null;
}
