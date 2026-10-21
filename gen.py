"""Generates every SVG asset for the ByEmG GitHub profile README.

Display type is converted to vector paths (Inter Display) so headlines look
identical on every OS. Body text uses system font stacks, since SVGs loaded
through <img> on GitHub cannot fetch web fonts.
"""
import os
import textwrap
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(os.path.join(OUT, "cards"), exist_ok=True)
os.makedirs(os.path.join(OUT, "sections"), exist_ok=True)

FONT_DIR = "/usr/share/fonts/opentype/inter/"

# ---------- palette ----------
BG = "#070707"
PANEL = "#0c0c0b"
LINE = "#1f1d17"
LINE2 = "#2a271e"
GOLD = "#f5c518"
GOLD_DIM = "#8a7010"
TEXT = "#ece9e2"
MUTED = "#8d897e"
FAINT = "#5a564c"
GREEN = "#3ddc84"
BLUE = "#7aa2f7"
VIOLET = "#b48ead"
ORANGE = "#f29e4c"
TEAL = "#5fd3c8"

MONO = "'JetBrains Mono','SF Mono','SFMono-Regular',ui-monospace,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


class PathFont:
    """Turns a string into a single SVG path using a real font file."""

    def __init__(self, filename):
        self.font = TTFont(FONT_DIR + filename)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.kern = self._load_kerning()

    def _load_kerning(self):
        pairs = {}
        if "GPOS" not in self.font:
            return pairs
        gpos = self.font["GPOS"].table
        for lookup in gpos.LookupList.Lookup:
            if lookup.LookupType not in (2, 9):
                continue
            for sub in lookup.SubTable:
                if lookup.LookupType == 9:
                    sub = sub.ExtSubTable
                if getattr(sub, "Format", None) == 1:
                    firsts = sub.Coverage.glyphs
                    for i, ps in enumerate(sub.PairSet):
                        for pvr in ps.PairValueRecord:
                            v = pvr.Value1
                            if v is not None and getattr(v, "XAdvance", 0):
                                pairs.setdefault((firsts[i], pvr.SecondGlyph), v.XAdvance)
                elif getattr(sub, "Format", None) == 2:
                    cov = sub.Coverage.glyphs
                    cd1 = sub.ClassDef1.classDefs if sub.ClassDef1 else {}
                    cd2 = sub.ClassDef2.classDefs if sub.ClassDef2 else {}
                    self._class_kern = getattr(self, "_class_kern", [])
                    self._class_kern.append((set(cov), cd1, cd2, sub.Class1Record))
        return pairs

    def _k(self, a, b):
        if (a, b) in self.kern:
            return self.kern[(a, b)]
        for cov, cd1, cd2, recs in getattr(self, "_class_kern", []):
            if a in cov:
                c1 = cd1.get(a, 0)
                c2 = cd2.get(b, 0)
                try:
                    v = recs[c1].Class2Record[c2].Value1
                except (IndexError, AttributeError):
                    continue
                if v is not None and getattr(v, "XAdvance", 0):
                    return v.XAdvance
                return 0
        return 0

    def path(self, text, x, y, size, tracking=0.0):
        s = size / self.upm
        cx = x
        parts = []
        prev = None
        for ch in text:
            g = self.cmap.get(ord(ch))
            if g is None:
                continue
            if prev is not None:
                cx += self._k(prev, g) * s
            pen = SVGPathPen(self.glyphs)
            self.glyphs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
            cmd = pen.getCommands()
            if cmd:
                parts.append(cmd)
            cx += self.glyphs[g].width * s + tracking * size
            prev = g
        return " ".join(parts), cx - x

    def width(self, text, size, tracking=0.0):
        return self.path(text, 0, 0, size, tracking)[1]


DISPLAY = PathFont("InterDisplay-Bold.otf")
DISPLAY_SEMI = PathFont("InterDisplay-SemiBold.otf")


def fade(delay, d=0.7):
    total = delay + d
    kt = delay / total if total else 0
    return (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{kt:.3f};1" '
            f'dur="{total:.2f}s" begin="0s" fill="freeze"/>')


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, body, title, defs="", style=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<defs>{defs}</defs>
<style>
.m{{font-family:{MONO}}} .s{{font-family:{SANS}}}
{style}
</style>
{body}
</svg>
"""


def write(name, content):
    assert "—" not in content, f"em-dash found in {name}"
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)


def frame(w, h, rx=18, fill=BG, glow=None):
    g = ""
    if glow:
        g = f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{rx}" fill="url(#{glow})"/>'
    return (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{rx}" fill="{fill}"/>'
            f'{g}<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{rx}" fill="none" stroke="{LINE}"/>')


DOTS = f"""<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
<circle cx="1.5" cy="1.5" r="1" fill="#ffffff" fill-opacity="0.055"/></pattern>"""


# =====================================================================
# HERO
# =====================================================================
def hero():
    W, H = 1200, 460
    name1, _ = DISPLAY.path("Pierre Emmanuel", 72, 222, 76, tracking=-0.025)
    name2, w2 = DISPLAY.path("Gérard", 72, 304, 76, tracking=-0.025)
    dot, _ = DISPLAY.path(".", 72 + w2 + 2, 304, 76)

    # typewriter line
    line = "I turn models into products people rely on."
    cw = 11.4  # approx mono advance at 19px
    n = len(line)
    vals = ";".join(f"{i*cw:.1f}" for i in range(n + 1))
    cvals = ";".join(f"{150 + i*cw + (4 if i == n else 0):.1f}" for i in range(n + 1))

    # agent loop graphic
    cx, cy, r = 935, 236, 128
    nodes = [("plan", -90), ("tools", -18), ("memory", 54), ("eval", 126), ("ship", 198)]
    import math
    graph = []
    graph.append(f'<circle cx="{cx}" cy="{cy}" r="{r+44}" fill="none" stroke="{LINE2}" stroke-dasharray="2 7">'
                 f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="90s" repeatCount="indefinite"/></circle>')
    graph.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE2}"/>')
    # arc highlight travelling round the ring
    graph.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#arc)" stroke-width="2" stroke-linecap="round" '
                 f'stroke-dasharray="120 {2*math.pi*r-120:.0f}">'
                 f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="9s" repeatCount="indefinite"/></circle>')
    for i, (label, ang) in enumerate(nodes):
        a = math.radians(ang)
        nx, ny = cx + r * math.cos(a), cy + r * math.sin(a)
        pid = f"edge{i}"
        graph.append(f'<path id="{pid}" d="M{cx},{cy} L{nx:.1f},{ny:.1f}" stroke="{LINE2}" stroke-width="1"/>')
        graph.append(f'<circle r="2.6" fill="{GOLD}"><animateMotion dur="2.4s" begin="{i*0.48:.2f}s" repeatCount="indefinite" '
                     f'keyPoints="0;1;0" keyTimes="0;0.5;1" calcMode="linear"><mpath href="#{pid}"/></animateMotion>'
                     f'<animate attributeName="opacity" values="0;1;1;0" dur="2.4s" begin="{i*0.48:.2f}s" repeatCount="indefinite"/></circle>')
        lw = len(label) * 7.6 + 26
        graph.append(f'<g><rect x="{nx-lw/2:.1f}" y="{ny-15:.1f}" width="{lw:.1f}" height="30" rx="15" fill="{PANEL}" stroke="{LINE2}"/>'
                     f'<circle cx="{nx-lw/2+13:.1f}" cy="{ny:.1f}" r="3" fill="{GOLD}" opacity=".85">'
                     f'<animate attributeName="opacity" values=".25;1;.25" dur="2.4s" begin="{i*0.48:.2f}s" repeatCount="indefinite"/></circle>'
                     f'<text x="{nx-lw/2+22:.1f}" y="{ny+4.5:.1f}" class="m" font-size="12.5" fill="{TEXT}">{label}</text></g>')
    graph.append(f'<circle cx="{cx}" cy="{cy}" r="58" fill="url(#core)"/>')
    graph.append(f'<circle cx="{cx}" cy="{cy}" r="38" fill="{PANEL}" stroke="{GOLD}" stroke-opacity=".7"/>')
    graph.append(f'<circle cx="{cx}" cy="{cy}" r="38" fill="none" stroke="{GOLD}" stroke-opacity=".5">'
                 f'<animate attributeName="r" values="38;56" dur="2.4s" repeatCount="indefinite"/>'
                 f'<animate attributeName="stroke-opacity" values=".5;0" dur="2.4s" repeatCount="indefinite"/></circle>')
    graph.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" class="m" font-size="13" font-weight="700" fill="{GOLD}">agent</text>')

    defs = DOTS + f"""
<radialGradient id="glowR" cx="78%" cy="50%" r="45%"><stop offset="0" stop-color="{GOLD}" stop-opacity=".16"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
<radialGradient id="glowL" cx="0%" cy="0%" r="60%"><stop offset="0" stop-color="#ffffff" stop-opacity=".05"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>
<radialGradient id="core"><stop offset="0" stop-color="{GOLD}" stop-opacity=".35"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
<linearGradient id="goldText" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffe27a"/><stop offset=".55" stop-color="{GOLD}"/><stop offset="1" stop-color="#b8900c"/></linearGradient>
<linearGradient id="whiteText" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#cfcbc1"/></linearGradient>
<linearGradient id="arc"><stop offset="0" stop-color="{GOLD}" stop-opacity="0"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>
<linearGradient id="scan" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{GOLD}" stop-opacity="0"/><stop offset=".5" stop-color="{GOLD}" stop-opacity=".9"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></linearGradient>
<clipPath id="type"><rect x="150" y="330" height="36" width="{n*cw+20:.0f}">
<animate attributeName="width" values="0;{vals}" dur="3.4s" begin="0s" fill="freeze" calcMode="discrete"/></rect></clipPath>
<clipPath id="card"><rect x="0" y="0" width="{W}" height="{H}" rx="18"/></clipPath>
"""
    style = f"""
.blink{{animation:blink 1.05s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.pulse{{animation:pulse 1.8s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
"""
    status_plain = "OPEN TO APPLIED AI ROLES & INTERNSHIPS  ·  UK"
    status = esc(status_plain)
    pill_w = len(status_plain) * 8.3 + 54
    body = f"""
<g clip-path="url(#card)">
{frame(W, H)}
<rect width="{W}" height="{H}" fill="url(#dots)"/>
<rect width="{W}" height="{H}" fill="url(#glowR)"/>
<rect width="{W}" height="{H}" fill="url(#glowL)"/>
<rect x="0" y="0" width="260" height="1.5" fill="url(#scan)"><animate attributeName="x" values="-260;{W}" dur="6s" repeatCount="indefinite"/></rect>

<g transform="translate(28 30)">
<circle cx="0" cy="0" r="5.5" fill="#2b2922"/><circle cx="18" cy="0" r="5.5" fill="#2b2922"/><circle cx="36" cy="0" r="5.5" fill="{GOLD}" fill-opacity=".8"/>
<text x="58" y="4.5" class="m" font-size="12.5" fill="{FAINT}">pierre@afryx  ~/applied-ai</text>
</g>
<text x="{W-28}" y="35" text-anchor="end" class="m" font-size="12.5" fill="{FAINT}">v2026.10</text>
<line x1="0" y1="58" x2="{W}" y2="58" stroke="{LINE}"/>

<g>{fade(0.1)}<text x="74" y="122" class="m" font-size="13.5" letter-spacing="3" fill="{GOLD}">APPLIED AI ENGINEER  /  FOUNDER &amp; CTO, AFRYX LABS</text></g>
<g>{fade(0.25)}<path d="{name1}" fill="url(#whiteText)"/></g>
<g>{fade(0.4)}<path d="{name2}" fill="url(#goldText)"/><path d="{dot}" fill="{TEXT}"/></g>

<text x="74" y="355" class="m" font-size="19" fill="{GOLD}">~$</text>
<text x="112" y="355" class="m" font-size="19" fill="{FAINT}">›</text>
<g clip-path="url(#type)"><text x="150" y="355" class="m" font-size="19" fill="{TEXT}">{esc(line)}</text></g>
<rect y="338" width="10" height="22" fill="{GOLD}" class="blink" x="{150+n*cw+4:.0f}">
<animate attributeName="x" values="150;{cvals}" dur="3.4s" begin="0s" fill="freeze" calcMode="discrete"/></rect>

<g>{fade(3.2)}
<rect x="74" y="390" width="{pill_w:.0f}" height="34" rx="17" fill="{GOLD}" fill-opacity=".06" stroke="{GOLD_DIM}" stroke-opacity=".7"/>
<circle cx="96" cy="407" r="4.5" fill="{GREEN}" class="pulse"/>
<circle cx="96" cy="407" r="4.5" fill="none" stroke="{GREEN}"><animate attributeName="r" values="4.5;11" dur="1.8s" repeatCount="indefinite"/><animate attributeName="opacity" values=".8;0" dur="1.8s" repeatCount="indefinite"/></circle>
<text x="112" y="411.5" class="m" font-size="12" letter-spacing="1" fill="{TEXT}">{status}</text>
</g>

{''.join(graph)}
</g>
"""
    write("hero.svg", svg(W, H, body, "Pierre Emmanuel Gérard, Applied AI Engineer and Founder & CTO of Afryx Labs", defs, style))


# =====================================================================
# SECTION HEADERS
# =====================================================================
def section(slug, num, title, kicker):
    W, H = 1200, 84
    p, tw = DISPLAY.path(title, 92, 56, 34, tracking=-0.02)
    x2 = 92 + tw + 26
    body = f"""
{frame(W, H, rx=14)}
<text x="24" y="54" class="m" font-size="14" fill="{GOLD}" letter-spacing="1">{num}</text>
<rect x="60" y="38" width="16" height="16" rx="3" fill="none" stroke="{GOLD_DIM}"/>
<rect x="64" y="42" width="8" height="8" rx="1.5" fill="{GOLD}"><animate attributeName="opacity" values="1;.25;1" dur="2.6s" repeatCount="indefinite"/></rect>
<path d="{p}" fill="{TEXT}"/>
<line x1="{x2:.0f}" y1="45" x2="{W-24-len(kicker)*9.4-20:.0f}" y2="45" stroke="{LINE2}"/>
<line x1="{x2:.0f}" y1="45" x2="{x2+70:.0f}" y2="45" stroke="{GOLD}" stroke-opacity=".6"/>
<text x="{W-24}" y="50" text-anchor="end" class="m" font-size="12" letter-spacing="2" fill="{MUTED}">{esc(kicker)}</text>
"""
    write(f"sections/{slug}.svg", svg(W, H, body, f"{num} {title}"))


# =====================================================================
# NOW PANEL
# =====================================================================
NOW = [
    ("LEAD", GOLD, "SiteDue", "Billing-completion app for UK electrical maintenance SMEs  ·  React + Supabase"),
    ("ARCH", BLUE, "Clinical AI triage", "Clinician-led screening prototype for a UK women's health clinic  ·  evals first"),
    ("EVAL", GREEN, "pierre-agent-evals", "Harder task groups, model and prompt experiments, traces published"),
    ("TEAM", VIOLET, "Edge AI Challenge", "Assembling an England-based team to build on-device AI"),
    ("SHIP", ORANGE, "Kampus", "Live with fee-paying schools  ·  co-developed by Afryx Labs"),
]


def now_panel():
    W = 1200
    top = 112
    step = 52
    H = top + step * len(NOW) + 46
    rows = []
    for i, (tag, col, title, desc) in enumerate(NOW):
        y = top + i * step
        rows.append(f"""<g>{fade(0.35 + i*0.22)}
<rect x="32" y="{y-17}" width="64" height="24" rx="6" fill="{col}" fill-opacity=".1" stroke="{col}" stroke-opacity=".45"/>
<text x="64" y="{y-0.5}" text-anchor="middle" class="m" font-size="11.5" font-weight="700" letter-spacing="1.5" fill="{col}">{tag}</text>
<text x="118" y="{y}" class="s" font-size="16.5" font-weight="600" fill="{TEXT}">{esc(title)}</text>
<text x="330" y="{y}" class="m" font-size="13.2" fill="{MUTED}">{esc(desc)}</text>
<line x1="32" y1="{y+19}" x2="{W-32}" y2="{y+19}" stroke="{LINE}" stroke-dasharray="2 5"/>
</g>""")
    endy = top + step * len(NOW) + 14
    body = f"""
{frame(W, H, glow="g")}
<rect width="{W}" height="{H}" rx="18" fill="url(#dots)"/>
<g transform="translate(26 28)"><circle r="5" fill="#2b2922"/><circle cx="16" r="5" fill="#2b2922"/><circle cx="32" r="5" fill="#2b2922"/></g>
<text x="{W/2}" y="32" text-anchor="middle" class="m" font-size="12.5" fill="{FAINT}">now.log</text>
<text x="{W-26}" y="32" text-anchor="end" class="m" font-size="12.5" fill="{FAINT}">updated Oct 2026</text>
<line x1="0" y1="52" x2="{W}" y2="52" stroke="{LINE}"/>
<text x="32" y="{top-38}" class="m" font-size="14"><tspan fill="{GOLD}">pierre@afryx</tspan><tspan fill="{FAINT}">:~$ </tspan><tspan fill="{TEXT}">tail -f now.log</tspan></text>
{''.join(rows)}
<g>{fade(0.35 + len(NOW)*0.22)}
<text x="32" y="{endy}" class="m" font-size="14"><tspan fill="{GOLD}">pierre@afryx</tspan><tspan fill="{FAINT}">:~$ </tspan></text>
<rect x="168" y="{endy-14}" width="9" height="18" fill="{GOLD}" class="blink"/>
</g>
"""
    defs = DOTS + f'<radialGradient id="g" cx="100%" cy="0%" r="70%"><stop offset="0" stop-color="{GOLD}" stop-opacity=".07"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>'
    style = """
.blink{animation:blink 1.05s steps(1) infinite}@keyframes blink{50%{opacity:0}}
"""
    write("now.svg", svg(W, H, body, "Now: what Pierre is working on, October 2026", defs, style))


# =====================================================================
# PROJECT CARDS
# =====================================================================
CARDS = [
    dict(slug="kampus", status="IN PRODUCTION", col=GREEN, title="Kampus",
         tag="Institution management, end to end.",
         desc="Admissions, academics, finance and communication with an AI operations layer. Live with fee-paying schools on a multi-tenant Postgres backend. Co-developed by Afryx Labs.",
         chips=["Next.js", "Supabase", "Expo", "LangGraph"], link=True, motif="grid"),
    dict(slug="arcflow", status="LIVE", col=GOLD, title="Arcflow",
         tag="An AI Chief of Staff for growing teams.",
         desc="One wedge, executed relentlessly: action tracking and accountability. A LangGraph multi-agent pipeline on a multi-tenant backend, shipped solo.",
         chips=["LangGraph", "Supabase", "Stripe", "Vercel"], link=True, motif="rings"),
    dict(slug="sitedue", status="IN BUILD", col=BLUE, title="SiteDue",
         tag="Finished jobs that actually get billed.",
         desc="A billing-completion web app for UK commercial electrical maintenance SMEs. I lead product and architecture across a five-person build team.",
         chips=["React", "Vite", "Supabase"], link=False, motif="bars"),
    dict(slug="triage", status="PROTOTYPE", col=TEAL, title="Clinical AI Triage",
         tag="AI that drafts. The clinician decides.",
         desc="A screening assistant for a UK women's health clinic: structured summaries, red-flag checks and missing-information prompts, evaluated on clinician-approved synthetic cases.",
         chips=["Human-in-the-loop", "Evals", "Synthetic data"], link=False, motif="pulse"),
    dict(slug="opep", status="IN DEV", col=ORANGE, title="O'pep",
         tag="Interurban bus travel, rebuilt for Cameroon.",
         desc="Search agencies, compare, pick your seat live and pay by Mobile Money. Two-sided: a traveller app plus free ticketing software for agencies.",
         chips=["Expo", "React", "Vite", "Supabase"], link=False, motif="route"),
    dict(slug="miyora", status="IN DEV", col=VIOLET, title="Miyora AI",
         tag="Skin intelligence with a consultant's care.",
         desc="Making an AI skincare recommendation feel as considered as a professional consultation, from image to routine.",
         chips=["Claude API", "React Native", "Computer vision"], link=False, motif="orbit"),
]


def motif(kind, col, W, H):
    ox, oy = W - 80, H - 90
    o = f'<g opacity=".07" stroke="{col}" fill="none">'
    if kind == "grid":
        for i in range(5):
            for j in range(4):
                o += f'<rect x="{ox-40+i*30}" y="{oy-40+j*30}" width="20" height="20" rx="4"/>'
    elif kind == "rings":
        for r in (30, 55, 80, 105):
            o += f'<circle cx="{ox+40}" cy="{oy+30}" r="{r}"/>'
    elif kind == "bars":
        for i, h in enumerate([40, 70, 55, 95, 80, 120]):
            o += f'<rect x="{ox-30+i*26}" y="{oy+90-h}" width="14" height="{h}" rx="3"/>'
    elif kind == "pulse":
        o += f'<path d="M{ox-60},{oy+30} h50 l12,-40 l16,80 l14,-60 l10,20 h90" stroke-width="2"/>'
    elif kind == "route":
        o += f'<path d="M{ox-50},{oy+80} C{ox},{oy-20} {ox+60},{oy+100} {ox+130},{oy-10}" stroke-width="2" stroke-dasharray="6 6"/>'
        o += f'<circle cx="{ox-50}" cy="{oy+80}" r="7"/><circle cx="{ox+130}" cy="{oy-10}" r="7"/>'
    elif kind == "orbit":
        o += f'<ellipse cx="{ox+40}" cy="{oy+30}" rx="90" ry="34"/><ellipse cx="{ox+40}" cy="{oy+30}" rx="90" ry="34" transform="rotate(60 {ox+40} {oy+30})"/>'
        o += f'<ellipse cx="{ox+40}" cy="{oy+30}" rx="90" ry="34" transform="rotate(-60 {ox+40} {oy+30})"/>'
    return o + "</g>"


def card(c):
    W, H = 580, 300
    col = c["col"]
    tp, _ = DISPLAY.path(c["title"], 32, 108, 34, tracking=-0.02)
    lines = textwrap.wrap(c["desc"], 66, break_on_hyphens=False)
    assert len(lines) <= 3, (c["slug"], lines)
    desc = "".join(f'<text x="32" y="{176 + i*22}" class="s" font-size="14.2" fill="{MUTED}">{esc(l)}</text>' for i, l in enumerate(lines))
    chips = ""
    x = 32
    for ch in c["chips"]:
        w = len(ch) * 7.3 + 22
        chips += (f'<rect x="{x:.1f}" y="250" width="{w:.1f}" height="26" rx="7" fill="#ffffff" fill-opacity=".03" stroke="{LINE2}"/>'
                  f'<text x="{x+11:.1f}" y="267.5" class="m" font-size="12" fill="{TEXT}" fill-opacity=".85">{esc(ch)}</text>')
        x += w + 8
    sw = len(c["status"]) * 8.4 + 40
    arrow = ""
    if c["link"]:
        arrow = (f'<g transform="translate({W-58} 26)"><rect width="30" height="30" rx="9" fill="#ffffff" fill-opacity=".03" stroke="{LINE2}"/>'
                 f'<path d="M11 19 L19 11 M12.5 11 H19 V17.5" stroke="{TEXT}" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>')
    body = f"""
{frame(W, H, glow="g")}
<rect width="{W}" height="{H}" rx="18" fill="url(#dots)"/>
{motif(c["motif"], col, W, H)}
<rect x="32" y="26" width="{sw:.1f}" height="26" rx="13" fill="{col}" fill-opacity=".08" stroke="{col}" stroke-opacity=".4"/>
<circle cx="47" cy="39" r="3.6" fill="{col}" class="pulse"/>
<text x="58" y="43" class="m" font-size="11.5" font-weight="700" letter-spacing="1.4" fill="{col}">{esc(c["status"])}</text>
{arrow}
<path d="{tp}" fill="{TEXT}"/>
<text x="32" y="140" class="s" font-size="16" font-weight="600" fill="{TEXT}" fill-opacity=".92">{esc(c["tag"])}</text>
{desc}
{chips}
<rect x="32" y="{H-1.5}" width="120" height="1.5" fill="{col}" opacity=".9"/>
"""
    defs = DOTS + (f'<radialGradient id="g" cx="100%" cy="0%" r="80%"><stop offset="0" stop-color="{col}" stop-opacity=".13"/>'
                   f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
    style = ".pulse{animation:pulse 1.8s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}"
    write(f"cards/{c['slug']}.svg", svg(W, H, body, f"{c['title']}: {c['tag']}", defs, style))


# =====================================================================
# EVALS FEATURE CARD
# =====================================================================
def evals_card():
    W, H = 1200, 360
    tp, _ = DISPLAY.path("pierre-agent-evals", 40, 114, 40, tracking=-0.02)
    desc = ["An evaluation harness for LLM agents. Every failure is classified against a six-category",
            "taxonomy, so improvements are measured rather than assumed. Results published as they land."]
    d = "".join(f'<text x="40" y="{152 + i*24}" class="s" font-size="15.5" fill="{MUTED}">{esc(l)}</text>' for i, l in enumerate(desc))
    stages = [("01", "task suite", "6 task groups"), ("02", "agent loop", "minimal, hand-rolled"),
              ("03", "judge", "programmatic + LLM"), ("04", "classify", "6 failure categories"),
              ("05", "report", "pass rate · cost · latency")]
    x0, y0, bw, bh, gap = 40, 236, 204, 84, 25
    st = ""
    for i, (n, t, s) in enumerate(stages):
        x = x0 + i * (bw + gap)
        hl = i == 3
        st += (f'<rect x="{x}" y="{y0}" width="{bw}" height="{bh}" rx="12" fill="{GOLD if hl else "#ffffff"}" fill-opacity="{".07" if hl else ".025"}" '
               f'stroke="{GOLD if hl else LINE2}" stroke-opacity="{".6" if hl else "1"}"/>'
               f'<text x="{x+18}" y="{y0+28}" class="m" font-size="11.5" fill="{GOLD}" letter-spacing="1">{n}</text>'
               f'<text x="{x+18}" y="{y0+52}" class="s" font-size="16.5" font-weight="600" fill="{TEXT}">{esc(t)}</text>'
               f'<text x="{x+18}" y="{y0+71}" class="m" font-size="11.5" fill="{MUTED}">{esc(s)}</text>')
        if i < len(stages) - 1:
            ax = x + bw
            st += (f'<line x1="{ax+3}" y1="{y0+bh/2}" x2="{ax+gap-3}" y2="{y0+bh/2}" stroke="{GOLD}" stroke-width="1.5" stroke-dasharray="3 4" class="flow"/>')
    body = f"""
{frame(W, H, glow="g")}
<rect width="{W}" height="{H}" rx="18" fill="url(#dots)"/>
<rect x="40" y="30" width="148" height="26" rx="13" fill="{GOLD}" fill-opacity=".08" stroke="{GOLD}" stroke-opacity=".4"/>
<circle cx="55" cy="43" r="3.6" fill="{GOLD}" class="pulse"/>
<text x="66" y="47" class="m" font-size="11.5" font-weight="700" letter-spacing="1.4" fill="{GOLD}">OPEN RESEARCH</text>
<g transform="translate({W-58} 30)"><rect width="30" height="30" rx="9" fill="#ffffff" fill-opacity=".03" stroke="{LINE2}"/>
<path d="M11 19 L19 11 M12.5 11 H19 V17.5" stroke="{TEXT}" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
<text x="{W-72}" y="50" text-anchor="end" class="m" font-size="12" fill="{FAINT}">github.com/ByEmG/pierre-agent-evals</text>
<path d="{tp}" fill="{TEXT}"/>
{d}
{st}
<rect x="40" y="{H-1.5}" width="160" height="1.5" fill="{GOLD}"/>
"""
    defs = DOTS + f'<radialGradient id="g" cx="0%" cy="100%" r="70%"><stop offset="0" stop-color="{GOLD}" stop-opacity=".09"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>'
    style = """.pulse{animation:pulse 1.8s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
.flow{animation:flow 1s linear infinite}@keyframes flow{to{stroke-dashoffset:-14}}"""
    write("cards/evals.svg", svg(W, H, body, "pierre-agent-evals: evaluation harness for LLM agents", defs, style))


# =====================================================================
# PRINCIPLES
# =====================================================================
def principles():
    W, H = 1200, 220
    items = [("01", "Orchestrate", ["Agents, tools and memory wired into", "workflows that hold up outside the demo."]),
             ("02", "Evaluate", ["Measure how a system fails before", "claiming it works. Traces over vibes."]),
             ("03", "Ship", ["Production, real users, and the feedback", "loops that make the next version better."])]
    cw, gap = 381, 28
    body = ""
    for i, (n, t, ls) in enumerate(items):
        x = i * (cw + gap) + 0.5
        tp, _ = DISPLAY_SEMI.path(t, x + 30, 112, 28, tracking=-0.015)
        body += (f'<rect x="{x}" y="0.5" width="{cw}" height="{H-1}" rx="18" fill="{BG}" stroke="{LINE}"/>'
                 f'<text x="{x+30}" y="50" class="m" font-size="13" fill="{GOLD}" letter-spacing="2">{n}</text>'
                 f'<line x1="{x+62}" y1="45" x2="{x+cw-30}" y2="45" stroke="{LINE2}"/>'
                 f'<path d="{tp}" fill="{TEXT}"/>'
                 + "".join(f'<text x="{x+30}" y="{150+j*22}" class="s" font-size="14.5" fill="{MUTED}">{esc(l)}</text>' for j, l in enumerate(ls)))
    write("principles.svg", svg(W, H, body, "Orchestrate, Evaluate, Ship"))


# =====================================================================
# STACK
# =====================================================================
def stack():
    cols = [("AI & AGENTS", GOLD, ["Claude API", "LangGraph", "Agent evaluation", "Tool use & memory"]),
            ("LANGUAGES", BLUE, ["Python", "TypeScript", "SQL"]),
            ("PRODUCT", GREEN, ["Next.js", "React", "React Native · Expo", "Vite"]),
            ("DATA & INFRA", ORANGE, ["Supabase · Postgres", "Stripe", "Vercel", "Playwright"]),
            ("CLASSICAL ML", VIOLET, ["scikit-learn", "XGBoost", "CNNs", "NLP pipelines"])]
    W, H = 1200, 250
    cw = (W - 4 * 16) / 5
    body = ""
    for i, (h, col, items) in enumerate(cols):
        x = i * (cw + 16) + 0.5
        body += (f'<rect x="{x:.1f}" y="0.5" width="{cw:.1f}" height="{H-1}" rx="16" fill="{BG}" stroke="{LINE}"/>'
                 f'<rect x="{x+22:.1f}" y="30" width="8" height="8" rx="2" fill="{col}"/>'
                 f'<text x="{x+38:.1f}" y="38.5" class="m" font-size="11.5" font-weight="700" letter-spacing="1.6" fill="{col}">{esc(h)}</text>'
                 f'<line x1="{x+22:.1f}" y1="58" x2="{x+cw-22:.1f}" y2="58" stroke="{LINE2}"/>')
        for j, it in enumerate(items):
            y = 92 + j * 38
            body += (f'<text x="{x+22:.1f}" y="{y}" class="m" font-size="12" fill="{FAINT}">{j+1:02d}</text>'
                     f'<text x="{x+50:.1f}" y="{y}" class="s" font-size="15" fill="{TEXT}">{esc(it)}</text>')
    write("stack.svg", svg(W, H, body, "Technical stack"))


# =====================================================================
# TIMELINE
# =====================================================================
def timeline():
    W, H = 1200, 360
    items = [("2021", "Data Science Intern", "BCPME"),
             ("2023", "Student Ambassador", "Oxford International Education"),
             ("2025", "Co-Founder", "Miyora Skin Lab"),
             ("2025", "Assistant Tech Engineer", "Institut Supérieur Fang de Messamena"),
             ("2026", "Founder & CEO", "Arcflow"),
             ("2026", "Founder & CTO", "Afryx Labs"),
             ("2027", "BSc Applied AI", "University of Bradford")]
    ly = 180
    x0, x1 = 90, W - 90
    step = (x1 - x0) / (len(items) - 1)
    body = f"""{frame(W, H)}
<rect width="{W}" height="{H}" rx="18" fill="url(#dots)"/>
<line x1="40" y1="{ly}" x2="{W-40}" y2="{ly}" stroke="{LINE2}" stroke-width="2"/>
<line x1="40" y1="{ly}" x2="{W-40}" y2="{ly}" stroke="url(#tl)" stroke-width="2" stroke-dasharray="{W-80}" stroke-dashoffset="0"><animate attributeName="stroke-dashoffset" values="{W-80};0" dur="2.2s" begin="0s" fill="freeze"/></line>
"""
    for i, (yr, role, org) in enumerate(items):
        x = x0 + i * step
        up = i % 2 == 0
        last = i == len(items) - 1
        ty = ly - 92 if up else ly + 56
        body += f'<line x1="{x:.1f}" y1="{ly + (-14 if up else 14)}" x2="{x:.1f}" y2="{ly + (-30 if up else 30)}" stroke="{LINE2}"/>'
        if last:
            body += (f'<circle cx="{x:.1f}" cy="{ly}" r="8" fill="{BG}" stroke="{GOLD}" stroke-width="2"/>'
                     f'<circle cx="{x:.1f}" cy="{ly}" r="8" fill="none" stroke="{GOLD}"><animate attributeName="r" values="8;18" dur="2s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values=".8;0" dur="2s" repeatCount="indefinite"/></circle>')
        else:
            body += f'<circle cx="{x:.1f}" cy="{ly}" r="6" fill="{GOLD}"/><circle cx="{x:.1f}" cy="{ly}" r="11" fill="none" stroke="{GOLD}" stroke-opacity=".25"/>'
        body += (f'<g>{fade(0.2 + i*0.18, 0.6)}'
                 f'<text x="{x:.1f}" y="{ty}" text-anchor="middle" class="m" font-size="12.5" letter-spacing="2" fill="{GOLD}">{yr}{" · EXPECTED" if last else ""}</text>'
                 f'<text x="{x:.1f}" y="{ty+24}" text-anchor="middle" class="s" font-size="15.5" font-weight="600" fill="{TEXT}">{esc(role)}</text>'
                 f'<text x="{x:.1f}" y="{ty+44}" text-anchor="middle" class="s" font-size="13" fill="{MUTED}">{esc(org)}</text></g>')
    body += f'<text x="{W-32}" y="{H-24}" text-anchor="end" class="m" font-size="12" fill="{FAINT}">+ CMI Level 5, Management &amp; Leadership</text>'
    defs = DOTS + f'<linearGradient id="tl"><stop offset="0" stop-color="{GOLD}" stop-opacity=".1"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>'
    write("timeline.svg", svg(W, H, body, "Career timeline", defs))


# =====================================================================
# FOOTER
# =====================================================================
def footer():
    W, H = 1200, 150
    tp, tw = DISPLAY_SEMI.path("Fewer things, done properly.", 0, 0, 30, tracking=-0.015)
    x = (W - tw) / 2
    tp, _ = DISPLAY_SEMI.path("Fewer things, done properly.", x, 84, 30, tracking=-0.015)
    body = f"""
{frame(W, H, rx=14)}
<rect x="0" y="0.5" width="200" height="1.5" fill="url(#scan)"><animate attributeName="x" values="-200;{W}" dur="5s" repeatCount="indefinite"/></rect>
<path d="{tp}" fill="{TEXT}"/>
<text x="{W/2}" y="120" text-anchor="middle" class="m" font-size="12.5" fill="{FAINT}">session closed  ·  <tspan fill="{GOLD}">afryxlabs.com</tspan>  ·  from the continent, for the continent</text>
"""
    defs = f'<linearGradient id="scan"><stop offset="0" stop-color="{GOLD}" stop-opacity="0"/><stop offset=".5" stop-color="{GOLD}"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></linearGradient>'
    write("footer.svg", svg(W, H, body, "Session closed. Fewer things, done properly.", defs))


if __name__ == "__main__":
    hero()
    for args in [("now", "01", "Now", "OCT 2026"), ("work", "02", "Selected work", "WHAT I'M SHIPPING"),
                 ("research", "03", "Open research", "EVALUATION"), ("principles", "04", "How I build", "PRINCIPLES"),
                 ("stack", "05", "Stack", "TOOLS I REACH FOR"), ("path", "06", "Path", "2021 TO NOW"),
                 ("contact", "07", "Contact", "LET'S BUILD")]:
        section(*args)
    now_panel()
    for c in CARDS:
        card(c)
    evals_card()
    principles()
    stack()
    timeline()
    footer()
    print("ok")
