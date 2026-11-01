# -*- coding: utf-8 -*-
"""role_ppd.py - Peranan PPD dengan menu baru Lantik Penyelia Kawasan (asing dari Selenggara Bilik Kebal)"""

import streamlit as st
import spm_core as _core
import ui_theme as _ui
from ui_theme import shell_header_ppd, shell_layout, esc
from spm_core import FLY_PPD, PPD_MAP, KOD_DAERAH
from tahun_sistem import tahun_semasa

# ambil semua dari core & ui
globals().update({k: v for k, v in vars(_core).items() if not k.startswith("__")})
globals().update({k: v for k, v in vars(_ui).items() if not k.startswith("__")})

# Menu utama PPD - baru: penyelia_kawasan di bawah selenggara
MENU_PPD = [
    ('dashboard', '📊 Dashboard PPD'),
    ('pusat', '🏫 Pusat'),
    ('zon', '🗺️ Penempatan Zon'),
    ('cadangan', '📋 Cadangan SUP'),
    ('jana', '🌍 Jana Penempatan'),
    ('hasil', '📊 Hasil Penempatan'),
    ('semakan', '🔍 Semakan Lantikan'),
    ('kelulusan', '✅ Kelulusan'),
    ('selenggara', '🔐 Selenggara Bilik Kebal'),
    ('penyelia_kawasan', '👮 Lantik Penyelia Kawasan'),
    ('jana_surat', '📄 Jana Surat Lantikan'),
    ('keluar', '🚪 Log Keluar'),
]

def render_ppd():
    kod_ppd = st.session_state.get("kod", "").upper()
    if kod_ppd not in KOD_DAERAH:
        st.error("Kod PPD tidak sah")
        return
    shell_header_ppd(kod_ppd)
    menu, fly_cur, col_main = shell_layout("ppd_menu_sel", MENU_PPD, FLY_PPD, "ppd_dash_sub", "fly_ppd")

    with col_main:
        if menu == "keluar":
            st.session_state.clear()
            st.rerun()

        elif menu == "dashboard":
            import ppd_dashboard as _dash
            if hasattr(_dash, "render"):
                _dash.render(kod_ppd, fly_cur)

        elif menu == "pusat":
            import ppd_pusat as _pusat
            if hasattr(_pusat, "render"):
                _pusat.render(kod_ppd, fly_cur)

        elif menu == "zon":
            import ppd_zon
            if fly_cur == "tetap":
                ppd_zon.render_tetapan_zon(kod_ppd)
            elif fly_cur == "tempat":
                ppd_zon._view_jana(kod_ppd, ppd_zon.zon_db_ok())
            elif fly_cur == "semak":
                ppd_zon._view_semak(kod_ppd, ppd_zon.zon_db_ok())
            else:
                ppd_zon.render_penempatan_zon(kod_ppd, fly_cur)

        elif menu == "cadangan":
            import ppd_cadangan
            ppd_cadangan.render_cadangan(kod_ppd, fly_cur)

        elif menu == "selenggara":
            # Selenggara Bilik Kebal sahaja (form, senarai, import) - TIDAK ada penyel ia lagi
            import selenggara_bilik_kebal as _sbk
            if hasattr(_sbk, "render"):
                _sbk.render(kod_ppd, fly_cur)
            else:
                # fallback jika file lama
                st.subheader("Selenggara Bilik Kebal")
                st.caption("Menu ini hanya untuk tetapkan zon bilik kebal (kod_ppd, kod_bilik_kebal, kod_sekolah)")
                # cuba render dari ppd_zon jika tiada
                try:
                    import selenggara_sp_1 as _ssp
                    _ssp.render_selenggara_bk(kod_ppd, fly_cur)
                except Exception as e:
                    st.info(f"Modul selenggara_bilik_kebal belum ada: {e}")

        elif menu == "penyelia_kawasan":
            # MENU BARU - asing dari selenggara
            import ppd_penyelia_kawasan
            ppd_penyelia_kawasan.render_penyelia_kawasan(kod_ppd, fly_cur)

        elif menu == "jana":
            import ppd_jana as _jana
            if hasattr(_jana, "render"):
                _jana.render(kod_ppd, fly_cur)

        elif menu == "hasil":
            import ppd_hasil as _hasil
            if hasattr(_hasil, "render"):
                _hasil.render(kod_ppd, fly_cur)

        elif menu == "semakan":
            import ppd_semakan as _sem
            if hasattr(_sem, "render"):
                _sem.render(kod_ppd, fly_cur)

        elif menu == "kelulusan":
            import ppd_kelulusan as _lulus
            if hasattr(_lulus, "render"):
                _lulus.render(kod_ppd, fly_cur)

        elif menu == "jana_surat":
            import ppd_surat as _surat
            if hasattr(_surat, "render"):
                _surat.render(kod_ppd, fly_cur)
            else:
                # fallback guna surat_tools
                from surat_tools import surat_panel
                surat_panel("PPD", kod_ppd)

        else:
            st.info(f"Menu {menu} belum diimplementasikan")
