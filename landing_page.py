# -*- coding: utf-8 -*-
"""landing_page.py - Halaman sambutan sebelum pilih portal JPN/PPD + selenggara oleh JPN.

Simpan: jadual Supabase `landing_config` (1 baris id=1, lajur config jsonb).
Gambar pegawai disaiz semula (PIL) dan disimpan sebagai base64 dalam JSON.
"""
import base64, copy, html as _html, io, json
import streamlit as st
import streamlit.components.v1 as components
import spm_core as core

N_PEGAWAI = 12
SQL_LANDING = """create table if not exists landing_config (
  id int primary key,
  config jsonb,
  updated_at timestamptz default now()
);
alter table landing_config disable row level security;"""

DEFAULT = {
    "tajuk": "Selamat Datang ke Sistem Pelantikan Petugas Negeri Selangor",
    "subtajuk": "Jabatan Pendidikan Negeri Selangor • Peperiksaan SPM 2026",
    "butang": "Klik Masuk ke Sistem →",
    "info": [
        {"ikon": "📢", "tajuk": "Pengumuman", "teks": "Semua PPD dan sekolah dimohon melengkapkan cadangan petugas mengikut tarikh yang ditetapkan."},
        {"ikon": "📅", "tajuk": "Tarikh Penting", "teks": "Kemas kini tarikh tutup cadangan SUP, kelulusan PPD dan pengeluaran surat lantikan di sini."},
        {"ikon": "📞", "tajuk": "Bantuan", "teks": "Sebarang masalah sila hubungi Sektor Pengurusan Akademik JPN Selangor."},
        {"ikon": "📘", "tajuk": "Panduan", "teks": "Rujuk manual pengguna untuk panduan SUP, PPD dan JPN."},
    ],
    "pegawai": [{"nama": "", "jawatan": "", "gambar": ""} for _ in range(N_PEGAWAI)],
}
DEFAULT["pegawai"][0] = {"nama": "DATIN WAN NOR ASHIKIN BINTI ABU KASSIM",
                         "jawatan": "Pengarah Pendidikan JPN Selangor", "gambar": ""}


def _esc(x):
    return _html.escape(str(x if x is not None else ""))


def _normalize(cfg):
    out = copy.deepcopy(DEFAULT)
    if isinstance(cfg, str):
        try: cfg = json.loads(cfg)
        except Exception: cfg = {}
    if not isinstance(cfg, dict):
        return out
    for k in ("tajuk", "subtajuk", "butang"):
        if str(cfg.get(k) or "").strip():
            out[k] = str(cfg[k])
    if isinstance(cfg.get("info"), list):
        info = []
        for b in cfg["info"][:8]:
            if isinstance(b, dict):
                info.append({"ikon": str(b.get("ikon") or ""), "tajuk": str(b.get("tajuk") or ""), "teks": str(b.get("teks") or "")})
        out["info"] = info
    if isinstance(cfg.get("pegawai"), list):
        peg = []
        for p in cfg["pegawai"][:N_PEGAWAI]:
            p = p if isinstance(p, dict) else {}
            peg.append({"nama": str(p.get("nama") or ""), "jawatan": str(p.get("jawatan") or ""), "gambar": str(p.get("gambar") or "")})
        while len(peg) < N_PEGAWAI:
            peg.append({"nama": "", "jawatan": "", "gambar": ""})
        out["pegawai"] = peg
    return out


@st.cache_data(ttl=300, show_spinner=False)
def load_config():
    """(config, ralat). Jika jadual belum ada -> lalai + mesej ralat."""
    try:
        res = core._RAW.table("landing_config").select("config").eq("id", 1).limit(1).execute()
        rows = res.data or []
        if rows:
            return _normalize(rows[0].get("config")), ""
        return _normalize(None), ""
    except Exception as e:
        return _normalize(None), str(e)


def save_config(cfg):
    """Simpan, kemudian baca semula terus dari DB (tanpa cache) untuk sahkan benar-benar tersimpan."""
    payload = {"id": 1, "config": cfg}
    core._RAW.table("landing_config").upsert(payload).execute()
    load_config.clear()
    res = core._RAW.table("landing_config").select("config").eq("id", 1).limit(1).execute()
    rows = res.data or []
    if not rows:
        raise RuntimeError("Simpan tidak berjaya: baris tidak ditemui selepas simpan (semak RLS / jadual landing_config).")
    cfg2 = _normalize(rows[0].get("config"))
    n_asal = sum(1 for p in cfg.get("pegawai", []) if p.get("gambar"))
    n_db = sum(1 for p in cfg2["pegawai"] if p.get("gambar"))
    if n_db < n_asal:
        raise RuntimeError(f"Hanya {n_db} daripada {n_asal} gambar tersimpan dalam pangkalan data.")


def proses_gambar(data: bytes, lebar=360, tinggi=450):
    """Potong ke nisbah 4:5 (tengah) & kecilkan -> data URI JPEG."""
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    nisbah = lebar / tinggi
    w, h = im.size
    if w / h > nisbah:
        nw = int(h * nisbah); x0 = (w - nw) // 2
        im = im.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(w / nisbah); y0 = max(0, int((h - nh) * 0.15))  # condong ke atas (muka)
        im = im.crop((0, y0, w, y0 + nh))
    im = im.resize((lebar, tinggi))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


# ------------------------------------------------------------------ hero (korporat)
def _logo_html(h=44):
    """Jata Negara (daripada spm_core.JATA_B64); jika tiada, kotak 'JPN' lama."""
    b64 = getattr(core, "JATA_B64", "") or ""
    if b64:
        return (f'<img src="data:image/png;base64,{b64}" style="height:{h}px;width:auto;margin-right:12px;'
                f'background:#fff;border-radius:8px;padding:3px">')
    return '<span class="logo">JPN</span>'


def hero_html(cfg, solid=False):
    """Seluruh bahagian hero (bar atas, tajuk, carousel pegawai) dalam satu iframe berlatar navy."""
    items = [p for p in cfg["pegawai"] if (p.get("nama") or p.get("jawatan") or p.get("gambar"))]
    cards = []
    for p in items:
        if p.get("gambar"):
            img = f'<img src="{_esc(p["gambar"])}" alt="">'
        else:
            ini = "".join(w[0] for w in (p.get("nama") or "?").split()[:2]).upper()
            img = f'<div class="ph">{_esc(ini)}</div>'
        cards.append(f'<div class="card">{img}<div class="cap"><div class="nm">{_esc(p.get("nama"))}</div>'
                     f'<div class="jw">{_esc(p.get("jawatan"))}</div></div></div>')
    logo = _logo_html(46)
    ring = (f'<div id="stage"><div id="ring">{"".join(cards)}</div></div>' if cards else "")
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--navy:#06193a;--navy2:#0b2d63;--gold:#c9a227;--gold2:#e9d28a}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:transparent;font-family:Inter,Arial,sans-serif;color:#fff;overflow:hidden}}
.wrap{{position:relative;min-height:100vh;overflow:hidden;background:transparent}}
.wrap.solid{{border-radius:18px;border:1px solid rgba(201,162,39,.45);
 background:radial-gradient(1200px 500px at 50% -10%,#1b4a9a 0%,rgba(27,74,154,0) 60%),linear-gradient(160deg,var(--navy2) 0%,var(--navy) 70%)}}
.wrap:before{{content:"";position:absolute;inset:0;opacity:.07;
 background-image:repeating-linear-gradient(45deg,#fff 0 1px,transparent 1px 22px);pointer-events:none}}
.top{{position:relative;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;padding:14px 22px;
 border-bottom:1px solid rgba(201,162,39,.35);background:rgba(3,12,30,.35)}}
.org{{display:flex;align-items:center}}
.org .n{{font-weight:700;font-size:13px;letter-spacing:.08em}}
.org .s{{font-size:10px;letter-spacing:.14em;color:var(--gold2);margin-top:2px}}
.top .r{{font-size:11px;letter-spacing:.1em;color:var(--gold2);text-transform:uppercase}}
.hd{{position:relative;text-align:center;padding:26px 16px 0}}
.chip{{display:inline-block;font-size:10.5px;font-weight:600;letter-spacing:.28em;color:var(--gold2);text-transform:uppercase;
 padding:6px 16px;border:1px solid rgba(201,162,39,.6);border-radius:999px}}
h1{{font-family:'Playfair Display',Georgia,serif;font-weight:700;font-size:clamp(24px,4.6vw,42px);line-height:1.18;margin:16px auto 0;max-width:880px;
 background:linear-gradient(180deg,#fff 30%,var(--gold2));-webkit-background-clip:text;background-clip:text;color:transparent}}
.rule{{width:90px;height:2px;margin:16px auto 10px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}}
.sub{{font-size:13px;letter-spacing:.06em;color:#c9d6ee}}
#stage{{position:relative;height:380px;perspective:1200px;display:flex;align-items:center;justify-content:center;margin-top:6px}}
#ring{{position:relative;width:180px;height:312px;transform-style:preserve-3d;animation:spin 48s linear infinite}}
#stage:hover #ring{{animation-play-state:paused}}
@keyframes spin{{from{{transform:rotateY(0)}}to{{transform:rotateY(-360deg)}}}}
.card{{position:absolute;left:0;top:0;width:180px;height:312px;border-radius:12px;overflow:hidden;text-align:center;
 background:linear-gradient(180deg,#0f2a57,#071a3a);border:1px solid var(--gold);
 box-shadow:0 10px 28px rgba(0,0,0,.45),0 0 0 3px rgba(201,162,39,.12);backface-visibility:hidden}}
.card img,.ph{{width:100%;height:224px;object-fit:cover;display:block;border-bottom:2px solid var(--gold)}}
.ph{{background:linear-gradient(135deg,#123a7a,#0a2250);color:var(--gold2);font:700 46px 'Playfair Display',serif;display:flex;align-items:center;justify-content:center}}
.cap{{padding:7px 8px}}
.nm{{font-size:10.5px;font-weight:700;color:#fff;line-height:1.25;letter-spacing:.02em}}
.jw{{font-size:9.5px;color:var(--gold2);margin-top:3px;line-height:1.25;letter-spacing:.03em}}
.foot{{height:16px}}
</style></head><body><div class="wrap{' solid' if solid else ''}">
<div class="top"><div class="org">{logo}<div><div class="n">JABATAN PENDIDIKAN NEGERI SELANGOR</div>
<div class="s">KEMENTERIAN PENDIDIKAN MALAYSIA</div></div></div><div class="r">Peperiksaan SPM 2026</div></div>
<div class="hd"><span class="chip">Portal Rasmi</span><h1>{_esc(cfg['tajuk'])}</h1><div class="rule"></div>
<div class="sub">{_esc(cfg['subtajuk'])}</div></div>
{ring}<div class="foot"></div></div>
<script>
var cs=document.querySelectorAll('.card'),n=cs.length,w=180;
if(n){{var R=n>2?Math.round((w/2+10)/Math.tan(Math.PI/n)):0;
cs.forEach(function(c,i){{c.style.transform=n>1?'rotateY('+(i*360/n)+'deg) translateZ('+R+'px)':'none';}});
if(n===1){{document.getElementById('ring').style.animation='none';}}
function fit(){{var s=Math.min(1,(window.innerWidth-16)/(2*R+w+30));if(!isFinite(s)||s<=0)s=1;
 document.getElementById('stage').style.transform='scale('+s+')';}}
fit();window.addEventListener('resize',fit);}}
</script></body></html>"""


def render_hero(cfg, solid=False):
    components.html(hero_html(cfg, solid), height=720 if any(
        (p.get("nama") or p.get("jawatan") or p.get("gambar")) for p in cfg["pegawai"]) else 340)


LANDING_CSS = """<style>
.lp-info{background:#fff;border:1px solid #dfe5f1;border-top:3px solid #c9a227;border-radius:10px;padding:16px 16px 14px;
 min-height:132px;box-shadow:0 4px 14px rgba(6,25,58,.07);margin-bottom:12px}
.lp-info .t{font-weight:700;color:#06193a;font-size:14px;letter-spacing:.02em}
.lp-info .x{color:#4a5873;font-size:12.5px;margin-top:7px;line-height:1.5}
.st-key-land_cta button{background:linear-gradient(180deg,#e0bd4a,#b8901c)!important;color:#06193a!important;border:1px solid #8a6b10!important;
 font-weight:800!important;letter-spacing:.06em;padding:.85rem 1rem!important;border-radius:10px!important;box-shadow:0 6px 18px rgba(184,144,28,.35)}
.st-key-land_cta button:hover{filter:brightness(1.06);transform:translateY(-1px)}
</style>"""

LANDING_FULL_CSS = """<style>
[data-testid="stAppViewContainer"],.stApp{background:radial-gradient(1400px 600px at 50% -5%,#1b4a9a 0%,rgba(27,74,154,0) 60%),
 linear-gradient(160deg,#0b2d63 0%,#06193a 65%,#041229 100%) fixed!important;color:#c9d6ee}
header[data-testid="stHeader"],[data-testid="stToolbar"]{background:transparent!important}
[data-testid="stMainBlockContainer"],.block-container{max-width:100%!important;padding:0 0 1.5rem 0!important}
[data-testid="stAppViewContainer"] iframe{display:block;border:0}
.st-key-land_body{padding:0 clamp(16px,6vw,110px);max-width:1400px;margin:0 auto}
.st-key-land_body .lp-info{background:rgba(255,255,255,.06);border:1px solid rgba(201,162,39,.35);border-top:3px solid #c9a227;
 box-shadow:0 8px 24px rgba(0,0,0,.25);backdrop-filter:blur(2px)}
.st-key-land_body .lp-info .t{color:#fff}
.st-key-land_body .lp-info .x{color:#c9d6ee}
.stApp p,.stApp span,.stApp label{color:#c9d6ee}
.st-key-land_cta button p,.st-key-land_cta button span{color:#06193a!important}
</style>"""


def info_cards(cfg):
    if not cfg["info"]:
        return
    cols = st.columns(min(4, len(cfg["info"])), gap="small")
    for i, b in enumerate(cfg["info"]):
        with cols[i % len(cols)]:
            st.markdown(f'<div class="lp-info"><div class="t">{_esc(b["ikon"])} {_esc(b["tajuk"])}</div>'
                        f'<div class="x">{_esc(b["teks"])}</div></div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ halaman awam
def render_landing():
    cfg, err = load_config()
    st.markdown(LANDING_CSS + LANDING_FULL_CSS, unsafe_allow_html=True)
    render_hero(cfg)
    with st.container(key="land_body"):
        info_cards(cfg)
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            with st.container(key="land_cta"):
                if st.button(cfg["butang"], key="btn_masuk_sistem", use_container_width=True):
                    st.session_state["masuk_sistem"] = True
                    st.rerun()


# ------------------------------------------------------------------ admin JPN
def render_admin_landing():
    st.header("🏠 Selenggara Landing Page")
    st.caption("Halaman sambutan yang dipaparkan sebelum pilihan JPN / PPD.")
    cfg, err = load_config()
    if err:
        st.error("Jadual `landing_config` belum sedia / tidak boleh dibaca. Jalankan SQL ini di Supabase (SQL Editor), kemudian muat semula:")
        st.code(SQL_LANDING, language="sql")
        st.caption(f"Butiran: {err[:200]}")

    n_img = sum(1 for p in cfg["pegawai"] if p.get("gambar"))
    st.info(f"Status semasa dalam pangkalan data: {n_img} gambar pegawai tersimpan.")

    t1, t2, t3 = st.tabs(["📝 Kandungan & Kotak Info", "🧑‍💼 12 Pegawai (Gambar)", "👁 Pratonton"])

    with t1:
        with st.form("frm_landing_kandungan"):
            tajuk = st.text_input("Tajuk utama", cfg["tajuk"])
            sub = st.text_input("Sub-tajuk", cfg["subtajuk"])
            butang = st.text_input("Teks butang masuk", cfg["butang"])
            st.markdown("**Kotak maklumat** (kosongkan tajuk & teks untuk membuang kotak)")
            info = []
            for i in range(4):
                b = cfg["info"][i] if i < len(cfg["info"]) else {"ikon": "", "tajuk": "", "teks": ""}
                c1, c2 = st.columns([1, 5])
                ik = c1.text_input("Ikon", b["ikon"], key=f"li_ik{i}")
                tj = c2.text_input(f"Tajuk kotak {i+1}", b["tajuk"], key=f"li_tj{i}")
                tx = st.text_area(f"Teks kotak {i+1}", b["teks"], height=70, key=f"li_tx{i}")
                if tj.strip() or tx.strip():
                    info.append({"ikon": ik, "tajuk": tj, "teks": tx})
            if st.form_submit_button("💾 Simpan Kandungan", type="primary"):
                new = copy.deepcopy(cfg)
                new.update({"tajuk": tajuk.strip() or DEFAULT["tajuk"], "subtajuk": sub, "butang": butang.strip() or DEFAULT["butang"], "info": info})
                try:
                    save_config(new)
                    st.success("✅ Kandungan disimpan.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal simpan: {e}")
                    st.code(SQL_LANDING, language="sql")

    with t2:
        st.caption("Muat naik gambar (JPG/PNG, disaran potret). Gambar dipotong 4:5 dan dikecilkan automatik. "
                   "Slot kosong tidak dipaparkan. Carousel berpusing automatik dan berhenti bila tetikus di atasnya.")
        with st.form("frm_landing_pegawai"):
            hasil = []
            for i in range(N_PEGAWAI):
                p = cfg["pegawai"][i]
                with st.container(border=True):
                    c0, c1, c2 = st.columns([1, 3, 3])
                    if p["gambar"]:
                        c0.markdown(f'<img src="{_esc(p["gambar"])}" style="width:70px;border-radius:6px">', unsafe_allow_html=True)
                    else:
                        c0.markdown(f"**#{i+1}**")
                    nama = c1.text_input(f"Nama #{i+1}", p["nama"], key=f"lp_n{i}")
                    jaw = c2.text_input(f"Jawatan #{i+1}", p["jawatan"], key=f"lp_j{i}")
                    f = st.file_uploader(f"Gambar #{i+1}", type=["jpg", "jpeg", "png", "webp"], key=f"lp_f{i}")
                    buang = st.checkbox("Buang gambar sedia ada", key=f"lp_b{i}") if p["gambar"] else False
                hasil.append((nama, jaw, f, buang, p["gambar"]))
            if st.form_submit_button("💾 Simpan Pegawai", type="primary"):
                peg, ralat = [], []
                for i, (nama, jaw, f, buang, lama) in enumerate(hasil):
                    g = "" if buang else lama
                    if f is not None:
                        try:
                            g = proses_gambar(f.getvalue())
                        except Exception as e:
                            ralat.append(f"#{i+1}: {e}")
                    peg.append({"nama": nama.strip(), "jawatan": jaw.strip(), "gambar": g})
                new = copy.deepcopy(cfg); new["pegawai"] = peg
                try:
                    save_config(new)
                    for m in ralat:
                        st.warning(f"Gambar gagal diproses - {m}")
                    st.success(f"✅ Pegawai disimpan ({sum(1 for p in peg if p['gambar'])} gambar). Muat semula halaman untuk melihat status terkini.")
                except Exception as e:
                    st.error(f"Gagal simpan: {e}")
                    st.code(SQL_LANDING, language="sql")

    with t3:
        st.markdown(LANDING_CSS, unsafe_allow_html=True)
        render_hero(cfg, solid=True)
        info_cards(cfg)
        st.button(cfg["butang"], disabled=True, key="prev_btn")
