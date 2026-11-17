"""Allo + кириллица из Inter -> статические Allo Cyr (Regular / Medium / Bold).

Метрики у Allo и Inter совпадают (UPM 2048, xHeight 1118, cap 1490),
поэтому контуры переносятся без масштабирования: копирование + cmap.
Затем кириллице ставится скругление углов в стиле Allo ROND=50.

Запуск (из корня репозитория):
    python build/merge.py                 # все начертания, со скруглением
    python build/merge.py Bold            # только Bold
    python build/merge.py --no-round      # без скругления
    python build/merge.py --out=DIR       # в другую папку
"""

import pathlib
import sys

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

import rounding

ROOT = pathlib.Path(__file__).resolve().parent.parent
ALLO_VAR = ROOT / "vendor" / "allo" / "fonts" / "variable" / "AlloVariable.ttf"
INTER_DIR = ROOT / "vendor" / "inter"
OUT = ROOT / "out" / "ttf"

# Allo weight -> (Inter source того же веса, радиус скругления на 90°)
FACES = {
    "Regular": (400, "Inter-Regular.ttf", 65.0),
    "Medium": (500, "Inter-Medium.ttf", 79.5),
    "Bold": (700, "Inter-Bold.ttf", 108.06),
}

INTER_COPYRIGHT = (
    "Cyrillic glyphs derived from Inter 4.1, Copyright (c) 2016 "
    "The Inter Project Authors (https://github.com/rsms/inter), SIL OFL 1.1."
)

AXES = {"opsz": 14, "ROND": 50}


def pin_axes(font, wght):
    instantiateVariableFont(font, {**AXES, "wght": wght}, inplace=True, updateFontNames=False)
    assert "fvar" not in font, "fvar still present: not all axes were pinned"
    return font


def copy_cyrillic(src, dst):
    src_cmap = src.getBestCmap()
    dst_cmap = dst.getBestCmap()
    src_gs = src.getGlyphSet()
    src_hmtx = src["hmtx"]

    glyf = dst["glyf"]
    hmtx = dst["hmtx"]
    taken = set(dst.getGlyphOrder())

    copied = []
    for code in range(0x0400, 0x0500):
        if code not in src_cmap or code in dst_cmap:
            continue
        src_name = src_cmap[code]
        rec = DecomposingRecordingPen(src_gs)
        src_gs[src_name].draw(rec)

        pen = TTGlyphPen(None)
        rec.replay(pen)
        glyph = pen.glyph()
        glyph.recalcBounds(glyf)

        new_name = f"uni{code:04X}"
        if new_name in taken:
            new_name += ".cyr"
        taken.add(new_name)

        glyf[new_name] = glyph
        hmtx[new_name] = (src_hmtx[src_name][0], glyph.xMin)
        copied.append((code, new_name))

    # glyf сам дописывает новые имена в свой glyphOrder; если вызвать
    # setGlyphOrder после, fontTools задвоит их. Поэтому берём порядок из glyf.
    dst.glyphOrder = list(glyf.glyphOrder)
    for table in dst["cmap"].tables:
        if table.isUnicode():
            for code, name in copied:
                table.cmap[code] = name
    return copied


def set_names(font, subfamily):
    name = font["name"]
    family = "Allo Cyr"
    full = f"{family} {subfamily}"
    ps = f"AlloCyr-{subfamily}"

    old_copyright = (name.getDebugName(0) or "").strip()
    values = {
        0: (old_copyright + " " + INTER_COPYRIGHT).strip(),
        1: family,
        2: subfamily,
        3: f"{full}: 1.0; merged cyrillic test",
        4: full,
        6: ps,
        16: family,
        17: subfamily,
    }
    for name_id, value in values.items():
        name.setName(value, name_id, 3, 1, 0x409)
        name.setName(value, name_id, 1, 0, 0)


def set_weight(font, weight):
    font["OS/2"].usWeightClass = weight
    font["OS/2"].ulUnicodeRange1 |= 1 << 2  # Cyrillic
    font["OS/2"].ulCodePageRange1 |= 1 << 2  # Cyrillic (IBM 866)

    fs = font["OS/2"].fsSelection
    fs &= ~((1 << 5) | (1 << 6))  # clear bold / regular
    if weight >= 700:
        fs |= 1 << 5
    elif weight == 400:
        fs |= 1 << 6
    font["OS/2"].fsSelection = fs

    mac = font["head"].macStyle
    mac = (mac | 1) if weight >= 700 else (mac & ~1)
    font["head"].macStyle = mac


def build_face(subfamily, do_round=True, out_dir=None):
    weight, inter_file, radius = FACES[subfamily]
    inter_path = INTER_DIR / inter_file
    if not inter_path.exists():
        sys.exit(f"missing {inter_path}; run build/fetch-sources.ps1")

    base = TTFont(ALLO_VAR)
    pin_axes(base, weight)

    src = TTFont(inter_path)
    copied = copy_cyrillic(src, base)
    src.close()

    arcs = touched = 0
    if do_round:
        for _code, glyph_name in copied:
            n = rounding.round_glyph(base, glyph_name, radius)
            if n:
                touched += 1
                arcs += n

    set_names(base, subfamily)
    set_weight(base, weight)
    # STAT остаётся от вариативного шрифта и сбивает с толку редакторы,
    # которые ищут оси у статика.
    if "STAT" in base:
        del base["STAT"]

    target_dir = pathlib.Path(out_dir) if out_dir else OUT
    target_dir.mkdir(parents=True, exist_ok=True)
    out = target_dir / f"AlloCyr-{subfamily}.ttf"
    base.save(out)
    base.close()
    rounds = f", rounded {touched}/{len(copied)} ({arcs} arcs @ d={radius})" if do_round else ", no rounding"
    print(f"{subfamily:8} wght {weight}: {len(copied)} cyr glyphs{rounds} -> {out} ({out.stat().st_size} B)")


def main():
    if not ALLO_VAR.exists():
        sys.exit(f"missing {ALLO_VAR}; run build/fetch-sources.ps1")
    out_dir = None
    args = []
    for a in sys.argv[1:]:
        if a.startswith("--out="):
            out_dir = a.split("=", 1)[1]
        elif not a.startswith("--"):
            args.append(a)
    do_round = "--no-round" not in sys.argv
    wanted = args or list(FACES)
    unknown = [w for w in wanted if w not in FACES]
    if unknown:
        sys.exit(f"unknown faces: {unknown}; choose from {list(FACES)}")
    for subfamily in wanted:
        build_face(subfamily, do_round, out_dir)


if __name__ == "__main__":
    main()
