/** @type {const} */
const themeColors = {
  // eco-base brand primary: circuit cyan
  primary:    { light: '#00D4FF', dark: '#00D4FF' },
  // eco-base brand background: deep navy / pure white
  background: { light: '#FFFFFF', dark: '#0D1B2A' },
  // eco-base surface: soft navy tint / slightly lighter navy
  surface:    { light: '#F0FAFF', dark: '#162233' },
  // foreground text
  foreground: { light: '#0D1B2A', dark: '#E8F8FF' },
  // muted / secondary text
  muted:      { light: '#4A6B7C', dark: '#7ABCCC' },
  // border
  border:     { light: '#B8E8F5', dark: '#1E3A4F' },
  // eco accent: emerald green (circuit tree leaves)
  tint:       { light: '#00FF88', dark: '#00FF88' },
  // semantic states
  success:    { light: '#00FF88', dark: '#00FF88' },
  warning:    { light: '#F59E0B', dark: '#FBBF24' },
  error:      { light: '#EF4444', dark: '#F87171' },
};

module.exports = { themeColors };
