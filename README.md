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

חזרה לאנגלית:

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
- installs the result.

To go back to English, run `install.ps1 -Restore`.

## What's in the repo

| Path | What |
|---|---|
| `translation/he/*.json` | The Hebrew text (string id → Hebrew) |
| `translation/glossary.md`, `translation/VOICE_GUIDE.md` | Names, terms and how each character speaks |
| `scripts/` | Build pipeline: right-to-left GML scripts, font builder, image redraw scripts, UTMT scripts, the checker |
| `fonts/` | The Hebrew pixel font "אנדרטייל" |
| `screenshots/final/` | In-game screenshots |

Check the translation (after a setup run, which creates the English table): `python scripts/check_batch.py --all`

## Credits

- The Hebrew font is "אנדרטייל" (Undertale Hebrew) by EpicCreepuh, from [FontStruct](https://fontstruct.com/fontstructions/show/2752684/ndrtyyl-undertale-hebrew). It is under the SIL Open Font License; see `fonts/src_fontstruct/license.txt`.
- [UndertaleModTool](https://github.com/UnderminersTeam/UndertaleModTool) by the Underminers team.
- UNDERTALE © Toby Fox. Buy the game to play this translation.
