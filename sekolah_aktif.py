# -*- coding: utf-8 -*-
"""sekolah_aktif.py - Sekolah Aktif (ada pusat peperiksaan) vs sekolah tidak aktif (penyumbang guru sahaja).

 * Sekolah AKTIF  = sekolah yang menjadi tuan rumah pusat peperiksaan. Pusatnya dijana petugas dan SUP-nya nampak "Petugas Hadir".
 * Sekolah TIDAK AKTIF = tiada pusat (atau PPD nyahtanda). Tiada petugas dijana di sekolah itu; gurunya masih boleh dilantik di pusat lain
   dan SUP hanya menerima Surat Lantikan.
 * Disimpan dalam sekolah_master.data["AKTIF_PUSAT"] (true/false) - tiada jadual baharu.
   Jika tiada nilai tersimpan: aktif jika sekolah itu mempunyai pusat (tingkah laku sedia ada tidak berubah).
 * Hanya NYAHTANDA EKSPLISIT menyembunyikan pusat daripada janaan (spm_core.get_pusat_df memanggil tapis_pusat).
"""
import json

import pandas as pd
import streamlit as st

import spm_core as core
from kuota_pusat import _data as _kdata, kod_tuan_rumah, no_pusat as _no_pusat

KUNCI = "AKTIF_PUSAT"


def _s(v):
    x = "" if v is None else str(v).strip()
    return "" if x.lower() in ("nan", "none", "null", "nat") else x


def _flag(row):
    """True / False jika ditetapkan, None jika belum."""
    d = _kdata(row)
    if KUNCI not in d:
        return None
    v = d.get(KUNCI)
    if v is None or _s(v) == "":
        return None
    return v is True or str(v).strip().lower() in ("1", "true", "ya", "yes", "y")


def _baca_sekolah(kod_ppd=None):
    try:
        t = core.supa.table("sekolah_master").select("*")
        if kod_ppd:
            t = t.eq("kod_ppd", kod_ppd)
        return t.limit(5000).execute().data or []
    except Exception:
        return []


def _baca_pusat_mentah():
    try:
        return core.supa.table("pusat_master").select("*").limit(2000).execute().data or []
    except Exception:
        return []


def host_map(rows_pusat=None):
    """{kod_sekolah: [no_pusat]} daripada pusat_master (data mentah, tidak ditapis)."""
    out = {}
    for r in (rows_pusat if rows_pusat is not None else _baca_pusat_mentah()):
        no = _no_pusat(r)
        if not no:
            continue
        for k in kod_tuan_rumah(r):
            out.setdefault(k, [])
            if no not in out[k]:
                out[k].append(no)
    return out


@st.cache_data(ttl=60, show_spinner=False)
def tak_aktif_set():
    """Kod sekolah yang dinyahtanda secara eksplisit oleh PPD."""
    return set()  # model baharu: aktif = ada pusat; bendera lama diabaikan


def tapis_pusat(df):
    """Buang pusat yang SEMUA sekolah tuan rumahnya dinyahtanda. Selamat: sebarang ralat -> pulang df asal."""
    try:
        if df is None or len(df) == 0:
            return df
        nt = tak_aktif_set()
        if not nt:
            return df
        keep = []
        for _, r in df.iterrows():
            h = kod_tuan_rumah(r)
            keep.append(not (h and (h & nt)))
        return df[pd.Series(keep, index=df.index)].reset_index(drop=True)
    except Exception:
        return df


@st.cache_data(ttl=60, show_spinner=False)
def is_aktif(kod_sekolah):
    kod = _s(kod_sekolah).upper()
    for r in _baca_sekolah():
        if _s(r.get("kod_sekolah")).upper() == kod:
            break
    return bool(host_map().get(kod))


def _simpan(row, aktif):
    d = dict(_kdata(row))
    d[KUNCI] = bool(aktif)
    val = json.dumps(d, ensure_ascii=False) if isinstance(row.get("data"), str) else d
    try:
        core.supa.table("sekolah_master").update({"data": val}).eq("kod_sekolah", row.get("kod_sekolah")).execute()
        return True
    except Exception:
        return False


def _segar():
    try:
        import ppd_aliran as al
        al._clear()
    except Exception:
        st.cache_data.clear()


def render_aktif(kod_ppd):
    """Aktif = sekolah ada pusat. Nyahaktif = padam pusat. Aktif semula = tambah pusat."""
    st.subheader(f"✅ Sekolah Aktif - PPD {kod_ppd} - {core.PPD_MAP.get(kod_ppd, '')}")
    st.caption("Sekolah **aktif** = sekolah yang mempunyai pusat peperiksaan. Untuk menjadikan sekolah tidak aktif, **padam pusatnya**; "
               "untuk mengaktifkan semula, **tambah pusat** (sekolah mesti sudah didaftarkan dahulu).")
    sek = _baca_sekolah(kod_ppd)
    if not sek:
        st.info("Tiada sekolah dalam PPD ini. Tambah sekolah dahulu (JPN: Selenggara Sekolah).")
        return
    pusat_ppd = [r for r in _baca_pusat_mentah() if _no_pusat(r).startswith(kod_ppd.upper())]
    hm = host_map(pusat_ppd)
    rows = []
    for r in sorted(sek, key=lambda x: _s(x.get("kod_sekolah"))):
        kod = _s(r.get("kod_sekolah")).upper()
        p = hm.get(kod, [])
        rows.append({"KOD": kod, "NAMA SEKOLAH": _s(r.get("nama_sekolah")), "BIL PUSAT": len(p), "NO PUSAT": ", ".join(p),
                     "STATUS": "Aktif" if p else "Tidak aktif"})
    n_aktif = sum(1 for x in rows if x["BIL PUSAT"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Jumlah sekolah", len(rows))
    c2.metric("Aktif (ada pusat)", n_aktif)
    c3.metric("Tidak aktif (guru sahaja)", len(rows) - n_aktif)
    tapis = st.radio("Papar", ["Aktif", "Tidak aktif", "Semua"], horizontal=True, key=f"sa_tapis_{kod_ppd}")
    cari = st.text_input("🔍 Cari kod / nama sekolah", key=f"sa_cari_{kod_ppd}").strip().lower()
    papar = [x for x in rows if (tapis == "Semua" or (tapis == "Aktif") == bool(x["BIL PUSAT"]))
             and (not cari or cari in x["KOD"].lower() or cari in x["NAMA SEKOLAH"].lower())]
    if papar:
        df = pd.DataFrame(papar)
        st.dataframe(df, use_container_width=True, hide_index=True, height=min(480, 60 + 35 * len(df)))
        st.download_button("📊 Muat turun senarai (Excel)", core.to_excel(df), file_name=f"sekolah_aktif_{kod_ppd}.xlsx", key=f"sa_dl_{kod_ppd}")
    else:
        st.info("Tiada sekolah sepadan.")
    st.divider()
    import selenggara_sp as sp
    sp.panel_ppd_pusat(kod_ppd)
