/** Formats a minor-unit integer without ever performing business arithmetic in floats. */
export function formatCents(cents: number, currency = "CNY", locale = "zh-CN"): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(cents / 100);
}
