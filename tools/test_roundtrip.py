"""Регресс-тест rounding.parse + rounding._emit: без фаски контур
должен воспроизводиться точка-в-точку (иначе кривые «плывут» при сборке).
"""
import pathlib
import sys

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build"))

import rounding  # noqa: E402

INTER = ROOT / "vendor" / "inter" / "Inter-Regular.ttf"
CHARS = "онЁжюяАМ"


def coords(font, name):
    arr, _ends, flags = font["glyf"][name].getCoordinates(font["glyf"])
    return [(int(x), int(y), flags[i] & 1) for i, (x, y) in enumerate(arr)]


def main():
    orig = TTFont(INTER)
    out = TTFont(INTER)
    cmap = orig.getBestCmap()
    bad = 0
    for ch in CHARS:
        name = cmap[ord(ch)]
        rec = DecomposingRecordingPen(orig.getGlyphSet())
        orig.getGlyphSet()[name].draw(rec)
        pen = TTGlyphPen(None)
        for cont in rounding.parse(rec):
            rounding._emit(pen, cont)
        glyph = pen.glyph()
        glyph.recalcBounds(out["glyf"])
        out["glyf"][name] = glyph

        before, after = coords(orig, name), coords(out, name)
        ok = before == after
        bad += not ok
        print(f"  {ch} {name:10}: {len(before)} точек, идентично={ok}")

    orig.close()
    out.close()
    print("ок" if not bad else f"ПРОВАЛ: {bad} глиф(ов) изменились")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
