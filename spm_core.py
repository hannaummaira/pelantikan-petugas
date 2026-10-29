"""
VERSION V37 - SERAGAM WARNA BIRU PEKAT & PUTIH SAHAJA (tajuk besar/kecil, menu, sub menu, SUP/PPD/JPN)
  - Logik / fungsi / pangkalan data TIDAK diubah (hanya warna)
VERSION V36 - FLYOUT SUB MENU UNTUK SEMUA (SUP / PPD / JPN) - BUTANG PETAK BIRU, TULISAN PUTIH
  - Menu utama & sub menu = butang petak biru/tulisan putih (butang aktif biru tua + jalur kuning)
  - Menu yang ada banyak bahagian/tab sekarang papar satu bahagian sahaja ikut pilihan flyout
  - Logik / fungsi / query pangkalan data TIDAK diubah (hanya cara paparan)
VERSION BARU - APP_33 - SISTEM LANTIKAN PETUGAS SPM 2026 - JPN TEMPLATE + ZIP PUKAL + SEKOLAH ASAL
Tarikh: 2026-10-23 23:59 - UPGRADE dari app_32.py LOCKED VERSION
Status: NEW FEATURE - TEMPLATE JPN SELARAS + ZIP + HANTAR SEKOLAH ASAL

UPGRADE V33:
1. ✅ Template surat lantikan ambil dari function JPN surat_templates_jpn (get_jpn_template_for_jawatan + render_jpn_template_html)
   - PPD punya akan diganti dengan template JPN jika JPN sudah cipta
   - Guna placeholder {{NAMA}}, {{IC}}, {{JAWATAN}}, {{SEKOLAH_ASAL}}, {{PUSAT}}, {{NO_SURAT}}, {{PPD}}, {{TARIKH}}
2. ✅ Bila PPD Jana Surat - keluar 2 button terus: PDF Kolektif (Pukal) + ZIP Individu Pukal (1000 PDF dalam 1 ZIP)
   - Guna create_zip_pukal_dari_JPN + generate_surat_kolektif_pdf_bytes_JPN
3. ✅ Surat yang dijana auto sampai ke sekolah asal petugas
   - Function hantar_surat_ke_sekolah_asal_bulk() update status SURAT_SAMPAI_SEKOLAH_ASAL
   - SUP boleh nampak di dashboard tab Surat Sampai Sekolah Asal
4. ✅ Semua tab (Keseluruhan, Ikut Pusat, Ikut Sekolah Asal) upgrade guna Template JPN + ZIP

BASE: app_32.py LOCKED VERSION OK
"""

import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO
import datetime
import math
import json
import re
import logging

_log = logging.getLogger("spm2026")

# ================= CONFIGURATION =================

# ---- v39: baris tema CSS dikumpul, dipaparkan setiap rerun melalui apply_global_ui() ----
_CSS_QUEUE = []
def _css_queue(html, **kw):
    _CSS_QUEUE.append(html)

def _secret(name, default=""):
    """Baca dari st.secrets / pembolehubah persekitaran dahulu; guna nilai asal jika tiada."""
    import os
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)



# ===== HIDE FORK & GITHUB CAT BUTTON (PPD MINTA BUANG) =====
def hide_fork_github():
    try:
        import streamlit as st
        st.markdown("""
        <style>
        /* Hide Fork button and GitHub cat */
        header {visibility: hidden !important;}
        header * {visibility: hidden !important;}
        [data-testid="stHeader"] {display: none !important; visibility: hidden !important;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        .stAppDeployButton {display: none !important; visibility: hidden !important;}
        /* Hide GitHub icon / Fork */
        a[href*="github"] {display: none !important;}
        button[kind="header"] {display: none !important;}
        /* Hide top right menu - Fork, Share etc */
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        /* Extra: hide any element containing Fork text */
        div:has(> button:has-text("Fork")) {display: none !important;}

        /* ===== TAMBAHAN HIDE FORK GITHUB - CONFIRM HILANG ===== */
        header[data-testid="stHeader"] {display: none !important;}
        .viewerBadge_container__1QSob {display: none !important;}
        .styles_viewerBadge__1yB5_ {display: none !important;}
        a.viewerBadge_link__1S137 {display: none !important;}
        /* Streamlit Cloud Fork button */
        [data-testid="stAppViewContainer"] > header {display: none !important;}
        iframe[title="streamlitApp"] {display: none !important;}

        </style>
        """, unsafe_allow_html=True)
    except:
        pass


# ================= TEMA CANTIK =================
def apply_pretty_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important; }
    .stApp { background: linear-gradient(180deg, #eef3fb 0%, #f8fafd 40%, #ffffff 100%); }
    .block-container { padding-top: 1.6rem !important; padding-bottom: 3rem !important; max-width: 1400px; }

    h1, h2, h3, h4 { color: #0d47a1; letter-spacing: -0.3px; font-weight: 700 !important; }

    /* Butang */
    .stButton > button, .stDownloadButton > button {
        border-radius: 12px !important; font-weight: 600 !important;
        border: 1px solid #cfd8e8 !important; transition: all .18s ease !important;
        box-shadow: 0 1px 2px rgba(13,71,161,.06);
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-1px); box-shadow: 0 6px 16px rgba(13,71,161,.18) !important;
        border-color: #1565c0 !important;
    }
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%) !important;
        color: #fff !important; border: none !important;
    }

    /* Tab */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background: #e8eef8; padding: 6px; border-radius: 14px; }
    .stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 18px; font-weight: 600; color: #0d47a1; }
    .stTabs [aria-selected="true"] { background: #ffffff !important; color: #0d47a1 !important; box-shadow: 0 2px 8px rgba(13,71,161,.15); }
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

    /* Kad metrik */
    [data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e1e8f5; border-radius: 16px;
        padding: 14px 18px; box-shadow: 0 2px 10px rgba(13,71,161,.07);
    }
    [data-testid="stMetricValue"] { color: #0d47a1; font-weight: 800; }
    [data-testid="stMetricLabel"] { color: #0d47a1; font-weight: 600; }

    /* Container bersempadan, expander, jadual */
    [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px !important; }
    [data-testid="stExpander"] { border: 1px solid #e1e8f5 !important; border-radius: 14px !important; background: #fff; overflow: hidden; }
    [data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; border: 1px solid #e1e8f5; }

    /* Input */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, [data-baseweb="select"] > div { border-radius: 10px !important; }

    /* Alert */
    [data-testid="stAlert"] { border-radius: 12px; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0d47a1 0%, #1565c0 100%); }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #ffffff !important; }
    [data-testid="stSidebar"] .stButton > button { background: rgba(255,255,255,.12) !important; border: 1px solid rgba(255,255,255,.25) !important; color: #fff !important; }

    /* Hero log masuk */
    .hero-login {
        background: linear-gradient(135deg, #0d47a1 0%, #1976d2 60%, #42a5f5 100%);
        color: #fff; border-radius: 22px; padding: 30px 24px; text-align: center; margin-bottom: 20px;
        box-shadow: 0 12px 32px rgba(13,71,161,.28);
    }
    .hero-login h1 { color: #fff !important; font-size: 1.7rem; margin: 0 0 6px 0; }
    .hero-login p { margin: 0; opacity: .92; font-size: .98rem; }
    .hero-stats { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; margin-top: 16px; }
    .hero-stats span { background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.28); padding: 6px 16px; border-radius: 999px; font-weight: 600; font-size: .9rem; }
    .app-footer { text-align: center; color: #0d47a1; font-size: .82rem; margin-top: 36px; padding-top: 14px; border-top: 1px solid #e1e8f5; }
    </style>
    """, unsafe_allow_html=True)


# ================= TAMBAHAN TEMA JPN SERAGAM - BIRU TUA PUTIH - TAK UBAH FUNGSI =================
JPN_COLORS = {
    "biru_tua": "#0D47A1",
    "biru_sederhana": "#1565C0",
    "biru_muda": "#E3F2FD",
    "biru_cair": "#EEF3FB",
    "biru_border": "#CFDBF0",
    "putih": "#FFFFFF",
    "hitam_teks": "#0D47A1",
    "kelabu_teks": "#0D47A1",
    "hijau_lulus": "#0D47A1",
    "hijau_bg": "#FFFFFF",
    "kuning_pending": "#0D47A1",
    "kuning_bg": "#E3F2FD",
    "merah_gagal": "#0D47A1",
    "merah_bg": "#BBDEFB",
    "jingga_need": "#0D47A1",
}

def _apply_jpn_kad_css():
    st.markdown(f'''
    <style>
    .jpn-kad {{
        background: {JPN_COLORS["putih"]};
        border: 1.5px solid {JPN_COLORS["biru_border"]};
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(13,71,161,.06);
        margin-bottom: 16px;
    }}
    .jpn-kad-biru {{
        background: linear-gradient(135deg, {JPN_COLORS["putih"]} 0%, {JPN_COLORS["biru_cair"]} 100%);
        border: 2px solid {JPN_COLORS["biru_tua"]};
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 14px rgba(13,71,161,.12);
        margin-bottom: 18px;
    }}
    .jpn-badge {{ display:inline-block; padding:4px 12px; border-radius:999px; font-weight:800; font-size:0.78rem; }}
    .jpn-badge-biru {{ background: {JPN_COLORS["biru_muda"]}; color: {JPN_COLORS["biru_tua"]}; border:1px solid {JPN_COLORS["biru_border"]}; }}
    .jpn-badge-hijau {{ background: {JPN_COLORS["hijau_bg"]}; color: {JPN_COLORS["hijau_lulus"]}; border:1px solid #FFFFFF; }}
    .jpn-badge-kuning {{ background: {JPN_COLORS["kuning_bg"]}; color: {JPN_COLORS["kuning_pending"]}; border:1px solid #E3F2FD; }}
    .jpn-no-pusat-box {{ background: {JPN_COLORS["kuning_bg"]}; border-left:4px solid {JPN_COLORS["kuning_pending"]}; padding:12px 16px; border-radius:8px; margin:12px 0; }}
    .jpn-no-pusat-label {{ font-size:0.82rem; color:{JPN_COLORS["kuning_pending"]}; font-weight:800; text-transform:uppercase; }}
    .jpn-no-pusat-value {{ font-size:1.35rem; font-weight:900; color:#0D47A1; letter-spacing:0.8px; word-spacing:6px; }}
    .surat-box img, .surat-container img, .tandatangan img {{ display:block !important; visibility:visible !important; }}
    </style>
    ''', unsafe_allow_html=True)


def jpn_kad_pusat(no_pusat_list_str, total_kelas, total_petugas, total_perlu, kod_sekolah=""):
    """v39: kad KEPERLUAN PENGAWAS gaya contoh (Dashboard SUP)."""
    import html as _h
    return (
        '<div class="sup-box">'
        f'<div class="sup-card-h"><span class="t">KEPERLUAN PENGAWAS - {_h.escape(str(kod_sekolah))}, JPN SELANGOR 2026</span>'
        f'<span class="sup-chip">NO PUSAT SEKOLAH ANDA: {_h.escape(str(no_pusat_list_str))}</span></div>'
        '<div class="sup-tiles">'
        f'<div class="sup-tile"><div class="l">JUMLAH KELAS</div><div class="n">{total_kelas}</div><div class="s">Bilik peperiksaan</div></div>'
        f'<div class="sup-tile"><div class="l">PETUGAS DIPERLUKAN</div><div class="n">{total_petugas}</div><div class="s">Termasuk simpanan</div></div>'
        f'<div class="sup-tile hl"><div class="l">SEKOLAH WAJIB CALONKAN</div><div class="n">{total_perlu} ORANG</div><div class="s">20% lebihan untuk tapisan PPD</div></div>'
        '</div></div>'
    )

def jpn_status_meter(total_pusat, total_calon, total_kelas, total_perlu, total_dicadang, ppd_code=""):
    kekurangan = total_perlu - total_dicadang
    if total_dicadang == 0:
        color = JPN_COLORS["merah_gagal"]; bg = JPN_COLORS["merah_bg"]; icon = "🔴"; teks = f"KURANG {kekurangan}"
    elif total_dicadang < total_perlu:
        color = JPN_COLORS["kuning_pending"]; bg = JPN_COLORS["kuning_bg"]; icon = "🟡"; teks = f"KURANG {kekurangan}"
    else:
        color = JPN_COLORS["hijau_lulus"]; bg = JPN_COLORS["hijau_bg"]; icon = "🟢"; teks = "CUKUP"
    return f'''
    <div style="background:{bg}; border:2px solid {color}; border-radius:12px; padding:14px 16px; margin-bottom:18px;">
        <div style="display:flex; gap:12px; align-items:center;">
            <div style="font-size:28px;">{icon}</div>
            <div>
                <div style="font-size:0.78rem; color:{JPN_COLORS["kelabu_teks"]}; font-weight:800;">RUMUSAN PPD {ppd_code} - {teks}</div>
                <div style="font-size:1rem; font-weight:800; color:{color};">{total_pusat} Pusat | {total_calon} Calon | {total_kelas} Kelas | Perlu {total_perlu} | Dicadang {total_dicadang}</div>
            </div>
        </div>
    </div>
    '''

def jpn_panduan_warna():
    return f'''
    <div class="jpn-kad" style="background:{JPN_COLORS["hijau_bg"]}; border-left:4px solid {JPN_COLORS["hijau_lulus"]}; padding:10px 14px;">
        <b>🟢 Panduan Warna:</b>
        <span class="jpn-badge jpn-badge-hijau" style="margin-left:8px;">HIJAU</span> = Sudah hantar ke PPD / Lulus
        <span class="jpn-badge jpn-badge-kuning" style="margin-left:8px;">KUNING</span> = Baru dicadangkan, belum hantar
    </div>
    '''
# ================= END TAMBAHAN TEMA =================




# ====== LOGO JATA NEGARA - MINIMAL TAMBAH (TAK KACAU LAIN) ======
JATA_B64 = """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"""
TANDA_B64 = """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"""
def get_jata_img_html(width=88):
    return f'<img src="data:image/png;base64,{JATA_B64}" width="{width}" style="display:block;margin:0 auto 12px auto;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.25));" />'

def show_hero_header():
    st.markdown(f"""
    <div style="background:linear-gradient(180deg,#ffffff 0%,#eef4ff 100%);border:1px solid #d6e2f5;border-radius:24px;padding:28px 20px 22px 20px;text-align:center;box-shadow:0 10px 30px rgba(13,71,161,0.08);margin-bottom:22px;">
        {get_jata_img_html(88)}
        <div style="font-family:Poppins,Inter,sans-serif;font-weight:800;font-size:1.45rem;color:#0d47a1;line-height:1.3;">SISTEM PELANTIKAN PETUGAS<br/>PEPERIKSAAN SPM TAHUN 2026</div>
        <div style="width:88px;height:4px;background:linear-gradient(90deg,#0d47a1,#1565c0);margin:14px auto 0 auto;border-radius:999px;"></div>
        <div style="font-weight:700;color:#0d47a1;font-size:0.98rem;margin-top:8px;">Jabatan Pendidikan Negeri Selangor</div>
        <div style="color:#0d47a1;font-size:0.86rem;margin-top:10px;max-width:620px;margin-left:auto;margin-right:auto;line-height:1.5;">Selamat Datang ke Portal Pelantikan — Sila pilih kategori petugas untuk log masuk. Sistem ini untuk urusan pelantikan petugas peperiksaan SPM Selangor 2026.</div>
        <div style="margin-top:16px;display:flex;justify-content:center;gap:8px;flex-wrap:wrap;">
            <span style="background:#fff;border:1px solid #dbe6f8;border-radius:999px;padding:6px 14px;font-weight:700;font-size:0.82rem;color:#0d47a1;">🏫 369 Sekolah</span>
            <span style="background:#fff;border:1px solid #dbe6f8;border-radius:999px;padding:6px 14px;font-weight:700;font-size:0.82rem;color:#0d47a1;">📍 506 Pusat</span>
            <span style="background:#fff;border:1px solid #dbe6f8;border-radius:999px;padding:6px 14px;font-weight:700;font-size:0.82rem;color:#0d47a1;">🎓 71,064 Calon</span>
        </div>
    </div>
    """, unsafe_allow_html=True)



SUPABASE_URL = _secret("SUPABASE_URL", "https://gnmaijhugkkvxejvsotk.supabase.co")
SUPABASE_KEY = _secret("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdubWFpamh1Z2trdnhlanZzb3RrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI0ODc4OTcsImV4cCI6MjEwODA2Mzg5N30.1YWg71nCwnQzP-KUzTdHR4rZAVCAesbKVqvVC1-X6lw")
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=600, show_spinner=False)
def get_jpn_templates_one():
    try:
        _supa = get_supabase()
        res = _supa.table("surat_templates_jpn").select("jawatan, template_html").execute()
        return {r["jawatan"].upper(): r["template_html"] for r in res.data if not str(r.get("jawatan", "")).startswith("__ASET_")} if res.data else {}
    except:
        return {}

# ===== NEW: JPN TEMPLATE FETCHER UNTUK PDF - WAJIB GUNA INI =====
@st.cache_data(ttl=300, show_spinner=False)
def get_jpn_template_for_jawatan(jawatan_str):
    """Ambil template JPN ikut jawatan (tepat dahulu; kalau tiada, padanan nama paling panjang)."""
    try:
        jw = re.sub(r"\s+", " ", str(jawatan_str or "")).upper().strip()
        if not jw:
            return None
        all_t = get_jpn_templates_one()
        norm = {re.sub(r"\s+", " ", k).upper().strip(): v for k, v in all_t.items() if v and len(v) > 30}
        if jw in norm:
            return norm[jw]
        # padanan separa: pilih nama jawatan paling panjang yang sepadan (elak "PENGAWAS" tersalah ambil "KETUA PENGAWAS")
        cands = [k for k in norm if k in jw or jw in k]
        if cands:
            return norm[max(cands, key=len)]
        return None
    except Exception:
        return None

def render_jpn_template_html(jawatan, nama, ic, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh, bilik_kebal=""):
    """Render template JPN dengan placeholder. Boleh guna {{NAMA}}, {{ nama }}, [NAMA] (huruf besar/kecil sama sahaja)."""
    try:
        tmpl = get_jpn_template_for_jawatan(jawatan)
        if not tmpl:
            return None
        nama = clean_nan(nama) or "Nama Guru"
        ic = clean_nan(ic)
        jawatan = clean_nan(jawatan) or "Petugas"
        sek_asal = clean_nan(sek_asal)
        nama_sek_asal = clean_nan(nama_sek_asal) or get_nama_sekolah_full(sek_asal, "")
        pusat = clean_nan(pusat)
        nama_pusat = clean_nan(nama_pusat) or pusat
        no_surat = clean_nan(no_surat)
        kod_ppd = clean_nan(kod_ppd)
        ppd_name = clean_nan(ppd_name) or kod_ppd
        tarikh = clean_nan(tarikh) or str(datetime.date.today().strftime("%d %B %Y"))
        bilik_kebal = clean_nan(bilik_kebal)

        sek_penuh = f"{sek_asal} - {nama_sek_asal}" if nama_sek_asal and nama_sek_asal.upper() != str(sek_asal).upper() else (nama_sek_asal or sek_asal)
        pusat_penuh = f"{pusat} - {nama_pusat}" if nama_pusat and nama_pusat.upper() != str(pusat).upper() else pusat

        replacements = {
            "NAMA": nama, "NAMA_GURU": nama,
            "IC": ic, "IC_GURU": ic,
            "JAWATAN": jawatan, "JAWATAN_CADANGAN": jawatan,
            "SEKOLAH_ASAL": sek_asal, "KOD_SEKOLAH_ASAL": sek_asal,
            "NAMA_SEKOLAH_ASAL": nama_sek_asal,
            "SEKOLAH_ASAL_PENUH": sek_penuh,
            "PUSAT": pusat, "KOD_PUSAT": pusat, "NO_PUSAT": pusat,
            "NAMA_PUSAT": nama_pusat,
            "PUSAT_PENUH": pusat_penuh,
            "BILIK_KEBAL": bilik_kebal, "KOD_BILIK_KEBAL": bilik_kebal,
            "NO_SURAT": no_surat,
            "PPD": kod_ppd, "KOD_PPD": kod_ppd,
            "PPD_NAME": ppd_name, "NAMA_PPD": ppd_name,
            "TARIKH": tarikh,
            "LOGO": _img_uri("logo"), "TANDATANGAN": _img_uri("tandatangan"), "TANDA_TANGAN": _img_uri("tandatangan"),
        }
        html = tmpl
        for k, v in replacements.items():
            v = str(v)
            esc = re.escape(k)
            html = re.sub(r"\{\{\s*" + esc + r"\s*\}\}", lambda m, v=v: v, html, flags=re.IGNORECASE)
            html = re.sub(r"\[" + esc + r"\]", lambda m, v=v: v, html, flags=re.IGNORECASE)
        html = _perbaiki_img_src(html)
        # FIX v40.1: jika {{LOGO}} asalnya bukan dalam <img> tag, tapi user letak {{LOGO}} sahaja, tukar jadi <img>
        # Dan pastikan kalau LOGO uri kosong, inject fallback
        import re as _re3
        logo_uri = _img_uri("logo")
        sign_uri = _img_uri("tandatangan")
        # Jika masih ada {{LOGO}} tinggal (sebab _img_uri kosong sebelum fix), ganti sekarang
        if logo_uri:
            html = _re3.sub(r"\{\{\s*LOGO\s*\}\}", f'<img src="{logo_uri}" style="width:90px;display:block;" />', html, flags=_re3.I)
            # kalau template tulis <img src="jata_negara_hd.png"> dan fix gagal, pastikan ada fallback
            if 'src=""' in html or "src=''" in html:
                html = html.replace('src=""', f'src="{logo_uri}"').replace("src=''", f"src='{logo_uri}'")
        if sign_uri:
            html = _re3.sub(r"\{\{\s*TANDATANGAN\s*\}\}", f'<img src="{sign_uri}" style="width:220px;display:block;" />', html, flags=_re3.I)
            html = _re3.sub(r"\{\{\s*TANDA_TANGAN\s*\}\}", f'<img src="{sign_uri}" style="width:220px;display:block;" />', html, flags=_re3.I)
        return html
    except Exception as e:
        _log.debug(f"render JPN error: {e}")
        return None


def _bungkus_html_surat(html):
    """Pastikan HTML templat lengkap (A4, UTF-8) sebelum jadi PDF / dipaparkan."""
    if "<html" in html.lower():
        return html
    return ("<html><head><meta charset='UTF-8'><style>@page { size: A4; margin: 15mm; } "
            "body { font-family: Helvetica, Arial, sans-serif; font-size: 10.5pt; }</style></head><body>"
            + html + "</body></html>")


def enjin_pdf_templat_ada():
    try:
        import xhtml2pdf  # noqa: F401
        return True
    except Exception:
        return False


def html_to_pdf_bytes(html):
    """Tukar HTML templat JPN kepada PDF (xhtml2pdf). Pulang None jika enjin tiada / gagal."""
    try:
        from xhtml2pdf import pisa
        import io
        buf = io.BytesIO()
        res = pisa.CreatePDF(src=_bungkus_html_surat(html), dest=buf, encoding="utf-8")
        if res.err:
            _surat_err("xhtml2pdf (templat JPN)", f"{res.err} ralat semasa menjana PDF dari templat")
            return None
        return buf.getvalue()
    except Exception as e:
        _log.debug(f"html_to_pdf error: {e}"); _surat_err("xhtml2pdf (templat JPN)", e)
        return None

# ---- v39: skop daerah ----
from scoped_db import ScopedSupabase
class _SessionScope:
    """Skop daerah PER SESI PENGGUNA (satu URL dikongsi ramai pengguna serentak).
    SCOPE["ppd"] -> None = JPN (semua daerah); "BG" = Gombak sahaja. Disimpan dalam st.session_state."""
    def __getitem__(self, key):
        try:
            return st.session_state.get("_scope_ppd")
        except Exception:
            return None
    def __setitem__(self, key, value):
        st.session_state["_scope_ppd"] = value
    def get(self, key, default=None):
        return self[key] or default

SCOPE = _SessionScope()
def set_scope(kod_ppd):
    SCOPE["ppd"] = (str(kod_ppd).strip().upper() or None) if kod_ppd else None
_RAW = get_supabase()
supa = ScopedSupabase(_RAW, lambda: SCOPE["ppd"])
def scope_label():
    return PPD_MAP.get(SCOPE["ppd"], SCOPE["ppd"]) if SCOPE["ppd"] else "Selangor"

def scope_cache(**cache_kw):
    """Seperti st.cache_data tetapi KUNCI CACHE merangkumi skop daerah sesi semasa.
    Tanpa ini, data satu daerah yang di-cache boleh dipaparkan kepada pengguna daerah lain."""
    import functools
    def deco(fn):
        @st.cache_data(**cache_kw)
        def _inner(scope_key, *a, **k):          # scope_key (tanpa garis bawah) = sebahagian kunci cache
            return fn(*a, **k)
        @functools.wraps(fn)
        def _outer(*a, **k):
            return _inner(SCOPE["ppd"] or "", *a, **k)
        _outer.clear = _inner.clear
        return _outer
    return deco

# Clear cache helper - untuk refresh button cepat
def clear_all_cache():
    st.cache_data.clear()
    st.cache_resource.clear()

# ✅ FIX: Buang trailing space dari KOD_DAERAH & PPD_MAP
KOD_DAERAH = ["BA", "BB", "BC", "BD", "BE", "BF", "BG", "BH", "BJ", "BK"]
PPD_MAP = {
    "BA": "Klang", "BB": "Kuala Langat", "BC": "Kuala Selangor",
    "BD": "Hulu Langat", "BE": "Hulu Selangor", "BF": "Sabak Bernam",
    "BG": "Gombak", "BH": "Petaling Perdana", "BJ": "Sepang", "BK": "Petaling Utama"
}

# ===== PANDUAN PASSWORD UNTUK TESTING 300 USER =====
ENABLE_TESTING_GUIDE = False
MAX_PDF_KOLEKTIF = 150
MAX_ZIP_FILES = 200

def show_testing_password_guide(df_sekolah_all):
    return


# ===== HELPER: WARNA HIJAU UNTUK GURU SUDAH HANTAR KE PPD =====
def style_nama_hijau_hantar(df_input):
    """Jika STATUS HANTAR/LULUS -> NAMA_GURU jadi hijau, belum hantar kekal biasa"""
    try:
        import pandas as pd
        # Cari column status
        status_col = None
        for cand in ["STATUS","status","Status"]:
            if cand in df_input.columns:
                status_col = cand
                break
        if status_col is None:
            return df_input

        # Buat styler
        def highlight_row(row):
            status_val = str(row.get(status_col, "") or "").upper()
            is_hantar = any(x in status_val for x in ["HANTAR","LULUS","DIHANTAR","DILULUSKAN"])
            is_baru = "DICADANGKAN" in status_val or status_val.strip()=="" or "BARU" in status_val
            styles = []
            for col in row.index:
                col_str = str(col).upper()
                if "NAMA_GURU" in col_str:
                    if is_hantar:
                        styles.append('background-color: #ffffff; color: #0d47a1; font-weight: 800; border-left: 4px solid #0d47a1;')
                    elif is_baru:
                        styles.append('background-color: #e3f2fd; color: #0d47a1; font-weight: 600;')
                    else:
                        styles.append('')
                else:
                    if is_hantar:
                        styles.append('background-color: #ffffff;')
                    elif is_baru:
                        styles.append('background-color: #e3f2fd;')
                    else:
                        styles.append('')
            return styles

        return df_input.style.apply(highlight_row, axis=1)
    except Exception as e:
        return df_input

def get_status_label(status_str):
    s = str(status_str).upper()
    if "LULUS" in s:
        return "✅ SUDAH HANTAR & LULUS PPD"
    elif "HANTAR" in s or "DIHANTAR" in s:
        return "🟢 SUDAH HANTAR KE PPD"
    else:
        return "🟡 BARU DICADANGKAN (Belum Hantar)"
# ===== END HELPER =====



# ================= CSS BIRU CAIR - BACKGROUND BIRU CAIR =================
_css_queue("""
<style>
[data-testid="stSidebar"] {display: none !important;}
.stSidebar {display: none !important;}
section[data-testid="stSidebar"] {display: none !important;}

/* ===== BACKGROUND BIRU CAIR ===== */
.stApp {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #e1f5fe 100%) !important;
    background-color: #e3f2fd !important;
    background-attachment: fixed !important;
}

/* Main container */
.main .block-container {
    background: transparent !important;
}

/* Metric cards - putih atas biru cair */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #90caf9 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: 0 2px 8px rgba(13, 71, 161, 0.1) !important;
}
[data-testid="stMetric"] label, [data-testid="stMetric"] div {
    color: #0d47a1 !important;
}
[data-testid="stMetricValue"] {
    color: #0d47a1 !important;
    font-weight: 800 !important;
}

[data-testid="stAlert"] {
    background: #ffffff !important;
    color: #0d47a1 !important;
    border: 1px solid #90caf9 !important;
    border-radius: 10px !important;
}
[data-testid="stAlert"] p, [data-testid="stAlert"] div {
    color: #0d47a1 !important;
}

[data-testid="stDataFrame"] {
    background: white !important;
    border-radius: 10px !important;
}

/* Custom sidebar - putih atas background biru cair */
.custom-sidebar {
    background: #ffffff !important;
    border-radius: 14px;
    padding: 16px;
    border: 2px solid #1976d2 !important;
    box-shadow: 0 4px 16px rgba(13, 71, 161, 0.15);
    height: fit-content;
    position: sticky;
    top: 10px;
}
.custom-sidebar h3 {
    font-size: 20px;
    color: #0d47a1 !important;
    font-weight: 800;
    margin-bottom: 4px;
}
.custom-sidebar p, .custom-sidebar span, .custom-sidebar div {
    color: #0d47a1 !important;
}
.custom-sidebar [data-testid="stCaptionContainer"] {
    color: #0d47a1 !important;
    opacity: 1 !important;
}
.custom-sidebar [data-testid="stCaptionContainer"] p {
    color: #0d47a1 !important;
    font-weight: 700 !important;
    font-size: 13px !important;
}

.no-pusat-box {
    background: #e3f2fd !important;
    border: 2px solid #0d47a1 !important;
    border-radius: 8px;
    padding: 10px 12px;
    margin: 10px 0;
}
.no-pusat-label {
    font-size: 11px;
    color: #0d47a1 !important;
    font-weight: 700;
}
.no-pusat-value {
    font-size: 18px;
    color: #0d47a1 !important;
    font-weight: 900;
}

.ppd-table {
    background: white !important;
    color: #0d47a1 !important;
}
.ppd-table th {
    background: #0d47a1 !important;
    color: white !important;
}
.ppd-table td {
    background: white !important;
    color: #0d47a1 !important;
    border-bottom: 1px solid #e0e0e0 !important;
}

.badge-merah, .badge-kuning, .badge-hijau {
    font-weight: 800 !important;
}
.badge-merah {background: #0d47a1 !important; border: 2px solid #0d47a1 !important; color: #ffffff !important;}
.badge-kuning {background: #bbdefb !important; border: 2px solid #0d47a1 !important; color: #0d47a1 !important;}
.badge-hijau {background: #ffffff !important; border: 2px solid #0d47a1 !important; color: #0d47a1 !important;}

[data-testid="stRadio"] label {
    color: #0d47a1 !important;
    font-weight: 600 !important;
}

.stButton button {
    font-weight: 700 !important;
}

[data-testid="stTabs"] button {
    color: #0d47a1 !important;
    font-weight: 600 !important;
}

h1, h2, h3, h4, h5, h6 {
    color: #0d47a1 !important;
}

[data-testid="stCaptionContainer"] p {
    color: #0d47a1 !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}

label {
    color: #0d47a1 !important;
    font-weight: 600 !important;
}

/* Card putih atas biru cair */
div[data-testid="stHorizontalBlock"] {
    background: transparent !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #90caf9 !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)


# ================= V37 - SERAGAM BIRU PEKAT & PUTIH (SUP / PPD / JPN) =================
_css_queue("""
<style>
:root { --biru-pekat:#0d47a1; --biru-gelap:#002171; --biru-sederhana:#1565c0; --biru-cair:#e3f2fd; --putih:#ffffff; accent-color:#0d47a1; }

/* ---- TAJUK BESAR (header / h1 / h2): palang biru pekat, tulisan putih ---- */
.stApp h1, .stApp h2 {
    background: #0d47a1 !important; color: #ffffff !important;
    padding: 12px 18px !important; border-radius: 8px !important;
    font-size: 1.35rem !important; font-weight: 800 !important;
    margin: 6px 0 14px 0 !important; letter-spacing: 0 !important;
}
/* ---- TAJUK KECIL (subheader / h3 / h4 / h5 / h6): palang biru pekat lebih kecil ---- */
.stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    background: #0d47a1 !important; color: #ffffff !important;
    padding: 8px 14px !important; border-radius: 6px !important;
    font-size: 1.02rem !important; font-weight: 700 !important;
    margin: 6px 0 10px 0 !important; letter-spacing: 0 !important;
}
.stApp h1 *, .stApp h2 *, .stApp h3 *, .stApp h4 *, .stApp h5 *, .stApp h6 * { color: #ffffff !important; }
/* tajuk di dalam kad/palang biru sedia ada: jangan bertindan */
.stApp [style*="linear-gradient"] h1, .stApp [style*="linear-gradient"] h2,
.stApp [style*="linear-gradient"] h3, .stApp [style*="linear-gradient"] h4,
.stApp [style*="background:#0d47a1"] h1, .stApp [style*="background:#0d47a1"] h2,
.stApp [style*="background:#0d47a1"] h3, .stApp [style*="background:#0d47a1"] h4,
.main-btn h3, .hero-login h1 {
    background: transparent !important; padding: 0 !important; margin: 0 0 4px 0 !important;
    color: #ffffff !important;
}
.main-btn h3 { color: #0d47a1 !important; }
.custom-sidebar h3 { margin-top: 0 !important; }

/* ---- LABEL & KAPSYEN: biru pekat (teks biasa ikut config.toml textColor) ---- */
[data-testid="stCaptionContainer"] p { color: #0d47a1 !important; }
.custom-sidebar p, .custom-sidebar span, .custom-sidebar div { color: #0d47a1 !important; }
[data-testid="stRadio"] label, [data-testid="stTabs"] button, label { color: #0d47a1 !important; }
.hero-login, .hero-login *, .hero-stats span { color: #ffffff !important; }

/* ---- TAB: biru pekat & putih ---- */
.stTabs [data-baseweb="tab-list"] { background: #0d47a1 !important; }
.stTabs [data-baseweb="tab"], .stTabs [data-baseweb="tab"] p, [data-testid="stTabs"] button { color: #ffffff !important; }
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"] p { background: #ffffff !important; color: #0d47a1 !important; }

/* ---- BUTANG BIASA & MUAT TURUN: biru pekat, tulisan putih ---- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    background: #0d47a1 !important; color: #ffffff !important; border: 1px solid #002171 !important;
}
.stButton > button *, .stDownloadButton > button *, .stFormSubmitButton > button * { color: #ffffff !important; }
.stButton > button:hover, .stDownloadButton > button:hover { background: #1565c0 !important; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] { background: #002171 !important; }

/* ---- AMARAN / MAKLUMAT / BERJAYA / RALAT: putih + jalur biru ---- */
[data-testid="stAlert"] { background: #ffffff !important; border: 1px solid #0d47a1 !important; border-left: 6px solid #0d47a1 !important; }
[data-testid="stAlert"] *, [data-testid="stAlert"] svg { color: #0d47a1 !important; fill: #0d47a1 !important; }

/* ---- Metrik, delta, pill, tag, slider, progress ---- */
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * { color: #0d47a1 !important; fill: #0d47a1 !important; }
[data-baseweb="tag"] { background: #0d47a1 !important; color: #ffffff !important; }
[data-baseweb="tag"] * { color: #ffffff !important; }
[data-testid="stProgress"] > div > div > div > div { background-color: #0d47a1 !important; }
[data-testid="stSlider"] [role="slider"] { background-color: #0d47a1 !important; }
input[type="checkbox"], input[type="radio"] { accent-color: #0d47a1 !important; }
[data-baseweb="checkbox"] > span:first-child, [data-baseweb="radio"] > div:first-child { border-color: #0d47a1 !important; }
[data-baseweb="checkbox"] input:checked + span, [data-baseweb="toggle"] input:checked + div { background-color: #0d47a1 !important; }
[data-baseweb="radio"] input:checked + div { background-color: #0d47a1 !important; border-color: #0d47a1 !important; }

/* ---- Kotak No Pusat: biru cair + sempadan biru pekat ---- */
.no-pusat-box, .jpn-no-pusat-box { background: #e3f2fd !important; border: 2px solid #0d47a1 !important; border-left-width: 6px !important; }
.no-pusat-label, .jpn-no-pusat-label, .no-pusat-value, .jpn-no-pusat-value { color: #0d47a1 !important; }
.jpn-badge-hijau { background: #ffffff !important; color: #0d47a1 !important; border: 1px solid #0d47a1 !important; }
.jpn-badge-kuning { background: #bbdefb !important; color: #0d47a1 !important; border: 1px solid #0d47a1 !important; }
</style>
""", unsafe_allow_html=True)
# ================= END V37 =================

# ================= HELPER FUNCTIONS (FORMULA & LOGIC) =================

def kira_kelas_dari_calon(jumlah_calon):
    """1 kelas = 20 calon, CEIL"""
    try:
        c = int(float(str(jumlah_calon).replace(",", "").strip() or 0))
        if c <= 0: return 0
        return math.ceil(c / 20)
    except: return 0

def kira_petugas_dari_kelas(jumlah_kelas):
    """User formula: kelas + 9 = petugas diperlukan"""
    try: return int(jumlah_kelas) + 9
    except: return 0

def kira_sekolah_perlu_calonkan(jumlah_kelas):
    """Sekolah perlu calonkan = petugas (kelas+9) + 1 KP +1 TKP +1 Penyelia = kelas+12"""
    try: return kira_petugas_dari_kelas(jumlah_kelas) + 3
    except: return 0


def clean_nan(val):
    """Bersihkan nan, None, 'nan', 'None' jadi string kosong"""
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none", "null", "nat", ""):
        return ""
    return s

def get_nama_sekolah_full(kod_sek, fallback=""):
    """Dapatkan nama penuh sekolah dari kod"""
    try:
        ks = str(kod_sek).upper().strip()
        if not ks:
            return fallback
        # Cari dalam supa sekolah_master
        try:
            res = supa.table("sekolah_master").select("nama_sekolah, kod_sekolah").eq("kod_sekolah", ks).limit(1).execute()
            if res.data:
                nm = res.data[0].get("nama_sekolah") or ""
                if nm and str(nm).lower() not in ("nan","none",""):
                    return str(nm).strip()
        except:
            pass
        # Jika fallback ada nama, guna
        if fallback and str(fallback).upper().strip() != ks:
            if str(fallback).lower() not in ("nan","none",""):
                return str(fallback).strip()
        return ks
    except:
        return fallback or str(kod_sek)

def generate_surat_html(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh):
    """Generate surat - PPD punya akan diganti dengan template JPN jika ada (JPN selaraskan)"""
    # Bersihkan semua input dari nan
    nama = clean_nan(nama) or "Nama Guru"
    ic = clean_nan(ic)
    jawatan = clean_nan(jawatan) or "Petugas Peperiksaan"
    sek_asal = clean_nan(sek_asal)
    nama_sek_asal = clean_nan(nama_sek_asal)
    pusat = clean_nan(pusat)
    nama_pusat = clean_nan(nama_pusat)
    # FIX: jika nama_pusat kosong, cari dari pusat_master ikut NO PUSAT
    if not nama_pusat or nama_pusat.upper() == pusat.upper():
        try:
            _pmap = build_pusat_map_from_master()
            if pusat and str(pusat).upper().strip() in _pmap and _pmap[str(pusat).upper().strip()]:
                nama_pusat = _pmap[str(pusat).upper().strip()]
        except:
            pass
    no_surat = clean_nan(no_surat) or clean_nan(tarikh) or "JPN.SPP.HHJH/0001"
    kod_ppd = clean_nan(kod_ppd) or "BA"
    ppd_name = clean_nan(ppd_name) or kod_ppd

    # === V37: TEMPLAT JPN DIUTAMAKAN (baca dari jadual surat_templates_jpn) ===
    _h37 = render_jpn_template_html(jawatan, nama, ic, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh)
    if _h37:
        return _bungkus_html_surat(_h37)

    # === CEK TEMPLATE JPN DULU - Jika JPN dah selaraskan, guna template JPN (PPD punya diganti) ===
    try:
        # Try load from surat_templates_jpn table
        tmpl_res = supa.table("surat_templates_jpn").select("template_html").eq("jawatan", jawatan.upper().strip()).limit(1).execute()
        if tmpl_res.data and len(tmpl_res.data) > 0:
            tmpl_html = tmpl_res.data[0].get("template_html")
            if tmpl_html and len(tmpl_html) > 50:
                # Guna template JPN - ganti placeholder
                html = tmpl_html
                replacements = {
                    "NAMA": nama,
                    "IC": ic,
                    "JAWATAN": jawatan,
                    "SEKOLAH_ASAL": sek_asal,
                    "NAMA_SEKOLAH_ASAL": nama_sek_asal or get_nama_sekolah_full(sek_asal, "") if "get_nama_sekolah_full" in globals() else sek_asal,
                    "PUSAT": pusat,
                    "NAMA_PUSAT": nama_pusat or pusat,
                    "NO_SURAT": no_surat,
                    "PPD": kod_ppd,
                    "PPD_NAME": ppd_name,
                    "TARIKH": tarikh,
                    "KOD_PUSAT": pusat,
                    "KOD_PPD": kod_ppd
                }
                for k,v in replacements.items():
                    html = html.replace("{{"+k+"}}", str(v)).replace("{{ "+k+" }}", str(v)).replace("{{"+k.lower()+"}}", str(v))
                # Wrap if not html
                if "<html>" not in html.lower():
                    html = f"<html><head><meta charset='UTF-8'></head><body>{html}</body></html>"
                return html
    except Exception as e:
        # If table not exists or error, fallback to old PPD template
        pass

    try:
        # Try session state JPN templates
        if "jpn_templates" in st.session_state:
            tmpl = st.session_state.jpn_templates.get(jawatan.upper().strip()) or st.session_state.jpn_templates.get(jawatan)
            if tmpl and len(tmpl) > 50:
                html = tmpl
                for k,v in {"NAMA": nama, "IC": ic, "JAWATAN": jawatan, "SEKOLAH_ASAL": sek_asal, "PUSAT": pusat, "NO_SURAT": no_surat, "PPD": kod_ppd, "TARIKH": tarikh}.items():
                    html = html.replace("{{"+k+"}}", str(v))
                return html
    except:
        pass

    # === FALLBACK: Template lama PPD (jika JPN belum sediakan) ===
    # Dapatkan nama penuh sekolah asal - bukan sekadar kod
    if nama_sek_asal and nama_sek_asal.upper() != sek_asal.upper():
        display_sek_asal = f"{sek_asal} - {nama_sek_asal}"
    else:
        try:
            full_nama = get_nama_sekolah_full(sek_asal, nama_sek_asal)
            if full_nama.upper() != sek_asal.upper():
                display_sek_asal = f"{sek_asal} - {full_nama}"
            else:
                display_sek_asal = sek_asal
        except:
            display_sek_asal = sek_asal or "Sekolah Asal"

    if nama_pusat and nama_pusat.upper() != pusat.upper():
        display_pusat = f"{pusat} - {nama_pusat}"
    else:
        display_pusat = pusat

    html = '<html><head><meta charset="UTF-8"><title>Surat Lantikan SPM 2026</title>'
    html += '<style>body{font-family:Times New Roman,serif;margin:40px;color:#000;}'
    html += '.surat{border:2px solid #000;padding:30px;margin-bottom:30px;page-break-after:always;background:white;}'
    html += '.header{text-align:center;border-bottom:3px double #000;padding-bottom:15px;margin-bottom:20px;}'
    html += '.kandungan{line-height:1.6;}'
    html += 'table.info{width:100%;border-collapse:collapse;margin:15px 0;}'
    html += 'table.info td{padding:5px 10px;}'
    html += 'table.info td:first-child{width:180px;font-weight:bold;}'
    html += '.tandatangan{margin-top:60px;display:flex;justify-content:space-between;}'
    html += '</style></head><body>'
    html += '<div class="surat"><div class="header">'
    html += '<h2>JABATAN PENDIDIKAN NEGERI SELANGOR</h2>'
    html += f'<h3>PEJABAT PENDIDIKAN DAERAH {kod_ppd} - {ppd_name}</h3>'
    html += f'<p>No Surat: {no_surat} | [Template JPN Selaras - Jika ada template JPN, surat ini akan diganti]</p></div>'
    html += '<div class="kandungan">'
    html += f'<p>Tarikh: {tarikh}</p>'
    html += '<p><strong>Tuan/Puan,</strong></p>'
    html += f'<p><strong>PELANTIKAN SEBAGAI {jawatan.upper()} PEPERIKSAAN SPM TAHUN 2026</strong></p>'
    html += '<p>Dengan hormatnya saya merujuk kepada perkara di atas.</p>'
    html += '<p>2. Sukacita dimaklumkan bahawa tuan/puan telah dilantik sebagai petugas peperiksaan SPM 2026 seperti butiran berikut:</p>'
    html += '<table class="info">'
    html += f'<tr><td>Nama</td><td>: {nama}</td></tr>'
    html += f'<tr><td>No. IC</td><td>: {ic}</td></tr>'
    html += f'<tr><td>Jawatan</td><td>: {jawatan}</td></tr>'
    html += f'<tr><td>Sekolah Asal</td><td>: {display_sek_asal}</td></tr>'
    html += f'<tr><td>Pusat Ditugaskan</td><td>: {display_pusat}</td></tr>'
    html += f'<tr><td>No Surat Lantikan</td><td>: {no_surat}</td></tr>'
    html += '</table>'
    html += '<p>3. Tuan/puan dikehendaki hadir bertugas di pusat peperiksaan yang telah ditetapkan mengikut jadual yang akan dimaklumkan kemudian.</p>'
    html += '<p>4. Kerjasama dan komitmen tuan/puan dalam menjayakan peperiksaan SPM 2026 amatlah dihargai dan didahului dengan ucapan terima kasih.</p>'
    html += '<p>Sekian.</p>'
    html += '<div class="footer"><p><strong>MALAYSIA MADANI</strong><br><strong>BERKHIDMAT UNTUK NEGARA</strong></p>'
    html += '<div class="tandatangan"><div><p>Yang benar,</p><br><br><br>'
    html += f'<p>_________________________<br><strong>Pegawai Pendidikan Daerah<br>PPD {kod_ppd} - {ppd_name}</strong></p></div>'
    html += '<div style="text-align:right;"><p>b.p Pengarah Pendidikan<br>Jabatan Pendidikan Negeri Selangor</p></div></div></div></div></body></html>'
    return html




def generate_surat_pdf_bytes(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh, no_rujukan=""):
    """Generate surat lantikan as PDF bytes - untuk download PDF - FIX nan & sekolah asal"""
    # Bersihkan
    try:
        nama = clean_nan(nama) or "Nama Guru"
        ic = clean_nan(ic)
        jawatan = clean_nan(jawatan) or "Petugas Peperiksaan"
        sek_asal = clean_nan(sek_asal)
        nama_sek_asal = clean_nan(nama_sek_asal)
        pusat = clean_nan(pusat)
        nama_pusat = clean_nan(nama_pusat)
        no_surat = clean_nan(no_surat) or "JPN.SPP.HHJH/0001"
        kod_ppd = clean_nan(kod_ppd) or "BA"
        ppd_name = clean_nan(ppd_name) or kod_ppd
        tarikh = clean_nan(tarikh) or str(datetime.date.today())

        # Nama penuh sekolah
        if nama_sek_asal and nama_sek_asal.upper() != sek_asal.upper():
            display_sek_asal = f"{sek_asal} - {nama_sek_asal}"
        else:
            try:
                full_nama = get_nama_sekolah_full(sek_asal, nama_sek_asal)
                display_sek_asal = full_nama if full_nama.upper() != sek_asal.upper() else f"{sek_asal} - {full_nama}" if full_nama else sek_asal
            except:
                display_sek_asal = sek_asal

        display_pusat = f"{pusat} - {nama_pusat}" if nama_pusat and nama_pusat.upper() != pusat.upper() else pusat
    except:
        display_sek_asal = sek_asal
        display_pusat = pusat

    # ===== V37: templat JPN diutamakan =====
    try:
        _h37 = render_jpn_template_html(jawatan, nama, ic, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh)
        if _h37:
            _pdf37 = html_to_pdf_bytes(_h37)
            if _pdf37:
                return _pdf37
    except Exception:
        pass

    # Cuba dengan reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)

        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('TitleCustom', parent=styles['Heading1'], fontSize=14, alignment=1, spaceAfter=6)
        style_heading = ParagraphStyle('HeadingCustom', parent=styles['Heading2'], fontSize=12, alignment=1, spaceAfter=4)
        style_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=4)

        story = []
        story.append(Paragraph("JABATAN PENDIDIKAN NEGERI SELANGOR", style_title))
        story.append(Paragraph(f"PEJABAT PENDIDIKAN DAERAH {ppd_name.upper() or kod_ppd}", style_heading))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>SURAT LANTIKAN PETUGAS PEPERIKSAAN SPM 2026</b>", style_heading))
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>No Rujukan: {no_surat}</b>", style_normal))
        story.append(Paragraph(f"Tarikh: {tarikh}", style_normal))
        story.append(Spacer(1, 8))

        isi = f"""
        <b>Tuan/Puan {nama} ({ic})</b><br/>
        {jawatan}<br/>
        {display_sek_asal}<br/><br/>
        Tuan/Puan,<br/><br/>
        <b>PELANTIKAN SEBAGAI {jawatan.upper()} PEPERIKSAAN SPM 2026</b><br/><br/>
        Dengan hormatnya dimaklumkan bahawa tuan/puan telah dilantik sebagai <b>{jawatan}</b> bagi Peperiksaan SPM Tahun 2026.<br/><br/>
        <b>Butiran Penempatan:</b><br/>
        - Sekolah Asal: {display_sek_asal}<br/>
        - Pusat Peperiksaan Ditugaskan: {display_pusat}<br/>
        - No Surat Lantikan: {no_surat}<br/>
        - Kod PPD: {kod_ppd} - {ppd_name}<br/><br/>
        Tuan/puan dikehendaki melapor diri di pusat peperiksaan yang ditetapkan pada tarikh dan masa yang akan dimaklumkan kelak.<br/><br/>
        Kerjasama tuan/puan amatlah dihargai dan didahului dengan ucapan terima kasih.<br/><br/>
        Sekian.<br/><br/>
        <b>"BERKHIDMAT UNTUK NEGARA"</b><br/><br/>
        Saya yang menjalankan amanah,<br/><br/><br/>
        <b>PEGAWAI PENDIDIKAN DAERAH</b><br/>
        {ppd_name}<br/>
        PPD {kod_ppd}<br/>
        """
        story.append(Paragraph(isi, style_normal))
        story.append(Spacer(1, 12))

        data_footer = [
            [f"No Surat: {no_surat}", f"Pusat: {display_pusat}"],
            [f"Sekolah Asal: {display_sek_asal}", f"Jawatan: {jawatan}"]
        ]
        t = Table(data_footer, colWidths=[85*mm, 85*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f5f5f5')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        story.append(t)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        # Fallback simple canvas
        try:
            import io
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 800, f"SURAT LANTIKAN SPM 2026 - {kod_ppd}")
            c.setFont("Helvetica", 10)
            y = 780
            lines = [
                f"No Surat: {no_surat}",
                f"Nama: {nama}",
                f"IC: {ic}",
                f"Jawatan: {jawatan}",
                f"Sekolah Asal: {display_sek_asal}",
                f"Pusat Tugas: {display_pusat}",
                f"Tarikh: {tarikh}",
                f"PPD: {kod_ppd} - {ppd_name}",
                "",
                "Tuan/Puan telah dilantik sebagai petugas peperiksaan SPM 2026.",
                f"Sila lapor diri di pusat {pusat}.",
            ]
            for line in lines:
                c.drawString(50, y, line[:100])
                y -= 20
                if y < 50:
                    c.showPage()
                    y = 800
            c.save()
            return buffer.getvalue()
        except Exception as e2:
            # Ultimate fallback: return HTML as bytes with pdf mime (still downloadable)
            try:
                html_fallback = generate_surat_html(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh)
                return html_fallback.encode('utf-8')
            except:
                return None


def generate_surat_kolektif_pdf_bytes(surat_list, kod_ppd, ppd_name, title="SURAT LANTIKAN KESELURUHAN"):
    """Generate kolektif PDF - V37: gabung surat individu ikut templat JPN; jika gagal guna ringkasan lama"""
    try:
        _kol = generate_surat_kolektif_pdf_bytes_JPN(surat_list, kod_ppd, ppd_name, title_prefix=title)
        if _kol:
            return _kol
    except Exception:
        pass
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib import colors
        import io
        from datetime import date

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=10*mm, bottomMargin=10*mm)
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('TitleCustom', parent=styles['Heading1'], fontSize=13, alignment=1, spaceAfter=6, leading=14)
        style_heading = ParagraphStyle('HeadingCustom', parent=styles['Heading2'], fontSize=11, alignment=1, spaceAfter=6)
        style_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=9, leading=12, spaceAfter=4)
        style_ruj = ParagraphStyle('RujCustom', parent=styles['Normal'], fontSize=9, alignment=2, leading=11)
        style_header = ParagraphStyle('HeaderCustom', parent=styles['Normal'], fontSize=10, leading=12)

        story = []

        # HEADER RASMI - Logo tepi kiri effect
        header_text = """<b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br/>JABATAN PENDIDIKAN NEGERI SELANGOR<br/><font size=8>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam</font>"""
        story.append(Paragraph(header_text, style_header))
        story.append(Paragraph("<hr/>", style_normal))

        # Ruj Kanan = No Surat
        no_surat_kolektif = surat_list[0].get('no_surat') if surat_list and len(surat_list)>0 else f"JPN.SPP.HHJH/PPD.{kod_ppd}/0001"
        tarikh_str = date.today().strftime('%d %B %Y')
        ruj_html = f"""<font size=9>Ruj. Kami: {no_surat_kolektif}<br/>Tarikh: {tarikh_str}</font>"""
        story.append(Paragraph(ruj_html, style_ruj))
        story.append(Spacer(1, 8))

        story.append(Paragraph(f"<b>{title}</b>", style_title))
        story.append(Paragraph(f"PPD {kod_ppd} - {ppd_name} - {len(surat_list)} Guru", style_heading))
        story.append(Spacer(1, 8))

        for idx, s in enumerate(surat_list, start=1):
            nama = s.get('nama','') or s.get('NAMA','') or s.get('NAMA GURU','')
            ic = s.get('ic','') or s.get('IC','')
            jawatan = s.get('jawatan') or s.get('JAWATAN') or ''
            sek_asal = s.get('sekolah_asal') or s.get('SEKOLAH ASAL') or ''
            nama_sek_asal = s.get('nama_sekolah_asal') or s.get('NAMA SEKOLAH ASAL') or ''
            pusat = s.get('pusat') or s.get('PUSAT') or ''
            no_surat = s.get('no_surat') or s.get('NO SURAT') or s.get('NO SURAT BARU') or ''
            nama_pusat = s.get('nama_pusat') or s.get('NAMA PUSAT') or ''
            bilik_kebal = s.get('bilik_kebal') or s.get('BILIK KEBAL') or ''
            sekolah_asal_full = f"{sek_asal} - {nama_sek_asal}" if nama_sek_asal else sek_asal

            isi = f"""
            <b>{idx}. {nama} ({ic}) - {jawatan}</b><br/>
            <font size=8>
            No Surat: <b>{no_surat}</b> | Sekolah Asal: {sekolah_asal_full}<br/>
            Pusat: {pusat} - {nama_pusat} | Bilik Kebal: {bilik_kebal}<br/>
            Tuan/Puan telah dilantik sebagai <b>{jawatan}</b> SPM 2026 di pusat {pusat}. Sila lapor diri mengikut arahan.<br/>
            </font>
            """
            story.append(Paragraph(isi, style_normal))
            story.append(Spacer(1, 6))
            if idx % 5 == 0 and idx < len(surat_list):
                story.append(PageBreak())
                story.append(Paragraph(header_text, style_header))
                story.append(Paragraph("<hr/>", style_normal))
                story.append(Paragraph(ruj_html, style_ruj))
                story.append(Spacer(1, 8))

        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>MALAYSIA MADANI - BERKHIDMAT UNTUK NEGARA</b><br/><br/>(DATIN WAN NOR ASHIKIN BINTI ABU KASSIM)<br/>Pengarah Pendidikan, JPN Selangor", style_normal))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        _log.debug(f"Error kolektif: {e}")
        return None




def generate_surat_penyelia_kawasan_html(nama, ic, sek_asal, nama_sek_asal, telefon, kod_bilik_kebal, nama_bilik_kebal, alamat_bilik_kebal, pusat_jagaan_list, no_surat, kod_ppd, ppd_name, tarikh):
    """Surat khas untuk Penyelia Kawasan yang ditempatkan ke Bilik Kebal"""
    # V34: Ensure pusat_jagaan_list is not empty, fallback to kod_pusat if needed
    if not pusat_jagaan_list:
        try:
            # Try from data JSON
            if isinstance(data_dict, dict):
                pusat_jagaan_list = data_dict.get("pusat_jagaan") or data_dict.get("pusat_jagaan_str","").split(",") if isinstance(data_dict.get("pusat_jagaan_str"), str) else []
        except:
            pass
    pusat_jagaan_str = ", ".join(pusat_jagaan_list) if isinstance(pusat_jagaan_list, list) else str(pusat_jagaan_list)
    pusat_jagaan_table = ""
    if isinstance(pusat_jagaan_list, list) and pusat_jagaan_list:
        for idx, p in enumerate(pusat_jagaan_list, 1):
            pusat_jagaan_table += f"<tr><td>{idx}</td><td>{p}</td></tr>"
    else:
        pusat_jagaan_table = f"<tr><td>1</td><td>{pusat_jagaan_str}</td></tr>"

    html = '<html><head><meta charset="UTF-8"><title>Surat Lantikan Penyelia Kawasan SPM 2026</title>'
    html += '<style>body{font-family:Times New Roman,serif;margin:40px;color:#000;}'
    html += '.surat{border:3px double #0d47a1;padding:30px;margin-bottom:30px;background:white;page-break-after:always;}'
    html += '.header{text-align:center;border-bottom:3px double #0d47a1;padding-bottom:15px;margin-bottom:20px;}'
    html += '.header h2{color:#0d47a1;margin:5px 0;}'
    html += '.kandungan{line-height:1.7;font-size:14px;}'
    html += 'table.info{width:100%;border-collapse:collapse;margin:15px 0;}'
    html += 'table.info td{padding:8px 12px;border:1px solid #ddd;}'
    html += 'table.info td:first-child{width:200px;font-weight:bold;background:#e3f2fd;}'
    html += 'table.pusat{width:100%;border-collapse:collapse;margin:10px 0;}'
    html += 'table.pusat th, table.pusat td{border:1px solid #0d47a1;padding:8px;text-align:left;}'
    html += 'table.pusat th{background:#0d47a1;color:white;}'
    html += '.tandatangan{margin-top:60px;display:flex;justify-content:space-between;}'
    html += '.penting{background:#e3f2fd;border-left:5px solid #0d47a1;padding:12px;margin:15px 0;}'
    html += '</style></head><body>'
    html += '<div class="surat"><div class="header">'
    html += '<h2>JABATAN PENDIDIKAN NEGERI SELANGOR</h2>'
    html += f'<h3>PEJABAT PENDIDIKAN DAERAH {kod_ppd} - {ppd_name}</h3>'
    html += '<h3 style="color:#0d47a1;">SURAT LANTIKAN PENYELIA KAWASAN SPM 2026</h3>'
    html += f'<p><strong>No Rujukan: {no_surat}</strong> | Tarikh: {tarikh}</p></div>'
    html += '<div class="kandungan">'
    html += '<p><strong>Tuan/Puan,</strong></p>'
    html += '<p><strong>PELANTIKAN SEBAGAI PENYELIA KAWASAN PEPERIKSAAN SPM TAHUN 2026 - PENEMPATAN DI BILIK KEBAL</strong></p>'
    html += '<p>Dengan hormatnya saya merujuk kepada perkara di atas dan sukacita dimaklumkan bahawa tuan/puan telah dilantik sebagai <strong>Penyelia Kawasan SPM 2026</strong> dengan butiran seperti berikut:</p>'
    html += '<table class="info">'
    html += f'<tr><td>Nama Penyelia Kawasan</td><td>{nama}</td></tr>'
    html += f'<tr><td>No. Kad Pengenalan</td><td>{ic}</td></tr>'
    html += f'<tr><td>Sekolah Asal</td><td>{sek_asal} - {nama_sek_asal}</td></tr>'
    html += f'<tr><td>No. Telefon</td><td>{telefon}</td></tr>'
    html += f'<tr><td>Jawatan Lantikan</td><td><strong>PENYELIA KAWASAN</strong></td></tr>'
    html += f'<tr><td>Dilantik di Bilik Kebal</td><td><strong>{kod_bilik_kebal} - {nama_bilik_kebal}</strong><br><small>{alamat_bilik_kebal}</small></td></tr>'
    html += f'<tr><td>No Surat Lantikan</td><td>{no_surat}</td></tr>'
    html += f'<tr><td>PPD</td><td>{kod_ppd} - {ppd_name}</td></tr>'
    html += '</table>'

    html += '<div class="penting">'
    html += '<strong>BERTANGGUNGJAWAB ATAS PUSAT-PUSAT PEPERIKSAAN:</strong>'
    html += '<p>Penyelia Kawasan ini bertanggungjawab memantau dan menyelia pusat-pusat peperiksaan berikut di bawah Bilik Kebal yang berkenaan:</p>'
    html += '</div>'

    html += '<table class="pusat">'
    html += '<tr><th>Bil</th><th>Kod Pusat / Pusat Peperiksaan Di Bawah Jagaan</th></tr>'
    html += pusat_jagaan_table
    html += '</table>'

    html += f'<p><strong>Jumlah Pusat Jagaan: {len(pusat_jagaan_list) if isinstance(pusat_jagaan_list, list) else 1} pusat</strong></p>'

    html += '<p>3. <strong>Tugas dan Tanggungjawab Penyelia Kawasan:</strong></p>'
    html += '<ul>'
    html += '<li>Bertanggungjawab sepenuhnya ke atas keselamatan dan kelancaran pengurusan kertas soalan di Bilik Kebal yang ditetapkan;</li>'
    html += f'<li>Menyelia dan memantau {len(pusat_jagaan_list) if isinstance(pusat_jagaan_list, list) else 1} pusat peperiksaan di bawah jagaan Bilik Kebal {kod_bilik_kebal};</li>'
    html += '<li>Memastikan semua prosedur keselamatan dan tatacara peperiksaan SPM dipatuhi;</li>'
    html += '<li>Melaporkan sebarang isu atau masalah kepada Pegawai Pendidikan Daerah dengan segera;</li>'
    html += '<li>Hadir bertugas mengikut jadual yang ditetapkan oleh PPD.</li>'
    html += '</ul>'

    html += '<p>4. Tuan/puan dikehendaki hadir taklimat Penyelia Kawasan yang akan dimaklumkan kemudian oleh PPD.</p>'
    html += '<p>5. Kerjasama, komitmen dan integriti tuan/puan dalam menjayakan peperiksaan SPM 2026 amatlah dihargai.</p>'
    html += '<p>Sekian, terima kasih.</p>'

    html += '<div class="footer"><p><strong>MALAYSIA MADANI</strong><br><strong>BERKHIDMAT UNTUK NEGARA</strong></p>'
    html += '<div class="tandatangan"><div><p>Yang benar,</p><br><br><br>'
    html += f'<p>_________________________<br><strong>Pegawai Pendidikan Daerah<br>PPD {kod_ppd} - {ppd_name}</strong><br><small>Tarikh: {tarikh}</small></p></div>'
    html += '<div style="text-align:right;"><p>b.p Pengarah Pendidikan<br>Jabatan Pendidikan Negeri Selangor<br><br><small>Salinan: Pengetua {nama_sek_asal}<br>Sekolah Asal Penyelia Kawasan</small></p></div></div></div></div></div>'
    html += '</body></html>'
    return html

def generate_surat_kolektif_html(guru_list, kod_ppd, ppd_name, tarikh, prefix):

    # guru_list is list of dicts with NAMA, IC, etc
    html = '<html><head><meta charset="UTF-8"><title>Surat Lantikan Kolektif</title>'
    html += '<style>body{font-family:Arial,sans-serif;margin:20px;} .surat{border:1px solid #ccc;padding:20px;margin:10px 0;} h2{text-align:center;}</style></head><body>'
    html += f'<h2>SURAT LANTIKAN PETUGAS SPM 2026 - PPD {kod_ppd}</h2>'
    html += f'<p>Tarikh: {tarikh} | Jumlah: {len(guru_list)} guru</p><hr>'
    for g in guru_list:
        html += generate_surat_html(g["NAMA GURU"], g["IC"], g["JAWATAN"], g["SEKOLAH ASAL"], g["NAMA SEKOLAH ASAL"], g["PUSAT DITEMPATKAN"], g["NAMA PUSAT DITEMPATKAN"], g["NO SURAT"], kod_ppd, ppd_name, tarikh)
    html += '</body></html>'
    return html


def safe_count(table_name):
    """Count dengan fallback kalau RLS block count exact"""
    try:
        res = supa.table(table_name).select("*", count="exact").limit(1).execute()
        if res.count is not None and res.count > 0: return res.count
        if res.data and len(res.data) > 0: return len(res.data)
        return 0
    except: return 0

def get_sekolah(kod):
    for col in ["kod_sekolah", "kod_sekolah_tuan_rumah", "KOD_SEKOLAH"]:
        try:
            res = supa.table("sekolah_master").select("*").eq(col, kod.upper()).limit(1).execute()
            if res.data:
                row = res.data[0]
                return {
                    "kod_sekolah": row.get("kod_sekolah") or row.get("KOD_SEKOLAH") or kod,
                    "nama_sekolah": row.get("nama_sekolah") or row.get("NAMA_SEKOLAH") or f"SEKOLAH {kod}",
                    "kod_ppd": row.get("kod_ppd") or row.get("KOD_PPD") or "BH",
                    "ppd": row.get("ppd") or row.get("PPD") or "Petaling Perdana",
                    "_raw": row
                }
        except: continue
    return {"kod_sekolah": kod, "nama_sekolah": f"SEKOLAH {kod}", "kod_ppd": "BH", "ppd": "Petaling Perdana"}

@scope_cache(ttl=300, show_spinner=False)
def get_guru_df(kod_sekolah):
    try:
        res = None
        for col in ["kod_sekolah", "KOD_SEKOLAH", "kod_sekolah_tuan_rumah"]:
            try:
                r = supa.table("guru_master").select("*").eq(col, kod_sekolah.upper()).limit(2000).execute()
                if r.data: res=r; break
            except: continue

        if not res:
            res = supa.table("guru_master").select("*").eq("kod_sekolah", kod_sekolah.upper()).limit(2000).execute()

        rows = []
        sekolah_map_guru = {}
        try:
            res_sek = supa.table("sekolah_master").select("kod_sekolah,nama_sekolah").limit(2000).execute()
            for s in res_sek.data or []:
                k = (s.get("kod_sekolah") or s.get("KOD_SEKOLAH") or "").upper()
                n = s.get("nama_sekolah") or s.get("NAMA_SEKOLAH") or ""
                if k: sekolah_map_guru[k] = n
        except: pass

        for r in res.data or []:
            d = r.get("data") or {}
            if isinstance(d, str):
                try: d = json.loads(d)
                except: d = {}

            def _nk(x): return re.sub(r"[^A-Z0-9]", "", str(x).upper())
            _kosong_val = ("", "none", "null", "nan", "n/a", "-")
            _dn, _rn = {}, {}

            for _k, _v in d.items():
                if _v is not None and not isinstance(_v, (dict, list)) and str(_v).strip().lower() not in _kosong_val:
                    _dn.setdefault(_nk(_k), str(_v).strip())
            for _k, _v in r.items():
                if _v is not None and not isinstance(_v, (dict, list)) and str(_v).strip().lower() not in _kosong_val:
                    _rn.setdefault(_nk(_k), str(_v).strip())

            def get_val(*keys, default=""):
                for k in keys:
                    nk = _nk(k)
                    if nk in _dn: return _dn[nk]
                    if nk in _rn: return _rn[nk]
                return default

            ic_val = get_val("IC", "ic_guru", "IC_GURU", "ic", "no_ic", "NO_KP", "NO KP")
            nama_val = get_val("NAMA GURU", "nama_guru", "NAMA_GURU", "nama", "NAMA")
            jantina_val = get_val("JANTINA", "jantina", "JANTINA_GURU", "Jantina", "SEX")
            poskod_val = get_val("POSKOD_RUMAH", "poskod_rumah", "POSKOD", "poskod", "POSKOD RUMAH")
            alamat_val = get_val("ALAMAT_RUMAH", "alamat_rumah", "ALAMAT RUMAH", "alamat", "ALAMAT")
            telefon_val = get_val("TELEFON_GURU", "telefon_guru", "NO TELEFON GURU", "TELEFON", "no_telefon")
            email_val = get_val("EMAIL_GURU", "email_guru", "EMAIL GURU", "EMAIL", "email", "EMEL", "EMEL GURU", "E-MEL", "E-MAIL")
            pengalaman_val = get_val("PENGALAMAN_SPM", "pengalaman_spm", "PENGALAMAN", "pengalaman")
            jawatan_val = get_val("JAWATAN_CADANGAN", "jawatan_cadangan", "JAWATAN CADANGAN", "jawatan")
            kod_ppd_val = get_val("KOD_PPD", "kod_ppd", "kod_ppd_asal", "KOD_PPD_ASAL", "ppd", "PPD")
            kod_sek_val = get_val("KOD_SEKOLAH", "kod_sekolah", "KOD SEKOLAH", "kod_sekolah_asal", "KOD_SEKOLAH_ASAL", default=kod_sekolah)
            nama_sek_val = get_val("NAMA_SEKOLAH", "nama_sekolah", "NAMA SEKOLAH", "sekolah_asal", "NAMA_SEKOLAH_ASAL")
            no_pusat_asal_val = get_val("NO_PUSAT_ASAL", "no_pusat_asal", "NO PUSAT ASAL", "PUSAT ASAL", "pusat_asal", "KOD PUSAT ASAL", "NO_PUSAT", "KOD PUSAT")

            if not nama_sek_val or nama_sek_val == "" or nama_sek_val == kod_sek_val:
                nama_sek_val = sekolah_map_guru.get(kod_sek_val.upper(), "") or sekolah_map_guru.get(kod_sekolah.upper(), "") or kod_sek_val

            if not kod_ppd_val or kod_ppd_val == "":
                kod_ppd_val = kod_sekolah[:2] if len(kod_sekolah) >= 2 else "BA"

            if not jawatan_val or jawatan_val.strip() == "":
                jawatan_val = "Pengawas Peperiksaan"

            rows.append({
                "id": r.get("id"),
                "NAMA GURU": nama_val, "IC": ic_val, "JANTINA": jantina_val,
                "POSKOD_RUMAH": poskod_val, "ALAMAT_RUMAH": alamat_val,
                "TELEFON": telefon_val, "TELEFON_GURU": telefon_val,
                "EMAIL_GURU": email_val, "EMAIL": email_val,
                "JAWATAN CADANGAN": jawatan_val, "JAWATAN_CADANGAN": jawatan_val,
                "PENGALAMAN_SPM": pengalaman_val, "PENGALAMAN": pengalaman_val,
                "KOD_PPD": kod_ppd_val, "KOD_PPD_ASAL": kod_ppd_val,
                "KOD SEKOLAH": kod_sek_val, "KOD_SEKOLAH": kod_sek_val,
                "KOD_SEKOLAH_ASAL": kod_sek_val,
                "NAMA_SEKOLAH_ASAL": nama_sek_val, "NAMA_SEKOLAH": nama_sek_val,
                "NO_PUSAT_ASAL": no_pusat_asal_val, "ALAMAT": alamat_val,
                "data_full": d if isinstance(d, dict) else {}, "raw": r
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

@scope_cache(ttl=300, show_spinner=False)
def get_pusat_df():
    try:
        res = supa.table("pusat_master").select("*").limit(2000).execute()
        df = pd.DataFrame(res.data or [])
        if not df.empty:
            df_norm = df.copy()
            if "no_pusat" in df_norm.columns: df_norm["kod_pusat_std"] = df_norm["no_pusat"]
            elif "kod_pusat" in df_norm.columns: df_norm["kod_pusat_std"] = df_norm["kod_pusat"]
            elif "NO_PUSAT" in df_norm.columns: df_norm["kod_pusat_std"] = df_norm["NO_PUSAT"]
            else: df_norm["kod_pusat_std"] = df_norm.iloc[:, 1] if len(df_norm.columns) > 1 else " "

            if "nama_pusat" in df_norm.columns: df_norm["nama_pusat_std"] = df_norm["nama_pusat"]
            elif "NAMA_PUSAT" in df_norm.columns: df_norm["nama_pusat_std"] = df_norm["NAMA_PUSAT"]
            else: df_norm["nama_pusat_std"] = df_norm.get("nama_sekolah", " ")
            return df
    except Exception as e:
        st.error(f"pusat_master error: {e}")
    return pd.DataFrame()

@scope_cache(ttl=120, show_spinner=False)
def get_cadangan_df(kod_ppd=None, kod_sekolah=None):
    try:
        # Fetch with larger limit and without strict eq first to avoid missing data due to case issues
        try:
            # Always fetch all then filter locally for robustness
            res = supa.table("cadangan_sup").select("*").limit(10000).execute()
        except:
            res = supa.table("cadangan_sup").select("*").limit(5000).execute()

        df = pd.DataFrame(res.data or [])
        if df.empty:
            return df

        # Normalize - merge data json and top-level columns
        norm_rows = []
        for _, r in df.iterrows():
            row_dict = {}
            for k, v in r.items():
                if k != 'data':
                    row_dict[k] = v
                else:
                    if isinstance(v, dict):
                        row_dict.update(v)
                    elif isinstance(v, str):
                        try:
                            parsed = json.loads(v)
                            if isinstance(parsed, dict):
                                row_dict.update(parsed)
                        except:
                            pass
            # Normalize keys to upper for consistency but keep original too
            # Ensure critical fields
            # JAWATAN - normalize various possible keys
            jaw = row_dict.get('JAWATAN_CADANGAN') or row_dict.get('jawatan_cadangan') or row_dict.get('JAWATAN') or row_dict.get('jawatan') or row_dict.get('JAWATAN CADANGAN') or ''
            jaw = str(jaw).strip()
            # Clean jawatan: remove extra spaces, normalize case for comparison but keep original display
            jaw_clean = ' '.join(jaw.split())
            row_dict['JAWATAN_CADANGAN'] = jaw_clean
            row_dict['jawatan_cadangan'] = jaw_clean
            row_dict['JAWATAN_CADANGAN_NORM'] = jaw_clean.lower()

            # KOD PPD
            kppd = row_dict.get('KOD_PPD') or row_dict.get('kod_ppd') or row_dict.get('KOD_PPD_ASAL') or row_dict.get('kod_ppd_asal') or ''
            row_dict['KOD_PPD'] = str(kppd).strip().upper()

            # KOD SEKOLAH ASAL
            ksa = row_dict.get('KOD_SEKOLAH_ASAL') or row_dict.get('kod_sekolah_asal') or row_dict.get('KOD_SEKOLAH') or row_dict.get('kod_sekolah') or row_dict.get('kod_sekolah_tuan_rumah') or ''
            row_dict['KOD_SEKOLAH_ASAL'] = str(ksa).strip().upper()

            # NAMA
            ng = row_dict.get('NAMA_GURU') or row_dict.get('nama_guru') or row_dict.get('NAMA GURU') or ''
            row_dict['NAMA_GURU'] = str(ng).strip().upper()

            # NAMA SEKOLAH ASAL - V28 FIX
            nsa = row_dict.get('NAMA_SEKOLAH_ASAL') or row_dict.get('nama_sekolah_asal') or row_dict.get('NAMA_SEKOLAH') or row_dict.get('nama_sekolah') or row_dict.get('NAMA SEKOLAH ASAL') or ''
            row_dict['NAMA_SEKOLAH_ASAL'] = str(nsa).strip().upper()
            row_dict['nama_sekolah_asal'] = str(nsa).strip()

            # IC
            ic = row_dict.get('IC_GURU') or row_dict.get('ic_guru') or row_dict.get('IC') or row_dict.get('ic') or ''
            ic = str(ic).strip()
            # Normalize IC - remove spaces
            ic = ic.replace(' ', '')
            row_dict['IC_GURU'] = ic

            # ALAMAT, TELEFON, EMAIL, POSKOD - ensure exists
            for key_lower, key_upper in [('alamat_rumah','ALAMAT_RUMAH'), ('telefon_guru','TELEFON_GURU'), ('email_guru','EMAIL_GURU'), ('poskod_rumah','POSKOD_RUMAH'), ('no_pusat_asal','NO_PUSAT_ASAL'), ('pengalaman_spm','PENGALAMAN_SPM')]:
                val = row_dict.get(key_upper) or row_dict.get(key_lower) or ''
                row_dict[key_upper] = str(val).strip()
                row_dict[key_lower] = str(val).strip()

            # Lajur `status` (top-level) ialah SUMBER SEBENAR - ia dikemas kini oleh Hantar / Jana / Lulus.
            # STATUS dalam JSON `data` hanya nilai semasa insert ("DICADANGKAN") dan tak pernah dikemas kini,
            # jadi ia tak boleh menimpa lajur `status` (punca paparan kekal "belum dihantar").
            _top = r.get('status')
            if _top is not None and not (isinstance(_top, float) and pd.isna(_top)) and str(_top).strip():
                row_dict['STATUS'] = str(_top).strip()
                row_dict['status'] = str(_top).strip()
            elif 'STATUS' not in row_dict or not row_dict['STATUS']:
                row_dict['STATUS'] = row_dict.get('status') or 'DICADANGKAN'

            # No Surat: lajur `no_surat` (top-level) ialah sumber sebenar. Nilai kosong dalam JSON `data`
            # tak boleh menimpanya (punca guru kekal "belum lulus" walaupun surat dah dijana).
            def _ns_ok(v):
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return ""
                t = str(v).strip()
                return "" if t.lower() in ("nan", "none", "null") else t
            _ns_final = _ns_ok(r.get('no_surat')) or _ns_ok(r.get('NO_SURAT')) \
                or _ns_ok(row_dict.get('no_surat')) or _ns_ok(row_dict.get('NO_SURAT')) \
                or _ns_ok(row_dict.get('surat_no')) or _ns_ok(row_dict.get('SURAT_NO')) \
                or _ns_ok(row_dict.get('no_surat_lantikan'))
            row_dict['no_surat'] = _ns_final
            row_dict['NO_SURAT'] = _ns_final

            norm_rows.append(row_dict)

        df_norm = pd.DataFrame(norm_rows)
        if df_norm.empty:
            return df_norm

        # V25 FIX: Deduplicate and keep HANTAR status prioritized over DICADANGKAN
        if 'IC_GURU' in df_norm.columns:
            # Create priority for status: LULUS=3, HANTAR=2, DICADANGKAN=1
            def status_priority(s):
                s = str(s).upper()
                if 'LULUS' in s:
                    return 5
                if any(x in s for x in ('DILANTIK', 'DIJANA', 'DITEMPATKAN', 'SURAT')):
                    return 4
                if 'HANTAR' in s or 'TERPILIH' in s or 'SIMPANAN' in s:
                    return 3
                return 1
            try:
                df_norm['status_prio'] = df_norm['STATUS'].apply(status_priority)
            except:
                try:
                    df_norm['status_prio'] = df_norm['status'].apply(status_priority)
                except:
                    df_norm['status_prio'] = 1

            # Add sort key: id descending, status_prio descending
            sort_cols = ['status_prio']
            if 'id' in df_norm.columns:
                try:
                    df_norm['id_num'] = pd.to_numeric(df_norm['id'], errors='coerce')
                    sort_cols.append('id_num')
                except:
                    pass
            if 'created_at' in df_norm.columns:
                sort_cols.append('created_at')

            df_norm = df_norm.sort_values(by=sort_cols, ascending=False)
            df_norm = df_norm.drop_duplicates(subset=['IC_GURU', 'KOD_SEKOLAH_ASAL'], keep='first')
            # Clean helper columns
            for col in ['id_num', 'status_prio']:
                if col in df_norm.columns:
                    df_norm = df_norm.drop(columns=[col])

        # Filter by PPD if requested - STRICT FILTER (FIX untuk isu Sepang nampak Klang)
        if kod_ppd:
            kod_ppd_u = kod_ppd.strip().upper()
            try:
                # Step 1: Get list of sekolah kod for this PPD from sekolah_master
                kod_list = []
                try:
                    res_sek = supa.table("sekolah_master").select("kod_sekolah").eq("kod_ppd", kod_ppd_u).limit(2000).execute()
                    kod_list = [str(s.get('kod_sekolah','')).upper().strip() for s in (res_sek.data or []) if str(s.get('kod_sekolah','')).strip()]
                except:
                    kod_list = []

                # Step 2: Strict filter - only allow if KOD_PPD exact match OR KOD_SEKOLAH_ASAL in kod_list
                # NOT include empty KOD_PPD unless sekolah is in list
                if kod_list:
                    # Exact match for KOD_PPD (not contains) + sekolah in list
                    mask_ppd_exact = df_norm['KOD_PPD'].astype(str).str.upper().str.strip() == kod_ppd_u
                    mask_sek_in_list = df_norm['KOD_SEKOLAH_ASAL'].astype(str).str.upper().str.strip().isin(kod_list)
                    # Strict: only keep if either PPD matches exactly OR sekolah is in this PPD's list
                    df_norm = df_norm[mask_ppd_exact | mask_sek_in_list].copy()
                else:
                    # Fallback if sekolah_master empty - filter exact PPD only, no empty allowed
                    mask_ppd_exact = df_norm['KOD_PPD'].astype(str).str.upper().str.strip() == kod_ppd_u
                    df_norm = df_norm[mask_ppd_exact].copy()
            except Exception as e:
                # On error, try exact match only
                try:
                    kod_ppd_u = kod_ppd.strip().upper()
                    df_norm = df_norm[df_norm['KOD_PPD'].astype(str).str.upper().str.strip() == kod_ppd_u].copy()
                except:
                    pass

        if kod_sekolah:
            kod_s_u = kod_sekolah.strip().upper()
            try:
                df_norm = df_norm[df_norm['KOD_SEKOLAH_ASAL'].astype(str).str.upper() == kod_s_u]
            except:
                pass

        return df_norm
    except Exception as e:
        return pd.DataFrame()

def flash(level, msg):
    st.session_state.setdefault("_flash", []).append((level, msg))

def show_flash():
    for level, msg in st.session_state.pop("_flash", []):
        getattr(st, level)(msg)

def _id_py(x):
    if hasattr(x, "item"): x = x.item()
    if isinstance(x, float) and x.is_integer(): return int(x)
    return x

def hantar_ke_ppd(ids, kod_ppd, df_sasaran=None):
    """FIX: Hanya update STATUS, jangan sentuh nama_guru"""
    berjaya, gagal = 0, []
    ic_list = []
    if df_sasaran is not None and not df_sasaran.empty:
        try:
            if 'IC_GURU' in df_sasaran.columns:
                ic_list = df_sasaran['IC_GURU'].astype(str).str.strip().tolist()
        except:
            pass
    for i in range(0, len(ids), 100):
        kelompok = ids[i:i+100]
        payloads_to_try = [
            {"status": "HANTAR KE PPD", "status": "HANTAR KE PPD"},
            {"status": "HANTAR KE PPD"},
            {"status": "HANTAR KE PPD"},
        ]
        success = False
        last_err = ""
        for payload in payloads_to_try:
            try:
                supa.table("cadangan_sup").update(payload).in_("id", kelompok).execute()
                success = True
                break
            except Exception as e:
                last_err = str(e)
                continue
        if success:
            berjaya += len(kelompok)
        else:
            gagal.append(last_err)
    if ic_list:
        for ic_val in ic_list:
            if not ic_val or ic_val.lower() in ["nan","none",""]:
                continue
            try:
                supa.table("cadangan_sup").update({"status": "HANTAR KE PPD"}).eq("ic_guru", ic_val).execute()
            except:
                pass
    return berjaya, gagal

def simpan_penempatan_ppd(items):
    """Simpan hasil janaan ke cadangan_sup (lajur kod_pusat + status DIJANA PPD), berkelompok ikut pusat.
    items: [{"id":..., "ic":..., "pusat":...}]. Pulang (bil_berjaya, senarai_gagal)."""
    berjaya, gagal = 0, []
    ikut_pusat = {}
    for it in items:
        ikut_pusat.setdefault(str(it["pusat"]), []).append(it)
    for pusat, senarai in ikut_pusat.items():
        ids = [_id_py(i["id"]) for i in senarai if str(i.get("id") or "").strip() not in ("", "nan", "None")]
        for k in range(0, len(ids), 100):
            kelompok = ids[k:k + 100]
            try:
                supa.table("cadangan_sup").update({"kod_pusat": pusat, "status": "DIJANA PPD"}).in_("id", kelompok).execute()
                berjaya += len(kelompok)
            except Exception as e:
                gagal.append(f"{pusat}: {e}")
        for i in senarai:
            if str(i.get("id") or "").strip() in ("", "nan", "None") and i.get("ic"):
                try:
                    supa.table("cadangan_sup").update({"kod_pusat": pusat, "status": "DIJANA PPD"}).eq("ic_guru", i["ic"]).execute()
                    berjaya += 1
                except Exception as e:
                    gagal.append(f"{i.get('ic')}: {e}")
    return berjaya, gagal


def to_excel(df):
    output = BytesIO()
    try:
        import openpyxl
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()
    except ImportError: pass
    except Exception: pass

    try:
        output.write(df.to_csv(index=False).encode('utf-8-sig'))
        return output.getvalue()
    except:
        return b""


def clean_nan(val):
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("nan","none","null","nat",""):
        return ""
    return s

def get_nama_sekolah_full(kod_sek, fallback=""):
    try:
        ks = str(kod_sek).upper().strip()
        if not ks:
            return fallback
        try:
            res = supa.table("sekolah_master").select("nama_sekolah, kod_sekolah").eq("kod_sekolah", ks).limit(1).execute()
            if res.data:
                nm = res.data[0].get("nama_sekolah") or ""
                if nm and str(nm).lower() not in ("nan","none",""):
                    return str(nm).strip()
        except:
            pass
        if fallback and str(fallback).upper().strip() != ks:
            if str(fallback).lower() not in ("nan","none",""):
                return str(fallback).strip()
        return ks
    except:
        return fallback or str(kod_sek)

def create_simple_pdf_bytes(pages_text_list, title="Surat Lantikan"):
    try:
        import io
        def esc_pdf(s):
            s = str(s)
            s = s.replace('\\','\\\\').replace('(','\\(').replace(')', '\\)')
            return s
        content_streams = []
        for page_lines in pages_text_list:
            stream = "BT\n/F1 10 Tf\n40 800 Td\n"
            for line in page_lines:
                line = str(line)[:120]
                if not line.strip():
                    stream += "0 -14 Td\n"
                    continue
                safe = esc_pdf(line)
                stream += f"({safe}) Tj\n0 -14 Td\n"
            stream += "ET\n"
            content_streams.append(stream)
        pdf_parts = []
        pdf_parts.append(b"%PDF-1.4\n")
        obj_offsets = []
        obj_id = 1
        obj_offsets.append(len(b"".join(pdf_parts)))
        pdf_parts.append(f"{obj_id} 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n".encode())
        obj_id+=1
        obj_offsets.append(len(b"".join(pdf_parts)))
        kids = " ".join([f"{3 + i*2} 0 R" for i in range(len(content_streams))])
        pdf_parts.append(f"{obj_id} 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(content_streams)} >>\nendobj\n".encode())
        obj_id+=1
        for i in range(len(content_streams)):
            obj_offsets.append(len(b"".join(pdf_parts)))
            content_obj_id = obj_id+1
            font_obj_id = 2 + len(content_streams)*2 + 1
            pdf_parts.append(f"{obj_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {content_obj_id} 0 R /Resources << /Font << /F1 {font_obj_id} 0 R >> >> >>\nendobj\n".encode())
            obj_id+=1
            obj_offsets.append(len(b"".join(pdf_parts)))
            stream_bytes = content_streams[i].encode('utf-8', errors='ignore')
            pdf_parts.append(f"{obj_id} 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode())
            pdf_parts.append(stream_bytes)
            pdf_parts.append(b"\nendstream\nendobj\n")
            obj_id+=1
        obj_offsets.append(len(b"".join(pdf_parts)))
        font_obj_id = obj_id
        pdf_parts.append(f"{font_obj_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n".encode())
        xref_offset = len(b"".join(pdf_parts))
        pdf_parts.append(f"xref\n0 {font_obj_id+1}\n".encode())
        pdf_parts.append(b"0000000000 65535 f \n")
        for off in obj_offsets:
            pdf_parts.append(f"{off:010d} 00000 n \n".encode())
        pdf_parts.append(f"trailer\n<< /Size {font_obj_id+1} /Root 1 0 R >>\n".encode())
        pdf_parts.append(f"startxref\n{xref_offset}\n%%EOF".encode())
        return b"".join(pdf_parts)
    except Exception as e:
        return None

def create_zip_of_individual_pdfs(surat_list, kod_ppd, ppd_name):
    import io, zipfile
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, s in enumerate(surat_list, start=1):
                nama = str(s.get('nama','') or s.get('NAMA GURU','')).strip()
                ic = str(s.get('ic','') or s.get('IC','')).strip()
                jawatan = str(s.get('jawatan') or s.get('JAWATAN') or '').strip()
                sek_asal = str(s.get('sekolah_asal') or s.get('SEKOLAH ASAL') or '').strip()
                pusat = str(s.get('pusat') or s.get('PUSAT') or '').strip()
                no_surat = str(s.get('no_surat') or s.get('NO SURAT') or s.get('NO SURAT BARU') or '').strip()
                nama_pusat = str(s.get('nama_pusat') or s.get('NAMA PUSAT') or '').strip()
                nama_sek_asal = str(s.get('nama_sekolah_asal') or s.get('NAMA SEKOLAH ASAL') or '').strip()
                def clean_z(v):
                    v = str(v).strip()
                    return "" if v.lower() in ("nan","none","null","") else v
                nama = clean_z(nama) or f"GURU_{idx}"
                no_surat = clean_z(no_surat) or f"JPN_{idx:04d}"
                try:
                    pdf_bytes = generate_surat_pdf_bytes(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, __import__("datetime").date.today().strftime('%d %B %Y'), no_surat)
                except:
                    pdf_bytes = None
                if pdf_bytes:
                    safe_nama = "".join(c if c.isalnum() or c in ("_","-") else "_" for c in nama)[:30]
                    safe_no = no_surat.replace("/","_").replace("\\","_")
                    file_name = f"{idx:02d}_{safe_nama}_{safe_no}.pdf"
                    zip_file.writestr(file_name, pdf_bytes)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    except Exception as e:
        return None

def generate_surat_html_FIXED(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh):
    nama = clean_nan(nama) or "Nama Guru"
    ic = clean_nan(ic)
    jawatan = clean_nan(jawatan) or "Petugas Peperiksaan"
    sek_asal = clean_nan(sek_asal)
    nama_sek_asal = clean_nan(nama_sek_asal)
    pusat = clean_nan(pusat)
    nama_pusat = clean_nan(nama_pusat)
    if not nama_pusat or nama_pusat.upper() == pusat.upper():
        try:
            _pmap = build_pusat_map_from_master()
            if pusat and str(pusat).upper().strip() in _pmap and _pmap[str(pusat).upper().strip()]:
                nama_pusat = _pmap[str(pusat).upper().strip()]
        except:
            pass
    no_surat = clean_nan(no_surat) or "JPN.SPP.HHJH/0001"
    kod_ppd = clean_nan(kod_ppd) or "BA"
    ppd_name = clean_nan(ppd_name) or kod_ppd
    if nama_sek_asal and nama_sek_asal.upper() != sek_asal.upper():
        display_sek_asal = f"{sek_asal} - {nama_sek_asal}"
    else:
        try:
            full_nama = get_nama_sekolah_full(sek_asal, nama_sek_asal)
            display_sek_asal = f"{sek_asal} - {full_nama}" if full_nama and full_nama.upper() != sek_asal.upper() else sek_asal
        except:
            display_sek_asal = sek_asal
    display_pusat = f"{pusat} - {nama_pusat}" if nama_pusat and nama_pusat.upper() != pusat.upper() else pusat
    html = '<html><head><meta charset="UTF-8"><title>Surat Lantikan SPM 2026</title>'
    html += '<style>body{font-family:Times New Roman,serif;margin:40px;color:#000;}.surat{border:2px solid #000;padding:30px;margin-bottom:30px;page-break-after:always;background:white;}.header{text-align:center;border-bottom:3px double #000;padding-bottom:15px;margin-bottom:20px;}.kandungan{line-height:1.6;}table.info{width:100%;border-collapse:collapse;margin:15px 0;}table.info td{padding:5px 10px;}table.info td:first-child{width:180px;font-weight:bold;}.tandatangan{margin-top:60px;display:flex;justify-content:space-between;}</style></head><body>'
    html += '<div class="surat"><div class="header">'
    html += '<h2>JABATAN PENDIDIKAN NEGERI SELANGOR</h2>'
    html += f'<h3>PEJABAT PENDIDIKAN DAERAH {kod_ppd} - {ppd_name}</h3>'
    html += f'<p>No Surat: {no_surat}</p></div>'
    html += '<div class="kandungan">'
    html += f'<p>Tarikh: {tarikh}</p><p><strong>Tuan/Puan,</strong></p><p><strong>PELANTIKAN SEBAGAI {jawatan.upper()} PEPERIKSAAN SPM TAHUN 2026</strong></p>'
    html += '<p>Dengan hormatnya saya merujuk kepada perkara di atas.</p><p>2. Sukacita dimaklumkan bahawa tuan/puan telah dilantik sebagai petugas peperiksaan SPM 2026 seperti butiran berikut:</p><table class="info">'
    html += f'<tr><td>Nama</td><td>: {nama}</td></tr><tr><td>No. IC</td><td>: {ic}</td></tr><tr><td>Jawatan</td><td>: {jawatan}</td></tr><tr><td>Sekolah Asal</td><td>: {display_sek_asal}</td></tr><tr><td>Pusat Ditugaskan</td><td>: {display_pusat}</td></tr><tr><td>No Surat Lantikan</td><td>: {no_surat}</td></tr></table>'
    html += '<p>3. Tuan/puan dikehendaki hadir bertugas di pusat peperiksaan yang telah ditetapkan mengikut jadual yang akan dimaklumkan kemudian.</p><p>4. Kerjasama dan komitmen tuan/puan dalam menjayakan peperiksaan SPM 2026 amatlah dihargai dan didahului dengan ucapan terima kasih.</p><p>Sekian.</p>'
    html += '<div class="footer"><p><strong>MALAYSIA MADANI</strong><br><strong>BERKHIDMAT UNTUK NEGARA</strong></p><div class="tandatangan"><div><p>Yang benar,</p><br><br><br>'
    html += f'<p>_________________________<br><strong>Pegawai Pendidikan Daerah<br>PPD {kod_ppd} - {ppd_name}</strong></p></div><div style="text-align:right;"><p>b.p Pengarah Pendidikan<br>Jabatan Pendidikan Negeri Selangor</p></div></div></div></div></div></body></html>'
    return html





def generate_surat_pdf_bytes_FIXED(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh, no_rujukan="", bilik_kebal="", kod_bilik_kebal=""):
    try:
        nama = clean_nan(nama) or "Nama Guru"
        ic = clean_nan(ic)
        jawatan = clean_nan(jawatan) or "Pengawas Peperiksaan"
        sek_asal = clean_nan(sek_asal)
        nama_sek_asal = clean_nan(nama_sek_asal) or get_nama_sekolah_full(sek_asal, "")
        pusat = clean_nan(pusat)
        nama_pusat = clean_nan(nama_pusat) or get_nama_sekolah_full(pusat, "")
        no_surat = clean_nan(no_surat) or f"JPNS.SPP 600-7/17/5 Jld.2 (01)"
        kod_ppd = clean_nan(kod_ppd) or "BA"
        ppd_name = clean_nan(ppd_name) or kod_ppd
        tarikh = clean_nan(tarikh) or datetime.date.today().strftime("%d %B %Y")
        bilik_kebal = clean_nan(bilik_kebal) or clean_nan(kod_bilik_kebal) or ""

        if nama_sek_asal and nama_sek_asal.upper() != sek_asal.upper() and sek_asal not in nama_sek_asal:
            display_sek_asal = f"{sek_asal} - {nama_sek_asal}"
        else:
            display_sek_asal = nama_sek_asal if nama_sek_asal else sek_asal
        if nama_pusat and nama_pusat.upper() != pusat.upper() and pusat not in nama_pusat:
            display_pusat = f"{pusat} - {nama_pusat}"
        else:
            display_pusat = nama_pusat if nama_pusat else pusat

        # No pusat untuk display - ambil dari pusat
        no_pusat_display = pusat.split("-")[0].strip() if "-" in pusat else pusat
        if len(no_pusat_display) < 3:
            no_pusat_display = pusat

        # ===== V37: TEMPLAT JPN DIUTAMAKAN - kalau JPN dah cipta templat jawatan ini, PDF dijana dari templat itu =====
        _h37 = render_jpn_template_html(jawatan, nama, ic, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh, bilik_kebal)
        if _h37:
            _pdf37 = html_to_pdf_bytes(_h37)
            if _pdf37:
                return _pdf37
        # (jika templat tiada / enjin PDF tiada -> guna susun atur lama di bawah)
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        import io, os
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=18*mm, topMargin=10*mm, bottomMargin=12*mm)
        styles = getSampleStyleSheet()

        style_header_mid = ParagraphStyle('HeaderMid', parent=styles['Normal'], fontSize=10.5, leading=13, alignment=0, fontName='Helvetica')
        style_header_right = ParagraphStyle('HeaderRight', parent=styles['Normal'], fontSize=8.5, leading=11, alignment=0, fontName='Helvetica')
        style_normal = ParagraphStyle('NormalJPN', parent=styles['Normal'], fontSize=10, leading=13.5, spaceAfter=3, alignment=4, fontName='Helvetica')
        style_normal_left = ParagraphStyle('NormalLeft', parent=styles['Normal'], fontSize=10, leading=13.5, spaceAfter=3, alignment=0, fontName='Helvetica')
        style_bold = ParagraphStyle('BoldJPN', parent=styles['Normal'], fontSize=10, leading=13, spaceAfter=4, alignment=0, fontName='Helvetica-Bold')
        style_tajuk = ParagraphStyle('TajukJPN', parent=styles['Normal'], fontSize=10.5, leading=13.5, spaceAfter=6, alignment=0, fontName='Helvetica-Bold')
        style_small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=9.5, leading=13, alignment=0, fontName='Helvetica')

        story = []

        # ===== HEADER - IKUT GAMBAR =====
        logo_path = find_asset(LOGO_NAMES)
        for cand in ([] if logo_path else ["/mnt/data/jata_cropped.png", "/mnt/data/65b0dade-7a33-4312-b19b-9d5b24dd57ce.jpg", "jata_negara_hd.png","./jata_negara_hd.png","jata_negara.png","./jata_negara.png","/mnt/data/jata_negara_hd.png"]):
            if os.path.exists(cand):
                logo_path = cand
                break
        # FIX v40.1: fallback tulis JATA_B64 ke file temp jika masih tiada
        if not logo_path:
            try:
                j = globals().get("JATA_B64","")
                if j and len(j) > 100:
                    import base64, tempfile, hashlib
                    b = base64.b64decode(j)
                    p = os.path.join(tempfile.gettempdir(), f"jata_fallback_{hashlib.md5(b).hexdigest()[:8]}.jpg")
                    if not os.path.exists(p):
                        with open(p,"wb") as f: f.write(b)
                    logo_path = p
            except Exception as e:
                _log.debug(f"jata fallback fail: {e}")


        middle_html = """<b>KEMENTERIAN PENDIDIKAN</b><br/>Jabatan Pendidikan Negeri Selangor<br/>Jalan Jambu Bol 4/3E, Seksyen 4<br/>40604 Shah Alam, Selangor"""
        right_html = """Tel : 03 - 5518 6500<br/>Faks : 03 - 5510 2133<br/>Laman Web : jpnselangor.moe.gov.my"""

        if logo_path:
            try:
                logo_img = RLImage(logo_path, width=24*mm, height=20*mm, kind='proportional')
                header_data = [[logo_img, Paragraph(middle_html, style_header_mid), Paragraph(right_html, style_header_right)]]
                t = Table(header_data, colWidths=[26*mm, 82*mm, 60*mm])
                t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.8, colors.black), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 2), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
                story.append(t)
            except:
                header_data = [[Paragraph("", style_header_mid), Paragraph(middle_html, style_header_mid), Paragraph(right_html, style_header_right)]]
                t = Table(header_data, colWidths=[26*mm, 82*mm, 60*mm])
                t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.8, colors.black), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
                story.append(t)
        else:
            header_data = [[Paragraph("", style_header_mid), Paragraph(middle_html, style_header_mid), Paragraph(right_html, style_header_right)]]
            t = Table(header_data, colWidths=[26*mm, 82*mm, 60*mm])
            t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.8, colors.black), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
            story.append(t)

        story.append(Spacer(1,6))

        # ===== RUJ KAMI & TARIKH - KANAN, TABLE KEMAS =====
        style_ruj_label = ParagraphStyle('RujLabel', parent=styles['Normal'], fontSize=10, leading=13, alignment=0, fontName='Helvetica')
        style_ruj_value = ParagraphStyle('RujValue', parent=styles['Normal'], fontSize=10, leading=13, alignment=0, fontName='Helvetica')
        style_ruj_colon = ParagraphStyle('RujColon', parent=styles['Normal'], fontSize=10, leading=13, alignment=0, fontName='Helvetica')

        ruj_inner_data = [
            [Paragraph("Ruj. Kami", style_ruj_label), Paragraph(":", style_ruj_colon), Paragraph(no_surat, style_ruj_value)],
            [Paragraph("Tarikh", style_ruj_label), Paragraph(":", style_ruj_colon), Paragraph(tarikh, style_ruj_value)]
        ]
        t_ruj_inner = Table(ruj_inner_data, colWidths=[22*mm, 4*mm, 62*mm])
        t_ruj_inner.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 1), ('RIGHTPADDING', (0,0), (-1,-1), 1), ('TOPPADDING', (0,0), (-1,-1), 1), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
        wrapper_data = [[Paragraph("", style_ruj_label), t_ruj_inner]]
        t_wrapper = Table(wrapper_data, colWidths=[80*mm, 88*mm])
        t_wrapper.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
        story.append(t_wrapper)
        story.append(Spacer(1,6))

        # ===== NAMA & MELALUI =====
        story.append(Paragraph(f"<b>{nama.upper()}</b>", style_bold))
        story.append(Spacer(1,6))
        story.append(Paragraph("Melalui:", style_normal_left))
        story.append(Spacer(1,2))
        story.append(Paragraph("Pengetua/Guru Besar,", style_normal_left))
        # Sekolah asal dari data
        story.append(Paragraph(f"{display_sek_asal.upper()},", style_normal_left))
        # PPD untuk GOMBAK etc - ambil dari ppd_name
        story.append(Paragraph(f"<b>{ppd_name.upper()}.</b>", style_normal_left))
        story.append(Spacer(1,6))
        story.append(Paragraph("Tuan,", style_normal_left))
        story.append(Spacer(1,6))

        # ===== TAJUK - IKUT GAMBAR =====
        tajuk_jawatan = jawatan.upper()
        if "PENYELIA KAWASAN" in tajuk_jawatan:
            tajuk_full = f"SIJIL PELAJARAN MALAYSIA ULANGAN ( SPMU ) TAHUN 2026 :<br/>PELANTIKAN SEBAGAI PENYELIA KAWASAN BERTULIS ( TATAKIRA/PEMEGANG KUNCI )"
        elif "KETUA PENGAWAS" in tajuk_jawatan:
            tajuk_full = f"SIJIL PELAJARAN MALAYSIA ( SPM ) TAHUN 2026 :<br/>PELANTIKAN SEBAGAI {tajuk_jawatan}"
        else:
            tajuk_full = f"SIJIL PELAJARAN MALAYSIA ( SPM ) TAHUN 2026 :<br/>PELANTIKAN SEBAGAI {tajuk_jawatan} - {display_pusat}"

        story.append(Paragraph(f"<b>{tajuk_full}</b>", style_tajuk))
        story.append(Spacer(1,6))
        story.append(Paragraph("Dengan segala hormatnya perkara di atas dirujuk.", style_normal))
        story.append(Spacer(1,6))

        # ===== PARA 2 - IKUT GAMBAR 100% - FIX NO PUSAT & BILIK KEBAL =====
        # LOGIK BARU: No Pusat = No Pusat sebenar (BB017), Bilik Kebal kosong dulu kalau belum set di selenggara
        # Kalau Penyelia Kawasan, bilik_kebal datang dari selenggara bilik kebal -> kod_bilik_kebal
        # No Pusat datang dari kod_pusat (pusat jagaan)

        # Tentukan jenis jawatan
        is_penyelia_kawasan = "PENYELIA KAWASAN" in jawatan.upper()

        if is_penyelia_kawasan:
            para2_text = f"2. &nbsp;&nbsp;&nbsp;&nbsp;Sukacita dimaklumkan bahawa, tuan dilantik sebagai <b>{jawatan}</b> bagi peperiksaan di atas dari tempoh <b>14 Julai hingga 16 Julai 2026</b>. Pelantikan ini merupakan sebahagian daripada tugas rasmi. Maklumat pusat peperiksaan di bawah pengawasan tuan adalah seperti berikut:"
        else:
            para2_text = f"2. &nbsp;&nbsp;&nbsp;&nbsp;Sukacita dimaklumkan tuan dilantik sebagai <b>{jawatan} bagi peperiksaan di atas. Berikut adalah pusat peperiksaan di bawah pengawasan tuan:</b>"

        story.append(Paragraph(para2_text, style_normal))
        story.append(Spacer(1,6))

        # 2.1, 2.2, 2.3 - TABLE KEMAS - FIX: No Pusat betul, Bilik Kebal ikut selenggara
        style_sub_label = ParagraphStyle('SubLabel', parent=styles['Normal'], fontSize=10, leading=13, alignment=0, leftIndent=15*mm, fontName='Helvetica')
        style_sub_value = ParagraphStyle('SubValue', parent=styles['Normal'], fontSize=10, leading=13, alignment=0, fontName='Helvetica-Bold')
        style_sub_value_empty = ParagraphStyle('SubValueEmpty', parent=styles['Normal'], fontSize=10, leading=13, alignment=0, fontName='Helvetica', textColor=colors.HexColor('#1565c0'))

        # LOGIK: No Pusat = kod pusat sebenar, BUKAN bilik kebal
        # Kalau bilik_kebal kosong, paparkan - atau kosong untuk isi kemudian
        if not bilik_kebal or bilik_kebal.strip() == "" or bilik_kebal.lower() in ("nan","none","null","-"):
            bilik_kebal_display = ""  # Kosongkan dulu seperti request
            bilik_kebal_para = Paragraph(f": <i>(Akan dikemaskini melalui Selenggara Bilik Kebal)</i>", style_sub_value_empty)
        else:
            bilik_kebal_display = bilik_kebal.upper()
            bilik_kebal_para = Paragraph(f": {bilik_kebal_display}", style_sub_value)

        # No Pusat - pastikan bukan bilik kebal code (CB, BK)
        # Jika no_pusat_display mengandungi CB/BK dan kita ada pusat sebenar, guna pusat sebenar
        if no_pusat_display.upper().startswith(("CB","BK")) and pusat:
            # no_pusat_display ni sebenarnya bilik kebal, tukar guna pusat sebenar
            no_pusat_final = pusat.split(",")[0].strip() if "," in pusat else pusat
        else:
            no_pusat_final = no_pusat_display

        sub_data = [
            [Paragraph("2.1", style_small), Paragraph("No. Pusat", style_small), Paragraph(f": {no_pusat_final}", style_sub_value)],
            [Paragraph("2.2", style_small), Paragraph("Nama Pusat", style_small), Paragraph(f": {display_pusat.upper()}", style_sub_value)],
            [Paragraph("2.3", style_small), Paragraph("Bilik Kebal", style_small), bilik_kebal_para],
        ]
        t_sub = Table(sub_data, colWidths=[10*mm, 30*mm, 110*mm])
        t_sub.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 2), ('RIGHTPADDING', (0,0), (-1,-1), 2), ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
        story.append(t_sub)
        story.append(Spacer(1,6))

        # ===== PARA 3 - ELAUN =====
        story.append(Paragraph("3. &nbsp;&nbsp;&nbsp;&nbsp;Tuan akan dibayar dengan kadar elaun berikut:", style_normal))
        story.append(Spacer(1,4))

        elaun_data = [
            [Paragraph("3.1", style_small), Paragraph("Elaun Ikhtisas", style_small), Paragraph(f": <b>RM 281.25 + S (S = Bil. Sesi)</b>", style_small)],
            [Paragraph("3.2", style_small), Paragraph("Elaun Perjalanan", style_small), Paragraph(": Tuan layak membuat tuntutan perjalanan<br/>&nbsp;&nbsp;&nbsp;&nbsp;menggunakan kenderaan sendiri/ awam berdasarkan<br/>&nbsp;&nbsp;&nbsp;&nbsp;kepada Arahan Perbendaharaan yang sedang<br/>&nbsp;&nbsp;&nbsp;&nbsp;berkuatkuasa.", style_small)],
        ]
        t_elaun = Table(elaun_data, colWidths=[10*mm, 35*mm, 105*mm])
        t_elaun.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 2), ('RIGHTPADDING', (0,0), (-1,-1), 2), ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
        story.append(t_elaun)
        story.append(Spacer(1,6))

        # ===== PARA 4 =====
        para4 = """4. &nbsp;&nbsp;&nbsp;&nbsp;Pelantikan ini adalah sebahagian daripada tugas rasmi. Sehubungan dengan itu, tuan dikehendaki melaksanakan tugasan seperti yang tersenarai di <b>Lampiran A</b>. Tuan boleh dilantik oleh Ketua Pengawas sebagai <b>Pengawas Pengiring</b> mengikut keperluan ke bilik kebal. Pelantikan tuan adalah <b>Sulit</b> dan tertakluk kepada <b>Akta Rahsia Rasmi 1972</b> dan lain-lain peraturan keselamatan yang sedang berkuatkuasa."""
        story.append(Paragraph(para4, style_normal))
        story.append(Spacer(1,6))

        # ===== PARA 5 =====
        para5 = "5. &nbsp;&nbsp;&nbsp;&nbsp;Semoga tuan dapat melaksanakan tugas ini dengan penuh dedikasi dan berintegriti dalam menyempurnakan amanah yang dipertanggungjawabkan."
        story.append(Paragraph(para5, style_normal))
        story.append(Spacer(1,6))
        # ===== PENUTUP + TANDATANGAN (satu blok, tak terpisah antara muka surat) =====
        sig_path = find_asset(SIGN_NAMES)
        _base = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
        for _name in ([] if sig_path else ["tandatangan_pengarah_hd.png", "tandatangan_pengarah.png", "tandatangan_pengarah.jpg", "tandatangan.png"]):
            for _dir in [_base, ".", "/mnt/data", os.path.join(_base, "assets")]:
                _p = os.path.join(_dir, _name)
                if os.path.exists(_p):
                    sig_path = _p
                    break
            if sig_path:
                break
        # FIX v40.1: kalau masih tiada, cuba aset_file tandatangan sekali lagi (Supabase)
        if not sig_path:
            try:
                pf = aset_file("tandatangan")
                if pf and os.path.exists(pf):
                    sig_path = pf
            except Exception:
                pass

        penutup = [
            Paragraph("Sekian, terima kasih.", style_normal_left),
            Spacer(1, 5),
            Paragraph("\"MALAYSIA MADANI\"", style_bold),
            Paragraph("\"BERKHIDMAT UNTUK NEGARA\"", style_bold),
            Spacer(1, 5),
            Paragraph("Saya yang menjalankan amanah,", style_normal_left),
        ]
        sig_flow = None
        if sig_path:
            try:
                sig_flow = RLImage(sig_path, width=36*mm, height=13*mm, kind='proportional')
                sig_flow.hAlign = 'LEFT'
            except Exception:
                sig_flow = None
        penutup.append(sig_flow if sig_flow is not None else Spacer(1, 26))
        penutup.append(Paragraph("<b>(DATIN WAN NOR ASHIKIN BINTI ABU KASSIM)</b><br/>Pengarah Pendidikan,<br/>Jabatan Pendidikan Negeri Selangor.", style_normal_left))
        story.append(KeepTogether(penutup))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        _log.debug(f"PDF surat error: {e}"); _surat_err("PDF surat (ReportLab)", e)
        return None




def generate_surat_kolektif_pdf_bytes_JPN(surat_list, kod_ppd, ppd_name, title_prefix="SURAT LANTIKAN"):
    if len(surat_list) > MAX_PDF_KOLEKTIF:
        st.warning(f"PDF dihadkan {MAX_PDF_KOLEKTIF} surat (ada {len(surat_list)}).")
        surat_list = surat_list[:MAX_PDF_KOLEKTIF]
    # RINGAN-START
    """Jana PDF kolektif guna template JPN - untuk PPD download pukal"""
    # ===== V37: gabung PDF individu (templat JPN) menjadi satu PDF kolektif =====
    try:
        from pypdf import PdfWriter, PdfReader
        import io as _io
        _w = PdfWriter()
        _n = 0
        for _s in surat_list:
            _pdf = generate_surat_pdf_bytes_FIXED(
                _s.get("nama",""), _s.get("ic",""), _s.get("jawatan",""),
                _s.get("sekolah_asal",""), _s.get("nama_sekolah_asal","") or _s.get("sekolah_asal",""),
                _s.get("pusat",""), _s.get("nama_pusat","") or _s.get("pusat",""),
                _s.get("no_surat",""), kod_ppd, ppd_name,
                datetime.date.today().strftime("%d %B %Y"),
                bilik_kebal=_s.get("bilik_kebal","") or _s.get("kod_bilik_kebal","")
            )
            if _pdf:
                for _pg in PdfReader(_io.BytesIO(_pdf)).pages:
                    _w.add_page(_pg)
                _n += 1
        if _n > 0:
            _out = _io.BytesIO()
            _w.write(_out)
            return _out.getvalue()
    except Exception as _e:
        _log.debug(f"Gabung PDF kolektif gagal, guna kaedah lama: {_e}"); _surat_err("PDF kolektif (pypdf) - guna susun atur ringkas", _e)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        import io
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=10*mm, bottomMargin=10*mm)
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('TitleKolektif', parent=styles['Heading1'], fontSize=12, alignment=1, spaceAfter=6)
        style_normal = ParagraphStyle('NormalKolektif', parent=styles['Normal'], fontSize=9, leading=12, spaceAfter=3)
        story = []
        story.append(Paragraph(f"{title_prefix} - PPD {kod_ppd} {ppd_name} - {len(surat_list)} Surat - JPN SELARAS", style_title))
        story.append(Spacer(1,8))
        for idx, s in enumerate(surat_list, 1):
            try:
                # Guna function JPN baru
                pdf_one = generate_surat_pdf_bytes_FIXED(
                    s.get("nama",""), s.get("ic",""), s.get("jawatan",""),
                    s.get("sekolah_asal",""), s.get("nama_sekolah_asal","") or s.get("sekolah_asal",""),
                    s.get("pusat",""), s.get("nama_pusat","") or s.get("pusat",""),
                    s.get("no_surat",""), kod_ppd, ppd_name,
                    datetime.date.today().strftime("%d %B %Y")
                )
                # Kita tak embed pdf_one, kita buat text representation kolektif - buat isi ringkas
                # Tapi untuk kolektif kita buat paragraph per surat guna template JPN HTML rendering
                jpn_html = render_jpn_template_html(
                    s.get("jawatan",""), s.get("nama",""), s.get("ic",""),
                    s.get("sekolah_asal",""), s.get("nama_sekolah_asal",""),
                    s.get("pusat",""), s.get("nama_pusat",""),
                    s.get("no_surat",""), kod_ppd, ppd_name,
                    datetime.date.today().strftime("%d %B %Y")
                )
                if jpn_html:
                    # bersihkan sikit
                    import re
                    clean = re.sub(r'<style.*?</style>', '', jpn_html, flags=re.DOTALL|re.IGNORECASE)
                    clean = re.sub(r'<head.*?</head>', '', clean, flags=re.DOTALL|re.IGNORECASE)
                    story.append(Paragraph(f"<b>{idx}. {s.get('nama','')} - {s.get('no_surat','')} - {s.get('sekolah_asal','')}</b>", style_normal))
                    story.append(Paragraph(clean[:8000], style_normal))
                else:
                    story.append(Paragraph(f"<b>{idx}. {s.get('nama','')} - {s.get('jawatan','')} - {s.get('pusat','')} - {s.get('no_surat','')}</b><br/>Sekolah Asal: {s.get('sekolah_asal','')} - Pusat: {s.get('pusat','')}", style_normal))
                story.append(Spacer(1,6))
                if idx % 3 == 0:
                    story.append(PageBreak())
            except Exception as e:
                story.append(Paragraph(f"Error surat {idx}: {e}", style_normal))
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        _log.debug(f"Kolektif JPN error: {e}"); _surat_err("PDF kolektif", e)
        return None

def create_zip_pukal_dari_JPN(surat_list, kod_ppd, ppd_name):
    """VERSI RINGAN: Limit 200 file per ZIP untuk 300 user"""
    try:
        import zipfile, io
        if len(surat_list) > MAX_ZIP_FILES:
            st.warning(f"ZIP dihadkan {MAX_ZIP_FILES} file (ada {len(surat_list)}).")
            surat_list = surat_list[:MAX_ZIP_FILES]
        zip_buffer = io.BytesIO()
        _zip_ok = 0
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, s in enumerate(surat_list, 1):
                try:
                    pdf_bytes = generate_surat_pdf_bytes_FIXED(
                        s.get("nama",""), s.get("ic",""), s.get("jawatan",""),
                        s.get("sekolah_asal",""), s.get("nama_sekolah_asal","") or s.get("sekolah_asal",""),
                        s.get("pusat",""), s.get("nama_pusat","") or s.get("pusat",""),
                        s.get("no_surat",""), kod_ppd, ppd_name,
                        datetime.date.today().strftime("%d %B %Y")
                    )
                    if pdf_bytes:
                        safe_nama = "".join(c if c.isalnum() or c in ("_","-") else "_" for c in str(s.get("nama",""))[:25])
                        safe_no = str(s.get("no_surat","")).replace("/","_").replace("\\","_").replace(" ","_")[:30]
                        safe_sek = str(s.get("sekolah_asal","")).replace("/","_")[:10]
                        # Format: 01_NAMA_SEKOLAH_NOSURAT.pdf - senang SUP cari
                        file_name = f"{idx:03d}_{safe_nama}_{safe_sek}_{safe_no}.pdf"
                        zip_file.writestr(file_name, pdf_bytes)
                        _zip_ok += 1
                except Exception as e:
                    _surat_err("ZIP surat individu", e)
                    continue
        if _zip_ok == 0:
            _surat_err("ZIP surat individu", "tiada satu pun PDF berjaya dijana - ZIP tidak dihasilkan")
            return None
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    except Exception as e:
        _log.debug(f"ZIP JPN error: {e}")
        return None

def hantar_surat_ke_sekolah_asal_bulk(surat_list, kod_ppd):
    """NEW: Bila PPD jana surat, auto update status supaya surat sampai ke sekolah asal petugas"""
    try:
        # Kita update cadangan_sup dengan status SURAT_SAMPAI_SEKOLAH_ASAL + tambah log
        berjaya = 0
        for s in surat_list:
            try:
                no_surat = s.get("no_surat","")
                ic = s.get("ic","")
                sek_asal = s.get("sekolah_asal","")
                pusat = s.get("pusat","")
                if not ic:
                    continue
                # Update cadangan_sup
                payload = {
                    "status": "SURAT_SAMPAI_SEKOLAH_ASAL",
                    "no_surat": no_surat,
                    "kod_pusat": pusat,
                    "tarikh_jana_surat": str(datetime.date.today()),
                    "sekolah_asal_hantar": sek_asal
                }
                try:
                    supa.table("cadangan_sup").update(payload).eq("ic_guru", ic).eq("kod_ppd", kod_ppd.lower() if kod_ppd else "bh").execute()
                    berjaya += 1
                except:
                    try:
                        supa.table("cadangan_sup").update(payload).eq("ic_guru", ic).execute()
                        berjaya += 1
                    except:
                        pass
            except:
                continue
        # Cuba simpan ke table log khas jika ada (surat_hantar_sekolah_asal) - optional
        try:
            log_data = []
            for s in surat_list:
                log_data.append({
                    "kod_ppd": kod_ppd,
                    "ic_guru": s.get("ic",""),
                    "nama_guru": s.get("nama",""),
                    "kod_sekolah_asal": s.get("sekolah_asal",""),
                    "kod_pusat": s.get("pusat",""),
                    "no_surat": s.get("no_surat",""),
                    "jawatan": s.get("jawatan",""),
                    "tarikh_hantar": str(datetime.date.today()),
                    "status": "SAMPAI_KE_SEKOLAH_ASAL"
                })
            # batch insert kalau table wujud
            try:
                supa.table("surat_hantar_sekolah_asal").insert(log_data).execute()
            except:
                pass
        except:
            pass
        return berjaya
    except Exception as e:
        _log.debug(f"hantar sekolah asal error: {e}")
        return 0

# Monkey-patch
try:
    generate_surat_html = generate_surat_html_FIXED
    generate_surat_pdf_bytes = generate_surat_pdf_bytes_FIXED
    generate_surat_pdf_bytes_FIXED_OLD = generate_surat_pdf_bytes_FIXED
    # keep original names also
    globals()['generate_surat_html'] = generate_surat_html_FIXED
    globals()['generate_surat_pdf_bytes'] = generate_surat_pdf_bytes_FIXED
    # new bulk funcs
    globals()['generate_surat_kolektif_pdf_bytes_JPN'] = generate_surat_kolektif_pdf_bytes_JPN
    globals()['create_zip_pukal_dari_JPN'] = create_zip_pukal_dari_JPN
    globals()['hantar_surat_ke_sekolah_asal_bulk'] = hantar_surat_ke_sekolah_asal_bulk
except:
    pass



def get_template_guru(kod_sekolah_contoh="BFT0003", nama_sekolah_contoh="SAM NURUL IMAN", kod_ppd_contoh="BH"):
    """Template FINAL ringkas - hanya wajib, pengalaman & jawatan boleh kosong"""
    template = {
        "kod_ppd": [kod_ppd_contoh.lower()],
        "kod_sekolah": [kod_sekolah_contoh.upper()],
        "nama_guru": ["CONTOH: ALI BIN ABU"],
        "ic_guru": ["900101-01-1234"],
        "jantina": ["LELAKI"],
        "poskod_rumah": ["40000"],
        "alamat_rumah": ["NO 1, JALAN CONTOH, KLANG"],
        "telefon_guru": ["012-3456789"],
        "no_pusat_asal": ["BA142"],
        "kod_sekolah_asal": [kod_sekolah_contoh.upper()],
        "nama_sekolah_asal": [nama_sekolah_contoh],
        "kod_ppd_asal": [kod_ppd_contoh],
        "jawatan_cadangan": [""],
        "pengalaman_spm": [""],
        "email_guru": [""],
    }
    return pd.DataFrame(template)

def get_template_guru_friendly():
    template_mudah = {
        "NAMA GURU": ["CONTOH: ALI BIN ABU"],
        "IC GURU": ["900101-01-1234"],
        "JANTINA": ["L/LELAKI/PEREMPUAN"],
        "KOD PPD": ["BH"],
        "KOD SEKOLAH": ["BFT0003"],
        "POSKOD RUMAH": ["40000"],
        "ALAMAT RUMAH": ["NO 1, JALAN CONTOH, KLANG"],
        "TELEFON GURU": ["012-3456789"],
        "NO PUSAT ASAL": ["BA142"],
        "KOD SEKOLAH ASAL": ["BFT0003"],
        "NAMA SEKOLAH ASAL": ["SAM NURUL IMAN"],
        "KOD PPD ASAL": ["BH"],
        "JAWATAN CADANGAN": ["(Kosongkan)"],
        "PENGALAMAN SPM": ["(Kosongkan)"],
    }
    return pd.DataFrame(template_mudah)

def normalize_guru_import(df_upload):
    HEADER_MAP = {
        "NAMA GURU": "nama_guru", "NAMA_GURU": "nama_guru", "nama_guru": "nama_guru", "NAMA": "nama_guru",
        "IC GURU": "ic_guru", "IC_GURU": "ic_guru", "ic_guru": "ic_guru", "IC": "ic_guru",
        "KOD PPD": "kod_ppd", "KOD_PPD": "kod_ppd", "kod_ppd": "kod_ppd",
        "KOD SEKOLAH": "kod_sekolah", "KOD_SEKOLAH": "kod_sekolah", "kod_sekolah": "kod_sekolah",
        "KOD SEKOLAH ASAL": "kod_sekolah_asal", "KOD_SEKOLAH_ASAL": "kod_sekolah_asal", "kod_sekolah_asal": "kod_sekolah_asal",
        "JANTINA": "jantina", "jantina": "jantina",
        "POSKOD RUMAH": "poskod_rumah", "POSKOD_RUMAH": "poskod_rumah", "poskod_rumah": "poskod_rumah",
        "ALAMAT RUMAH": "alamat_rumah", "ALAMAT_RUMAH": "alamat_rumah", "alamat_rumah": "alamat_rumah",
        "TELEFON GURU": "telefon_guru", "TELEFON_GURU": "telefon_guru", "telefon_guru": "telefon_guru",
        "EMAIL GURU": "email_guru", "EMAIL_GURU": "email_guru", "email_guru": "email_guru",
        "JAWATAN CADANGAN": "jawatan_cadangan", "JAWATAN_CADANGAN": "jawatan_cadangan", "jawatan_cadangan": "jawatan_cadangan",
        "PENGALAMAN SPM": "pengalaman_spm", "PENGALAMAN_SPM": "pengalaman_spm", "pengalaman_spm": "pengalaman_spm",
        "NO PUSAT ASAL": "no_pusat_asal", "NO_PUSAT_ASAL": "no_pusat_asal", "no_pusat_asal": "no_pusat_asal",
        "NAMA SEKOLAH ASAL": "nama_sekolah_asal", "NAMA_SEKOLAH_ASAL": "nama_sekolah_asal", "nama_sekolah_asal": "nama_sekolah_asal",
        "KOD PPD ASAL": "kod_ppd_asal", "KOD_PPD_ASAL": "kod_ppd_asal", "kod_ppd_asal": "kod_ppd_asal",
    }
    normalized_cols = {}
    for col in df_upload.columns:
        col_str = str(col).strip()
        if col_str in HEADER_MAP:
            normalized_cols[col] = HEADER_MAP[col_str]
        elif col_str.upper() in HEADER_MAP:
            normalized_cols[col] = HEADER_MAP[col_str.upper()]
        elif col_str.lower() in HEADER_MAP:
            normalized_cols[col] = HEADER_MAP[col_str.lower()]
        else:
            for k,v in HEADER_MAP.items():
                if k.lower() == col_str.lower():
                    normalized_cols[col] = v
                    break
            else:
                normalized_cols[col] = None
    return normalized_cols

# ================= REFRESH COMPONENT =================
def add_refresh_button():
    """v39: butang refresh kini berada dalam header (ui_theme.shell_header). Dikekalkan untuk keserasian."""
    if st.button("REFRESH - Baca Data Baru", use_container_width=True, type="primary", key=f"refresh_legacy_{st.session_state.get('role')}"):
        st.cache_data.clear()
        st.rerun()

# ================= SESSION INIT =================
# ================= LOGIN PAGE =================


# ===== FIX: BUILD PUSAT MAP ROBUST - IKUT NO PUSAT COLUMN REFER PUSAT_MASTER =====
def build_pusat_map_from_master():
    """Map NO_PUSAT/KOD_PUSAT -> NAMA_PUSAT dari pusat_master"""
    pmap = {}
    try:
        df_p = get_pusat_df()
        for _, pr in df_p.iterrows():
            d = pr.get("data") if isinstance(pr.get("data"), dict) else {}
            if isinstance(d, str):
                try:
                    import json as _js
                    d = _js.loads(d)
                except:
                    d = {}
            # Ambil semua kemungkinan key untuk NO PUSAT
            no_p = str(pr.get("no_pusat") or pr.get("kod_pusat") or pr.get("NO_PUSAT") or pr.get("KOD_PUSAT") or d.get("NO_PUSAT") or d.get("NO PUSAT") or d.get("KOD_PUSAT") or d.get("KOD PUSAT") or "").upper().strip()
            nama_p = str(pr.get("nama_pusat") or pr.get("NAMA_PUSAT") or d.get("NAMA_PUSAT") or d.get("NAMA PUSAT") or "").strip()
            if no_p:
                pmap[no_p] = nama_p
                # juga map tanpa prefix? simpan kedua-dua
                # contoh BA140 tetap BA140
        # Fallback: cuba direct dari supabase pusat_master jika get_pusat_df kosong
        if not pmap:
            try:
                _supa = supa
                res = _supa.table("pusat_master").select("*").limit(1000).execute()
                for r in (res.data or []):
                    no_p = str(r.get("no_pusat") or r.get("kod_pusat") or r.get("NO_PUSAT") or "").upper().strip()
                    nama_p = str(r.get("nama_pusat") or r.get("NAMA_PUSAT") or "").strip()
                    if no_p:
                        pmap[no_p] = nama_p
            except:
                pass
    except Exception as _e:
        pass
    return pmap


# ================= LOGIN POPUP BARU - IKUT HTML (SUP/PPD/JPN POPUP) =================
FLY_SUP = {
    'dashboard': [('utama', '🏠 Utama'), ('pusat', '📍 Senarai Pusat'), ('guru', '👥 Guru Terkini')],
    'senarai':   [('filter', '🔍 Senarai & Filter'), ('edit', '✏️ Edit Data Guru')],
    'cadangan':  [('pilih', '👥 Pilih & Cadang'), ('senarai', '📋 Senarai Cadangan')],
    'surat':     [('jadual', '📑 Jadual Jawatan'), ('individu', '📄 Surat Individu')],
}
FLY_PPD = {
    'dashboard':  [('ringkasan', '📊 Ringkasan'), ('status', '📍 Status Pusat'), ('berwarna', '🎨 Paparan Warna'), ('sekolah', '🏫 Sekolah & Export')],
    'pusat':      [('senarai', '📋 Senarai Pusat'), ('poskod', '📮 Poskod Pusat')],
    'zon':        [('tetap', '⚙️ Tetapan Zon'), ('tempat', '🚀 Jana Penempatan Zon'), ('semak', '📋 Semakan Zon')],
    'cadangan':   [('sekolah', '🏫 Ikut Sekolah'), ('nama', '📝 Senarai Nama Cadangan'), ('simpanan', '📦 Senarai Simpanan')],
    'jana':       [('auto', '🌍 Jana Auto Poskod'), ('jawatan', '👑 Ikut Jawatan')],
    'hasil':      [('ringkasan', '📋 Ringkasan Pusat'), ('sekolah', '🏫 Ikut Sekolah Asal'), ('guru', '👥 Semua Guru')],
    'semakan':    [('semak', '🔍 Semakan Lantikan'), ('kosong', '➕ Isi Kekosongan')],
    'kelulusan':  [('keseluruhan', '✅ Lulus Keseluruhan'), ('pusat', '🏫 Lulus Ikut Pusat')],
    'selenggara': [('form', '➕ Tambah Bilik Kebal'), ('senarai', '📋 Senarai Bilik Kebal'), ('import', '📤 Import Excel'), ('penyelia', '🔐 Tempatkan Penyelia'), ('surat', '📄 Jana Surat Penyelia')],
    'jana_surat': [('keseluruhan', '📄 Semua Surat'), ('pusat', '🏫 Ikut Pusat'), ('sekolah', '🏫 Ikut Sekolah Asal')],
}
FLY_JPN = {
    'dashboard': [('ringkasan', '📊 Ringkasan'), ('ppd', '🏢 Breakdown PPD')],
    'sekolah':   [('senarai', '🏫 Senarai Sekolah'), ('import', '📤 Import Sekolah'), ('auto', '⚡ Auto Generate')],
    'pusat':     [('senarai', '📋 Senarai Pusat'), ('fix', '🔧 Fix Jumlah Calon'), ('tambah', '➕ Tambah Pusat'), ('import', '📤 Import Pusat'), ('kosong', '🗑️ Kosongkan Pusat')],
    'guru':      [('import', '📤 Import Master 60K'), ('data', '📊 Data Sedia Ada')],
    'admin':     [('status', '🩺 Status Sistem'), ('table', '🛠️ Buat Table')],
}

import os as _os
_ASSET_DIR = _os.path.dirname(_os.path.abspath(__file__))
LOGO_NAMES = ["jata_cropped.png", "jata_negara_hd.png", "jata_negara.png"]
SIGN_NAMES = ["tandatangan_pengarah_hd.png", "tandatangan_pengarah.png", "tandatangan_pengarah.jpg", "tandatangan.png"]

def find_asset(names):
    """Cari imej: (1) yang dimuat naik ke Supabase, (2) fail di folder projek, ./, /mnt/data dan assets/."""
    kind = "logo" if names is LOGO_NAMES else ("tandatangan" if names is SIGN_NAMES else None)
    if kind:
        _p = aset_file(kind)
        if _p:
            return _p
    for n in names:
        for d in (_ASSET_DIR, ".", "/mnt/data", _os.path.join(_ASSET_DIR, "assets"), "assets"):
            p = _os.path.join(d, n)
            if _os.path.exists(p):
                return p
    return None

def surat_aset_amaran():
    """Papar amaran jika logo / tandatangan surat tiada dalam repo (surat akan keluar tanpa logo/sign)."""
    miss = []
    if not find_asset(LOGO_NAMES):
        miss.append("logo Jata Negara (jata_negara_hd.png)")
    if not find_asset(SIGN_NAMES):
        miss.append("tandatangan Pengarah (tandatangan_pengarah_hd.png)")
    if miss:
        st.warning("⚠️ Fail imej surat tidak dijumpai dalam repo: " + " dan ".join(miss) +
                   ". Letakkan fail ini di folder yang sama dengan spm_core.py (atau dalam folder assets/), kemudian deploy semula. "
                   "Tanpa fail ini, surat PDF keluar tanpa logo dan tandatangan.")


# ======================================================================= v40: ASET SURAT & DIAGNOSTIK
ASET_KEYS = {"logo": "__ASET_LOGO__", "tandatangan": "__ASET_TANDATANGAN__"}


def _surat_err(ctx, e):
    """Simpan ralat terakhir penjanaan surat (dipaparkan dalam panel Semakan Sistem Surat)."""
    try:
        st.session_state["_surat_err"] = f"{ctx}: {type(e).__name__}: {str(e)[:300]}" if isinstance(e, Exception) else f"{ctx}: {e}"
    except Exception:
        pass


@st.cache_data(ttl=300, show_spinner=False)
def aset_data_uri(kind):
    """Imej logo/tandatangan yang dimuat naik JPN (disimpan dalam surat_templates_jpn). Pulang data URI atau ''."""
    try:
        res = get_supabase().table("surat_templates_jpn").select("template_html").eq("jawatan", ASET_KEYS[kind]).limit(1).execute()
        v = ((res.data or [{}])[0].get("template_html")) or ""
        return v if str(v).startswith("data:image") else ""
    except Exception:
        return ""


def aset_bytes(kind):
    import base64
    uri = aset_data_uri(kind)
    if not uri:
        return None
    try:
        return base64.b64decode(uri.split(",", 1)[1])
    except Exception:
        return None


def aset_file(kind):
    """Tulis imej dari Supabase ke fail sementara supaya boleh dibaca oleh ReportLab / xhtml2pdf."""
    import hashlib, tempfile
    b = aset_bytes(kind)
    if not b:
        return None
    p = _os.path.join(tempfile.gettempdir(), f"spm_aset_{kind}_{hashlib.md5(b).hexdigest()[:10]}.png")
    if not _os.path.exists(p):
        with open(p, "wb") as f:
            f.write(b)
    return p


def aset_save(kind, raw_bytes):
    """Kecilkan (maks 900px) dan simpan sebagai PNG dalam surat_templates_jpn. Pulang (ok, mesej)."""
    import base64, io
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
        im.thumbnail((900, 900))
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        data = buf.getvalue()
        if len(data) > 600_000:
            im.thumbnail((500, 500))
            buf = io.BytesIO()
            im.save(buf, format="PNG", optimize=True)
            data = buf.getvalue()
        uri = "data:image/png;base64," + base64.b64encode(data).decode()
    except Exception as e:
        return False, f"Fail imej tidak sah: {e}"
    try:
        get_supabase().table("surat_templates_jpn").delete().eq("jawatan", ASET_KEYS[kind]).execute()
        get_supabase().table("surat_templates_jpn").insert({"jawatan": ASET_KEYS[kind], "template_html": uri}).execute()
        aset_data_uri.clear()
        return True, ""
    except Exception as e:
        return False, f"Gagal simpan ke Supabase: {str(e)[:200]}"


def aset_delete(kind):
    try:
        get_supabase().table("surat_templates_jpn").delete().eq("jawatan", ASET_KEYS[kind]).execute()
        aset_data_uri.clear()
        return True
    except Exception:
        return False


def _img_uri(kind):
    """Data URI logo/tandatangan: Supabase dahulu, kemudian fail repo, kemudian JATA_B64/TANDA_B64 fallback."""
    import base64, mimetypes, os as _os2
    uri = aset_data_uri(kind)
    if uri and uri.startswith("data:"):
        return uri
    try:
        p = find_asset(LOGO_NAMES if kind == "logo" else SIGN_NAMES)
        if p and _os2.path.exists(p):
            with open(p, "rb") as f:
                data = f.read()
                if data:
                    return f"data:{mimetypes.guess_type(p)[0] or 'image/png'};base64," + base64.b64encode(data).decode()
    except Exception:
        pass
    if kind == "logo":
        try:
            j = globals().get("JATA_B64","")
            if j and len(j) > 100:
                j = j.strip()
                mime = "image/png"
                return f"data:{mime};base64,{j}"
        except Exception:
            pass
    if kind == "tandatangan":
        try:
            j = globals().get("TANDA_B64","")
            if j and len(j) > 100:
                j = j.strip()
                return f"data:image/png;base64,{j}"
        except Exception:
            pass
    return ""

    return ""


def _perbaiki_img_src(html):
    """Pastikan <img src="..."> dalam templat JPN boleh dibaca: fail relatif tiada -> guna imej Supabase/repo/data URI. FIXED v40.1"""
    import re as _re2, base64, mimetypes, os as _os2, tempfile, hashlib

    def fix(m):
        q, src = m.group(1), m.group(2)
        s_low = src.lower()
        if s_low.startswith(("data:", "http://", "https://")):
            return m.group(0)
        if not src or src.strip() == "":
            # src kosong dari {{LOGO}} yang gagal -> inject logo
            uri = _img_uri("logo")
            return f"src={q}{uri}{q}" if uri else m.group(0)
        base = _os2.path.basename(src)
        low = base.lower()
        # detect kind lebih awal
        kind = None
        if any(x in low for x in ("jata", "logo", "lambang")):
            kind = "logo"
        elif any(x in low for x in ("tanda", "sign", "ttd")):
            kind = "tandatangan"

        # 1. cuba aset_file dari Supabase dahulu (paling utama)
        if kind:
            try:
                pf = aset_file(kind)
                if pf and _os2.path.exists(pf):
                    with open(pf, "rb") as f:
                        return f"src={q}data:{mimetypes.guess_type(pf)[0] or 'image/png'};base64,{base64.b64encode(f.read()).decode()}{q}"
            except Exception:
                pass
            # fallback _img_uri yang dah include JATA_B64
            uri = _img_uri(kind)
            if uri:
                return f"src={q}{uri}{q}"

        # 2. cuba cari fail fizikal ikut nama
        p = src if _os2.path.exists(src) else find_asset([base])
        if p and _os2.path.exists(p):
            try:
                with open(p, "rb") as f:
                    return f"src={q}data:{mimetypes.guess_type(p)[0] or 'image/png'};base64,{base64.b64encode(f.read()).decode()}{q}"
            except Exception:
                pass
        
        # 3. kalau masih gagal tapi nampak macam logo, paksa guna JATA_B64
        if kind == "logo" or "jata" in low:
            uri = _img_uri("logo")
            if uri:
                return f"src={q}{uri}{q}"
        return m.group(0)
    
    # fix img src biasa
    html = _re2.sub(r'src\s*=\s*(["\'])([^"\']+)\1', fix, html, flags=_re2.I)
    
    # FIX TAMBAHAN: kalau template guna {{LOGO}} atau {{TANDATANGAN}} yang jadi src="" atau hilang, pastikan ada img tag
    # Ini handle kes _img_uri return "" sebelum ni
    return html


def render_footer():
    st.markdown("<div class='app-footer'>Sistem Pelantikan Petugas SPM Selangor 2026 · Jabatan Pendidikan Negeri Selangor</div>", unsafe_allow_html=True)

def apply_global_ui():
    """Panggil SETIAP rerun (CSS mesti dipaparkan semula)."""
    try:
        hide_fork_github()
    except Exception:
        pass
    apply_pretty_theme()
    _apply_jpn_kad_css()
    for _h in _CSS_QUEUE:
        st.markdown(_h, unsafe_allow_html=True)
