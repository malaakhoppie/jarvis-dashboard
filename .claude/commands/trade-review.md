# Trade Review

> Pre-trade check against the official Closed Loop Trading System (4-step intraday).
> All other rules (FU, HCS, zones, TFS) are refinements that feed INTO this system — not separate checklists.

---

## Step 0 — Daily Loss Limit (Run First, Always)

- Daily limit: **$250**
- Weekly limit: **$500**
- Risk per trade (funded): **$125 (0.5% of $25K)**
- Max trades per session: **1-3**

| P&L Today | Action |
|-----------|--------|
| -$125 | YELLOW — halfway to limit, slow down |
| -$200 | RED — strongly advise no more trades |
| -$250 | HARD STOP — close the laptop, done for the day |

---

## Step 0b — Session Window Check

Only trade during:
- **LDN:** 2am – 4am EST
- **NY:** 7am – 12pm EST ← primary
- **ASIA:** 7pm – 10pm EST

Outside these windows = no trade, no exceptions.

---

## The 4-Step Closed Loop (ALL 4 must be present — no exceptions)

### Step 1 — Intraday Major Liq Taken + Target
- Has intraday major liquidity been TAKEN? (swept, manipulated — not just approached)
- Is there a clear intraday major liquidity TARGET on the other side?
- **TF hierarchy:** Liq must be identified on intraday TFs (3hr–30m). HTF liq always overrides LTF liq.
- If no clear taken liq + clear target = **STOP. Do not proceed.**

### Step 2 — Price in Intraday MZ (Manipulation Zone)
- Is price currently inside a valid intraday Manipulation Zone?
- Valid MZ = FU zone / broken FU wick / FU+OB / IB zone
- Zone must be confirmed (HCS must have formed inside it on the relevant TF)
- **TF hierarchy:** MZ must be intraday TF (3hr–30m minimum). Lower TF MZs only valid for entry refinement.
- If price is NOT in a MZ = **STOP. Wait.**

### Step 3 — Intraday EM + Scalp TSL EM
- Has an Intraday Entry Model formed? (FU / ATT FU / HCS on intraday TF)
- Has a Scalp True Stop Level Entry Model formed within that? (10min+ HCS or negation minimum)
- **Minimum backing rule:** No 10min+ HCS/negation = NO trade. Full stop.
- Both must be present — intraday EM sets direction, scalp TSL EM confirms the entry zone

### Step 4 — LTF EM In Scalp TSL EM
- Has a LTF Entry Model formed (1m–7m) INSIDE the scalp TSL area?
- This is the actual trigger — FU or HCS on 1m/3m/5m within the scalp TSL EM zone
- SL goes under the FIRST FU — not the retest candle
- **TF hierarchy:** LTF EM cannot override scalp/intraday direction. Must align, not conflict.

---

## TF Hierarchy Rules (Non-Negotiable)

- HTF manipulation always overpowers LTF — always
- 4hr FU down + 5m FU up = still bearish. Do not buy.
- Each step must be on the correct TF tier:
  - Step 1-2: Intraday (3hr–30m)
  - Step 3: Scalp (30m–7m)
  - Step 4: LTF entry (7m–1m)
- Never skip a TF tier. Never use LTF to justify against HTF.

---

## Verdict

| Score | Result |
|-------|--------|
| All 4 steps + valid session + no loss limit breach | GREEN — valid trade |
| Steps 1-2 present, waiting on 3-4 | YELLOW — wait for confirmation, do not force |
| Missing step 1 or 2 | RED — no setup, walk away |
| Loss limit hit | HARD STOP — no trade regardless of setup |

End every review with:
> "Break even ASAP. Never let a winner turn into a loser."
