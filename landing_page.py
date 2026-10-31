# -*- coding: utf-8 -*-
"""landing_page.py - FIXED VERSION - No emoji to avoid mojibake + fix gambar"""

import base64, copy, html as _html, io, json
import streamlit as st
import streamlit.components.v1 as components
import spm_core as core

N_PEGAWAI = 12

DEFAULT = {
    "tajuk": "Selamat Datang ke Sistem Pelantikan Petugas Negeri Selangor",
    "subtajuk": "Jabatan Pendidikan Negeri Selangor - Peperiksaan SPM 2026",
    "butang": "Klik Masuk ke Sistem",
    "info": [
        {"ikon": "", "tajuk": "Pengumuman", "teks": "Semua PPD dan sekolah dimohon melengkapkan cadangan petugas mengikut tarikh yang ditetapkan."},
        {"ikon": "", "tajuk": "Tarikh Penting", "teks": "Kemas kini tarikh tutup cadangan SUP, kelulusan PPD dan pengeluaran surat lantikan di sini."},
        {"ikon": "", "tajuk": "Bantuan", "teks": "Sebarang masalah sila hubungi Sektor Pengurusan Akademik JPN Selangor."},
        {"ikon": "", "tajuk": "Panduan", "teks": "Rujuk manual pengguna untuk panduan SUP, PPD dan JPN."},
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
    try:
        res = core._RAW.table("landing_config").select("config").eq("id", 1).limit(1).execute()
        rows = res.data or []
        if rows:
            return _normalize(rows[0].get("config")), ""
        return _normalize(None), ""
    except Exception as e:
        return _normalize(None), str(e)

def save_config(cfg):
    payload = {"id": 1, "config": cfg}
    core._RAW.table("landing_config").upsert(payload).execute()
    load_config.clear()

def proses_gambar(data: bytes, lebar=300, tinggi=375):
    from PIL import Image, ImageOps
    im = Image.open(io.BytesIO(data))
    im = ImageOps.exif_transpose(im)
    # Handle PNG transparent jadi putih
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        if im.mode == "P":
            im = im.convert("RGBA")
        try:
            mask = im.split()[-1]
            bg.paste(im, mask=mask)
        except:
            bg.paste(im)
        im = bg
    else:
        im = im.convert("RGB")
    
    nisbah = lebar / tinggi
    w, h = im.size
    if w / h > nisbah:
        nw = int(h * nisbah); x0 = (w - nw) // 2
        im = im.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(w / nisbah); y0 = max(0, int((h - nh) * 0.15))
        im = im.crop((0, y0, w, y0 + nh))
    im = im.resize((lebar, tinggi))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=65, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

# Carousel - FIXED: Jangan escape gambar
def carousel_html(pegawai):
    items = [p for p in pegawai if (p.get("nama") or p.get("jawatan") or p.get("gambar"))]
    if not items:
        return ""
    cards = []
    for p in items:
        gambar = p.get("gambar","").strip()
        if gambar and gambar.startswith("data:image"):
            # JANGAN ESCAPE base64 - ini punca gambar putih
            img = f'<img src="{gambar}" alt="">'
        elif gambar:
            img = f'<img src="{_esc(gambar)}" alt="">'
        else:
            ini = "".join(w[0] for w in (p.get("nama") or "?").split()[:2]).upper()
            img = f'<div class="ph">{_esc(ini)}</div>'
        cards.append(f'<div class="card">{img}<div class="nm">{_esc(p.get("nama"))}</div><div class="jw">{_esc(p.get("jawatan"))}</div></div>')
    
    html_cards = "".join(cards)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;background:transparent;font-family:Inter,Arial,sans-serif;overflow:hidden}}
#stage{{height:400px;perspective:1100px;display:flex;align-items:center;justify-content:center}}
#ring{{position:relative;width:170px;height:300px;transform-style:preserve-3d;animation:spin 40s linear infinite}}
#stage:hover #ring{{animation-play-state:paused}}
@keyframes spin{{from{{transform:rotateY(0)}}to{{transform:rotateY(-360deg)}}}}
.card{{position:absolute;left:0;top:0;width:170px;height:300px;background:#fff;border:1px solid #cfdcf3;border-radius:12px;box-shadow:0 6px 18px rgba(13,71,161,.18);overflow:hidden;text-align:center;backface-visibility:hidden}}
.card img,.ph{{width:170px;height:212px;object-fit:cover;display:block}}
.ph{{background:linear-gradient(135deg,#0d47a1,#1976d2);color:#fff;font-size:44px;font-weight:800;display:flex;align-items:center;justify-content:center}}
.nm{{font-size:10.5px;font-weight:700;color:#0d47a1;padding:6px 6px 0;line-height:1.25}}
.jw{{font-size:10px;color:#37474f;padding:2px 6px;line-height:1.25}}
</style></head><body><div id="stage"><div id="ring">{html_cards}</div></div>
<script>
var cs=document.querySelectorAll('.card'),n=cs.length,w=170;
var R=n>1?Math.round((w/2+8)/Math.tan(Math.PI/n)):0; if(n<3)R=0;
cs.forEach(function(c,i){{c.style.transform=n>1?'rotateY('+(i*360/n)+'deg) translateZ('+R+'px)':'none';}});
if(n===1){{document.getElementById('ring').style.animation='none';}}
function fit(){{var s=Math.min(1,(window.innerWidth-10)/(2*R+w+20)); if(!isFinite(s)||s<=0)s=1;
 document.getElementById('stage').style.transform='scale('+s+')';}}
window.addEventListener('resize',fit); fit();
</script></body></html>"""

def render_carousel(pegawai):
    h = carousel_html(pegawai)
    if h:
        components.html(h, height=410)

def render_landing():
    cfg, err = load_config()
    st.markdown(f"""
    <div class="land-top">
      <div style="display:flex;align-items:center"><span class="logo">JPN</span>
        <div><div class="n">JABATAN PENDIDIKAN NEGERI SELANGOR</div><div class="s">KEMENTERIAN PENDIDIKAN MALAYSIA</div></div></div>
      <div class="r">Sistem Pelantikan Petugas SPM Selangor 2026</div>
    </div>
    <div style="text-align:center;padding:26px 8px 6px">
      <span class="land-chip"><i></i>Portal Rasmi</span>
      <div class="land-h1" style="font-size:clamp(24px,5vw,38px);margin:14px auto 6px;max-width:860px"><span style="color:#0d47a1">{_esc(cfg['tajuk'])}</span></div>
      <div style="color:#455a64;font-size:14px">{_esc(cfg['subtajuk'])}</div>
    </div>""", unsafe_allow_html=True)

    render_carousel(cfg["pegawai"])

    if cfg["info"]:
        cols = st.columns(min(4, len(cfg["info"])), gap="small")
        for i, b in enumerate(cfg["info"]):
            with cols[i % len(cols)]:
                st.markdown(f"""<div style="background:#fff;border:1px solid #dbe3f0;border-left:4px solid #0d47a1;border-radius:10px;
                  padding:12px 14px;margin-bottom:10px;min-height:120px">
                  <div style="font-weight:700;color:#0d47a1;font-size:14px">{_esc(b['tajuk'])}</div>
                  <div style="color:#37474f;font-size:12.5px;margin-top:6px;line-height:1.45">{_esc(b['teks'])}</div></div>""",
                            unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button(cfg["butang"], key="btn_masuk_sistem", type="primary", use_container_width=True):
            st.session_state["masuk_sistem"] = True
            st.rerun()

# Halaman admin JPN - TANPA EMOJI
def render_admin_landing():
    st.header("Selenggara Landing Page")
    st.caption("Halaman sambutan yang dipaparkan sebelum pilihan JPN / PPD.")
    cfg, err = load_config()
    if err:
        st.error(f"Ralat baca config: {err}")

    tab1, tab2, tab3 = st.tabs(["Kandungan & Kotak Info", "12 Pegawai (Gambar)", "Pratonton"])

    with tab1:
        with st.form("frm_landing_kandungan"):
            tajuk = st.text_input("Tajuk utama", cfg["tajuk"])
            sub = st.text_input("Sub-tajuk", cfg["subtajuk"])
            butang = st.text_input("Teks butang masuk", cfg["butang"])
            st.markdown("**Kotak maklumat**")
            info = []
            for i in range(4):
                b = cfg["info"][i] if i < len(cfg["info"]) else {"ikon": "", "tajuk": "", "teks": ""}
                c1, c2 = st.columns([1, 5])
                ik = c1.text_input("Ikon", b["ikon"], key=f"li_ik{i}")
                tj = c2.text_input(f"Tajuk kotak {i+1}", b["tajuk"], key=f"li_tj{i}")
                tx = st.text_area(f"Teks kotak {i+1}", b["teks"], height=70, key=f"li_tx{i}")
                if tj.strip() or tx.strip():
                    info.append({"ikon": ik, "tajuk": tj, "teks": tx})
            if st.form_submit_button("Simpan Kandungan", type="primary"):
                new = copy.deepcopy(cfg)
                new.update({"tajuk": tajuk.strip() or DEFAULT["tajuk"], "subtajuk": sub, "butang": butang.strip() or DEFAULT["butang"], "info": info})
                try:
                    save_config(new)
                    st.success("Kandungan disimpan.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal simpan: {e}")

    with tab2:
        st.caption("Muat naik gambar JPG/PNG potret. Gambar akan dipotong 4:5 dan dikecilkan automatik. Upload 1-2 gambar dulu, jangan 12 sekali gus.")
        with st.form("frm_landing_pegawai"):
            hasil = []
            for i in range(N_PEGAWAI):
                p = cfg["pegawai"][i]
                with st.container(border=True):
                    c0, c1, c2 = st.columns([1, 3, 3])
                    if p["gambar"]:
                        try:
                            c0.image(p["gambar"], width=70)
                        except:
                            c0.markdown(f"**#{i+1}** ada gambar")
                    else:
                        c0.markdown(f"**#{i+1}**")
                    nama = c1.text_input(f"Nama #{i+1}", p["nama"], key=f"lp_n{i}")
                    jaw = c2.text_input(f"Jawatan #{i+1}", p["jawatan"], key=f"lp_j{i}")
                    f = st.file_uploader(f"Gambar #{i+1}", type=["jpg", "jpeg", "png", "webp"], key=f"lp_f{i}")
                    buang = st.checkbox("Buang gambar", key=f"lp_b{i}") if p["gambar"] else False
                    # Preview file baru
                    if f is not None:
                        st.info(f"File baru dipilih: {f.name} ({f.size/1024:.1f} KB) - akan disimpan bila tekan Simpan")
                hasil.append((nama, jaw, f, buang, p["gambar"]))
            
            if st.form_submit_button("Simpan Pegawai", type="primary"):
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
                        st.warning(f"Gambar gagal - {m}")
                    st.success(f"Berjaya simpan {len([p for p in peg if p['nama']])} pegawai.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal simpan: {e}")

    with tab3:
        st.markdown(f"### {_esc(cfg['tajuk'])}")
        st.caption(cfg["subtajuk"])
        render_carousel(cfg["pegawai"])
