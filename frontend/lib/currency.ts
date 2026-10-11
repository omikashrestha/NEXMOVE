export interface CurrencyOption {
  code: string;
  name: string;
  symbol: string;
  rateAgainstInr: number; // 1 unit of currency = X INR
  locale: string;
}

export const CURRENCY_OPTIONS: CurrencyOption[] = [
  { code: "INR", name: "Indian Rupee", symbol: "₹", rateAgainstInr: 1.0, locale: "en-IN" },
  { code: "USD", name: "US Dollar", symbol: "$", rateAgainstInr: 83.5, locale: "en-US" },
  { code: "EUR", name: "Euro", symbol: "€", rateAgainstInr: 90.5, locale: "de-DE" },
  { code: "GBP", name: "British Pound", symbol: "£", rateAgainstInr: 106.0, locale: "en-GB" },
  { code: "AED", name: "UAE Dirham", symbol: "AED", rateAgainstInr: 22.7, locale: "en-AE" },
  { code: "SGD", name: "Singapore Dollar", symbol: "S$", rateAgainstInr: 62.0, locale: "en-SG" },
  { code: "AUD", name: "Australian Dollar", symbol: "A$", rateAgainstInr: 54.5, locale: "en-AU" },
  { code: "CAD", name: "Canadian Dollar", symbol: "C$", rateAgainstInr: 61.0, locale: "en-CA" },
];

/**
 * Converts an INR amount to the specified currency and formats it.
 * Preserves the original INR value in tooltips/footnotes while providing an exact conversion.
 */
export function formatCurrency(
  amountInInr: number | undefined | null,
  currencyCode: string = "INR",
  compact: boolean = false
): string {
  if (amountInInr === undefined || amountInInr === null || isNaN(amountInInr)) {
    return "—";
  }

  const selected = CURRENCY_OPTIONS.find((c) => c.code === currencyCode) || CURRENCY_OPTIONS[0];

  // Base currency is INR
  if (selected.code === "INR") {
    if (compact && Math.abs(amountInInr) >= 100000) {
      const lakhs = (amountInInr / 100000).toFixed(1);
      return `₹${lakhs} Lakh`;
    }
    return `₹${Math.round(amountInInr).toLocaleString("en-IN")}`;
  }

  // Convert to foreign currency using indicative exchange rate
  const converted = amountInInr / selected.rateAgainstInr;
  const rounded = Math.round(converted);

  if (compact && Math.abs(rounded) >= 1000) {
    return `${selected.symbol}${(rounded / 1000).toFixed(1)}k ${selected.code}`;
  }

  return `${selected.symbol}${rounded.toLocaleString(selected.locale)} ${selected.code}`;
}

/**
 * Converts a foreign currency input back into INR for backend API calls.
 */
export function convertToInr(foreignAmount: number, currencyCode: string): number {
  const selected = CURRENCY_OPTIONS.find((c) => c.code === currencyCode) || CURRENCY_OPTIONS[0];
  return Math.round(foreignAmount * selected.rateAgainstInr);
}

/**
 * Explanatory helper note for foreign currency conversion.
 */
export function getCurrencyFootnote(currencyCode: string): string | null {
  if (currencyCode === "INR") return null;
  const selected = CURRENCY_OPTIONS.find((c) => c.code === currencyCode);
  if (!selected) return null;
  return `Amounts shown in ${selected.code} for reference (1 ${selected.code} ≈ ₹${selected.rateAgainstInr.toFixed(2)} INR). Contracts and payments in India are calculated in Indian Rupees (INR).`;
}
