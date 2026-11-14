# Translator brief (for each batch)

You are translating part of UNDERTALE into Hebrew for a personal fan patch of the user's own copy.
Workspace: the repo root (all paths below are relative to it).

1. Read `translation/glossary.md` in full first. It is binding: names, places, items, terms, voices and the technical rules.
2. Input: `translation/batches/bNN_in.json`, a list of {id, en, max, face, where}, in game-table order,
   so neighbouring strings usually belong to the same scene. `where` names the game objects/scripts
   that show the string, which tells you who is speaking (e.g. `obj_papyrus...`, `scr_papcall` = Papyrus
   on the phone, `obj_sans...`, `SCR_TEXT` = mixed). `max` is the widest allowed line (in cells).
   Use your knowledge of Undertale's story and characters to get the speaker, tone and scene right.
3. Output: `translation/he/bNN.json`, ONE JSON object mapping every input id to its Hebrew string,
   e.g. {"SCR_TEXT_291": "\W* היי^2!&* ..."}. JSON escaping: every backslash in a game code is
   doubled in the file (`\E0` is written `"\E0"`). Double quotes inside a string are written `\"`.
   For large batches it's fine to write parts (`translation/he/bNN_part1.json`, `..._part2.json`) and then merge
   them into `bNN.json` with a small Python one-liner, then delete the part files.
4. Natural, idiomatic, modern Hebrew that keeps each character's voice and humour. Not a word-for-word
   translation. Hebrew is usually shorter than English; use the room.
5. Run `python scripts/check_batch.py translation/he/bNN.json` (set PYTHONIOENCODING=utf-8) and fix every E-* error
   until it prints BATCH PASS. W-* warnings are fine when intentional (e.g. a Latin name).
6. Write any new recurring term or important choice to `translation/notes/bNN_notes.md` (don't edit glossary.md).
7. Don't touch any other files. Don't run the game.
8. Finish with a short report: ids translated, checker result, and notes worth knowing (choices, doubtful spots).
