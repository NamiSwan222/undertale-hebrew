// Coverage check: lists every piece of English the Hebrew build still shows.
//   node scripts/coverage.js [original data.win] [Hebrew data.win] [--unused]
// Defaults: backup/data.win.orig and build/data.win (what setup.ps1 makes). Needs Node 18+, no packages.
// Exit code 0 only at 100% (nothing left except reviewed entries in patch/coverage-allowlist.json).
//
// What it checks:
//  1. The text table (gml_Script_textdata_en, all 16,455 dialogue/menu/item/battle strings): an entry is
//     untranslated when its English has a Latin word and the Hebrew build's value has no Hebrew letter.
//  2. Text hard-coded in game code (outside the text table): an English sentence-like literal that is still in the
//     same code entry of the Hebrew build. Code of objects that no room places is reported separately as unused.
// Not checked by machine: text drawn inside images (sprites/backgrounds); see README.
const fs = require('fs');
const path = require('path');
const gm = require('./gmdata');

const ALLOW = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'translation', 'coverage-allowlist.json'), 'utf8'));
const CONTROL = /\\\[.\]|\\[A-Za-z*>][0-9A-Za-z]?|\^\d|\/%*|%%+|&|#/g;

const hasLatinWord = (s) => /[A-Za-z]{2,}/.test(s.replace(CONTROL, ' '));
const hasHebrew = (s) => /[א-ת]/.test(s);
const looksLikeText = (s) =>
  (/^\* \S/.test(s) || /[A-Za-z]{2,}[,.'!?]* +[A-Za-z]{2,}/.test(s)) &&
  !/^(gml_|obj_|spr_|scr_|snd_|mus_|room_)/.test(s) &&
  !/^[\w./-]+\.(ogg|ini|png|gif|exe|txt|dat)$/i.test(s);

function placedObjects(d) {
  const b = d.buf;
  const name = (p) => d.str.strings[d.str.byAddr.get(b.readUInt32LE(p))];
  const list = (c) => {
    const s = d.ch[c].start;
    return Array.from({ length: b.readUInt32LE(s) }, (_, i) => b.readUInt32LE(s + 4 + i * 4));
  };
  const objects = list('OBJT').map(name);
  const placed = new Set();
  for (const room of list('ROOM')) {
    const instances = b.readUInt32LE(room + 48);
    const n = b.readUInt32LE(instances);
    for (let i = 0; i < n; i++) placed.add(objects[b.readInt32LE(b.readUInt32LE(instances + 4 + i * 4) + 8)]);
  }
  return placed;
}

const objectOf = (codeName) => (codeName.match(/^gml_Object_(.+)_(Create|Destroy|Alarm|Step|Collision|Keyboard|Mouse|Other|Draw|KeyPress|KeyRelease|PreCreate)_/) || [])[1];

function checkCoverage(originalFile, hebrewFile) {
  const en = gm.load(originalFile);
  const he = gm.load(hebrewFile);
  const enCode = gm.readCode(en.buf, en.ch, en.str);
  const heCode = gm.readCode(he.buf, he.ch, he.str);
  const enTable = gm.readTextTable(enCode.get('gml_Script_textdata_en'));
  const heTable = gm.readTextTable(heCode.get('gml_Script_textdata_en'));
  const keyPatterns = ALLOW.textTable.keyPatterns.map((p) => new RegExp(p.pattern));

  const report = { table: { total: enTable.size, needText: 0, translated: 0, allowed: [], missing: [] }, code: { missing: [], allowed: [], unused: 0, unusedList: [] } };

  for (const [key, english] of enTable) {
    if (!hasLatinWord(english)) continue;
    report.table.needText++;
    const hebrew = heTable.get(key);
    if (hebrew !== undefined && hasHebrew(hebrew)) { report.table.translated++; continue; }
    if (ALLOW.textTable.keys[key] || keyPatterns.some((r) => r.test(key))) report.table.allowed.push({ key, english });
    else report.table.missing.push({ key, english, hebrew });
  }

  const placed = placedObjects(en);
  for (const [name, ops] of enCode) {
    if (name.startsWith('gml_Script_textdata_')) continue;
    const stillThere = new Set((heCode.get(name) || []).filter((o) => o.kind === 'str').map((o) => o.value));
    const left = [...new Set(ops.filter((o) => o.kind === 'str' && looksLikeText(o.value) && stillThere.has(o.value)).map((o) => o.value))];
    if (!left.length) continue;
    const obj = objectOf(name);
    if (obj && !placed.has(obj)) { report.code.unused += left.length; report.code.unusedList.push({ code: name, strings: left }); continue; }
    const entry = { code: name, strings: left };
    if (ALLOW.codeLiterals.entries[name]) report.code.allowed.push(entry);
    else report.code.missing.push(entry);
  }

  const done = report.table.missing.length === 0 && report.code.missing.length === 0;
  report.percent = (100 * (report.table.translated + report.table.allowed.length)) / report.table.needText;
  report.complete = done;
  return report;
}

function main() {
  const W = path.join(__dirname, '..');
  const args = process.argv.slice(2).filter((a) => !a.startsWith('--'));
  const showUnused = process.argv.includes('--unused');
  const original = args[0] || path.join(W, 'backup', 'data.win.orig');
  const hebrew = args[1] || path.join(W, 'build', 'data.win');
  for (const f of [original, hebrew]) {
    if (!fs.existsSync(f)) {
      console.error(`Not found: ${f}\nRun setup.ps1 -NoInstall first, or pass both paths.`);
      process.exit(2);
    }
  }
  const r = checkCoverage(original, hebrew);
  const t = r.table;
  console.log(`Text table: ${t.translated} translated + ${t.allowed.length} reviewed (kept Latin) of ${t.needText} entries with English text (${t.total} entries in all)`);
  for (const m of t.missing) console.log(`  STILL ENGLISH  ${m.key}: ${JSON.stringify(m.english)}`);
  console.log(`Code literals: ${r.code.missing.length} code entries with English text, ${r.code.allowed.length} reviewed, ${r.code.unused} literals in objects no room uses`);
  for (const m of r.code.missing) console.log(`  STILL ENGLISH  ${m.code}: ${m.strings.map((s) => JSON.stringify(s)).join(', ')}`);
  if (showUnused) for (const m of r.code.unusedList) console.log(`  UNUSED OBJECT  ${m.code}: ${m.strings.map((s) => JSON.stringify(s)).join(', ')}`);
  else if (r.code.unused) console.log('  (run with --unused to list them for review)');
  console.log(r.complete ? 'COVERAGE 100% (text table + code literals)' : `COVERAGE INCOMPLETE (${r.percent.toFixed(2)}% of the text table)`);
  console.log('Not machine-checked: text inside images. The sprite audit covers those.');
  process.exit(r.complete ? 0 : 1);
}

if (require.main === module) main();

module.exports = { checkCoverage };
