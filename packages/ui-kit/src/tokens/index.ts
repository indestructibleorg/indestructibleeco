export const tokens = {
  colors: {
    primary: "var(--color-primary, #00F5D4)",
    accent: "var(--color-accent, #4361EE)",
    destructive: "var(--color-danger, #F72585)",
    success: "var(--color-success, #06D6A0)",
    warning: "var(--color-warning, #FFB703)",
    bg: "var(--color-bg, #06060F)",
    surface: "var(--color-surface, #0D0D1A)",
    text: "var(--color-text, #E0E0E0)",
    muted: "var(--color-muted, #6B7A99)",
  },
  radius: { sm: "4px", md: "8px", lg: "12px", full: "9999px" },
  font: { sans: "Arial, sans-serif", mono: "'Courier New', monospace" },
} as const;
