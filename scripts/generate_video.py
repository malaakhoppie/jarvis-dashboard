"""
Mala — Mr. Casino Full Curriculum Video Generator
Complete 8-Chapter Teaching Video — Beginner to Closed Loop Mastery
Voice: en-GB-RyanNeural (Microsoft Neural TTS)
Captions: burned-in subtitle bar + external SRT file
Output: mala-curriculum-full.mp4 + mala-curriculum-full.srt
"""

import os, re, textwrap, numpy as np, asyncio
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

# ── Config ────────────────────────────────────────────────────────────────────
W, H       = 1920, 1080
FPS        = 15
BG         = (13, 13, 13)
WHITE      = (255, 255, 255)
GOLD       = (212, 175, 55)
DIM        = (160, 160, 160)
VOICE      = "en-GB-RyanNeural"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR  = os.path.join(SCRIPT_DIR, "_audio_tmp")
OUT_FILE   = os.path.join(os.path.dirname(SCRIPT_DIR), "mala-curriculum-full.mp4")
SRT_FILE   = os.path.join(os.path.dirname(SCRIPT_DIR), "mala-curriculum-full.srt")
os.makedirs(AUDIO_DIR, exist_ok=True)

FONT_BOLD  = "C:/Windows/Fonts/arialbd.ttf"
FONT_REG   = "C:/Windows/Fonts/arial.ttf"
FONT_LIGHT = "C:/Windows/Fonts/ariali.ttf"

CHART_1 = r"C:\Users\Malaa\OneDrive\01_TRADING\discord-exports\❓understanding-manipulation❓\images\XAUUSD_2022-11-06_12-02-28-81914d39dc3fea8d.png"
CHART_2 = r"C:\Users\Malaa\OneDrive\01_TRADING\discord-exports\❓understanding-manipulation❓\images\XAUUSD_2022-11-24_17-38-19_79f2d-dc09d535d269fd48.png"
CHART_3 = r"C:\Users\Malaa\OneDrive\01_TRADING\discord-exports\❓understanding-manipulation❓\images\XAUUSD_2022-11-06_11-47-32-0e563ddb1e889a0f.png"
CHART_4 = r"C:\Users\Malaa\OneDrive\01_TRADING\discord-exports\❓understanding-manipulation❓\images\XAUUSD_2022-11-06_11-43-56-d5ccb4a34c79afba.png"
CHART_5 = r"C:\Users\Malaa\OneDrive\01_TRADING\discord-exports\❓understanding-manipulation❓\images\XAUUSD_2022-11-06_11-39-06-1b673692811fe71f.png"

# ── SRT tracking ─────────────────────────────────────────────────────────────
_clip_log = []    # list of ('narration'|'silent', duration_or_tag)

def _srt_time(ms):
    h = ms // 3_600_000; ms %= 3_600_000
    m = ms // 60_000;    ms %= 60_000
    s = ms // 1_000;     ms %= 1_000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def _shift_srt(raw_srt, offset_ms):
    """Shift all timestamps in an SRT block by offset_ms."""
    def shift(match):
        t = match.group(0)
        h, rest = t.split(':', 1)
        m, rest2 = rest.split(':', 1)
        s, ms_str = rest2.split(',')
        total = (int(h)*3600 + int(m)*60 + int(s))*1000 + int(ms_str) + offset_ms
        total = max(0, total)
        return _srt_time(total)
    return re.sub(r'\d{2}:\d{2}:\d{2},\d{3}', shift, raw_srt)

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def wrap(text, width=52):
    return textwrap.wrap(text, width=width)

def _draw_caption_bar(d, text, font, y_base):
    """Draw a semi-transparent caption bar at the bottom of the image."""
    lines = textwrap.wrap(text, width=90)[:2]  # max 2 lines
    for i, ln in enumerate(lines):
        y = y_base + i * 38
        # Shadow for readability
        d.text((W//2 + 1, y + 1), ln, font=font, fill=(0,0,0), anchor="mm")
        d.text((W//2, y), ln, font=font, fill=WHITE, anchor="mm")

def make_title_card(title, subtitle=None, duration=4.0):
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)
    tf  = load_font(FONT_BOLD, 90)
    sf  = load_font(FONT_REG,  42)
    d.line([(240, H//2 - 80), (W - 240, H//2 - 80)], fill=GOLD, width=2)
    d.text((W//2, H//2 - 10), title, font=tf, fill=GOLD, anchor="mm")
    d.line([(240, H//2 + 70), (W - 240, H//2 + 70)], fill=GOLD, width=2)
    if subtitle:
        d.text((W//2, H//2 + 130), subtitle, font=sf, fill=DIM, anchor="mm")
    c = ImageClip(np.array(img), duration=duration).with_fps(FPS)
    _clip_log.append(('silent', duration))
    return c

def make_quote_card(quote, author=None, duration=6.0):
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)
    qf  = load_font(FONT_LIGHT, 54)
    af  = load_font(FONT_REG,   34)
    lines = wrap(f'"{quote}"', width=50)
    total = len(lines) * 66
    y = (H - total) // 2
    for ln in lines:
        d.text((W//2, y), ln, font=qf, fill=WHITE, anchor="mm")
        y += 66
    if author:
        d.text((W//2, y + 30), f"— {author}", font=af, fill=GOLD, anchor="mm")
    c = ImageClip(np.array(img), duration=duration).with_fps(FPS)
    _clip_log.append(('silent', duration))
    return c

def make_text_slide(heading, bullets, audio_clip, caption_text=""):
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)
    hf  = load_font(FONT_BOLD, 62)
    bf  = load_font(FONT_REG,  38)
    cf  = load_font(FONT_REG,  30)
    d.text((W//2, 130), heading, font=hf, fill=GOLD, anchor="mm")
    d.line([(160, 185), (W - 160, 185)], fill=GOLD, width=1)
    y = 250
    for b in bullets:
        lines = wrap(b, width=62)
        for i, ln in enumerate(lines):
            prefix = "·  " if i == 0 else "    "
            d.text((200, y), prefix + ln, font=bf, fill=WHITE)
            y += 50
        y += 12
    # Caption bar at bottom
    if caption_text:
        bar = Image.new("RGBA", (W, 90), (0, 0, 0, 180))
        img_rgba = img.convert("RGBA")
        img_rgba.paste(bar, (0, H - 90), bar)
        img = img_rgba.convert("RGB")
        d2 = ImageDraw.Draw(img)
        _draw_caption_bar(d2, caption_text, cf, H - 78)
    dur = audio_clip.duration
    return ImageClip(np.array(img), duration=dur).with_fps(FPS)

def make_chart_slide(chart_path, label, audio_clip, caption_text=""):
    base = Image.open(chart_path).convert("RGB").resize((W, H), Image.LANCZOS)
    overlay = Image.new("RGBA", (W, 90), (13, 13, 13, 200))
    base_rgba = base.convert("RGBA")
    base_rgba.paste(overlay, (0, 0), overlay)
    img = base_rgba.convert("RGB")
    d  = ImageDraw.Draw(img)
    lf = load_font(FONT_BOLD, 36)
    cf = load_font(FONT_REG,  30)
    d.text((W//2, 45), label, font=lf, fill=GOLD, anchor="mm")
    if caption_text:
        bar = Image.new("RGBA", (W, 90), (0, 0, 0, 200))
        img_rgba = img.convert("RGBA")
        img_rgba.paste(bar, (0, H - 90), bar)
        img = img_rgba.convert("RGB")
        d2 = ImageDraw.Draw(img)
        _draw_caption_bar(d2, caption_text, cf, H - 78)
    dur = audio_clip.duration
    return ImageClip(np.array(img), duration=dur).with_fps(FPS)

async def _synthesize(text, path):
    sub = edge_tts.SubMaker()
    c = edge_tts.Communicate(text, VOICE)
    with open(path, 'wb') as f:
        async for chunk in c.stream():
            if chunk['type'] == 'audio':
                f.write(chunk['data'])
            elif chunk['type'] == 'WordBoundary':
                sub.feed(chunk)
    srt_path = path.replace('.mp3', '.srt')
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(sub.get_srt())

def tts(text, tag):
    path = os.path.join(AUDIO_DIR, f"{tag}.mp3")
    if not os.path.exists(path):
        print(f"  >> Generating audio: {tag}")
        asyncio.run(_synthesize(text, path))
    a = AudioFileClip(path)
    _clip_log.append(('narration', tag, a.duration))
    return a

def write_srt():
    """Build and write the merged SRT file from per-segment SRT files."""
    offset_ms = 0
    all_entries = []
    for record in _clip_log:
        if record[0] == 'silent':
            offset_ms += int(record[1] * 1000)
        elif record[0] == 'narration':
            tag = record[1]
            dur_ms = int(record[2] * 1000)
            srt_path = os.path.join(AUDIO_DIR, f"{tag}.srt")
            if os.path.exists(srt_path):
                with open(srt_path, 'r', encoding='utf-8') as f:
                    raw = f.read().strip()
                if raw:
                    shifted = _shift_srt(raw, offset_ms)
                    all_entries.append(shifted)
            offset_ms += dur_ms

    # Merge and renumber
    merged = []
    entry_num = 1
    for block in all_entries:
        entries = re.split(r'\n\n+', block.strip())
        for entry in entries:
            lines = entry.strip().split('\n')
            if len(lines) >= 2:
                merged.append(f"{entry_num}")
                merged.extend(lines[1:])  # skip original entry number
                merged.append("")
                entry_num += 1

    with open(SRT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(merged))
    print(f"  SRT written -> {SRT_FILE}")

# ── Narration Segments ────────────────────────────────────────────────────────

SEGMENTS = {

# INTRO ────────────────────────────────────────────────────────────────────────
"intro_a": (
    "Mala. "
    "This one is for you specifically. "
    "What I am about to walk you through is not a general overview. "
    "It is not a summary of concepts you have seen written down somewhere. "
    "This is the complete picture — rebuilt from the ground up, in the correct order, "
    "with everything connected — so that by the end, you are not just someone who understands the method. "
    "You are someone who can sit down, open a chart, and execute with full clarity every single session."
),
"intro_b": (
    "We are going to start at the very beginning. And I mean the very beginning. "
    "Because no matter how long you have been studying, the foundations either become second nature "
    "or they become assumptions. And assumptions are where gaps hide. "
    "We go through all of it. Foundation. Core language. Structure. The story. "
    "Daily execution. And finally — the four-step closed loop system that ties every concept "
    "you have ever learned into one clean, repeatable framework for extraction. "
    "By the end of this, you will know exactly where you are, exactly what you are doing "
    "when you sit down to trade, and exactly why each piece of the framework exists. "
    "Let us begin."
),

# CHAPTER 1 ────────────────────────────────────────────────────────────────────
"ch1_a": (
    "Before we touch a concept. Before we look at a single candle. "
    "Before anything — this truth must be embedded into your thinking so deeply "
    "that it reshapes every decision you make. "
    "Every trader starts off non-profitable. "
    "You have heard this. But hearing it and truly internalising it are two completely different things. "
    "Most people nod at it and move on. And then they trade as if it does not apply to them. "
    "As if their intelligence, their effort, their drive somehow exempts them "
    "from the universal starting point of this industry. "
    "It does not."
),
"ch1_b": (
    "Here is what this statement actually means — not philosophically — statistically. "
    "Most people assume trading gives you a fifty-fifty chance. Buy or sell. Fifty percent. "
    "But this is not a coin flip market. This is a manipulated, engineered environment. "
    "The banks need liquidity to fill their orders. Billions of dollars cannot be placed quietly — "
    "they need a counterparty. That counterparty is retail. Your stop loss. "
    "Ten thousand people's stop losses. All clustered at the same obvious level. "
    "The real statistic for an uninformed retail trader is not fifty percent. It is zero. "
    "Not fifty. Zero. The manipulation makes the probability effectively zero "
    "for anyone operating without a true understanding of the mechanics."
),
"ch1_c": (
    "This is not discouraging. This is the most liberating thing I can tell you. "
    "Because it means the problem was never your intelligence. It was never your character. "
    "It was simply that no one handed you the actual floor plan of the building. "
    "The retail world was handing you a fake map and telling you it was real. "
    "ICT — Michael Huddleston — was the first to expose the true map. "
    "What we do here is a refinement of that truth, taken further, made more precise. "
    "We trade with a minimum risk-to-reward of one to twenty. "
    "Our trades regularly close at one to fifty, one to a hundred — not unusually higher. "
    "We target a win rate of sixty percent minimum. Most students, once the method is genuinely "
    "internalised, achieve seventy to ninety percent. "
    "One percent of your account at one to twenty risk-to-reward equals twenty percent account growth "
    "in a single trade. That is the floor plan. And now we build with it."
),

# CHAPTER 2 ────────────────────────────────────────────────────────────────────
"ch2_intro": (
    "One word sits beneath every concept in this method. "
    "Every candle formation, every entry model, every zone, every timeframe decision — "
    "they all exist to serve this one word. Liquidity. "
    "Write it down. Say it. Understand it at its root. "
    "Liquidity in our context means this: any obvious area on the chart "
    "where retail stop losses are clustered. That is all. "
    "Any place where a mass of retail orders is sitting — either as stops waiting to be triggered, "
    "or as positions yet to be filled — is liquidity. "
    "Banks need liquidity to fill their orders. "
    "To place a billion-dollar position, you need someone on the other side. "
    "That someone is retail. The banks move price into the obvious retail clusters, "
    "trigger the stops, fill their institutional orders — and then reverse. "
    "The retail stops become the bank's fuel. This is the manipulation. The entire game."
),
"ch2_type1": (
    "There are five types of major liquidity. You must know these five with complete certainty. "
    "These are the targets. These are what you mark first, every session, every day, "
    "before any other decision is made. "
    "Type one — the unmanipulated doji. "
    "A doji that forms within a previous candle's wick. A pure, equal-force candle. "
    "No FU element, no manipulation. Just a clean balance. "
    "Retail traders learn that dojis signal reversals. They place stops just above or below it. "
    "Banks know this. The concentration of retail stops at this level makes it a premium target. "
    "The critical distinction — a true doji stays contained within the previous candle's wick. "
    "It has not taken any liquidity outside that range. "
    "If it has reached outside the previous wick even partially — it is an Attempted FU, not a true doji. "
    "Confusing these two will cost you RR and win rate."
),
"ch2_type2": (
    "Type two — the perfect double top or bottom. "
    "Not almost. Not close. Perfect. The exact same price level, touched twice, with matching precision. "
    "Check this on your broker platform. Not TradingView. "
    "TradingView data can deviate fractionally. In our world, fractions matter. "
    "IC Markets or Forex dot com — these are your verification sources. "
    "A perfect double top creates the illusion that price cannot break through. "
    "Every chartist in the world can identify it. "
    "That concentration of obvious retail orders is exactly why it becomes a target. "
    "A double or triple rejection that is point one pip apart — major liquidity, premium entry signal. "
    "A pip-perfect rejection — price reacts to exactly one pip apart — "
    "is actually the sign of manipulation, and is considered low liquidity. Know the difference."
),
"ch2_type3": (
    "Type three — the perfect trendline. Three perfect rejections minimum. Not two. Three. "
    "Two rejections make a trendline visible. Three rejections make it undeniable. "
    "Every retail trader can see a three-touch trendline. "
    "They load it with orders. They place their stops beyond it. "
    "The more obvious it is, the more liquidity it contains. "
    "The more liquidity it contains — the more certain it is that price will target it. "
    "Two touches: minor liquidity. Three or more: major. "
    "Do not mark a two-touch trendline as a major target."
),
"ch2_types45": (
    "Type four — the imbalanced candle. "
    "A move that begins instantly in one direction. No wick rejection at the open. No hesitation. "
    "Just immediate momentum. No wick means it is a true imbalance. "
    "If a wick is present on that side — price has already been manipulated there. "
    "A true imbalanced candle has no wick on the entry side. "
    "Price is always attracted back to fill these areas. "
    "Type five — the Fair Value Gap. "
    "A gap between candles where price moved so fast "
    "that the first and third candle of a sequence do not overlap. "
    "A blank space left in the order book. Price is always attracted back to fill it. "
    "Use five-minute and above imbalances only. "
    "Always verify imbalances on your broker platform, never TradingView."
),
"ch2_chart": (
    "Here is a real example from XAU USD on the four-hour timeframe. "
    "Major liquidity being taken. An Attempted FU forms — the weak start, the banks testing. "
    "Then all the liquidity on the buy side is finally swept. "
    "The annotation reads — buys are finally ready. "
    "And the target on the other side? A five-hundred pip move. "
    "With a stop loss of just ten pips. "
    "This is what liquidity calculation gives you. "
    "Not guesswork. Reading the manipulation and following the banks."
),
"ch2_daily": (
    "On the daily timeframe — a different perspective. "
    "Notice the Attempted FU forming. "
    "Then a doji retest of the Attempted FU — this is low liquidity. "
    "The imbalances are marked. "
    "Price is always attracted back to these unfilled areas. "
    "The daily chart tells the macro story. "
    "Everything on the lower timeframes is serving this macro structure. "
    "Never trade a lower timeframe signal that fights the daily story."
),
"ch2_process": (
    "Here is the daily liquidity calculation process. "
    "Step one — open your chart from the weekly timeframe. No bias. "
    "You are mapping the terrain. Where are the major dojis? Double tops? Trendlines? Imbalances? "
    "Mark them. Both sides. "
    "Step two — drop to the daily, then the four-hour. Continue mapping. "
    "Step three — drop to the one-hour and thirty-minute. Now you begin to read direction. "
    "Which side has more manipulation building? More FU clusters, more HCS formations? "
    "The side with more concentrated lower timeframe manipulation is where price is heading. "
    "Step four — you know the major target and the direction. "
    "You do not trade yet. You wait for your entry model. "
    "One final rule — place your take profit slightly before the target, not at it. "
    "Price may react without fully taking the level. Protect the profit."
),

# CHAPTER 3 ────────────────────────────────────────────────────────────────────
"ch3_intro": (
    "You know where to look — the liquidity targets. "
    "Now you learn how to read what price is doing as it moves toward and away from those targets. "
    "This is the language. And you must become fluent, not merely familiar. "
    "There are five formations in this language: "
    "the FU candle, the Attempted FU, the Negation, the X3, and the High Confluence Setup. "
    "Master these five and you can read any chart on any timeframe in any market."
),
"ch3_fu_a": (
    "The FU candle is the most important formation in this entire method. "
    "It does two things within the same candle. "
    "It takes liquidity in one direction — the wick reaches out and hunts the stops. "
    "Then it closes strongly in the opposite direction — the body reverses. "
    "Both. In one candle. The wick is the hunt. The body is the true move beginning. "
    "Two confirmations are required for a valid FU. "
    "First — it takes liquidity. The wick reaches into an area of retail stop losses. "
    "Second — it breaks structure. The close is in the opposite direction, breaking a previous high or low. "
    "The stronger the close — the less rejection wick on the body side — the stronger the signal. "
    "The FU wick becomes your Point of Interest. "
    "Where did the banks enter? At the base of that wick. "
    "Where do banks re-enter? Often at the same level on a retest. "
    "A retest of the FU wick is one of your most reliable entry models."
),
"ch3_fu_b": (
    "There are specific types of FU candles you must distinguish. "
    "The Strong FU — full body close in the opposite direction after taking liquidity. The best signal. "
    "The Attempted FU — started as an FU, took liquidity with the wick, "
    "but closed as a doji instead of a strong reversal. "
    "The banks stepped in but did not commit fully. "
    "This creates minor liquidity — not a major target. "
    "Distinguishing the Attempted FU from a true unmanipulated doji is critical. "
    "The Attempted FU has a wick that took liquidity outside a previous range. "
    "The true doji does not. "
    "And the three-candle FU — the FU formation spread across three candles instead of one. "
    "The wick phase, the hesitation, the close — each on a separate candle. "
    "The logic is identical. The execution requires recognising the spread."
),
"ch3_attfu_chart": (
    "Here on this four-hour XAU USD chart — the Attempted FU story unfolds. "
    "A weak start from the ATT FU — the banks testing but not committing. "
    "Failed to form a clean FU low — banks applying pressure. "
    "Then a huge drop without a proper manipulation candle on the four-hour — "
    "because the real confirmation was already on the daily zone. "
    "This is the Attempted FU in its natural context. "
    "The wick came out, tested the level, but the body told the real story. "
    "Daily zone below confirmed the direction. "
    "The big move happened not because of the ATT FU — "
    "but because of what sat beneath it in the structure."
),
"ch3_negation_a": (
    "When banks form an FU in one direction — "
    "and the very next candle forms an FU in the opposite direction — this is a negation. "
    "What happened? The banks attempted to move price one way. "
    "Then they changed their mind — or the opposite side had more power. "
    "The second FU cancels the first. The power of the first move is exhausted. "
    "Change in order flow begins. "
    "The negation is not just information — it is a trade. "
    "The wick of the negating candle becomes a Point of Interest. Mark it. "
    "When price returns to that wick area, you have a potential entry in the direction of the negation."
),
"ch3_negation_b": (
    "Negation counting rule: if the first candle after an FU forms as an Attempted FU — "
    "not a complete negation — the second candle can still count as the negation. "
    "Give it two candles to confirm before dismissing. "
    "One-minute negations: potential entries on the lowest timeframe. "
    "Four-hour negations: powerful directional signals for the session. "
    "The logic is identical across all timeframes — only the weight of the statement differs. "
    "A higher timeframe negation always outweighs a lower timeframe FU pointing the other way. "
    "This is timeframe strength in action."
),
"ch3_neg_chart": (
    "On this four-hour chart — watch the negation unfold in real time. "
    "The Attempted FU sell forms — weakness. "
    "Other liquidity is being generated on the buy side as the sell fails. "
    "The strong negation forms — buys are finally ready. "
    "Notice the one-hour double bottom sitting below this move. "
    "That lower timeframe structure was holding up against the sell pressure — "
    "which is exactly why the sell move could not sustain itself. "
    "The negation here was backed by the lower timeframe structure. "
    "Multi-timeframe alignment is the difference between a signal and a trade."
),
"ch3_x3": (
    "X3 is when a negation itself gets negated. "
    "Three layers of manipulation stacking on each other. "
    "Three instances of banks fighting for this level. "
    "By the third — the fight is over. "
    "One side has exhausted itself. The true move begins with the full force of triple confirmation. "
    "The three phases: "
    "First — an FU wick in one direction. "
    "Second — a negation attempt — the opposing FU. "
    "Third — that negation is broken — the original direction asserts with conviction. "
    "This can be spread across multiple candles. "
    "What you are looking for is the pattern: push, counter, counter-counter. "
    "When you see all three — you have X3. "
    "Every true move should begin with some form of X3 confirmation. "
    "A single FU on a one-minute chart means nothing in isolation. "
    "An X3 building at a major liquidity level on a backed timeframe — that is your signal."
),
"ch3_hcs_a": (
    "When an FU candle is retested — and the retest itself forms an FU — you have an HCS. "
    "A High Confluence Setup. "
    "The anatomy: "
    "First FU — banks moved. True direction established. "
    "Retest — retail attempts to reclaim. Price returns to the FU wick. "
    "Retest FU — the banks defend aggressively. They step in at the retest "
    "and drive price back in the original direction. "
    "Three events. Three confirmations. All pointing the same way. "
    "The HCS carries double the strength of a standard FU on the same timeframe. "
    "A thirty-minute HCS is equivalent to a one-hour FU in timeframe strength. "
    "A one-hour HCS is equivalent to a two-hour FU. "
    "This is structural mathematics — two institutional confirmations stacked."
),
"ch3_hcs_b": (
    "Mr Domino's rule — one of the most important you will absorb. "
    "We only trade HCS. Only. "
    "This is not an exaggeration. The HCS is the filter that separates high-probability from noise. "
    "Two uses: "
    "As directional bias on higher timeframes — "
    "an HCS on the four-hour tells you the banks are comfortable and targeting the opposite side. "
    "As an entry model on lower timeframes — "
    "when the second FU forms on the retest, that is your trigger. "
    "Stop loss for HCS entries: the SL goes under the FIRST FU — not the retest candle. "
    "This is the most common mistake. "
    "If the first FU is broken, the entire HCS is invalidated. "
    "Zone validity rule: a zone is only confirmed valid when an HCS forms INSIDE it. "
    "Fresh zone equals potential. HCS inside zone equals confirmed."
),
"ch3_phase3": (
    "This changes how you execute entries at every level once you understand it. "
    "Every FU candle, in its mechanics, consists of four phases. "
    "Phase one — the cluster. Retail stop losses are sitting at a level. "
    "Banks know where it is. They are targeting it. "
    "Phase two — the sweep. Price moves through the cluster. "
    "Stop losses are triggered. Breakout traders enter in the wrong direction. "
    "Banks fill their orders using this stop-loss fuel. "
    "Phase three — the return. Price returns to the exact same price level "
    "as the original cluster — coming from the opposite side. "
    "This is the banks completing their order fill. The FU is forming right now. "
    "Phase four — the true move. Direction established. The actual move begins. "
    "The entry secret: enter on Phase three. "
    "Not after the FU closes — that is Phase four. The RR is already diminished. "
    "Phase three — when price returns to the exact original cluster level from the opposite side. "
    "That is your entry. Tightest possible stop. Best possible RR. "
    "If you are late to Phase three — do not enter. Wait for the next opportunity."
),

# CHAPTER 4 ────────────────────────────────────────────────────────────────────
"ch4_tfs_a": (
    "One rule. Memorise it. Apply it without exception. "
    "Higher timeframe manipulation always overpowers lower timeframe manipulation. "
    "If a four-hour FU points down — you need a four-hour or higher FU pointing up to negate it. "
    "A one-minute FU pointing up is not a reversal signal. "
    "It is an entry signal within the downward four-hour move, or it is noise. "
    "A three-hour or higher confirmed FU closure is what we look for to identify prevalent direction. "
    "On timeframes below three hours — we are only looking at HCS and negation formations. "
    "Not confirmed FU closures. That distinction matters."
),
"ch4_tfs_b": (
    "The timeframe hierarchy for entries. "
    "Swing entries require a three-hour or higher confirmed FU closure. "
    "Intraday entries require a one-hour or higher HCS or negation alignment. "
    "Scalp entries require a ten-minute or higher HCS or negation. "
    "The absolute minimum: no ten-minute or higher HCS or negation backing equals no trade. "
    "This is not negotiable. "
    "If you cannot identify a ten-minute or higher HCS or negation that supports your entry — "
    "you do not have a trade. You have hope. And hope is not a trading plan. "
    "The strength equivalency: "
    "a thirty-minute HCS equals a one-hour FU in weight. "
    "A one-hour HCS equals a two-hour FU. "
    "HCS always doubles the timeframe strength of its base timeframe."
),
"ch4_zones_a": (
    "Zones are powerful — but they are secondary to liquidity. "
    "Do not fixate on a zone when the liquidity story says otherwise. "
    "Zones confirm. Liquidity decides. "
    "There are two types of zones. "
    "The standard orderblock zone: the last opposing candle before a significant move — "
    "the body only, no wicks, unless manipulation occurred in the wick. "
    "Four-hour zones are the most powerful and hold long-term. "
    "One-hour zones drive intraday sharp rejections. "
    "Thirty-minute minimum for a valid zone."
),
"ch4_zones_b": (
    "The manipulation zone — advanced. "
    "The formula: orderblock plus FU, plus any manipulation sign — another FU, "
    "Attempted FU, or another orderblock — AND liquidity inside the zone. "
    "This is a zone pre-confirmed by manipulation. "
    "The key difference: the presence of internal liquidity — stops sitting inside the zone itself. "
    "A manipulation zone is valid for twenty-four hours only. After that, discard it. Refresh. "
    "Zone refinement: a one-hour zone refines to fifteen-minute only. "
    "A fifteen-minute manipulation zone refines to five-minute only. "
    "Strongest confluence: weekly, daily, and four-hour zones overlapping. "
    "Zone validity has two stages: "
    "fresh — the orderblock plus FU. Potential. "
    "Confirmed — an HCS forms inside the zone. Only at this stage is the zone fully valid for entry."
),
"ch4_zones_chart": (
    "Here on the daily chart — watch how the zone and liquidity work together. "
    "The Attempted FU at the low. The imbalances marked above. "
    "The daily zone acting as the structural anchor for this entire move. "
    "Zone plus liquidity plus timeframe alignment working together. "
    "This is not one signal — it is four signals from different systems "
    "all pointing at the same area. That convergence is what you are always looking for."
),
"ch4_true_stop": (
    "The True Stop is the most concentrated area of manipulation "
    "where both buy and sell orders occur without the level breaking. "
    "It is our version of the break of structure — "
    "identified through manipulation language, not retail patterns. "
    "When the True Stop breaks — the banks are targeting liquidity beyond that point. "
    "The True Stop being broken is not a loss — it is information. "
    "How to identify it: "
    "find a move on the higher timeframe. "
    "Go to the beginning of that move. "
    "Refine down to where the manipulation happened. "
    "On the lower timeframe — multiple manipulation events concentrated at one level — "
    "that is your True Stop. "
    "At a major HTF doji or Last Area of Liquidity — four levels to watch. "
    "Level one: low of the doji. "
    "Level two: fifty percent of the doji body. "
    "Level three: high of the doji. "
    "Level four: fifty percent of the wick. "
    "If one level breaks, move to the next. "
    "Level four breaks — the zone is invalid. Done."
),

# CHAPTER 5 ────────────────────────────────────────────────────────────────────
"ch5_intro": (
    "Individual concepts are vocabulary. The top-down analysis is the grammar. "
    "This is where you stop seeing isolated candles "
    "and start reading the complete market narrative from highest timeframe to lowest. "
    "Every professional trader operates from the top down. "
    "They do not start at the one-minute and work upward. "
    "They start at the weekly — build the map — "
    "and by the time they reach the entry timeframe, they already know the answer. "
    "The one-minute trigger is just the final confirmation of a decision already made."
),
"ch5_topdown_a": (
    "Step one — weekly and daily: the landscape. "
    "Open with no bias. You are reading the terrain. "
    "Where are the major dojis? Double tops and bottoms? Major trendlines? "
    "Imbalances and fair value gaps? Mark them — both directions. "
    "These are your macro targets. Every intraday move is serving these. "
    "Step two — four-hour: institutional zones and bias. "
    "What zones exist? Where has price been building manipulation? "
    "Do you see consecutive HCS or negation sequences pointing one way? "
    "The four-hour is where institutional bias lives. "
    "A four-hour FU or HCS is a major statement."
),
"ch5_topdown_b": (
    "Step three — one-hour: direction confirmation. "
    "Which side has more lower timeframe manipulation? "
    "You are now counting FU formations, HCS clusters, negation sequences. "
    "The side with more concentrated manipulation pointing toward it "
    "is the direction price is headed. "
    "This is how you resolve direction — not by gut, not by news — "
    "by counting the manipulation. "
    "Step four — thirty-minute to fifteen-minute: the entry zone. "
    "Identify your manipulation zone — your point of interest. "
    "Orderblock plus FU plus manipulation sign with internal liquidity. "
    "This is where you will enter. You are not entering yet. You are waiting. "
    "Step five — five-minute and one-minute: the trigger. "
    "Entry model within the point of interest, within the True Stop region, "
    "backed by a ten-minute or higher HCS or negation. "
    "When you see it — that is the trade."
),
"ch5_chart_topdown": (
    "This chart tells the full story in sequence. "
    "The four-hour structure. The Attempted FU. The liquidity being swept. "
    "The five-hundred pip move that followed. "
    "Someone who read the weekly and daily first knew this was coming "
    "long before the one-minute trigger fired. "
    "The move was obvious — at the right timeframe, with the right eyes. "
    "That is what you are building."
),
"ch5_doji_dual": (
    "A doji has two possible identities depending on its context. "
    "It will be targeted quickly if it is NOT at a zone or manipulation zone. "
    "Sitting alone in open space — it will be taken. Banks will hunt it relatively quickly. "
    "It can hold — for sessions or even days — "
    "if it started a significant move AND is sitting at an orderblock or manipulation zone. "
    "The doji that launched a major move, resting against a zone from its origin — this can hold. "
    "When strong HCS or FU forms after major liquidity is established — "
    "that confirms the doji will hold until the opposite Last Area of Liquidity is met. "
    "Before you mark a doji as a target to be taken — check whether it is sitting at a zone. "
    "If it is — do not blindly target it. Read the fuller context first."
),
"ch5_9step": (
    "Before any trade — this is the chronological sequence of confirmations you walk through. "
    "Not all nine may align perfectly — but the more that do, the higher the probability. "
    "One: you are trading within the correct session timing window. "
    "Two: zones are drawn — daily and four-hour bias established. "
    "Three: the first FU of the HCS has formed after X3 manipulation. "
    "Four: a major liquidity target exists on the other side of your intended direction. "
    "Five: timeframe strength confirmed — direction backed by higher timeframe. "
    "Six: lower timeframe story aligning — one to fifteen minute liquidity same direction. "
    "Seven: last areas of major liquidity calculated in both directions. "
    "Eight: final bias formed — the essence of all above into one directional conclusion. "
    "Nine: entry found within a point of interest — True Stop region — "
    "with ten-minute or higher HCS or negation as trigger. "
    "One through nine. Every time."
),
"ch5_domino": (
    "To show what deep multi-timeframe confluence looks like in practice — "
    "here is a real confirmation stack documented on a live trade. "
    "Four-hour doji present. "
    "Four-hour Attempted FU retest confirming. "
    "One-hour Attempted FU retest adding weight. "
    "Thirty-minute doji taken. "
    "Thirty-minute FU forming. "
    "Fifteen-minute Attempted FU retest. "
    "Five-minute FU retest. "
    "Seven layers of confirmation. Top-down. All pointing the same direction. "
    "When you have this depth of agreement — you trade with full size, full conviction. "
    "When you have two or three layers — you trade smaller. "
    "When you have one — you wait."
),

# CHAPTER 6 ────────────────────────────────────────────────────────────────────
"ch6_intro": (
    "Everything up to this point has been vocabulary and grammar. "
    "This chapter is how you speak the language in real time. Every day. In every session. "
    "The four-step closed loop system is not a strategy. "
    "It is the container that holds the strategy. "
    "Every FU, every HCS, every zone, every negation — "
    "they are all feeding into these four steps. "
    "If you are not inside the loop — you are not in a trade. "
    "There are no exceptions."
),
"ch6_tiers": (
    "Before the four steps — understand the timeframe tiers. "
    "Each step operates on a specific tier. "
    "Tier one — swing: four-day to three-hour. This is macro context. The landscape. "
    "Tier two — intraday: three-hour to thirty-minute. Steps one and two live here. "
    "Tier three — scalp: thirty-minute to seven-minute. Step three lives here. "
    "Tier four — lower timeframe entry: seven-minute to one-minute. Step four. The trigger. "
    "Always working top-down through these tiers. You never skip one. "
    "You never use a Tier four observation to justify an entry without Tier two and three alignment. "
    "The hierarchy is the rule."
),
"ch6_step1": (
    "Step one — intraday major liquidity taken plus target. "
    "The question: "
    "Has intraday major liquidity been swept on one side? "
    "AND — is there a clear major liquidity target on the other side? "
    "Both must be true. Both. "
    "You need the sweep because it tells you the banks have filled their orders on that side. "
    "The hunt is complete. They are ready to move in the other direction. "
    "Without the sweep — you do not know the banks have finished. "
    "You are entering before the job is done. "
    "You need the target because you need to know where price is going. "
    "A trade without a target is not a trade — it is a hope. "
    "Mark the target before you enter. "
    "You cannot proceed to Step two without Step one confirmed."
),
"ch6_step2": (
    "Step two — price in intraday manipulation zone. "
    "The question: is price currently inside a confirmed intraday manipulation zone? "
    "Formula: orderblock plus FU plus manipulation sign plus internal liquidity. "
    "Valid for twenty-four hours. If the zone is older — refresh or discard. "
    "This step confirms location. Step one was the story. Step two is the address. "
    "You are not reacting to random price movement in open space. "
    "You are reacting to price reaching a specific, pre-planned zone "
    "where you know institutional activity has occurred. "
    "Intentional, prepared, calm. Not reactive."
),
"ch6_step3": (
    "Step three — intraday entry model plus scalp True Stop entry model. "
    "The question: "
    "Has an intraday entry model formed? "
    "AND — has the scalp-level True Stop Entry Model confirmed? "
    "Ten-minute or higher HCS or negation minimum. "
    "The intraday structure has set the stage. "
    "Now you drop to the scalp timeframe — thirty-minute to seven-minute — "
    "and you wait for the manipulation confirmation. "
    "No HCS or negation at this level — no trade. "
    "It does not matter how perfect Steps one and two were. "
    "If Step three does not confirm — you wait. The loop is not complete. "
    "When Step three confirms, you mark the scalp True Stop level."
),
"ch6_step4": (
    "Step four — lower timeframe entry model inside the scalp True Stop region. "
    "The question: "
    "Has a lower timeframe entry model formed INSIDE the scalp True Stop region? "
    "This is the trigger. This is the moment you actually enter. "
    "Your entry timeframe is one-minute to seven-minute. "
    "You are watching for an HCS or negation forming within the scalp True Stop area. "
    "When it appears — this is the Phase three moment. "
    "Price is completing its manipulation cycle and returning to the original cluster level. "
    "This is your entry. "
    "Stop loss: behind the first FU of the HCS, at the True Stop. Tight. Precise. "
    "Take profit: the major liquidity target from Step one. "
    "Pre-planned. Pre-marked. No guessing in the moment."
),
"ch6_loop": (
    "The loop in plain language. "
    "Step one: HTF liquidity swept plus target on the other side. "
    "Step two: price inside the intraday manipulation zone. "
    "Step three: ten-minute or higher HCS or negation confirmed — scalp True Stop established. "
    "Step four: one to seven minute entry model fires inside the scalp True Stop region. "
    "Enter. Manage. Extract. "
    "Every session, every trade, every day — this is the sequence. "
    "Any step unconfirmed — do not advance. Wait. "
    "The market gives this setup regularly. "
    "There is no reason to force an incomplete loop."
),

# CHAPTER 7 ────────────────────────────────────────────────────────────────────
"ch7_intro": (
    "The method works at any time. "
    "But it does not work equally at any time. "
    "There are specific windows when manipulation is highest, "
    "when institutional activity is at its peak, "
    "when the risk-to-reward available is greatest. "
    "You do not need to trade all day. "
    "You need to be present and prepared for the right hours. "
    "Most consistent traders work two to four hours maximum per day. "
    "The discipline is not staying at the chart — "
    "it is knowing when to be there and when to step away."
),
"ch7_sessions_a": (
    "Priority one — eight to nine AM Eastern Standard Time: the Golden Hour. "
    "The New York open. Every single day — without exception — "
    "this hour produces high risk-to-reward entry potential. "
    "The majority of swing positions are found here. "
    "Average opportunity: one hundred pips over two positions within this single hour. "
    "This is the most important trading hour in existence for this method. "
    "Do not miss it. Be prepared before it opens. "
    "Priority two — ten to eleven AM Eastern Standard Time. "
    "After the nine to ten cooling period, a new four-hour candle forms. "
    "High manipulation potential. "
    "Often determines whether the New York morning move continues or reverses. "
    "Second most important intraday window."
),
"ch7_sessions_b": (
    "Priority three — two to four AM Eastern Standard Time: London open. "
    "Two hours. Not as powerful as New York, but assured true entry potential. "
    "Valid for all three entry types. "
    "Priority four — nine to ten PM and eleven PM to midnight Eastern: Asia. "
    "Lesser potential by default. Valid — but expect smaller moves. "
    "Best used for position management or conservative scalps. "
    "Priority five — twelve to one PM and two to three PM Eastern. "
    "Final bias of the day solidifies. Last valid entry windows. "
    "Avoid: three to eight PM, five to eight AM, nine to ten AM unless swing point of interest only. "
    "The rule: refresh your liquidity calculation at the start of every new timing window. "
    "A liquidity map from two hours ago may be partially invalidated. "
    "Always check before the window opens."
),
"ch7_presession": (
    "The pre-session routine. "
    "React to trades in one to two seconds. "
    "That speed is not talent — it is preparation. "
    "Every element of the trade is pre-confirmed before the session opens. "
    "The only decision in real time is whether the loop has completed — "
    "and you are watching for Step four. "
    "Step one: mark all major liquidity targets — weekly down to thirty-minute — before the session. "
    "Step two: identify existing manipulation zones — confirm validity or discard. "
    "Step three: establish intraday bias from closed loop Steps one and two. "
    "Step four: mark potential scalp True Stop levels within your manipulation zones. "
    "Step five: note which session timing window you are in and when the next opens. "
    "Step six: set alerts as confirmation triggers for when price enters your zones. "
    "When the session opens — you are watching. Not analysing. "
    "The analysis is done."
),
"ch7_risk_a": (
    "Your numbers — Funded Next twenty-five thousand dollars. "
    "Risk per trade: zero point five percent equals one hundred and twenty-five dollars. "
    "Daily loss limit: two hundred and fifty dollars — two losing trades. "
    "Weekly loss limit: five hundred dollars. "
    "Sessions per trade: one to three maximum. "
    "Consistency rule: no single day exceeds five hundred dollars profit. "
    "The mathematics of your edge: "
    "one percent risk at one to twenty risk-to-reward equals twenty percent account growth in one trade. "
    "A two hundred dollar account, twenty percent daily for forty days — over two hundred thousand. "
    "This is not fantasy. "
    "This is the mathematical reality of the edge you have access to."
),
"ch7_risk_b": (
    "Trade management. "
    "Move to break-even as fast as possible — especially on funded accounts. "
    "This is the single most important intra-trade discipline. "
    "Take partials at natural liquidity levels. Never let a winner become a loser. "
    "After partials, let the remainder run at break-even. "
    "Home run potential with zero downside. "
    "Session discipline rule: three losses in one session — close the platform. "
    "Not negotiate. Not one more look. Close it. "
    "A losing day must never exceed half of your previous winning day. "
    "Compound momentum is the asset. One bad day cannot erase two good ones. "
    "And the most important rule: "
    "when the daily loss limit hits — close the laptop. "
    "Not after one more look. Immediately. "
    "The session is over."
),

# CHAPTER 8 ────────────────────────────────────────────────────────────────────
"ch8_intro": (
    "The method is learned. The loop is understood. "
    "And here is where most students stall. "
    "Because knowing the method is not mastery. Not even close. "
    "Mastery is when the method is automatic. "
    "When you look at a chart and the liquidity pools announce themselves without conscious effort. "
    "When the HCS forms and you are already calculating whether Steps one and two are satisfied "
    "before your mind has finished forming the question. "
    "When a loss happens and your body does not change — "
    "because you genuinely understand that one trade outcome tells you nothing "
    "about the quality of your analysis across a sample size."
),
"ch8_stages": (
    "There are three stages. "
    "Stage one — confusion. "
    "Everything is new. Individual concepts make sense in isolation "
    "but refuse to connect into a coherent whole. "
    "Charts feel overwhelming. Every candle looks like an FU if you squint. "
    "This is universal. Every student passes through here. "
    "Do not interpret confusion as a sign this is not for you. "
    "It is a sign that you are at the beginning. Nothing more. "
    "Stage two — pattern recognition. "
    "The concepts connect. You begin to see liquidity before it is taken. "
    "You identify setups that subsequently play out correctly. "
    "But here — the dangerous phase. "
    "You can now see enough to act, but not enough to filter. "
    "Most blown accounts happen here. Not from ignorance. "
    "From partial knowledge applied with full confidence. "
    "Stage three — filtration. True mastery. "
    "You see everything Stage two sees — and you also see what not to trade. "
    "The trades you pass on become as important as the trades you take. "
    "Almost is not enough when your account depends on certainty. "
    "You wait."
),
"ch8_mala_a": (
    "Mala — this section is for you directly. "
    "Your strategy is not the issue. It has not been the issue. "
    "What you have is real. The win rate when you follow the method is real. "
    "The risk-to-reward when you follow the method is real. "
    "The issue is a specific pattern that you know about yourself already — "
    "because you have seen it repeat. "
    "And the fact that it repeats is not a character flaw. "
    "It is a documented behavioural cycle. And documented cycles can be broken "
    "when they are named clearly enough. "
    "The pattern: you get funded — or you get close — and then you hit a loss. "
    "Not a catastrophic loss. A normal, expected, within-parameters loss. "
    "But that loss triggers a state change. "
    "Ego activates. The rational mind that passed the challenge goes quiet. "
    "The emotional mind that says I can make it back right now takes over. "
    "One extra trade becomes three. Three becomes five. Account gone. "
    "You are not alone in this. But that does not make it acceptable."
),
"ch8_mala_b": (
    "The solution is not a new system. "
    "It is not a different strategy. "
    "It is one action, taken consistently, at one specific moment. "
    "When the daily loss limit hits — close the laptop. "
    "Not tomorrow's problem. Not after one last check. "
    "The moment that limit is hit. The moment. Laptop closed. "
    "That single action, performed consistently, is the difference "
    "between where you are and where you are capable of being. "
    "Everything else — the technical skill, the method, the closed loop system — you have it. "
    "The one missing piece is that one action. "
    "The backtesting, the preparation, the pre-session work — "
    "it all compounds on that foundation of discipline. "
    "Without it, it does not matter how refined your analysis becomes. "
    "With it — the method does the rest."
),
"ch8_backtesting": (
    "Before this session closes — one more non-negotiable. "
    "Five hundred hours. Minimum. "
    "With stored, documented, verifiable data before going live with size. "
    "This is the threshold at which chart recognition transitions from conscious thought to instinct. "
    "At five hundred hours of proper backtesting — your brain has processed enough repetitions "
    "that patterns announce themselves before you have consciously looked for them. "
    "The correct backtesting state: when your mind begins to strain. "
    "When focused application produces discomfort. "
    "That discomfort is the signal that you are at the edge of your current capacity — "
    "exactly where growth happens. That is where you stay. "
    "Store everything. Printed charts. Annotated screenshots. Written notes. "
    "Pen to paper will always consolidate learning faster than digital notes."
),
"ch8_closing": (
    "You now have the complete picture. "
    "From the confirmed fact that every trader starts non-profitable — "
    "all the way through the four-step closed loop system "
    "that you execute every single session. "
    "The concepts are not separate. They are one system. "
    "Liquidity is the king — the target of every move. "
    "FU, HCS, Negation, and X3 are the language — how you read the move forming. "
    "Timeframe Strength is the law — the hierarchy that resolves every conflict. "
    "Zones and True Stop are the address — where within the liquidity story you position yourself. "
    "The Closed Loop is the framework — the four steps that confirm every trade before it fires. "
    "Session Timing is the edge amplifier — when the loop fires at highest probability. "
    "And the psychology — the willingness to sit with boredom, to accept a small loss, "
    "to close the laptop when the limit is hit — "
    "that is the container that holds all of it together. "
    "You have the floor plan. The building is already there. "
    "Now you walk through it correctly, every day, with full clarity and full control. "
    "Go prepare your charts for tomorrow's session."
),

}

# ── Build ─────────────────────────────────────────────────────────────────────

def build():
    clips = []
    print("\n=== GENERATING AUDIO + BUILDING CLIPS ===")

    def S(tag):
        """Get narration + first line as caption preview."""
        text = SEGMENTS[tag]
        cap = text[:120].rstrip() + "..."
        a = tts(text, tag)
        return a, cap

    # ── OPENING ───────────────────────────────────────────────────────────────
    clips.append(make_title_card("MALA", "A Complete Personal Curriculum — Beginner to Mastery", duration=5))

    a, cap = S("intro_a")
    clips.append(make_text_slide("One-on-One Teaching Session", [
        "Built specifically for you — Mala",
        "From complete beginner to live daily execution",
        "Every concept connected — nothing left loose",
        "The 4-Step Closed Loop System at the end",
    ], a, cap).with_audio(a))

    a, cap = S("intro_b")
    clips.append(make_text_slide("What We Cover", [
        "Ch 1: The Only Confirmed Fact",
        "Ch 2: Liquidity — The Foundation of Every Decision",
        "Ch 3: Candlestick Language (FU · Negation · X3 · HCS)",
        "Ch 4: Structure (TFS · Zones · True Stop)",
        "Ch 5: Reading the Full Story (Top-Down Analysis)",
        "Ch 6: The 4-Step Closed Loop System",
        "Ch 7: Session Timing and Extraction",
        "Ch 8: Mastery and The Mala Factor",
    ], a, cap).with_audio(a))

    # ── CHAPTER 1 ─────────────────────────────────────────────────────────────
    clips.append(make_title_card("CHAPTER 1", "The Only Confirmed Fact", duration=4))
    clips.append(make_quote_card("Every trader starts off non-profitable.", duration=5))

    a, cap = S("ch1_a")
    clips.append(make_text_slide("The Universal Starting Point", [
        "Every single trader — no exceptions",
        "Not 50/50. Statistically zero for the uninformed",
        "The manipulation changes the odds completely",
        "Knowing this is the most liberating truth in trading",
    ], a, cap).with_audio(a))

    a, cap = S("ch1_b")
    clips.append(make_text_slide("Why Zero — Not Fifty Percent", [
        "Banks need a counterparty to fill billion-dollar orders",
        "Retail stop losses = the counterparty",
        "Banks hunt the clusters → fill orders → reverse",
        "Uninformed trader: 0% statistical edge",
        "The manipulation is the mechanism",
    ], a, cap).with_audio(a))

    a, cap = S("ch1_c")
    clips.append(make_text_slide("Our Advantage — The Floor Plan", [
        "Minimum 1:20 Risk-to-Reward",
        "Regular closes at 1:50, 1:100+",
        "Target win rate: 60% minimum",
        "Students achieve 70–90% once internalised",
        "1% risk × 1:20 RR = 20% account growth per trade",
    ], a, cap).with_audio(a))

    # ── CHAPTER 2 ─────────────────────────────────────────────────────────────
    clips.append(make_title_card("CHAPTER 2", "The Language: Liquidity", duration=4))

    a, cap = S("ch2_intro")
    clips.append(make_text_slide("LIQUIDITY — The Foundation of Every Decision", [
        "Definition: any obvious area where retail stop losses cluster",
        "Banks hunt liquidity to fill their institutional orders",
        "Retail stops = bank fuel",
        "Every chart is a story of where liquidity will be taken next",
    ], a, cap).with_audio(a))

    a, cap = S("ch2_type1")
    clips.append(make_text_slide("Liquidity Type 1 — Unmanipulated Doji", [
        "A doji contained within a previous candle's wick",
        "No FU element — pure balance candle",
        "Retail places stops above/below = premium target",
        "KEY: True doji vs ATT FU — most critical distinction",
        "Wick breaks outside previous range = ATT FU, not doji",
    ], a, cap).with_audio(a))

    a, cap = S("ch2_type2")
    clips.append(make_text_slide("Liquidity Type 2 — Perfect Double Top/Bottom", [
        "NOT almost. Perfect — exact same price twice",
        "Verify on BROKER (IC Markets, Forex.com) — not TradingView",
        "0.1 pip apart = major liquidity + premium entry signal",
        "Pip-perfect rejection = sign of manipulation = LOW liquidity",
    ], a, cap).with_audio(a))

    a, cap = S("ch2_type3")
    clips.append(make_text_slide("Liquidity Type 3 — Perfect Trendline", [
        "Minimum 3 perfect rejections — not 2, not almost",
        "2 touches = visible. 3 touches = undeniable = major target",
        "More obvious → more retail orders → more liquidity",
        "2 touches = minor liquidity only. Do not mark as major.",
    ], a, cap).with_audio(a))

    a, cap = S("ch2_types45")
    clips.append(make_text_slide("Liquidity Types 4 & 5 — IMB + Fair Value Gap", [
        "Type 4: Candle opens instantly — NO wick on entry side",
        "Wick exists = manipulation already there = ATT FU",
        "Type 5 (FVG): candles 1 and 3 do not overlap",
        "A blank space in the order book — price always fills it",
        "Use 5min+ only. Verify on BROKER, not TradingView",
    ], a, cap).with_audio(a))

    if os.path.exists(CHART_1):
        a, cap = S("ch2_chart")
        clips.append(make_chart_slide(CHART_1, "XAUUSD 4H — Liquidity Taken + 500 Pip Move", a, cap).with_audio(a))

    if os.path.exists(CHART_2):
        a, cap = S("ch2_daily")
        clips.append(make_chart_slide(CHART_2, "XAUUSD Daily — ATT FU + IMB + Doji Retest", a, cap).with_audio(a))

    a, cap = S("ch2_process")
    clips.append(make_text_slide("The Daily Liquidity Calculation Process", [
        "Step 1: Weekly → mark ALL major liquidity. No bias.",
        "Step 2: Daily → 4H → continue mapping both sides",
        "Step 3: 1H → 30M → count manipulation. Which side more?",
        "Step 4: Know target + direction. WAIT for entry model.",
        "Rule: TP slightly BEFORE the target — never at it",
    ], a, cap).with_audio(a))

    # ── CHAPTER 3 ─────────────────────────────────────────────────────────────
    clips.append(make_title_card("CHAPTER 3", "Candlestick Language", duration=4))
    clips.append(make_title_card("FU · ATT FU · Negation · X3 · HCS", "Phase 3 Entry Model", duration=4))

    a, cap = S("ch3_intro")
    clips.append(make_text_slide("Reading the Manipulation", [
        "5 formations — become fluent, not merely familiar",
        "FU Candle: the most important formation",
        "Attempted FU: minor liquidity, critical distinction",
        "Negation: banks changing direction — tradeable",
        "X3: triple manipulation, strongest signal",
        "HCS: High Confluence Setup — Mr Domino: 'only trade this'",
    ], a, cap).with_audio(a))

    a, cap = S("ch3_fu_a")
    clips.append(make_text_slide("The FU Candle — How Banks Execute", [
        "Does TWO things in ONE candle:",
        "Wick = takes liquidity (hunts stops)",
        "Body = closes strongly in opposite direction",
        "Two requirements: takes liquidity + breaks structure",
        "Stronger close = banks committed = stronger signal",
        "FU wick = Point of Interest. Retest of wick = entry model.",
    ], a, cap).with_audio(a))

    a, cap = S("ch3_fu_b")
    clips.append(make_text_slide("FU Types — Know the Difference", [
        "Strong FU (SFU): full body close after taking liq. Best.",
        "ATT FU: took liq with wick, closed as doji. Minor liquidity.",
        "ATT FU wick broke OUTSIDE previous range",
        "True Doji: contained within previous wick. Major liq target.",
        "3-Candle FU: spread across 3 candles. Same logic.",
    ], a, cap).with_audio(a))

    if os.path.exists(CHART_4):
        a, cap = S("ch3_attfu_chart")
        clips.append(make_chart_slide(CHART_4, "XAUUSD 4H — ATT FU Weak Start + Banks Pressure", a, cap).with_audio(a))

    # NEGATION — full section ──────────────────────────────────────────────────
    a, cap = S("ch3_negation_a")
    clips.append(make_text_slide("FU Negation — Identifying Change", [
        "FU in one direction → next candle FU opposite = NEGATION",
        "First FU's power exhausted. Order flow changes.",
        "Negation wick = Point of Interest. Mark it.",
        "When price returns to that wick = potential entry",
        "In direction of the negation — not the original FU",
    ], a, cap).with_audio(a))

    a, cap = S("ch3_negation_b")
    clips.append(make_text_slide("Negation — Rules and Timeframe Weight", [
        "Counting rule: ATT FU after FU? Give it 2 candles to confirm",
        "1min negation = entry signal on LTF",
        "4H negation = powerful directional signal for the session",
        "Higher TF negation always outweighs LTF FU pointing opposite",
        "This IS timeframe strength in action",
        "Negation = the most overlooked trade in the method",
    ], a, cap).with_audio(a))

    if os.path.exists(CHART_3):
        a, cap = S("ch3_neg_chart")
        clips.append(make_chart_slide(CHART_3, "XAUUSD 4H — ATT FU Weakness + Negation + Buys Ready", a, cap).with_audio(a))

    a, cap = S("ch3_x3")
    clips.append(make_text_slide("X3 — Triple Manipulation. The Strongest Signal.", [
        "A negation that itself gets negated = X3",
        "Phase 1: FU wick in one direction",
        "Phase 2: negation attempt — opposing FU",
        "Phase 3: negation broken — original direction asserts",
        "Pattern: push → counter → counter-counter",
        "Every true move begins with some form of X3",
    ], a, cap).with_audio(a))

    if os.path.exists(CHART_5):
        clips.append(make_title_card("XAUUSD 4H — Full Sequence Building to the Big Move", duration=8))

    a, cap = S("ch3_hcs_a")
    clips.append(make_text_slide("HCS — High Confluence Setup", [
        "FU candle → retested → retest forms FU = HCS",
        "First FU: banks moved. Direction established.",
        "Retest: retail tries to reclaim. Returns to FU wick.",
        "Retest FU: banks defend. Drive price back original direction.",
        "THREE confirmations all pointing same way",
        "HCS doubles the TF strength of its base timeframe",
    ], a, cap).with_audio(a))

    a, cap = S("ch3_hcs_b")
    clips.append(make_text_slide("HCS — Rules, Stop Loss, Zone Validity", [
        "Mr Domino: 'We only trade HCS. Only.'",
        "SL goes under the FIRST FU — not the retest candle",
        "If first FU breaks = entire HCS invalidated",
        "Use HTF HCS for directional bias",
        "Use LTF HCS as entry model trigger",
        "Zone confirmed ONLY when HCS forms INSIDE it",
    ], a, cap).with_audio(a))

    a, cap = S("ch3_phase3")
    clips.append(make_text_slide("The Manipulation Cycle — Phase 3 Entry", [
        "Phase 1: Cluster — retail stops at the level",
        "Phase 2: Sweep — price takes stops, banks fill orders",
        "Phase 3: Return — price returns to original cluster level",
        "Phase 4: True Move — direction established, move begins",
        "ENTER ON PHASE 3 — not after FU closes (Phase 4)",
        "Late to Phase 3 = RR gone. Do NOT enter. Wait.",
    ], a, cap).with_audio(a))

    # ── CHAPTER 4 ─────────────────────────────────────────────────────────────
    clips.append(make_title_card("CHAPTER 4", "The Structure", duration=4))
    clips.append(make_title_card("Timeframe Strength · Zones · True Stop", duration=4))

    a, cap = S("ch4_tfs_a")
    clips.append(make_text_slide("Timeframe Strength — The Law That Ends Confusion", [
        "One rule: higher TF manipulation overpowers lower TF",
        "4H FU pointing down? Need 4H+ FU up to negate it.",
        "1min FU up against 4H FU down = entry signal, NOT reversal",
        "3H+ confirmed FU closure = prevalent direction signal",
        "Below 3H = look for HCS and negation only",
    ], a, cap).with_audio(a))

    a, cap = S("ch4_tfs_b")
    clips.append(make_text_slide("Timeframe Hierarchy for Entries", [
        "Swing: 3H+ confirmed FU closure backing",
        "Intraday: 1H+ HCS or negation alignment",
        "Scalp: 10min+ HCS or negation — THE MINIMUM",
        "No 10min+ HCS/Neg = NO TRADE. Non-negotiable.",
        "30min HCS = 1H FU in strength",
        "1H HCS = 2H FU in strength",
    ], a, cap).with_audio(a))

    a, cap = S("ch4_zones_a")
    clips.append(make_text_slide("Zones — Standard Orderblock", [
        "Zones confirm. Liquidity decides. (Zones are secondary.)",
        "Standard OB: last opposing candle before significant move",
        "Body only — no wicks (unless manipulation in wick)",
        "4H zones = most powerful, hold long-term",
        "1H zones = sharp intraday rejections",
        "30min minimum for a valid zone",
    ], a, cap).with_audio(a))

    a, cap = S("ch4_zones_b")
    clips.append(make_text_slide("Zones — Manipulation Zone (Advanced)", [
        "Formula: OB + FU + manipulation sign + internal liquidity",
        "Internal liquidity = stops sitting inside the zone itself",
        "Valid for 24 hours only — 3 sessions max. Then discard.",
        "1H zone → refine to 15min only. 15min → 5min only.",
        "Strongest: Weekly + Daily + 4H zones overlapping",
        "Zone valid ONLY when HCS forms inside it",
    ], a, cap).with_audio(a))

    if os.path.exists(CHART_2):
        a, cap = S("ch4_zones_chart")
        clips.append(make_chart_slide(CHART_2, "XAUUSD Daily — Zone + ATT FU + IMB Working Together", a, cap).with_audio(a))

    a, cap = S("ch4_true_stop")
    clips.append(make_text_slide("The True Stop Loss — Structural Anchor", [
        "Most concentrated area of manipulation at a key level",
        "Both buys and sells occur without the level breaking",
        "True Stop breaks = banks targeting liquidity beyond it",
        "Not a loss — it is information about where price goes next",
        "4 levels at HTF doji: Low → 50% body → High → 50% wick",
        "Level 4 breaks = zone invalid. No longer interested.",
    ], a, cap).with_audio(a))

    # ── CHAPTER 5 ─────────────────────────────────────────────────────────────
    clips.append(make_title_card("CHAPTER 5", "Reading the Full Story", duration=4))

    a, cap = S("ch5_intro")
    clips.append(make_text_slide("The Top-Down Analysis — Connecting Everything", [
        "Individual concepts = vocabulary",
        "Top-down analysis = grammar",
        "Stop seeing isolated candles. Read the full narrative.",
        "Professionals start at Weekly and work DOWN",
        "By the time you reach 1min — you already know the answer",
    ], a, cap).with_audio(a))

    a, cap = S("ch5_topdown_a")
    clips.append(make_text_slide("Top-Down: Weekly → Daily → 4H", [
        "Step 1 — Weekly/Daily: no bias. Map the terrain.",
        "Mark ALL major liq both sides: dojis, DT/DB, trendlines, IMB",
        "These are macro targets. All intraday serves these.",
        "Step 2 — 4H: institutional zones and bias",
        "Where has manipulation been building?",
        "4H FU or HCS = a major institutional statement",
    ], a, cap).with_audio(a))

    a, cap = S("ch5_topdown_b")
    clips.append(make_text_slide("Top-Down: 1H → 15M → 5M → 1M", [
        "Step 3 — 1H: direction confirmation",
        "Count FU formations and HCS/negation clusters on each side",
        "More concentrated manipulation = direction price is heading",
        "Step 4 — 30M/15M: identify manipulation zone (POI)",
        "OB + FU + manipulation sign + internal liquidity",
        "Step 5 — 5M/1M: wait for entry model within POI + True Stop",
    ], a, cap).with_audio(a))

    if os.path.exists(CHART_1):
        a, cap = S("ch5_chart_topdown")
        clips.append(make_chart_slide(CHART_1, "XAUUSD 4H — Top-Down Story: The Full Sequence", a, cap).with_audio(a))

    a, cap = S("ch5_doji_dual")
    clips.append(make_text_slide("The Doji — Dual Identity", [
        "Will be TAKEN quickly if: not at a zone, open space",
        "Can HOLD for days if: launched major move + at zone",
        "The zone underneath = the reason it holds",
        "Before targeting a doji — check if it is at an OB or MZ",
        "HCS forming after major liq = doji will hold until opp LAL",
    ], a, cap).with_audio(a))

    a, cap = S("ch5_9step")
    clips.append(make_text_slide("The 9-Step Confirmation List", [
        "1. Correct session timing window",
        "2. Zones drawn — daily + 4H bias established",
        "3. First FU of HCS formed after X3 manipulation",
        "4. Major liq target exists on the other side",
        "5. Timeframe strength confirmed — HTF backing",
        "6. LTF story aligning — 1M–15M liq same direction",
        "7. Last areas of major liq calculated both sides",
        "8. Final bias formed — one directional conclusion",
        "9. Entry in POI — True Stop — 10min+ HCS/neg trigger",
    ], a, cap).with_audio(a))

    a, cap = S("ch5_domino")
    clips.append(make_text_slide("Mr Domino's Confirmation Stack", [
        "4H doji present",
        "4H ATT FU retest confirming",
        "1H ATT FU retest adding weight",
        "30M doji taken — 30M FU forming",
        "15M ATT FU retest",
        "5M FU retest",
        "7 layers. All pointing same direction.",
        "More layers = more size. Fewer = smaller. 1 = wait.",
    ], a, cap).with_audio(a))

    # ── CHAPTER 6 ─────────────────────────────────────────────────────────────
    clips.append(make_title_card("CHAPTER 6", "Daily Execution: The Closed Loop System", duration=4))
    clips.append(make_quote_card(
        "The loop is not the strategy. It is the container that holds the strategy.",
        duration=5
    ))

    a, cap = S("ch6_intro")
    clips.append(make_text_slide("The 4-Step Closed Loop System", [
        "Chapters 1–5 = vocabulary and grammar",
        "This chapter = speaking the language in real time",
        "Every FU, HCS, zone, negation feeds into these 4 steps",
        "Not inside the loop = not in a trade",
        "There are no exceptions",
    ], a, cap).with_audio(a))

    a, cap = S("ch6_tiers")
    clips.append(make_text_slide("The 4-Tier Timeframe Structure", [
        "Tier 1 — SWING: 4D to 3H (macro context, landscape)",
        "Tier 2 — INTRADAY: 3H to 30M (Steps 1 and 2)",
        "Tier 3 — SCALP: 30M to 7M (Step 3)",
        "Tier 4 — LTF ENTRY: 7M to 1M (Step 4 — the trigger)",
        "Always top-down. Never skip a tier.",
    ], a, cap).with_audio(a))

    a, cap = S("ch6_step1")
    clips.append(make_text_slide("STEP 1 — HTF Liquidity Swept + Target", [
        "Q: Has intraday major liq been swept?",
        "Q: Is there a clear major liq target on the other side?",
        "BOTH must be true. Both.",
        "Sweep = banks finished filling. Ready to move opposite.",
        "No sweep = do not know banks are done. Do not enter.",
        "Target = where price is going. Mark it BEFORE entering.",
    ], a, cap).with_audio(a))

    a, cap = S("ch6_step2")
    clips.append(make_text_slide("STEP 2 — Price in Intraday Manipulation Zone", [
        "Q: Is price inside a confirmed intraday manipulation zone?",
        "Formula: OB + FU + manipulation sign + internal liquidity",
        "Valid for 24hrs only. Older zone = discard or refresh.",
        "Step 1 = the story. Step 2 = the address.",
        "Pre-planned, pre-marked, calm — not reactive",
    ], a, cap).with_audio(a))

    a, cap = S("ch6_step3")
    clips.append(make_text_slide("STEP 3 — Intraday EM + Scalp TSL EM", [
        "Q: Has intraday entry model formed?",
        "Q: Has scalp True Stop EM confirmed?",
        "Minimum: 10min or higher HCS or negation",
        "No HCS/neg at this level = NO TRADE. Period.",
        "Perfect Steps 1 and 2 don't matter if Step 3 fails.",
        "When confirmed: mark the scalp True Stop level.",
    ], a, cap).with_audio(a))

    a, cap = S("ch6_step4")
    clips.append(make_text_slide("STEP 4 — LTF Entry Model Inside Scalp TSL", [
        "Q: Has LTF entry model formed INSIDE scalp TSL region?",
        "Entry timeframe: 1M to 7M",
        "Wait for HCS or negation inside the scalp True Stop area",
        "This is the Phase 3 moment — enter as FU is forming",
        "SL: behind FIRST FU of HCS, at the True Stop. Tight.",
        "TP: the major liq target from Step 1. Pre-planned.",
    ], a, cap).with_audio(a))

    a, cap = S("ch6_loop")
    clips.append(make_text_slide("The Loop — Plain Language", [
        "Step 1: HTF liq swept + target on the other side",
        "Step 2: Price inside intraday manipulation zone",
        "Step 3: 10min+ HCS/neg confirmed — scalp TSL established",
        "Step 4: 1–7min entry model fires inside scalp TSL region",
        "",
        "ENTER.   MANAGE.   EXTRACT.",
        "",
        "Any step unconfirmed = wait. Never force the loop.",
    ], a, cap).with_audio(a))

    # ── CHAPTER 7 ─────────────────────────────────────────────────────────────
    clips.append(make_title_card("CHAPTER 7", "Session Timing and Extraction", duration=4))

    a, cap = S("ch7_intro")
    clips.append(make_text_slide("When the Loop Fires Best", [
        "The method works at any time — but NOT equally",
        "Specific windows: highest manipulation, best RR",
        "You do not need to trade all day",
        "Most consistent traders: 2–4 hours maximum daily",
        "Know when to be there. Know when to step away.",
    ], a, cap).with_audio(a))

    a, cap = S("ch7_sessions_a")
    clips.append(make_text_slide("Priority Session Windows (EST)", [
        "Priority 1: 8–9 AM EST — THE GOLDEN HOUR (NY Open)",
        "Every day. Without exception. Highest RR potential.",
        "Average: 100 pips over 2 positions in this single hour.",
        "Do not miss it. Be prepared BEFORE it opens.",
        "Priority 2: 10–11 AM EST",
        "New 4H candle forms. NY continuation or reversal.",
    ], a, cap).with_audio(a))

    a, cap = S("ch7_sessions_b")
    clips.append(make_text_slide("All Session Windows (EST)", [
        "Priority 3: 2–4 AM — London Open. Valid all 3 entry types.",
        "Priority 4: 9–10 PM + 11 PM–12 AM — Asia. Smaller moves.",
        "Priority 5: 12–1 PM + 2–3 PM — Final daily bias.",
        "AVOID: 3–8 PM, 5–8 AM, 9–10 AM (swing POI exception only)",
        "Rule: refresh liq calc at start of every timing window",
    ], a, cap).with_audio(a))

    a, cap = S("ch7_presession")
    clips.append(make_text_slide("Pre-Session Preparation Routine", [
        "React in 1–2 seconds. Speed = preparation, not talent.",
        "1. Mark all major liq Weekly → 30M before session",
        "2. ID manipulation zones — confirm validity or discard",
        "3. Establish intraday bias (Loop Steps 1 and 2)",
        "4. Mark potential scalp TSL levels inside zones",
        "5. Note which session window + when next opens",
        "6. Set alerts as confirmation triggers for your zones",
        "When session opens: WATCH. Not analyse. Analysis is done.",
    ], a, cap).with_audio(a))

    a, cap = S("ch7_risk_a")
    clips.append(make_text_slide("Your Numbers — Funded Next $25K", [
        "Risk per trade: 0.5% = $125",
        "Daily loss limit: $250 (2 losing trades)",
        "Weekly loss limit: $500",
        "Sessions per trade: 1–3 maximum",
        "Consistency rule: no single day exceeds $500 profit",
        "Mathematics: 1% × 1:20 RR = 20% account growth per trade",
    ], a, cap).with_audio(a))

    a, cap = S("ch7_risk_b")
    clips.append(make_text_slide("Trade Management + Session Discipline", [
        "Move to break-even FAST — especially on funded accounts",
        "Take partials at natural liq levels. Never let winner → loser.",
        "After partials: let remainder run at break-even",
        "3 losses in one session = close the platform. Not negotiate.",
        "Losing day must not exceed half of previous winning day",
        "DAILY LOSS LIMIT HIT = CLOSE THE LAPTOP. Immediately.",
    ], a, cap).with_audio(a))

    # ── CHAPTER 8 ─────────────────────────────────────────────────────────────
    clips.append(make_title_card("CHAPTER 8", "Mastery and The Mala Factor", duration=4))

    a, cap = S("ch8_intro")
    clips.append(make_text_slide("Where the Method Ends and the Trader Begins", [
        "Knowing the method is NOT mastery",
        "Mastery = the method is automatic",
        "Liquidity pools announce without conscious effort",
        "HCS forms: you are calculating before you consciously look",
        "A loss happens: your body does not change",
    ], a, cap).with_audio(a))

    a, cap = S("ch8_stages")
    clips.append(make_text_slide("The Three Stages of Mastery", [
        "Stage 1 — CONFUSION: concepts won't connect. Universal.",
        "Confusion is not 'this is not for me' — it is 'I am beginning'",
        "Stage 2 — PATTERN RECOGNITION: the dangerous phase",
        "Can see enough to act — not enough to FILTER",
        "Most blown accounts: partial knowledge + full confidence",
        "Stage 3 — FILTRATION: true mastery",
        "Trades you PASS ON = as important as trades you take",
        "Almost-textbook is NOT textbook. You wait.",
    ], a, cap).with_audio(a))

    a, cap = S("ch8_mala_a")
    clips.append(make_text_slide("The Mala Factor — Named Directly", [
        "Your strategy is not the issue. It has not been the issue.",
        "Win rate when you follow the method — real.",
        "The issue: a specific repeating behavioural cycle",
        "Get funded → normal loss → state change → ego activates",
        "Rational mind goes quiet. Emotional mind: 'make it back now'",
        "One extra trade → three → five → account gone",
    ], a, cap).with_audio(a))

    a, cap = S("ch8_mala_b")
    clips.append(make_text_slide("The One Fix", [
        "Not a new system. Not a different strategy.",
        "One action at one specific moment:",
        "",
        "DAILY LOSS LIMIT HIT = CLOSE THE LAPTOP.",
        "",
        "The moment that limit is hit. Laptop closed.",
        "This single action = the difference.",
        "You have everything else. This is the one missing piece.",
    ], a, cap).with_audio(a))

    a, cap = S("ch8_backtesting")
    clips.append(make_text_slide("The Backtesting Standard — 500 Hours", [
        "500 hours minimum with documented, verifiable data",
        "Threshold: pattern recognition → instinct",
        "At 500 hours: patterns announce before you consciously look",
        "Correct state: mind straining = you are at the right edge",
        "Discomfort during backtesting = growth happening",
        "Store everything: printed charts, screenshots, written notes",
        "Pen to paper consolidates faster than digital",
    ], a, cap).with_audio(a))

    a, cap = S("ch8_closing")
    clips.append(make_text_slide("The Complete Picture", [
        "Liquidity = the king. Target of every move.",
        "FU · HCS · Negation · X3 = the language.",
        "Timeframe Strength = the law. Resolves every conflict.",
        "Zones + True Stop = the address.",
        "The Closed Loop = the framework. 4 steps every trade.",
        "Session Timing = edge amplifier.",
        "Psychology = the container that holds all of it together.",
    ], a, cap).with_audio(a))

    # ── CLOSING ───────────────────────────────────────────────────────────────
    clips.append(make_quote_card(
        "You have the floor plan. The building is already there. "
        "Walk through it correctly, every day, with full clarity and full control.",
        duration=8
    ))
    clips.append(make_title_card(
        "GO PREPARE YOUR CHARTS",
        "Tomorrow's session starts with tonight's preparation.",
        duration=6
    ))
    clips.append(make_quote_card(
        "Success is no accident. It is hard work, perseverance, learning, studying, "
        "sacrifice, and most of all, love of what you are doing.",
        "Pele",
        duration=7
    ))

    # ── RENDER ────────────────────────────────────────────────────────────────
    print("\n=== RENDERING VIDEO ===")
    final = concatenate_videoclips(clips, method="compose")
    print(f"  Total duration: {final.duration:.1f}s ({final.duration/60:.1f} min)")
    print(f"  Writing to: {OUT_FILE}")
    final.write_videofile(
        OUT_FILE,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger="bar"
    )

    # ── WRITE SRT ─────────────────────────────────────────────────────────────
    print("\n=== WRITING SUBTITLES ===")
    write_srt()
    print(f"\nDone -> {OUT_FILE}")
    print(f"Subtitles -> {SRT_FILE}")
    print("Open in VLC — subtitles load automatically from the SRT file.")

if __name__ == "__main__":
    build()
