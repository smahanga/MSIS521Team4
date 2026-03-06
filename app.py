"""
BrandForge — Streamlit Web UI
==============================
A beautiful web interface for the AI Brand Kit Generator.

Run with:
    streamlit run app.py

Requires:
    pip install streamlit anthropic
"""

import streamlit as st
import anthropic
import json
import time
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BrandForge — AI Brand Kit Generator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Outfit:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp { background-color: #0C0B0F; }
    section[data-testid="stSidebar"] { background-color: #15141A; border-right: 1px solid #2A2833; }
    .stApp header { background-color: transparent !important; }

    /* Typography */
    h1, h2, h3 { font-family: 'Playfair Display', Georgia, serif !important; letter-spacing: -0.02em; }
    p, li, div, span, label { font-family: 'Outfit', sans-serif !important; }

    /* Hero */
    .hero-title {
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: 42px !important;
        font-weight: 700 !important;
        text-align: center;
        line-height: 1.15;
        margin-bottom: 8px;
        color: #EDECF0;
    }
    .hero-accent { color: #E8C872 !important; font-style: italic; }
    .hero-sub {
        text-align: center; font-size: 16px; color: #9B99A6;
        max-width: 500px; margin: 0 auto 32px; line-height: 1.6;
        font-weight: 300;
    }

    /* Cards */
    .brand-card {
        background: #15141A;
        border: 1px solid #2A2833;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 16px;
        position: relative;
        overflow: hidden;
        transition: border-color 0.2s;
    }
    .brand-card:hover { border-color: #35333F; }

    .card-stripe {
        position: absolute; top: 0; left: 0; right: 0; height: 3px;
        border-radius: 14px 14px 0 0;
    }

    .card-header {
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 14px;
    }

    .card-icon {
        width: 32px; height: 32px; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 15px;
    }

    .card-title {
        font-size: 14px !important; font-weight: 600 !important;
        color: #EDECF0 !important; margin: 0 !important;
        font-family: 'Outfit', sans-serif !important;
    }

    /* Taglines */
    .tagline-item {
        padding: 10px 0;
        border-bottom: 1px solid #2A2833;
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: 17px; color: #EDECF0;
    }
    .tagline-item:last-child { border-bottom: none; }

    /* Description blocks */
    .desc-block { padding: 11px 0; border-bottom: 1px solid #2A2833; }
    .desc-block:last-child { border-bottom: none; }
    .desc-label {
        font-size: 10px; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.06em; color: #6B6878; margin-bottom: 4px;
    }
    .desc-text { font-size: 14px; line-height: 1.65; color: #9B99A6; }

    /* Voice traits */
    .trait-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .trait-card {
        background: #1C1B22; border-radius: 10px; padding: 14px; text-align: center;
    }
    .trait-word {
        font-family: 'Playfair Display', serif !important;
        font-size: 18px; font-weight: 600; color: #EDECF0; margin-bottom: 4px;
    }
    .trait-desc { font-size: 11px; color: #6B6878; line-height: 1.4; }

    /* Do/Don't */
    .guidelines-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 14px; }
    .guideline-item {
        font-size: 13px; color: #9B99A6;
        padding: 7px 0; border-bottom: 1px solid #2A2833;
    }
    .guideline-label {
        font-size: 12px; font-weight: 600; margin-bottom: 8px;
    }
    .do-label { color: #5DD9A8; }
    .dont-label { color: #F08A7E; }

    /* Sidebar styling */
    .sidebar-brand {
        display: flex; align-items: center; gap: 12px;
        margin-bottom: 24px; padding-bottom: 20px;
        border-bottom: 1px solid #2A2833;
    }
    .sidebar-logo {
        width: 38px; height: 38px; border-radius: 10px;
        background: linear-gradient(135deg, #E8C872, #D4A84A);
        display: flex; align-items: center; justify-content: center;
        font-size: 18px;
        box-shadow: 0 0 24px rgba(232,200,114,0.15);
    }
    .sidebar-title {
        font-family: 'Playfair Display', serif !important;
        font-size: 22px; font-weight: 600; color: #EDECF0;
    }
    .sidebar-title span { color: #E8C872; }

    /* Tone chips */
    .tone-selected {
        background: rgba(232,200,114,0.12) !important;
        border: 1px solid #E8C872 !important;
        color: #E8C872 !important;
    }

    /* Badge */
    .powered-badge {
        font-size: 11px; font-weight: 500; color: #E8C872;
        background: rgba(232,200,114,0.12); padding: 5px 12px;
        border-radius: 20px; border: 1px solid rgba(232,200,114,0.15);
        display: inline-block; margin-top: 12px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #E8C872, #D4A84A) !important;
        color: #0C0B0F !important;
        border: none !important;
        border-radius: 50px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 12px 36px !important;
        box-shadow: 0 4px 24px rgba(232,200,114,0.25) !important;
        font-family: 'Outfit', sans-serif !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #D4A84A, #C49A3A) !important;
        box-shadow: 0 6px 32px rgba(232,200,114,0.35) !important;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background-color: #1C1B22 !important;
        border: 1px solid #2A2833 !important;
        border-radius: 10px !important;
        color: #EDECF0 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #E8C872 !important;
        box-shadow: 0 0 0 3px rgba(232,200,114,0.12) !important;
    }

    /* Multiselect */
    .stMultiSelect > div > div { background-color: #1C1B22 !important; border-color: #2A2833 !important; border-radius: 10px !important; }
    span[data-baseweb="tag"] { background-color: rgba(232,200,114,0.15) !important; border-color: #E8C872 !important; }
    span[data-baseweb="tag"] span { color: #E8C872 !important; }

    /* Labels */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stMultiSelect label {
        color: #9B99A6 !important; font-size: 13px !important; font-weight: 500 !important;
    }

    /* Expander */
    .streamlit-expanderHeader { color: #EDECF0 !important; background: #15141A !important; }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

TONES = [
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

SYSTEM_PROMPT = """You are a world-class brand strategist and copywriter with 20 years of 
experience at top agencies. You create compelling, memorable brand identities.
IMPORTANT: Respond with ONLY valid JSON. No markdown, no backticks, no preamble."""


# ─────────────────────────────────────────────────────────────
# AI ENGINE
# ─────────────────────────────────────────────────────────────

def generate_brand_kit(name, industry, audience, differentiator, description, tones):
    """Call Claude API to generate a brand kit. Returns parsed dict or raises error."""

    tone_str = ", ".join(tones) if tones else "Professional, Modern"

    prompt = f"""Generate a complete brand kit for the following brand:

Brand: {name}
Industry: {industry or 'Not specified'}
Target Audience: {audience or 'General'}
Key Differentiator: {differentiator or 'Not specified'}
Description: {description or 'Not provided'}
Desired Tone: {tone_str}

Return this EXACT JSON structure (no other text):
{{
  "taglines": ["tagline1", "tagline2", "tagline3", "tagline4", "tagline5"],
  "elevator_pitch": "A compelling 2-3 sentence elevator pitch",
  "descriptions": {{
    "short": "One-line description (under 15 words)",
    "medium": "2-3 sentence description for a website hero section",
    "long": "Full paragraph (4-5 sentences) for an about page"
  }},
  "social_bios": {{
    "twitter": "Twitter/X bio (under 160 characters)",
    "linkedin": "LinkedIn summary (2-3 professional sentences)",
    "instagram": "Instagram bio with emojis and line breaks"
  }},
  "brand_voice": {{
    "traits": [
      {{"word": "Trait1", "description": "What this means for communication"}},
      {{"word": "Trait2", "description": "Brief explanation"}},
      {{"word": "Trait3", "description": "Brief explanation"}},
      {{"word": "Trait4", "description": "Brief explanation"}},
      {{"word": "Trait5", "description": "Brief explanation"}},
      {{"word": "Trait6", "description": "Brief explanation"}}
    ],
    "do": ["Writing guideline 1", "Guideline 2", "Guideline 3"],
    "dont": ["Thing to avoid 1", "Avoid 2", "Avoid 3"]
  }}
}}"""

    client = anthropic.Anthropic(api_key=st.session_state.get("api_key", ""))

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = "".join(b.text for b in message.content if b.type == "text")
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return json.loads(cleaned.strip())


def generate_sample_kit(name, industry, audience, differentiator, description, tones):
    """Generate a sample kit without API — for demo purposes."""
    tone = tones[0] if tones else "Professional"
    return {
        "taglines": [
            f"{name} — Where {tone.lower()} meets innovation",
            f"The future of {(industry or 'business').lower()} starts here",
            f"{name}: Built for builders",
            f"Less noise. More {name}.",
            f"Your {(industry or 'business').lower()} journey, reimagined",
        ],
        "elevator_pitch": (
            f"{name} is a {tone.lower()} platform built for {(audience or 'professionals').lower()}. "
            f"By focusing on {(differentiator or 'innovation').lower()}, we help users achieve more "
            f"with less friction — turning complexity into clarity."
        ),
        "descriptions": {
            "short": f"{name} — {tone} {(industry or 'solutions').lower()} for {(audience or 'everyone').lower()}.",
            "medium": (
                f"{name} is the {tone.lower()} platform that {(audience or 'professionals').lower()} trust. "
                f"{description or 'We make things better.'}"
            ),
            "long": (
                f"{name} was founded on a simple belief: {(industry or 'technology').lower()} should work "
                f"for everyone. We built a platform around {(differentiator or 'innovation').lower()} to "
                f"serve {(audience or 'our users').lower()} who demand more. {description or ''} "
                f"Today, thousands of users rely on {name} to transform how they work."
            ),
        },
        "social_bios": {
            "twitter": f"{name} — {differentiator or 'Innovation meets simplicity'}. Built for {(audience or 'you').lower()}. 🚀",
            "linkedin": (
                f"{name} is a {(industry or 'technology').lower()} company empowering "
                f"{(audience or 'professionals').lower()}. {description or 'We build the future.'}"
            ),
            "instagram": f"✦ {name}\n💡 {differentiator or 'Innovation'}\n🎯 For {(audience or 'you').lower()}\n🔗 Link in bio",
        },
        "brand_voice": {
            "traits": [
                {"word": "Confident", "description": f"Speak with authority about {(industry or 'your field').lower()}"},
                {"word": tone, "description": f"Reflect the {tone.lower()} tone in every touchpoint"},
                {"word": "Clear", "description": "No jargon — make complex ideas accessible"},
                {"word": "Human", "description": "Talk like a knowledgeable friend, not a corporation"},
                {"word": "Ambitious", "description": f"Inspire {(audience or 'users').lower()} to think bigger"},
                {"word": "Precise", "description": "Every word earns its place — cut the fluff"},
            ],
            "do": [
                "Use active voice and direct language",
                f"Lead with benefits for {(audience or 'users').lower()}",
                "Keep sentences under 20 words when possible",
            ],
            "dont": [
                "Use buzzwords like 'synergy' or 'leverage'",
                "Write paragraphs longer than 3 sentences",
                "Make promises the product can't keep",
            ],
        },
    }


# ─────────────────────────────────────────────────────────────
# RENDER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def render_card(title, icon, stripe_color, icon_bg, content_html):
    st.markdown(f"""
    <div class="brand-card">
        <div class="card-stripe" style="background:{stripe_color};"></div>
        <div class="card-header">
            <div class="card-icon" style="background:{icon_bg};">{icon}</div>
            <div class="card-title">{title}</div>
        </div>
        {content_html}
    </div>
    """, unsafe_allow_html=True)


def render_results(kit, brand_name):
    """Render the complete brand kit results."""

    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; margin-top:12px;">
        <h2 style="margin:0; color:#EDECF0;">Your <em style="color:#E8C872;">Brand Kit</em></h2>
        <span style="font-size:12px; color:#6B6878;">Generated for "{brand_name}"</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # ── Taglines ──
    with col1:
        taglines_html = "".join(
            f'<div class="tagline-item">{t}</div>' for t in kit["taglines"]
        )
        render_card("Taglines", "⚡", "#E8C872", "rgba(232,200,114,0.12)", taglines_html)

    # ── Elevator Pitch ──
    with col2:
        render_card("Elevator Pitch", "💬", "#7EB3F0", "rgba(126,179,240,0.12)",
                     f'<div class="desc-text">{kit["elevator_pitch"]}</div>')

    col3, col4 = st.columns(2)

    # ── Descriptions ──
    with col3:
        desc_html = ""
        for label, key in [("One-liner", "short"), ("Website Hero", "medium"), ("About Page", "long")]:
            desc_html += f"""
            <div class="desc-block">
                <div class="desc-label">{label}</div>
                <div class="desc-text">{kit['descriptions'][key]}</div>
            </div>"""
        render_card("Descriptions", "📄", "#5DD9A8", "rgba(93,217,168,0.12)", desc_html)

    # ── Social Bios ──
    with col4:
        social_html = ""
        for label, key in [("Twitter / X", "twitter"), ("LinkedIn", "linkedin"), ("Instagram", "instagram")]:
            bio = kit["social_bios"][key].replace("\n", "<br>")
            social_html += f"""
            <div class="desc-block">
                <div class="desc-label">{label}</div>
                <div class="desc-text">{bio}</div>
            </div>"""
        render_card("Social Media Bios", "📱", "#F08A7E", "rgba(240,138,126,0.12)", social_html)

    # ── Brand Voice (full width) ──
    traits_html = '<div class="trait-grid">'
    for t in kit["brand_voice"]["traits"]:
        traits_html += f"""
        <div class="trait-card">
            <div class="trait-word">{t['word']}</div>
            <div class="trait-desc">{t['description']}</div>
        </div>"""
    traits_html += '</div>'

    guidelines_html = '<div class="guidelines-grid"><div>'
    guidelines_html += '<div class="guideline-label do-label">✓ Do</div>'
    for g in kit["brand_voice"]["do"]:
        guidelines_html += f'<div class="guideline-item">{g}</div>'
    guidelines_html += '</div><div>'
    guidelines_html += '<div class="guideline-label dont-label">✕ Don\'t</div>'
    for g in kit["brand_voice"]["dont"]:
        guidelines_html += f'<div class="guideline-item">{g}</div>'
    guidelines_html += '</div></div>'

    render_card("Brand Voice Guide", "🎙", "linear-gradient(90deg, #E8C872, #F08A7E)",
                "rgba(232,200,114,0.12)", traits_html + guidelines_html)


# ─────────────────────────────────────────────────────────────
# SIDEBAR — Input Form
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo">⚡</div>
        <div class="sidebar-title">Brand<span>Forge</span></div>
    </div>
    """, unsafe_allow_html=True)

    # API Key
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-... (optional for demo)",
        help="Get your key at console.anthropic.com. Leave blank for demo mode.",
    )
    st.session_state["api_key"] = api_key

    use_demo = not api_key
    if use_demo:
        st.info("🎭 **Demo mode** — using sample generation.  \nAdd an API key for live AI output.", icon="ℹ️")

    st.markdown("---")

    # Brand inputs
    brand_name = st.text_input("Brand Name *", placeholder="e.g. Solaris, Moonbeam")
    industry = st.selectbox("Industry", [""] + INDUSTRIES, format_func=lambda x: x or "Select industry…")
    audience = st.text_input("Target Audience", placeholder="e.g. Young professionals")
    differentiator = st.text_input("Key Differentiator", placeholder="e.g. AI-powered, sustainable")
    description = st.text_area("Brand Description", placeholder="Briefly describe your brand…", height=80)
    selected_tones = st.multiselect("Brand Tone", TONES, default=["Professional"])

    st.markdown("")
    generate_clicked = st.button("⚡ Generate Brand Kit", use_container_width=True, disabled=not brand_name)

    st.markdown('<div class="powered-badge">✦ Powered by Claude AI</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────

# Hero
st.markdown("""
<div style="padding-top: 20px;">
    <div class="hero-title">Generate your entire<br><span class="hero-accent">brand identity</span> in seconds</div>
    <div class="hero-sub">Fill in the sidebar and click Generate — our AI will craft taglines, bios, descriptions, and a complete voice guide.</div>
</div>
""", unsafe_allow_html=True)

# Session state for results
if "kit" not in st.session_state:
    st.session_state["kit"] = None
if "kit_brand" not in st.session_state:
    st.session_state["kit_brand"] = None

# Generate
if generate_clicked and brand_name:
    with st.spinner("✨ Generating your brand kit..."):
        try:
            if use_demo:
                time.sleep(1.5)  # Simulate loading
                kit = generate_sample_kit(
                    brand_name, industry, audience,
                    differentiator, description, selected_tones,
                )
            else:
                kit = generate_brand_kit(
                    brand_name, industry, audience,
                    differentiator, description, selected_tones,
                )
            st.session_state["kit"] = kit
            st.session_state["kit_brand"] = brand_name
        except json.JSONDecodeError:
            st.error("Failed to parse AI response. Please try again.")
        except anthropic.AuthenticationError:
            st.error("Invalid API key. Please check your key or use demo mode.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Show results
if st.session_state["kit"]:
    render_results(st.session_state["kit"], st.session_state["kit_brand"])

    # Export options
    st.markdown("---")
    st.markdown("### 📦 Export")

    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        json_str = json.dumps(st.session_state["kit"], indent=2)
        st.download_button(
            "📥 Download JSON",
            data=json_str,
            file_name=f"brandkit_{st.session_state['kit_brand'].lower().replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with exp_col2:
        kit = st.session_state["kit"]
        md_content = f"""# Brand Kit — {st.session_state['kit_brand']}

*Generated by BrandForge AI*

---

## Taglines

{chr(10).join(f'{i}. **{t}**' for i, t in enumerate(kit['taglines'], 1))}

## Elevator Pitch

{kit['elevator_pitch']}

## Descriptions

**One-liner:** {kit['descriptions']['short']}

**Website Hero:** {kit['descriptions']['medium']}

**About Page:** {kit['descriptions']['long']}

## Social Media Bios

**Twitter/X:** {kit['social_bios']['twitter']}

**LinkedIn:** {kit['social_bios']['linkedin']}

**Instagram:** {kit['social_bios']['instagram']}

## Brand Voice

| Trait | Description |
|-------|-------------|
{chr(10).join(f"| **{t['word']}** | {t['description']} |" for t in kit['brand_voice']['traits'])}

**Do:** {', '.join(kit['brand_voice']['do'])}

**Don't:** {', '.join(kit['brand_voice']['dont'])}
"""
        st.download_button(
            "📥 Download Markdown",
            data=md_content,
            file_name=f"brandkit_{st.session_state['kit_brand'].lower().replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
