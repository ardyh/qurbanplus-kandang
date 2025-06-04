import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="Sistem Manajemen Qurban",
    page_icon="🐑",
    layout="wide"
)

st.title("Master App Tim Kandang")
st.markdown("""
### QurbanPlus 1446H

Sistem ini membantu Anda mengelola inventaris hewan qurban dengan mudah dan efisien.

Gunakan menu di sidebar untuk:
- **Form Masuk**: Mencatat hewan yang masuk ke kandang
- **Form Keluar**: Mencatat hewan yang keluar dari kandang
- **Dashboard**: Melihat ringkasan dan statistik inventaris

Untuk memulai, pilih salah satu menu di sidebar sebelah kiri.
""") 