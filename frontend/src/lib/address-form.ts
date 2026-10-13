import type { AddressCreatePayload, AddressUpdatePayload } from "@/api/account";
import { fieldMessages, type FieldIssue } from "@/lib/api-failure";

/**
 * The address book's rules, kept out of the components so they can be tested directly (`US-2.5`).
 *
 * The fields and their bounds are `AddressCreateSchema`'s, repeated here for the same reason the
 * schema repeats the model's: a value that is too long or blank should be refused with a sentence
 * beside the input, not by a `400` after a round trip — and on SQLite an over-long value is refused
 * by nothing at all, which `M1.2` found the hard way. The API stays authoritative; this only avoids
 * asking it what it would have said.
 *
 * The form's names are camelCase and the API's are snake_case, so the table below is also the
 * translation both ways. That is not decoration: the error mapper has to turn `body.postal_code`
 * back into the input the customer is looking at, and a mapping that lived in the component could
 * not be tested.
 */

export type AddressValues = {
  label: string;
  recipient: string;
  line1: string;
  line2: string;
  city: string;
  region: string;
  postalCode: string;
  country: string;
  phone: string;
  isDefault: boolean;
};

/** The text inputs. `isDefault` is a checkbox and is not part of these. */
export type AddressField = Exclude<keyof AddressValues, "isDefault">;

export type FieldMessages = Partial<Record<AddressField, string>>;

type Field = {
  name: AddressField;
  /** The name the API knows the field by (`AddressCreateSchema`). */
  api: string;
  label: string;
  /** The model's own bound — see `accounts/schemas.py`. */
  max: number;
  required: boolean;
  autoComplete: string;
  /** What to say when a required field is blank. Authored per field, because "Required" says less. */
  missing: string;
  /** Full width in the layout: an address line is longer than a postal code. */
  wide?: boolean;
};

/**
 * The order is the order a customer fills an address in, which is why the recipient and the phone
 * come before the street rather than after everything.
 */
export const FIELDS: readonly Field[] = [
  {
    name: "recipient",
    api: "recipient",
    label: "Recipient",
    max: 120,
    required: true,
    autoComplete: "name",
    missing: "Enter who the parcel is for.",
    wide: true,
  },
  {
    name: "phone",
    api: "phone",
    label: "Phone",
    max: 32,
    required: false,
    autoComplete: "tel",
    missing: "",
    wide: true,
  },
  {
    name: "line1",
    api: "line1",
    label: "Address",
    max: 120,
    required: true,
    autoComplete: "address-line1",
    missing: "Enter the street address.",
    wide: true,
  },
  {
    name: "line2",
    api: "line2",
    label: "Address line 2",
    max: 120,
    required: false,
    autoComplete: "address-line2",
    missing: "",
    wide: true,
  },
  {
    name: "city",
    api: "city",
    label: "City",
    max: 120,
    required: true,
    autoComplete: "address-level2",
    missing: "Enter the city.",
  },
  {
    name: "region",
    api: "region",
    label: "Region",
    max: 120,
    required: false,
    autoComplete: "address-level1",
    missing: "",
  },
  {
    name: "postalCode",
    api: "postal_code",
    label: "Postal code",
    max: 32,
    required: true,
    autoComplete: "postal-code",
    missing: "Enter the postal code.",
  },
  {
    name: "country",
    api: "country",
    label: "Country",
    max: 2,
    required: true,
    autoComplete: "country",
    missing: "Enter the two-letter country code.",
  },
  {
    name: "label",
    api: "label",
    label: "Label",
    max: 60,
    required: false,
    autoComplete: "off",
    missing: "",
  },
];

const BY_API_NAME = new Map(FIELDS.map((field) => [field.api, field.name] as const));

/** A country code is two letters, as `AddressCreateSchema` insists. */
const COUNTRY_LENGTH = 2;

export function emptyValues(): AddressValues {
  const values: AddressValues = {
    label: "",
    recipient: "",
    line1: "",
    line2: "",
    city: "",
    region: "",
    postalCode: "",
    country: "",
    phone: "",
    isDefault: false,
  };
  return values;
}

export function valuesFrom(address: {
  label: string;
  recipient: string;
  line1: string;
  line2: string;
  city: string;
  region: string;
  postal_code: string;
  country: string;
  phone: string;
  is_default: boolean;
}): AddressValues {
  return {
    label: address.label,
    recipient: address.recipient,
    line1: address.line1,
    line2: address.line2,
    city: address.city,
    region: address.region,
    postalCode: address.postal_code,
    country: address.country,
    phone: address.phone,
    isDefault: address.is_default,
  };
}

export function validate(values: AddressValues): FieldMessages {
  const messages: FieldMessages = {};

  for (const field of FIELDS) {
    const value = values[field.name].trim();
    if (value === "") {
      if (field.required) {
        messages[field.name] = field.missing;
      }
      continue;
    }
    if (value.length > field.max) {
      messages[field.name] = `Use at most ${field.max} characters.`;
    }
  }

  const country = values.country.trim();
  if (country !== "" && country.length !== COUNTRY_LENGTH) {
    messages.country = "Use the two-letter country code, for example GB.";
  }

  return messages;
}

/**
 * The API's field errors, named as the inputs on this form are named.
 *
 * An issue for a field this form does not show is dropped here rather than guessed at — the form
 * still shows the envelope's own message, so nothing is swallowed, it is only not pinned to an
 * input. `is_default` is the realistic case: the API reports it as a `409` with no field at all.
 */
export function fieldErrors(details: FieldIssue[]): FieldMessages {
  const reported = fieldMessages(details);
  const errors: FieldMessages = {};

  for (const [api, message] of Object.entries(reported)) {
    const field = BY_API_NAME.get(api);
    if (field !== undefined) {
      errors[field] = message;
    }
  }

  return errors;
}

/**
 * The trimmed, normalised values every payload built from this form shares — including the
 * checkout's (`M4.5`), which sends the same fields with `label` left out.
 *
 * Exported rather than private because a second copy of these rules is a second place the country
 * could stay lower-case, and `API.md` section 6 would then see one country spelled two ways.
 */
export function cleanedAddress(values: AddressValues) {
  return {
    label: values.label.trim(),
    recipient: values.recipient.trim(),
    line1: values.line1.trim(),
    line2: values.line2.trim(),
    city: values.city.trim(),
    region: values.region.trim(),
    postal_code: values.postalCode.trim(),
    // Uppercased because a country code is upper-case by convention and the API accepts either, so
    // without this the same country could be stored twice in two spellings.
    country: values.country.trim().toUpperCase(),
    phone: values.phone.trim(),
  };
}

export function toCreatePayload(values: AddressValues): AddressCreatePayload {
  return { ...cleanedAddress(values), is_default: values.isDefault };
}

/**
 * A `PATCH` that never carries `is_default`.
 *
 * Promoting an address is an action in the list rather than a checkbox here, because the API refuses
 * to let the default be cleared: a checkbox that can be unticked but never accepted would be a
 * control that lies about what it does.
 */
export function toUpdatePayload(values: AddressValues): AddressUpdatePayload {
  return cleanedAddress(values);
}

/** What a card leads with: the label if the customer gave one, otherwise who it is for. */
export function headingFor(address: { label: string; recipient: string }): string {
  return address.label !== "" ? address.label : address.recipient;
}

/**
 * The lines under that heading. The recipient is repeated when a label exists, because "Home" does
 * not say who is collecting the parcel; the phone is last because it is the least about the place.
 */
export function addressLines(address: {
  label: string;
  recipient: string;
  line1: string;
  line2: string;
  city: string;
  region: string;
  postal_code: string;
  country: string;
  phone: string;
}): string[] {
  const lines: string[] = [];

  if (address.label !== "") {
    lines.push(address.recipient);
  }
  lines.push(address.line1);
  if (address.line2 !== "") {
    lines.push(address.line2);
  }

  const locality = [address.city, address.region, address.postal_code]
    .filter((part) => part !== "")
    .join(", ");
  if (locality !== "") {
    lines.push(locality);
  }
  if (address.country !== "") {
    lines.push(address.country);
  }
  if (address.phone !== "") {
    lines.push(address.phone);
  }

  return lines;
}
