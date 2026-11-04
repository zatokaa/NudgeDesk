"""Theme and visual styling definition for NudgeDesk with 6 curated color palettes."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class Palette:
    id: str
    name: str
    subtitle: str
    is_light: bool
    description: str
    tags: List[Tuple[str, str, str]]  # (Label, BG color, Text color)
    accent_icon: str
    
    # Core Colors
    bg_main: str
    bg_sidebar: str
    bg_card: str
    bg_card_hover: str
    bg_input: str
    border: str
    border_light: str
    
    # Accent & Interaction
    accent: str
    accent_hover: str
    accent_text: str
    accent_subtle: str
    
    # Typography
    text_primary: str
    text_secondary: str
    text_muted: str
    
    # Status
    success: str
    warning: str
    danger: str
    info: str

PALETTES: Dict[str, Palette] = {
    # -------------------------------------------------------------
    # 1. Warm Linen (Solara Light)
    # -------------------------------------------------------------
    "warm_linen": Palette(
        id="warm_linen",
        name="Warm Linen",
        subtitle="Solara Light",
        is_light=True,
        description="Dedicated redesigned Light mode. Organic cream canvas, porcelain cards, terracotta coral buttons, and deep espresso text.",
        tags=[
            ("Terracotta", "#D9534F", "#FFFFFF"),
            ("Honey Gold", "#E5A93C", "#1E1A17"),
            ("Porcelain", "#FAF6EF", "#2D231E"),
        ],
        accent_icon="🎨",
        bg_main="#F7F3EB",
        bg_sidebar="#EFE9DE",
        bg_card="#FFFFFF",
        bg_card_hover="#FDFBF7",
        bg_input="#EFE9DE",
        border="#E2DACD",
        border_light="#ECE5DA",
        accent="#D9534F",
        accent_hover="#C4433F",
        accent_text="#FFFFFF",
        accent_subtle="#FBE9E7",
        text_primary="#2D231E",
        text_secondary="#73665D",
        text_muted="#A3968C",
        success="#2E7D32",
        warning="#E5A93C",
        danger="#D9534F",
        info="#0284C7",
    ),

    # -------------------------------------------------------------
    # 2. Emerald Pure (Mint Sage Light)
    # -------------------------------------------------------------
    "emerald_pure": Palette(
        id="emerald_pure",
        name="Emerald Pure",
        subtitle="Mint Sage Light",
        is_light=True,
        description="Pristine white canvas, fresh cool sage borders, vibrant emerald green buttons, and deep forest charcoal typography.",
        tags=[
            ("Emerald Green", "#059669", "#FFFFFF"),
            ("Mint Sage", "#A7F3D0", "#064E3B"),
            ("Pure White", "#FFFFFF", "#111827"),
        ],
        accent_icon="🍃",
        bg_main="#F2FAF5",
        bg_sidebar="#E5F5EC",
        bg_card="#FFFFFF",
        bg_card_hover="#F6FCF8",
        bg_input="#E3F4EA",
        border="#C2E6D1",
        border_light="#D6EFE1",
        accent="#059669",
        accent_hover="#047857",
        accent_text="#FFFFFF",
        accent_subtle="#D1FAE5",
        text_primary="#064E3B",
        text_secondary="#336754",
        text_muted="#6B9685",
        success="#059669",
        warning="#F59E0B",
        danger="#EF4444",
        info="#0284C7",
    ),

    # -------------------------------------------------------------
    # 3. Nordic Frost (Glacier Sky Light)
    # -------------------------------------------------------------
    "nordic_frost": Palette(
        id="nordic_frost",
        name="Nordic Frost",
        subtitle="Glacier Sky Light",
        is_light=True,
        description="Pristine pearl white canvas, cool arctic borders, crisp glacier sky blue accents, and deep Scandinavian slate typography.",
        tags=[
            ("Glacier Cyan", "#06B6D4", "#FFFFFF"),
            ("Sky Blue", "#0284C7", "#FFFFFF"),
            ("Pure White", "#FFFFFF", "#0F172A"),
        ],
        accent_icon="❄️",
        bg_main="#F0F7FB",
        bg_sidebar="#E2EEF6",
        bg_card="#FFFFFF",
        bg_card_hover="#F7FBFE",
        bg_input="#E2EEF6",
        border="#C5DFEE",
        border_light="#D8ECF7",
        accent="#0284C7",
        accent_hover="#0369A1",
        accent_text="#FFFFFF",
        accent_subtle="#E0F2FE",
        text_primary="#0F172A",
        text_secondary="#475569",
        text_muted="#94A3B8",
        success="#10B981",
        warning="#F59E0B",
        danger="#EF4444",
        info="#0284C7",
    ),

    # -------------------------------------------------------------
    # 4. Zest (Amber Gold - Dark)
    # -------------------------------------------------------------
    "zest": Palette(
        id="zest",
        name="Zest",
        subtitle="Amber Gold",
        is_light=False,
        description="Deep charcoal onyx with radiant warm amber gold pills, matching the official Zest brand identity.",
        tags=[
            ("Amber Gold", "#F5C542", "#111827"),
            ("Charcoal Onyx", "#191C23", "#F5F5F5"),
        ],
        accent_icon="⚡",
        bg_main="#111318",
        bg_sidebar="#191C23",
        bg_card="#20242D",
        bg_card_hover="#282D39",
        bg_input="#161920",
        border="#2B303C",
        border_light="#363C4B",
        accent="#F5C542",
        accent_hover="#E5B533",
        accent_text="#111827",
        accent_subtle="#2D2614",
        text_primary="#F5F5F5",
        text_secondary="#9CA3AF",
        text_muted="#6B7280",
        success="#34D399",
        warning="#FBBF24",
        danger="#F87171",
        info="#60A5FA",
    ),

    # -------------------------------------------------------------
    # 5. Slate Pro (Apple iOS Blue - Dark)
    # -------------------------------------------------------------
    "slate_pro": Palette(
        id="slate_pro",
        name="Slate Pro",
        subtitle="Apple iOS Blue",
        is_light=False,
        description="Professional Deep Slate canvas with Apple iOS blue accents and indigo micro-gradients.",
        tags=[
            ("iOS Blue", "#0A84FF", "#FFFFFF"),
            ("Deep Slate", "#1E293B", "#F8FAFC"),
        ],
        accent_icon="💎",
        bg_main="#0F172A",
        bg_sidebar="#172235",
        bg_card="#1E293B",
        bg_card_hover="#26344B",
        bg_input="#131D2E",
        border="#2C3D55",
        border_light="#384C69",
        accent="#0A84FF",
        accent_hover="#0070E0",
        accent_text="#FFFFFF",
        accent_subtle="#132742",
        text_primary="#F8FAFC",
        text_secondary="#94A3B8",
        text_muted="#64748B",
        success="#34D399",
        warning="#FBBF24",
        danger="#F87171",
        info="#38BDF8",
    ),

    # -------------------------------------------------------------
    # 6. Midnight OLED (Pitch Black & Indigo - Dark)
    # -------------------------------------------------------------
    "midnight_oled": Palette(
        id="midnight_oled",
        name="Midnight OLED",
        subtitle="Pitch Black & Indigo",
        is_light=False,
        description="Ultra-high contrast pure black OLED canvas with vivid electric indigo accents. Perfect for night focus.",
        tags=[
            ("Electric Indigo", "#6366F1", "#FFFFFF"),
            ("OLED Black", "#121215", "#FFFFFF"),
        ],
        accent_icon="🌑",
        bg_main="#000000",
        bg_sidebar="#09090C",
        bg_card="#121216",
        bg_card_hover="#1B1B22",
        bg_input="#0A0A0E",
        border="#22222A",
        border_light="#2E2E38",
        accent="#6366F1",
        accent_hover="#4F46E5",
        accent_text="#FFFFFF",
        accent_subtle="#1E1E38",
        text_primary="#FFFFFF",
        text_secondary="#A1A1AA",
        text_muted="#71717A",
        success="#10B981",
        warning="#F59E0B",
        danger="#EF4444",
        info="#818CF8",
    ),
}

class Theme:
    """Active application theme manager."""
    
    current_palette_id: str = "zest"
    active: Palette = PALETTES["zest"]

    # Active dynamic color attributes
    BG_MAIN = active.bg_main
    BG_SIDEBAR = active.bg_sidebar
    BG_CARD = active.bg_card
    BG_CARD_HOVER = active.bg_card_hover
    BG_INPUT = active.bg_input

    BORDER = active.border
    BORDER_LIGHT = active.border_light

    ACCENT = active.accent
    ACCENT_HOVER = active.accent_hover
    ACCENT_TEXT = active.accent_text
    ACCENT_SUBTLE = active.accent_subtle

    TEXT_PRIMARY = active.text_primary
    TEXT_SECONDARY = active.text_secondary
    TEXT_MUTED = active.text_muted

    SUCCESS = active.success
    WARNING = active.warning
    DANGER = active.danger
    INFO = active.info

    FONT_FAMILY = "Segoe UI"

    @classmethod
    def apply_palette(cls, palette_id: str) -> Palette:
        """Applies a selected palette and updates active attributes."""
        if palette_id not in PALETTES:
            palette_id = "zest"
        
        cls.current_palette_id = palette_id
        cls.active = PALETTES[palette_id]
        p = cls.active

        cls.BG_MAIN = p.bg_main
        cls.BG_SIDEBAR = p.bg_sidebar
        cls.BG_CARD = p.bg_card
        cls.BG_CARD_HOVER = p.bg_card_hover
        cls.BG_INPUT = p.bg_input

        cls.BORDER = p.border
        cls.BORDER_LIGHT = p.border_light

        cls.ACCENT = p.accent
        cls.ACCENT_HOVER = p.accent_hover
        cls.ACCENT_TEXT = p.accent_text
        cls.ACCENT_SUBTLE = p.accent_subtle

        cls.TEXT_PRIMARY = p.text_primary
        cls.TEXT_SECONDARY = p.text_secondary
        cls.TEXT_MUTED = p.text_muted

        cls.SUCCESS = p.success
        cls.WARNING = p.warning
        cls.DANGER = p.danger
        cls.INFO = p.info

        return p

    @classmethod
    def get_font(cls, size: int = 13, weight: str = "normal"):
        return (cls.FONT_FAMILY, size, weight)
