# Sprite redraw brief

We are translating UNDERTALE into Hebrew. All dialogue and menus are done. The remaining job is the
images that show English words. Workspace: the repo root.

## Your input

You get one audit file: `translation/audit_sprites_{a,b,c}.json`. Each entry gives a sprite or background
name, the frames with text, what it says, its size and style notes.

## Tools

- **`scripts/sprite_text.py`** is the shared helper library; read its docstring. Its functions:
  - `load_sprite(name, frame)` gives a full-size frame and exports missing frames on demand. `load_bg(name)` loads a background.
  - `clear(im, box)` erases old text, filling with the surrounding colour.
  - `text_image(text, scale, color, outline, letter_gap, align)` renders Hebrew in the game's pixel font. Give the text in
    normal typing (logical) order: right-to-left layout and Latin/digit runs are handled for you.
  - `fit_scale`, `paste`, `paste_center`.
  - `save_sprite(im, name, frame)` / `save_bg(im, name)` write into `fonts/sprites/` and `fonts/backgrounds/`, where the build picks them up.
  - `preview([...], out)` builds a check image.
- **Your script:** write ONE Python script `scripts/sprites/redraw_<a|b|c>.py` that produces all your images, so the
  work can be re-run. Run it with `python scripts/sprites/redraw_<x>.py`.

## Rules

- **Keep each image's exact size, and every non-text pixel.** Only replace the words.
  - Measure the text's bounding box yourself by looking at pixels: find the text colour, then compute the box with PIL.
  - Clear just that box with `clear(...)`, sampling the right background.
  - For text on a busy background (posters, tilesets), clear tightly and re-fill with the local background colour or
    pattern. If a sign has a plain plate, refill the plate.
- **Match the style:**
  - Use the same colour as the old text. Use an outline/shadow if the old text had one.
  - Size it like the original: about the same height, centred where the old word was.
  - If a word is too long, use `scale=(sx, sy)` with a smaller x scale, or `letter_gap=0`, or a shorter Hebrew word.
- **Animation frames:** do all frames that contain the text, and keep them consistent (same position frame to frame).
  - For coloured/selected variants (e.g. orange vs yellow), use each frame's own colour.
- **Translation and wording:**
  - Use `translation/glossary.md` for names, places and terms.
  - Match the in-game dialogue that refers to the image. Search `translation/he/*.json` for the Hebrew already used, e.g.
    Grillby's = "אצל גרילבי", Snowdin = "סנודין", the misspelled LIBRARBY sign: check how the dialogue jokes about it and
    misspell the Hebrew the same way.
  - Keep short and punchy.
  - Keep a typo where the English has a deliberate typo.
- **Stay in Latin (don't redraw):**
  - keyboard key letters (Z, X, C) and controller button pictures;
  - "LV", "HP", "KR", "EXP", "MTT", "G" (gold) and digits;
  - the quiz / door / marker letters A, B, C, D, X (the dialogue keeps these letters);
  - "Zzz" sleep marks;
  - developer placeholder art that isn't used in the real game.
  - The battle buttons FIGHT/ACT/ITEM/MERCY main variants (`spr_fightbt*`, `spr_actbt_center*`, `spr_talkbt*`,
    `spr_itembt*`, `spr_sparebt*`) are ALREADY done by `scripts/build_buttons.py`. Skip them.
- **The UNDERTALE title logo:** redraw it as a Hebrew logo "אנדרטייל" in the same chunky white style, with the red
  heart in place of a letter if it fits naturally. If it can't look good, leave it and say why.
- **Check your work:** look at every result with `preview(...)` and the Read tool, original next to new.
  - The Hebrew must read correctly right to left.
  - Nothing outside the text may change, and nothing may be cut off.
- **Files:** don't edit files other than your script, your outputs in `fonts/sprites` and `fonts/backgrounds`, and your
  notes `translation/notes/sprites_<x>.md`.
  - The notes list each image: the Hebrew used, or "kept" plus the reason.
  - Don't run the game or the build.

Finish with a short report: what you redrew, what you kept, and anything that looked weak.
