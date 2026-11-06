import os
import json
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from sehirler import SEHIRLER

app = Flask(__name__)
app.secret_key = "admin_super_gizli_anahtar_2026"

# MongoDB Bulut Bağlantısı
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://mervekelbek_db_user:yo6W3KzcqroFUml6@cluster0.utn3afb.mongodb.net/?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI)
db = client["merve_vitrin_db"]

ilanlar_col = db["ilanlar"]
ayarlar_col = db["ayarlar"]

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------
# TEMEL SEO KELİME HAVUZU
# ---------------------------------------------------------
TEMEL_KELIMELER = [
    "escort", "escort bayan", "vip", "model", "kendi yeri olan", 
    "rezidans", "otel", "türbanlı", "merkez escort", "güncel vitrin"
]

VARSAYILAN_AYARLAR = {
    "site_basligi": "✨ mervekelbek vitrin",
    "karsilama_baslik": "mervekelbek vitrin sayfasına hoşgeldiniz! 🎉",
    "karsilama_metin": "Sitemizin kapanmaması ve en güncel ilanlardan anında haberdar olmak için lütfen WhatsApp kanalımıza katılın.",
    "whatsapp_link": "https://whatsapp.com/channel/0029VbECRV8Dp2QIwgjHse0N",
    "vip_bilgi_mesaji": "VIP alana giriş yapmak için lütfen Proxy Numarası ve Şifrenizi giriniz.",
    "banner_gorsel": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1400",
    "kayan_duyurular": [
        "🔥 Yeni ilanlar eklendi! Sitemizin kapanmaması için WhatsApp kanalımıza katılın.",
        "📢 İlan danışma ve reklam için lütfen WhatsApp kanalımızdan bizimle iletişime geçin.",
        "⭐ Güvenli ve güncel vitrin deneyimi için bildirimleri açık tutun."
    ],
    "popup_aktif": True,
    "popup_baslik": "🌟 ÖNEMLİ DUYURU & HOŞ GELDİNİZ",
    "popup_metin": "Sitemize hoş geldiniz! Güncel ilanlardan ve duyurulardan haberdar olmak, ayrıca sitemizin kapanmaması için lütfen WhatsApp kanalımıza katılmayı unutmayın."
}

def ayartari_yukle():
    kayitli = ayarlar_col.find_one({"_id": "site_ayarlari"})
    if not kayitli:
        ayarlar_col.insert_one({"_id": "site_ayarlari", **VARSAYILAN_AYARLAR})
        return VARSAYILAN_AYARLAR
    
    degisiklik = False
    for k, v in VARSAYILAN_AYARLAR.items():
        if k not in kayitli:
            kayitli[k] = v
            degisiklik = True
    if degisiklik:
        ayarlar_col.update_one({"_id": "site_ayarlari"}, {"$set": kayitli})
    return kayitli

def ayarlari_kaydet(ayarlar):
    ayarlar_col.update_one({"_id": "site_ayarlari"}, {"$set": ayarlar}, upsert=True)

def ilanlari_yukle():
    ilanlar = list(ilanlar_col.find({}, {"_id": 0}))
    simdi = datetime.now()
    degisiklik_var = False
    
    for ilan in ilanlar:
        if ilan.get('sabit', False) and ilan.get('sabit_bitis_tarihi'):
            try:
                bitis_tarihi = datetime.fromisoformat(ilan['sabit_bitis_tarihi'])
                if simdi > bitis_tarihi:
                    ilanlar_col.update_one({"id": ilan['id']}, {"$set": {"sabit": False, "sabit_hafta": 0, "sabit_bitis_tarihi": None}})
                    degisiklik_var = True
            except:
                pass
    if degisiklik_var:
        ilanlar = list(ilanlar_col.find({}, {"_id": 0}))
    return ilanlar

def ilanlari_kaydet_tek(ilan):
    ilanlar_col.update_one({"id": ilan['id']}, {"$set": ilan}, upsert=True)

def telefon_maskele(tel):
    if not tel or len(tel) < 6:
        return "555 *** ** **"
    rakamlar = "".join(filter(str.isdigit, str(tel)))
    if len(rakamlar) >= 10:
        bas = rakamlar[:3]
        son = rakamlar[-2:]
        return f"{bas} *** ** {son}"
    return tel

app.jinja_env.filters['telefon_maskele'] = telefon_maskele

VIP_KULLANICILARI = [
    {
        "proxy_no": "15004332996",
        "proxy_sifre": "551487",
        "rol": "admin"
    }
]

# ---------------------------------------------------------
# 81 İL VE TÜM İLÇELERİ KAPSAYAN DİNAMİK ESCORT SEO MOTORU
# ---------------------------------------------------------
def seo_meta_uret(il=None, semt=None, ilan_ismi=None):
    # Tam aradığın mantık: "İl İlçe Escort" veya "İl Escort" formatını dinamik üretir
    lokasyon_metni = ""
    if il and semt:
        lokasyon_metni = f"{il} {semt} escort"
    elif il:
        lokasyon_metni = f"{il} escort"
    else:
        lokasyon_metni = "türkiye geneli escort"

    rastgele_ek_kw = random.choice(TEMEL_KELIMELER)
    
    if ilan_ismi:
        title = f"{ilan_ismi} | {lokasyon_metni.title()} - Güncel İletişim ve Vitrin"
        description = f"{lokasyon_metni} arayanlar için {ilan_ismi} profili, {rastgele_ek_kw} seçenekleri ve iletişim detayları. WhatsApp kanalımıza katılın."
    elif il and semt:
        title = f"{il} {semt} Escort | {il} {semt} Bayan ve Model Vitrini"
        description = f"{il} {semt} bölgesinde en güncel escort, {rastgele_ek_kw} ve vip ilanlar. Hemen incele."
    elif il:
        title = f"{il} Escort ve İlçe Vitrin Rehberi | Güncel İlanlar"
        description = f"{il} merkez ve tüm ilçelerinde en yeni escort, bayan ve {rastgele_ek_kw} vitrin seçenekleri."
    else:
        title = f"Türkiye Geneli Escort ve Güncel Vitrin Rehberi"
        description = f"81 il ve tüm ilçeler için en yeni escort, model, kendi yeri olan ve vip ilan seçeneklerini keşfedin."
        
    return {"title": title, "description": description}

@app.route('/')
def anasayfa():
    secilen_il = request.args.get('il', '').strip()
    secilen_semt = request.args.get('semt', '').strip()
    ilanlar = ilanlari_yukle()
    ayarlar = ayartari_yukle()
    
    if secilen_il:
        ilanlar = [i for i in ilanlar if i.get('il') == secilen_il]
    if secilen_semt:
        ilanlar = [i for i in ilanlar if i.get('semt') == secilen_semt]
        
    sirali_ilanlar = sorted(ilanlar, key=lambda x: (not x.get('sabit', False), -x.get('id', 0)))
    
    seo_veri = seo_meta_uret(il=secilen_il, semt=secilen_semt)
    
    return render_template('index.html', ilanlar=sirali_ilanlar, ayarlar=ayarlar, sehirler=SEHIRLER, secilen_il=secilen_il, secilen_semt=secilen_semt, seo=seo_veri)

@app.route('/model/<int:id>')
def model_detay(id):
    ilanlar = ilanlari_yukle()
    ilan = next((i for i in ilanlar if i.get('id') == id), None)
    if not ilan:
        return "İlan bulunamadı", 404
    vip_giris_var = session.get('vip_giris', False)
    
    seo_veri = seo_meta_uret(il=ilan.get('il'), semt=ilan.get('semt'), ilan_ismi=ilan.get('isim'))
    
    return render_template('model_detay.html', ilan=ilan, vip_giris_var=vip_giris_var, seo=seo_veri)

@app.route('/admin/giris', methods=['GET', 'POST'])
def admin_giris():
    hata = None
    ayarlar = ayartari_yukle()
    if request.method == 'POST':
        p_no = request.form.get('proxy_no', '').strip()
        p_sifre = request.form.get('proxy_sifre', '').strip()
        bulundu_rol = None
        for vip in VIP_KULLANICILARI:
            if vip["proxy_no"] == p_no and vip["proxy_sifre"] == p_sifre:
                bulundu_rol = vip["rol"]
                break
        if bulundu_rol == "admin":
            session['admin_giris'] = True
            session['vip_giris'] = True
            return redirect(url_for('admin_paneli'))
        else:
            hata = "Hatalı Proxy Numarası veya Şifresi!"
    return render_template('admin_giris.html', hata=hata, ayarlar=ayarlar)

@app.route('/admin')
def admin_paneli():
    if not session.get('admin_giris'):
        return redirect(url_for('admin_giris'))
    ilanlar = ilanlari_yukle()
    ayarlar = ayartari_yukle()
    
    arama_sorgu = request.args.get('q', '').strip().lower()
    if arama_sorgu:
        ilanlar = [
            i for i in ilanlar 
            if arama_sorgu in i.get('isim', '').lower() or 
               arama_sorgu in i.get('il', '').lower() or 
               arama_sorgu in i.get('semt', '').lower() or 
               arama_sorgu in i.get('tel', '') or 
               arama_sorgu in i.get('tel2', '')
        ]

    sabit_sayisi = sum(1 for i in ilanlari_yukle() if i.get('sabit', False))
    return render_template('admin_paneli.html', ayarlar=ayarlar, ilanlar=ilanlar, vip_listesi=VIP_KULLANICILARI, sehirler=SEHIRLER, sabit_sayisi=sabit_sayisi, arama_sorgu=arama_sorgu)

@app.route('/admin/whatsapp-guncelle', methods=['POST'])
def admin_whatsapp_guncelle():
    if not session.get('admin_giris'): 
        return redirect(url_for('admin_giris'))
    ayarlar = ayartari_yukle()
    yeni_link = request.form.get('whatsapp_link', '').strip()
    if yeni_link:
        ayarlar['whatsapp_link'] = yeni_link
        ayarlari_kaydet(ayarlar)
    return redirect(url_for('admin_paneli'))

@app.route('/admin/popup-guncelle', methods=['POST'])
def admin_popup_guncelle():
    if not session.get('admin_giris'): 
        return redirect(url_for('admin_giris'))
    ayarlar = ayartari_yukle()
    ayarlar['popup_aktif'] = True if request.form.get('popup_aktif') == '1' else False
    ayarlar['popup_baslik'] = request.form.get('popup_baslik', '').strip()
    ayarlar['popup_metin'] = request.form.get('popup_metin', '').strip()
    ayarlari_kaydet(ayarlar)
    return redirect(url_for('admin_paneli'))

@app.route('/admin/banner-guncelle', methods=['POST'])
def admin_banner_guncelle():
    if not session.get('admin_giris'): 
        return redirect(url_for('admin_giris'))
    ayarlar = ayartari_yukle()
    yeni_baslik = request.form.get('karsilama_baslik', '').strip()
    yeni_metin = request.form.get('karsilama_metin', '').strip()
    if yeni_baslik: ayarlar['karsilama_baslik'] = yeni_baslik
    if yeni_metin: ayarlar['karsilama_metin'] = yeni_metin

    banner_dosya = request.files.get('banner_dosya')
    if banner_dosya and banner_dosya.filename:
        fname = secure_filename(banner_dosya.filename)
        banner_dosya.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        ayarlar['banner_gorsel'] = f"/{UPLOAD_FOLDER}/{fname}"
        
    ayarlari_kaydet(ayarlar)
    return redirect(url_for('admin_paneli'))

@app.route('/admin/ilan-ekle', methods=['POST'])
def admin_ilan_ekle():
    if not session.get('admin_giris'): 
        return redirect(url_for('admin_giris'))
    ilanlar = ilanlari_yukle()
    
    sabit_istegi = True if request.form.get('sabit') == '1' else False
    if sabit_istegi and sum(1 for i in ilanlar if i.get('sabit', False)) >= 10:
        sabit_istegi = False

    sabit_hafta = max(1, min(4, int(request.form.get('sabit_hafta', 1))))
    sabit_bitis_tarihi = (datetime.now() + timedelta(weeks=sabit_hafta)).isoformat() if sabit_istegi else None

    fotolar = request.files.getlist('fotolar')
    galeri_yollari = []
    for dosya in fotolar[:3]:
        if dosya and dosya.filename:
            fname = secure_filename(dosya.filename)
            dosya.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            galeri_yollari.append(f"/{UPLOAD_FOLDER}/{fname}")

    if not galeri_yollari:
        galeri_yollari = ["https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600"]

    video_dosya = request.files.get('video_dosya')
    video_yolu = ""
    if video_dosya and video_dosya.filename:
        vname = secure_filename(video_dosya.filename)
        video_dosya.save(os.path.join(app.config['UPLOAD_FOLDER'], vname))
        video_yolu = f"/{UPLOAD_FOLDER}/{vname}"

    yeni_id = max([i.get('id', 0) for i in ilanlar], default=0) + 1

    # İL VE İLÇEYE GÖRE OTOMATİK "ESCORT" KELİME ENTEGRASYONU
    ham_aciklama = request.form.get('aciklama', '')
    il_adi = request.form.get('il', '')
    semt_adi = request.form.get('semt', '')
    
    lokasyon_ifade = f"{il_adi} {semt_adi}".strip()
    
    otomatik_seo_eklenti = f"\n\n[{lokasyon_ifade} escort, {il_adi} escort ve kendi yeri olan bayan arayanlar için en güncel ilan detayları. İletişim bilgileri yukarıda yer almaktadır.]"
    zenginlesmis_aciklama = ham_aciklama + otomatik_seo_eklenti

    yeni_ilan = {
        "id": yeni_id,
        "isim": request.form.get('isim'),
        "tel": request.form.get('tel'),
        "tel2": request.form.get('tel2', '').strip(),
        "yas": request.form.get('yas'),
        "boy": request.form.get('boy'),
        "kilo": request.form.get('kilo'),
        "il": il_adi,
        "semt": semt_adi,
        "gorusme": request.form.get('gorusme'),
        "sabit": sabit_istegi,
        "sabit_hafta": sabit_hafta if sabit_istegi else 0,
        "sabit_bitis_tarihi": sabit_bitis_tarihi,
        "galeri": galeri_yollari,
        "ana_gorsel": galeri_yollari[0],
        "video": video_yolu,
        "aciklama": zenginlesmis_aciklama
    }

    ilanlar_col.insert_one(yeni_ilan)
    return redirect(url_for('admin_paneli'))

@app.route('/admin/ilan-duzenle/<int:id>', methods=['GET', 'POST'])
def admin_ilan_duzenle(id):
    if not session.get('admin_giris'): 
        return redirect(url_for('admin_giris'))
    ilanlar = ilanlari_yukle()
    ilan = next((i for i in ilanlar if i.get('id'] == id), None)
    if not ilan: return "İlan bulunamadı", 404
        
    if request.method == 'POST':
        sabit_istegi = True if request.form.get('sabit') == '1' else False
        if sabit_istegi and not ilan.get('sabit', False) and sum(1 for i in ilanlar if i.get('sabit', False)) >= 10:
            sabit_istegi = False

        sabit_hafta = int(request.form.get('sabit_hafta', 1))
        if sabit_istegi:
            if not ilan.get('sabit', False) or ilan.get('sabit_hafta') != sabit_hafta:
                ilan['sabit_bitis_tarihi'] = (datetime.now() + timedelta(weeks=sabit_hafta)).isoformat()
        else:
            ilan['sabit_bitis_tarihi'] = None

        ilan['isim'] = request.form.get('isim')
        ilan['tel'] = request.form.get('tel')
        ilan['tel2'] = request.form.get('tel2', '').strip()
        ilan['yas'] = request.form.get('yas')
        ilan['boy'] = request.form.get('boy')
        ilan['kilo'] = request.form.get('kilo')
        ilan['il'] = request.form.get('il')
        ilan['semt'] = request.form.get('semt')
        ilan['gorusme'] = request.form.get('gorusme')
        ilan['sabit'] = sabit_istegi
        ilan['sabit_hafta'] = sabit_hafta if sabit_istegi else 0
        ilan['aciklama'] = request.form.get('aciklama')
        
        ilanlari_kaydet_tek(ilan)
        return redirect(url_for('admin_paneli'))
        
    return render_template('admin_duzenle.html', ilan=ilan)

@app.route('/admin/ilan-sil/<int:id>')
def admin_ilan_sil(id):
    if not session.get('admin_giris'): 
        return redirect(url_for('admin_paneli'))
    ilanlar_col.delete_one({"id": id})
    return redirect(url_for('admin_paneli'))

@app.route('/admin/cikis')
def admin_cikis():
    session.clear()
    return redirect(url_for('anasayfa'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
