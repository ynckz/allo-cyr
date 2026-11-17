"""Проверка собранных шрифтов.

Сверяет скруглённые TTF с версией без скругления и печатает отклонения.
Ожидаемо: advance widths не меняются никогда; bbox может уменьшиться там,
где срезается острая вершина (у Allo с ROND=50 то же самое).
Код возврата 1, если что-то действительно сломалось.
"""
import pathlib
import sys

from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
TTF = ROOT / "out" / "ttf"
FACES = (("Regular", 400), ("Medium", 500), ("Bold", 700))
RU = range(0x0410, 0x0450)


def point_count(font, name):
    g = font["glyf"][name]
    if not g.numberOfContours:
        return 0
    return len(g.getCoordinates(font["glyf"])[0])


def main():
    failed = False

    print("=== скруглённый vs чистый ===")
    for sub, weight in FACES:
        plain_path = TTF / "plain" / f"AlloCyr-{sub}.ttf"
        round_path = TTF / f"AlloCyr-{sub}.ttf"
        if not plain_path.exists() or not round_path.exists():
            print(f"  {sub}: пропуск, нет файлов (сначала build.ps1)")
            failed = True
            continue
        a, b = TTFont(plain_path), TTFont(round_path)
        assert a.getGlyphOrder() == b.getGlyphOrder()
        bbox_changed = adv_changed = 0
        changed = untouched = 0
        for name in a.getGlyphOrder():
            if not name.startswith("uni04"):
                continue
            ga, gb = a["glyf"][name], b["glyf"][name]
            if (ga.xMin, ga.yMin, ga.xMax, ga.yMax) != (gb.xMin, gb.yMin, gb.xMax, gb.yMax):
                bbox_changed += 1
            if a["hmtx"][name][0] != b["hmtx"][name][0]:
                adv_changed += 1
            if point_count(a, name) != point_count(b, name):
                changed += 1
            else:
                untouched += 1
        print(
            f"  {sub:8}: изменено {changed}, без изменений {untouched}, "
            f"bbox срезан у {bbox_changed}, advance изменён у {adv_changed}"
        )
        failed |= adv_changed > 0
        a.close()
        b.close()

    print()
    print("=== целостность ===")
    for sub, weight in FACES:
        path = TTF / f"AlloCyr-{sub}.ttf"
        if not path.exists():
            failed = True
            continue
        f = TTFont(path)
        order = f.getGlyphOrder()
        cmap = f.getBestCmap()
        missing = [chr(c) for c in RU if c not in cmap]
        problems = []
        if len(order) != len(set(order)):
            problems.append("дубли имён")
        if f["maxp"].numGlyphs != len(order):
            problems.append("maxp != glyphOrder")
        if f["OS/2"].usWeightClass != weight:
            problems.append("usWeightClass")
        if missing:
            problems.append(f"нет {missing}")
        f.save(str(path) + ".tmp")
        pathlib.Path(str(path) + ".tmp").unlink()
        print(
            f"  {sub:8}: {len(order)} глифов, {len([u for u in cmap if 0x400 <= u <= 0x4FF])} кир., "
            f"weight {f['OS/2'].usWeightClass}, family "
            f"{f['name'].getDebugName(1)!r}/{f['name'].getDebugName(2)!r}"
            + ("  ОШИБКИ: " + ", ".join(problems) if problems else "  ок")
        )
        failed |= bool(problems)
        f.close()

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
