"""Builds assets/header.svg, the one image on the GitHub profile.

Every word is converted to vector outlines from the bundled fonts, so the
header looks identical on every device. Edit the TEXT block below, then run:

    python3 tools/gen.py
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(os.path.dirname(HERE), "assets", "header.svg")

# ---------------- TEXT ----------------
ROLE = "APPLIED AI ENGINEER"
PLACE = "LEEDS, UNITED KINGDOM"
NAME_1 = "Pierre Emmanuel"
NAME_2 = "Gérard"
LEDE = ["I build AI products end to end,",
        "from the agent logic to the",
        "interface people use every day."]
FACTS = [("NOW", "Founder & CTO, Afryx Labs"),
         ("STUDYING", "BSc Applied AI, Bradford"),
         ("OPEN TO", "Applied AI roles in the UK")]

# ---------------- COLOURS ----------------
PAPER = "#F3F0E8"
INK = "#1A1917"
MUTED = "#6E695F"
RULE = "#D9D4C7"
ACCENT = "#B5562A"


class PathFont:
    def __init__(self, filename):
        self.font = TTFont(os.path.join(FONTS, filename))
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.kern = {}
        self.class_kern = []
        if "GPOS" in self.font:
            for lookup in self.font["GPOS"].table.LookupList.Lookup:
                if lookup.LookupType not in (2, 9):
                    continue
                for sub in lookup.SubTable:
                    if lookup.LookupType == 9:
                        sub = sub.ExtSubTable
                    if getattr(sub, "Format", None) == 1:
                        firsts = sub.Coverage.glyphs
                        for i, ps in enumerate(sub.PairSet):
                            for rec in ps.PairValueRecord:
                                v = rec.Value1
                                if v is not None and getattr(v, "XAdvance", 0):
                                    self.kern.setdefault((firsts[i], rec.SecondGlyph), v.XAdvance)
                    elif getattr(sub, "Format", None) == 2:
                        self.class_kern.append((set(sub.Coverage.glyphs),
                                                sub.ClassDef1.classDefs if sub.ClassDef1 else {},
                                                sub.ClassDef2.classDefs if sub.ClassDef2 else {},
                                                sub.Class1Record))

    def _k(self, a, b):
        if (a, b) in self.kern:
            return self.kern[(a, b)]
        for cov, cd1, cd2, recs in self.class_kern:
            if a in cov:
                try:
                    v = recs[cd1.get(a, 0)].Class2Record[cd2.get(b, 0)].Value1
                except (IndexError, AttributeError):
                    continue
                return getattr(v, "XAdvance", 0) or 0 if v is not None else 0
        return 0

    def layout(self, text, x, y, size, tracking=0.0):
        s = size / self.upm
        cx, prev, parts = x, None, []
        for ch in text:
            g = self.cmap.get(ord(ch))
            if g is None:
                continue
            if prev is not None:
                cx += self._k(prev, g) * s
            pen = SVGPathPen(self.glyphs)
            self.glyphs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
            if pen.getCommands():
                parts.append(pen.getCommands())
            cx += self.glyphs[g].width * s + tracking * size
            prev = g
        return " ".join(parts), cx - x - (tracking * size if text else 0)

    def width(self, text, size, tracking=0.0):
        return self.layout(text, 0, 0, size, tracking)[1]

    def path(self, text, x, y, size, fill, tracking=0.0, anchor="start"):
        if anchor == "end":
            x -= self.width(text, size, tracking)
        d, _ = self.layout(text, x, y, size, tracking)
        return f'<path d="{d}" fill="{fill}"/>'


SERIF = PathFont("InstrumentSerif-Regular.woff")
SERIF_I = PathFont("InstrumentSerif-Italic.woff")
SANS = PathFont("Inter-Regular.otf")
SANS_M = PathFont("Inter-Medium.otf")


def build():
    W, H, M = 1200, 590, 72
    parts = [f'<rect width="{W}" height="{H}" rx="20" fill="{PAPER}"/>']

    # top line
    parts.append(SANS_M.path(ROLE, M, 92, 14, INK, tracking=0.12))
    parts.append(SANS_M.path(PLACE, W - M, 92, 14, MUTED, tracking=0.12, anchor="end"))
    parts.append(f'<rect x="{M}" y="118" width="{W - 2*M}" height="1" fill="{RULE}"/>')

    # name
    size = 150
    parts.append(SERIF.path(NAME_1, M - 4, 274, size, INK, tracking=-0.012))
    w2 = SERIF_I.width(NAME_2, size, tracking=-0.012)
    parts.append(SERIF_I.path(NAME_2, M - 4, 412, size, INK, tracking=-0.012))
    parts.append(f'<circle cx="{M - 4 + w2 + 18:.1f}" cy="{412 - 10}" r="10" fill="{ACCENT}"/>')

    # lede, set to the right of the second line
    lx = M - 4 + w2 + 110
    for i, line in enumerate(LEDE):
        parts.append(SANS.path(line, lx, 350 + i * 31, 21, MUTED))

    # facts
    parts.append(f'<rect x="{M}" y="462" width="{W - 2*M}" height="1" fill="{RULE}"/>')
    col = (W - 2 * M) / len(FACTS)
    for i, (label, value) in enumerate(FACTS):
        x = M + i * col
        parts.append(SANS_M.path(label, x, 506, 12.5, MUTED, tracking=0.12))
        parts.append(SANS.path(value, x, 538, 19, INK))

    title = f"{NAME_1} {NAME_2}, {ROLE.title()}"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'role="img" aria-label="{title}"><title>{title}</title>' + "".join(parts) + "</svg>\n")
    assert "—" not in svg
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    return lx


if __name__ == "__main__":
    print("lede x:", round(build()))
