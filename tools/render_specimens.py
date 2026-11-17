"""Рендер всех PNG-спексименов в out/png (Pillow)."""
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
TTF = ROOT / "out" / "ttf"
PNG = ROOT / "out" / "png"
ALLO_OTF = ROOT / "vendor" / "allo" / "fonts" / "otf" / "Allo-Regular.otf"
INTER = ROOT / "vendor" / "inter" / "Inter-Regular.ttf"

BG, INK, MUT = "#f4f1ea", "#0d1b1a", "#8a8272"
LABEL = "segoeui.ttf"
FACES = (("400 Regular", "Regular"), ("500 Medium", "Medium"), ("700 Bold", "Bold"))


def font(path, size):
    return ImageFont.truetype(str(path), size)


def label(size=18):
    return ImageFont.truetype(LABEL, size)


def hero():
    W, H = 1400, 980
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    cyr = TTF / "AlloCyr-Regular.ttf"

    y = 30
    d.text((40, y), "Allo Cyr — латиница и кириллица одним шрифтом", font=font(cyr, 22), fill=MUT)
    y += 50
    d.text((40, y), "ynckz / ckzyn / ункз", font=font(cyr, 72), fill=INK)
    y += 100
    d.text((40, y), "Съешь же ещё этих мягких французских булок, да выпей чаю.", font=font(cyr, 40), fill=INK)
    y += 60
    d.text((40, y), "Широкая электрификация южных губерний даст мощный толчок.", font=font(cyr, 40), fill=INK)
    y += 60
    d.text((40, y), "Ёжик в тумане: ЁЁЁ ёёё · Щука, Цапля, Жук · 0123456789", font=font(cyr, 40), fill=INK)

    y += 90
    d.text((40, y), "для сравнения — кириллица Inter как есть:", font=label(16), fill=MUT)
    y += 30
    d.text((40, y), "унказ Съешь ещё этих мягких французских булок", font=font(INTER, 40), fill="#3a4a45")

    y += 80
    d.text((40, y), "оригинальный Allo без кириллицы:", font=label(16), fill=MUT)
    y += 30
    d.text((40, y), "ynckz / ckzyn / ", font=font(ALLO_OTF, 40), fill="#3a4a45")
    x = 40 + d.textlength("ynckz / ckzyn / ", font=font(ALLO_OTF, 40))
    d.text((x, y), "ункз", font=font("segoeui.ttf", 40), fill="#b03a2e")

    y += 70
    d.text((40, y), "алфавит, 22px:", font=label(16), fill=MUT)
    y += 28
    d.text((40, y), "А Б В Г Д Е Ё Ж З И Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ъ Ы Ь Э Ю Я", font=font(cyr, 22), fill=INK)
    y += 34
    d.text((40, y), "а б в г д е ё ж з и й к л м н о п р с т у ф х ц ч ш щ ъ ы ь э ю я", font=font(cyr, 22), fill=INK)

    img.save(PNG / "hero.png")
    print("  hero.png")


def weights():
    W, ROW = 1900, 190
    text = "Н К Ж Ю Я У З Д Л Ц Щ"
    size = 104
    H = 120 + len(FACES) * 2 * ROW + 340
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((40, 24), "Allo Cyr — скругление углов по мотивам Allo ROND=50, 104 px", font=label(19), fill=MUT)

    y = 70
    for title, sub in FACES:
        for state, folder in (("до", "plain"), ("после", None)):
            path = TTF / folder / f"AlloCyr-{sub}.ttf" if folder else TTF / f"AlloCyr-{sub}.ttf"
            d.text((40, y + 8), f"{title} — {state}", font=label(17), fill=MUT)
            d.text((300, y), text, font=font(path, size), fill=INK)
            y += ROW
        y += 14

    y += 16
    d.text((40, y), "Текст после скругления", font=label(17), fill=MUT)
    y += 30
    for sub, txt in (
        ("Regular", "Съешь же ещё этих мягких французских булок, да выпей чаю."),
        ("Medium", "Широкая электрификация южных губерний даст мощный толчок."),
        ("Bold", "Ёжик в тумане: Щука, Цапля, Жук · 0123456789 — Hello"),
    ):
        d.text((40, y), txt, font=font(TTF / f"AlloCyr-{sub}.ttf", 40), fill=INK)
        y += 52
    d.text((40, y), "24 px: В чащах юга жил бы цитрус? Да, но фальшивый экземпляр.", font=font(TTF / "AlloCyr-Regular.ttf", 24), fill=INK)
    y += 34
    d.text((40, y), "14 px: В чащах юга жил бы цитрус? Да, но фальшивый экземпляр.", font=font(TTF / "AlloCyr-Regular.ttf", 14), fill=INK)

    img.save(PNG / "weights.png")
    print("  weights.png")


def zh():
    img = Image.new("RGB", (1000, 1320), BG)
    d = ImageDraw.Draw(img)
    rows = (
        ("Regular ж — до", TTF / "plain" / "AlloCyr-Regular.ttf"),
        ("Regular ж — после", TTF / "AlloCyr-Regular.ttf"),
        ("Bold ж — до", TTF / "plain" / "AlloCyr-Bold.ttf"),
        ("Bold ж — после", TTF / "AlloCyr-Bold.ttf"),
    )
    for i, (title, path) in enumerate(rows):
        y = i * 320 + 30
        d.text((30, y), title, font=label(18), fill=MUT)
        d.text((30, y + 26), "ж", font=font(path, 260), fill=INK)
    img.save(PNG / "zh.png")
    print("  zh.png")


def grids():
    from fontTools.ttLib import TTFont

    def one(path, title, out_name):
        f = TTFont(path)
        codes = [c for c in range(0x0400, 0x0500) if c in f.getBestCmap()]
        f.close()
        cols, cell = 16, 88
        rows = (len(codes) + cols - 1) // cols
        img = Image.new("RGB", (cols * cell + 40, rows * cell + 80), BG)
        d = ImageDraw.Draw(img)
        d.text((20, 16), title, font=label(18), fill=MUT)
        fnt = font(path, 58)
        for i, code in enumerate(codes):
            d.text((20 + (i % cols) * cell, 52 + (i // cols) * cell), chr(code), font=fnt, fill=INK)
        img.save(PNG / out_name)
        print(f"  {out_name} ({len(codes)} глифов)")

    one(TTF / "plain" / "AlloCyr-Regular.ttf", "U+0400-04FF, Regular — до скругления", "grid_before.png")
    one(TTF / "AlloCyr-Regular.ttf", "U+0400-04FF, Regular — после скругления", "grid_after.png")


def main():
    PNG.mkdir(parents=True, exist_ok=True)
    print("out/png:")
    hero()
    weights()
    zh()
    grids()


if __name__ == "__main__":
    main()
