export function formatINR(amount: number): string {
  try {
    return amount.toLocaleString('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2 })
  } catch {
    // Fallback
    return `₹${amount.toFixed(2)}`
  }
}

