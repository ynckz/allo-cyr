"""Сабсеты woff2 для веба из собранных TTF.

    RU   - латиница + русская кириллица + типографская пунктуация
    full - весь шрифт (вся кириллица U+0400-04FF и все фичи)
"""

import pathlib
import shutil

from fontTools import subset

ROOT = pathlib.Path(__file__).resolve().parent.parent
TTF = ROOT / "out" / "ttf"
WEB = ROOT / "out" / "web"
VENDOR = ROOT / "vendor"

FACES = ("Regular", "Medium", "Bold")
RU_UNICODES = (
    "U+0020-007E,U+00A0-00FF,U+0400-045F,U+2010-2027,U+2030,"
    "U+2039-203A,U+2116,U+2122"
)


def woff2(src, dst, unicodes):
    dst.parent.mkdir(parents=True, exist_ok=True)
    subset.main(
        [
            str(src),
            f"--output-file={dst}",
            "--flavor=woff2",
            f"--unicodes={unicodes}",
            "--layout-features=*",
            "--no-hinting",
        ]
    )
    print(f"  {dst.relative_to(ROOT)}  {dst.stat().st_size} B")


def main():
    WEB.mkdir(parents=True, exist_ok=True)
    for sub in FACES:
        ttf = TTF / f"AlloCyr-{sub}.ttf"
        if not ttf.exists():
            raise SystemExit(f"missing {ttf}; run build/merge.py first")
        print(sub)
        woff2(ttf, WEB / f"AlloCyr-{sub}.woff2", RU_UNICODES)
        woff2(ttf, WEB / f"AlloCyr-{sub}-full.woff2", "*")

    plain_ttf = TTF / "plain" / "AlloCyr-Regular.ttf"
    if plain_ttf.exists():
        print("plain Regular")
        woff2(plain_ttf, WEB / "plain" / "AlloCyr-Regular.woff2", RU_UNICODES)

    # для демо-страницы: оригинальная латиница Allo и чистая кириллица Inter
    shutil.copy2(
        VENDOR / "allo" / "fonts" / "webfonts" / "Allo-Regular.woff2",
        WEB / "Allo-Regular.woff2",
    )
    woff2(VENDOR / "inter" / "Inter-Regular.ttf", WEB / "Inter-Cyr-RU.woff2", "U+0400-045F")
    print("done")


if __name__ == "__main__":
    main()
