# UNDERTALE בעברית

תרגום מעריצים מלא של UNDERTALE לעברית. כל הטקסט במשחק: דיאלוגים, תפריטים, קרבות, חפצים, חנויות, שיחות טלפון, סופים וקרדיטים. התרגום כולל כתיבה מימין לשמאל, פונט עברי בסגנון הפיקסלים של המשחק, ותמונות עם טקסט שצוירו מחדש בעברית (הלוגו, שלטים, GAME OVER, כפתורי הקרב ועוד).

> זה פרויקט מעריצים לא רשמי. הוא לא קשור ל-Toby Fox. **המאגר לא כולל אף קובץ של המשחק.** הסקריפט בונה את הגרסה העברית מתוך העותק של המשחק שלכם.

## התקנה (Windows, גרסת Steam 1.08)

1. התקינו [Python 3](https://www.python.org/downloads/) וסמנו "Add python.exe to PATH".
2. הורידו את המאגר (Code > Download ZIP) וחלצו אותו.
3. סגרו את המשחק. אחר כך פתחו PowerShell בתיקייה והריצו:

```
powershell -ExecutionPolicy Bypass -File setup.ps1
```

הסקריפט עושה את הפעולות האלה:
- מוצא את המשחק.
- שומר גיבוי של `data.win` המקורי.
- מוריד את [UndertaleModTool](https://github.com/UnderminersTeam/UndertaleModTool) CLI 0.9.2.0 מהגרסה הרשמית שלו.
- בונה את העברית מהעותק שלכם ומתקין אותה.

אם המשחק מותקן במקום אחר, הוסיפו `-GameDir "<התיקייה של המשחק>"`.

הקובץ `data.win` של המשחק לא משתנה. העברית נשמרת בקובץ נפרד, `data_he.win`, ולכן הפעלה רגילה מ-Steam נשארת באנגלית. כדי לשחק בעברית:

```
powershell -ExecutionPolicy Bypass -File install.ps1 -Play
```

הסרת העברית:

```
powershell -ExecutionPolicy Bypass -File install.ps1 -Restore
```

השמירות שלכם לא משתנות. הגרסה העברית והאנגלית משתמשות באותן שמירות.

## English

A complete fan translation of UNDERTALE into Hebrew. It covers all of the game's text and draws it right to left. It also adds a Hebrew pixel font and Hebrew redraws of the images that contain English text.

**No game files are included.** `setup.ps1` does the following on your own Steam copy (v1.08, `data.win` SHA-256 `B718F822…C81C7`):
- backs up the original `data.win`;
- decompiles it with UndertaleModTool CLI 0.9.2.0, which it downloads from the official release;
- applies the Hebrew text, fonts, right-to-left rendering and image redraws;
- installs the result as a separate file, `data_he.win`, next to the untouched `data.win`.

Starting UNDERTALE from Steam stays English. Start Hebrew with `install.ps1 -Play`. Remove it with `install.ps1 -Restore`, which also undoes a v0.1.0 install that had replaced `data.win`.

## What's in the repo

| Path | What |
|---|---|
| `translation/he/*.json` | The Hebrew text (string id → Hebrew) |
| `translation/glossary.md`, `translation/VOICE_GUIDE.md` | Names, terms and how each character speaks |
| `scripts/` | Build pipeline: right-to-left GML scripts, font builder, image redraw scripts, UTMT scripts, the checker |
| `fonts/` | The Hebrew pixel font "אנדרטייל" |
| `screenshots/final/` | In-game screenshots |

Check the translation (after a setup run, which creates the English table): `python scripts/check_batch.py --all`

Check the built game for leftover English: `node scripts/coverage.js` (Node 18+, after `setup.ps1 -NoInstall`; or pass the original and Hebrew data files). It compares the original `data.win` with the Hebrew build directly, with no decompiler. It covers the text table and the English sentences hard-coded in game code. It exits 0 only when nothing is left except the reviewed exceptions in `translation/coverage-allowlist.json` (credits names, LV/HP, debug text, cut rooms; each has a reason). `--unused` lists text in objects that no room places (cut content). Release 0.2.0 checks 100%: 15,195 of 15,272 text-table entries are in Hebrew, and the other 77 stay Latin on purpose. Text inside images is covered by the sprite audit, not by this script.

### Launcher pack

`scripts/make_launcher_pack.ps1 -Version X.Y.Z` builds the Tirgumim launcher pack `build\undertale-he-X.Y.Z.zip`. The pack contains no game file. It holds a binary patch (bsdiff) from the original v1.08 `data.win` to the Hebrew build, plus the font licence. The launcher (0.4.0 or later) checks the player's `data.win` hash and writes the Hebrew game to a new file, `data_he.win`; `data.win` itself is never changed. Hebrew runs only when the launcher starts the game (through Steam, with `-game data_he.win`). Started from Steam, UNDERTALE stays English. The pack is for free launcher accounts only (`requiresAccount: false`).

The script runs `setup.ps1 -NoInstall` (use `-SkipBuild` to reuse an existing build). It then makes the patch with `scripts/bsdiff`, a small Rust tool built on the same `qbsdiff` crate the launcher uses, and checks that the patch reproduces the Hebrew file. Last, it writes `tirgumim-pack.json` with the `patches` entry and zips the pack. It needs Rust (`cargo`) in addition to what `setup.ps1` needs. The draft catalog entry is in `pack/catalog-entry.json`.

## Credits

- The Hebrew font is "אנדרטייל" (Undertale Hebrew) by EpicCreepuh, from [FontStruct](https://fontstruct.com/fontstructions/show/2752684/ndrtyyl-undertale-hebrew). It is under the SIL Open Font License; see `fonts/src_fontstruct/license.txt`.
- [UndertaleModTool](https://github.com/UnderminersTeam/UndertaleModTool) by the Underminers team.
- UNDERTALE © Toby Fox. Buy the game to play this translation.
