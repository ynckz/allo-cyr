"""Замер радиуса скругления d на мастерах Allo (opsz 14, ROND 0 vs 50).

Печатает таблицу: для каждого веса берёт несколько глифов с плоским верхом,
находит точку касания на верхней кромке и считает d = x_касания - xMin.
"""
import pathlib

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
ALLO_VAR = ROOT / "vendor" / "allo" / "fonts" / "variable" / "AlloVariable.ttf"

WEIGHTS = (400, 500, 700)
GLYPHS = "HTFKI"


def instance(wght, rond):
    f = TTFont(ALLO_VAR)
    instantiateVariableFont(
        f, {"opsz": 14, "wght": wght, "ROND": rond}, inplace=True, updateFontNames=False
    )
    return f


def oncurve(font, ch):
    """Только on-curve точки (последний аргумент каждой команды пера)."""
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(ch)]
    rec = DecomposingRecordingPen(gs)
    gs[name].draw(rec)
    return [args[-1] for op, args in rec.value if op in ("moveTo", "lineTo", "curveTo", "qCurveTo") and args]


def d_top_left(font, ch):
    pts = oncurve(font, ch)
    xmin, ymax = min(p[0] for p in pts), max(p[1] for p in pts)
    top = sorted(p[0] for p in pts if abs(p[1] - ymax) < 0.6)
    return top[0] - xmin


def stem(font, ch):
    pts = oncurve(font, ch)
    ymin = min(p[1] for p in pts)
    bottom = sorted({round(p[0], 3) for p in pts if abs(p[1] - ymin) < 0.6})
    return bottom[1] - bottom[0]


print(f"{'вес':>5}  {'глиф':>4}  {'stem':>7}  {'d':>8}  {'d/stem':>7}")
for wght in WEIGHTS:
    f0, f50 = instance(wght, 0), instance(wght, 50)
    for ch in GLYPHS:
        s, d = stem(f0, ch), d_top_left(f50, ch)
        print(f"{wght:>5}  {ch:>4}  {s:>7.1f}  {d:>8.3f}  {d / s:>7.4f}")
    f0.close()
    f50.close()
