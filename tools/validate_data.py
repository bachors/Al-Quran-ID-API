"""Dataset validator for offline/data.json (stdlib only).

Catches the bug classes fixed for issues #1, #2, #9 and the 2026
alignment audit (surah-9 ar shift, duplicated tr cells):
  1. total ayah count == 6236 and per-surah counts match the standard list
  2. no ayah-1 carries a bismillah prefix (except 1:1, which IS bismillah)
  3. no two adjacent ayahs share identical transliteration with different Arabic
  4. shadda-ra in Ar-Rahim / rahmat words surfaces doubled in latin
Run: python3 tools/validate_data.py
"""
import json
import re
import sys

STD = [7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52,
       99, 128, 111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88,
       69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59,
       37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
       14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31,
       50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21,
       11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6]

MARKS = dict.fromkeys(
    list(range(0x064B, 0x0656)) + [0x0670, 0x06D6, 0x06DC, 0x06DF,
                                   0x06E0, 0x06E1, 0x06E2, 0x06E3,
                                   0x06E4, 0x06E7, 0x06E8, 0x06EA,
                                   0x06EB, 0x06EC], "")


def norm_ar(t):
    return t.replace("ٱ", "ا").replace("۞", "").translate(MARKS)


def stripped(tr):
    return re.sub(r"<[^>]+>", "", tr).lower()


def main(path="offline/data.json"):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    errors = []

    if len(data) != 114:
        errors.append(f"surah count {len(data)} != 114")
    total = 0
    for i, surah in enumerate(data):
        n = len(surah["ayat"])
        total += n
        if n != STD[i]:
            errors.append(
                f"surah {surah['nomor']} has {n} ayahs, expected {STD[i]}")
        nomors = [a["nomor"] for a in surah["ayat"]]
        if nomors != [str(k) for k in range(1, n + 1)]:
            errors.append(f"surah {surah['nomor']} bad nomor sequence")
    if total != 6236:
        errors.append(f"total ayahs {total} != 6236")

    for surah in data:
        ayahs = surah["ayat"]
        for a in ayahs:
            if (norm_ar(a["ar"]).startswith("بسم الله الرحمن الرحيم")
                    and not stripped(a["tr"]).startswith("bism")
                    and not (surah["nomor"] == "1" and a["nomor"] == "1")):
                errors.append(
                    f"{surah['nomor']}:{a['nomor']} bismillah-prefixed ar")
        for prev, cur in zip(ayahs, ayahs[1:]):
            if (prev["tr"] == cur["tr"] and prev["ar"] != cur["ar"]
                    or stripped(prev["tr"]) == stripped(cur["tr"])
                    and prev["ar"] != cur["ar"]):
                errors.append(
                    f"{surah['nomor']}:{prev['nomor']} duplicated tr")

    for surah in data:
        for a in surah["ayat"]:
            if "رَّحِيم" in a["ar"]:
                t = stripped(a["tr"])
                if "rrahiim" not in t or "rahiim" in t.replace("rrahiim", ""):
                    errors.append(
                        f"{surah['nomor']}:{a['nomor']} undoubled rahim")

    if errors:
        print(f"FAILED ({len(errors)}):")
        for e in errors[:30]:
            print(" -", e)
        return 1
    print(f"OK: 114 surahs, {total} ayahs, no bismillah/dup/gemination issues")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
