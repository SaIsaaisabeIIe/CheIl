#!/usr/bin/env python3
"""
Perakit gabungan 1 file:

    ETW POKET.lua  +  Emotes-cheII (whitelist dihapus)  ->  etw-poket-cheii-gabungan.lua

Kedua file sumber TIDAK diubah. Masing-masing ditempel VERBATIM ke dalam
long-bracket string, lalu dijalankan lewat load() di dalam pcall, jadi:

  * isi kedua script sama persis byte-per-byte dengan aslinya;
  * file tetap satu berkas .lua yang bisa langsung dieksekusi;
  * error di satu bagian tidak menghentikan bagian lain.

Contoh:
    python3 tools/gabung-etw-poket.py
    python3 tools/gabung-etw-poket.py --etw "ETW POKET.lua" --out hasil.lua
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEADER = """\
--[[
    ============================================================
    GABUNGAN 1 FILE  -  ETW POKET  +  cheII Emotes
    ============================================================
    Sumber:
      BAGIAN 1 : {etw_name}  (verbatim, tidak diubah)
      BAGIAN 2 : {emotes_name}  (verbatim, tidak diubah)

    Cara kerja:
      * Kedua script asli disimpan apa adanya di dalam long-bracket
        string, lalu dijalankan berurutan lewat load() + pcall().
      * BAGIAN 1 dijalankan lebih dulu (panel ETW POKET), baru
        BAGIAN 2 (panel cheII Emotes).
      * Error di salah satu bagian hanya memunculkan warning
        "[GABUNGAN] ..." dan TIDAK mematikan bagian lainnya.
      * Kedua bagian berbagi environment global yang sama
        (getgenv/_G), sama seperti kalau dijalankan terpisah.

    Catatan:
      * Tidak ada whitelist tambahan di file ini. Whitelist bawaan
        cheII memang sudah dihapus dari file sumber BAGIAN 2.
      * Kalau ingin menambah blok whitelist sendiri, taruh di atas
        "LAPISAN PEREKAT" dan hentikan script dengan `return`.
    ============================================================
]]

-- ============================================================
--  LAPISAN PEREKAT (bukan bagian dari kedua script asli)
-- ============================================================
local __gLoad = loadstring or load

local function __gPesan(teks)
    local ok = pcall(function()
        warn("[GABUNGAN] " .. teks)
    end)
    if not ok then
        pcall(function()
            print("[GABUNGAN] " .. teks)
        end)
    end
end

local function __gJalankan(nama, sumber)
    if type(sumber) ~= "string" or #sumber == 0 then
        __gPesan(nama .. " kosong, dilewati.")
        return false
    end

    local chunk, err = __gLoad(sumber, "=" .. nama)
    if not chunk then
        __gPesan(nama .. " gagal dimuat: " .. tostring(err))
        return false
    end

    local ok, errJalan = pcall(chunk)
    if not ok then
        __gPesan(nama .. " error: " .. tostring(errJalan))
        return false
    end

    return true
end

-- ============================================================
--  BAGIAN 1  |  ETW POKET (verbatim)
-- ============================================================
local __srcETW = {open_etw}
{sumber_etw}{close_etw}

__gJalankan("BAGIAN 1 (ETW POKET)", __srcETW)
__srcETW = nil

-- ============================================================
--  BAGIAN 2  |  cheII Emotes (verbatim)
-- ============================================================
local __srcCheII = {open_emotes}
{sumber_emotes}{close_emotes}

__gJalankan("BAGIAN 2 (cheII Emotes)", __srcCheII)
__srcCheII = nil

-- ============================================================
--  AKHIR GABUNGAN
-- ============================================================
"""


def bracket_level(teks: str) -> int:
    """Cari level '=' yang penutupnya (]=*]) tidak muncul di dalam teks."""
    level = 0
    while True:
        penutup = "]" + "=" * level + "]"
        if penutup not in teks:
            return level
        level += 1


def buka(level: int) -> str:
    return "[" + "=" * level + "["


def tutup(level: int) -> str:
    return "]" + "=" * level + "]"


def baca(path: str) -> str:
    # Baca mode biner supaya isi file tidak diubah sama sekali (tanpa
    # normalisasi CRLF, tanpa translasi encoding oleh locale).
    with open(path, "rb") as f:
        return f.read().decode("utf-8", "surrogateescape")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--etw", default=None,
                    help="file script ETW POKET (default: cari otomatis di folder repo)")
    ap.add_argument("--emotes", default=os.path.join(ROOT, "Emotes-cheII-whitelist-removed.lua"),
                    help="file script cheII Emotes")
    ap.add_argument("--out", default=os.path.join(ROOT, "etw-poket-cheii-gabungan.lua"),
                    help="file hasil gabungan")
    args = ap.parse_args()

    if args.etw is None:
        for kandidat in ("ETW POKET.lua", "ETW POKET.lua.txt",
                         "ETW%20POKET.lua.txt", "ETW%20POKET.lua"):
            path = os.path.join(ROOT, kandidat)
            if os.path.isfile(path):
                args.etw = path
                break
        else:
            print("ERROR: file ETW POKET tidak ditemukan. Taruh salah satu dari ini "
                  "di folder repo: ETW POKET.lua / ETW POKET.lua.txt, "
                  "atau pakai --etw <path>.", file=sys.stderr)
            return 2

    for path in (args.etw, args.emotes):
        if not os.path.isfile(path):
            print("ERROR: file sumber tidak ditemukan: %s" % path, file=sys.stderr)
            return 2

    sumber_etw = baca(args.etw)
    sumber_emotes = baca(args.emotes)

    if not sumber_etw.strip():
        print("ERROR: %s kosong." % args.etw, file=sys.stderr)
        return 2
    if not sumber_emotes.strip():
        print("ERROR: %s kosong." % args.emotes, file=sys.stderr)
        return 2

    lv_etw = bracket_level(sumber_etw)
    lv_emotes = bracket_level(sumber_emotes)

    hasil = HEADER.format(
        etw_name=os.path.basename(args.etw),
        emotes_name=os.path.basename(args.emotes),
        open_etw=buka(lv_etw),
        close_etw=tutup(lv_etw),
        sumber_etw=sumber_etw,
        open_emotes=buka(lv_emotes),
        close_emotes=tutup(lv_emotes),
        sumber_emotes=sumber_emotes,
    )

    with open(args.out, "wb") as f:
        f.write(hasil.encode("utf-8", "surrogateescape"))

    print("OK  %s" % args.out)
    print("    BAGIAN 1 : %-40s %9d byte  (bracket level %d)" %
          (os.path.basename(args.etw), len(sumber_etw.encode("utf-8", "surrogateescape")), lv_etw))
    print("    BAGIAN 2 : %-40s %9d byte  (bracket level %d)" %
          (os.path.basename(args.emotes), len(sumber_emotes.encode("utf-8", "surrogateescape")), lv_emotes))
    print("    TOTAL    : %9d byte" % os.path.getsize(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
