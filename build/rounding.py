"""Скругление углов в стиле Allo ROND=50 для TrueType-контуров.

Параметры сняты с мастеров Allo (opsz 14, ROND 0 vs 50):

    вес   d (units)   d / stem
    400      65.0       0.346
    500      79.5       0.351
    700     108.06      0.357

d - расстояние от вершины до точки касания вдоль каждого из двух прямых
отрезков. Скругляются только выпуклые стыки двух ПРЯМЫХ отрезков на внешних
контурах; вогнутые стыки, все кривые и внутренние контуры (счётчики)
остаются как есть. Управляющие точки кубики стоят на 0.2613*d от вершины,
что почти совпадает с круговой дугой (для 90°: 0.2613 против 0.2652).

Кубика угла переводится в квадратики через fontTools.cu2qu; остальные
сегменты глифа переносятся без изменений (квадратики остаются квадратиками).
"""

import math

from fontTools.cu2qu import curve_to_quadratic
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

# радиус на 90° в юнитах: замерен на инстансах AlloVariable при opsz 14
R_BY_WEIGHT = {400: 65.0, 500: 79.5, 700: 108.06}

K90 = 0.261315          # управляющие точки на 90° (доля от d)
FLOOR, CAP = 0.8, 2.0   # ограничение d для острых/тупых углов, в долях r
MIN_TURN = 5.0          # градусы: почти прямые стыки не трогаем
MIN_D = 2.0             # юниты: совсем мелкие скругления пропускаем
MAX_ERR = 1.0           # ошибка перевода кубики угла в квадратики, юниты


def k_for(turn_deg):
    """Доля d для управляющих точек; подогнано под мастера Allo."""
    return max(0.18, min(0.52, K90 + 0.0054 * (turn_deg - 90.0)))


def parse(rec):
    """Запись пера -> список замкнутых контуров из сегментов.

    Сегмент: (kind, start, end, args)
      "line"   -> args is None
      "qcurve" -> args is the original qCurveTo tuple
      "curve"  -> args is the original curveTo tuple
    Контур замкнут: у последнего сегмента end == start первого.
    """
    contours, cur, start = [], None, None
    for op, args in rec.value:
        if op == "moveTo":
            if cur:
                contours.append(cur)
            cur, start = [], args[0]
        elif cur is None:
            continue
        elif op == "lineTo":
            cur.append(("line", cur[-1][2] if cur else start, args[0], None))
        elif op == "qCurveTo":
            cur.append(("qcurve", cur[-1][2] if cur else start, args[-1], args))
        elif op == "curveTo":
            cur.append(("curve", cur[-1][2] if cur else start, args[-1], args))
        elif op in ("closePath", "endPath"):
            if cur:
                if cur[-1][2] != start:
                    cur.append(("line", cur[-1][2], start, None))
                contours.append(cur)
            cur = None
    if cur:
        contours.append(cur)
    return contours


def signed_area(cont):
    """Площадь по опорным точкам; знак = направление обхода (TT: <0 наружу)."""
    a = 0.0
    for _kind, p0, p1, _args in cont:
        a += p0[0] * p1[1] - p1[0] * p0[1]
    return a / 2.0


def fillet(cont, r):
    """Возвращает новый контур со скруглениями в выпуклых прямых углах."""
    n = len(cont)
    if n < 3 or signed_area(cont) >= 0:  # >=0: дырка/счётчик, не трогаем
        return cont

    rounds = {}
    for i in range(n):
        prev, nxt = cont[i - 1], cont[i]
        if prev[0] != "line" or nxt[0] != "line":
            continue
        ax, ay = prev[1]
        bx, by = prev[2]
        cx, cy = nxt[2]
        if (bx, by) != nxt[1]:
            continue
        ux, uy = bx - ax, by - ay
        vx, vy = cx - bx, cy - by
        lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
        if lu < 1e-6 or lv < 1e-6:
            continue
        ux, uy, vx, vy = ux / lu, uy / lu, vx / lv, vy / lv
        cross = ux * vy - uy * vx
        if cross >= 0:  # вогнутый стык (у внешнего контура TT обход по часовой)
            continue
        turn = math.degrees(math.acos(max(-1.0, min(1.0, ux * vx + uy * vy))))
        if turn < MIN_TURN:
            continue
        theta = math.pi - math.radians(turn)
        d = r / math.tan(theta / 2) if theta > 1e-3 else CAP * r
        d = max(FLOOR * r, min(CAP * r, d))
        d = min(d, 0.5 * lu, 0.5 * lv)
        if d < MIN_D:
            continue
        h = k_for(turn) * d
        rounds[i] = (
            (bx - ux * d, by - uy * d),   # T0: конец предыдущего отрезка
            (bx + vx * d, by + vy * d),   # T1: начало следующего
            (bx - ux * h, by - uy * h),   # P1
            (bx + vx * h, by + vy * h),   # P2
        )

    if not rounds:
        return cont

    segs = [list(s) for s in cont]
    for i, (t0, t1, _p1, _p2) in rounds.items():
        segs[i - 1][2] = t0
        segs[i][1] = t1

    out = []
    for i, seg in enumerate(segs):
        out.append(seg)
        j = (i + 1) % n
        if j in rounds:
            t0, t1, p1, p2 = rounds[j]
            out.append(("qarc", t0, t1, (p1, p2)))
    return out


def _emit(pen, cont):
    pen.moveTo(cont[0][1])
    for kind, _p0, p1, args in cont:
        if kind == "line":
            pen.lineTo(p1)
        elif kind == "qcurve":
            pen.qCurveTo(*args)
        elif kind == "curve":
            pen.curveTo(*args)
        elif kind == "qarc":
            quad = curve_to_quadratic(
                (_p0, args[0], args[1], p1), max_err=MAX_ERR
            )
            pen.qCurveTo(*quad[1:])
    pen.closePath()


def round_glyph(font, name, r):
    """Скругляет глиф name в шрифте font. Возвращает число дуг (0 = без изменений)."""
    gs = font.getGlyphSet()
    rec = DecomposingRecordingPen(gs)
    gs[name].draw(rec)

    contours = parse(rec)
    new = [fillet(c, r) for c in contours]
    arcs = sum(1 for c in new for s in c if s[0] == "qarc")
    if not arcs:
        return 0

    pen = TTGlyphPen(None)
    for c in new:
        _emit(pen, c)
    glyph = pen.glyph()
    glyph.recalcBounds(font["glyf"])

    glyf = font["glyf"]
    glyf[name] = glyph
    advance = font["hmtx"][name][0]
    font["hmtx"][name] = (advance, glyph.xMin)
    return arcs
