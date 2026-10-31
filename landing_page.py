# -*- coding: utf-8 -*-
"""landing_page.py - FIXED V2 - Buang form untuk pegawai supaya gambar tak hilang"""
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
DEFAULT["pegawai"][0] = {"nama": "DATIN WAN NOR ASHIKIN BINTI ABU KASSIM", "jawatan": "Pengarah Pendidikan JPN Selangor", "gambar": ""}

def _esc(x):
    return _html.escape(str(x if x is not None else ""))

def _normalize(cfg):
    out = copy.deepcopy(DEFAULT)
    if isinstance(cfg, str):
        try: cfg = json.loads(cfg)
        except: cfg = {}
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

@st.cache_data(ttl=60, show_spinner=False)
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
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255,255,255))
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
        nw = int(h * nisbah); x0 = (w - nw)//2
        im = im.crop((x0, 0, x0+nw, h))
    else:
        nh = int(w / nisbah); y0 = max(0, int((h-nh)*0.15))
        im = im.crop((0, y0, w, y0+nh))
    im = im.resize((lebar, tinggi))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=65, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return "data:image/jpeg;base64," + b64

def carousel_html(pegawai):
    items = [p for p in pegawai if (p.get("nama") or p.get("jawatan") or p.get("gambar"))]
    if not items:
        return ""
    cards = []
    for p in items:
        g = p.get("gambar","").strip()
        if g.startswith("data:image"):
            img = f'<img src="{g}" alt="">'
        elif g:
            img = f'<img src="{_esc(g)}" alt="">'
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
      <div class="land-h1" style="font-size:clamp(24px,5vw,38px);margin:14px auto 6px;max-width:860px"><span style="color:#0d47a1">{_esc(cfg['tajuk'])}</span></div>
      <div style="color:#455a64;font-size:14px">{_esc(cfg['subtajuk'])}</div>
    </div>""", unsafe_allow_html=True)
    render_carousel(cfg["pegawai"])
    if cfg["info"]:
        cols = st.columns(min(4, len(cfg["info"])), gap="small")
        for i, b in enumerate(cfg["info"]):
            with cols[i % len(cols)]:
                st.markdown(f"""<div style="background:#fff;border:1px solid #dbe3f0;border-left:4px solid #0d47a1;border-radius:10px;padding:12px 14px;margin-bottom:10px;min-height:120px">
                  <div style="font-weight:700;color:#0d47a1;font-size:14px">{_esc(b['tajuk'])}</div>
                  <div style="color:#37474f;font-size:12.5px;margin-top:6px;line-height:1.45">{_esc(b['teks'])}</div></div>""", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button(cfg["butang"], key="btn_masuk_sistem", type="primary", use_container_width=True):
            st.session_state["masuk_sistem"] = True
            st.rerun()

def render_admin_landing():
    st.header("Selenggara Landing Page")
    cfg, err = load_config()

    tab1, tab2, tab3 = st.tabs(["Kandungan & Kotak Info", "12 Pegawai (Gambar)", "Pratonton"])
    with tab1:
        with st.form("frm_kandungan"):
            tajuk = st.text_input("Tajuk utama", cfg["tajuk"])
            sub = st.text_input("Sub-tajuk", cfg["subtajuk"])
            butang = st.text_input("Teks butang masuk", cfg["butang"])
            info = []
            for i in range(4):
                b = cfg["info"][i] if i < len(cfg["info"]) else {"tajuk": "", "teks": ""}
                tj = st.text_input(f"Tajuk kotak {i+1}", b["tajuk"], key=f"li_tj{i}")
                tx = st.text_area(f"Teks kotak {i+1}", b["teks"], height=70, key=f"li_tx{i}")
                if tj.strip() or tx.strip():
                    info.append({"tajuk": tj, "teks": tx})
            if st.form_submit_button("Simpan Kandungan", type="primary"):
                new = copy.deepcopy(cfg)
                new.update({"tajuk": tajuk, "subtajuk": sub, "butang": butang, "info": info})
                save_config(new)
                st.success("Kandungan disimpan.")
                st.rerun()

    with tab2:
        st.info("FIXED: Sekarang tidak guna form, jadi gambar takkan hilang lagi bila tekan Simpan.")
        # Kita TIDAK guna st.form di sini lagi!
        peg_baru = []
        for i in range(N_PEGAWAI):
            p = cfg["pegawai"][i]
            with st.container(border=True):
                c0, c1, c2 = st.columns([1, 3, 3])
                with c0:
                    if p["gambar"]:
                        st.image(p["gambar"], width=80)
                        st.caption(f"Ada gambar ({len(p['gambar'])//1000}KB)")
                    else:
                        st.write(f"#{i+1} Kosong")
                with c1:
                    nama = st.text_input(f"Nama #{i+1}", p["nama"], key=f"v2_n{i}")
                with c2:
                    jaw = st.text_input(f"Jawatan #{i+1}", p["jawatan"], key=f"v2_j{i}")
                
                f = st.file_uploader(f"Upload Gambar Baru #{i+1} (PNG/JPG)", type=["jpg","jpeg","png","webp"], key=f"v2_f{i}")
                buang = st.checkbox(f"Buang gambar #{i+1}", key=f"v2_b{i}") if p["gambar"] else False
                
                # Logic simpan gambar
                g = ""
                if buang:
                    g = ""
                    st.warning(f"Gambar #{i+1} akan dibuang bila tekan Simpan")
                elif f is not None:
                    try:
                        g = proses_gambar(f.getvalue())
                        st.success(f"Gambar baru #{i+1} OK: {f.name} -> {len(g)//1000}KB")
                        st.image(g, width=80)
                    except Exception as e:
                        st.error(f"Gagal proses gambar #{i+1}: {e}")
                        g = p["gambar"]
                else:
                    g = p["gambar"]
                
                peg_baru.append({"nama": nama, "jawatan": jaw, "gambar": g, "_file": f})

        if st.button("SIMPAN SEMUA PEGAWAI", type="primary", use_container_width=True, key="btn_save_pegawai_v2"):
            final_peg = [{"nama": p["nama"].strip(), "jawatan": p["jawatan"].strip(), "gambar": p["gambar"]} for p in peg_baru]
            # Filter debug
            ada_gambar = sum(1 for p in final_peg if p["gambar"])
            st.write(f"Mahu simpan: {len(final_peg)} pegawai, {ada_gambar} ada gambar")
            try:
                new = copy.deepcopy(cfg)
                new["pegawai"] = final_peg
                save_config(new)
                st.success(f"Berjaya! {ada_gambar} gambar disimpan. Sila check Pratonton.")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Gagal simpan: {e}")
                import traceback
                st.code(traceback.format_exc())

    with tab3:
        st.subheader(cfg["tajuk"])
        render_carousel(cfg["pegawai"])
        if not any(p["gambar"] for p in cfg["pegawai"]):
            st.warning("Tiada gambar lagi dalam database. Upload dalam tab 12 Pegawai.")
