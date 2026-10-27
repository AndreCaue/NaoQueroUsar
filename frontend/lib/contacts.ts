/**
 * Application-channel builders (PUBL-06, UI-SPEC §Copywriting).
 *
 * The reveal endpoint returns the contact **raw** (Phase 3 decision): phones
 * may carry spaces, `+` and dashes, e-mails may carry stray whitespace. These
 * helpers are the single place that turns those values into a safe link, so
 * every CTA in the app produces the same href.
 *
 * Both builders only ever build a link from values that came from the reveal
 * endpoint — nothing here is used for data the board was allowed to see
 * before verification (PUBL-05).
 */

/** Pre-filled WhatsApp message — exact approved copy (UI-SPEC §Copywriting). */
export function messageFor(title: string): string {
  return `Olá! Vi a vaga "${title}" no NaoQueroUsar e quero me candidatar.`;
}

/** `wa.me` wants digits only: `+55 11 90000-0000` → `5511900000000`. */
export function digitsOnly(phone: string): string {
  return phone.replace(/\D/g, "");
}

/**
 * WhatsApp deep link, or `null` when the number has no usable length.
 *
 * The host is hard-coded (`https://wa.me/`) and the number is reduced to
 * digits, so a value from the API can never steer the link elsewhere
 * (T-04-14). A short/garbage number yields no CTA instead of a dead link.
 */
export function waHref(phone: string, title: string): string | null {
  const digits = digitsOnly(phone);
  if (digits.length < 10) {
    return null;
  }
  return `https://wa.me/${digits}?text=${encodeURIComponent(messageFor(title))}`;
}

/**
 * `mailto:` link with the job title as subject.
 *
 * Browsers treat CR/LF in a `mailto:` as header injection, so they are
 * stripped before the address is used; the subject is `encodeURIComponent`ed
 * so quotes/accents in a title cannot break the href (T-04-14).
 */
export function mailtoHref(email: string, title: string): string {
  const address = email.replace(/[\r\n]/g, "").trim();
  return `mailto:${address}?subject=${encodeURIComponent(`Candidatura: ${title}`)}`;
}
