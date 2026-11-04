export interface Theme {
  name: string;
  embedColor: number;
  textColor: string;
  /** `null` → transparent PNG */
  background: string | null;
}

export const THEMES: Record<string, Theme> = {
  discord_dark: { name: "discord_dark", embedColor: 0x5865f2, textColor: "#FFFFFF", background: null },
  discord_light: { name: "discord_light", embedColor: 0x5865f2, textColor: "#060607", background: null },
  solid_dark: { name: "solid_dark", embedColor: 0x2b2d31, textColor: "#FFFFFF", background: "#2B2D31" },
  amoled: { name: "amoled", embedColor: 0x111214, textColor: "#FFFFFF", background: "#000000" },
  emerald: { name: "emerald", embedColor: 0x57f287, textColor: "#FFFFFF", background: null },
  crimson: { name: "crimson", embedColor: 0xed4245, textColor: "#FFFFFF", background: null },
  gold: { name: "gold", embedColor: 0xfee75c, textColor: "#FFFFFF", background: null },
};

export function getTheme(theme?: string | Theme): Theme {
  if (!theme) return THEMES.discord_dark;
  if (typeof theme !== "string") return theme;
  const t = THEMES[theme];
  if (!t) throw new Error(`Unknown theme "${theme}". Available: ${Object.keys(THEMES).join(", ")}`);
  return t;
}
