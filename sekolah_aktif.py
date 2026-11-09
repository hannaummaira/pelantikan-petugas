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
    return {_s(r.get("kod_sekolah")).upper() for r in _baca_sekolah() if _flag(r) is False}


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
            f = _flag(r)
            if f is not None:
                return f
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
    st.subheader(f"✅ Selenggara Sekolah Aktif - PPD {kod_ppd} - {core.PPD_MAP.get(kod_ppd, '')}")
    st.caption("Tick sekolah yang mempunyai pusat peperiksaan. Hanya sekolah aktif akan dijana petugas dan SUP-nya nampak Petugas Hadir. "
               "Sekolah tidak aktif hanya menyumbang guru dan menerima Surat Lantikan di menu SUP.")
    sek = _baca_sekolah(kod_ppd)
    if not sek:
        st.info("Tiada sekolah dalam PPD ini.")
        return
    pusat_ppd = [r for r in _baca_pusat_mentah() if _no_pusat(r).startswith(kod_ppd.upper())]
    hm = host_map(pusat_ppd)
    # petugas sedia ada ditempatkan di pusat (amaran sebelum nyahtanda)
    try:
        from kemajuan import muat_rekod
        ada_petugas = {}
        for r in muat_rekod(kod_ppd):
            if r["pusat"] and r["rank"] >= 0 and not r["amali_jaw"]:
                ada_petugas[r["pusat"]] = ada_petugas.get(r["pusat"], 0) + 1
    except Exception:
        ada_petugas = {}
    rows = []
    for r in sorted(sek, key=lambda x: _s(x.get("kod_sekolah"))):
        kod = _s(r.get("kod_sekolah")).upper()
        pusat = hm.get(kod, [])
        f = _flag(r)
        aktif = f if f is not None else bool(pusat)
        rows.append({"row": r, "AKTIF": aktif, "KOD": kod, "NAMA SEKOLAH": _s(r.get("nama_sekolah")), "BIL PUSAT": len(pusat),
                     "NO PUSAT": ", ".join(pusat), "PETUGAS DITEMPATKAN": sum(ada_petugas.get(p, 0) for p in pusat),
                     "STATUS": ("Aktif" if aktif else ("Tidak aktif (dinyahtanda)" if pusat else "Tiada pusat"))})
    jum = len(rows)
    n_aktif = sum(1 for x in rows if x["AKTIF"])
    n_pusat = sum(1 for x in rows if x["BIL PUSAT"] > 0)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jumlah sekolah", jum)
    c2.metric("Ada pusat", n_pusat)
    c3.metric("Aktif", n_aktif)
    c4.metric("Tidak aktif (guru sahaja)", jum - n_aktif)

    b1, b2 = st.columns(2)
    if b1.button("⚡ Tick semua sekolah yang ada pusat", key=f"sa_auto_{kod_ppd}", use_container_width=True,
                 help="Aktifkan semua sekolah yang ada pusat; sekolah tanpa pusat ditandakan tidak aktif."):
        ok = sum(1 for x in rows if _simpan(x["row"], x["BIL PUSAT"] > 0))
        _segar()
        st.success(f"✅ {ok} sekolah dikemas kini: sekolah ada pusat = aktif.")
        st.rerun()
    tapis = b2.radio("Papar", ["Aktif", "Tidak aktif", "Semua"], horizontal=True, key=f"sa_tapis_{kod_ppd}",
                     help="Aktif = dijana petugas. Sekolah yang dinyahaktifkan berpindah ke paparan Tidak aktif.")
    cari = st.text_input("🔍 Cari kod / nama sekolah", key=f"sa_cari_{kod_ppd}").strip().lower()
    papar = [x for x in rows if (tapis == "Semua" or (tapis == "Aktif") == bool(x["AKTIF"]))
             and (not cari or cari in x["KOD"].lower() or cari in x["NAMA SEKOLAH"].lower())]
    if not papar:
        st.info("Tiada sekolah sepadan." if cari or tapis == "Semua" else f"Tiada sekolah dalam paparan {tapis}.")
        return
    if tapis == "Aktif":
        st.caption("Nyahtanda ✅ lalu tekan Simpan untuk menyahaktifkan - sekolah itu akan hilang daripada paparan ini dan berpindah ke **Tidak aktif**.")
    elif tapis == "Tidak aktif":
        st.caption("Tick ✅ lalu tekan Simpan untuk mengaktifkan semula (hanya sekolah yang ada pusat).")
    df = pd.DataFrame([{k: v for k, v in x.items() if k != "row"} for x in papar])
    ed = st.data_editor(df, use_container_width=True, hide_index=True, height=min(560, 60 + 35 * len(df)), key=f"sa_ed_{kod_ppd}_{tapis}_{len(df)}",
                        disabled=["KOD", "NAMA SEKOLAH", "BIL PUSAT", "NO PUSAT", "PETUGAS DITEMPATKAN", "STATUS"],
                        column_config={"AKTIF": st.column_config.CheckboxColumn("✅ Aktif")})
    ubah = []
    for x, (_, b) in zip(papar, ed.iterrows()):
        baru = bool(b["AKTIF"])
        if baru != bool(x["AKTIF"]):
            ubah.append((x, baru))
    tolak = [x["KOD"] for x, baru in ubah if baru and x["BIL PUSAT"] == 0]
    nyah = [(x, baru) for x, baru in ubah if (not baru) and x["BIL PUSAT"] > 0]
    ada_p = sum(x["PETUGAS DITEMPATKAN"] for x, _ in nyah)
    if tolak:
        st.warning(f"{len(tolak)} sekolah tiada pusat peperiksaan, tidak boleh diaktifkan: " + ", ".join(tolak[:8]))
    if nyah:
        st.warning(f"{len(nyah)} sekolah ada pusat akan dinyahaktifkan. Pusatnya tidak lagi dijana petugas dan disembunyikan"
                   + (f"; {ada_p} petugas sudah ditempatkan di pusat itu juga tidak akan dipaparkan." if ada_p else "."))
    sah = True
    if nyah:
        sah = st.checkbox("Saya faham dan mahu nyahaktifkan sekolah berpusat ini", key=f"sa_sah_{kod_ppd}")
    boleh = [(x, b) for x, b in ubah if not (b and x["BIL PUSAT"] == 0)]
    if st.button(f"💾 Simpan ({len(boleh)} perubahan)", type="primary", disabled=(not boleh) or not sah, key=f"sa_simpan_{kod_ppd}"):
        ok = sum(1 for x, b in boleh if _simpan(x["row"], b))
        _segar()
        st.success(f"✅ {ok} sekolah dikemas kini.")
        st.rerun()
    st.download_button("📊 Muat turun senarai (Excel)", core.to_excel(df.drop(columns=[], errors="ignore")), file_name=f"sekolah_aktif_{kod_ppd}.xlsx", key=f"sa_dl_{kod_ppd}")
