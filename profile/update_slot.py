import hashlib
import os
import random
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


PROFILE_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_COUNT = 23236
DEFAULT_BASE_DATE = date(2026, 8, 12)
DEFAULT_TIMEZONE = "Europe/Berlin"
COUNTER_SEED = "tenbyte-glitch-counter-v1"


def daily_commit_minutes(day):
    """Return deterministic, randomly distributed commit minutes for one day."""
    digest = hashlib.sha256(f"{COUNTER_SEED}:{day.isoformat()}".encode()).digest()
    generator = random.Random(int.from_bytes(digest, "big"))
    daily_total = generator.randint(5, 50)
    return sorted(generator.sample(range(24 * 60), daily_total))


def synthetic_commit_count(now=None, base_count=None, base_date=None):
    timezone = ZoneInfo(os.environ.get("COUNTER_TIMEZONE", DEFAULT_TIMEZONE))
    if now is None:
        now = datetime.now(timezone)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone)
    else:
        now = now.astimezone(timezone)

    if base_count is None:
        base_count = int(os.environ.get("COUNTER_BASE_COUNT", DEFAULT_BASE_COUNT))
    if base_date is None:
        base_date = date.fromisoformat(
            os.environ.get("COUNTER_BASE_DATE", DEFAULT_BASE_DATE.isoformat())
        )

    if now.date() < base_date:
        return base_count

    total = base_count
    day = base_date
    while day < now.date():
        total += len(daily_commit_minutes(day))
        day += timedelta(days=1)

    current_minute = now.hour * 60 + now.minute
    total += sum(minute <= current_minute for minute in daily_commit_minutes(now.date()))
    return total


def generate_sequence(target_digit, spins):
    return list(range(10)) * spins + list(range(target_digit + 1))


def format_slot_count(commit_count):
    digits = f"{commit_count:06d}"
    groups = []
    while digits:
        groups.append(digits[-3:])
        digits = digits[:-3]
    return ",".join(reversed(groups))


def generate_counter_svg(commit_count):
    display_count = format_slot_count(commit_count)
    digit_count = sum(character.isdigit() for character in display_count)
    comma_count = display_count.count(",")
    compact = digit_count >= 6
    digit_spacing = 17 if compact else 20
    comma_spacing = 8 if compact else 10
    font_size = 24 if compact else 28
    right_edge = 190 if compact else 185
    x = right_edge - (digit_count - 1) * digit_spacing - comma_count * comma_spacing
    rolling_columns = []
    animations = []
    digit_index = 0

    for character in display_count:
        if character == ",":
            rolling_columns.append(f'<text x="{x - 2}" y="54">,</text>')
            x += comma_spacing
            continue

        sequence = generate_sequence(int(character), min(digit_index + 1, 5))
        texts = "".join(
            f'<text y="{index * 30}">{digit}</text>'
            for index, digit in enumerate(sequence)
        )
        end_y = -(len(sequence) - 1) * 30
        class_name = f"roll-{digit_index}"
        duration = 1.5 + digit_index * 0.5
        animations.append(
            f".{class_name} {{ animation: {class_name} {duration:.2f}s "
            "cubic-bezier(0.2, 0.8, 0.2, 1) 1.2s forwards; }\n"
            f"@keyframes {class_name} {{ 0% {{ transform: translateY(0); }} "
            f"100% {{ transform: translateY({end_y}px); }} }}"
        )
        rolling_columns.append(
            f'<g transform="translate({x}, 54)"><g class="{class_name}">{texts}</g></g>'
        )
        digit_index += 1
        x += digit_spacing

    animation_css = "\n".join(animations)
    columns = "\n      ".join(rolling_columns)

    return f"""<svg width="250" height="70" viewBox="0 0 250 70" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .digit-col {{ font-family: "Courier New", Courier, monospace; font-size: {font_size}px; fill: #00d2ff; font-weight: 900; filter: drop-shadow(0 0 4px rgba(0, 210, 255, 0.5)); }}
      .label {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; font-weight: 700; fill: #8892b0; letter-spacing: 1.5px; }}
      .arm {{ transform-origin: 220px 45px; animation: pull 1s ease-in-out forwards; }}
      @keyframes pull {{ 0% {{ transform: rotate(0deg); }} 50% {{ transform: rotate(100deg); }} 100% {{ transform: rotate(0deg); }} }}
      {animation_css}
    </style>
    <clipPath id="digit-mask"><rect x="70" y="27" width="140" height="35" /></clipPath>
    <linearGradient id="boxBg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0a1128" /><stop offset="100%" stop-color="#050505" />
    </linearGradient>
  </defs>
  <g class="arm"><rect x="220" y="10" width="6" height="35" fill="#8892b0" rx="3" /><circle cx="223" cy="10" r="8" fill="#ff007a" /></g>
  <rect x="218" y="40" width="10" height="15" fill="#444a5e" rx="2" />
  <rect x="0" y="20" width="220" height="50" fill="url(#boxBg)" rx="8" stroke="#1d2847" stroke-width="2" />
  <text x="15" y="51" class="label">COMMITS</text>
  <g clip-path="url(#digit-mask)"><g class="digit-col">
      {columns}
  </g></g>
</svg>"""


def generate_jackpot_svg():
    return """<svg width="250" height="70" viewBox="0 0 250 70" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; font-weight: 700; fill: #8892b0; letter-spacing: 1.5px; }
      .arm { transform-origin: 220px 45px; animation: pull 1s ease-in-out forwards; }
      @keyframes pull { 0% { transform: rotate(0deg); } 50% { transform: rotate(100deg); } 100% { transform: rotate(0deg); } }
      .coin { animation: dropIn 1s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; opacity: 0; }
      .coin-1 { animation-delay: 1.2s; } .coin-2 { animation-delay: 1.7s; } .coin-3 { animation-delay: 2.2s; }
      @keyframes dropIn { 0% { transform: translateY(-50px); opacity: 0; } 50% { opacity: 1; } 100% { transform: translateY(0); opacity: 1; } }
      .glow { animation: coinGlow 1.5s infinite alternate; }
      @keyframes coinGlow { 0% { filter: drop-shadow(0 0 5px rgba(255, 215, 0, 0.5)); } 100% { filter: drop-shadow(0 0 15px rgba(255, 215, 0, 1)); } }
    </style>
    <clipPath id="mask"><rect x="0" y="20" width="220" height="50" rx="8" /></clipPath>
    <linearGradient id="boxBg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#0a1128" /><stop offset="100%" stop-color="#050505" /></linearGradient>
    <linearGradient id="gold" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#FFDF00" /><stop offset="100%" stop-color="#D4AF37" /></linearGradient>
  </defs>
  <g class="arm"><rect x="220" y="10" width="6" height="35" fill="#8892b0" rx="3" /><circle cx="223" cy="10" r="8" fill="#ff007a" /></g>
  <rect x="218" y="40" width="10" height="15" fill="#444a5e" rx="2" />
  <rect x="0" y="20" width="220" height="50" fill="url(#boxBg)" rx="8" stroke="#1d2847" stroke-width="2" />
  <text x="15" y="51" class="label">JACKPOT</text>
  <g clip-path="url(#mask)"><g class="glow">
    <g transform="translate(105, 45)"><g class="coin coin-1"><circle r="15" fill="url(#gold)" stroke="#B8860B" stroke-width="2" /><text y="5" font-family="sans-serif" font-size="16" font-weight="bold" fill="#B8860B" text-anchor="middle">$</text></g></g>
    <g transform="translate(150, 45)"><g class="coin coin-2"><circle r="15" fill="url(#gold)" stroke="#B8860B" stroke-width="2" /><text y="5" font-family="sans-serif" font-size="16" font-weight="bold" fill="#B8860B" text-anchor="middle">$</text></g></g>
    <g transform="translate(195, 45)"><g class="coin coin-3"><circle r="15" fill="url(#gold)" stroke="#B8860B" stroke-width="2" /><text y="5" font-family="sans-serif" font-size="16" font-weight="bold" fill="#B8860B" text-anchor="middle">$</text></g></g>
  </g></g>
</svg>"""


def jackpot_selected():
    chance = float(os.environ.get("JACKPOT_CHANCE", "0.03"))
    if not 0 <= chance <= 0.05:
        raise RuntimeError("JACKPOT_CHANCE must be between 0 and 0.05.")
    return random.SystemRandom().random() < chance


def update_profile(commit_count, is_jackpot=None):
    svg_path = PROFILE_DIR / "animated-slot-counter.svg"
    readme_path = PROFILE_DIR / "README.md"
    if is_jackpot is None:
        is_jackpot = jackpot_selected()
    counter_svg = generate_jackpot_svg() if is_jackpot else generate_counter_svg(commit_count)

    old_svg = svg_path.read_text(encoding="utf-8") if svg_path.exists() else ""
    if old_svg == counter_svg:
        print(f"Profile unchanged at {commit_count} commits.")
        return False

    svg_path.write_text(counter_svg, encoding="utf-8")
    cache_key = hashlib.sha256(counter_svg.encode()).hexdigest()[:12]
    readme = readme_path.read_text(encoding="utf-8")
    readme = re.sub(
        r"animated-slot-counter\.svg(?:\?v=[A-Za-z0-9_-]+)?",
        f"animated-slot-counter.svg?v={cache_key}",
        readme,
    )
    readme_path.write_text(readme, encoding="utf-8")
    state = "jackpot" if is_jackpot else f"{commit_count} commits"
    print(f"Updated profile with {state}.")
    return True


def main():
    update_profile(synthetic_commit_count())


if __name__ == "__main__":
    main()
