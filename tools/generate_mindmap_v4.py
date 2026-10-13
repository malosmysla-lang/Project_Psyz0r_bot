#!/usr/bin/env python3
"""Generate Psyz0r_bot mind-map v4 artifacts from the approved Markdown registry."""

from __future__ import annotations

import html
import math
import re
import textwrap
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "MINDMAP_V4_CONTENT_RECONCILIATION_RU.md"
OUT = ROOT / "docs" / "mindmap_v4"

COLORS = [
    "#74D8FF", "#FFD76A", "#C89BFF", "#FF929D", "#8FE596",
    "#F4E7A2", "#79E1D1", "#FFB06A", "#8CB7FF", "#E58DE3",
    "#A9E26F", "#FF7F73", "#6FD3A4", "#D1A2FF", "#F1BE78",
]
STATUS_COLORS = {
    "LIVE": "#59D98E", "PARTIAL": "#F7C65B", "LOCAL": "#79B8FF",
    "SPEC": "#D0D6E2", "DATA": "#B494F5", "PAUSED": "#8993A5",
    "CONFLICT": "#FF6B72",
}


def parse() -> tuple[str, list[dict], list[str]]:
    raw = SOURCE.read_text(encoding="utf-8")
    center_match = re.search(r"## Центр карты\s+\n\*\*(.+?)\*\*", raw, re.S)
    center = re.sub(r"\s+", " ", center_match.group(1)).strip() if center_match else "Psyz0r_bot"
    branch_re = re.compile(r"^## ([A-O])\. (.+)$", re.M)
    matches = list(branch_re.finditer(raw))
    branches = []
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw)
        block = raw[match.end():end]
        items = []
        for line in block.splitlines():
            line = line.strip()
            if not line.startswith("- `"):
                continue
            m = re.match(r"- `([^`]+)`\s+(.+)", line)
            if not m:
                continue
            tag, text = m.groups()
            parts = tag.split()
            item_id = parts[0]
            statuses = "/".join(parts[1:]) if len(parts) > 1 else "SPEC"
            items.append({"id": item_id, "status": statuses, "text": text})
        branches.append({"letter": match.group(1), "title": match.group(2), "items": items})
    conflicts = []
    conflict_block = re.search(r"## Видимые конфликты.*?(?=\n## |\Z)", raw, re.S)
    if conflict_block:
        for line in conflict_block.group(0).splitlines():
            m = re.match(r"\d+\.\s+(.+)", line.strip())
            if m:
                conflicts.append(m.group(1))
    return center, branches, conflicts


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def svg_text(lines, x, y, size, color, anchor="start", weight=400, gap=1.22):
    spans = []
    for i, line in enumerate(lines):
        dy = 0 if i == 0 else size * gap
        spans.append(f'<tspan x="{x:.1f}" dy="{dy:.1f}">{esc(line)}</tspan>')
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="Segoe UI,Arial,sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}">' + "".join(spans) + "</text>"
    )


def wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [""]


def generate_svg(center: str, branches: list[dict], conflicts: list[str]) -> Path:
    w = h = 8192
    cx = cy = 4096
    radius = 2840
    card_w, card_h = 1280, 1120
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="#151922"/>',
        '<text x="180" y="230" font-family="Segoe UI,Arial" font-size="76" font-weight="700" fill="#F4F7FB">Psyz0r_bot — Mind Map v4</text>',
        '<text x="180" y="315" font-family="Segoe UI,Arial" font-size="34" fill="#95A0B5">Полная логика проекта · 12.10.2026 · масштабируемый источник</text>',
    ]
    # Rays first.
    positions = []
    for i, branch in enumerate(branches):
        angle = -math.pi / 2 + i * (2 * math.pi / len(branches))
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        positions.append((x, y, angle))
        color = COLORS[i]
        hub_x = cx + 1320 * math.cos(angle)
        hub_y = cy + 1320 * math.sin(angle)
        elements.append(f'<path d="M {cx} {cy} Q {hub_x:.1f} {hub_y:.1f} {x:.1f} {y:.1f}" fill="none" stroke="{color}" stroke-width="10" opacity="0.72"/>')
        elements.append(f'<circle cx="{hub_x:.1f}" cy="{hub_y:.1f}" r="74" fill="#252B38" stroke="{color}" stroke-width="8"/>')
        elements.append(svg_text([branch["letter"]], hub_x, hub_y + 20, 52, color, "middle", 800))

    # Center.
    elements.append('<rect x="3280" y="3600" width="1632" height="992" rx="90" fill="#242A37" stroke="#566176" stroke-width="8"/>')
    elements.append(svg_text(["Psyz0r_bot"], cx, 3900, 112, "#FFFFFF", "middle", 800))
    elements.append(svg_text(["TRAINING DUEL BOT", "QUAKE LIVE"], cx, 4030, 44, "#7EDCFF", "middle", 700, 1.3))
    center_lines = wrap(center.split(". ")[0] + ".", 42)
    elements.append(svg_text(center_lines, cx, 4265, 38, "#C8D0DD", "middle", 400, 1.3))
    elements.append(svg_text([f"{sum(len(b['items']) for b in branches)} micro-rules · {len(branches)} branches · {len(conflicts)} conflicts"], cx, 4495, 34, "#AAB4C5", "middle", 600))

    # Cards.
    for i, (branch, (x, y, angle)) in enumerate(zip(branches, positions)):
        color = COLORS[i]
        left = max(80, min(w - card_w - 80, x - card_w / 2))
        top = max(410, min(h - card_h - 80, y - card_h / 2))
        elements.append(f'<rect x="{left:.1f}" y="{top:.1f}" width="{card_w}" height="{card_h}" rx="44" fill="#202632" stroke="{color}" stroke-width="6"/>')
        elements.append(f'<rect x="{left:.1f}" y="{top:.1f}" width="{card_w}" height="126" rx="44" fill="{color}" opacity="0.94"/>')
        title = f"{branch['letter']}. {branch['title']}"
        title_lines = wrap(title, 31)[:2]
        elements.append(svg_text(title_lines, left + 42, top + 58, 38, "#141821", "start", 800, 1.05))
        yy = top + 178
        for item in branch["items"]:
            # Compact but complete: ID/status + first meaningful clause.
            status = item["status"]
            status_key = status.split("/")[0]
            status_color = STATUS_COLORS.get(status_key, "#D0D6E2")
            short = item["text"].split("; ")[0]
            lines = wrap(short, 61)
            max_lines = 2
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                lines[-1] = lines[-1].rstrip(".,;:") + "…"
            elements.append(f'<circle cx="{left + 42:.1f}" cy="{yy - 10:.1f}" r="10" fill="{status_color}"/>')
            elements.append(svg_text([f"{item['id']} {status}"], left + 68, yy, 25, status_color, "start", 700))
            elements.append(svg_text(lines, left + 68, yy + 34, 24, "#E5E9F0", "start", 400, 1.15))
            yy += 38 + len(lines) * 28
            if yy > top + card_h - 45:
                remaining = len(branch["items"]) - branch["items"].index(item) - 1
                if remaining > 0:
                    elements.append(svg_text([f"+ ещё {remaining} правил — на листе раздела"], left + 68, top + card_h - 30, 24, color, "start", 700))
                break

    elements.append('</svg>')
    path = OUT / "Psyz0r_bot_mindmap_v4_full.svg"
    path.write_text("\n".join(elements), encoding="utf-8")
    return path


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_wrapped(draw, xy, text, fnt, fill, width_chars, spacing=8):
    lines = wrap(text, width_chars)
    draw.multiline_text(xy, "\n".join(lines), font=fnt, fill=fill, spacing=spacing)
    bbox = draw.multiline_textbbox(xy, "\n".join(lines), font=fnt, spacing=spacing)
    return bbox[3] - bbox[1]


def generate_overview_png(branches: list[dict]) -> Path:
    w, h = 3840, 2160
    im = Image.new("RGB", (w, h), "#151922")
    d = ImageDraw.Draw(im)
    cx, cy = w // 2, h // 2
    d.text((110, 75), "Psyz0r_bot — полная карта логики v4", font=font(60, True), fill="#F5F7FB")
    d.text((112, 150), "15 веток · цвет = тема · точка = фактический статус", font=font(28), fill="#9DA8BA")
    # Center.
    d.rounded_rectangle((1510, 820, 2330, 1340), radius=52, fill="#242A37", outline="#657086", width=5)
    d.text((1920, 905), "Psyz0r_bot", anchor="ma", font=font(72, True), fill="white")
    d.text((1920, 1010), "Training Duel Bot", anchor="ma", font=font(34, True), fill="#79D8FF")
    d.multiline_text((1920, 1120), "Человечная игра\nбез WH и физических читов", anchor="ma", align="center", font=font(26), fill="#C9D1DE", spacing=8)
    radii = (655, 860)
    for i, branch in enumerate(branches):
        angle = -math.pi / 2 + i * 2 * math.pi / len(branches)
        hx = cx + radii[0] * math.cos(angle)
        hy = cy + radii[0] * math.sin(angle)
        bx = cx + 1530 * math.cos(angle)
        by = cy + 850 * math.sin(angle)
        color = COLORS[i]
        dx, dy = bx - cx, by - cy
        edge_scale = min(410 / max(abs(dx), 1), 260 / max(abs(dy), 1))
        d.line((cx + dx * edge_scale, cy + dy * edge_scale, bx, by), fill=color, width=6)
        # compact branch capsule
        box_w, box_h = 430, 118
        left = max(50, min(w - box_w - 50, bx - box_w / 2))
        top = max(235, min(h - box_h - 55, by - box_h / 2))
        d.rounded_rectangle((left, top, left + box_w, top + box_h), radius=28, fill="#222936", outline=color, width=4)
        title = f"{branch['letter']}. {branch['title']}"
        title_lines = wrap(title, 32)
        d.multiline_text((left + box_w / 2, top + 12), "\n".join(title_lines), anchor="ma", align="center", font=font(20, True), fill=color, spacing=2)
        counts = Counter(i["status"].split("/")[0] for i in branch["items"])
        status_line = " · ".join(f"{k} {v}" for k, v in counts.items())
        d.text((left + box_w / 2, top + 92), status_line, anchor="mm", font=font(15), fill="#C7CFDC")
    # Legend.
    lx, ly = 95, 2020
    for name, color in STATUS_COLORS.items():
        d.ellipse((lx, ly, lx + 18, ly + 18), fill=color)
        d.text((lx + 28, ly - 5), name, font=font(17, True), fill="#C7CFDC")
        lx += 175
    path = OUT / "Psyz0r_bot_mindmap_v4_overview_4K.png"
    im.save(path, dpi=(100, 100), optimize=True)
    return path


def generate_branch_sheets(branches: list[dict], conflicts: list[str]) -> list[Path]:
    paths = []
    for idx, branch in enumerate(branches):
        w, h = 3840, 2160
        im = Image.new("RGB", (w, h), "#151922")
        d = ImageDraw.Draw(im)
        color = COLORS[idx]
        d.rounded_rectangle((90, 80, 3750, 290), radius=42, fill="#222936", outline=color, width=6)
        d.text((150, 135), f"{branch['letter']}. {branch['title']}", font=font(52, True), fill=color)
        d.text((150, 230), f"{len(branch['items'])} микро-правил · Mind Map v4 · 12.10.2026", font=font(24), fill="#AEB8C8")
        col_w = 1760
        x_positions = (150, 2000)
        y_positions = [370, 370]
        for n, item in enumerate(branch["items"]):
            col = min(range(2), key=lambda c: y_positions[c])
            x, y = x_positions[col], y_positions[col]
            status_key = item["status"].split("/")[0]
            sc = STATUS_COLORS.get(status_key, "#D0D6E2")
            lines = wrap(item["text"], 78)
            card_h = 88 + len(lines) * 31
            d.rounded_rectangle((x, y, x + col_w, y + card_h), radius=22, fill="#202632", outline="#343C4D", width=2)
            d.ellipse((x + 25, y + 27, x + 49, y + 51), fill=sc)
            d.text((x + 66, y + 20), f"{item['id']}  {item['status']}", font=font(24, True), fill=sc)
            d.multiline_text((x + 28, y + 66), "\n".join(lines), font=font(23), fill="#E6EAF0", spacing=5)
            y_positions[col] += card_h + 20
        path = OUT / f"{idx + 1:02d}_{branch['letter']}_detail.png"
        im.save(path, dpi=(100, 100), optimize=True)
        paths.append(path)

    # Conflict sheet.
    im = Image.new("RGB", (3840, 2160), "#151922")
    d = ImageDraw.Draw(im)
    d.text((130, 100), "Неразрешённые противоречия", font=font(62, True), fill=STATUS_COLORS["CONFLICT"])
    d.text((132, 190), "Их нельзя молча превращать в код — требуется решение владельца.", font=font(28), fill="#C8D0DD")
    y = 300
    for idx, conflict in enumerate(conflicts, 1):
        lines = wrap(conflict, 118)
        card_h = 82 + len(lines) * 38
        d.rounded_rectangle((130, y, 3710, y + card_h), radius=25, fill="#25232C", outline="#A84E57", width=3)
        d.text((165, y + 25), str(idx), font=font(30, True), fill="#FF747C")
        d.multiline_text((225, y + 24), "\n".join(lines), font=font(28), fill="#F0E5E7", spacing=8)
        y += card_h + 24
    path = OUT / "16_conflicts_detail.png"
    im.save(path, dpi=(100, 100), optimize=True)
    paths.append(path)
    return paths


def generate_opml(center: str, branches: list[dict], conflicts: list[str]) -> Path:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<opml version="2.0">', '<head><title>Psyz0r_bot Mind Map v4</title></head>', '<body>']
    lines.append(f'<outline text="{esc(center)}">')
    for branch in branches:
        lines.append(f'<outline text="{esc(branch["letter"] + ". " + branch["title"])}">')
        for item in branch["items"]:
            label = f'{item["id"]} [{item["status"]}] {item["text"]}'
            lines.append(f'<outline text="{esc(label)}"/>')
        lines.append('</outline>')
    lines.append('<outline text="CONFLICT — требуется решение владельца">')
    for idx, conflict in enumerate(conflicts, 1):
        lines.append(f'<outline text="{esc(str(idx) + ". " + conflict)}"/>')
    lines.extend(['</outline>', '</outline>', '</body>', '</opml>'])
    path = OUT / "Psyz0r_bot_mindmap_v4.opml"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_readme(branches: list[dict]) -> Path:
    total = sum(len(b["items"]) for b in branches)
    text = f"""# Psyz0r_bot Mind Map v4

Источник: [`../MINDMAP_V4_CONTENT_RECONCILIATION_RU.md`](../MINDMAP_V4_CONTENT_RECONCILIATION_RU.md).

- `Psyz0r_bot_mindmap_v4_overview_4K.png` — обзорный слайд 3840×2160, 100 dpi.
- `Psyz0r_bot_mindmap_v4_full.svg` — масштабируемая радиальная карта с микро-правилами.
- `01_A_detail.png` … `15_O_detail.png` — крупные листы разделов.
- `16_conflicts_detail.png` — числа и формулировки, которые нельзя разрешать молча.
- `Psyz0r_bot_mindmap_v4.opml` — редактируемое дерево для XMind и совместимых программ.
- `index.html` — полный реестр с поиском, раскрываемыми ветками и обзорной картой; открывается без интернета.

Карта содержит {len(branches)} веток и {total} микро-правил. Цвет обозначает тему; статус рядом с ID обозначает фактическую готовность. Markdown остаётся источником истины: изображения генерируются командой `python tools/generate_mindmap_v4.py`.
"""
    path = OUT / "README.md"
    path.write_text(text, encoding="utf-8")
    return path


def generate_html(branches, conflicts):
    cards = []
    for idx, branch in enumerate(branches):
        rules = ''.join('<li><b>' + esc(item['id'] + ' · ' + item['status']) + '</b><p>' + esc(item['text']) + '</p></li>' for item in branch['items'])
        cards.append('<details open style="--accent:' + COLORS[idx] + '"><summary>' + esc(branch['letter'] + '. ' + branch['title']) + '</summary><ul>' + rules + '</ul></details>')
    conflict_html = ''.join('<li>' + esc(c) + '</li>' for c in conflicts)
    page = '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Psyz0r_bot · Mind Map v4</title>
<style>body{background:#151922;color:#e6eaf0;font:17px/1.55 system-ui;margin:0 auto;padding:32px;max-width:1500px}h1{color:#79d8ff}a{color:#79d8ff}input{box-sizing:border-box;width:100%;padding:18px;background:#252c3a;border:1px solid #657086;border-radius:12px;color:white;font:inherit;position:sticky;top:12px;z-index:2}img{width:100%;border-radius:20px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:20px}details{background:#202632;border:1px solid var(--accent);border-radius:16px;padding:20px;align-self:start}summary{font-weight:700;color:var(--accent);cursor:pointer}ul{padding-left:22px}li{margin:22px 0}li b{color:var(--accent)}p{margin:5px 0}aside{border:1px solid #ff747c;padding:24px;border-radius:16px;margin:24px 0}button{padding:10px;margin:12px 8px 12px 0;cursor:pointer}small{color:#aeb8c8}@media(max-width:600px){main{display:block}details{margin:18px 0}body{padding:16px}}</style>
<h1>Psyz0r_bot — Mind Map v4</h1><p>15 веток · 198 микро-правил · полный текст сохраняется без сокращений.</p><small>Статусы — документальный срез на 12.10.2026, а не новая проверка игрового сервера.</small>
<p><a href="../MINDMAP_V4_CONTENT_RECONCILIATION_RU.md">Исходный текст</a> · <a href="Psyz0r_bot_mindmap_v4.opml">Дерево OPML</a></p><img src="Psyz0r_bot_mindmap_v4_overview_4K.png" alt="Обзорная карта 15 разделов">
<input id="search" placeholder="Поиск: красный, дебют, тильт, A01…" aria-label="Поиск правил"><div><button onclick="document.querySelectorAll('details').forEach(d=>d.open=true)">Раскрыть всё</button><button onclick="document.querySelectorAll('details').forEach(d=>d.open=false)">Свернуть всё</button></div><main>''' + ''.join(cards) + '''</main><aside><h2>Спорные параметры и неподтверждённые результаты</h2><ol>''' + conflict_html + '''</ol></aside><script>document.getElementById('search').addEventListener('input',e=>{const q=e.target.value.toLocaleLowerCase();document.querySelectorAll('details').forEach(d=>{let hits=0;const title=d.querySelector('summary').textContent.toLocaleLowerCase();d.querySelectorAll('li').forEach(li=>{const match=!q||title.includes(q)||li.textContent.toLocaleLowerCase().includes(q);li.hidden=!match;if(match)hits++});d.hidden=hits===0;if(q&&hits)d.open=true})});</script></html>'''
    path = OUT / 'index.html'
    path.write_text(page, encoding='utf-8')
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    center, branches, conflicts = parse()
    if len(branches) != 15:
        raise SystemExit(f"Expected 15 branches, got {len(branches)}")
    ids = [item["id"] for branch in branches for item in branch["items"]]
    duplicates = [item for item, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise SystemExit(f"Duplicate IDs: {duplicates}")
    generated = [
        generate_svg(center, branches, conflicts),
        generate_overview_png(branches),
        *generate_branch_sheets(branches, conflicts),
        generate_opml(center, branches, conflicts),
        generate_readme(branches),
        generate_html(branches, conflicts),
    ]
    print(f"Generated {len(generated)} artifacts; {len(ids)} rules; {len(conflicts)} conflicts")
    for path in generated:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
