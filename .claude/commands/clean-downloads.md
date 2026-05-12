# Clean Downloads

> Audit the Downloads folder and flag files that need sorting or deletion.

## Run

Scan `C:\Users\Malaa\Downloads` and categorize everything found:

1. **Stale installers** — any `.exe`, `.msi`, `.msix` files
2. **Duplicate files** — files with `(1)`, `(2)`, `(3)` in the name
3. **Old zips** — `.zip` files older than 30 days that aren't active projects
4. **Unsorted files** — anything that belongs in `01_TRADING`, `02_JARVIS`, `03_BUSINESS`, or `04_PERSONAL` but is sitting loose in Downloads
5. **Unknown files** — anything unrecognized

## Output

Report as a table:

| File | Category | Action |
|------|----------|--------|
| ... | Installer | Delete |
| ... | Trading doc | Move to 01_TRADING/strategy |
| ... | Duplicate | Delete |

Then ask: **"Approve all, or go item by item?"**

If approved, execute the moves and deletions.

## Rules

- Never delete without listing first
- Keep: `Telegram Desktop`, `jarvis_template` (active workspace)
- When in doubt, flag as "Review" rather than auto-delete
