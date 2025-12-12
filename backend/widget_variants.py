"""
Polymorphic Widget System
Generates diverse visual presentations to prevent habituation
"""

import random
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class LayoutStyle(Enum):
    MINIMAL = "minimal"  # Simple icon + short text
    CARD = "card"  # Bordered card with gradient
    BANNER = "banner"  # Full-width banner
    BADGE = "badge"  # Circular badge
    AMBIENT = "ambient"  # Subtle, low-contrast


class AnimationType(Enum):
    BREATHE = "breathe"  # Slow scale pulse (mimics breathing)
    FADE = "fade"  # Opacity cycle
    SLIDE = "slide"  # Gentle slide-in
    GLOW = "glow"  # Pulsing border glow
    NONE = "none"  # Static


@dataclass
class ColorPalette:
    """Color scheme for a variant"""
    primary: str
    secondary: str
    text: str
    accent: Optional[str] = None
    
    def to_gradient(self) -> str:
        """Generate CSS gradient string"""
        return f"linear-gradient(135deg, {self.primary}, {self.secondary})"


@dataclass
class WidgetVariant:
    """Complete visual configuration for a widget"""
    variant_id: str
    habit_id: str
    layout: LayoutStyle
    colors: ColorPalette
    message: str
    emoji: str
    font_family: str
    animation: AnimationType
    message_tone: str  # "inviting", "neutral", "playful"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "variant_id": self.variant_id,
            "habit_id": self.habit_id,
            "layout": self.layout.value,
            "colors": {
                "primary": self.colors.primary,
                "secondary": self.colors.secondary,
                "text": self.colors.text,
                "accent": self.colors.accent,
                "gradient": self.colors.to_gradient()
            },
            "message": self.message,
            "emoji": self.emoji,
            "font_family": self.font_family,
            "animation": self.animation.value,
            "message_tone": self.message_tone
        }


class WidgetVariantGenerator:
    """
    Generates diverse widget variants to maintain novelty
    
    Design Principles:
    1. Non-imperative language (invitation, not command)
    2. Visual diversity (8-12 variants per habit)
    3. Perceptual distinctiveness (force visual cortex re-processing)
    """
    
    # Color palettes (optimized for readability + emotional tone)
    COLOR_PALETTES = {
        "calm_blue": ColorPalette("#4A90E2", "#7B68EE", "#FFFFFF", "#ADD8E6"),
        "warm_sunset": ColorPalette("#FF6B6B", "#FFA500", "#FFFFFF", "#FFD700"),
        "nature_green": ColorPalette("#2ECC71", "#27AE60", "#FFFFFF", "#98D8C8"),
        "deep_purple": ColorPalette("#9B59B6", "#8E44AD", "#FFFFFF", "#DDA0DD"),
        "ocean_teal": ColorPalette("#16A085", "#1ABC9C", "#FFFFFF", "#7FDBDA"),
        "sunrise_pink": ColorPalette("#FF69B4", "#FFB6C1", "#FFFFFF", "#FFC0CB"),
        "earth_brown": ColorPalette("#8B4513", "#D2691E", "#FFFFFF", "#DEB887"),
        "midnight_blue": ColorPalette("#191970", "#4169E1", "#FFFFFF", "#87CEEB"),
        "forest_green": ColorPalette("#228B22", "#32CD32", "#FFFFFF", "#90EE90"),
        "lavender": ColorPalette("#E6E6FA", "#D8BFD8", "#4B0082", "#DDA0DD")
    }
    
    # Font families (web-safe + system fonts)
    FONTS = [
        "SF Pro Rounded",  # iOS
        "Segoe UI",  # Windows
        "Roboto",  # Android
        "Helvetica Neue",
        "Georgia",
        "Inter",
        "Poppins",
        "Lato"
    ]
    
    # Message templates by habit category
    MESSAGE_TEMPLATES = {
        "meditation": [
            "Still point available",
            "Anchor moment ready",
            "Breath space open",
            "Pause window active",
            "Clarity opportunity",
            "Silence calling",
            "Center awaits",
            "Stillness portal",
            "Present moment ready"
        ],
        "hydration": [
            "Thirst check-in",
            "H₂O moment",
            "Refresh available",
            "Hydration window",
            "Body asking",
            "Water pause",
            "Fluid time",
            "Drink space"
        ],
        "exercise": [
            "Movement portal open",
            "Energy ready",
            "Body wants motion",
            "Strength window",
            "Flow time available",
            "Active moment",
            "Power hour ready",
            "Motion calling"
        ],
        "reading": [
            "Story waiting",
            "Page time",
            "Words ready",
            "Chapter calling",
            "Book space open",
            "Reading moment",
            "Narrative ready",
            "Literary pause"
        ],
        "posture": [
            "Alignment check",
            "Spine moment",
            "Posture portal",
            "Body scan ready",
            "Reset available",
            "Ergonomic pause",
            "Alignment time",
            "Center check"
        ],
        "gratitude": [
            "Thankful moment",
            "Appreciation pause",
            "Gratitude space",
            "Blessing count",
            "Joy inventory",
            "Positive scan",
            "Grace moment",
            "Abundance check"
        ]
    }
    
    # Emoji sets by habit
    EMOJI_SETS = {
        "meditation": ["🧘", "🌊", "🍃", "☮️", "🕊️", "🌙", "✨", "🌸"],
        "hydration": ["💧", "🚰", "🌊", "💦", "🥤", "🫗", "🏔️", "🌈"],
        "exercise": ["💪", "🏃", "🚴", "🏋️", "⚡", "🔥", "🎯", "🌟"],
        "reading": ["📖", "📚", "📝", "📜", "🔖", "📰", "📑", "✍️"],
        "posture": ["🪑", "🧍", "🦴", "⚖️", "🎯", "🔄", "📐", "🧘"],
        "gratitude": ["🙏", "❤️", "🌟", "✨", "🌈", "🌻", "☀️", "💝"]
    }
    
    def __init__(self, habit_id: str, habit_category: str):
        self.habit_id = habit_id
        self.habit_category = habit_category
        self.generated_variants: List[WidgetVariant] = []
    
    def generate_variant_pool(self, count: int = 10) -> List[WidgetVariant]:
        """
        Generate a pool of diverse variants for a habit
        
        Strategy:
        - Distribute across all layout types
        - Rotate through color palettes
        - Mix animation styles
        - Ensure message diversity
        """
        variants = []
        
        layouts = list(LayoutStyle)
        palettes = list(self.COLOR_PALETTES.values())
        animations = list(AnimationType)
        messages = self.MESSAGE_TEMPLATES.get(
            self.habit_category,
            self.MESSAGE_TEMPLATES["meditation"]  # Fallback
        )
        emojis = self.EMOJI_SETS.get(
            self.habit_category,
            self.EMOJI_SETS["meditation"]
        )
        
        for i in range(count):
            variant = WidgetVariant(
                variant_id=f"{self.habit_id}_variant_{i+1}",
                habit_id=self.habit_id,
                layout=layouts[i % len(layouts)],
                colors=palettes[i % len(palettes)],
                message=messages[i % len(messages)],
                emoji=emojis[i % len(emojis)],
                font_family=self.FONTS[i % len(self.FONTS)],
                animation=animations[i % len(animations)],
                message_tone=["inviting", "neutral", "playful"][i % 3]
            )
            variants.append(variant)
        
        self.generated_variants = variants
        return variants
    
    def select_random_variant(self, exclude_recent: Optional[List[str]] = None) -> WidgetVariant:
        """
        Select a variant, avoiding recently used ones
        
        Args:
            exclude_recent: List of variant IDs used in last N triggers
        """
        if not self.generated_variants:
            self.generate_variant_pool()
        
        available = self.generated_variants
        
        if exclude_recent:
            available = [
                v for v in self.generated_variants
                if v.variant_id not in exclude_recent
            ]
        
        if not available:
            available = self.generated_variants
        
        return random.choice(available)
    
    def get_contextual_variant(self, context: Dict) -> WidgetVariant:
        """
        Select variant based on context (time, location, mood)
        
        Context-aware selection rules:
        - Morning: Brighter colors, energetic animations
        - Evening: Calmer colors, subtle animations
        - Focus mode: Minimal layout, no animation
        - High stress: Calming colors and messages
        """
        if not self.generated_variants:
            self.generate_variant_pool()
        
        # Filter based on context
        candidates = self.generated_variants
        
        # Time-based filtering
        hour = context.get("hour", 12)
        if hour < 10:  # Morning
            candidates = [v for v in candidates if v.layout != LayoutStyle.AMBIENT]
        elif hour >= 20:  # Evening
            candidates = [v for v in candidates if v.animation in [AnimationType.FADE, AnimationType.BREATHE, AnimationType.NONE]]
        
        # Focus mode filtering
        if context.get("focus_mode"):
            candidates = [
                v for v in candidates
                if v.layout == LayoutStyle.MINIMAL and v.animation == AnimationType.NONE
            ]
        
        # Stress level filtering (if available)
        if context.get("stress_level") == "high":
            calming_palettes = ["calm_blue", "ocean_teal", "nature_green"]
            candidates = [
                v for v in candidates
                if any(v.colors.primary == self.COLOR_PALETTES[p].primary for p in calming_palettes)
            ]
        
        return random.choice(candidates) if candidates else self.generated_variants[0]


class AdaptiveMessageGenerator:
    """
    Generates contextually-appropriate messages that avoid imperative tone
    
    Linguistic Principles:
    1. Opportunity framing ("available", "ready", "open")
    2. No commands ("do this", "you should")
    3. Time-bounded ("window", "moment", "space")
    4. Subject-less (removes pressure)
    """
    
    @staticmethod
    def enhance_with_context(base_message: str, context: Dict) -> str:
        """Add contextual enhancements to message"""
        enhanced = base_message
        
        # Weather context
        if context.get("weather") == "sunny":
            enhanced += " ☀️"
        elif context.get("weather") == "rainy":
            enhanced += " 🌧️"
        
        # Time context
        hour = context.get("hour", 12)
        if 5 <= hour < 12:
            enhanced += " 🌅"
        elif 12 <= hour < 17:
            enhanced += ""  # Neutral
        elif 17 <= hour < 21:
            enhanced += " 🌆"
        else:
            enhanced += " 🌙"
        
        # Streak context (if user has multi-day streak)
        if context.get("streak_days", 0) >= 3:
            enhanced += " 🔥"
        
        return enhanced
    
    @staticmethod
    def get_completion_celebration(habit_category: str, streak: int) -> str:
        """Generate celebration message after habit completion"""
        celebrations = [
            "🎉 Complete",
            "✨ Done",
            "🌟 Finished",
            "💪 Achieved",
            "🎯 Success"
        ]
        
        message = random.choice(celebrations)
        
        if streak >= 7:
            message += f" • {streak} day streak!"
        elif streak >= 3:
            message += f" • {streak} days"
        
        return message


# Example usage and testing
if __name__ == "__main__":
    print("🎨 Polymorphic Widget System Demo\n")
    
    # Generate variants for meditation habit
    generator = WidgetVariantGenerator(
        habit_id="meditation_001",
        habit_category="meditation"
    )
    
    variants = generator.generate_variant_pool(count=10)
    
    print(f"Generated {len(variants)} variants for meditation habit:\n")
    
    for i, variant in enumerate(variants[:5], 1):  # Show first 5
        print(f"{i}. Variant ID: {variant.variant_id}")
        print(f"   Layout: {variant.layout.value}")
        print(f"   Message: {variant.emoji} {variant.message}")
        print(f"   Colors: {variant.colors.primary} → {variant.colors.secondary}")
        print(f"   Font: {variant.font_family}")
        print(f"   Animation: {variant.animation.value}")
        print()
    
    # Test contextual selection
    print("🕐 Contextual Variant Selection:\n")
    
    contexts = [
        {"hour": 8, "focus_mode": False, "weather": "sunny"},
        {"hour": 22, "focus_mode": True, "weather": "clear"},
        {"hour": 14, "focus_mode": False, "stress_level": "high"}
    ]
    
    for ctx in contexts:
        variant = generator.get_contextual_variant(ctx)
        print(f"Context: {ctx}")
        print(f"Selected: {variant.emoji} {variant.message}")
        print(f"Layout: {variant.layout.value}, Animation: {variant.animation.value}\n")
    
    # Test message enhancement
    message_gen = AdaptiveMessageGenerator()
    
    base_message = "Breath space open"
    context = {"hour": 8, "weather": "sunny", "streak_days": 5}
    enhanced = message_gen.enhance_with_context(base_message, context)
    
    print(f"📝 Message Enhancement:")
    print(f"Base: {base_message}")
    print(f"Enhanced: {enhanced}")
    
    # Export variant pool as JSON
    import json
    
    variant_pool = {
        "habit_id": generator.habit_id,
        "category": generator.habit_category,
        "variants": [v.to_dict() for v in variants]
    }
    
    with open('variant_pool.json', 'w') as f:
        json.dump(variant_pool, f, indent=2)
    
    print("\n💾 Variant pool exported to variant_pool.json")
