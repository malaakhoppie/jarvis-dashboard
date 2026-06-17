import json
import streamlit as st
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent.parent
_BUILD_PATH = ROOT / "config" / "build_status.json"


def _load() -> dict:
    if _BUILD_PATH.exists():
        return json.loads(_BUILD_PATH.read_text())
    return {"phases": [], "notes": ""}


def _save(data: dict):
    data["last_updated"] = str(date.today())
    _BUILD_PATH.write_text(json.dumps(data, indent=2))


def render_build_tracker():
    st.markdown("## CLS EA Build Tracker")

    data     = _load()
    phases   = data.get("phases", [])
    notes    = data.get("notes", "")
    updated  = data.get("last_updated", "—")
    changed  = False

    hc1, hc2 = st.columns([3, 1])
    with hc1:
        if notes:
            st.markdown(f"<div style='color:#9ca3af;font-size:0.92rem'>{notes}</div>", unsafe_allow_html=True)
    with hc2:
        st.markdown(
            f"<div style='color:#6b7280;font-size:0.85rem;text-align:right'>Updated: {updated}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    STATUS_STYLES = {
        "complete":    ("#14532d", "#22c55e", "✓ COMPLETE"),
        "in_progress": ("#422006", "#f59e0b", "⟳ IN PROGRESS"),
        "pending":     ("#1f2937", "#6b7280", "○ PENDING"),
    }

    for phase in phases:
        phase_id  = phase.get("id", "")
        name      = phase.get("name", "")
        status    = phase.get("status", "pending")
        desc      = phase.get("description", "")
        tasks     = phase.get("tasks", [])
        comp_date = phase.get("completed_date", "")
        start_d   = phase.get("started_date", "")

        total_tasks = len(tasks)
        done_tasks  = sum(1 for t in tasks if t.get("done"))
        progress    = done_tasks / total_tasks if total_tasks else 0

        border_bg, accent, status_label = STATUS_STYLES.get(status, STATUS_STYLES["pending"])
        is_current   = phase_id == data.get("current_phase", "")
        border_style = f"2px solid {accent}" if is_current else f"1px solid {border_bg}"
        bar_color    = accent

        st.markdown(
            f"<div style='background:#13131f;border:{border_style};border-radius:12px;"
            f"padding:1.2rem;margin-bottom:0.5rem'>"
            f"<div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.5rem'>"
            f"<div>"
            f"<span style='color:{accent};font-size:0.82rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.05em'>{phase_id}</span>"
            f"<span style='color:#f9fafb;font-size:1.1rem;font-weight:700;margin-left:0.6rem'>{name}</span>"
            f"</div>"
            f"<span style='background:{border_bg};color:{accent};padding:0.2rem 0.7rem;"
            f"border-radius:999px;font-size:0.78rem;font-weight:600'>{status_label}</span>"
            f"</div>"
            f"<div style='color:#9ca3af;font-size:0.88rem;margin-bottom:0.6rem'>{desc}</div>"
            + (f"<div style='color:#6b7280;font-size:0.78rem;margin-bottom:0.4rem'>Completed: {comp_date}</div>" if comp_date else "")
            + (f"<div style='color:#6b7280;font-size:0.78rem;margin-bottom:0.4rem'>Started: {start_d}</div>" if start_d else "")
            + (
                f"<div style='background:#1e1e3a;border-radius:999px;height:6px;margin-top:0.4rem'>"
                f"<div style='background:{bar_color};width:{progress*100:.0f}%;height:6px;border-radius:999px'></div>"
                f"</div>"
                f"<div style='color:#6b7280;font-size:0.78rem;margin-top:0.4rem'>{done_tasks}/{total_tasks} tasks complete</div>"
                if total_tasks else ""
            )
            + "</div>",
            unsafe_allow_html=True,
        )

        if tasks:
            with st.expander(f"Tasks ({done_tasks}/{total_tasks})", expanded=(status == "in_progress")):
                for i, task in enumerate(tasks):
                    prev_done = task.get("done", False)
                    new_done  = st.checkbox(
                        task.get("name", f"Task {i+1}"),
                        value=prev_done,
                        key=f"task_{phase_id}_{i}",
                    )
                    if new_done != prev_done:
                        task["done"] = new_done
                        changed = True

    if changed:
        _save(data)
        st.rerun()

    st.divider()
    st.markdown(
        "<div style='color:#6b7280;font-size:0.85rem'>"
        "Click any checkbox to mark a task complete. Saves automatically.</div>",
        unsafe_allow_html=True,
    )
