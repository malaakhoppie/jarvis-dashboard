"""
Settings — API keys, service connections, and app preferences.
On Streamlit Cloud: reads from st.secrets (read-only).
On local: reads/writes config/config.env.
"""
import os
import requests
import streamlit as st
from pathlib import Path

ROOT       = Path(__file__).parent.parent.parent
CONFIG_ENV = ROOT / "config" / "config.env"

_CORRECT_TABLE_IDS = {
    "trades":        "tblQx04ovCVqlE3va",
    "daily_summary": "tblNwbrJMSIL8hJb9",
    "pattern_flags": "tblZG4C8mmH4kN4BH",
}


def _is_cloud() -> bool:
    return not CONFIG_ENV.exists()


def _load_env() -> dict[str, str]:
    if _is_cloud():
        result = {}
        for key in ["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID", "ANTHROPIC_API_KEY",
                    "TRADOVATE_USERNAME", "TRADOVATE_MODE", "TRADOVATE_CID"]:
            try:
                result[key] = st.secrets[key]
            except Exception:
                pass
        return result
    result = {}
    if not CONFIG_ENV.exists():
        return result
    for line in CONFIG_ENV.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _, value = stripped.partition("=")
            value = value.split(" #")[0].strip() if " #" in value else value.strip()
            result[key.strip()] = value
    return result


def _save_env(updates: dict[str, str]):
    if not CONFIG_ENV.exists():
        return
    lines = CONFIG_ENV.read_text().splitlines()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                continue
        new_lines.append(line)
    CONFIG_ENV.write_text("\n".join(new_lines))


def _mask(value: str, show: int = 8) -> str:
    if not value or value.startswith("your_"):
        return "(not set)"
    return value[:show] + "•" * min(12, max(0, len(value) - show))


def _status_card(title: str, dot_color: str, line1: str, line2: str = "") -> str:
    return (
        f"<div style='background:#0c0c14;border:1px solid #1a1a2e;border-radius:10px;padding:1rem'>"
        f"<div style='display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem'>"
        f"<div style='width:9px;height:9px;border-radius:50%;background:{dot_color};"
        f"box-shadow:0 0 6px {dot_color}'></div>"
        f"<span style='color:#f0f0f8;font-size:0.98rem;font-weight:700'>{title}</span></div>"
        f"<div style='color:#8888aa;font-size:0.85rem'>{line1}</div>"
        + (f"<div style='color:#44445a;font-size:0.8rem;margin-top:0.2rem'>{line2}</div>" if line2 else "")
        + "</div>"
    )


def render_settings():
    st.markdown("## Settings")

    env    = _load_env()
    cloud  = _is_cloud()

    if cloud:
        st.markdown(
            "<div style='background:#0a0a18;border:1px solid #f0b42944;border-radius:8px;"
            "padding:0.75rem 1rem;margin-bottom:1rem'>"
            "<span style='color:#f0b429;font-weight:600;font-size:0.88rem'>Streamlit Cloud mode — </span>"
            "<span style='color:#8888aa;font-size:0.85rem'>"
            "Keys are read from Streamlit Secrets (Settings → Secrets in the Streamlit dashboard). "
            "Changes here don't persist — update them in the cloud dashboard.</span></div>",
            unsafe_allow_html=True,
        )

    # ── Connections ───────────────────────────────────────────────────────────
    st.markdown("#### Connections")

    airtable_key  = env.get("AIRTABLE_API_KEY", "")
    airtable_base = env.get("AIRTABLE_BASE_ID", "appg72lUB8VIEKWy4")
    anthropic_key = env.get("ANTHROPIC_API_KEY", "")
    tv_user       = env.get("TRADOVATE_USERNAME", "")
    tv_mode       = env.get("TRADOVATE_MODE", "demo")

    if airtable_key and not airtable_key.startswith("your_"):
        try:
            r = requests.get(
                f"https://api.airtable.com/v0/meta/bases/{airtable_base}/tables",
                headers={"Authorization": f"Bearer {airtable_key}"},
                timeout=5,
            )
            at_ok = r.status_code == 200
        except Exception:
            at_ok = False
    else:
        at_ok = False

    anth_ok = bool(anthropic_key and not anthropic_key.startswith("your_") and len(anthropic_key) > 20)
    tv_ok   = bool(tv_user and not tv_user.startswith("your_"))

    c1, c2, c3 = st.columns(3)
    c1.markdown(_status_card(
        "Airtable", "#00e676" if at_ok else "#ff4444",
        "Connected" if at_ok else "Not connected",
        f"Base: {airtable_base[:14]}…",
    ), unsafe_allow_html=True)
    c2.markdown(_status_card(
        "Anthropic", "#00e676" if anth_ok else "#ff4444",
        "Key configured" if anth_ok else "Not configured",
        _mask(anthropic_key),
    ), unsafe_allow_html=True)
    c3.markdown(_status_card(
        "Tradovate", "#00e676" if tv_ok else "#f0b429",
        f"Mode: {tv_mode.upper()}",
        tv_user if tv_ok else "Not configured",
    ), unsafe_allow_html=True)

    st.divider()

    # ── API Keys ──────────────────────────────────────────────────────────────
    st.markdown("#### API Keys")

    if cloud:
        st.markdown(
            "<div style='color:#8888aa;font-size:0.88rem;margin-bottom:0.8rem'>"
            "Running on Streamlit Cloud. To change keys: open your app in "
            "<b>share.streamlit.io</b> → ⋮ → Settings → Secrets.</div>",
            unsafe_allow_html=True,
        )
        with st.expander("View current keys (masked)"):
            for k in ["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID", "ANTHROPIC_API_KEY",
                      "TRADOVATE_USERNAME", "TRADOVATE_CID", "TRADOVATE_MODE"]:
                v = env.get(k, "")
                st.markdown(
                    f"<div style='font-family:JetBrains Mono,monospace;font-size:0.82rem;"
                    f"color:#8888aa;margin-bottom:0.2rem'>"
                    f"<span style='color:#f0b429'>{k}</span> = {_mask(v) if k not in ('AIRTABLE_BASE_ID','TRADOVATE_MODE','TRADOVATE_USERNAME') else v}</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.markdown(
            "<div style='color:#8888aa;font-size:0.88rem;margin-bottom:0.8rem'>"
            "Stored in <code>config/config.env</code>. Restart the app after saving.</div>",
            unsafe_allow_html=True,
        )
        with st.form("api_keys_form"):
            k1, k2 = st.columns(2)
            with k1:
                new_anthropic     = st.text_input("Anthropic API Key",  value=env.get("ANTHROPIC_API_KEY", ""),  type="password")
                new_airtable_key  = st.text_input("Airtable API Key",   value=env.get("AIRTABLE_API_KEY", ""),   type="password")
                new_airtable_base = st.text_input("Airtable Base ID",   value=env.get("AIRTABLE_BASE_ID", "appg72lUB8VIEKWy4"))
            with k2:
                new_tv_user   = st.text_input("Tradovate Username", value=env.get("TRADOVATE_USERNAME", ""))
                new_tv_cid    = st.text_input("Tradovate CID",      value=env.get("TRADOVATE_CID", ""))
                new_tv_secret = st.text_input("Tradovate Secret",   value=env.get("TRADOVATE_SECRET", ""), type="password")
                new_tv_mode   = st.selectbox("Tradovate Mode", ["demo", "live"],
                                              index=0 if tv_mode == "demo" else 1)
            if st.form_submit_button("Save API Keys", use_container_width=True, type="primary"):
                _save_env({
                    "ANTHROPIC_API_KEY":  new_anthropic,
                    "AIRTABLE_API_KEY":   new_airtable_key,
                    "AIRTABLE_BASE_ID":   new_airtable_base,
                    "TRADOVATE_USERNAME": new_tv_user,
                    "TRADOVATE_CID":      new_tv_cid,
                    "TRADOVATE_SECRET":   new_tv_secret,
                    "TRADOVATE_MODE":     new_tv_mode,
                })
                st.success("Saved. Restart the app for changes to take effect.")

    st.divider()

    # ── Airtable Table IDs ────────────────────────────────────────────────────
    st.markdown("#### Airtable Tables")

    t1, t2, t3 = st.columns(3)
    for col, (name, tid) in zip([t1, t2, t3], _CORRECT_TABLE_IDS.items()):
        col.markdown(
            f"<div style='background:#0c0c14;border:1px solid #1a1a2e;border-radius:8px;padding:0.9rem'>"
            f"<div style='color:#f0b429;font-size:0.78rem;text-transform:uppercase;"
            f"letter-spacing:0.08em;margin-bottom:0.3rem'>{name}</div>"
            f"<div style='color:#f0f0f8;font-size:0.82rem;font-family:JetBrains Mono,monospace'>{tid}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='background:#0c0c14;border:1px solid #f0b429;border-radius:8px;"
        "padding:0.75rem 1rem;margin-bottom:0.8rem'>"
        "<span style='color:#f0b429;font-weight:600;font-size:0.88rem'>Token scopes required: </span>"
        "<span style='color:#8888aa;font-size:0.85rem'>"
        "<code style='color:#00d4ff'>data.records:read</code> + "
        "<code style='color:#00d4ff'>data.records:write</code> — both needed for CSV import. "
        "Edit at <b>airtable.com/create/tokens</b>.</span></div>",
        unsafe_allow_html=True,
    )

    tc1, tc2 = st.columns(2)
    if tc1.button("Test Read", use_container_width=True):
        if not airtable_key or airtable_key.startswith("your_"):
            st.error("No Airtable API key configured.")
        else:
            for name, tid in _CORRECT_TABLE_IDS.items():
                try:
                    r = requests.get(
                        f"https://api.airtable.com/v0/{airtable_base}/{tid}?maxRecords=1",
                        headers={"Authorization": f"Bearer {airtable_key}"},
                        timeout=8,
                    )
                    if r.status_code == 200:
                        count = len(r.json().get("records", []))
                        st.success(f"READ OK — {name} ({count} record(s))")
                    elif r.status_code == 403:
                        st.error(f"READ BLOCKED — {name}: token missing data.records:read scope")
                    else:
                        msg = r.json().get("error", {}).get("message", "Error")
                        st.error(f"{name}: {r.status_code} — {msg}")
                except Exception as e:
                    st.error(f"{name}: {e}")

    if tc2.button("Test Write (dry-run)", use_container_width=True):
        if not airtable_key or airtable_key.startswith("your_"):
            st.error("No Airtable API key configured.")
        else:
            try:
                r = requests.post(
                    f"https://api.airtable.com/v0/{airtable_base}/{_CORRECT_TABLE_IDS['trades']}",
                    headers={"Authorization": f"Bearer {airtable_key}", "Content-Type": "application/json"},
                    json={"fields": {"__write_test__": True}},
                    timeout=8,
                )
                if r.status_code == 403:
                    st.error(
                        "WRITE BLOCKED — token missing data.records:write scope. "
                        "Go to airtable.com/create/tokens → edit token → add data.records:write."
                    )
                elif r.status_code in (200, 201, 422):
                    st.success("WRITE OK — token has write permission.")
                else:
                    st.warning(f"Write test returned {r.status_code} — may still work.")
            except Exception as e:
                st.error(f"Write test failed: {e}")

    st.divider()

    # ── App Preferences ───────────────────────────────────────────────────────
    st.markdown("#### App Preferences")

    pref_c1, pref_c2 = st.columns(2)
    with pref_c1:
        if st.button("Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared — data will reload from Airtable.")
    with pref_c2:
        if not cloud:
            acct_path = ROOT / "config" / "accounts.json"
            if acct_path.exists():
                st.download_button(
                    "Export Accounts JSON",
                    data=acct_path.read_text(),
                    file_name="accounts.json",
                    mime="application/json",
                    use_container_width=True,
                )
        else:
            st.markdown(
                "<div style='color:#44445a;font-size:0.82rem;padding:0.4rem'>"
                "Account data lives in Airtable on cloud.</div>",
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown(
        "<div style='color:#44445a;font-size:0.82rem'>Jarvis v1.0 · June 2026 · "
        + ("☁ Cloud" if cloud else "💻 Local")
        + "</div>",
        unsafe_allow_html=True,
    )
