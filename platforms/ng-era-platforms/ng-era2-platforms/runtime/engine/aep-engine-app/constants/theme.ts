/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: constants-theme
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

/**
 * Thin re-exports so consumers don't need to know about internal theme plumbing.
 * Full implementation lives in lib/_core/theme.ts.
 */
export {
  Colors,
  Fonts,
  SchemeColors,
  ThemeColors,
  type ColorScheme,
  type ThemeColorPalette,
} from "@/lib/_core/theme";
