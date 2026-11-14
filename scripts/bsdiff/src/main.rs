//! ut-bsdiff diff  <original> <patched> <out.bsdiff>   writes a BSDIFF40 patch, then applies it to check it
//! ut-bsdiff apply <original> <in.bsdiff> <out>        applies a patch
use std::io::Cursor;
use std::process::exit;

use qbsdiff::{Bsdiff, Bspatch};

fn read(p: &str) -> Vec<u8> {
    std::fs::read(p).unwrap_or_else(|e| fail(&format!("{p}: {e}")))
}
fn fail(msg: &str) -> ! {
    eprintln!("ut-bsdiff: {msg}");
    exit(1)
}
fn apply(source: &[u8], patch: &[u8]) -> Vec<u8> {
    let p = Bspatch::new(patch).unwrap_or_else(|e| fail(&format!("bad patch: {e}")));
    let mut out = Vec::with_capacity(p.hint_target_size() as usize);
    p.apply(source, Cursor::new(&mut out)).unwrap_or_else(|e| fail(&format!("apply failed: {e}")));
    out
}

fn main() {
    let a: Vec<String> = std::env::args().skip(1).collect();
    match (a.first().map(String::as_str), a.len()) {
        (Some("diff"), 4) => {
            let (src, dst) = (read(&a[1]), read(&a[2]));
            let mut patch = Vec::new();
            Bsdiff::new(&src, &dst).compare(Cursor::new(&mut patch)).unwrap_or_else(|e| fail(&format!("diff failed: {e}")));
            if apply(&src, &patch) != dst {
                fail("the patch doesn't reproduce the patched file");
            }
            std::fs::write(&a[3], &patch).unwrap_or_else(|e| fail(&format!("{}: {e}", a[3])));
            println!("patch {} bytes, checked", patch.len());
        }
        (Some("apply"), 4) => {
            let out = apply(&read(&a[1]), &read(&a[2]));
            std::fs::write(&a[3], out).unwrap_or_else(|e| fail(&format!("{}: {e}", a[3])));
        }
        _ => fail("usage: ut-bsdiff diff <original> <patched> <out.bsdiff> | apply <original> <in.bsdiff> <out>"),
    }
}
