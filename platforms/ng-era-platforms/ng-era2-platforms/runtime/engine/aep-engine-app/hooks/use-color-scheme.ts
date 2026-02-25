/**
 * @ECO-governed
 * @ECO-layer: aep-engine-app
 * @ECO-semantic: hooks-use-color-scheme
 * @ECO-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 * 
 * GL Unified Charter Activated
 */

import { useThemeContext } from "@/lib/theme-provider";

export function useColorScheme() {
  return useThemeContext().colorScheme;
}
