"""
BrandForge — AI Brand Kit Generator
=====================================
A Python prototype that uses Claude AI to generate complete brand identity kits
including taglines, elevator pitches, product descriptions, social media bios,
and brand voice guidelines.

Author: [Your Name]
Course: [Your Course]
Date:   March 2026

Architecture:
    ┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
    │  User Input  │ ──> │  BrandForge  │ ──> │  Claude AI API  │
    │  (CLI Form)  │     │   Engine     │     │  (Generation)   │
    └─────────────┘     └──────┬───────┘     └────────┬────────┘
                               │                      │
                               v                      v
                        ┌──────────────┐     ┌─────────────────┐
                        │   Exporter   │     │  JSON Response   │
                        │ (MD/JSON/TXT)│     │  (Parsed Kit)    │
                        └──────────────┘     └─────────────────┘

Usage:
    python brandforge.py                    # Interactive mode
    python brandforge.py --demo             # Run with sample data
    python brandforge.py --export md        # Export to Markdown
    python brandforge.py --export json      # Export to JSON
"""

import anthropic
import json
import sys
import os
import textwrap
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict

# ─────────────────────────────────────────────────────────────
# Rich library for beautiful terminal output (graceful fallback)
# ─────────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.columns import Columns
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich.markdown import Markdown
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None


# ═════════════════════════════════════════════════════════════
# DATA MODELS
# ═════════════════════════════════════════════════════════════

@dataclass
class BrandInput:
    """Represents the user's brand information input."""
    name: str
    industry: str = "Not specified"
    audience: str = "General audience"
    differentiator: str = "Not specified"
    description: str = "Not provided"
    tones: list = field(default_factory=lambda: ["Professional", "Modern"])

    def summary(self) -> str:
        return (
            f"Brand: {self.name}\n"
            f"Industry: {self.industry}\n"
            f"Target Audience: {self.audience}\n"
            f"Key Differentiator: {self.differentiator}\n"
            f"Description: {self.description}\n"
            f"Desired Tone: {', '.join(self.tones)}"
        )


@dataclass
class BrandVoiceTrait:
    """A single brand voice personality trait."""
    word: str
    description: str


@dataclass
class BrandVoice:
    """Complete brand voice guide."""
    traits: list  # List of BrandVoiceTrait
    do_guidelines: list  # List of strings
    dont_guidelines: list  # List of strings


@dataclass
class BrandKit:
    """The complete generated brand kit."""
    brand_name: str
    taglines: list  # List of strings
    elevator_pitch: str
    descriptions: dict  # {short, medium, long}
    social_bios: dict  # {twitter, linkedin, instagram}
    brand_voice: BrandVoice
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to a serializable dictionary."""
        return {
            "brand_name": self.brand_name,
            "taglines": self.taglines,
            "elevator_pitch": self.elevator_pitch,
            "descriptions": self.descriptions,
            "social_bios": self.social_bios,
            "brand_voice": {
                "traits": [{"word": t.word, "description": t.description} for t in self.brand_voice.traits],
                "do": self.brand_voice.do_guidelines,
                "dont": self.brand_voice.dont_guidelines,
            },
            "generated_at": self.generated_at,
        }


# ═════════════════════════════════════════════════════════════
# PROMPT ENGINEERING
# ═════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a world-class brand strategist and copywriter with 20 years of 
experience at top agencies. You create compelling, memorable brand identities that resonate 
with target audiences. Your copy is sharp, creative, and strategically sound.

IMPORTANT: Respond with ONLY valid JSON. No markdown, no backticks, no preamble, no explanation."""

def build_generation_prompt(brand: BrandInput) -> str:
    """
    Constructs the prompt for Claude to generate a brand kit.
    
    Prompt engineering techniques used:
    - Role assignment (brand strategist persona in system prompt)
    - Structured input with clear labels
    - Explicit output schema with JSON structure
    - Constraints on format and length
    - Few-shot style guidance through tone parameters
    """
    return f"""Generate a complete brand kit for the following brand:

{brand.summary()}

Return this EXACT JSON structure (no other text):
{{
  "taglines": ["tagline1", "tagline2", "tagline3", "tagline4", "tagline5"],
  "elevator_pitch": "A compelling 2-3 sentence elevator pitch",
  "descriptions": {{
    "short": "One-line description (under 15 words)",
    "medium": "2-3 sentence description suitable for a website hero section",
    "long": "Full paragraph (4-5 sentences) for an about page"
  }},
  "social_bios": {{
    "twitter": "Twitter/X bio (under 160 characters)",
    "linkedin": "LinkedIn company summary (2-3 professional sentences)",
    "instagram": "Instagram bio with relevant emojis and line breaks"
  }},
  "brand_voice": {{
    "traits": [
      {{"word": "Trait1", "description": "What this means for the brand's communication"}},
      {{"word": "Trait2", "description": "Brief explanation"}},
      {{"word": "Trait3", "description": "Brief explanation"}},
      {{"word": "Trait4", "description": "Brief explanation"}},
      {{"word": "Trait5", "description": "Brief explanation"}},
      {{"word": "Trait6", "description": "Brief explanation"}}
    ],
    "do": ["Writing guideline to follow 1", "Guideline 2", "Guideline 3"],
    "dont": ["Thing to avoid in writing 1", "Avoid 2", "Avoid 3"]
  }}
}}

Requirements:
- Taglines should be memorable, concise, and varied in style
- Descriptions should match the specified tone: {', '.join(brand.tones)}
- Social bios should be platform-appropriate
- Brand voice traits should be actionable for a content team"""


# ═════════════════════════════════════════════════════════════
# AI ENGINE — Core generation logic
# ═════════════════════════════════════════════════════════════

class BrandForgeEngine:
    """
    Core AI engine that communicates with the Claude API
    to generate brand kits.
    
    Attributes:
        client: Anthropic API client
        model:  The Claude model to use
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic()
        self.model = model

    def generate(self, brand: BrandInput, offline: bool = False) -> BrandKit:
        """
        Generate a complete brand kit from brand input.
        
        Args:
            brand:   BrandInput with the user's brand details
            offline: If True, use sample data instead of calling the API
            
        Returns:
            BrandKit: The fully generated brand identity kit
            
        Raises:
            ValueError: If the API response cannot be parsed
            anthropic.APIError: If the API call fails
        """
        if offline:
            return self._generate_sample(brand)

        if console:
            console.print("\n[dim]Calling Claude AI...[/dim]", end="")

        # ── API Call ──
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": build_generation_prompt(brand)}
            ]
        )

        # ── Parse Response ──
        raw_text = "".join(
            block.text for block in message.content if block.type == "text"
        )

        # Clean potential markdown fences
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse AI response as JSON: {e}\n"
                f"Raw response (first 500 chars): {raw_text[:500]}"
            )

        # ── Build BrandKit ──
        voice = BrandVoice(
            traits=[BrandVoiceTrait(**t) for t in data["brand_voice"]["traits"]],
            do_guidelines=data["brand_voice"]["do"],
            dont_guidelines=data["brand_voice"]["dont"],
        )

        kit = BrandKit(
            brand_name=brand.name,
            taglines=data["taglines"],
            elevator_pitch=data["elevator_pitch"],
            descriptions=data["descriptions"],
            social_bios=data["social_bios"],
            brand_voice=voice,
        )

        if console:
            console.print(" [green]Done![/green]\n")

        # ── Log token usage ──
        usage = message.usage
        if console:
            console.print(
                f"[dim]  Tokens used: {usage.input_tokens} input + "
                f"{usage.output_tokens} output = {usage.input_tokens + usage.output_tokens} total[/dim]\n"
            )

        return kit

    def _generate_sample(self, brand: BrandInput) -> BrandKit:
        """
        Generate a sample brand kit using pre-built templates.
        Used for demos/testing when no API key is available.
        """
        import time
        if console:
            console.print("\n[yellow]⚠ No API key found — using offline sample generation[/yellow]")
            console.print("[dim]Set ANTHROPIC_API_KEY to enable live AI generation[/dim]\n")
            console.print("[dim]Generating sample kit...[/dim]", end="")
            time.sleep(1)
            console.print(" [green]Done![/green]\n")
        else:
            print("\n⚠ Offline mode — using sample generation\n")

        name = brand.name
        tone_word = brand.tones[0] if brand.tones else "Modern"

        voice = BrandVoice(
            traits=[
                BrandVoiceTrait("Confident", f"Speak with authority about {brand.industry}"),
                BrandVoiceTrait(tone_word, f"Reflect the {tone_word.lower()} tone in every touchpoint"),
                BrandVoiceTrait("Clear", "No jargon — make complex ideas accessible"),
                BrandVoiceTrait("Human", "Talk like a knowledgeable friend, not a corporation"),
                BrandVoiceTrait("Ambitious", f"Inspire {brand.audience} to think bigger"),
                BrandVoiceTrait("Precise", "Every word earns its place — cut the fluff"),
            ],
            do_guidelines=[
                f"Use active voice and direct language",
                f"Lead with benefits for {brand.audience}",
                f"Keep sentences under 20 words when possible",
            ],
            dont_guidelines=[
                "Use buzzwords like 'synergy' or 'leverage'",
                "Write paragraphs longer than 3 sentences",
                "Make promises the product can't keep",
            ],
        )

        return BrandKit(
            brand_name=name,
            taglines=[
                f"{name} — Where {tone_word.lower()} meets innovation",
                f"The future of {brand.industry.lower()} starts here",
                f"{name}: Built for builders",
                f"Less noise. More {name}.",
                f"Your {brand.industry.lower()} journey, reimagined",
            ],
            elevator_pitch=(
                f"{name} is a {tone_word.lower()} platform built for {brand.audience.lower()}. "
                f"By leveraging {brand.differentiator.lower()}, we help our users achieve more "
                f"with less friction — turning complexity into clarity."
            ),
            descriptions={
                "short": f"{name} — {tone_word} {brand.industry.lower()} for {brand.audience.lower()}.",
                "medium": (
                    f"{name} is the {tone_word.lower()} {brand.industry.lower()} platform that "
                    f"{brand.audience.lower()} trust. {brand.description}"
                ),
                "long": (
                    f"{name} was founded on a simple belief: {brand.industry.lower()} should work "
                    f"for everyone. We built a platform around {brand.differentiator.lower()} to "
                    f"serve {brand.audience.lower()} who demand more. {brand.description} "
                    f"Today, thousands of users rely on {name} to transform the way they work."
                ),
            },
            social_bios={
                "twitter": f"{name} — {brand.differentiator}. Built for {brand.audience.lower()}. 🚀",
                "linkedin": (
                    f"{name} is a {brand.industry.lower()} company on a mission to empower "
                    f"{brand.audience.lower()}. {brand.description}"
                ),
                "instagram": f"✦ {name}\n💡 {brand.differentiator}\n🎯 For {brand.audience.lower()}\n🔗 Link in bio",
            },
            brand_voice=voice,
        )


# ═════════════════════════════════════════════════════════════
# DISPLAY — Rich terminal rendering
# ═════════════════════════════════════════════════════════════

class BrandKitDisplay:
    """Renders the generated brand kit in the terminal using Rich."""

    @staticmethod
    def show(kit: BrandKit):
        """Display the full brand kit with beautiful formatting."""
        if not RICH_AVAILABLE:
            BrandKitDisplay._show_plain(kit)
            return

        console.print()
        console.rule(f"[bold]✦ Brand Kit for [yellow]{kit.brand_name}[/yellow] ✦[/bold]")
        console.print()

        # ── 1. Taglines ──
        tagline_text = Text()
        for i, tagline in enumerate(kit.taglines, 1):
            tagline_text.append(f"  {i}. ", style="dim")
            tagline_text.append(f"{tagline}\n", style="bold")

        console.print(Panel(
            tagline_text,
            title="[yellow]⚡ Taglines[/yellow]",
            border_style="yellow",
            padding=(1, 2),
        ))

        # ── 2. Elevator Pitch ──
        console.print(Panel(
            f"[white]{kit.elevator_pitch}[/white]",
            title="[blue]💬 Elevator Pitch[/blue]",
            border_style="blue",
            padding=(1, 2),
        ))

        # ── 3. Product Descriptions ──
        desc_table = Table(box=box.SIMPLE_HEAVY, show_header=True, padding=(0, 2))
        desc_table.add_column("Length", style="bold green", width=12)
        desc_table.add_column("Description", style="white")

        for label, key in [("One-liner", "short"), ("Website", "medium"), ("About Page", "long")]:
            desc_table.add_row(label, kit.descriptions[key])

        console.print(Panel(
            desc_table,
            title="[green]📄 Product Descriptions[/green]",
            border_style="green",
            padding=(1, 1),
        ))

        # ── 4. Social Media Bios ──
        social_table = Table(box=box.SIMPLE_HEAVY, show_header=True, padding=(0, 2))
        social_table.add_column("Platform", style="bold magenta", width=12)
        social_table.add_column("Bio", style="white")

        for platform, key in [("Twitter/X", "twitter"), ("LinkedIn", "linkedin"), ("Instagram", "instagram")]:
            social_table.add_row(platform, kit.social_bios[key])

        console.print(Panel(
            social_table,
            title="[magenta]📱 Social Media Bios[/magenta]",
            border_style="magenta",
            padding=(1, 1),
        ))

        # ── 5. Brand Voice Guide ──
        # Traits grid
        trait_panels = []
        for trait in kit.brand_voice.traits:
            trait_panels.append(Panel(
                f"[dim]{trait.description}[/dim]",
                title=f"[bold yellow]{trait.word}[/bold yellow]",
                border_style="dim",
                width=36,
                padding=(0, 1),
            ))

        voice_content = Columns(trait_panels, equal=True, expand=True)

        console.print(Panel(
            voice_content,
            title="[yellow]🎙 Brand Voice — Personality Traits[/yellow]",
            border_style="yellow",
            padding=(1, 2),
        ))

        # Do / Don't
        guidelines = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
        guidelines.add_column("✓ Do", style="green", ratio=1)
        guidelines.add_column("✕ Don't", style="red", ratio=1)

        max_rows = max(len(kit.brand_voice.do_guidelines), len(kit.brand_voice.dont_guidelines))
        for i in range(max_rows):
            do_text = kit.brand_voice.do_guidelines[i] if i < len(kit.brand_voice.do_guidelines) else ""
            dont_text = kit.brand_voice.dont_guidelines[i] if i < len(kit.brand_voice.dont_guidelines) else ""
            guidelines.add_row(do_text, dont_text)

        console.print(Panel(
            guidelines,
            title="[cyan]📝 Writing Guidelines[/cyan]",
            border_style="cyan",
            padding=(1, 1),
        ))

        console.print()
        console.print(f"[dim]Generated at {kit.generated_at}[/dim]", justify="center")
        console.print()

    @staticmethod
    def _show_plain(kit: BrandKit):
        """Fallback display without Rich library."""
        print(f"\n{'='*60}")
        print(f"  BRAND KIT: {kit.brand_name}")
        print(f"{'='*60}\n")

        print("TAGLINES:")
        for i, t in enumerate(kit.taglines, 1):
            print(f"  {i}. {t}")

        print(f"\nELEVATOR PITCH:\n  {kit.elevator_pitch}")

        print("\nDESCRIPTIONS:")
        for label, key in [("Short", "short"), ("Medium", "medium"), ("Long", "long")]:
            print(f"  [{label}] {kit.descriptions[key]}")

        print("\nSOCIAL BIOS:")
        for platform, key in [("Twitter", "twitter"), ("LinkedIn", "linkedin"), ("Instagram", "instagram")]:
            print(f"  [{platform}] {kit.social_bios[key]}")

        print("\nBRAND VOICE TRAITS:")
        for t in kit.brand_voice.traits:
            print(f"  • {t.word}: {t.description}")

        print("\nDO:")
        for g in kit.brand_voice.do_guidelines:
            print(f"  ✓ {g}")
        print("DON'T:")
        for g in kit.brand_voice.dont_guidelines:
            print(f"  ✕ {g}")
        print()


# ═════════════════════════════════════════════════════════════
# EXPORTERS — Save results in different formats
# ═════════════════════════════════════════════════════════════

class BrandKitExporter:
    """Export brand kits to various file formats."""

    @staticmethod
    def to_json(kit: BrandKit, filepath: str) -> str:
        """Export brand kit to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(kit.to_dict(), f, indent=2)
        return filepath

    @staticmethod
    def to_markdown(kit: BrandKit, filepath: str) -> str:
        """Export brand kit to a Markdown document."""
        md = f"""# Brand Kit — {kit.brand_name}

*Generated on {kit.generated_at[:10]} by BrandForge AI*

---

## Taglines

{chr(10).join(f'{i}. **{t}**' for i, t in enumerate(kit.taglines, 1))}

---

## Elevator Pitch

{kit.elevator_pitch}

---

## Product Descriptions

### One-Liner
{kit.descriptions['short']}

### Website Hero
{kit.descriptions['medium']}

### About Page
{kit.descriptions['long']}

---

## Social Media Bios

### Twitter / X
{kit.social_bios['twitter']}

### LinkedIn
{kit.social_bios['linkedin']}

### Instagram
{kit.social_bios['instagram']}

---

## Brand Voice Guide

### Personality Traits

| Trait | Description |
|-------|-------------|
{chr(10).join(f'| **{t.word}** | {t.description} |' for t in kit.brand_voice.traits)}

### Writing Guidelines

**Do:**
{chr(10).join(f'- {g}' for g in kit.brand_voice.do_guidelines)}

**Don't:**
{chr(10).join(f'- {g}' for g in kit.brand_voice.dont_guidelines)}

---

*Generated by BrandForge — AI Brand Kit Generator*
"""
        with open(filepath, 'w') as f:
            f.write(md)
        return filepath

    @staticmethod
    def to_text(kit: BrandKit, filepath: str) -> str:
        """Export brand kit to a plain text file."""
        lines = [
            f"BRAND KIT: {kit.brand_name}",
            f"Generated: {kit.generated_at[:10]}",
            "=" * 50, "",
            "TAGLINES:",
            *[f"  {i}. {t}" for i, t in enumerate(kit.taglines, 1)],
            "", "ELEVATOR PITCH:",
            f"  {kit.elevator_pitch}",
            "", "DESCRIPTIONS:",
            f"  [One-liner] {kit.descriptions['short']}",
            f"  [Website]   {kit.descriptions['medium']}",
            f"  [About]     {kit.descriptions['long']}",
            "", "SOCIAL MEDIA BIOS:",
            f"  [Twitter]   {kit.social_bios['twitter']}",
            f"  [LinkedIn]  {kit.social_bios['linkedin']}",
            f"  [Instagram] {kit.social_bios['instagram']}",
            "", "BRAND VOICE TRAITS:",
            *[f"  • {t.word}: {t.description}" for t in kit.brand_voice.traits],
            "", "DO:",
            *[f"  ✓ {g}" for g in kit.brand_voice.do_guidelines],
            "DON'T:",
            *[f"  ✕ {g}" for g in kit.brand_voice.dont_guidelines],
        ]
        with open(filepath, 'w') as f:
            f.write("\n".join(lines))
        return filepath


# ═════════════════════════════════════════════════════════════
# CLI — Interactive input collection
# ═════════════════════════════════════════════════════════════

AVAILABLE_TONES = [
    "Professional", "Friendly", "Bold", "Luxurious",
    "Playful", "Minimalist", "Empowering", "Trustworthy",
    "Witty", "Warm", "Edgy", "Sophisticated",
]

INDUSTRIES = [
    "Technology / SaaS", "E-commerce / Retail", "Health & Wellness",
    "Finance / Fintech", "Education", "Food & Beverage",
    "Fashion & Beauty", "Travel & Hospitality", "Creative Agency",
    "Real Estate", "Other",
]


def collect_input_rich() -> BrandInput:
    """Collect brand input interactively using Rich prompts."""
    console.print()
    console.print(Panel(
        "[bold]Welcome to [yellow]BrandForge[/yellow][/bold]\n"
        "[dim]AI-powered brand identity generation[/dim]",
        border_style="yellow",
        padding=(1, 4),
    ))
    console.print()

    # Brand name (required)
    name = Prompt.ask("[bold]Brand name[/bold]")
    while not name.strip():
        console.print("[red]Brand name is required![/red]")
        name = Prompt.ask("[bold]Brand name[/bold]")

    # Industry
    console.print("\n[bold]Industry:[/bold]")
    for i, ind in enumerate(INDUSTRIES, 1):
        console.print(f"  [dim]{i:2d}.[/dim] {ind}")
    ind_choice = Prompt.ask("\n[dim]Enter number or type custom[/dim]", default="1")
    try:
        industry = INDUSTRIES[int(ind_choice) - 1]
    except (ValueError, IndexError):
        industry = ind_choice

    # Audience
    audience = Prompt.ask("\n[bold]Target audience[/bold]", default="General audience")

    # Differentiator
    differentiator = Prompt.ask("[bold]Key differentiator[/bold]", default="Not specified")

    # Description
    description = Prompt.ask("[bold]Brand description[/bold] [dim](brief)[/dim]", default="Not provided")

    # Tones (multi-select)
    console.print("\n[bold]Select brand tones[/bold] [dim](comma-separated numbers)[/dim]:")
    for i, tone in enumerate(AVAILABLE_TONES, 1):
        console.print(f"  [dim]{i:2d}.[/dim] {tone}")

    tone_input = Prompt.ask("\n[dim]Enter numbers[/dim]", default="1,2")
    selected_tones = []
    for t in tone_input.split(","):
        t = t.strip()
        try:
            idx = int(t) - 1
            if 0 <= idx < len(AVAILABLE_TONES):
                selected_tones.append(AVAILABLE_TONES[idx])
        except ValueError:
            if t:
                selected_tones.append(t)

    if not selected_tones:
        selected_tones = ["Professional", "Modern"]

    return BrandInput(
        name=name.strip(),
        industry=industry,
        audience=audience,
        differentiator=differentiator,
        description=description,
        tones=selected_tones,
    )


def collect_input_plain() -> BrandInput:
    """Fallback input collection without Rich."""
    print("\n" + "=" * 50)
    print("  BRANDFORGE — AI Brand Kit Generator")
    print("=" * 50 + "\n")

    name = input("Brand name: ").strip()
    while not name:
        name = input("Brand name (required): ").strip()

    print("\nIndustries:")
    for i, ind in enumerate(INDUSTRIES, 1):
        print(f"  {i}. {ind}")
    ind_choice = input("Industry (number or custom) [1]: ").strip() or "1"
    try:
        industry = INDUSTRIES[int(ind_choice) - 1]
    except (ValueError, IndexError):
        industry = ind_choice

    audience = input("Target audience [General]: ").strip() or "General audience"
    differentiator = input("Key differentiator: ").strip() or "Not specified"
    description = input("Brief description: ").strip() or "Not provided"

    print("\nTones:")
    for i, tone in enumerate(AVAILABLE_TONES, 1):
        print(f"  {i}. {tone}")
    tone_input = input("Select tones (comma-separated numbers) [1,2]: ").strip() or "1,2"
    selected_tones = []
    for t in tone_input.split(","):
        try:
            selected_tones.append(AVAILABLE_TONES[int(t.strip()) - 1])
        except (ValueError, IndexError):
            pass

    return BrandInput(
        name=name, industry=industry, audience=audience,
        differentiator=differentiator, description=description,
        tones=selected_tones or ["Professional"],
    )


def get_demo_input() -> BrandInput:
    """Return pre-filled demo data for testing."""
    return BrandInput(
        name="Solaris",
        industry="Technology / SaaS",
        audience="Startup founders and small business owners",
        differentiator="AI-powered automation that learns and adapts to each business",
        description="Solaris is an intelligent business automation platform that uses AI to "
                    "streamline workflows, reduce manual tasks, and help small businesses "
                    "operate like enterprises.",
        tones=["Bold", "Empowering", "Professional"],
    )


# ═════════════════════════════════════════════════════════════
# MAIN — Entry point
# ═════════════════════════════════════════════════════════════

def main():
    """
    Main entry point for BrandForge.
    
    Supports:
        --demo          Run with pre-filled sample data
        --export md     Export results to Markdown
        --export json   Export results to JSON
        --export txt    Export results to plain text
    """
    args = sys.argv[1:]
    demo_mode = "--demo" in args
    export_format = None

    if "--export" in args:
        idx = args.index("--export")
        if idx + 1 < len(args):
            export_format = args[idx + 1].lower()

    # ── Collect input ──
    if demo_mode:
        brand = get_demo_input()
        if console:
            console.print("\n[yellow]⚡ Running in demo mode with sample data[/yellow]")
            console.print(f"[dim]{brand.summary()}[/dim]\n")
        else:
            print("\n⚡ Demo mode\n")
            print(brand.summary() + "\n")
    else:
        brand = collect_input_rich() if RICH_AVAILABLE else collect_input_plain()

    # ── Confirm ──
    if not demo_mode and RICH_AVAILABLE:
        console.print()
        console.print(Panel(brand.summary(), title="[bold]Your Brand Input[/bold]", border_style="dim"))
        if not Confirm.ask("\n[bold]Generate brand kit?[/bold]", default=True):
            console.print("[dim]Cancelled.[/dim]")
            return

    # ── Generate ──
    engine = BrandForgeEngine()
    offline = not os.environ.get("ANTHROPIC_API_KEY")

    try:
        kit = engine.generate(brand, offline=offline)
    except Exception as e:
        if console:
            console.print(f"\n[red bold]Error:[/red bold] {e}")
        else:
            print(f"\nError: {e}")
        sys.exit(1)

    # ── Display ──
    BrandKitDisplay.show(kit)

    # ── Export ──
    if export_format:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = brand.name.lower().replace(" ", "_")

        if export_format == "json":
            path = BrandKitExporter.to_json(kit, f"brandkit_{safe_name}_{timestamp}.json")
        elif export_format in ("md", "markdown"):
            path = BrandKitExporter.to_markdown(kit, f"brandkit_{safe_name}_{timestamp}.md")
        elif export_format in ("txt", "text"):
            path = BrandKitExporter.to_text(kit, f"brandkit_{safe_name}_{timestamp}.txt")
        else:
            if console:
                console.print(f"[red]Unknown export format: {export_format}[/red]")
            return

        if console:
            console.print(f"[green]✓ Exported to:[/green] {path}")
        else:
            print(f"✓ Exported to: {path}")

    # ── Offer export if not already exporting ──
    if not export_format and RICH_AVAILABLE:
        if Confirm.ask("\n[bold]Export results?[/bold]", default=False):
            fmt = Prompt.ask("Format", choices=["md", "json", "txt"], default="md")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = brand.name.lower().replace(" ", "_")

            if fmt == "json":
                path = BrandKitExporter.to_json(kit, f"brandkit_{safe_name}_{timestamp}.json")
            elif fmt == "md":
                path = BrandKitExporter.to_markdown(kit, f"brandkit_{safe_name}_{timestamp}.md")
            else:
                path = BrandKitExporter.to_text(kit, f"brandkit_{safe_name}_{timestamp}.txt")

            console.print(f"[green]✓ Exported to:[/green] {path}")


if __name__ == "__main__":
    main()
