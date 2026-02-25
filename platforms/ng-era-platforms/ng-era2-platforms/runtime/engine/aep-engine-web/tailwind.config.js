/**
 * @GL-governed
 * @GL-layer: aep-engine-web
 * @GL-semantic: aep-engine-web-tailwind.config
 * @GL-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0a7ea4',
        success: '#22C55E',
        warning: '#F59E0B',
        error: '#EF4444',
        surface: '#f5f5f5',
        'surface-dark': '#1e2022',
        foreground: '#11181C',
        'foreground-dark': '#ECEDEE',
        muted: '#687076',
        'muted-dark': '#9BA1A6',
        border: '#E5E7EB',
        'border-dark': '#334155',
      },
    },
  },
  plugins: [],
}
