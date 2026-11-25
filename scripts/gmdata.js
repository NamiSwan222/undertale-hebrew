// Minimal reader for GameMaker Studio 1.4 data files (UNDERTALE's data.win, bytecode 15+).
// It is enough to list the strings and the string literals each code entry pushes, so the coverage check can
// compare the English game with the Hebrew build without decompiling anything.
const fs = require('fs');

function chunks(buf) {
  if (buf.toString('ascii', 0, 4) !== 'FORM') throw new Error('not a GameMaker data file');
  const out = {};
  let p = 8;
  while (p + 8 <= buf.length) {
    const name = buf.toString('ascii', p, p + 4);
    const size = buf.readUInt32LE(p + 4);
    out[name] = { start: p + 8, size };
    p += 8 + size;
  }
  return out;
}

function readStrings(buf, ch) {
  const { start } = ch.STRG;
  const n = buf.readUInt32LE(start);
  const strings = new Array(n);
  const byAddr = new Map(); // address of the characters -> index (code entry names point there)
  for (let i = 0; i < n; i++) {
    const at = buf.readUInt32LE(start + 4 + i * 4);
    const len = buf.readUInt32LE(at);
    strings[i] = buf.toString('utf8', at + 4, at + 4 + len);
    byAddr.set(at + 4, i);
  }
  return { strings, byAddr };
}

// Extra operand bytes after the 4-byte instruction word, for bytecode 15/16.
function operandSize(word) {
  const op = word >>> 24;
  const t1 = (word >>> 16) & 0x0f;
  if (op === 0xc0 || op === 0xc1 || op === 0xc2 || op === 0xc3) { // push, pushloc, pushglb, pushbltn
    if (t1 === 0x0 || t1 === 0x3) return 8; // double, int64
    if (t1 === 0xf) return 0; // int16 is inside the word
    return 4; // float, int32, bool, variable, string
  }
  if (op === 0x45 || op === 0xd9) return 4; // pop, call
  if (op === 0x84) return 0; // pushi (int16)
  return 0;
}

const TYPE_STRING = 0x6;

// Returns Map(codeName -> [{ kind: 'str', value } | { kind: 'call' } | { kind: 'add' }]) for the named entries,
// or for all entries when names is null.
function readCode(buf, ch, str, names = null) {
  const { start } = ch.CODE;
  const n = buf.readUInt32LE(start);
  const out = new Map();
  for (let i = 0; i < n; i++) {
    const e = buf.readUInt32LE(start + 4 + i * 4);
    const name = str.strings[str.byAddr.get(buf.readUInt32LE(e))];
    if (names && !names.has(name)) continue;
    const length = buf.readUInt32LE(e + 4);
    const bcAt = e + 12 + buf.readInt32LE(e + 12);
    const ops = [];
    let p = bcAt;
    while (p < bcAt + length) {
      const w = buf.readUInt32LE(p);
      const op = w >>> 24;
      const extra = operandSize(w);
      if (op === 0xc0 && ((w >>> 16) & 0x0f) === TYPE_STRING) ops.push({ kind: 'str', value: str.strings[buf.readUInt32LE(p + 4)] });
      else if (op === 0xd9) ops.push({ kind: 'call' });
      else if (op === 0x0c) ops.push({ kind: 'add' });
      p += 4 + extra;
    }
    out.set(name, ops);
  }
  return out;
}

// textdata_en is a long list of ds_map_add(global.text_data_en, key, value) calls. GML pushes the arguments
// right to left, so between two calls: the value's string parts (joined with add), then the key.
function readTextTable(ops) {
  const table = new Map();
  let strs = [];
  for (const o of ops) {
    if (o.kind === 'str') strs.push(o.value);
    else if (o.kind === 'call') {
      if (strs.length >= 2) table.set(strs[strs.length - 1], strs.slice(0, -1).join(''));
      strs = [];
    }
  }
  return table;
}

function load(file) {
  const buf = fs.readFileSync(file);
  const ch = chunks(buf);
  const str = readStrings(buf, ch);
  return { buf, ch, str };
}

module.exports = { load, chunks, readStrings, readCode, readTextTable };
