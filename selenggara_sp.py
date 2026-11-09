# -*- coding: utf-8 -*-
"""selenggara_sp.py - JPN: tambah / edit Sekolah dan Pusat Peperiksaan ikut daerah (PPD).
Menulis terus ke sekolah_master / pusat_master
Versi FIX - buang column 'data' yang tak wujud dalam Supabase
"""
import json
import pandas as pd
import streamlit as st
import spm_core as core
from kuota_pusat import simpan_pusat, kelas_auto, kuota_pusat, no_pusat as _no_pusat, kod_tuan_rumah

FLY_SP = [("sekolah", "🏫 Selenggara Sekolah"), ("pusat", "🏢 Selenggara Pusat"), ("amali", "🔬 Pusat Amali Sains"), ("templat", "📥 Muat Turun Templat")]

def _db():
    return core._RAW

def _s(v):
    x = "" if v is None else str(v).strip()
    return "" if x.lower() in ("nan", "none", "null", "nat") else x

def _data(row):
    # Compat - kalau ada data, pakai. Kalau takde, return {}
    d = row.get("data")
    if isinstance(d, dict):
        return dict(d)
    if isinstance(d, str) and d.strip().startswith("{"):
        try:
            return json.loads(d)
        except Exception:
            return {}
    return {}

def _bungkus(row, d):
    return json.dumps(d, ensure_ascii=False) if isinstance(row.get("data"), str) else d

def _semua(table, kod_ppd):
    out, mula = [], 0
    while True:
        q = _db().table(table).select("*")
        if table == "sekolah_master":
            q = q.eq("kod_ppd", kod_ppd)
        res = q.range(mula, mula + 999).execute().data or []
        out += res
        if len(res) < 1000:
            break
        mula += 1000
    return out

def _pusat_daerah(kod_ppd):
    out, mula = [], 0
    while True:
        res = _db().table("pusat_master").select("*").range(mula, mula + 999).execute().data or []
        out += res
        if len(res) < 1000:
            break
        mula += 1000
    return [r for r in out if (_s(r.get("kod_ppd")).upper() == kod_ppd) or _no_pusat(r).startswith(kod_ppd)]

def _ada(table, lajur, nilai):
    for c in lajur:
        try:
            if _db().table(table).select("*").eq(c, nilai).limit(1).execute().data:
                return True
        except Exception:
            pass
    return False

def _segar():
    try:
        st.cache_data.clear()
    except Exception:
        pass

def _pilih_daerah(kunci):
    ppd = core.PPD_MAP
    kods = sorted(ppd.keys())
    pilih = st.selectbox("Pilih Daerah (PPD)", kods, format_func=lambda k: f"{k} - {ppd.get(k, k)}", key=f"sp_ppd_{kunci}")
    return pilih

# ------------------------------------------------------------------------- sekolah
def _panel_sekolah(kod_ppd):
    rows = _semua("sekolah_master", kod_ppd)
    st.caption(f"{len(rows)} sekolah dalam daerah {kod_ppd} - {core.PPD_MAP.get(kod_ppd, '')}")
    t1, t2, t3 = st.tabs(["✏️ Edit Nama Sekolah", "➕ Tambah Sekolah", "🗑️ Batal Sekolah"])

    with t1:
        if not rows:
            st.info("Tiada sekolah dalam daerah ini.")
        else:
            df = pd.DataFrame([{"KOD SEKOLAH": _s(r.get("kod_sekolah")).upper(), "NAMA SEKOLAH": _s(r.get("nama_sekolah")),
                                "POSKOD": _s(r.get("poskod")) or _s(_data(r).get("POSKOD"))} for r in rows]).sort_values("KOD SEKOLAH")
            st.dataframe(df, use_container_width=True, hide_index=True, height=260)
            peta = {_s(r.get("kod_sekolah")).upper(): r for r in rows}
            kod = st.selectbox("Pilih sekolah untuk diedit", list(df["KOD SEKOLAH"]),
                               format_func=lambda k: f"{k} - {_s(peta[k].get('nama_sekolah'))}", key=f"sp_es_{kod_ppd}")
            r = peta[kod]
            d = _data(r)
            with st.form(f"form_es_{kod_ppd}_{kod}"):
                nama = st.text_input("Nama Sekolah", value=_s(r.get("nama_sekolah")))
                pk = st.text_input("Poskod (pilihan)", value=_s(r.get("poskod")) or _s(d.get("POSKOD")), max_chars=5)
                if st.form_submit_button("💾 Simpan Perubahan Sekolah", type="primary"):
                    nama = nama.strip().upper()
                    if not nama:
                        st.error("Nama sekolah tidak boleh kosong.")
                    else:
                        # FIX: Tak guna column data lagi
                        payload = {"nama_sekolah": nama}
                        # cuba update poskod kalau column tu wujud
                        if pk.strip():
                            payload["poskod"] = pk.strip()
                        try:
                            _db().table("sekolah_master").update(payload).eq("kod_sekolah", _s(r.get("kod_sekolah"))).execute()
                            _segar()
                            st.success(f"✅ {kod} dikemas kini: {nama}")
                        except Exception as e:
                            # kalau error sebab poskod tak wujud, cuba tanpa poskod
                            if "poskod" in str(e).lower():
                                try:
                                    _db().table("sekolah_master").update({"nama_sekolah": nama}).eq("kod_sekolah", _s(r.get("kod_sekolah"))).execute()
                                    _segar()
                                    st.success(f"✅ {kod} dikemas kini: {nama} (tanpa poskod)")
                                except Exception as e2:
                                    st.error(f"Gagal simpan: {str(e2)[:300]}")
                            else:
                                st.error(f"Gagal simpan: {str(e)[:300]}")

    with t2:
        with st.form(f"form_ts_{kod_ppd}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            kod = c1.text_input("Kod Sekolah *", placeholder="cth: BBA1234")
            nama = c2.text_input("Nama Sekolah *")
            pk = c1.text_input("Poskod (pilihan)", max_chars=5)
            st.caption(f"Sekolah akan didaftarkan di bawah PPD {kod_ppd} - {core.PPD_MAP.get(kod_ppd, '')}.")
            if st.form_submit_button("➕ Tambah Sekolah", type="primary"):
                kod, nama = kod.strip().upper(), nama.strip().upper()
                if not kod or not nama:
                    st.error("Kod sekolah dan nama sekolah wajib diisi.")
                elif _ada("sekolah_master", ["kod_sekolah"], kod):
                    st.error(f"Kod sekolah {kod} sudah wujud.")
                else:
                    # FIX: Insert terus ikut column sebenar, TANPA column data
                    # sekolah_master ADA kod_ppd - ikut screenshot kau
                    payload = {
                        "kod_sekolah": kod,
                        "nama_sekolah": nama,
                        "kod_ppd": kod_ppd,
                        "ppd": core.PPD_MAP.get(kod_ppd, "Klang")
                    }
                    # Tambah field tambahan yang mungkin ada dalam table kau
                    # dari gambar kau ada: password, bil_pusat, senarai_pusat
                    payload_extra = {}
                    try:
                        # Check column wujud dengan cuba insert simple dulu
                        # Kita cuba include field standard dari screenshot kau
                        if pk.strip():
                            # poskod - kalau tak wujud, nanti fallback
                            payload["poskod"] = pk.strip()
                        
                        _db().table("sekolah_master").insert(payload).execute()
                        _segar()
                        st.success(f"✅ Sekolah {kod} - {nama} ditambah ke PPD {kod_ppd}.")
                    except Exception as e:
                        err = str(e).lower()
                        # Kalau gagal sebab poskod tak wujud, retry tanpa poskod
                        if "poskod" in err or "pgrst204" in err:
                            try:
                                payload.pop("poskod", None)
                                payload.pop("kod_ppd_text", None)
                                _db().table("sekolah_master").insert(payload).execute()
                                _segar()
                                st.success(f"✅ Sekolah {kod} - {nama} ditambah ke PPD {kod_ppd}.")
                            except Exception as e2:
                                st.error(f"Gagal tambah: {str(e2)[:500]}")
                        else:
                            st.error(f"Gagal tambah: {str(e)[:500]}")


    with t3:
        form_padam_sekolah(kod_ppd, f"jpns_{kod_ppd}")


# ------------------------------------------------------------------------- pusat
def _panel_pusat(kod_ppd):
    rows = _pusat_daerah(kod_ppd)
    st.caption(f"{len(rows)} pusat peperiksaan dalam daerah {kod_ppd} - {core.PPD_MAP.get(kod_ppd, '')}")
    sek = {_s(r.get("kod_sekolah")).upper(): _s(r.get("nama_sekolah")) for r in _semua("sekolah_master", kod_ppd)}
    t1, t2, t3 = st.tabs(["✏️ Edit Pusat", "➕ Tambah Pusat", "🗑️ Batal Pusat"])

    with t1:
        if not rows:
            st.info("Tiada pusat dalam daerah ini.")
        else:
            lst = []
            for r in rows:
                q = kuota_pusat(r)
                d = _data(r)
                tuan = sorted(kod_tuan_rumah(r))
                lst.append({"NO PUSAT": _no_pusat(r), "NAMA PUSAT": _s(r.get("nama_pusat")) or _s(d.get("NAMA_PUSAT")),
                            "KOD SEKOLAH": tuan[0] if tuan else "", "BIL CALON": q["calon"], "KELAS": q["kelas"],
                            "POSKOD": _s(d.get("POSKOD_PUSAT")) or _s(d.get("POSKOD")) or _s(r.get("poskod"))})
            df = pd.DataFrame(lst).sort_values("NO PUSAT")
            st.dataframe(df, use_container_width=True, hide_index=True, height=260)
            peta = {_no_pusat(r): r for r in rows}
            no = st.selectbox("Pilih pusat untuk diedit", list(df["NO PUSAT"]),
                              format_func=lambda k: f"{k} - {_s(peta[k].get('nama_pusat'))}", key=f"sp_ep_{kod_ppd}")
            r = peta[no]
            baris = df[df["NO PUSAT"] == no].iloc[0]
            with st.form(f"form_ep_{kod_ppd}_{no}"):
                nama = st.text_input("Nama Pusat", value=str(baris["NAMA PUSAT"]))
                c1, c2, c3 = st.columns(3)
                ks = c1.text_input("Kod Sekolah (tuan rumah)", value=str(baris["KOD SEKOLAH"]))
                calon = c2.number_input("Bil Calon", min_value=0, max_value=3000, value=int(baris["BIL CALON"]), step=1)
                kelas = c3.number_input("Kelas (kosongkan = auto calon/20)", min_value=0, max_value=200, value=int(baris["KELAS"]), step=1)
                pk = st.text_input("Poskod Pusat", value=str(baris["POSKOD"]), max_chars=5)
                if st.form_submit_button("💾 Simpan Perubahan Pusat", type="primary"):
                    nama, ks = nama.strip().upper(), ks.strip().upper()
                    if not nama:
                        st.error("Nama pusat tidak boleh kosong.")
                    else:
                        try:
                            col = "no_pusat" if r.get("no_pusat") else "kod_pusat"
                            payload = {"nama_pusat": nama}
                            # tambah column lain kalau ada
                            if ks:
                                payload["kod_sekolah_tuan_rumah"] = ks
                                # cuba update semua kemungkinan nama column alamat
                                payload["alamat_pusat"] = ks
                                if "alamat" in r:
                                    payload["alamat"] = ks
                            if pk.strip() and "poskod" in r:
                                payload["poskod"] = pk.strip()
                            
                            _db().table("pusat_master").update(payload).eq(col, no).execute()
                            simpan_pusat(_db(), no, int(calon), int(kelas))
                            _segar()
                            st.success(f"✅ Pusat {no} dikemas kini. Petugas perlu: {int(kelas) + 9}.")
                        except Exception as e:
                            st.error(f"Gagal simpan: {str(e)[:500]}")

    with t2:
        form_tambah_pusat(kod_ppd, f"jpn_{kod_ppd}")

    with t3:
        form_padam_pusat(kod_ppd, f"jpnp_{kod_ppd}")


# ------------------------------------------------------------------------- tambah / padam pusat, padam sekolah, templat
def _sekolah_ppd(kod_ppd):
    return {_s(r.get("kod_sekolah")).upper(): _s(r.get("nama_sekolah")) for r in _semua("sekolah_master", kod_ppd) if _s(r.get("kod_sekolah"))}


def _cadangan_pusat(no):
    try:
        return _db().table("cadangan_sup").select("*").eq("kod_pusat", no).limit(5000).execute().data or []
    except Exception:
        return []


def _no_cadangan(kod_ppd):
    """Cadangan no pusat seterusnya (kod PPD + 3 digit)."""
    mx = 100
    for r in _pusat_daerah(kod_ppd):
        n = _no_pusat(r)
        if n.startswith(kod_ppd) and n[len(kod_ppd):].isdigit():
            mx = max(mx, int(n[len(kod_ppd):]))
    return f"{kod_ppd}{mx + 1}"


def form_tambah_pusat(kod_ppd, kunci):
    """Tambah pusat: sekolah mesti sudah ada (pilih daripada senarai). Menambah pusat = sekolah menjadi AKTIF."""
    sek = _sekolah_ppd(kod_ppd)
    if not sek:
        st.info("Tiada sekolah dalam PPD ini. Tambah sekolah dahulu (Selenggara Sekolah), kemudian tambah pusat.")
        return
    st.caption("Langkah: sekolah mesti didaftarkan dahulu, kemudian pilih sekolah itu untuk dijadikan pusat. Sekolah yang ada pusat = **AKTIF**.")
    hos = {}
    for r in _pusat_daerah(kod_ppd):
        for k in kod_tuan_rumah(r):
            hos.setdefault(k, []).append(_no_pusat(r))
    kod = st.selectbox("Pilih Sekolah *", sorted(sek), key=f"tp_sek_{kunci}",
                       format_func=lambda k: f"{k} - {sek[k]}" + (f"   [sudah ada pusat: {', '.join(hos[k])}]" if k in hos else "   [tidak aktif]"))
    with st.form(f"form_tp2_{kunci}_{kod}", clear_on_submit=True):
        c1, c2 = st.columns(2)
        no = c1.text_input("No Pusat Peperiksaan *", value=_no_cadangan(kod_ppd))
        nama = c2.text_input("Nama Pusat *", value=sek.get(kod, ""))
        calon = c1.number_input("Bil Calon *", min_value=0, max_value=3000, value=0, step=1)
        pk = c2.text_input("Poskod Pusat", max_chars=5)
        st.caption(f"Kelas = CEIL(calon/20); petugas = kelas + 9. Pusat didaftarkan di bawah PPD {kod_ppd}.")
        if st.form_submit_button("➕ Tambah Pusat", type="primary"):
            no, nama = no.strip().upper(), nama.strip().upper()
            if not no or not nama:
                st.error("No pusat dan nama pusat wajib diisi.")
            elif not no.startswith(kod_ppd):
                st.error(f"No pusat mesti bermula dengan kod PPD ({kod_ppd}).")
            elif _ada("pusat_master", ["kod_pusat", "no_pusat"], no):
                st.error(f"No pusat {no} sudah wujud.")
            else:
                kelas = kelas_auto(calon)
                payload = {"no_pusat": no, "kod_pusat": no, "nama_pusat": nama, "kod_sekolah_tuan_rumah": kod, "nama_sekolah_tuan_rumah": sek.get(kod, nama),
                           "jumlah_calon": int(calon), "jumlah_kelas": kelas, "calon": int(calon), "bilik": kelas, "alamat_pusat": kod}
                if pk.strip():
                    payload["poskod"] = pk.strip()
                try:
                    try:
                        _db().table("pusat_master").insert(payload).execute()
                    except Exception:
                        payload.pop("poskod", None)
                        _db().table("pusat_master").insert({k: payload[k] for k in ("kod_pusat", "no_pusat", "nama_pusat", "kod_sekolah_tuan_rumah")}).execute()
                    simpan_pusat(_db(), no, int(calon), kelas)
                    _segar()
                    st.success(f"✅ Pusat {no} - {nama} ditambah. Sekolah {kod} kini AKTIF ({int(calon)} calon, {kelas} kelas, petugas perlu {kelas + 9}).")
                except Exception as e:
                    st.error(f"Gagal tambah: {str(e)[:300]}")


def form_padam_pusat(kod_ppd, kunci):
    """Padam pusat = sekolah tuan rumah menjadi TIDAK AKTIF. Petugas di pusat itu dilepaskan (kecuali ada surat dijana)."""
    rows = _pusat_daerah(kod_ppd)
    if not rows:
        st.info("Tiada pusat dalam PPD ini.")
        return
    peta = {_no_pusat(r): r for r in rows}
    no = st.selectbox("Pilih pusat untuk dipadam", sorted(peta), key=f"pp_no_{kunci}",
                      format_func=lambda k: f"{k} - {_s(peta[k].get('nama_pusat'))}")
    r = peta[no]
    cad = _cadangan_pusat(no)
    ada_surat = [c for c in cad if _s(c.get("no_surat")) or any(x in _s(c.get("status")).upper() for x in ("SURAT", "LULUS", "DIHANTAR"))]
    tuan = ", ".join(sorted(kod_tuan_rumah(r))) or "-"
    c1, c2, c3 = st.columns(3)
    c1.metric("Sekolah tuan rumah", tuan)
    c2.metric("Petugas ditempatkan", len(cad))
    c3.metric("Sudah ada surat", len(ada_surat))
    st.warning(f"Memadam pusat **{no}** menjadikan sekolah {tuan} TIDAK AKTIF (tiada petugas dijana, tiada Petugas Hadir di SUP). Tindakan ini tidak boleh diundur; "
               "untuk mengaktifkan semula, tambah pusat baharu.")
    if ada_surat:
        st.error(f"🔒 {len(ada_surat)} petugas sudah mempunyai surat lantikan. Batalkan / padam surat itu di Sah Lantik dahulu sebelum memadam pusat.")
        return
    lepas = True
    if cad:
        lepas = st.checkbox(f"Lepaskan {len(cad)} petugas di pusat ini (kembali ke ruang belum ditempatkan)", key=f"pp_lepas_{kunci}")
    taip = st.text_input(f"Taip no pusat **{no}** untuk mengesahkan", key=f"pp_taip_{kunci}").strip().upper()
    if st.button("🗑️ Padam Pusat", type="primary", disabled=not (lepas and taip == no), key=f"pp_btn_{kunci}"):
        try:
            if cad:
                for c in cad:
                    _db().table("cadangan_sup").update({"kod_pusat": None, "status": "HANTAR KE PPD"}).eq("id", c.get("id")).execute()
            col = "no_pusat" if r.get("no_pusat") else "kod_pusat"
            _db().table("pusat_master").delete().eq(col, no).execute()
            _segar()
            try:
                import ppd_aliran as _al
                _al._clear()
            except Exception:
                pass
            st.success(f"✅ Pusat {no} dipadam; {len(cad)} petugas dilepaskan. Sekolah {tuan} kini tidak aktif.")
            st.rerun()
        except Exception as e:
            st.error(f"Gagal padam: {str(e)[:300]}")


def form_padam_sekolah(kod_ppd, kunci):
    """Batal sekolah (JPN): hanya jika tiada pusat dan tiada cadangan petugas."""
    sek = _sekolah_ppd(kod_ppd)
    if not sek:
        st.info("Tiada sekolah dalam PPD ini.")
        return
    kod = st.selectbox("Pilih sekolah untuk dibatalkan", sorted(sek), key=f"ps_sek_{kunci}", format_func=lambda k: f"{k} - {sek[k]}")
    pusat = [_no_pusat(r) for r in _pusat_daerah(kod_ppd) if kod in kod_tuan_rumah(r)]
    try:
        cad = _db().table("cadangan_sup").select("id").eq("kod_sekolah", kod).limit(5000).execute().data or []
    except Exception:
        cad = []
    c1, c2 = st.columns(2)
    c1.metric("Pusat di sekolah ini", len(pusat))
    c2.metric("Cadangan petugas dari sekolah", len(cad))
    if pusat:
        st.error("🔒 Sekolah ini masih ada pusat: " + ", ".join(pusat) + ". Padam pusat dahulu (submenu Selenggara Pusat › Batal Pusat).")
        return
    if cad:
        st.error(f"🔒 Sekolah ini ada {len(cad)} cadangan petugas. Batalkan cadangan itu dahulu.")
        return
    st.warning(f"Sekolah {kod} - {sek[kod]} akan dibuang daripada senarai sekolah. Tidak boleh diundur.")
    taip = st.text_input(f"Taip kod sekolah **{kod}** untuk mengesahkan", key=f"ps_taip_{kunci}").strip().upper()
    if st.button("🗑️ Batal / Padam Sekolah", type="primary", disabled=taip != kod, key=f"ps_btn_{kunci}"):
        try:
            _db().table("sekolah_master").delete().eq("kod_sekolah", kod).execute()
            _segar()
            st.success(f"✅ Sekolah {kod} dipadam.")
            st.rerun()
        except Exception as e:
            st.error(f"Gagal padam: {str(e)[:300]}")


def render_templat():
    st.header("📥 Muat Turun Templat")
    st.caption("Templat Excel kosong dengan satu baris contoh. Padam baris contoh sebelum import.")
    ppd = "BA"
    sekolah = pd.DataFrame([{"KOD SEKOLAH": "BBA0001", "NAMA SEKOLAH": "SMK CONTOH", "KOD PPD": ppd}])
    pusat = pd.DataFrame([{"KOD PUSAT": f"{ppd}101", "NAMA PUSAT": "SMK CONTOH", "KOD SEKOLAH": "BBA0001", "KOD PPD": ppd,
                           "ALAMAT PUSAT": "JALAN CONTOH, 40000 SHAH ALAM", "POSKOD": "40000", "BILIK": 10, "CALON": 200}])
    try:
        guru = core.get_template_guru()
    except Exception:
        guru = pd.DataFrame([{"kod_ppd": ppd.lower(), "kod_sekolah": "BBA0001", "nama_guru": "CONTOH: ALI BIN ABU", "ic_guru": "900101-01-1234",
                              "jantina": "LELAKI", "poskod_rumah": "40000", "alamat_rumah": "NO 1, JALAN CONTOH", "telefon_guru": "012-3456789"}])
    c1, c2, c3 = st.columns(3)
    c1.download_button("📥 Templat Sekolah Master", core.to_excel(sekolah), file_name="templat_sekolah_master.xlsx", key="tpl_sek", use_container_width=True)
    c2.download_button("📥 Templat Pusat Master", core.to_excel(pusat), file_name="templat_pusat_master.xlsx", key="tpl_pusat", use_container_width=True)
    c3.download_button("📥 Templat Guru Master", core.to_excel(guru), file_name="templat_guru_master.xlsx", key="tpl_guru", use_container_width=True)
    with st.expander("Lajur dalam setiap templat"):
        st.write("**Sekolah:** " + ", ".join(sekolah.columns))
        st.write("**Pusat:** " + ", ".join(pusat.columns))
        st.write("**Guru:** " + ", ".join(guru.columns))


def panel_ppd_pusat(kod_ppd):
    """Untuk PPD: tambah pusat (aktifkan sekolah) dan padam pusat (nyahaktif sekolah)."""
    t1, t2 = st.tabs(["➕ Tambah Pusat (aktifkan sekolah)", "🗑️ Padam Pusat (nyahaktifkan sekolah)"])
    with t1:
        form_tambah_pusat(kod_ppd, f"ppd_{kod_ppd}")
    with t2:
        form_padam_pusat(kod_ppd, f"ppd_{kod_ppd}")


def render_selenggara_sp(fly_cur):
    fly_cur = fly_cur or "sekolah"
    if fly_cur == "amali":
        import amali_sains as _am
        _am.render_jpn_amali()
        return
    if fly_cur == "templat":
        render_templat()
        return
    st.header("🛠️ Selenggara Sekolah & Pusat Peperiksaan")
    st.caption("Perubahan di sini terus masuk ke data PPD dan SUP serta dipaparkan di halaman hadapan PPD.")
    kod_ppd = _pilih_daerah(fly_cur)
    if fly_cur == "pusat":
        _panel_pusat(kod_ppd)
    else:
        _panel_sekolah(kod_ppd)
