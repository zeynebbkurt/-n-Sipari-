import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import os

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Saat Sipariş Formu", page_icon="⌚")

# Google Sheet Linkin
url = "https://docs.google.com/spreadsheets/d/1DRZn56SaIYCCRnhPP7sN-IMgnqFwJcS2KaEchqihUvw/edit?usp=sharing"

# 2. MODEL VE STOK VERİSİNİ .XLS DOSYASINDAN OKU
@st.cache_data
def stoklu_modelleri_getir():
    # Uzantıyı .xls olarak bıraktık
    dosya_adi = 'Satış.xls'
    if os.path.exists(dosya_adi):
        try:
            # .xls dosyalarını okumak için engine='xlrd' ekledik
            df = pd.read_excel(dosya_adi, engine='xlrd')
            
            # Başlıklardaki boşlukları temizle
            df.columns = [str(c).strip() for c in df.columns]
            
            if 'Model' in df.columns and 'Stok' in df.columns:
                # Boş satırları temizle ve sözlüğe çevir
                df = df.dropna(subset=['Model', 'Stok'])
                return dict(zip(df['Model'], df['Stok']))
            else:
                st.error("Excel'de 'Model' veya 'Stok' başlıkları bulunamadı!")
        except Exception as e:
            st.error(f"Excel okuma hatası: {e}")
            
    return {"Örnek Model A": 10} # Dosya bulunamazsa görünecek yedek

# --- ARAYÜZ (ANKET FORMU YAPISI) ---
st.title("⌚ Saat Sipariş Formu")
st.info("Lütfen bilgilerinizi girin ve istediğiniz modellerin adetlerini seçin.")

musteri = st.text_input("Müşteri Ad Soyad")
firma = st.text_input("Firma Adı")

stok_verisi = stoklu_modelleri_getir()
siparisler = {}

st.write("### Mevcut Modeller ve Stoklar")

# Excel'den gelen her model için bir satır oluştur
for model, stok_miktari in stok_verisi.items():
    try:
        max_adet = int(stok_miktari)
    except:
        max_adet = 0

    if max_adet > 0:
        col1, col2 = st.columns([3, 1])
        with col1: 
            st.write(f"**{model}**")
            st.caption(f"Kalan Stok: {max_adet}")
        with col2:
            # max_value=max_adet sayesinde stok sınırı koyduk
            adet = st.number_input(
                "Adet", 
                min_value=0, 
                max_value=max_adet, 
                step=1, 
                key=f"key_{model}", 
                label_visibility="collapsed"
            )
            if adet > 0:
                siparisler[model] = adet
    else:
        st.write(f"~~{model} (Stok Tükendi)~~")

# --- VERİYİ GOOGLE SHEET'E KAYDETME ---
if st.button("🚀 Siparişi Tamamla"):
    if musteri and firma and siparisler:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            try:
                df_mevcut = conn.read(spreadsheet=url)
            except:
                df_mevcut = pd.DataFrame(columns=["Tarih", "Müşteri", "Firma", "Model", "Adet"])
            
            yeni_satirlar = []
            zaman = datetime.now().strftime("%d/%m/%Y %H:%M")
            for m, a in siparisler.items():
                yeni_satirlar.append({
                    "Tarih": zaman, "Müşteri": musteri, "Firma": firma, "Model": m, "Adet": a
                })
            
            df_yeni = pd.DataFrame(yeni_satirlar)
            df_final = pd.concat([df_mevcut, df_yeni], ignore_index=True)
            
            conn.update(spreadsheet=url, data=df_final)
            
            st.success(f"Teşekkürler {musteri}, talebiniz başarıyla iletildi!")
            st.balloons()
            
        except Exception as e:
            st.error("Google Sheet bağlantı hatası!")
            st.info(f"Hata detayı: {e}")
    else:
        st.warning("Lütfen bilgilerinizi doldurun ve en az bir ürün seçin.")



