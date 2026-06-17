import streamlit as st
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

# ── Doc registry — ordered by priority in the system prompt ──────────────────
# (title, relative_path, category)
_DOCS = [
    # ── Identity & Operating Context ─────────────────────────────────────────
    ("Jarvis Operating Standard",       "context/jarvis-operating-standard.md",           "identity"),
    ("Personal Info",                   "context/personal-info.md",                        "identity"),
    ("Strategy & Goals",                "context/strategy.md",                             "identity"),
    ("Trader Daily Lifestyle",          "context/trader-daily-lifestyle.md",               "identity"),
    ("Grand Plan",                      "context/grand-plan.md",                           "identity"),

    # ── Core Mr. Casino / CLS Methodology ────────────────────────────────────
    ("Full Methodology Rules",          "context/methodology-rules.md",                    "methodology"),
    ("Q&A Archive",                     "context/qa-archive.md",                           "methodology"),
    ("Mr. Casino Teaching Script",      "context/mr-casino-teaching-script.md",            "methodology"),
    ("Chart Catalog",                   "context/chart-catalog.md",                        "methodology"),

    # ── Blue Rabbit ──────────────────────────────────────────────────────────
    ("Blue Rabbit Profile",             "context/blue-rabbit-profile.md",                  "methodology"),
    ("Blue Rabbit EA Guidelines",       "scripts/CLS_BlueRabbit_EA_Guidelines.txt",        "methodology"),
    ("Blue Rabbit Integration Doc",     "scripts/CLS_BlueRabbit_Integration_Doc.txt",      "methodology"),

    # ── Psychology & Execution ────────────────────────────────────────────────
    ("Trading Psychology",              "context/trading-psychology.md",                   "psychology"),
    ("Reflection Tasks (Backtesting)",  "context/reflection-tasks.md",                     "psychology"),

    # ── CLS EA — Full Master Spec ─────────────────────────────────────────────
    ("CLS Master Spec (B1 Full)",       "scripts/CLS_B1_MasterSpec_UpdateForJJ.txt",       "ea_spec"),
    ("CLS B1b Final Spec",              "scripts/CLS_JJ_B1b_Spec_Jun08_FINAL.txt",         "ea_spec"),
    ("CLS B1b v1.6 Spec",               "scripts/CLS_B1b_v1.6_Spec_ForJJ.txt",             "ea_spec"),
    ("CLS B1b Zone Spec",               "scripts/CLS_JJ_ZoneSpec_Jun08.txt",               "ea_spec"),
    ("CLS B1b Zone Rebuild Task",       "scripts/CLS_JJ_ZoneRebuild_Task.txt",             "ea_spec"),
    ("CLS Zone Verify Jun11",           "scripts/CLS_JJ_ZoneVerify_Jun11.txt",             "ea_spec"),
    ("CLS Build Map (Current)",         "scripts/CLS_BuildMap_Current.txt",                "ea_spec"),
    ("CLS Master Task Jun10",           "scripts/CLS_JJ_MasterTask_Jun10.txt",             "ea_spec"),
    ("CLS Rebuild Task v2",             "scripts/CLS_JJ_RebuildTask_v2.txt",               "ea_spec"),

    # ── CLS Q&A ───────────────────────────────────────────────────────────────
    ("CLS Q&A (Main)",                  "scripts/CLS_JJ_QA_UpdateForJJ.txt",               "ea_qa"),
    ("CLS Q&A Jun08",                   "scripts/CLS_JJ_QA_Jun08_UpdateForJJ.txt",         "ea_qa"),

    # ── Trading Journal & Firm ────────────────────────────────────────────────
    ("Trading Journal 4.0 Spec",        "context/trading-journal-4-spec.md",               "systems"),
    ("Firm Portfolio Projections",      "context/firm-portfolio-projections.md",            "systems"),

    # ── Mr. Casino Source Material — Ebooks & Transcripts ────────────────────
    ("How Banks Harvest Stops (Transcript)", "context/mrc_banks_transcript.md",            "mrc_source"),
    ("Mr Casino — 10 Free Lessons",          "context/mrc_10_free_lessons.md",             "mrc_source"),
    ("Mr Casino — Quick Start Guide",        "context/mrc_quick_start.md",                 "mrc_source"),
    ("Mr Casino — Unlock The Market",        "context/mrc_unlock_market.md",               "mrc_source"),
    ("Mr Casino — Basic Steps Institutional","context/mrc_basic_steps.md",                 "mrc_source"),

    # ── Mr. Casino Discord — Full Export (585KB, topic-grouped) ─────────────
    ("Discord — Masterclass Core Teaching",  "context/discord_masterclass_full.md",        "mrc_discord"),
    ("Discord — Price Action Reflection",    "context/discord_price_action_full.md",       "mrc_discord"),
    ("Discord — Q&A Sessions",              "context/discord_qa_full.md",                 "mrc_discord"),
    ("Discord — Market Analysis",           "context/discord_analysis_full.md",           "mrc_discord"),
    ("Discord — EA / Robot / Algo",         "context/discord_ea_full.md",                 "mrc_discord"),
    ("Discord — Other Channels",            "context/discord_other_full.md",              "mrc_discord"),
]

_CATEGORY_LABELS = {
    "identity":    "Identity & Context",
    "methodology": "Mr. Casino / CLS Methodology",
    "psychology":  "Psychology & Execution",
    "ea_spec":     "CLS EA Specs",
    "ea_qa":       "CLS Q&A",
    "systems":     "Journal & Firm Systems",
    "mrc_source":  "Mr. Casino Source Material",
    "mrc_discord": "Mr. Casino Discord (Live Teaching)",
}

# Max chars per doc for large Discord extracts — keeps total context under ~140K tokens
_DISCORD_MAX_CHARS = 60_000


@st.cache_data
def load_methodology() -> str:
    """Load all strategy docs into one concatenated string for the AI system prompt."""
    parts = []
    for title, rel_path, category in _DOCS:
        path = ROOT / rel_path
        if path.exists():
            content = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not content:
                continue
            # Cap large Discord extracts so total context stays under ~140K tokens
            if category == "mrc_discord" and len(content) > _DISCORD_MAX_CHARS:
                content = content[:_DISCORD_MAX_CHARS] + f"\n\n[... {(len(content)-_DISCORD_MAX_CHARS)//1000}KB additional content available — ask Jarvis about specific topics ...]"
            label = _CATEGORY_LABELS.get(category, category)
            parts.append(f"## [{label}] {title}\n\n{content}")
    return "\n\n---\n\n".join(parts)


@st.cache_data
def get_doc_status() -> list[dict]:
    status = []
    for title, rel_path, category in _DOCS:
        path = ROOT / rel_path
        exists = path.exists()
        status.append({
            "doc":      title,
            "path":     rel_path,
            "category": _CATEGORY_LABELS.get(category, category),
            "loaded":   exists,
            "size_kb":  round(path.stat().st_size / 1024, 1) if exists else 0,
        })
    return status


def get_total_kb() -> float:
    total = 0
    for _, rel_path, _ in _DOCS:
        p = ROOT / rel_path
        if p.exists():
            total += p.stat().st_size
    return round(total / 1024, 0)
