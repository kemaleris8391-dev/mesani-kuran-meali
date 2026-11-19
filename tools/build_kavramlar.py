# -*- coding: utf-8 -*-
"""
Kavramlar Klasörü ve Ayrıntılı Ayet Haritalayıcı
Tüm mühürlü kökler için tek merkezi Tabula Rasa & İ'rablı Sentaktik Üretim Motoru (v3.0)
"""

import os
import re
import json
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quran_analyzer import (
    DATA_DIR,
    SURAH_NAMES,
    QuranCorpus,
    extract_ayah_words,
    load_verses,
    strip_tashkeel,
)
from tabula_rasa import purify_tabula_rasa

ROOT_CONFIG = {
    'أ-ل-ه': {
        'buckwalter': 'Alh',
        'slug': 'ilah_allah_alh',
        'concept_name': 'İlâh / Allâh (Yegâne Mutlak Sığınak ve Otorite Mercii)',
        'keywords': ['allah', 'ilâh', 'ilâhlar', 'sığınak'],
    },
    'ق-و-ل': {
        'buckwalter': 'qwl',
        'slug': 'kavl_qwl',
        'concept_name': 'Kavl (Söz, İfade, Dışa Vurum ve Beyan)',
        'keywords': ['dedi', 'derler', 'de ki', 'deyin', 'söz', 'söyledi', 'söylediler', 'der', 'söyle', 'uydurma'],
    },
    'أ-م-ن': {
        'buckwalter': 'Amn',
        'slug': 'iman_amn',
        'concept_name': 'İman / Güven (İçsel Emniyet, Sarsılmazlık ve Güven Bağı)',
        'keywords': ['güven', 'emin', 'bağlan', 'itimat', 'emanet'],
    },
    'ق-و-م': {
        'buckwalter': 'qwm',
        'slug': 'kiyam_qwm',
        'concept_name': 'Kıyâm / İkāmet (Ayağa Kalkış, Duruş ve Ayakta Tutma)',
        'keywords': ['ayakta', 'duruş', 'diril', 'kalk', 'dosdoğru', 'topluluk', 'kavim'],
    },
    'ك-ف-ر': {
        'buckwalter': 'kfr',
        'slug': 'kufr_kfr',
        'concept_name': 'Küfür (Gerçeğin Üzerini Örtme ve Yok Sayma)',
        'keywords': ['üzerini ört', 'örttü', 'çiftçi', 'yok say'],
    },
    'ن-ف-ق': {
        'buckwalter': 'nfq',
        'slug': 'infak_nifak_nfq',
        'concept_name': 'İnfak / Nifak (Dolaşıma Sokma / İki Çıkışlı Kaypaklık)',
        'keywords': ['dolaşım', 'paylaş', 'iki çıkışlı', 'kaypak', 'tünel'],
    },
    'ص-ل-و': {
        'buckwalter': 'Slw',
        'slug': 'salat_slw',
        'concept_name': 'Salât (Yöneliş, İrtibat ve Sorumluluk Bağı)',
        'keywords': ['irtibat', 'yönel', 'salât', 'destek', 'bağ'],
    },
    'س-ج-د': {
        'buckwalter': 'sjd',
        'slug': 'sucud_sjd',
        'concept_name': 'Sücûd (Boyun Eğme ve Koşulsuz Teslimiyet)',
        'keywords': ['boyun', 'teslim'],
    },
    'ش-ك-ر': {
        'buckwalter': '$kr',
        'slug': 'sukr_skr',
        'concept_name': 'Şükür (Nimetin Değerini Bilip Açığa Vurma)',
        'keywords': ['değerini bil', 'açığa vur', 'nimet', 'emek'],
    },
    'ر-ك-ع': {
        'buckwalter': 'rkE',
        'slug': 'ruku_rke',
        'concept_name': 'Rükû (Tevazu ile Öne Eğilme ve Ortak İradeye Katılma)',
        'keywords': ['boyun bük', 'tevazu', 'eğil', 'esne'],
    },
    'ك-و-ن': {
        'buckwalter': 'kwn',
        'slug': 'kevn_kwn',
        'concept_name': 'Kevn / Kâne (Yerleşip Ortaya Çıkma, Oluş ve Sabit Gerçeklik)',
        'keywords': ['oldu', 'olur', 'olun', 'olsun', 'idi', 'yer', 'konum', 'meydan', 'bulun'],
    },
    'ر-ب-ب': {
        'buckwalter': 'rbb',
        'slug': 'rabb_rbb',
        'concept_name': 'Rabb (Besleyip Büyüten, Onarıp Olgunlaştıran Sahip ve Otorite)',
        'keywords': ['rabb', 'rabler', 'erbab', 'efendi', 'yetiştir', 'eğit', 'üvey', 'topluluk'],
    },
    'ع-ل-م': {
        'buckwalter': 'Elm',
        'slug': 'ilim_elm',
        'concept_name': 'İlim / Alîm / Âlem (Ayırt Edici İz, İşaret ve Doğrudan Bilgi)',
        'keywords': ['bil', 'bilen', 'bilgi', 'öğret', 'öğren', 'âlem', 'işaret', 'belirti', 'dağ', 'belirli'],
    },
    'أ-ت-ي': {
        'buckwalter': 'Aty',
        'slug': 'ita_ityan_aty',
        'concept_name': 'İtâ / İtyân (Engelsiz Akıp Gelmek, Yönelip Ulaşmak ve Teslim Etmek)',
        'keywords': ['gel', 'getir', 'ver', 'ulaş', 'teslim', 'yap', 'işle'],
    },
    'ش-ي-أ': {
        'buckwalter': '$yA',
        'slug': 'mesiet_sey_sya',
        'concept_name': 'Şey / Meşîet (İrade ile Seçip Oldurmak, Varlık Birimi)',
        'keywords': ['şey', 'birim', 'nesne', 'eşya', 'dile', 'iste', 'irade', 'seç', 'oldur', 'varlık'],
    },
    'ب-ي-ن': {
        'buckwalter': 'byn',
        'slug': 'beyan_byn',
        'concept_name': 'Beyân / Beyn (Aralık Açma, Sınırını Ayırıp Belirginleştirme)',
        'keywords': ['açık', 'apaçık', 'belirgin', 'aralık', 'arasında', 'ayırt', 'açıkla', 'kanıt', 'belge'],
    },
    'ر-س-ل': {
        'buckwalter': 'rsl',
        'slug': 'irsal_resul_rsl',
        'concept_name': 'İrsâl / Resûl (Salıp Göndermek, Akıtmak, Görevli Elçi)',
        'keywords': ['gönder', 'sal', 'elçi', 'haberci', 'mesaj', 'bildiri', 'görevli', 'akım'],
    },
    'أ-ر-ض': {
        'buckwalter': 'ArD',
        'slug': 'arz_ard',
        'concept_name': 'Arz (Alt Taban, Üzerinde Yaşanılan Zemin ve Coğrafya)',
        'keywords': ['yeryüzü', 'yer', 'toprak', 'zemin', 'taban', 'diyar', 'ülke', 'yurt'],
    },
    'ي-و-م': {
        'buckwalter': 'ywm',
        'slug': 'yevm_ywm',
        'concept_name': 'Yevm (Zaman Birimi, Aydınlık Döngü, Tarihsel Dönem / Aşama)',
        'keywords': ['gün', 'dönem', 'çağ', 'evre', 'aşama', 'vakit', 'bugün', 'süre'],
    },
    'أ-ي-ي': {
        'buckwalter': 'Ayy',
        'slug': 'ayet_ayy',
        'concept_name': 'Âyet (Açık İşaret, Doğal Kanıt, Bilgilendirici Metin Birimi)',
        'keywords': ['ayet', 'işaret', 'delil', 'kanıt', 'belge', 'gösterge', 'mesaj'],
    },
    'س-م-و': {
        'buckwalter': 'smw',
        'slug': 'sema_isim_smw',
        'concept_name': 'Semâ / İsim (Üst Kozmik Katman, Tavan ve Tanımlayıcı Ad)',
        'keywords': ['gök', 'gökler', 'sema', 'semavat', 'tavan', 'isim', 'ad', 'adlandır', 'belirlenmiş', 'süre'],
    },
    'ع-ذ-ب': {
        'buckwalter': 'E*b',
        'slug': 'azap_ezb',
        'concept_name': 'Azap (Tatlılıktan Kesilme, Mahrumiyet ve Ağır Yaptırım / Acı)',
        'keywords': ['azap', 'yaptırım', 'ceza', 'acı', 'ıstırap', 'sıkıntı', 'yoksunluk', 'tatlı'],
    },
    'ك-ل-ل': {
        'buckwalter': 'kll',
        'slug': 'kull_kll',
        'concept_name': 'Küll / Kelâle / Kell (Kapsayan Bütünlük, Yanal Akrabalık ve Ağır Yük)',
        'keywords': ['her', 'bütün', 'tamam', 'hepsi', 'tüm', 'her ne zaman', 'kelale', 'yük'],
    },
    'ع-م-ل': {
        'buckwalter': 'Eml',
        'slug': 'amel_eml',
        'concept_name': 'Amel (Bilinçli Eylem, İş, Emek ve Üretim)',
        'keywords': ['amel', 'iş', 'yap', 'işle', 'üret', 'çalış', 'eylem', 'emek', 'memur', 'topla', 'boşa', 'yaptık'],
    },
    'ج-ع-ل': {
        'buckwalter': 'jEl',
        'slug': 'cel_jel',
        'concept_name': "Ce'l (Kılmak, Düzenlemek, İşlev ve Rol Atamak)",
        'keywords': ['kıl', 'yap', 'eyle', 'et', 'dönüştür', 'halife', 'önder', 'döşek', 'örtü', 'say', 'ortak', 'işlev'],
    },
    'ر-ح-م': {
        'buckwalter': 'rHm',
        'slug': 'rahmet_rhm',
        'concept_name': 'Rahmet (Kuşatıcı Şefkat, Besleyici Koruma ve Rahim Bağı)',
        'keywords': ['rahmet', 'rahman', 'rahim', 'merhamet', 'şefkat', 'rahimlerinde', 'akrab', 'esirge', 'koru', 'besle'],
    },
    'ر-أ-ي': {
        'buckwalter': 'rAy',
        'slug': 'rey_ruya_ray',
        'concept_name': 'Re\'y / Rüya (Görmek, Zihinsel İdrak, Göstermek ve Görüş)',
        'keywords': ['gör', 'göster', 'görmez', 'gördü', 'görü', 'görüş', 'rüya', 'rüyam', 'rüyayı', 'gösteriş', 'görün'],
    },
    'ك-ت-ب': {
        'buckwalter': 'ktb',
        'slug': 'kitap_ketb_ktb',
        'concept_name': 'Kitap / Ketb (Yazmak, Sabitlemek, Bağlayıcı Yasa ve Kayıt)',
        'keywords': ['kitap', 'kitab', 'yaz', 'yazıl', 'farz', 'mektup', 'katip', 'sicil', 'kütüb', 'mübin'],
    },
    'ه-د-ي': {
        'buckwalter': 'hdy',
        'slug': 'hidayet_hdy',
        'concept_name': 'Hidayet / Hedy (Zarafetle Yol Göstermek, Doğrultu Vermek ve Armağan Sunmak)',
        'keywords': ['doğru yol', 'yol göster', 'eriştir', 'kılavuz', 'rehber', 'hidayet', 'hediye', 'yakınlaşma sunu', 'yola', 'götür'],
    },
    'ظ-ل-م': {
        'buckwalter': 'Zlm',
        'slug': 'zulum_zulumat_zlm',
        'concept_name': 'Zulüm / Zulumât (Karanlık, Bir Şeyi Yerinden Etmek ve Haksızlık)',
        'keywords': ['haksız', 'zulm', 'zulüm', 'zalim', 'karanlık', 'yazık et', 'eksik bırak', 'karar'],
    },
    'ن-ف-س': {
        'buckwalter': 'nfs',
        'slug': 'can_benlik_nfs',
        'concept_name': 'Can / Benlik / Soluk (Kişilik, Öz, Hayat Nefesi ve Yarış)',
        'keywords': ['kendi', 'benli', 'can', 'kimse', 'kişi', 'öz', 'yarış', 'ağarma', 'soluk', 'nefes'],
    },
    'ن-ز-ل': {
        'buckwalter': 'nzl',
        'slug': 'nuzul_tenzil_nzl',
        'concept_name': 'Nüzûl / Tenzîl (Ölçülü İndirme, Kademeli Ulaştırma ve Konaklama İkramı)',
        'keywords': ['indir', 'inen', 'iner', 'yağ', 'konak', 'ikram', 'evre', 'sofra', 'demir', 'huzur'],
    },
    'ق-ب-ل': {
        'buckwalter': 'qbl',
        'slug': 'kabul_kible_qbl',
        'concept_name': 'Kabûl / Kıble / Kabile (Yüz Yüze Karşılama, Yönelim ve Öncelik)',
        'keywords': ['önce', 'yönel', 'kabul', 'karşı', 'yön', 'takat', 'kabile', 'boy', 'yüz yüze', 'ön', 'cephe'],
    },
    'ذ-ك-ر': {
        'buckwalter': '*kr',
        'slug': 'zikir_zekar_zkr',
        'concept_name': 'Zikir / Zekâr (Zihinde İz Tutma, Unutmama, Hatırlatma ve Eril Cinsiyet)',
        'keywords': ['hatır', 'an', 'düşün', 'öğüt', 'erkek', 'eril', 'unut', 'uyar', 'belge', 'bilinç'],
    },
    'ح-ق-ق': {
        'buckwalter': 'Hqq',
        'slug': 'hak_hakikat_hqq',
        'concept_name': 'Hak (Örtüşen Sağlam Gerçek, Sabit Ölçü, Hak Edilen Pay ve Borç)',
        'keywords': ['hak', 'gerçek', 'hakikat', 'doğru', 'pay', 'borç', 'layık', 'öncelik', 'kesin', 'haksız'],
    },
    'ك-ذ-ب': {
        'buckwalter': 'k*b',
        'slug': 'kizb_tekzib_kzb',
        'concept_name': 'Kizb / Tekzîb (Beklentiyi Boşa Çıkarma, Gerçeği Çarpıtma ve Kanıtı Yalanlama)',
        'keywords': ['yalan', 'yalanla', 'çarpıt', 'uydur', 'asılsız', 'sahte', 'boşa çık', 'reddet'],
    },
    'ج-ي-أ': {
        'buckwalter': 'jyA',
        'slug': 'meci_cye',
        'concept_name': 'Mecî\' (Ağırlıklı Varmak, Somut Sonuç Getirmek ve Geri Dönülmez Ortaya Çıkış)',
        'keywords': ['gel', 'geldi', 'varmak', 'getir', 'ulaş', 'çıkagel', 'kanıt', 'karşılık'],
    },
    'ع-ب-د': {
        'buckwalter': 'Ebd',
        'slug': 'ubudiyet_abd_ebd',
        'concept_name': 'Abd / Ubûdiyet (Düzlenmiş Yol Gibi Boyun Eğme, Emek Sunma ve Bilinçli Hizmet Bağlılığı)',
        'keywords': ['kulluk', 'kul', 'kullar', 'köle', 'tap', 'hizmet', 'boyun eğ'],
    },
    'أ-خ-ذ': {
        'buckwalter': 'Ax*',
        'slug': 'ahz_ittihaz_ehz',
        'concept_name': 'Ahz / İttihâz (Kavramak, Somut Yakalayış ve Kalıcı Olarak Edinmek)',
        'keywords': ['al', 'aldı', 'alın', 'yakala', 'tut', 'edin', 'hesaba çek', 'sorumlu'],
    },
    'خ-ل-ق': {
        'buckwalter': 'xlq',
        'slug': 'halk_hlk',
        'concept_name': 'Halk (Ölçüp Tasarlamak, Oranlı Biçim Vermek, Pay ve İç Karakter)',
        'keywords': ['yarat', 'tasarla', 'biçim', 'pay', 'karakter', 'uydur', 'ölçü', 'ahlak'],
    },
    'و-ق-ي': {
        'buckwalter': 'wqy',
        'slug': 'vikaye_ittika_wky',
        'concept_name': 'Vikâye / İttikâ (Kalkan Tutma, Zarardan Korunma ve Sorumluluk Bilinci)',
        'keywords': ['koru', 'korun', 'sakın', 'sorumluluk', 'kalkan', 'çekin', 'zırh'],
    },
    'أ-خ-ر': {
        'buckwalter': 'Axr',
        'slug': 'ahir_ahar_tehir_ehr',
        'concept_name': 'Âhir / Âhar / Te’hîr (Sonraki Aşama, Öteki Birim ve Geriye Bırakma)',
        'keywords': ['sonraki', 'sonra', 'diğer', 'öteki', 'başka', 'ertele', 'geriye', 'son'],
    },
    'أ-م-ر': {
        'buckwalter': 'Amr',
        'slug': 'emr_surec_emr',
        'concept_name': 'Emr (Yönlendirici İşaret, Karar, İşletim Düzeni ve Süreç)',
        'keywords': ['emir', 'emret', 'buyur', 'iş', 'işler', 'karar', 'yönlendir', 'danış', 'istişare'],
    },
    'ن-و-س': {
        'buckwalter': 'nws',
        'slug': 'nas_nws',
        'concept_name': 'Nâs (Hareketli İnsanlık Toplumu ve Kamuoyu)',
        'keywords': ['insan', 'insanlar', 'insanlık', 'halk', 'toplum', 'çoğunluk', 'kitle', 'kamuoyu'],
    },
    'غ-ف-ر': {
        'buckwalter': 'gfr',
        'slug': 'magfiret_gufran_gfr',
        'concept_name': 'Mağfiret / Gufrân (Miğfer Gibi Örtüp Zırhlama ve Kusurun Üstünü Kapatma)',
        'keywords': ['bağışla', 'mağfiret', 'örtsün', 'ört', 'koru', 'zırh', 'kusur', 'gafur', 'gaffar'],
    },
    'و-ل-ي': {
        'buckwalter': 'wly',
        'slug': 'velayet_tevelli_wly',
        'concept_name': 'Velâyet / Tevellî (Bitişik Yakınlık, Sahiplenip Üstlenme ve Sırt Çevirme)',
        'keywords': ['dost', 'yakın', 'yardımcı', 'koruyucu', 'veli', 'mevla', 'yüz çevir', 'dön', 'yönet', 'velayet', 'üstlen', 'sahiplen', 'en layık', 'öncelikli'],
    },
    'ب-ع-د': {
        'buckwalter': 'bEd',
        'slug': 'bud_bad_bed',
        'concept_name': 'Bu\'d / Ba\'d (Araya Giren Mesafe, Uzaklık, Ardından Gelme ve Tarihten Silinme)',
        'keywords': ['uzak', 'sonra', 'ardından', 'mesafe', 'uzaklaş', 'bunca', 'sonrası', 'aralık', 'yok ol', 'silin'],
    },
    'د-ع-و': {
        'buckwalter': 'dEw',
        'slug': 'davet_dua_dew',
        'concept_name': 'Da\'vet / Duâ (Seslenerek Kendine Çekme, Çağrı, Adlandırma ve Talep)',
        'keywords': ['çağır', 'davet', 'dua', 'yakar', 'seslen', 'iste', 'çağrı', 'adlandır', 'iddia', 'çığlık'],
    },
    'ح-ك-م': {
        'buckwalter': 'Hkm',
        'slug': 'hukum_hikmet_hkm',
        'concept_name': 'Hüküm / Hikmet (Gem Vurup Frenleme, Sağlamlaştırma, Ölçülü Karar ve Bilgelik)',
        'keywords': ['hüküm', 'hükmet', 'hikmet', 'hakim', 'hakem', 'kesin', 'sağlamlaştır', 'hükmeden', 'muhakeme', 'karar'],
    },
    'م-ل-ك': {
        'buckwalter': 'mlk',
        'slug': 'mulk_melik_mlk',
        'concept_name': 'Mülk / Melik / Kozmik Görev (Sağlam Tutup Hükümranlık Etme, Sahiplik ve Görevli Güçler)',
        'keywords': ['mülk', 'hükümran', 'sahip', 'kozmik görevli', 'hükümdar', 'yetki', 'gücü yet', 'elinizin altında', 'köle', 'nöbetçi'],
    },
    'ج-ن-ن': {
        'buckwalter': 'jnn',
        'slug': 'cennat_cann_cunun_jnn',
        'concept_name': 'Cennât / Cânn / Cünûn (Örtüp Gizleme, Sık Esenlik Bahçesi, Görünmeyen Bilinç ve Zihin Örtülmesi)',
        'keywords': ['bahçe', 'bağ', 'esenlik bahç', 'görünmeyen', 'aklı örtül', 'akıl tutul', 'deli', 'kalkan', 'gece', 'cenin', 'yılan', 'sarmaş dolaş'],
    },
    'خ-ي-ر': {
        'buckwalter': 'xyr',
        'slug': 'hayr_ihtiyar_xyr',
        'concept_name': 'Hayr / İhtiyâr (Seçkin İyi, Faydalı Değer-Mal ve Bilinçli Seçim)',
        'keywords': ['hayır', 'hayırlı', 'iyi', 'seç', 'seçkin', 'mal', 'yararlı', 'üstün', 'fayda', 'bolluk', 'iyilik'],
    },
    'ع-ن-د': {
        'buckwalter': 'End',
        'slug': 'ind_anid_end',
        'concept_name': 'İnd / Anîd (Bitişik Yan, Kaynak Katı, Huzur ve Hizadan Sapıp Direnme)',
        'keywords': ['katınd', 'yanınd', 'yanın', 'yanı', 'nezd', 'huzur', 'elinde', 'elimde', 'inat', 'bende', 'sizde', 'bizde', 'taraf'],
    },
    'ن-و-ر': {
        'buckwalter': 'nwr',
        'slug': 'nur_nar_munir_nwr',
        'concept_name': 'Nûr / Nâr / Münîr (Berrak Aydınlık, Yakıcı Ateş ve Yol Açıcı Işık)',
        'keywords': ['aydınl', 'ışık', 'ışığ', 'nur', 'ateş', 'alev', 'kor', 'yakıt', 'tutuştur', 'karanlık', 'serin', 'yakıcı'],
    },
    'ح-س-ن': {
        'buckwalter': 'Hsn',
        'slug': 'husn_ihsan_ahsen_Hsn',
        'concept_name': 'Hüsn / İhsân / Ahsen (Sağlam Uyum, Ölçülü Güzellik ve İşi Özenle Tam Yapma)',
        'keywords': ['güzel', 'iyilik', 'iyi', 'ihsan', 'özen', 'kusursuz', 'uyum', 'örnek', 'karşılık', 'en güzel', 'en iyi'],
    },
    'ض-ل-ل': {
        'buckwalter': 'Dll',
        'slug': 'dalalet_tadlil_dll',
        'concept_name': 'Dalâlet / Tadlîl (Pusula Kaybı, İz Silinmesi ve Doğru Yoldan Şaşma)',
        'keywords': ['sap', 'şaş', 'kayb', 'boşa', 'yitir', 'yol', 'şaşkın', 'eriyip', 'karış', 'şaşır'],
    },
    'س-م-ع': {
        'buckwalter': 'smE',
        'slug': 'sem_istima_sme',
        'concept_name': 'Sem\' / İstima\' (Ses Yakalama, Dikkatle Kulak Verme ve Yanıtla İçselleştirme)',
        'keywords': ['işit', 'duy', 'dinle', 'kulak', 'sağır', 'ses', 'fısıltı', 'casusluk', 'algıla', 'karşılık'],
    },
    'ب-ن-ي': {
        'buckwalter': 'bny',
        'slug': 'bina_ibn_bny',
        'concept_name': 'Binâ / İbn (Taş Taş Örüp Yapı Kurmak, Soy Ve Aidiyet İnşası)',
        'keywords': ['bina', 'yapı', 'inşa', 'kur', 'oğul', 'oğullar', 'kız', 'yavru', 'yolcu', 'evlat'],
    },
    'ح-ي-ي': {
        'buckwalter': 'Hyy',
        'slug': 'hayat_hayy_hyy',
        'concept_name': 'Hayat / Hayy / İhyâ / İstihyâ (Canlılık, İşlevsel Dirilik, Sağ Bırakma ve Hassas Sakınma)',
        'keywords': ['hayat', 'yaşa', 'diri', 'canlı', 'dirilt', 'sağ bırak', 'çekin', 'sakın', 'selam', 'esenlik', 'yılan', 'ölü'],
    },
    'خ-ر-ج': {
        'buckwalter': 'xrj',
        'slug': 'huruc_ihrac_xrj',
        'concept_name': 'Hurûc / İhrâc / İstihrâc (Kapalı Sınırı Yarıp Dışarı Çıkmak, Açığa Çıkarmak ve Sürgün)',
        'keywords': ['çık', 'çıkar', 'sürgün', 'kov', 'bitki', 'ürün', 'vergi', 'ücret', 'açığa', 'aydınlık', 'kurtuluş'],
    },
    'ص-ل-ح': {
        'buckwalter': 'SlH',
        'slug': 'salah_islah_slh',
        'concept_name': 'Salâh / İslâh / Sâlihât / Sulh (Bozulmayı Giderip İşlevsel Dengeye Getirmek, Onarmak ve Barışı Kurmak)',
        'keywords': ['ıslah', 'onar', 'düzelt', 'barış', 'uzlaş', 'yararlı', 'uyumlu', 'salih', 'bozguncu', 'dirlik'],
    },
    'س-ب-ل': {
        'buckwalter': 'sbl',
        'slug': 'sebil_subul_sbl',
        'concept_name': 'Sebîl / Sübül (Engelsiz İşlek Akış, Geçiş Yolu, Yöntem ve Sorumluluk Kapısı)',
        'keywords': ['yol', 'sebil', 'yolcu', 'yolda kal', 'yöntem', 'güzergah', 'geçit', 'imkan', 'çıkış', 'sap', 'alıkoy'],
    },
    'ت-ب-ع': {
        'buckwalter': 'tbE',
        'slug': 'ittiba_teba_tbe',
        'concept_name': 'İttibâ\' / Teba\' / İtbâ\' (Adım Adım İz Sürmek, Peşinden Yetişip Takip Etmek ve Örnek Almak)',
        'keywords': ['uy', 'tâbi', 'peş', 'iz', 'takip', 'kovala', 'ard', 'ardışık', 'yetiş', 'kat', 'ekle'],
    },
    'أ-و-ل': {
        'buckwalter': 'Awl',
        'slug': 'evvel_al_tevil_awl',
        'concept_name': 'Evvel / Âl / Ülî / Te\'vîl (Başlangıç Kaynağı, Dönüp Bağlanan Yakın Çevre, Nitelik Sahipleri ve Asıl Sonuç)',
        'keywords': ['ilk', 'önce', 'evvel', 'eski', 'sahip', 'akıl', 'kavrayış', 'hanedan', 'yakın', 'sonuç', 'rüya', 'tevil', 'yorum'],
    },
    'ق-ت-ل': {
        'buckwalter': 'qtl',
        'slug': 'katl_kital_qtl',
        'concept_name': 'Katl / Kıtâl / Taktîl / İktitâl (Can Bağını Kesip Etkisizleştirme, Karşılıklı Çarpışma ve İç Çatışma)',
        'keywords': ['öldür', 'savaş', 'çarpış', 'katl', 'kısas', 'can', 'etkisiz', 'lanet', 'çatış'],
    },
    'م-ث-ل': {
        'buckwalter': 'mvl',
        'slug': 'mesel_misil_mvl',
        'concept_name': 'Mesel / Misil / Timsâl / Temessül (Karşılıklı Denk Model, Eşdeğer Ölçü, Örnek Tablo ve Surete Bürünme)',
        'keywords': ['örnek', 'benzer', 'gibi', 'misil', 'denk', 'temsil', 'heykel', 'ibret', 'bürün', 'kat'],
    },
    'ق-ل-ب': {
        'buckwalter': 'qlb',
        'slug': 'kalp_inkilab_qlb',
        'concept_name': 'Kalp / Taklîb / İnkılâb (Merkez Öz, Bilişsel Dönüşüm Odası ve Tersine Çevrilip Dönüş)',
        'keywords': ['kalp', 'gönül', 'yürek', 'dön', 'çevir', 'devir', 'inkılap', 'değiş', 'döndür', 'katı'],
    },
    'ش-ر-ك': {
        'buckwalter': '$rk',
        'slug': 'serik_istirak_srk',
        'concept_name': 'Şerîk / İştirâk / Ortak Koşma (Yetki Bölüşümü, Paydaş Edinme ve Bir İşe Ortak Kılma)',
        'keywords': ['ortak', 'pay', 'bölüş', 'yetki', 'paydaş', 'katıl', 'birlik', 'teklik', 'eş'],
    },
    'ك-ث-ر': {
        'buckwalter': 'kvr',
        'slug': 'kesret_kevser_kvr',
        'concept_name': 'Kesret / Ekser / Tekâsür / Kevser (Sayısal Çokluk, Yığılma Yarışı ve Taşkın Hayır Kaynağı)',
        'keywords': ['çok', 'çoğul', 'fazla', 'ekser', 'çoğunluk', 'bol', 'yığ', 'yarış', 'bereket', 'az'],
    },
    'س-و-أ': {
        'buckwalter': 'swA',
        'slug': 'su_seyyie_swa',
        'concept_name': 'Sû\' / Seyyie / Sev\'e / İsâe (Çirkinlik, Keder Veren Bozukluk, Zarar ve Kusur)',
        'keywords': ['çirkin', 'kötü', 'zarar', 'bozuk', 'keder', 'üzüntü', 'ayıp', 'kusur', 'karşılık', 'ört'],
    },
    'م-و-ت': {
        'buckwalter': 'mwt',
        'slug': 'mevt_memat_mwt',
        'concept_name': 'Mevt / Memât / Meyyit / İmâte (Güç ve İşlevin Çekilmesi, Durağanlaşma ve Evre Değişimi)',
        'keywords': ['ölüm', 'ölü', 'ölmek', 'diril', 'hareketsiz', 'fonksiyon', 'can', 'toprak', 'hayat', 'evre'],
    },
    'ك-ب-ر': {
        'buckwalter': 'kbr',
        'slug': 'kibr_kebir_kbr',
        'concept_name': 'Kibr / Kebîr / Ekber / İstikbâr (Büyüklük, İleri Yaş ve Haksız Büyüklenme)',
        'keywords': ['büyük', 'yüce', 'kibir', 'büyüklen', 'yaşlı', 'ağır', 'en büyük', 'ululuk', 'küçük', 'tasla'],
    },
    'ش-ه-د': {
        'buckwalter': '$hd',
        'slug': 'sehadet_sahid_shd',
        'concept_name': 'Şehâdet / Şâhid / Şehîd / Meşhûd (Yerinde Hazır Bulunuş, Açık Gözlem ve Sorumlu Tanıklık)',
        'keywords': ['tanık', 'şahit', 'gözlem', 'hazır', 'belge', 'açık', 'gizli', 'kanıt', 'beyan', 'bildir'],
    },
    'ن-ب-أ': {
        'buckwalter': 'nbA',
        'slug': 'nebe_nebi_nba',
        'concept_name': 'Nebe\' / Nebî / Nübüvvet / İnbâ (Büyük Haber, Geçmişten Geleceğe Bilgi Aktarma ve Haber Elçiliği)',
        'keywords': ['haber', 'nebi', 'bildir', 'vahiy', 'elçi', 'büyük', 'gayb', 'doğrula', 'sor', 'aktar'],
    },
    'ب-ع-ض': {
        'buckwalter': 'bED',
        'slug': 'baz_parca_bed',
        'concept_name': 'Ba\'z / Ba\'ûda (Bütünden Ayrılan Parça, Karşılıklı Bağlantı ve Sivrisinek)',
        'keywords': ['parça', 'kısım', 'bazı', 'birbir', 'bölüm', 'derece', 'sivrisinek', 'bütün', 'seçme', 'katman'],
    },
    'ن-ص-ر': {
        'buckwalter': 'nSr',
        'slug': 'nasr_intisar_nsr',
        'concept_name': 'Nasr / Nasîr / Ensâr / İntisâr / Nasârâ (Hayır ve Güç Ulaştırma, Aktif Destek ve Haklı Savunma)',
        'keywords': ['yardım', 'destek', 'zafer', 'koru', 'yardımcı', 'savun', 'ensar', 'nasara', 'üstün', 'galip'],
    },
    'ص-د-ق': {
        'buckwalter': 'Sdq',
        'slug': 'sidk_sadaka_sdk',
        'concept_name': 'Sıdk / Sadâkat / Sadaka / Tasdik (Sağlamlık, Söz-Eylem Örtüşmesi, Doğrulama ve Özden Paylaşım)',
        'keywords': ['doğru', 'gerçek', 'sadık', 'tasdik', 'doğrula', 'sadaka', 'bağış', 'söz', 'vaat', 'dost'],
    },
    'غ-ي-ر': {
        'buckwalter': 'gyr',
        'slug': 'gayr_tagyir_gyr',
        'concept_name': 'Gayr / Tağyîr / Muğîrât (Sınır Çizen Başkalık, Nitelik Değişimi ve Öz-Eksen Dönüşüm)',
        'keywords': ['başka', 'dışında', 'değiştir', 'olmayan', 'bozul', 'aksine', 'farklı', 'hesapsız', 'haksız'],
    },
    'و-ع-د': {
        'buckwalter': 'wEd',
        'slug': 'vad_vaid_wed',
        'concept_name': 'Va\'d / Vaîd / Mevid / Mîâd (Geleceğe Bağlayıcı Söz-Hedef Kurma, Belirlenmiş Vade ve Yaptırım Uyarısı)',
        'keywords': ['söz', 'vadet', 'vaded', 'vade', 'tehdit', 'buluşma', 'sözleş', 'tayin', 'cayma', 'vakit'],
    },
    'ب-ص-ر': {
        'buckwalter': 'bSr',
        'slug': 'basar_basiret_bsr',
        'concept_name': 'Basar / Basîret / İbsâr (Seçik Görme, Ayırt Edici İçgörü ve Kanıtla Fark Etme)',
        'keywords': ['gör', 'göz', 'göster', 'gözetle', 'gören', 'aydınlık', 'belge', 'anlayış', 'şahit', 'bilerek'],
    },
    'ر-و-د': {
        'buckwalter': 'rwd',
        'slug': 'irade_muravede_rwd',
        'concept_name': 'İrâde / Murâvede / Ruveyd (Hedefe Yönelme, Meyletme, Çekerek Döndürmeye Çalışma ve Yumuşak Mühlet)',
        'keywords': ['iste', 'dile', 'murad', 'meyl', 'yüz tut', 'yönel', 'ikna', 'çağır', 'mühlet', 'geri bırak'],
    },
    'ل-ق-ي': {
        'buckwalter': 'lqy',
        'slug': 'lika_ilka_lqy',
        'concept_name': 'Likā / İlkā / Telakkî / İltikā (Karşılaşma-Yüzleşme ve Önüne Bırakıp Ulaştırma)',
        'keywords': ['karşılaş', 'kavuş', 'rastla', 'buluş', 'at', 'bırak', 'sal', 'koy', 'yön', 'al'],
    },
    'د-و-ن': {
        'buckwalter': 'dwn',
        'slug': 'dun_berisi_dwn',
        'concept_name': 'Dûn (Üst Sınırın Berisinde ve Altında Kalan, İkincil veya Dışındaki Konum)',
        'keywords': ['başka', 'bırakıp', 'aşağı', 'berisi', 'altında', 'dışında', 'hafif', 'önce', 'ötesinde'],
    },
    'ن-ع-م': {
        'buckwalter': 'nEm',
        'slug': 'nimet_naim_nem',
        'concept_name': 'Nimet / Naîm (Yumuşak Refah, Hoşluk ve İyilik Bahşı)',
        'keywords': ['nimet', 'iyilik', 'lütuf', 'rahatlık', 'refah', 'hoş', 'hayvan', 'ne güzel', 'pırıl'],
    },
    'س-ل-م': {
        'buckwalter': 'slm',
        'slug': 'selam_teslimiyet_slm',
        'concept_name': 'Selâm / Teslimiyet / Bütünlük (Kusurdan Arınma, Güvenlik, Barış ve İçten Adanma)',
        'keywords': ['esenlik', 'barış', 'selam', 'teslim', 'sağlam', 'kusursuz', 'merdiven', 'bütün'],
    },
    'د-ن-و': {
        'buckwalter': 'dnw',
        'slug': 'dunya_edna_dnw',
        'concept_name': 'Dünyâ / Dünuv (Yakınlaşan, Mesafece ve Zamanca En Yakın İlk Aşama)',
        'keywords': ['yakın', 'dünya', 'yaklaş', 'sark', 'salkım', 'yakınlık', 'yamaç', 'ilk aşama'],
    },
    'ق-د-ر': {
        'buckwalter': 'qdr',
        'slug': 'kader_kudret_qdr',
        'concept_name': 'Kader / Kudret / Miktar (Ölçü Belirleme, Orantılı Planlama, Kapasite ve Güç)',
        'keywords': ['ölçü', 'miktar', 'kader', 'güç', 'gücü yet', 'daralt', 'ölç', 'kazan', 'değer'],
    },
    'ن-ذ-ر': {
        'buckwalter': 'n*r',
        'slug': 'nezr_inzar_nzar',
        'concept_name': 'Nezr / İnzâr (Tehlikeyi Önceden Bildirerek Uyarma ve Bağlayıcı Adak Sorumluluğu)',
        'keywords': ['uyar', 'uyarıcı', 'adak', 'ada', 'korkut', 'tehlike', 'sorumluluk', 'önceden haber'],
    },
    'ج-م-ع': {
        'buckwalter': 'jmE',
        'slug': 'cem_cemi_jme',
        'concept_name': 'Cem\' / Cemî / İcmâ (Dağınık Parçaları Bir Araya Toplama, Birlik ve Kesin Bütünlük)',
        'keywords': ['topla', 'bir araya', 'bütün', 'hepsi', 'topluluk', 'toplanma', 'kavuşma', 'birik'],
    },
    'ن-ظ-ر': {
        'buckwalter': 'nZr',
        'slug': 'nazar_intizar_nzr',
        'concept_name': 'Nazar / İntizâr (Dikkatle Bakıp İnceleme, Gözetleme ve Süre/Mühlet Tanıma)',
        'keywords': ['bak', 'gözle', 'incele', 'mühlet', 'süre', 'bekle', 'gözet', 'tanık'],
    },
    'س-أ-ل': {
        'buckwalter': 'sAl',
        'slug': 'sual_mesuliyet_sal',
        'concept_name': 'Suâl / Mes\'ûliyet (Bilgi Öğrenmek İçin Sormak, İhtiyaç Talep Etmek ve Hesap Sorumluluğu)',
        'keywords': ['sor', 'iste', 'talep', 'sorumluluk', 'hesap', 'sorgu', 'ihtiyaç sahibi', 'araştır'],
    },
    'ط-و-ع': {
        'buckwalter': 'TwE',
        'slug': 'tav_itaat_twe',
        'concept_name': 'Tav\' / Tâat / İstitâat (Zorlanmadan Gönüllü Uyum, İçten Adanma ve İmkan-Güç Yetişi)',
        'keywords': ['gönüllü', 'iste', 'uymak', 'itaat', 'gücü yet', 'imkan', 'uyum', 'kolaylaştır'],
    },
    'ع-ظ-م': {
        'buckwalter': 'EZm',
        'slug': 'azim_kemik_ezm',
        'concept_name': 'Azîm / Azm / Ta\'zîm (Kemik Gibi Sarsılmaz Yapısal Sağlamlık, Büyüklük ve Yüceltme)',
        'keywords': ['büyük', 'yüce', 'muazzam', 'kemik', 'kemikler', 'ağır', 'en büyük', 'yücelt'],
    },
    'خ-ل-ف': {
        'buckwalter': 'xlf',
        'slug': 'hilafet_ihtilaf_xlf',
        'concept_name': 'Hilâfet / İhtilâf / Halef (Arkasından Gelip Yerini Alma, Çeşitlenme ve Ters Düşme)',
        'keywords': ['arka', 'sonra', 'yerini al', 'farklı', 'ayrıl', 'halef', 'cay', 'geri kal'],
    },
    'أ-ه-ل': {
        'buckwalter': 'Ahl',
        'slug': 'ehl_ehliyet_ahl',
        'concept_name': 'Ehl / Ehliyet (Aynı Otağ-Evi Paylaşan Aile, Yerleşim Halkı ve İlkeye Lâyık/Mensup Olanlar)',
        'keywords': ['aile', 'ev halkı', 'halk', 'mensup', 'ehil', 'layık', 'sahip', 'yakın'],
    },
    'د-خ-ل': {
        'buckwalter': 'dxl',
        'slug': 'duhul_mudhal_dxl',
        'concept_name': 'Duhûl / Müdhal / Dehâl (İçeri Girme, Sığınak Kovuğu ve Gizli İç Çürüme)',
        'keywords': ['gir', 'giriş', 'içeri', 'içine', 'kovuk', 'bozgun', 'sokul', 'katıl'],
    },
    'خ-و-ف': {
        'buckwalter': 'xwf',
        'slug': 'havf_hife_xwf',
        'concept_name': 'Havf / Hîfe / Tehavvüf (Tehlike Beklentisinden Doğan Ürküntü, İç Çekince ve Kenardan Azaltma)',
        'keywords': ['kork', 'ürper', 'çekin', 'endişe', 'korkut', 'güven', 'eksilt', 'ürk'],
    },
    'ر-ز-ق': {
        'buckwalter': 'rzq',
        'slug': 'rizik_rezzak_rzq',
        'concept_name': 'Rızık / Rezzâk (Zamanlı Tahsisat, Yaşam Payı ve Sürdürülebilir Geçim Kaynağı)',
        'keywords': ['rızık', 'rızıklandır', 'geçim', 'nasip', 'pay', 'tayın', 'besle', 'nimet'],
    },
    'ب-ش-ر': {
        'buckwalter': 'b$r',
        'slug': 'beser_bisaret_bsr',
        'concept_name': 'Beşer / Bişâret / Mübâşeret (Dış Deri/Ten, Ölümlü İnsan ve Yüzü Parlatan Müjde)',
        'keywords': ['beşer', 'insan', 'müjde', 'müjdele', 'sevin', 'ten', 'yakınlaş', 'müjdeci'],
    },
    'ي-د-ي': {
        'buckwalter': 'ydy',
        'slug': 'yed_eydi_ydy',
        'concept_name': 'Yed / Eydî (Organ Olarak El, Yetki Tasarrufu ve Ön-Zaman Yönelimi)',
        'keywords': ['el', 'elleri', 'iki el', 'yetki', 'güç', 'önü', 'cömert', 'tasarruf'],
    },
    'أ-م-م': {
        'buckwalter': 'Amm',
        'slug': 'umm_ummet_imam_amm',
        'concept_name': 'Ümm / Ümmet / İmâm (Yönelinen Ana Kaynak, Anne, Ortak Yönlü Topluluk ve Öncü)',
        'keywords': ['anne', 'ana', 'kaynak', 'topluluk', 'ümmet', 'önder', 'imam', 'süre'],
    },
    'ع-ز-ز': {
        'buckwalter': 'Ezz',
        'slug': 'izzet_aziz_ezz',
        'concept_name': 'İzzet / Azîz (Sarsılmaz Sağlamlık, Yenilmez Üstünlük ve Eşsiz Değerlilik)',
        'keywords': ['aziz', 'izzet', 'onur', 'üstün', 'yenilmez', 'güç', 'sağlam', 'baskın'],
    },
    'ج-ز-ي': {
        'buckwalter': 'jzy',
        'slug': 'ceza_mucazat_jzy',
        'concept_name': 'Cezâ / Mücâzât (Yerine Geçip Kefil Olma, Birebir Denklik ve Eylem Karşılığı)',
        'keywords': ['karşılık', 'ceza', 'ödül', 'bedel', 'kefil', 'denk', 'cizye', 'öde'],
    },
    'أ-ب-و': {
        'buckwalter': 'Abw',
        'slug': 'eb_ebeveyn_aba_abw',
        'concept_name': 'Eb / Ebevân / Âbâ (Baba, Anne-Baba Birliği, Atalar ve Taklit-Soy Hukuku)',
        'keywords': ['baba', 'atalar', 'anne-baba', 'babacığım', 'soy', 'nesil', 'miras', 'kök'],
    },
    'ن-ه-ر': {
        'buckwalter': 'nhr',
        'slug': 'nehir_nehar_nhr',
        'concept_name': 'Nehir / Nehâr (Yatağı Yarıp Akma, Aydınlık Gündüz ve Taşkınca Azarlama)',
        'keywords': ['nehir', 'ırmak', 'gündüz', 'aydınlık', 'azarla', 'tersle', 'akıntı', 'gece'],
    },
    'أ-ك-ل': {
        'buckwalter': 'Akl',
        'slug': 'ekl_ukul_akl',
        'concept_name': 'Ekl / Ükül (Parça Parça Eksiltip Tüketme, Beslenme ve Verim Alma)',
        'keywords': ['ye', 'yer', 'yiy', 'yemek', 'yemiş', 'tüket', 'ürün', 'otla', 'kemir', 'meyve'],
    },
    'ح-س-ب': {
        'buckwalter': 'Hsb',
        'slug': 'hesap_hisab_hasb_hsb',
        'concept_name': 'Hesap / Hasb / Hisâb (Sayma, Muhasebe, Tek Taraflı Sanı ve Tam Yetme)',
        'keywords': ['hesap', 'hesab', 'san', 'zann', 'say', 'yeter', 'yetiş', 'kafi', 'bekle'],
    },
    'ف-ع-ل': {
        'buckwalter': 'fEl',
        'slug': 'fiil_fail_meful_fel',
        'concept_name': 'Fiil / Fâil / Mef’ûl (Etki Ortaya Koyma ve Olguya Dönüştürme)',
        'keywords': ['yap', 'yaptı', 'et', 'etti', 'iş', 'işle', 'eylem', 'olgu', 'yerine getir', 'gerçekleş'],
    },
    'أ-ج-ر': {
        'buckwalter': 'Ajr',
        'slug': 'ecir_ucret_ujur_ejr',
        'concept_name': 'Ecir / Ücret (Emeği ve Eksikliği Onaran Hak Edilmiş Denk Bedel)',
        'keywords': ['ecir', 'ücret', 'mükafat', 'karşılık', 'mehir', 'öde', 'çalış', 'tut'],
    },
    'و-ج-د': {
        'buckwalter': 'wjd',
        'slug': 'vucud_vicdan_vucd_wjd',
        'concept_name': 'Vecd / Vücd / Bulmak (Deneyimsel Tespit ve Eldeki İmkân Genişliği)',
        'keywords': ['bul', 'buldu', 'bulur', 'rastla', 'gör', 'hisset', 'koku', 'imkan', 'güç'],
    },
    'ع-د-و': {
        'buckwalter': 'Edw',
        'slug': 'udvan_aduv_adavat_edw',
        'concept_name': 'Adv / Udvân / Adûv (Sınırı Aşıp Öte Yakaya Geçmek ve Karşıt Saflaşma)',
        'keywords': ['düşman', 'aşırı', 'haddi aş', 'taşkın', 'tecavüz', 'saldır', 'koş', 'yamaç', 'uzaklaş'],
    },
    'ر-ج-ع': {
        'buckwalter': 'rjE',
        'slug': 'rucu_merci_rec_rje',
        'concept_name': 'Rec / Rücû / Merci (Çıkış Kaynağına ve Hesap Merciine Geri Dönüş)',
        'keywords': ['dön', 'döner', 'döndür', 'çevir', 'iade', 'dönüş', 'merci', 'cevap'],
    },
    'ف-ض-ل': {
        'buckwalter': 'fDl',
        'slug': 'fadl_tefdil_tefaddul_fdl',
        'concept_name': 'Fadl / Tefdîl (Taban Ölçüyü Aşan Artı Pay, İşlevsel Ayrışma ve İhsân)',
        'keywords': ['lütuf', 'bol', 'artır', 'üstün', 'farklı', 'rızık', 'iyilik', 'fazla'],
    },
    'ص-ب-ر': {
        'buckwalter': 'Sbr',
        'slug': 'sebat_direnc_istibar_sbr',
        'concept_name': 'Sebat / Direnç / Istibâr (Benliği Hedefe Kenetleyip Sarsılmadan Tutma)',
        'keywords': ['sebat', 'diren', 'direnç', 'dayan', 'katlan', 'sabit', 'tut'],
    },
    'أ-ذ-ن': {
        'buckwalter': 'A*n',
        'slug': 'izn_uzn_ezan_istizan_azn',
        'concept_name': 'İzin / Üzün / Ezân (Kulak, İşitip Onaylama, Duyuru ve Yetki Kanalı)',
        'keywords': ['izin', 'kulak', 'duyur', 'ilan', 'çağır', 'izin iste', 'dinle', 'onay'],
    },
    'ش-د-د': {
        'buckwalter': '$dd',
        'slug': 'sedid_esedd_esudd_sdd',
        'concept_name': 'Şedd / Şedîd / Eşudd (Sımsıkı Bağlama, Yapısal Sağlamlık ve Baskı Yoğunluğu)',
        'keywords': ['şiddet', 'çetin', 'sert', 'sağlam', 'kuvvet', 'pekiştir', 'bağla', 'ergin', 'olgun', 'zor'],
    },
    'و-ل-د': {
        'buckwalter': 'wld',
        'slug': 'veled_valid_mevlud_vildan_wld',
        'concept_name': 'Veled / Vâlid / Mevlûd / Vildân (Doğurma, Doğurulma ve Soy-Bakım Sorumluluğu)',
        'keywords': ['doğur', 'doğan', 'doğum', 'çocuk', 'evlat', 'evlât', 'anne', 'baba', 'soy', 'nesil'],
    },
    'د-ي-ن': {
        'buckwalter': 'dyn',
        'slug': 'deyn_diyn_medinin_dyn',
        'concept_name': 'Dîn / Deyn / Medînîn (Boyun Eğme, Borç-Karşılık Bağı ve Hesap Düzeni)',
        'keywords': ['borç', 'hesap', 'yargı', 'karşılık', 'yasa', 'itaat', 'boyun eğ', 'sistem', 'düzen', 'öde'],
    },
    'ص-ح-ب': {
        'buckwalter': 'SHb',
        'slug': 'ashab_sahib_sahibe_shb',
        'concept_name': 'Ashâb / Sâhib / Sâhibe (Yan Yanalık, Yol Arkadaşlığı ve Sürekli Birliktelik)',
        'keywords': ['arkadaş', 'yoldaş', 'ehil', 'sahip', 'eş', 'beraber', 'yakın', 'yan', 'topluluk', 'koru'],
    },
    'أ-ن-س': {
        'buckwalter': 'Ans',
        'slug': 'insan_ins_inas_uns_ans',
        'concept_name': 'İns / İnsân / Înâs / Üns (Açık Algılanma, Yabancılığı Kırma ve Sosyal Ünsiyet)',
        'keywords': ['insan', 'ün', 'ünsiyet', 'gör', 'sez', 'yakınlık', 'izin', 'sohbet', 'topluluk', 'görünür'],
    },
    'ق-ر-ب': {
        'buckwalter': 'qrb',
        'slug': 'karib_akrab_kurba_mukarrab_qrb',
        'concept_name': 'Karîb / Akrab / Kurbâ / Mukarrab (Yakınlaşma, Mesafe Kapatma ve Sunu-Soy Bağı)',
        'keywords': ['yakın', 'yaklaş', 'akraba', 'hısım', 'sunu', 'yakınlık', 'mesafe', 'komşu', 'seçkin', 'sınır'],
    },
    'ب-غ-ي': {
        'buckwalter': 'bgy',
        'slug': 'bagy_ibtiga_yanbagi_bgy',
        'concept_name': 'Bagy / İbtigâ / Yenbağî (Şiddetle Aramak, Yaraşmak ve Sınırı Taşıp Saldırmak)',
        'keywords': ['ara', 'iste', 'taşkın', 'azgın', 'saldır', 'yaraş', 'uygun', 'hedef', 'iffet', 'sınır'],
    },
    'أ-خ-و': {
        'buckwalter': 'Axw',
        'slug': 'ah_uht_ihvet_ihvan_axw',
        'concept_name': 'Eh / Uht / İhve / İhvân (Ortak Kaynak, Omuzdaşlık ve Eşdeğer Kardeşlik)',
        'keywords': ['kardeş', 'kız kardeş', 'omuzdaş', 'ortak', 'akraba', 'soydaş', 'eşdeğer', 'miras', 'barış', 'dayanışma'],
    },
    'ح-ب-ب': {
        'buckwalter': 'Hbb',
        'slug': 'hubb_habb_habbe_istihbab_hbb',
        'concept_name': 'Hubb / Habb / Habbe / İstihbâb (Özde Sabitlenen Bağ, Tohum Çekirdeği ve Değer Tercihi)',
        'keywords': ['sev', 'sevgi', 'tohum', 'tane', 'çekirdek', 'tercih', 'bağlan', 'seç', 'gönül', 'arzula'],
    },
    'س-ب-ح': {
        'buckwalter': 'sbH',
        'slug': 'sebh_tesbih_subhan_sbh',
        'concept_name': 'Sebh / Tesbîh / Sübhân (Engin Akışta Yörüngede Yüzme ve Kusursuz Aşkınlığa Uzaklaştırma)',
        'keywords': ['yüz', 'akış', 'yörünge', 'aşkın', 'uzak', 'arındır', 'tesbih', 'sübhan', 'dön', 'sürat'],
    },
    'ل-ي-ل': {
        'buckwalter': 'lyl',
        'slug': 'leyl_leyle_leyali_lyl',
        'concept_name': 'Leyl / Leyle / Leyâlî (Karanlık Örtü, Sükûnet Kuşağı ve Sayılı Vahiy Gecesi)',
        'keywords': ['gece', 'karanlık', 'örtü', 'sükûnet', 'dinlen', 'geceler', 'kadir', 'vakit', 'uyku', 'kuşak'],
    },
    'ل-ي-س': {
        'buckwalter': 'lys',
        'slug': 'leyse_leste_lestum_lys',
        'concept_name': 'Leyse / Leste / Lestüm (Varlık-Nispet Olumsuzlaması, Muafiyet ve Kesin İkrar)',
        'keywords': ['değil', 'yok', 'muaf', 'sorumluluk', 'bilgi', 'benzer', 'zulüm', 'imkân', 'dayanak'],
    },
    'ش-ط-ن': {
        'buckwalter': '$Tn',
        'slug': 'setn_setan_setatin_stn',
        'concept_name': 'Şetn / Şetân / Şeyâtîn (Haktan Uzaklaşıp Bozan Taşkın Saptırıcı Güç)',
        'keywords': ['uzak', 'saptır', 'yıkıcı', 'vesvese', 'düşman', 'aldat', 'dürt', 'sığın', 'azgın'],
    },
    'ق-ر-أ': {
        'buckwalter': 'qrA',
        'slug': 'kuran_karee_kuru_qra',
        'concept_name': 'Kur’an / Karae / Kurû’ (Dağınık Olanı Toplayıp Bütünleme, Okuma ve Döngüsel Birikim)',
        'keywords': ['oku', 'kuran', 'topla', 'derle', 'bütün', 'düşün', 'dinle', 'döngü', 'kitap'],
    },
    'خ-ل-د': {
        'buckwalter': 'xld',
        'slug': 'huld_halid_ahlade_xld',
        'concept_name': 'Huld / Hâlid / Ahlede (Bozulmadan Sabit Kalıcılık, Yerleşme ve Yere Yapışma)',
        'keywords': ['kalıcı', 'temelli', 'sonsuz', 'kal', 'yerleş', 'yapış', 'ölümsüz', 'sürekli', 'taze'],
    },
    'ت-و-ب': {
        'buckwalter': 'twb',
        'slug': 'tevbe_tawwab_metab_twb',
        'concept_name': 'Tevbe / Tevvâb / Metâb (Yanlış İstikametten Bilinçle Geri Dönüş ve İlâhî Rahmet Kabulü)',
        'keywords': ['dön', 'dönüş', 'tevbe', 'tövbe', 'onar', 'bağışla', 'kabul', 'yönel', 'merhamet'],
    },
    'م-و-ل': {
        'buckwalter': 'mwl',
        'slug': 'mal_emval_mwl',
        'concept_name': 'Mâl / Emvâl (Emanet Edilmiş Taşınabilir Varlık, Toplumsal Hak Ölçüsü ve Geçici Dünya Sınavı)',
        'keywords': ['mal', 'mallar', 'mülk', 'servet', 'sermaye', 'varlık', 'harca', 'infak', 'yetim', 'kazan'],
    },
    'أ-ح-د': {
        'buckwalter': 'AHd',
        'slug': 'ehad_ihda_ahd',
        'concept_name': 'Ehad / İhdâ (Bölünmez Mutlak Teklik, İkiden Biri ve İstisnasız Her Tek Fert)',
        'keywords': ['bir', 'tek', 'biri', 'birini', 'kimse', 'hiç', 'hiçbir', 'herhangi', 'ortak'],
    },
    'ن-ج-و': {
        'buckwalter': 'njw',
        'slug': 'necat_necva_njw',
        'concept_name': 'Necât / Necvâ (Kuşatmadan Yüksek Selamete Çekip Kurtarma ve Tenhaya Çekilip Gizlice Konuşma)',
        'keywords': ['kurtar', 'kurtul', 'kurtuluş', 'gizli', 'fısılda', 'konuş', 'çıkar', 'toplantı'],
    },
    'س-و-ي': {
        'buckwalter': 'swy',
        'slug': 'sevi_tesviye_swy',
        'concept_name': 'Sevî / Tesviye (Pürüzsüz Düzlem, Eksiksiz Uyum ve İki Yönlü Denge/Denklik)',
        'keywords': ['düz', 'denk', 'eşit', 'düzenle', 'kurul', 'yönel', 'tamam', 'orta', 'hizala', 'dosdoğru'],
    },
    'ك-ي-ف': {
        'buckwalter': 'kyf',
        'slug': 'keyf_hal_tarz_kyf',
        'concept_name': 'Keyf / Hâl-Tarz Sorgusu (Oluş Biçimi, İşleyiş Mekanizması ve Mantıksal Yüzleştirme)',
        'keywords': ['nasıl', 'biçim', 'tarz', 'hâl', 'bak', 'gör', 'dilediği', 'yöntem', 'son', 'akıbet'],
    },
}

_DYNAMIC_SPECS_PATH = os.path.join(DATA_DIR, 'root_build_specs.json')
DYNAMIC_ROOT_SPECS = {}
if os.path.exists(_DYNAMIC_SPECS_PATH):
    with open(_DYNAMIC_SPECS_PATH, 'r', encoding='utf-8') as _sf:
        DYNAMIC_ROOT_SPECS = json.load(_sf)
    for _ar_root, _spec in DYNAMIC_ROOT_SPECS.items():
        if _ar_root not in ROOT_CONFIG:
            ROOT_CONFIG[_ar_root] = {
                'buckwalter': _spec['buckwalter'],
                'slug': _spec['slug'],
                'concept_name': _spec['concept_name'],
                'keywords': _spec.get('keywords', []),
            }


def _rule_matches(rule, lemma, pos, features, s, a, word_rasm=''):
    ref = f"{s}:{a}"
    ayahs = rule.get('ayahs')
    if ayahs and ref not in ayahs:
        return False
    lemmas = rule.get('lemma')
    if lemmas:
        if isinstance(lemmas, str):
            if lemma != lemmas:
                return False
        elif lemma not in lemmas:
            return False
    pos_req = rule.get('pos')
    if pos_req:
        if isinstance(pos_req, str):
            if pos != pos_req:
                return False
        elif pos not in pos_req:
            return False
    feats = rule.get('features_contains')
    if feats and not all(ft in features for ft in feats):
        return False
    feats_any = rule.get('features_any')
    if feats_any and not any(ft in features for ft in feats_any):
        return False
    rasm_req = rule.get('rasm')
    if rasm_req:
        if isinstance(rasm_req, str):
            if word_rasm != rasm_req:
                return False
        elif word_rasm not in rasm_req:
            return False
    return True


def extract_turkish_snippet(full_tr, root_ar):
    """Uzun Türkçe ayetlerde kökün geçtiği cümle bağlamını çıkarır."""
    if not full_tr:
        return ""
    if len(full_tr) <= 160:
        return full_tr

    clauses = re.split(r'([.;:])', full_tr)
    parts = []
    for i in range(0, len(clauses) - 1, 2):
        parts.append(clauses[i].strip() + clauses[i + 1])
    if len(clauses) % 2 == 1 and clauses[-1].strip():
        parts.append(clauses[-1].strip())

    kws = ROOT_CONFIG.get(root_ar, {}).get('keywords', [])
    matched_idx = -1
    for idx, p in enumerate(parts):
        p_lower = p.lower()
        if any(kw in p_lower for kw in kws):
            matched_idx = idx
            break

    if matched_idx != -1:
        start = max(0, matched_idx - 1) if (matched_idx > 0 and len(parts[matched_idx]) < 70) else matched_idx
        end = min(len(parts), matched_idx + 2)
        snippet = ' '.join(parts[start:end])
        if start > 0:
            snippet = '... ' + snippet
        if end < len(parts):
            snippet = snippet + ' ...'
        return snippet

    return full_tr[:160] + '...'


def determine_literal_irab(root_ar, lemma, pos, features, s, a):
    """Kelimelerin tam irablı, birebir sentaktik Tabula Rasa Türkçe karşılığını üretir."""
    f = features

    if root_ar == 'أ-ل-ه':
        if lemma == '{ll~ah':
            if 'ACC' in f:
                return "Allah'ı (mef'ûl / belirtili nesne mansûb)"
            elif 'GEN' in f:
                return "Allah'ın / Allah'a (harf-i cer ile veya muzâfun ileyh mecrûr)"
            return "Allah (özne / fâil veya mübtedâ merfû')"
        elif lemma == '<ila`h':
            if 'ACC' in f:
                return "İlâhı / sığınak odağını (mef'ûl mansûb)"
            elif 'GEN' in f:
                return "İlâhın / sığınağın (mecrûr)"
            return "İlâh / sığınak mercii (özne merfû')"
        elif lemma == '{ll~ahum~a':
            return "Ey Allah'ım! / Ey yegâne mutlak sığınağım! (tazim ve doğrudan iltica nidası)"

    elif root_ar == 'ق-و-ل':
        if lemma == 'taqaw~ala':
            if 'IMPF' in f:
                return "Kendi kafalarından uydurup isnat ederler (Form V muzâri fiil)"
            return "Kendi kafasından söz uydurup isnat etti (Form V mâzî fiil)"
        elif lemma == '>aqaAwiyl':
            return "Uydurma laflar / asılsız yakıştırmalar (çoğul isim, mecrûr)"
        elif lemma == 'qaA^}il':
            if 'NOM' in f:
                return "Sözü söyleyen / konuşan kimse (ismi fâil, merfû' özne)"
            elif 'ACC' in f:
                return "Konuşan bir kimse olarak (ismi fâil, mansûb hâl)"
            return "Sözü söyleyen / konuşan kimse (ismi fâil)"
        elif lemma == 'qiyl':
            if 'GEN' in f:
                return "Yakarış sözünün / çağrısının (isim, muzâfun ileyh mecrûr)"
            return "Söz / deyiş (isim)"
        elif lemma == 'qawol':
            if 'ACC' in f:
                if (s, a) == (73, 5):
                    return "Ağır ve sorumluluğu büyük bir sözü (mef'ûl / nesne mansûb)"
                elif (s, a) == (33, 70):
                    return "Sağlam ve dosdoğru sözü (mef'ûl / nesne mansûb)"
                elif (s, a) == (20, 44):
                    return "Yumuşak ve incitmeyen bir sözü (mef'ûl / nesne mansûb)"
                elif (s, a) == (17, 23):
                    return "Onurlandırıcı ve ikramkâr bir sözü (mef'ûl mansûb)"
                return "Sözü / beyanı / iddiayı (mef'ûl / nesne mansûb veya mef'ûl-i mutlak)"
            elif 'GEN' in f:
                return "Sözün / beyanın / ilkenin (mecrûr - harf-i cer veya muzâfun ileyh)"
            elif 'NOM' in f:
                return "Söz / beyan / hüküm (merfû' - özne veya mübtedâ)"
            return "Söz / beyan / bildiri (isim / masdar)"
        elif lemma == 'qaAla':
            if 'PASS' in f:
                return "Denildi / söylendi / bildirildi (Form I meçhul mâzî fiil)"
            if 'IMPV' in f:
                if '2MP' in f or 'P' in f:
                    return "Deyin / bildirin / ikrar edin (Form I emir fiil, muhatap çoğul)"
                elif '2MD' in f or 'D' in f:
                    return "İkiniz deyin / söyleyin (Form I emir fiil, muhatap tesniye/ikil)"
                return "De! / Söyle! / Bildir! (Form I emir fiil, muhatap tekil)"
            if 'PERF' in f:
                if '1S' in f:
                    return "Ben dedim / söyledim (Form I mâzî fiil, 1. tekil şahıs)"
                elif '1P' in f:
                    return "Biz dedik / bildirdik (Form I mâzî fiil, 1. çoğul şahıs)"
                elif '2MS' in f:
                    return "Sen dedin / söyledin (Form I mâzî fiil, 2. tekil şahıs)"
                elif '2MP' in f:
                    return "Siz dediniz / söylediniz (Form I mâzî fiil, 2. çoğul şahıs)"
                elif '3FS' in f:
                    return "Dedi / ifade etti (Form I mâzî fiil, 3. dişil tekil şahıs)"
                elif '3MD' in f or '3FD' in f:
                    return "İkisi dedi / söyledi (Form I mâzî fiil, 3. ikil şahıs)"
                elif '3MP' in f:
                    return "Dediler / söylediler / iddia ettiler (Form I mâzî fiil, 3. çoğul şahıs)"
                elif '3FP' in f:
                    return "Dediler / ifade ettiler (Form I mâzî fiil, 3. dişil çoğul)"
                return "Dedi / söyledi / ifade etti (Form I mâzî fiil, 3. eril tekil şahıs)"
            if 'IMPF' in f:
                if '1S' in f:
                    return "Derim / söylerim (Form I muzâri fiil, 1. tekil şahıs)"
                elif '1P' in f:
                    return "Deriz / bildiririz (Form I muzâri fiil, 1. çoğul şahıs)"
                elif '2MS' in f:
                    return "Dersin / söylersin (Form I muzâri fiil, 2. tekil şahıs)"
                elif '2MP' in f:
                    return "Dersiniz / söylersiniz (Form I muzâri fiil, 2. çoğul şahıs)"
                elif '3FS' in f:
                    return "Der / söyler (Form I muzâri fiil, 3. dişil tekil şahıs)"
                elif '3MP' in f:
                    return "Derler / söylerler / iddia ederler (Form I muzâri fiil, 3. çoğul şahıs)"
                return "Der / söyler / beyan eder (Form I muzâri fiil, 3. eril tekil şahıs)"
        return "Söz / beyan eylemi (Form I fiil)"

    elif root_ar == 'ص-ل-و':
        if lemma == 'Salaw`p':
            if 'ACC' in f:
                return "İrtibat ve sorumluluk bağını (mef'ûl / belirtili nesne mansûb)"
            elif 'GEN' in f:
                return "İrtibat ve sorumluluk bağına / bağının (mecrûr)"
            elif 'NOM' in f:
                return "İrtibat ve sorumluluk bağı (özne / mübtedâ merfû')"
            return "İrtibat ve sorumluluk bağı (isim / masdar)"
        elif lemma == 'Sal~aY`':
            if 'IMPV' in f:
                if 'ala' in f or 'P:l' in f or (s, a) == (33, 56):
                    return "Onun arkasında durup destek verin (Form II emir fiil + alâ)"
                return "Yüzünü dönüp yönel, bağ kur (Form II emir fiil)"
            elif 'IMPF' in f:
                if (s, a) in [(33, 43), (33, 56)]:
                    return "Arkasında durup destek verirler (Form II muzâri fiil + alâ)"
                return "Yüzünü dönüp yönelir, bağ kurar (Form II muzâri fiil)"
            else:
                if (s, a) == (75, 31):
                    return "Ne de yönelip bağ kurdu / arkasında durdu (Form II mâzî fiil, nefiy)"
                return "Yüzünü dönüp yöneldi, davanın arkasında durdu (Form II mâzî fiil)"
        elif lemma == 'muSal~iyn':
            return "Sırt çevirmeyip sürekli yönelenler, bağ kurup davanın arkasında duranlar (etken sıfat / ismi fâil)"
        elif lemma == 'muSal~FY':
            return "Yöneliş ve irtibat makamı / odaklanma durağı (mekân ismi)"

    elif root_ar == 'س-ج-د':
        if lemma == 'sajada':
            if 'IMPV' in f:
                return "Kibrinizi kırıp boyun eğin, teslim olun (Form I emir fiil)"
            elif 'IMPF' in f:
                return "Boyun eğerler, ilahi nizama teslim olurlar (Form I muzâri fiil)"
            return "Kibrini kırıp boyun eğdi, teslim oldu (Form I mâzî fiil)"
        elif lemma == 'saAjid':
            return "Boyun eğenler, koşulsuz teslimiyet gösterenler (etken sıfat / ismi fâil)"
        elif lemma == 'masojid':
            return "Boyun eğme ve teslimiyet odakları / mekânları (mekân ismi)"
        elif lemma == 's~ujuwd':
            return "Boyun eğiş ve teslim olma durumu (masdar)"

    elif root_ar == 'ق-و-م':
        if lemma == '>aqaAma':
            if 'IMPV' in f:
                return "Ayakta tutun, diriltin, kurumsallaştırın (Form IV emir fiil)"
            elif 'IMPF' in f:
                return "Ayakta tutarlar, diriltip işletirler (Form IV muzâri fiil)"
            return "Ayakta tuttu, diriltip kurumsallaştırdı (Form IV mâzî fiil)"
        elif lemma in ['<iqaAmat', '<iqaAm', 'm~uqiym']:
            return "Ayakta tutma / ayakta tutan (Form IV masdar / ismi fâil)"
        elif lemma == '{sotaqa`mu':
            if 'IMPV' in f:
                return "Dosdoğru istikamette durun, sapmayın (Form X emir fiil)"
            elif 'IMPF' in f:
                return "Dosdoğru istikamette dururlar (Form X muzâri fiil)"
            return "Dosdoğru istikamet tuttu, sapmadan durdu (Form X mâzî fiil)"
        elif lemma == 'qaAma':
            if 'IMPV' in f:
                return "Ayağa kalkın, duruş sergileyin (Form I emir fiil)"
            elif 'IMPF' in f:
                return "Ayağa kalkarlar, duruş gösterirler (Form I muzâri fiil)"
            return "Ayağa kalktı, duruş sergiledi (Form I mâzî fiil)"
        elif lemma == 'qawom':
            return "Ortak bir duruş sergileyen insan topluluğu (isim)"
        elif lemma == 'qiya`map':
            return "Büyük ayağa kalkış, diriliş ve nihai hesaplaşma anı (masdar isim)"
        elif lemma in ['qiyam', 'qawaAm']:
            return "Ayakta tutucu düzen / denge ölçüsü (sıfat / isim)"
        elif lemma in ['qay~uwm', 'qay~im', 'qay~imap']:
            return "Kendi varlığıyla ayakta duran, her şeyi ayakta tutan; dosdoğru (mübalağa sıfatı)"
        elif lemma in ['qaA^}im', 'qaA^}imap']:
            return "Ayakta duran, görevi ve düzeni gözetip sürdüren (Form I ismi fâil)"
        elif lemma == 'qaw~a`miyn':
            return "Ölçüyü ve adaleti süreklilikle ayakta tutanlar (mübalağa ismi fâili)"
        elif lemma == '>aqowam':
            return "En sağlam, en doğru ve en sarsılmaz olan (ism-i tafdîl)"
        elif lemma == 'taqowiym':
            return "En dengeli biçimde doğrultup şekillendirme (Form II masdar)"
        elif lemma == 'm~usotaqiym':
            return "Hiçbir eğrilik göstermeksizin dosdoğru duran (Form X ismi fâil)"
        elif lemma in ['maqaAm', 'muqaAm', 'muqaAmap']:
            return "Duruş yeri, onurlu makam / yerleşik yurt (mekân ismi)"

    elif root_ar == 'ر-ك-ع':
        if lemma == 'yarokaEu':
            if 'IMPV' in f:
                return "Kibir yapmayıp boyun bükün, tevazu ile katılın (Form I emir fiil)"
            elif 'IMPF' in f:
                return "Boyun bükerler, tevazu gösterirler (Form I muzâri fiil)"
            return "Boyun büktü, tevazu ile boyun eğdi (Form I mâzî fiil)"
        elif lemma == 'raAkiE':
            return "Bireysel kibrini kırıp hakikate boyun bükenler, tevazu ile katılanlar (ismi fâil)"

    elif root_ar == 'ك-ف-ر':
        if (s, a) == (57, 20):
            return "Tohumu toprağa gömüp örten çiftçileri (mef'ûl / çıplak fiziksel asıl)"
        elif lemma == 'kaAfuwr':
            return "Kokusuyla diğer tatları örten kâfûr karışımlı kaynak (etimolojik örtme köklü isim, mansûb)"
        elif lemma == '>akofara':
            return "Ne kadar da gerçeğin üzerini örter / nankörlük eder! (Form IV taaccüp mâzî fiil, 80:17)"
        elif lemma == 'kafara':
            if 'IMPF' in f:
                return "Apaçık gerçeğin üzerini örterler, nankörlük ederler (Form I muzâri fiil)"
            elif 'IMPV' in f:
                return "Gerçeğin üzerini örtün, nankörlük edin (Form I emir fiil)"
            return "Apaçık gerçeğin üzerini örttü / örttüler, nankörlük etti (Form I mâzî fiil)"
        elif lemma in ['kaf~ara', 'kaf~a`rap']:
            return "Kusurların üzerini örtüp siler / kusuru örten telafi bedeli (Form II fiil / masdar)"
        elif lemma in ['kaAfir', 'ka`firuwn', 'kaAfirap', 'kawaAfir']:
            return "Apaçık gerçeğin üzerini kasten örten, yok sayan kimse (ismi fâil)"
        elif lemma in ['kafuwr', 'kaf~aAr', 'kufuwr']:
            return "Nimetin değerini bilmeyip üzerini örtmekte son derece inatçı olan (mübalağa sıfatı)"
        elif lemma in ['kufor', 'kuforaAn']:
            return "Gerçeğin üzerini örtme, yok sayma ve nankörlük durumu (masdar)"

    elif root_ar == 'ش-ك-ر':
        if lemma == '$akara':
            if 'IMPV' in f:
                return "Nimetin değerini bilip açığa vurun (Form I emir fiil)"
            elif 'IMPF' in f:
                return "Nimetin değerini bilip hakkını verirler (Form I muzâri fiil)"
            return "Nimetin değerini bilip hakkını verdi (Form I mâzî fiil)"
        elif lemma in ['$akuwr', '$aAkir']:
            return "Nimetin değerini bilip hakkını tam veren, az iyiliğe çokça karşılık veren (sıfat)"
        elif lemma in ['$ukor', '$ukuwr', 'm~a$okuwr']:
            return "Nimetin değerini bilip açığa vurma, gereğini yapma (masdar / ismi mef'ûl)"

    elif root_ar == 'أ-م-ن':
        if lemma == "'aAmana":
            if 'IMPV' in f:
                return "Şüpheden arınıp içsel güvene erin, emin olup bağlanın (Form IV emir fiil)"
            elif 'IMPF' in f:
                if 'li' in f or 'P:l' in f or (s, a) == (9, 61):
                    return "Ona güvenir, sözüne itimat eder (Form IV muzâri fiil + lî)"
                return "Şüpheden kurtulup içsel güvene ererler, emin olup bağlanırlar (Form IV muzâri fiil)"
            else:
                if 'li' in f or 'P:l' in f:
                    return "Ona güvendi, sözünü doğru kabul edip itimat etti (Form IV mâzî fiil + lî)"
                return "Şüpheden arınıp güvene erdi / erdiler (Form IV mâzî fiil)"
        elif lemma == '>amina':
            if 'IMPV' in f:
                return "Korkudan arınıp güven içinde olun (Form I emir fiil)"
            elif 'IMPF' in f:
                return "Korkudan emin olur, güvende hisseder (Form I muzâri fiil)"
            return "Korkudan kurtulup güvende oldu, emin kaldı (Form I mâzî fiil)"
        elif lemma == '{&otumina':
            return "Kendisine güvenilip emanet bırakıldı (Form VIII meçhul mâzî fiil, 2:283)"
        elif lemma == '<iyma`n':
            return "Korkudan ve şüpheden arınmış sarsılmaz içsel güven bağı (Form IV masdar)"
        elif lemma in ['mu&omin', 'm~u&omina`t', 'm~u&ominap']:
            return "Kendisi güvene eren, emin olan ve çevresine güven veren kimse (Form IV ismi fâil)"
        elif lemma in ['>ama`nat', '>ama`na`t']:
            return "Güvene dayalı olarak korunması gereken sorumluluk / emanet (isim)"
        elif lemma in ['>amon', '>amanap']:
            return "Korkudan kurtulup güvende olma, eminlik ve güvenlik hali (masdar)"
        elif lemma == 'ma>oman':
            return "Korku ve tehlikeden uzak tam güvenlik yeri / sığınak (mekân ismi, 9:6)"
        elif lemma in ["'aAmin", "'aAminiyn", "'aAminap", '>amiyn', 'ma>omuwn']:
            return "Her türlü korkudan emin, kendisine tam itimat edilen (sıfat)"

    elif root_ar == 'ن-ف-ق':
        if lemma == '>anfaqa':
            if 'IMPV' in f:
                return "Eldekini dondurmayıp dolaşıma sokun, toplumun yararına akıtın (Form IV emir fiil)"
            elif 'IMPF' in f:
                return "Dolaşıma sokup paylaştırırlar (Form IV muzâri fiil)"
            return "Dolaşıma soktu / paylaştırdı (Form IV mâzî fiil)"
        elif lemma in ['<infaAq', 'nafaqap', 'nafaqa`t', 'munfiqiyn']:
            return "Dolaşıma sokma payı / dolaşıma sokanlar (Form IV masdar / ismi fâil)"
        elif lemma in ['naAfaqu', 'muna`fiquwn', 'muna`fiqa`t', 'nifaAq']:
            return "Tünelin iki çıkışını kullanarak çift taraflı oynayanlar, iki çıkışlı kaypaklar (Form III)"
        elif lemma == 'nafaq' or (s, a) == (6, 35):
            return "Yerin derinliklerine inen tünel / gizli geçit (isim)"

    elif root_ar == 'ك-و-ن':
        if lemma == 'makaAnat':
            return "Duruş seviyesi / konum ve güç zemini (isim, harf-i cer ile mecrûr)"
        elif lemma == 'm~akaAn':
            if 'POS:LOC' in f:
                return "Belirli bir yer ve sabit konum olarak (mekân zarfı mansûb)"
            elif 'GEN' in f:
                return "Sabit bir konum / mevki (harf-i cer ile veya muzâfun ileyh mecrûr)"
            elif (s, a) == (10, 28):
                return "Konumunuzda / yerinizde sabit kalın! (zarf/ism-i fiil mansûb, 10:28)"
            elif (s, a) in [(4, 20), (16, 101)]:
                return "Bir unsurun / başkasının yerine (ikame bildiren mef'ûl/zarf mansûb)"
            return "Sabit konumu / mevkiyi (mef'ûl veya mekân zarfı mansûb)"
        elif lemma == 'kaAna':
            if 'IMPV' in f:
                if (s, a) in [(2, 117), (3, 47), (3, 59), (6, 73), (16, 40), (19, 35), (36, 82), (40, 68)]:
                    return "Varlık alanına çık / gerçekleş! (Form I tâm emir fiil: kün)"
                elif '2FS' in f:
                    return "Ol / yeni bir nitelik üzere sabitlen! (Form I emir fiil, 2. dişil tekil)"
                elif '2MP' in f:
                    return "Olun / o duruş üzere sağlamca yer tutun! (Form I emir fiil, 2. çoğul)"
                return "Ol / o konum üzere sağlamca dur! (Form I emir fiil, 2. tekil)"
            elif 'PERF' in f:
                if (s, a) == (2, 280):
                    return "Ortaya çıkarsa / darlık çeken biri bulunursa (Form I tâm mâzî fiil, 2:280)"
                perf_map = {
                    '1S': "Oldum / o hal üzere bulundum (Form I mâzî fiil, 1. tekil şahıs)",
                    '1P': "Olduk / o konumda yer tuttuk (Form I mâzî fiil, 1. çoğul şahıs)",
                    '2MS': "Oldun / o durumdaydın (Form I mâzî fiil, 2. eril tekil şahıs)",
                    '2FS': "Oldun / o durumdaydın (Form I mâzî fiil, 2. dişil tekil şahıs)",
                    '2MP': "Oldunuz / o hal üzere bulundunuz (Form I mâzî fiil, 2. çoğul şahıs)",
                    '2FP': "Oldunuz / o konumda bulundunuz (Form I mâzî fiil, 2. dişil çoğul)",
                    '3FS': "Oldu / vuku buldu / öyleydi (Form I mâzî fiil, 3. dişil tekil şahıs)",
                    '3MD': "İkisi oldu / o konumda bulundu (Form I mâzî fiil, 3. eril ikil)",
                    '3FD': "İkisi oldu / o konumda bulundu (Form I mâzî fiil, 3. dişil ikil)",
                    '3MP': "Oldular / vuku buldular / o hal üzereydiler (Form I mâzî fiil, 3. eril çoğul)",
                    '3FP': "Oldular / o konumda bulundular (Form I mâzî fiil, 3. dişil çoğul)",
                }
                for key, desc in perf_map.items():
                    if f'|{key}' in f or f.endswith(key):
                        return desc
                return "Oldu / vuku buldu / köklü biçimde öyledir (Form I mâzî fiil, 3. eril tekil)"
            elif 'IMPF' in f:
                if (s, a) in [(2, 117), (3, 47), (3, 59), (6, 73), (16, 40), (19, 35), (36, 82), (40, 68)] and 'MOOD' not in f:
                    return "Derhal varlık sahasına çıkar / vuku bulur (Form I tâm muzâri fiil)"
                mood = "mecmû (cezm)" if 'MOOD:JUS' in f else ("mansûb (nasb)" if 'MOOD:SUBJ' in f else "merfû")
                impf_map = {
                    '1S': f"Olurum / olurum ki / olmam (Form I muzâri fiil, 1. tekil, {mood})",
                    '1P': f"Oluruz / olalım / olmayalım (Form I muzâri fiil, 1. çoğul, {mood})",
                    '2MS': f"Olursun / olasın / olmayasın (Form I muzâri fiil, 2. eril tekil, {mood})",
                    '2D': f"İkiniz olursunuz / olasınız (Form I muzâri fiil, 2. ikil, {mood})",
                    '2MP': f"Olursunuz / olasınız / olmayasınız (Form I muzâri fiil, 2. çoğul, {mood})",
                    '3FS': f"Olur / vuku bulur / olmasın (Form I muzâri fiil, 3. dişil tekil, {mood})",
                    '3MD': f"İkisi olur / vuku bulur (Form I muzâri fiil, 3. ikil, {mood})",
                    '3MP': f"Olurlar / vuku bulurlar / olmasınlar (Form I muzâri fiil, 3. eril çoğul, {mood})",
                    '3FP': f"Olurlar / o konumda bulunurlar (Form I muzâri fiil, 3. dişil çoğul, {mood})",
                }
                for key, desc in impf_map.items():
                    if f'|{key}|' in f or f.endswith(f'|{key}'):
                        return desc
                return f"Olur / vuku bulur / sabitlenir (Form I muzâri fiil, 3. eril tekil, {mood})"

    elif root_ar == 'ر-ب-ب':
        if lemma == 'rab~a`niy~in':
            if 'ACC' in f:
                return "Kitabı öğreterek toplumu eğitip yetiştirenler (çoğul isim, mansûb haber, 3:79)"
            return "Bilgiyle toplumu eğitip olgunlaştıran rehberler (çoğul isim, merfû)"
        elif lemma == 'rib~iy~uwn':
            return "Aynı ilke ve terbiye etrafında kenetlenmiş büyük topluluklar (çoğul isim, merfû, 3:146)"
        elif lemma == 'raba`^}ib':
            return "Himayenizde büyütülüp yetiştirilen üvey kızlarınız (çoğul isim, merfû, 4:23)"
        elif lemma == 'rab~':
            if 'MP' in f:
                if 'NOM' in f:
                    return "Bölünmüş ve çekişen sahte otoriteler / efendiler (çoğul isim, merfû, 12:39)"
                return "Sahte otoriteler / birbirine efendilik taslayan merciiler (çoğul isim, mansûb)"
            elif (s, a) in [(4, 65), (6, 30), (15, 92), (19, 68), (51, 23), (64, 7)] and 'GEN' in f:
                return "Yetiştirip büyüten Rabb'e kesin ant ve bağlayıcı çağrı (kasem vav'ı ile mecrûr)"
            elif (s, a) in [(25, 30), (43, 88)]:
                return "Ey beni yetiştirip gözetleyen Rabbim! (açık nida 'yâ rabbi', mahallen mansûb)"
            elif ((s, a) in [(12, 41), (12, 42)] or ((s, a) == (12, 50) and 'GEN' in f)):
                if 'ACC' in f:
                    return "Bakımını ve idaresini üstlenen beşerî efendisini (mef'ûl mansûb)"
                return "Bakımını ve idaresini üstlenen beşerî efendisi / hükümdar (mecrûr)"
            elif (s, a) == (12, 23):
                return "Beni barındırıp himaye eden efendim / gözetleyen Rabbim (merfû haber, 12:23)"
            elif 'GEN' in f:
                return "Besleyip büyüten, onarıp olgunlaştıran Rabb'in / Rabb'ine (harf-i cer veya muzâfun ileyh mecrûr)"
            elif 'ACC' in f:
                return "Besleyip büyüten, onarıp olgunlaştıran Rabb'i / Ey Rabb! (mansûb mef'ûl, inne ismi veya münâdâ)"
            return "Besleyip büyüten, onarıp olgunlaştıran Rabb (merfû özne, mübtedâ veya haber)"

    elif root_ar == 'ع-ل-م':
        if lemma == 'Eala`ma`t':
            return "Yön gösteren açık işaretler / yol nişanları (çoğul isim, nekre mecrûr, 16:16)"
        elif lemma == '>aEola`m':
            return "Yüce dağlar / denizde yükselen açık işaret kuleleri (çoğul isim, harf-i cer ile mecrûr)"
        elif lemma == 'muEal~am':
            return "Başkasından talim görüp ezberletilmiş (Form II ismi mef'ûl, haber merfû, 44:14)"
        elif lemma == 'm~aEoluwma`t':
            return "Vakti ve sınırları açıkça belirlenmiş / işaretlenmiş olanlar (çoğul sıfat)"
        elif lemma == 'm~aEoluwm':
            return "Sınırı, vakti veya payı kesin olarak belirlenmiş olan (ismi mef'ûl)"
        elif lemma == 'Ea`lamiyn':
            return "Kendisindeki işaretlerle bilinen tüm varlık ve yaşam katmanları / âlemler (çoğul isim, mecrûr)"
        elif lemma == 'Eal~a`m':
            return "Görünmeyen en derin katmanların dahi her izini eksiksiz bilen (mübalağa sıfatı, merfû)"
        elif lemma == 'Ea`lim':
            if 'MP' in f:
                return "Bilgi sahibi olanlar / kavrayanlar (ismi fâil çoğul)"
            return "Görünmeyeni ve görünür alanı kuşatıp bilen (ismi fâil)"
        elif lemma == '>aEolam':
            return "En iyi bilen / tüm iz ve ayrıntıları en keskin ayırt eden (ism-i tafdîl)"
        elif lemma == 'Ealiym':
            if 'MP' in f:
                return "Varlık işaretlerini derinlemesine okuyup çözümleyen bilginler (çoğul isim, merfû)"
            if 'ACC' in f:
                return "Her ayrıntıyı ve iç niyeti eksiksiz bilen (sıfat/isim, mansûb)"
            elif 'GEN' in f:
                return "Her ayrıntıyı eksiksiz bilenin / bilene (mecrûr)"
            return "Her ayrıntıyı, niyeti ve izi eksiksiz bilen (sıfat/isim, merfû)"
        elif lemma == 'Eilom':
            if 'ACC' in f:
                return "Kesin kanıt ve izlere dayalı bilgiyi / kavrayışı (masdar/isim, mansûb)"
            elif 'GEN' in f:
                return "Kesin bilginin / bilgiye / bilgi ile (masdar/isim, mecrûr)"
            return "Kesin kanıt ve izlere dayalı bilgi / kavrayış (masdar/isim, merfû)"
        elif lemma == 'yataEal~amu':
            return "O yöntemi ve izi kendi üzerine alıp öğrenirler (Form V muzâri fiil, 3. çoğul)"
        elif lemma == 'Eal~ama':
            if 'PASS' in f:
                return "Kendisine iz, yöntem ve beceri öğretildi / kazandırıldı (Form II meçhul mâzî fiil)"
            elif 'IMPF' in f:
                mood = "mansûb" if 'MOOD:SUBJ' in f else "merfû"
                return f"Ayırt edici bilgi, yöntem ve nişan öğreterek zihne işler (Form II muzâri fiil, {mood})"
            return "Ayırt edici bilgi, yöntem ve beceri öğretti / eğitti (Form II mâzî fiil)"
        elif lemma == 'Ealima':
            if 'PASS' in f:
                return "Fark edilsin / açıkça bilinsin diye (Form I meçhul muzâri fiil, mansûb, 24:31)"
            if 'IMPV' in f:
                if '2MP' in f:
                    return "Kesin olarak bilin / farkına varıp kavrayın! (Form I emir fiil, 2. çoğul)"
                return "Kesin olarak bil / kavra! (Form I emir fiil, 2. tekil)"
            mood_sfx = ", mecmû" if 'MOOD:JUS' in f else (", mansûb" if 'MOOD:SUBJ' in f else "")
            if 'IMPF' in f:
                for k, txt in [
                    ('1S', "Bilirim / bilmem / kavrarım"),
                    ('1P', "Biliriz / bilmeyiz / fark ederiz"),
                    ('2MS', "Bilirsin / bilmezsin / kavrarsın"),
                    ('2FS', "Bilirsin / kavrarsın (dişil)"),
                    ('2MP', "Bilirsiniz / bilir misiniz / kavrarsınız"),
                    ('3FS', "Bilir / fark eder (dişil)"),
                    ('3MP', "Bilirler / kavrarlar"),
                    ('3FP', "Bilirler / fark ederler (dişil)"),
                ]:
                    if f'|{k}|' in f or f.endswith(f'|{k}'):
                        return f"{txt} (Form I muzâri fiil{mood_sfx})"
                return f"Bilir / her işareti kavrar (Form I muzâri fiil{mood_sfx})"
            for k, txt in [
                ('1S', "Bildim / kesin öğrendim"),
                ('1P', "Bildik / farkına vardık"),
                ('2MS', "Bildin / anladın"),
                ('2FS', "Bildin / anladın (dişil)"),
                ('2MP', "Bildiniz / kesin kavradınız"),
                ('2FP', "Bildiniz / anladınız (dişil)"),
                ('3FS', "Bildi / fark etti (dişil)"),
                ('3MD', "İkisi bildi / anladı"),
                ('3MP', "Bildiler / gerçeği kavradılar"),
                ('3FP', "Bildiler / fark ettiler (dişil)"),
            ]:
                if f'|{k}|' in f or f.endswith(f'|{k}'):
                    return f"{txt} (Form I mâzî fiil)"
            return "Bildi / izi üzerinden gerçeği kesin kavradı (Form I mâzî fiil)"

    elif root_ar == 'أ-ت-ي':
        if lemma == 'ma>otiy~N':
            return "Gelinip ulaşılacak / gerçekleşmesi kesin olan (Form I ismi mef'ûl, mansûb haber, 19:61)"
        elif lemma == 'mu&otuwn':
            return "Arınma ve paylaşım payını hakkıyla teslim edenler (Form IV ismi fâil çoğul, merfû, 4:162)"
        elif lemma == "<iytaA'N":
            if 'ACC' in f:
                return "Hakkı ve paylaşım payını ulaştırıp teslim etmeyi (Form IV masdar, mansûb)"
            return "Hakkı ve paylaşım payını ulaştırıp teslim etmenin (Form IV masdar, mecrûr)"
        elif lemma == 'A^tiy':
            if 'F|' in f or '|F|' in f:
                return "Kaçınılmaz biçimde gelmekte olan (Form I dişil ismi fâil, merfû)"
            return "Dosdoğru yürüyüp gelen / huzura varan (Form I ismi fâil, merfû)"
        elif lemma == 'A^taY':
            if 'PASS' in f:
                if 'IMPF' in f:
                    mood = "mecmû" if 'MOOD:JUS' in f else ("mansûb" if 'MOOD:SUBJ' in f else "merfû")
                    return f"Kendisine bilgi, yetki veya pay ulaştırılır / verilir (Form IV meçhul muzâri, {mood})"
                return "Kendisine kitap, hikmet, yetki veya nimet ulaştırıldı / verildi (Form IV meçhul mâzî)"
            if 'IMPV' in f:
                if '2FP' in f:
                    return "Hak edilen paylaşım payını eksiksiz teslim edin! (Form IV dişil çoğul emir, 33:33)"
                elif '2MP' in f:
                    return "Arınma payını ve hakkı eksiksiz ulaştırıp teslim edin! (Form IV çoğul emir)"
                return "Bize/ona hak ettiği payı ve lütfu ulaştır! (Form IV tekil emir)"
            if 'IMPF' in f:
                mood = ", mecmû" if 'MOOD:JUS' in f else (", mansûb" if 'MOOD:SUBJ' in f else "")
                for k, txt in [
                    ('1S', "Ulaştırırım / teslim ederim"),
                    ('1P', "Ulaştırırız / hak edileni veririz"),
                    ('2MS', "Ulaştırırsın / verirsin"),
                    ('2MP', "Ulaştırırsınız / hakkı teslim edersiniz"),
                    ('3FS', "Ulaştırır / verir (dişil)"),
                    ('3MP', "Ulaştırırlar / paylaşım payını teslim ederler"),
                ]:
                    if f'|{k}|' in f or f.endswith(f'|{k}'):
                        return f"{txt} (Form IV muzâri fiil{mood})"
                return f"Ulaştırır / verir / hakkı teslim eder (Form IV muzâri fiil{mood})"
            for k, txt in [
                ('1S', "Verdim / ulaştırdım"),
                ('1P', "Biz bilgiyi, belgeyi ve imkânı ulaştırıp verdik"),
                ('2MS', "Sen verdin / ulaştırdın"),
                ('2MP', "Siz verdiniz / teslim ettiniz"),
                ('3FS', "Verdi / ulaştırdı (dişil)"),
                ('3MP', "Verdiler / ulaştırıp teslim ettiler"),
            ]:
                if f'|{k}|' in f or f.endswith(f'|{k}'):
                    return f"{txt} (Form IV mâzî fiil)"
            return "Ulaştırdı / hak edilen değeri veya bilgiyi önüne getirip teslim etti (Form IV mâzî fiil)"
        elif lemma == '>ataY':
            if 'PASS' in f:
                return "Kendilerine benzerlik içinde getirildi / sunuldu (Form I meçhul mâzî, 2:25)"
            if 'IMPV' in f:
                if '2MD' in f:
                    return "İkiniz dosdoğru yönelip gelin / varın! (Form I ikil emir)"
                elif '2MP' in f:
                    return "Usulünce yönelip gelin / kanıtı getirin! (Form I çoğul emir)"
                return "Yönelip gel / getir! (Form I tekil emir)"
            if 'IMPF' in f:
                mood = ", mecmû" if 'MOOD:JUS' in f else (", mansûb" if 'MOOD:SUBJ' in f else "")
                for k, txt in [
                    ('1S', "Gelirim / getiririm"),
                    ('1P', "Geliriz / getiririz"),
                    ('2MS', "Gelirsin / getirirsin"),
                    ('2MP', "Gelirsiniz / getirirsiniz / yönelip işlersiniz"),
                    ('3FS', "Gelir / ulaşır / gerçekleşir (dişil)"),
                    ('3MD', "İkisi gelir / ulaşır"),
                    ('3MP', "Gelirler / getirirler / yönelip işlerler"),
                    ('3FP', "Gelirler / yönelip işlerler (dişil)"),
                ]:
                    if f'|{k}|' in f or f.endswith(f'|{k}'):
                        return f"{txt} (Form I muzâri fiil{mood})"
                return f"Engelsiz akışla gelir / ulaşır / getirir (Form I muzâri fiil{mood})"
            for k, txt in [
                ('1P', "Uyumla ve doğrudan yönelip geldik"),
                ('2MS', "Geldin / getirdin"),
                ('3FS', "Geldi / başa geldi / ulaştı (dişil)"),
                ('3MD', "İkisi geldi / ulaştı"),
                ('3MP', "Geldiler / yönelip işlediler"),
                ('3FP', "Geldiler / yöneldiler (dişil)"),
            ]:
                if f'|{k}|' in f or f.endswith(f'|{k}'):
                    return f"{txt} (Form I mâzî fiil)"
            return "Engelsiz akışla geldi / doğrudan yönelip ulaştı (Form I mâzî fiil)"

    elif root_ar == 'ش-ي-أ':
        if lemma == "$aYo'":
            if '|MP|' in f or f.endswith('|MP'):
                if 'GEN' in f:
                    return "Şeyler / olgular hakkında (gayr-ı munsarıf çoğul isim, عَنْ sonrası fethalı mecrûr)"
                return "Eşyalarını / hak ettikleri maddî varlıklarını (çoğul isim, mansûb)"
            if 'GEN' in f:
                return "Herhangi bir şey / varlık birimi / nesne (nekre tekil isim, mecrûr)"
            if 'ACC' in f:
                return "Herhangi bir şeyi / varlık birimini / en küçük bir payı (nekre tekil isim, mansûb)"
            return "Herhangi bir şey / varlık birimi (nekre tekil isim, merfû)"
        elif lemma == "$aA^'a":
            if 'IMPF' in f:
                mood = ", mecmûm" if 'MOOD:JUS' in f else (", mansûb" if 'MOOD:SUBJ' in f else "")
                for k, txt in [
                    ('1S', "İrademle seçip oldururum / dilerim"),
                    ('1P', "İrademizle seçip oldururuz / dileriz"),
                    ('2MS', "İradenle seçersin / dilersin"),
                    ('2MP', "İradenizle seçersiniz / dilersiniz"),
                    ('3MP', "İradeleriyle seçerler / dilerler"),
                    ('3MS', "İradesiyle seçip fiilen oldurur / diler"),
                ]:
                    if f'|{k}|' in f or f.endswith(f'|{k}'):
                        return f"{txt} (Form I muzâri fiil{mood})"
                return f"İradesiyle seçip oldurur / diler (Form I muzâri fiil{mood})"
            for k, txt in [
                ('1P', "İrademizle seçip oldurduk / diledik"),
                ('2MS', "İradenle seçtin / diledin"),
                ('2D', "İkiniz nasıl ve nereden seçtiyseniz / dilediyseniz (ikil)"),
                ('2MP', "İradenizle seçtiniz / dilediniz"),
                ('3MS', "İradesiyle seçip fiilen oldurdu / diledi"),
            ]:
                if f'|{k}|' in f or f.endswith(f'|{k}'):
                    return f"{txt} (Form I mâzî fiil)"
            return "İradesiyle seçip fiilen oldurdu / diledi (Form I mâzî fiil)"

    elif root_ar == 'ب-ي-ن':
        if lemma == 'bayon':
            if pos == 'N':
                return "Aradaki mesafe / ayrım eşiği / ara bağ (mekân veya ilişki ismi, mecrûr)"
            return "Arasında / iki sınır veya tarafın ara alanında (yer ve yön zarfı)"
        elif lemma == 'm~ubiyn':
            def_str = "belirsiz " if 'INDEF' in f else "belirli "
            role = "isim" if pos == 'N' else "sıfat"
            case_str = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else "mecrûr")
            return f"Apaçık ortaya koyan / bulanıklıktan arınmış ({def_str}Form IV ism-i fâil {role}, {case_str})"
        elif lemma == 'bay~inap':
            num_str = "çoğul " if '|FP' in f else "tekil "
            def_str = "belirsiz " if 'INDEF' in f else "belirli "
            role = "isim" if pos == 'N' else "sıfat"
            case_str = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else "mecrûr")
            return f"Kuşkuyu kesen açık kanıt / belge / belirti ({def_str}{num_str}{role}, {case_str})"
        elif lemma == 'bay~in':
            return "Açık, seçik ve kanıtlı (tekil eril sıfat, mecrûr)"
        elif lemma == 'bayaAn':
            case_str = "merfû" if 'NOM' in f else "mansûb"
            return f"Kavramları ayrıştırıp anlaşılır biçimde dışa vurma / açıklama bütünü (mastar isim, {case_str})"
        elif lemma == 'tiboya`n':
            return "Her yönüyle ayrıştırıp netleştiren kapsamlı açıklama (tef'âl/tif'âl yoğunlaştırma mastarı, mansûb)"
        elif lemma in ['m~ubay~inap', 'm~ubay~ina`t']:
            num_str = "dişil çoğul " if '|FP' in f else "dişil tekil "
            role = "isim" if pos == 'N' else "sıfat"
            return f"Sınırlarını dışa vurup açıkça sergileyen (Form II ism-i fâil {num_str}{role})"
        elif lemma == 'musotabiyn':
            return "Anlamı ve yolu bütünüyle ayrışıp netleşmiş (Form X ism-i fâil sıfat, mansûb)"
        elif lemma == 'yubiynu':
            return "İfadeyi karıştırmadan açıkça dile getirir / sınırını belirginleştirir (Form IV muzâri fiil, 3MS)"
        elif lemma == 'tasotabiyna':
            return "Yolu ve sınırı bütünüyle açığa çıkıp netleşsin diye (Form X mansûb muzâri fiil, 3FS)"
        elif lemma == 'bay~anu':
            if 'IMPF' in f:
                mood = ", mecmûm" if 'MOOD:JUS' in f else (", mansûb" if 'MOOD:SUBJ' in f else "")
                for k, txt in [
                    ('1S', "Karışıklığı ayırıp netleştiririm"),
                    ('1P', "Açıkça ayrıştırır ve ortaya sereriz"),
                    ('2MS', "Sen onlara açıp netleştirirsin"),
                    ('2MP', "Siz onu insanlara mutlaka açıp netleştireceksiniz"),
                    ('3MS', "Ayrıştırıp açıkça ortaya koyar"),
                ]:
                    if f'|{k}|' in f or f.endswith(f'|{k}'):
                        return f"{txt} (Form II muzâri fiil{mood})"
                return f"Ayrıştırıp açıkça ortaya koyar (Form II muzâri fiil{mood})"
            for k, txt in [
                ('1P', "Ayrıştırıp açıkça ortaya serdik"),
                ('3MP', "Gerçeği gizlemeyip açıkça ortaya koydular"),
            ]:
                if f'|{k}|' in f or f.endswith(f'|{k}'):
                    return f"{txt} (Form II mâzî fiil)"
            return "Ayrıştırıp açıkça ortaya serdi (Form II mâzî fiil)"
        elif lemma == 'tabay~ana':
            if 'IMPV' in f:
                return "Acele karar vermeden önce iyice araştırıp sınırları netleştirin! (Form V çoğul emir)"
            if 'IMPF' in f:
                return "Ayrışıp belirginleşsin / seçilip netleşsin diye (Form V mansûb muzâri fiil, 3MS)"
            if '|3FS|' in f or f.endswith('|3FS'):
                return "Gerçeğin sınırı ayrışıp apaçık anlaşıldı (Form V mâzî fiil, 3FS)"
            return "Sınırı ayrıştı / bulanıklıktan sıyrılıp netleşti (Form V mâzî fiil, 3MS)"

    elif root_ar == 'ر-س-ل':
        if lemma == 'rasuwl':
            num = "çoğul " if '|MP|' in f or f.endswith('|MP') else ("ikil " if '|MD|' in f or f.endswith('|MD') else "tekil ")
            def_s = "belirsiz " if 'INDEF' in f else "belirli "
            case_s = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else "mecrûr")
            return f"Merkezden görevlendirilmiş elçi / mesaj taşıyıcısı ({def_s}{num}isim, {case_s})"
        elif lemma == 'm~urosal':
            num = "çoğul " if '|MP|' in f else "tekil "
            def_s = "belirsiz " if 'INDEF' in f else "belirli "
            role = "sıfat" if pos == 'ADJ' else "isim"
            case_s = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else "mecrûr")
            return f"Hedefe doğru salınıp gönderilmiş elçi / görevli ({def_s}{num}Form IV ism-i mef'ûl {role}, {case_s})"
        elif lemma in ['risaAlap', 'risa`la`t']:
            num = "çoğul " if '|FP|' in f else "tekil "
            case_s = "mansûb" if 'ACC' in f else "mecrûr"
            return f"Elçiyle iletilen mesaj / görev bildirisi ({num}dişil isim, {case_s})"
        elif lemma in ['murosil', 'murosilap']:
            num = "dişil " if lemma == 'murosilap' else ("çoğul " if '|MP|' in f else "tekil ")
            case_s = "merfû" if 'NOM' in f else "mansûb"
            return f"Yola çıkaran / serbest bırakıp gönderen ({num}Form IV ism-i fâil isim, {case_s})"
        elif lemma == 'murosala`t':
            return "Peş peşe salınıp gönderilen rüzgâr / akım dalgaları (dişil çoğul Form IV ism-i mef'ûl, mecrûr)"
        elif lemma == '>arosala':
            if 'PASS' in f:
                if 'IMPF' in f:
                    return "Hedefe doğru salınır / püskürtülür (Form IV edilgen muzâri fiil, 3MS)"
                for k, txt in [
                    ('1S', "Mesaj ve görevle gönderildim"),
                    ('1P', "Bir görevle gönderildik"),
                    ('2MP', "Size iletilmek üzere gönderildiniz"),
                    ('3MP', "Gözcü/bekçi olarak salındılar / gönderildiler"),
                ]:
                    if f'|{k}|' in f or f.endswith(f'|{k}'):
                        return f"{txt} (Form IV edilgen mâzî fiil)"
                return "Bir görev veya mesajla gönderildi (Form IV edilgen mâzî fiil, 3MS)"
            if 'IMPV' in f:
                if '|2MP|' in f or f.endswith('|2MP'):
                    return "Beni hemen gönderin / salıverin! (Form IV çoğul emir)"
                return "Yanımıza sal / gönder! (Form IV tekil emir)"
            if 'IMPF' in f:
                mood = ", mecmûm" if 'MOOD:JUS' in f else (", mansûb" if 'MOOD:SUBJ' in f else "")
                for k, txt in [
                    ('1S', "Onu sizinle asla göndermem / salıvermem"),
                    ('1P', "Salıverir / göndeririz"),
                    ('3MS', "Salıverip gönderir / akışa bırakır"),
                ]:
                    if f'|{k}|' in f or f.endswith(f'|{k}'):
                        return f"{txt} (Form IV muzâri fiil{mood})"
                return f"Salıverip gönderir (Form IV muzâri fiil{mood})"
            for k, txt in [
                ('1P', "Salıverdik / görevlendirip gönderdik"),
                ('2MS', "Sen onların üzerine saldın / gönderdin"),
                ('3FS', "Onlara haberci gönderdi (dişil)"),
                ('3MP', "Sucu görevlilerini kuyuya gönderdiler"),
                ('3MS', "Gönderdi / serbest bırakıp akıttı"),
            ]:
                if f'|{k}|' in f or f.endswith(f'|{k}'):
                    return f"{txt} (Form IV mâzî fiil)"
            return "Salıverip gönderdi (Form IV mâzî fiil)"

    elif root_ar == 'أ-ر-ض':
        if 'INDEF' in f:
            if 'GEN' in f:
                return "Herhangi bir toprak parçası / yer (belirsiz tekil dişil isim, mecrûr)"
            return "Herhangi bir yer / bölge / toprak (belirsiz tekil dişil isim, mansûb)"
        if (s, a) == (11, 44):
            return "Ey yer / alt zemin! (nidâ halinde tekil dişil isim, merfû)"
        if 'GEN' in f:
            return "Yeryüzü / üzerinde yaşanılan alt zemin veya bölge (tekil dişil isim, mecrûr)"
        if 'ACC' in f:
            return "Yeryüzünü / üzerinde yaşanılan alt zemini veya toprağı (tekil dişil isim, mansûb)"
        return "Yeryüzü / üzerinde yaşanılan alt zemin (tekil dişil isim, merfû)"

    elif root_ar == 'ي-و-م':
        if lemma == 'yawom':
            if 'MD' in f:
                return "İki gün / iki dönem veya iki aşama boyunca (ikil eril isim, mecrûr)"
            if 'MP' in f or 'FP' in f:
                if 'INDEF' in f:
                    if pos == 'T':
                        return "Sayılı günler boyunca / belirli bir süre içinde (çoğul belirsiz zaman zarfı, mansûb)"
                    if 'NOM' in f:
                        return "Günler / belirli dönemler (çoğul belirsiz isim, merfû)"
                    if 'ACC' in f:
                        return "Günleri / belirli dönemleri (çoğul belirsiz isim, mansûb)"
                    return "Günler / belirli dönemler veya aşamalar (çoğul belirsiz isim, mecrûr)"
                if 'NOM' in f:
                    return "O günler / söz konusu tarihsel dönemler (çoğul belirli isim, merfû)"
                if 'ACC' in f:
                    return "O günleri / tarihsel dönüşüm dönemlerini (çoğul belirli isim, mansûb)"
                return "O günler / tarihsel aşamalar ve ibretlik süreçler (çoğul belirli isim, mecrûr)"
            if pos == 'T':
                return "Bugün / o belirlenen günde veya aşama anında (tekil eril zaman zarfı, mansûb)"
            if 'INDEF' in f:
                if 'NOM' in f:
                    return "Bir gün / tekil bir zaman birimi veya dönem (tekil belirsiz eril isim, merfû)"
                if 'ACC' in f:
                    return "Bir günü / tekil bir zaman dilimini (tekil belirsiz eril isim, mansûb)"
                return "Bir gün / herhangi bir zaman birimi veya dönem (tekil belirsiz eril isim, mecrûr)"
            if 'NOM' in f:
                return "O gün / belirlenmiş vakit veya süreç dönemi (tekil eril isim, merfû)"
            if 'ACC' in f:
                return "O günü / belirlenmiş dönem veya zaman dilimini (tekil eril isim, mansûb)"
            return "O gün / söz konusu dönem veya hesaplaşma aşaması (tekil eril isim, mecrûr)"

    elif root_ar == 'أ-ي-ي':
        if lemma == "'aAyap":
            if 'FD' in f:
                return "İki açık göstergeyi / iki kozmik işareti (ikil dişil isim, mansûb)"
            if 'FP' in f:
                if 'INDEF' in f:
                    if 'NOM' in f:
                        return "Açık göstergeler / kanıtlar veya bilgi birimleri (çoğul belirsiz dişil isim, merfû)"
                    if 'ACC' in f:
                        return "Açık göstergeleri / doğadaki ve metindeki kanıtları (çoğul belirsiz dişil isim, mansûb)"
                    return "Açık göstergeler / çoklu deliller veya işaretler (çoğul belirsiz dişil isim, mecrûr)"
                if 'NOM' in f:
                    return "O göstergeler / belirlenmiş evrensel kanıtlar ve ifadeler (çoğul dişil isim, merfû)"
                if 'ACC' in f:
                    return "O göstergeleri / belirlenmiş kanıtları ve metin birimlerini (çoğul dişil isim, mansûb)"
                return "O göstergeler / evrensel ve yazılı kanıtlar (çoğul dişil isim, mecrûr)"
            if 'INDEF' in f:
                if 'NOM' in f:
                    return "Bir gösterge / somut bir kanıt veya belirgin işaret (tekil belirsiz dişil isim, merfû)"
                if 'ACC' in f:
                    return "Bir göstergeyi / tekil bir kanıt veya işareti (tekil belirsiz dişil isim, mansûb)"
                return "Bir gösterge / herhangi bir kanıt veya metin birimi (tekil belirsiz dişil isim, mecrûr)"
            if 'NOM' in f:
                return "O gösterge / beklenen somut işaret veya belirteç (tekil dişil isim, merfû)"
            if 'ACC' in f:
                return "O göstergeyi / en büyük somut kanıtı veya işareti (tekil dişil isim, mansûb)"
            return "O gösterge / söz konusu somut işaret (tekil dişil isim, mecrûr)"

    elif root_ar == 'س-م-و':
        if lemma == "samaA^'":
            if 'FP' in f:
                if 'INDEF' in f:
                    return "Yüksek katmanlar / yedi kozmik gök düzlemi (çoğul belirsiz dişil isim, mecrûr)"
                if 'NOM' in f:
                    return "Gökler / üst kozmik katmanlar (çoğul dişil isim, merfû)"
                if 'ACC' in f:
                    return "Gökleri / üst kozmik katmanları (çoğul dişil isim, mansûb)"
                return "Gökler / üst kozmik katmanlar ve uzay yapısı (çoğul dişil isim, mecrûr)"
            if 'INDEF' in f:
                return "Bir gök katmanı / her bir yüksek kozmik alan (tekil belirsiz dişil isim, mecrûr)"
            if 'NOM' in f:
                return "Gök / üst atmosfer veya tavan düzlemi (tekil dişil isim, merfû)"
            if 'ACC' in f:
                return "Göğü / üst kozmik yapıyı veya tavanı (tekil dişil isim, mansûb)"
            return "Gök / üst katman, yağmur kaynağı veya yüksek tavan (tekil dişil isim, mecrûr)"
        elif lemma == '{som':
            if 'MP' in f:
                if 'INDEF' in f:
                    if 'NOM' in f:
                        return "İsimler / belirleyici kavram ve adlar (çoğul belirsiz eril isim, merfû)"
                    if 'ACC' in f:
                        return "İsimleri / belirleyici sıfat veya adları (çoğul belirsiz eril isim, mansûb)"
                    return "İsimler / sonradan yakıştırılmış uydurma adlar (çoğul belirsiz eril isim, mecrûr)"
                if 'NOM' in f:
                    return "İsimler / en güzel tanıtıcı sıfat ve kavramlar (çoğul eril isim, merfû)"
                if 'ACC' in f:
                    return "İsimleri / tüm varlıkların tanımlayıcı kavramlarını (çoğul eril isim, mansûb)"
                return "İsimler / varlığı ve özü tanıtan kavramlar (çoğul eril isim, mecrûr)"
            if 'NOM' in f:
                return "İsim / anılan kimlik, ad veya niteleme (tekil eril isim, merfû)"
            if 'ACC' in f:
                return "İsmi / kimliği, adı veya belirteci (tekil eril isim, mansûb)"
            return "İsim / otorite, kimlik veya referans adı (tekil eril isim, mecrûr)"
        elif lemma == 'm~usam~FY':
            if 'NOM' in f:
                return "Adı konulmuş / sınırı belirlenmiş vade (II. bab edilgen ortaç, merfû)"
            if 'GEN' in f:
                return "Adı konulmuş / sınırı önceden çizilmiş vade veya süre (II. bab edilgen ortaç, mecrûr)"
            return "Adı konulmuş / belirlenmiş süre (II. bab edilgen ortaç, mansûb)"
        elif 'sam~aY' in lemma:
            if 'PASS' in f:
                return "Adlandırılır / anılır (II. bab edilgen muzâri fiil, 3. tekil dişil)"
            if 'IMPV' in f:
                return "Adlandırın / kimliğini ortaya koyun (II. bab emir fiili, 2. çoğul)"
            if 'IMPF' in f:
                return "Adlandırıyorlar / isim yakıştırıyorlar (II. bab etken muzâri fiil, 3. çoğul)"
            if '1S' in f:
                return "Adını koydum / adlandırdım (II. bab mâzî fiil, 1. tekil)"
            if '2MP' in f:
                return "Adlandırdınız / isim taktınız (II. bab mâzî fiil, 2. çoğul)"
            return "Sizi adlandırdı / kimlik verdi (II. bab mâzî fiil, 3. tekil eril)"
        elif lemma == 'samiy~':
            return "Adaş / aynı isimde veya denk olan bir benzeri (tekil belirsiz eril isim, mansûb)"
        elif lemma == 'tasomiyap':
            return "Adlandırma / isim takma ve yakıştırma biçimini (II. bab mastar/isim, mansûb)"

    elif root_ar == 'ع-ذ-ب':
        if lemma == 'Ea*aAb':
            if 'INDEF' in f:
                if 'NOM' in f:
                    return "Bir ağır yaptırım / keskin bir acı ve yoksunluk durumu (tekil belirsiz eril isim, merfû)"
                if 'ACC' in f:
                    return "Ağır bir yaptırımı / keskin bir ıstırap veya yoksunluğu (tekil belirsiz eril isim, mansûb)"
                return "Ağır bir yaptırım / acı sonuç veya yoksunluk hâli (tekil belirsiz eril isim, mecrûr)"
            if 'NOM' in f:
                return "O ağır yaptırım / söz konusu yoksunluk ve acı sonuç (tekil eril isim, merfû)"
            if 'ACC' in f:
                return "O ağır yaptırımı / yoksunluk ve eziyeti (tekil eril isim, mansûb)"
            return "O ağır yaptırım / söz konusu acı, eziyet veya yoksunluk (tekil eril isim, mecrûr)"
        elif lemma == 'Ea*ob':
            return "Tatlı ve ferahlatıcı su / susuzluğu kesen duru içecek (tekil belirsiz eril isim/sıfat, merfû)"
        elif lemma == 'Ea*~aba':
            if 'PERF' in f:
                if '1P' in f:
                    return "Ağır yaptırıma uğrattık / acı sonuca tabi kıldık (II. bab mâzî fiil, 1. çoğul)"
                return "Ağır yaptırıma uğrattı / huzurdan mahrum kıldı (II. bab mâzî fiil, 3. tekil eril)"
            if '1S' in f:
                return "Ağır yaptırıma uğratırım / kesinlikle cezalandırırım (II. bab muzâri fiil, 1. tekil)"
            if '1P' in f:
                return "Ağır yaptırıma uğratırız / cezalandırırız (II. bab muzâri fiil, 1. çoğul)"
            if '2MS' in f:
                return "Sen yaptırım uygularsın / cezalandırırsın (II. bab muzâri fiil, 2. tekil eril)"
            return "Ağır yaptırıma ve yoksunluğa uğratır / cezalandırır (II. bab muzâri fiil, 3. tekil eril)"
        elif lemma == 'muEa*~ib':
            if 'MP' in f:
                if 'ACC' in f:
                    return "Ağır yaptırım uygulayanlar / cezalandırıcılar (II. bab etken ortaç, çoğul mansûb)"
                return "Ağır yaptırım uygulayacak olanlar / cezalandıracaklar (II. bab etken ortaç, çoğul merfû)"
            if 'ACC' in f:
                return "Yaptırım uygulayıcıyı / cezalandıran merciyi (II. bab etken ortaç, tekil mansûb)"
            return "Yaptırım uygulayıcısı / cezalandırıcısı (II. bab etken ortaç, tekil merfû)"
        elif lemma == 'muEa*~abiyn':
            return "Ağır yaptırıma uğratılanlar / acı sonuçla yüzleşecek olanlar (II. bab edilgen ortaç, çoğul mecrûr)"

    elif root_ar == 'ك-ل-ل':
        if lemma == 'kul~':
            if pos == 'T':
                return "Her ne zaman / her tekrarlandığında (tekil eril zaman zarfı, mansûb)"
            if 'INDEF' in f:
                if 'NOM' in f:
                    return "Her biri / istisnasız tamamı (tenvinli bağımsız eril isim, merfû)"
                if 'ACC' in f:
                    return "Her birini / tamamını eksiksiz (tenvinli bağımsız eril isim, mansûb)"
                return "Her biri / her kesim için (tenvinli bağımsız eril isim, mecrûr)"
            if 'NOM' in f:
                return "Her / bütünü ve istisnasız her bir öğesi (tamlayan eril isim, merfû)"
            if 'ACC' in f:
                return "Her birini / bütününü veya tam kapsamını (tamlayan eril isim, mansûb)"
            return "Her / kapsadığı tüm birimler ve öğeler (tamlayan eril isim, mecrûr)"
        elif lemma == 'kul~amaA':
            return "Her ne zaman / bir olay her tekrarlandığında (bileşik zaman-koşul zarfı)"
        elif lemma == 'kala`lap':
            if 'INDEF' in f:
                return "Anne-babası ve çocuğu olmadan yanal akrabalık durumunda (tekil belirsiz dişil isim, mansûb)"
            return "Anne-babasız ve çocuksuz yanal miras halkası hakkında (tekil belirli dişil isim, mecrûr)"
        elif lemma == 'kal~':
            return "Üzerinde yaşadığı koruyucuya ağır ve verimsiz bir yük (tekil belirsiz eril isim, merfû)"

    elif root_ar == 'ع-م-ل':
        if lemma == 'Eamila':
            if 'IMPV' in f:
                if '2MP' in f:
                    return "Bilinçle iş yapın / üretin (I. bab emir fiil, 2. çoğul eril)"
                return "Bilinçle yap / üret (I. bab emir fiil, 2. tekil eril)"
            if 'PERF' in f:
                if '3MP' in f:
                    return "Bilinçli olarak yaptılar / ürettiler (I. bab mâzî fiil, 3. çoğul eril)"
                if '3FS' in f:
                    return "Yaptı / eliyle işleyip ortaya koydu (I. bab mâzî fiil, 3. tekil dişil)"
                if '2MP' in f:
                    return "Siz yaptınız / işlediniz (I. bab mâzî fiil, 2. çoğul eril)"
                return "Bilinçli bir iş yaptı / ortaya koydu (I. bab mâzî fiil, 3. tekil eril)"
            if '2MP' in f:
                return "Yapıp ediyorsunuz / işliyorsunuz (I. bab muzâri fiil, 2. çoğul eril)"
            if '3MP' in f:
                return "Yapıp ediyorlar / işliyorlar (I. bab muzâri fiil, 3. çoğul eril)"
            if '1S' in f:
                if 'SUBJ' in f:
                    return "Yapayım / bilinçli iş ortaya koyayım (I. bab muzâri mansûb fiil, 1. tekil)"
                return "Ben yaparım / yaptığım iş (I. bab muzâri fiil, 1. tekil)"
            if '1P' in f:
                if 'JUS' in f or 'SUBJ' in f:
                    return "Yapalım / farklı ve onarıcı iş üretelim (I. bab muzâri meczûm/mansûb fiil, 1. çoğul)"
                return "Biz yapıyorduk / üretiyorduk (I. bab muzâri fiil, 1. çoğul)"
            if '3FS' in f:
                if 'JUS' in f:
                    return "Yapsın / yararlı iş üretsin (I. bab muzâri meczûm fiil, 3. tekil dişil)"
                return "Yapıyor / işliyor (I. bab muzâri fiil, 3. tekil dişil)"
            if 'JUS' in f:
                return "Yaparsa / işlesin (I. bab muzâri meczûm fiil, 3. tekil eril)"
            return "Yapar / işler (I. bab muzâri fiil, 3. tekil eril)"
        elif lemma == 'Eamal':
            if 'MP' in f:
                if 'NOM' in f:
                    return "Yapılan işler / eylemler ve ürünler (çoğul eril isim, merfû)"
                if 'ACC' in f:
                    return "Yapılan işleri / eylemleri (çoğul eril isim, mansûb)"
                return "Yapılan işlerden / eylemlerinin (çoğul eril isim, mecrûr)"
            if 'NOM' in f:
                return "İş / yapılan somut eylem ve ürün (tekil eril isim, merfû)"
            if 'ACC' in f:
                return "İşi / somut bir eylemi ve ürünü (tekil eril isim, mansûb)"
            return "İşin / yapılan eylemin (tekil eril isim, mecrûr)"
        elif lemma == 'Ea`mil':
            if 'MP' in f:
                if 'NOM' in f:
                    return "İşi fiilen yapanlar / çalışan üreticiler (çoğul eril etken ortaç, merfû)"
                return "Çalışanlar / sahada görev yürütenler için (çoğul eril etken ortaç, mecrûr)"
            if 'NOM' in f:
                return "İşi yürüten / bilinçle üreten özne (tekil eril etken ortaç, merfû)"
            return "Çalışan / iş yapan kimse (tekil eril etken ortaç, mecrûr)"
        elif lemma == 'EaAmilap':
            return "Ağır ve yorucu iş altında durmadan çalışan (tekil belirsiz dişil sıfat, merfû)"

    elif root_ar == 'ج-ع-ل':
        if lemma == 'jaEala':
            if 'IMPV' in f:
                if '2MP' in f:
                    return "İşlevselleştirin / kılın veya konumlandırın (I. bab emir fiil, 2. çoğul eril)"
                return "Kıl / dönüştür veya bir konuma yerleştir (I. bab emir fiil, 2. tekil eril)"
            if 'PASS' in f:
                return "Kılındı / düzenlenip bağlayıcı hâle getirildi (I. bab edilgen mâzî fiil, 3. tekil eril)"
            if 'PERF' in f:
                if '1P' in f:
                    return "Kıldık / düzenleyip işlevsel kıldık (I. bab mâzî fiil, 1. çoğul)"
                if '3MP' in f:
                    return "Kıldılar / dönüştürdüler veya yakıştırdılar (I. bab mâzî fiil, 3. çoğul eril)"
                if '2MP' in f:
                    return "Siz kıldınız / konumlandırdınız (I. bab mâzî fiil, 2. çoğul eril)"
                if '3FS' in f:
                    return "Kıldı / yerleştirdi (I. bab mâzî fiil, 3. tekil dişil)"
                if '1S' in f:
                    return "Kıldım / düzenledim (I. bab mâzî fiil, 1. tekil)"
                return "Kıldı / işlevsel hâle getirdi veya tayin etti (I. bab mâzî fiil, 3. tekil eril)"
            if '3MS' in f:
                if 'JUS' in f or 'SUBJ' in f:
                    return "Kılsın / dönüştürsün veya yerleştirsin (I. bab muzâri meczûm/mansûb fiil, 3. tekil eril)"
                return "Kılar / işlevselleştirir veya atar (I. bab muzâri fiil, 3. tekil eril)"
            if '2MS' in f:
                if 'JUS' in f or 'SUBJ' in f:
                    return "Kılma / dönüştüresin (I. bab muzâri meczûm/mansûb fiil, 2. tekil eril)"
                return "Kılarsın / düzenlersin (I. bab muzâri fiil, 2. tekil eril)"
            if '1P' in f:
                if 'JUS' in f or 'SUBJ' in f:
                    return "Kılalım / dönüştürelim veya koyalım (I. bab muzâri meczûm/mansûb fiil, 1. çoğul)"
                return "Kılarız / işlevselleştiririz (I. bab muzâri fiil, 1. çoğul)"
            if '3MP' in f:
                if 'SUBJ' in f:
                    return "Kılsınlar / yakıştırsınlar diye (I. bab muzâri mansûb fiil, 3. çoğul eril)"
                return "Kılarlar / konumlandırırlar veya yakıştırırlar (I. bab muzâri fiil, 3. çoğul eril)"
            if '2MP' in f:
                if 'JUS' in f or 'SUBJ' in f:
                    return "Kılmayın / dönüştürmeyesiniz (I. bab muzâri meczûm/mansûb fiil, 2. çoğul eril)"
                return "Kılıyorsunuz / dönüştürüyorsunuz (I. bab muzâri fiil, 2. çoğul eril)"
            if '1S' in f:
                if 'JUS' in f:
                    return "Kılayım / yerleştireyim (I. bab muzâri meczûm fiil, 1. tekil)"
                return "Ben kılarım / dönüştürürüm (I. bab muzâri fiil, 1. tekil)"
        elif lemma == 'jaAEil':
            if 'MP' in f:
                return "Düzenleyip dönüştürecek / görevlendirecek olanlar (çoğul eril etken ortaç, merfû)"
            if 'GEN' in f:
                return "Görev ve işlev atayanın (tekil eril etken ortaç, mecrûr)"
            if 'INDEF' in f:
                return "Mutlaka konumlandırıp görevlendirecek olan (tekil belirsiz eril etken ortaç, merfû)"
            return "Atayacak / üstün veya önder konuma yerleştirecek olan (tekil eril etken ortaç, merfû)"

    elif root_ar == 'ر-ح-م':
        if lemma == 'r~aHiym':
            if 'MP' in f:
                return "Birbirine karşı şefkatli ve koruyucu olanlar (çoğul sıfat, merfû)"
            if 'ACC' in f:
                return "Kesintisiz koruyup besleyen, şefkatli (tekil eril mansûb)"
            if 'GEN' in f:
                return "Sürekli koruyucu ve şefkatli olanın (tekil eril mecrûr)"
            return "Sürekli koruyan, besleyip onaran Rahîm (tekil eril merfû)"
        elif lemma == 'raHomap':
            if 'ACC' in f:
                return "Kuşatıcı şefkat, koruma ve yaşam desteğini (dişil isim, mansûb)"
            if 'GEN' in f:
                return "Koruyucu şefkat, onarım ve desteğin (dişil isim, mecrûr)"
            return "Kuşatıcı şefkat, besleyici koruma ve esenlik (dişil isim, merfû)"
        elif lemma == 'r~aHoma`n':
            if 'GEN' in f:
                return "Hiçbir şart aramadan tüm evreni kuşatan Rahmân'ın (tekil eril mecrûr)"
            if 'ACC' in f:
                return "Tüm canlıları koşulsuz kucaklayan Rahmân'ı (tekil eril mansûb)"
            return "Her varlığı şefkatle besleyen mutlak Rahmân (tekil eril merfû)"
        elif lemma == 'r~aHima':
            if 'PASS' in f:
                return "Şefkat görüp koruma altına alınmanız için (I. bab edilgen muzâri fiil, 2. çoğul eril)"
            if 'IMPV' in f:
                return "Koru, gözet ve şefkatle sar (I. bab emir fiil, 2. tekil eril)"
            if 'PERF' in f:
                if '1P' in f:
                    return "Şefkatle koruduk ve esenliğe aldık (I. bab mâzî fiil, 1. çoğul)"
                if '2MS' in f:
                    return "Sen şefkat gösterip korudun (I. bab mâzî fiil, 2. tekil eril)"
                return "Şefkatle korudu ve esirgedi (I. bab mâzî fiil, 3. tekil eril)"
            if '3FS' in f:
                return "Geri dönülmez ise acıyıp korur / esirger (I. bab muzâri meczûm fiil, 3. tekil dişil)"
            if '2MS' in f:
                return "Sen koruyup esirgersin (I. bab muzâri meczûm fiil, 2. tekil eril)"
            return "Koruyup şefkatle kuşatır / esirger (I. bab muzâri fiil, 3. tekil eril)"
        elif lemma == '>aroHaAm':
            if 'ACC' in f:
                return "Ana rahimlerini / rahim kaynaklı akrabalık bağlarını (çoğul isim, mansûb)"
            if 'GEN' in f:
                return "Ana rahimlerinin / rahim temelli soy bağlarının (çoğul isim, mecrûr)"
            return "Ana rahimleri / rahim temelli soy yakınlıkları (çoğul isim, merfû)"
        elif lemma == 'r~a`Himiyn':
            return "Şefkat gösteren ve koruyanların (çoğul eril etken ortaç, mecrûr)"
        elif lemma == '>aroHam':
            return "En çok şefkat göstereni ve en kapsayıcı koruyucusu (üstünlük ismi, tekil eril merfû)"
        elif lemma == 'ruHom':
            return "İçten şefkat, sevgi ve yakınlık bağı bakımından (tekil belirsiz eril isim, mansûb)"
        elif lemma == 'maroHamap':
            return "İnsanların birbirine karşılıklı şefkat ve koruma tavsiye etmesi (tekil dişil isim, mecrûr)"

    elif root_ar == 'ر-أ-ي':
        if lemma == "ri}aA^'":
            return "Başkalarının gözüne görünmek için sergilenen vitrin gösterişi (III. bab mastarı, mansûb)"
        elif lemma == "yuraA^'u":
            return "Başkalarına gösteriş yaparlar / vitrin davranışı sergilerler (III. bab muzâri fiil, 3. çoğul eril)"
        elif lemma == "taraA^'ati":
            return "İki topluluk karşı karşıya gelip birbirini gördüğünde (VI. bab işteş fiil)"
        elif lemma == "r~u'oyaA":
            if 'GEN' in f:
                return "Uykuda veya içsel bilinçte beliren öngörü tablosunun / rüyanın (tekil dişil isim, mecrûr)"
            return "Uykuda veya içsel bilinçte beliren simgesel öngörü / rüya (tekil dişil isim, merfû)"
        elif lemma == "ra>oY":
            if 'ACC' in f:
                return "Gözün açık tanıklığıyla / doğrudan gözlem ölçüsüyle (tekil eril isim, mansûb)"
            return "Derinlemesine incelemeden oluşan yüzeysel ilk görüşün / kanaatin (tekil eril isim, mecrûr)"
        elif lemma == "ri'oy":
            return "Dış görünüş, gösteriş ve ihtişam bakımından (tekil belirsiz eril isim, mansûb)"
        elif lemma == '>arayo':
            if (s, a) in [(5, 31), (7, 27)]:
                return "Ona / ikisine eylemi veya durumu görünür kılıp göstermek için (IV. bab etken ettirgen muzâri mansûb fiil)"
            if 'PASS' in f:
                return "Yaptıklarının kendilerine gösterilmesi için (IV. bab edilgen muzâri mansûb fiil, 3. çoğul eril)"
            if 'IMPV' in f:
                if '2MP' in f:
                    return "Bana gösterin / somut kanıtını ortaya koyun (IV. bab emir fiil, 2. çoğul eril)"
                return "Bana / bize göster, görünür ve anlaşılır kıl (IV. bab emir fiil, 2. tekil eril)"
            if 'PERF' in f:
                return "Sana / ona kesin olarak gösterdik ve görünür kıldık (IV. bab mâzî fiil, 1. çoğul)"
            if '1S' in f:
                return "Size göstereceğim / kendi görüşümü sunuyorum (IV. bab muzâri fiil, 1. tekil)"
            if '1P' in f:
                if 'SUBJ' in f:
                    return "Sana / ona belgelerimizi göstermek için (IV. bab muzâri mansûb fiil, 1. çoğul)"
                return "Gösteririz / kesinlikle göstereceğiz (IV. bab muzâri fiil, 1. çoğul)"
            if '2MS' in f:
                return "Eğer bana göstereceksen (IV. bab tekitli muzâri fiil, 2. tekil eril)"
            if 'SUBJ' in f:
                return "Size delillerini görünür kılıp göstermek için (IV. bab muzâri mansûb fiil, 3. tekil eril)"
            return "Size / onlara ayetlerini ve sonucu gösteriyor / gösterecektir (IV. bab muzâri fiil, 3. tekil eril)"
        elif lemma == 'ra\'aA':
            if (s, a) in [(3, 152), (8, 43), (79, 20)]:
                return "Size / sana / ona açıkça gösterdi (ettirgen anlamlı geçmiş zaman fiil, 3. tekil eril)"
            if 'PASS' in f:
                return "Görülür hale gelecek / başka izi görülmeyecek durumda (I. bab edilgen muzâri mansûb fiil, 3. tekil eril)"
            if 'PERF' in f:
                if (s, a) in {
                    (6, 40), (6, 46), (6, 47), (10, 50), (10, 59), (11, 28), (11, 63), (11, 88),
                    (17, 62), (18, 63), (19, 77), (25, 43), (26, 75), (26, 205), (28, 71), (28, 72),
                    (35, 40), (39, 38), (41, 52), (45, 23), (46, 4), (46, 10), (53, 19), (53, 33),
                    (56, 58), (56, 63), (56, 68), (56, 71), (67, 28), (67, 30), (96, 9), (96, 11),
                    (96, 13), (107, 1),
                }:
                    if '2MP' in f:
                        return "Hiç görüp düşündünüz mü / ne dersiniz? (I. bab soru-muhasebe mâzî fiil, 2. çoğul eril)"
                    return "Hiç görüp değerlendirdin mi? (I. bab soru-muhasebe mâzî fiil, 2. tekil eril)"
                if '1S' in f:
                    return "Ben kesinlikle gördüm / müşahede ettim (I. bab mâzî fiil, 1. tekil)"
                if '2MS' in f:
                    return "Sen gördün / müşahede ettin (I. bab mâzî fiil, 2. tekil eril)"
                if '2MP' in f:
                    return "Siz gördünüz / gözlerinizle tanık oldunuz (I. bab mâzî fiil, 2. çoğul eril)"
                if '3MS' in f:
                    return "Gördü / duyusal veya zihinsel olarak fark edip kavradı (I. bab mâzî fiil, 3. tekil eril)"
                if '3FS' in f:
                    return "O (dişil özne) gördü / karşılaştı (I. bab mâzî fiil, 3. tekil dişil)"
                if '3FP' in f:
                    return "Onlar (dişil özne) gördüler (I. bab mâzî fiil, 3. çoğul dişil)"
                return "Onlar gördüler / olayla yüz yüze geldiler (I. bab mâzî fiil, 3. çoğul eril)"
            if '1S' in f:
                if 'SUBJ' in f:
                    return "Görüyorum / kendimi görüyorum (I. bab muzâri mansûb fiil, 1. tekil)"
                return "Ben görüyorum / kanaatimce böyle değerlendiriyorum (I. bab muzâri fiil, 1. tekil)"
            if '1P' in f:
                if 'SUBJ' in f:
                    return "Açıkça görmedikçe / seni yalnızca şöyle görüyoruz (I. bab muzâri mansûb fiil, 1. çoğul)"
                return "Biz görüyoruz / değerlendiriyoruz (I. bab muzâri fiil, 1. çoğul)"
            if '2FS' in f:
                return "İnsanlardan kimi görürsen (I. bab tekitli muzâri fiil, 2. tekil dişil)"
            if '2MS' in f:
                if 'JUS' in f:
                    return "Görmedin mi / akıl gözüyle fark etmiyor musun? (I. bab muzâri meczûm fiil, 2. tekil eril)"
                if 'SUBJ' in f:
                    return "Beni duyusal olarak asla göremeyeceksin (I. bab muzâri mansûb fiil, 2. tekil eril)"
                return "Görürsün / gözlemlersin (I. bab muzâri fiil, 2. tekil eril)"
            if '2MP' in f:
                if 'JUS' in f:
                    return "Görmediniz mi / görmüyorsunuz (I. bab muzâri meczûm fiil, 2. çoğul eril)"
                return "Siz görüyorsunuz / fark ediyorsunuz (I. bab muzâri fiil, 2. çoğul eril)"
            if '3FS' in f:
                if 'JUS' in f:
                    return "Görmüyor musun / dikkat etmedin mi? (I. bab muzâri meczûm kipi)"
                return "Görür / gözlemlersin (I. bab muzâri fiil)"
            if '3MP' in f:
                if 'JUS' in f:
                    return "Hiç görmüyorlar mı / görmediler mi? (I. bab muzâri meczûm fiil, 3. çoğul eril)"
                if 'SUBJ' in f:
                    return "Acı sonucu görünceye kadar / görmezler (I. bab muzâri mansûb fiil, 3. çoğul eril)"
                return "Onlar görüyorlar / değerlendiriyorlar (I. bab muzâri fiil, 3. çoğul eril)"
            if 'JUS' in f:
                return "Görmedi mi / hiç fark etmedi mi? (I. bab muzâri meczûm fiil, 3. tekil eril)"
            if 'SUBJ' in f:
                return "Yapıp ettiklerinizi görecektir / görüyor (I. bab muzâri mansûb fiil, 3. tekil eril)"
            return "Görür / her şeyi izler ve değerlendirir (I. bab muzâri fiil, 3. tekil eril)"

    elif root_ar == 'ك-ت-ب':
        if lemma == "kaAtib":
            if 'ADJ' in f:
                return "Eylemleri eksiksiz kayda geçiren yazıcı güçler (çoğul eril etken ortaç sıfat, mansûb)"
            if 'MP' in f:
                return "Biz çabasını kayda geçirenleriz (çoğul eril etken ortaç isim, merfû)"
            if 'ACC' in f:
                return "Sözleşmeyi kayıt altına alacak bir yazıcı / kâtip (tekil belirsiz eril etken ortaç, mansûb)"
            return "Aranızda adaletle yazacak tarafsız bir yazıcı / kâtip (tekil belirsiz eril etken ortaç, merfû)"
        elif lemma == "kaAtibu":
            return "Kendileriyle karşılıklı özgürlük sözleşmesi yazıp imzalayın (III. bab emir fiil, 2. çoğul eril)"
        elif lemma == "{kotataba":
            return "Kendi adına yazdırıp kopyalattı iddiası (VIII. bab mâzî fiil, 3. tekil eril)"
        elif lemma == "makotuwb":
            return "Kendi kayıtlarında açıkça yazılı olarak buldukları (edilgen ortaç isim, tekil eril mansûb)"
        elif lemma == "kita`biY":
            return "Bu mektubumu / yazılı resmi belgemi (1. tekil iyelik ekiyle isim, mecrûr)"
        elif lemma == "kita`b":
            if 'MP' in f:
                if 'NOM' in f:
                    return "Dosdoğru hükümler içeren yazılı belgeler / kitaplar (çoğul isim, merfû)"
                return "Önceki yazılı kitapların / kayıt tomarlarının (çoğul isim, mecrûr)"
            if 'ACC' in f:
                if 'INDEF' in f:
                    return "Zamanlanmış ölçülü bir yasa, kayıt veya belirlenmiş yazılı bir metin (tekil belirsiz eril isim, mansûb)"
                return "Bağlayıcı ilke kitabını, kaydı veya eylem sicilini (tekil eril isim, mansûb)"
            if 'GEN' in f:
                if 'INDEF' in f:
                    return "Açık veya korunmuş bir kayıt sisteminin / belgenin (tekil belirsiz eril isim, mecrûr)"
                return "Ana ilke kitabının, yazılı hukuk kaynağının veya defterin (tekil eril isim, mecrûr)"
            if 'INDEF' in f:
                return "Yol gösterici ve doğrulayıcı yazılı bir kitap / belirlenmiş yazılı vade (tekil belirsiz eril isim, merfû)"
            return "İçinde çelişki bulunmayan temel rehber kitap veya konulan defter (tekil eril isim, merfû)"
        elif lemma == "kataba":
            if 'PASS' in f:
                if 'IMPF' in f:
                    return "İddiaları ve tanıklıkları kesinlikle kayda geçirilip yazılacaktır (I. bab edilgen muzâri fiil, 3. tekil dişil)"
                return "Bağlayıcı sorumluluk ve yasa olarak konuldu / lehlerine hak kaydedildi (I. bab edilgen mâzî fiil, 3. tekil eril)"
            if 'IMPV' in f:
                if '2MP' in f:
                    return "Sözleşmeyi ve süresini hemen yazıya dökün (I. bab emir fiil, 2. çoğul eril)"
                return "Bizi tanıklarla birlikte yaz veya lehimize iyilik kaydet (I. bab emir fiil, 2. tekil eril)"
            if 'PERF' in f:
                if '1P' in f:
                    return "Bağlayıcı ilke olarak yazdık ve kayda geçirdik (I. bab mâzî fiil, 1. çoğul)"
                if '2MS' in f:
                    return "Sen üzerimize bağlayıcı sorumluluk yazdın (I. bab mâzî fiil, 2. tekil eril)"
                if '3FS' in f:
                    return "Ellerinin uydurup yazdığı şeyler (I. bab mâzî fiil, 3. tekil dişil)"
                return "Kendi ilkesine yazdı / bağlayıcı hüküm veya nasip olarak kaydetti (I. bab mâzî fiil, 3. tekil eril)"
            if '1S' in f:
                return "Koruyucu şefkatimi onlar için kesinlikle yazacağım (I. bab muzâri fiil, 1. tekil)"
            if '1P' in f:
                return "Sözlerini ve izlerini eksiksiz yazıp kaydediyoruz / yazacağız (I. bab muzâri fiil, 1. çoğul)"
            if '2MP' in f:
                return "Küçük büyük demeden yazmanız / sözleşmeyi belgelemeniz (I. bab muzâri mansûb fiil, 2. çoğul eril)"
            if '3MP' in f:
                return "Kendi elleriyle uydurup yazarlar / planlarını gizlice kayda alırlar (I. bab muzâri fiil, 3. çoğul eril)"
            if 'JUS' in f:
                return "Aranızdan biri adaletle yazsın, yazmaktan kaçınmasın (I. bab muzâri meczûm fiil, 3. tekil eril)"
            if 'SUBJ' in f:
                return "Adaletle yazmayı kabul etsin / yerine getirsin (I. bab muzâri mansûb fiil, 3. tekil eril)"
            return "Söylenenleri ve yapılanları eksiksiz yazıp kayda geçirir (I. bab muzâri fiil, 3. tekil eril)"

    elif root_ar == 'ه-د-ي':
        if lemma == ">ahodaY`":
            if 'ACC' in f:
                return "Doğrultu ve gidişat bakımından daha isabetli / daha doğru yol gösteren (üstünlük ismi, tekil eril mansûb)"
            if 'GEN' in f:
                return "Öncekilerin üzerinde bulunduğundan daha doğru ve isabetli bir doğrultuyla (üstünlük ismi, tekil eril mecrûr)"
            return "Gidişat bakımından daha doğru yolda / daha isabetli kılavuzluk eden (üstünlük ismi, tekil eril merfû)"
        elif lemma == "haAd":
            if 'INDEF' in f:
                return "Yolu gösteren herhangi bir kılavuz / öncü rehber (etken ortaç belirsiz tekil eril isim, mecrûr)"
            if 'GEN' in f:
                return "Körleşmişleri savrulmaktan döndürüp doğruya ulaştıracak bir kılavuz (etken ortaç tekil eril isim, mecrûr; izâfette son yâ düşmüş)"
            return "Güven bağı kuranları doğru doğrultuya ulaştıran kesin kılavuz (etken ortaç tekil eril isim, merfû)"
        elif lemma == "haAdiy":
            if 'INDEF' in f:
                return "Doğru yolu gösteren açık bir kılavuz ve rehber olarak (etken ortaç belirsiz tekil eril isim, mansûb)"
            return "Yoldan sapmışa doğrultuyu gösterecek bir kılavuz (etken ortaç tekil eril isim, mansûb)"
        elif lemma == "ha`diY":
            return "Körleşmişleri sapmalarından çevirip doğrultuya iletecek bir kılavuz (etken ortaç tekil eril isim, mecrûr; son yâ korunmuş)"
        elif lemma == "hadiy~ap":
            if 'INDEF' in f:
                return "Niyet yoklamak ve yakınlık kurmak üzere sunulan diplomatik bir armağanla (belirsiz tekil dişil isim, mecrûr)"
            return "Sunduğunuz kendi hediyenizle ve maddi gösterişinizle (tekil dişil isim, mecrûr)"
        elif lemma == "hadoy":
            if 'INDEF' in f:
                return "Paylaşım ve dayanışma merkezine ulaştırılacak bir ikramlık destek hayvanı olarak (belirsiz tekil eril isim, mansûb)"
            if 'ACC' in f:
                return "Büyük toplanma merkezine dayanışma nişanesi olarak gönderilen ikramlık sunuyu (tekil eril isim, mansûb)"
            if 'GEN' in f:
                return "Kolaya gelen yakınlaşma ve paylaşım ikramının (tekil eril isim, mecrûr)"
            return "Gönderilen paylaşım ve yakınlaşma ikramı belirlenen yerine ulaşıncaya dek (tekil eril isim, merfû)"
        elif lemma == "hudFY":
            if 'INDEF' in f:
                if 'ACC' in f:
                    return "Doğruya ulaştıran bir kılavuzluk ve doğrultu haritası olarak (belirsiz tekil eril mastar isim, mansûb)"
                if 'GEN' in f:
                    return "Bir doğruluk kılavuzluğu ve isabetli yöneliş üzere (belirsiz tekil eril mastar isim, mecrûr)"
                return "Kişiyi doğrultuya ulaştıran temel bir kılavuz ve yol göstericilik (belirsiz tekil eril mastar isim, merfû)"
            if 'ACC' in f:
                return "Temel yol göstericiliği / doğru doğrultu haritasını (belirli/izâfetli tekil eril mastar isim, mansûb)"
            if 'GEN' in f:
                return "Açık doğrultu kılavuzunun / yol göstericiliğin (belirli/izâfetli tekil eril mastar isim, mecrûr)"
            return "Doğru doğrultu ilkesi / yol gösterme sorumluluğu (belirli/izâfetli tekil eril mastar isim, merfû)"
        elif lemma == "muhotadiY":
            return "Kılavuzluğu benimseyip doğru doğrultuyu bulmuş kimse (VIII. bab etken ortaç tekil eril isim, merfû; yâ harfi yazılı)"
        elif lemma == "m~uhotad":
            if 'INDEF' in f:
                return "Doğru doğrultuyu benimseyip bulan kimse (VIII. bab belirsiz etken ortaç tekil eril isim, mecrûr)"
            return "Kılavuzluğu alıp doğru yolu bulan kimse (VIII. bab etken ortaç tekil eril isim, merfû; son yâ düşmüş)"
        elif lemma == "m~uhotaduwn":
            if 'ACC' in f:
                return "Doğru doğrultuyu bulup izinde yürüyen kimseler (VIII. bab etken ortaç çoğul eril isim, mansûb)"
            if 'GEN' in f:
                return "Kılavuzluğu kabul edip doğru doğrultuyu bulanların (VIII. bab etken ortaç çoğul eril isim, mecrûr)"
            return "Gerçekten doğru doğrultuyu bulmuş olanlar (VIII. bab etken ortaç çoğul eril isim, merfû)"
        elif lemma == "{hotadaY`":
            if 'PERF' in f:
                if '1S' in f:
                    return "Eğer doğru doğrultuyu bulduysam (VIII. bab mâzî fiil, 1. tekil)"
                if '2MP' in f:
                    return "Siz kendi doğrultunuzu koruyup doğru yola girdiğinizde (VIII. bab mâzî fiil, 2. çoğul eril)"
                if '3MP' in f:
                    return "Kendi iradeleriyle kılavuzu benimseyip doğru doğrultuyu buldular (VIII. bab mâzî fiil, 3. çoğul eril)"
                return "Kendi seçimiyle doğru doğrultuyu bulup yönünü düzeltirse (VIII. bab mâzî fiil, 3. tekil eril)"
            if '1P' in f:
                return "Biz kendi başımıza bu doğrultuyu bulabilecek durumda değildik (VIII. bab muzâri mansûb fiil, 1. çoğul)"
            if '2MP' in f:
                if 'JUS' in f:
                    return "Böylece doğru doğrultuyu bulup isabete eresiniz (VIII. bab muzâri meczûm fiil, 2. çoğul eril)"
                if 'SUBJ' in f:
                    return "Doğru doğrultuyu bulasınız diye (VIII. bab muzâri mansûb fiil, 2. çoğul eril)"
                return "Siz doğru doğrultuyu bulur ve yönünüzü belirlersiniz (VIII. bab muzâri fiil, 2. çoğul eril)"
            if '3FS' in f:
                return "Doğru doğrultuyu fark edip tanıyacak mı? (VIII. bab muzâri fiil, 3. tekil dişil)"
            if '3MP' in f:
                if 'JUS' in f:
                    return "Doğru doğrultuyu bulamadılar / kabul etmediler (VIII. bab muzâri meczûm fiil, 3. çoğul eril)"
                if 'SUBJ' in f:
                    return "Asla kendi iradeleriyle doğru doğrultuya yönelemeyecekler (VIII. bab muzâri mansûb fiil, 3. çoğul eril)"
                return "Kılavuzu izleyip doğru doğrultuyu bulurlar / yönlerini tayin ederler (VIII. bab muzâri fiil, 3. çoğul eril)"
            if (s, a) == (10, 35):
                return "Başkasının yönlendirmesi olmadan kendi kendine doğrultuyu bulup yola giremez (VIII. bab muzâri fiil, 3. tekil eril; idgamlı يَهِدِّىٓ)"
            return "Kendi tercihiyle doğru doğrultuyu bulur ve izler (VIII. bab muzâri fiil, 3. tekil eril)"
        elif lemma == "hadaY":
            if 'PASS' in f:
                if 'IMPF' in f:
                    return "Başkası tarafından yöneltilip doğru doğrultuya götürülmedikçe (I. bab edilgen muzâri mansûb fiil, 3. tekil eril)"
                if '3MP' in f:
                    return "Güzel söze ve övülmeye layık ana doğrultuya ulaştırıldılar (I. bab edilgen mâzî fiil, 3. çoğul eril)"
                return "Dosdoğru ana doğrultuya kesin olarak ulaştırılmış olur (I. bab edilgen mâzî fiil, 3. tekil eril)"
            if 'IMPV' in f:
                if '2MP' in f:
                    return "Onları hak ettikleri yakıcı yıkım yolunun önüne katıp götürün (I. bab emir fiil, 2. çoğul eril; kinayeli kullanım)"
                return "Bizi dosdoğru ana doğrultuya yönelt ve ulaştır (I. bab emir fiil, 2. tekil eril)"
            if 'PERF' in f:
                if '1P' in f:
                    return "Onlara iki yolu da gösterdik / açıkça doğrultuya ulaştırdık (I. bab mâzî fiil, 1. çoğul)"
                if '2MS' in f:
                    return "Bize doğru doğrultuyu gösterip kalplerimizi oturttuktan sonra (I. bab mâzî fiil, 2. tekil eril)"
                return "Yol gösterdi, her varlığa yaratılış doğrultusunu verdi / hedefe ulaştırdı (I. bab mâzî fiil, 3. tekil eril)"
            if '1P' in f:
                return "Onlara yollarımızı kesinlikle göstereceğiz / dilediğimizi doğruya eriştiriyoruz (I. bab muzâri fiil, 1. çoğul)"
            if '1S' in f:
                if 'JUS' in f:
                    return "Seni dosdoğru, esenlikli doğrultuya iletip kılavuzlayayım (I. bab muzâri meczûm fiil, 1. tekil)"
                if 'SUBJ' in f:
                    return "Sana Rabbine giden yolu göstereyim (I. bab muzâri mansûb fiil, 1. tekil)"
                return "Size ancak doğruluk ve isabet yolunu gösteriyorum (I. bab muzâri fiil, 1. tekil)"
            if '2MP' in f:
                return "Başkasının saptırdığı kimseleri doğru doğrultuya mı iletmek istiyorsunuz? (I. bab muzâri mansûb fiil, 2. çoğul eril)"
            if '2MS' in f:
                return "Doğru doğrultuya kılavuzluk edip işaret edersin (I. bab muzâri fiil, 2. tekil eril)"
            if '3FS' in f:
                return "Sen içsel kılavuzlukla sevdiğini doğrudan hedefe erdiremezsin (I. bab muzâri, hitaben 2. tekil eril; korpus kodlamasında 3FS)"
            if '3MP' in f:
                return "Hak ile yol gösterip doğru doğrultuya kılavuzluk ederler (I. bab muzâri fiil, 3. çoğul eril)"
            if 'JUS' in f:
                return "Doğru doğrultuya iletmez / yolunu açmadı mı? (I. bab muzâri meczûm fiil, 3. tekil eril)"
            if 'SUBJ' in f:
                return "Size doğru doğrultuyu göstermek ve hedefe ulaştırmak için (I. bab muzâri mansûb fiil, 3. tekil eril)"
            if (s, a) == (22, 4):
                return "Onu yakıcı yıkım azabının yoluna sevk eder ve sürükler (I. bab muzâri fiil, 3. tekil eril; kinayeli kullanım)"
            return "Kendi yöntemiyle doğru doğrultuya kılavuzluk eder ve hedefe ulaştırır (I. bab muzâri fiil, 3. tekil eril)"

    elif root_ar == 'ظ-ل-م':
        if lemma == ">aZolam":
            if 'ACC' in f:
                return "Doğruluktan daha fazla sapmış ve koyu karanlığa gömülmüş / daha haksız (üstünlük ismi, tekil eril mansûb)"
            return "Hakikati örten ve gerçeği yerinden edenden daha haksız kimdir? (üstünlük ismi, tekil eril merfû)"
        elif lemma == ">aZolama":
            return "Üzerlerine zifiri karanlık çöküp aydınlık kesilince (IV. bab mâzî fiil, 3. tekil eril)"
        elif lemma == "ZaAlim":
            if 'ADJ' in f:
                if 'MP' not in f:
                    return "Halkı hakkı çiğneyen ve dengeyi bozan yönetici zümre / belde (etken ortaç tekil eril sıfat, mecrûr)"
                if 'ACC' in f:
                    return "Sınırı aşan ve gerçeği yerinden eden hak çiğneyicileri (etken ortaç çoğul eril sıfat, mansûb)"
                if 'GEN' in f:
                    return "Dengeyi bozan ve başkalarına yazık eden hak çiğneyicilerin (etken ortaç çoğul eril sıfat, mecrûr)"
                return "Sadece hak ve denge ölçüsünü çiğneyen topluluk (etken ortaç çoğul eril sıfat, merfû)"
            if 'MP' in f:
                if 'ACC' in f:
                    return "Başkasına veya kendi özüne yazık edip dengeyi bozanları (etken ortaç çoğul eril isim, mansûb)"
                if 'GEN' in f:
                    return "Sınır tanımayıp gerçeği yerinden eden hak çiğneyicilerin (etken ortaç çoğul eril isim, mecrûr)"
                return "Bilerek hakkı eksilten ve kendini karartan haksızlık failleri (etken ortaç çoğul eril isim, merfû)"
            if 'INDEF' in f:
                return "Kendi özüne yazık eden / emaneti sarsan kimse (etken ortaç belirsiz tekil eril isim, merfû)"
            return "Gerçeği yerinden edip pişmanlıktan ellerini ısıran hak çiğneyici (etken ortaç tekil eril isim, merfû)"
        elif lemma == "ZaAlimap":
            if 'ACC' in f:
                return "Halkının hak ve adalet dengesini çürüttüğü kent (etken ortaç belirsiz tekil dişil isim, mansûb)"
            return "İç düzeni haksızlık ve baskıyla kararmış şehir (etken ortaç belirsiz tekil dişil isim, merfû)"
        elif lemma == "ZaAlimiY^":
            if 'ACC' in f:
                return "Çıkış imkanı varken geri kalıp kendi kendilerine yazık edenler halinde (çoğul etken ortaç isim, izâfetle nûn düşmüş, mansûb)"
            return "Yaşam tercihleriyle kendi özlerine yazık etmiş kimseler olarak (çoğul etken ortaç isim, izâfetle nûn düşmüş, mecrûr)"
        elif lemma == "Zal~a`m":
            return "Varlıklara ve insanlara asla en ufak haksızlık edici değildir (mübalağa فَعَّال kalıbı, belirsiz tekil eril isim, mecrûr)"
        elif lemma == "Zaluwm":
            if 'ACC' in f:
                return "Üstlendiği büyük emanetin dengesini kolayca bozabilen çok haksız ve aceleci (mübalağa فَعُول kalıbı, belirsiz tekil eril isim, mansûb)"
            return "Verilen nimetler karşısında nankörlük edip sınırı aşırı çiğneyen (mübalağa فَعُول kalıbı, belirsiz tekil eril isim, merfû)"
        elif lemma == "Zulom":
            if 'INDEF' in f:
                if 'ACC' in f:
                    return "Haksız yere, dengeyi bozarak / herhangi bir haksızlık olarak (belirsiz tekil eril isim, mansûb)"
                if 'GEN' in f:
                    return "Yaptıkları büyük haksızlık sebebiyle veya güvene katılan haksızlıkla (belirsiz tekil eril isim, mecrûr)"
                return "Bir şeyi ait olmadığı yere koymak olan ağır bir haksızlıktır (belirsiz tekil eril isim, merfû)"
            if 'ACC' in f:
                return "Bugün hiç kimseye en ufak hak kaybı / haksızlık yoktur (tekil eril isim, mansûb)"
            return "Yaptıkları haksızlığın / dengesizliğin (tekil eril isim, mecrûr)"
        elif lemma == "Zuluma`t":
            if 'ADJ' in f:
                return "Birbiri üstüne yığılmış katman katman karanlıklar (çoğul dişil belirsiz sıfat, merfû)"
            if 'INDEF' in f:
                if 'NOM' in f:
                    return "Göz gözü görmeyen yoğun karanlıklar (belirsiz çoğul dişil isim, merfû)"
                return "Üç aşamalı ana rahmi karanlığı, derin deniz veya belirsiz karanlıklar içinde (belirsiz çoğul dişil isim, mecrûr)"
            if 'ACC' in f:
                return "Karanlıkları ve tek aydınlığı var etti (çoğul dişil isim, mansûb)"
            if 'NOM' in f:
                return "Katmanlı karanlıklar ile tek aydınlık bir olmaz (çoğul dişil isim, merfû)"
            return "Parçalı karanlıkların içinden tek aydınlığa doğru (çoğul dişil isim, mecrûr)"
        elif lemma == "maZoluwm":
            return "Haksız yere canına kıyılmış, hakkı çiğnenmiş mağdur kimse (edilgen ortaç belirsiz tekil eril isim, mansûb)"
        elif lemma == "muZolim":
            if 'MP' in f:
                return "Gündüz çekildiğinde ansızın koyu karanlıkta kalıverirler (IV. bab etken ortaç çoğul eril isim, merfû)"
            return "Zifiri karanlık basmış bir gece parçasıyla örtülü (IV. bab etken ortaç belirsiz tekil eril isim, mansûb)"
        elif lemma == "Zalama":
            if 'PASS' in f:
                if 'PERF' in f:
                    if '3MP' in f:
                        return "Haksızlığa ve baskıya uğratıldılar (I. bab edilgen mâzî fiil, 3. çoğul eril)"
                    return "Haklı olarak haksızlığa uğradığını açıkça duyuran (I. bab edilgen mâzî fiil, 3. tekil eril)"
                if '2MP' in f:
                    return "Emeğinizden ve ana sermayenizden asla haksızlığa uğratılmazsınız (I. bab edilgen muzâri meczûm fiil, 2. çoğul eril)"
                if 'JUS' in f:
                    return "Zerre kadar hak kaybına / haksızlığa uğratılmazlar (I. bab edilgen muzâri meczûm fiil, 3. çoğul eril)"
                return "Hiçbir hak kaybına ve haksızlığa uğramazlar (I. bab edilgen muzâri fiil, 3. çoğul eril)"
            if 'PERF' in f:
                if '1P' in f:
                    return "Kendi özümüze yazık ettik / biz onlara haksızlık etmedik (I. bab mâzî fiil, 1. çoğul)"
                if '1S' in f:
                    return "Gerçekten kendi kendime haksızlık / yazık ettim (I. bab mâzî fiil, 1. tekil)"
                if '2MP' in f:
                    return "Kendi özünüze haksızlık ettiniz (I. bab mâzî fiil, 2. çoğul eril)"
                if '3FS' in f:
                    return "Haksızlık işlemiş olan her kişi (I. bab mâzî fiil, 3. tekil dişil)"
                if '3MP' in f:
                    return "Gerçeği yerinden ederek kendi özlerine yazık ettiler (I. bab mâzî fiil, 3. çoğul eril)"
                return "Sınırı aşıp kendine yazık etti / adalet ilkesi kimseye haksızlık etmedi (I. bab mâzî fiil, 3. tekil eril)"
            if '2MP' in f:
                if 'JUS' in f:
                    return "Bu ölçüler içinde kendi kendinize sakın haksızlık etmeyin (I. bab muzâri meczûm fiil, 2. çoğul eril)"
                return "Kimseye haksızlık etmezsiniz (I. bab muzâri fiil, 2. çoğul eril)"
            if '3FS' in f:
                if (s, a) == (18, 33):
                    return "İki bahçe de ürününden hiçbir şey eksiltmedi (I. bab etken muzâri meczûm fiil, 3. tekil dişil; eksiltme anlamı)"
                return "Hiçbir kimse zerre kadar haksızlığa uğratılmaz (edilgen çekimli muzâri merfû fiil, 3. tekil dişil; korpus kodlamasında 3FS|JUS)"
            if '3MP' in f:
                return "Sadece kendi kendilerine yazık edip haksızlıkta direnirler (I. bab muzâri fiil, 3. çoğul eril)"
            if 'JUS' in f:
                return "Kendi özüne yazık ederse / içinizden kim haksızlık yaparsa (I. bab muzâri meczûm fiil, 3. tekil eril)"
            if 'SUBJ' in f:
                return "Onlara asla haksızlık edecek değildi (I. bab muzâri mansûb fiil, 3. tekil eril)"
            return "Zerre ağırlığınca dahi haksızlık etmez (I. bab muzâri fiil, 3. tekil eril)"

    elif root_ar == 'ن-ف-س':
        if lemma == "mutana`fisuwn":
            return "Değerli ve kalıcı olana kavuşmak için soluk soluğa yarışanlar (VI. bab etken ortaç çoğul eril isim, merfû)"
        elif lemma == "tanaf~asa":
            return "Gecenin basıncı dağılırken sabahın nefes alıp aydınlığa açıldığı an (V. bab mâzî fiil, 3. tekil eril)"
        elif lemma == "yatanaAfasi":
            return "Artık kalıcı ve değerli olan bu hedef uğruna yarışa girsinler (VI. bab muzâri meczûm talep fiili, 3. tekil eril)"
        elif lemma == "nafos":
            if 'FP' in f:
                if (s, a) == (17, 25):
                    return "İç dünyanızda ve gönüllerinizde saklı olanların (فُعُول çokluk kırık çoğulu dişil isim, mecrûr)"
                if (s, a) == (81, 7):
                    return "Bütün canlılar ve bireysel benlikler eşleştirilip kümelendiğinde (فُعُول çokluk kırık çoğulu dişil isim, merfû)"
                if 'ACC' in f:
                    return "Kendi benliklerini, kendi canlarını veya kendi varlıklarını (أَفْعُل kırık çoğulu dişil isim, mansûb)"
                if 'GEN' in f:
                    return "Kendi kendilerine, canları ve iç dünyaları bakımından (أَفْعُل kırık çoğulu dişil isim, mecrûr)"
                return "İç dünyalarınız veya kendi benlikleriniz (أَفْعُل kırık çoğulu dişil isim, merfû)"
            if 'INDEF' in f:
                if 'ACC' in f:
                    return "Herhangi bir canı, bir kişiyi veya bir kimseyi (belirsiz tekil dişil isim, mansûb)"
                if 'GEN' in f:
                    return "Tek bir candan, herhangi bir kimseden veya bir kişilikten (belirsiz tekil dişil isim, mecrûr)"
                return "Hiçbir kimse, hiçbir can veya her canlı birey (belirsiz tekil dişil isim, merfû)"
            if 'ACC' in f:
                return "Kendi benliğini, canını veya bizzat kendisini (belirli/iyelikli tekil dişil isim, mansûb)"
            if 'GEN' in f:
                return "Kendi benliğinin, iç dünyasının veya kendi lehine/aleyhine (belirli/iyelikli tekil dişil isim, mecrûr)"
            return "Kendi benliği, içsel dürtü merkezi veya huzurlu canlı öz (belirli/iyelikli tekil dişil isim, merfû)"

    elif root_ar == 'ن-ز-ل':
        if lemma == "tanziyl":
            if 'ACC' in f:
                return "Aşama aşama, sindire sindire ve planlı bir düzenle indirişle (II. bab masdar, mansûb / mef'ûl-i mutlak)"
            return "Bölüm bölüm ve ölçülü bir düzenle indirilmiş açıklama/bildirim (II. bab masdar, merfû)"
        elif lemma == "nuzul":
            if 'NOM' in f:
                return "Varılan durakta konuk önüne çıkarılan hazırlanmış karşılama ikramı (tekil isim, merfû)"
            return "Yolculuğun ardından konuk için önceden hazırlanmış ilk ağırlama ve ikram olarak (tekil isim, mansûb)"
        elif lemma == "manaAzil":
            return "Ay'ın gökyüzü yörüngesindeki evreleri ve hesap ölçüsü kılınan konak noktaları (mîm'li mekân kırık çoğul isim, mansûb)"
        elif lemma == "nazolap":
            return "Yukarıdan aşağıya doğru gerçekleşen belirgin bir tek iniş anında (tekil dişil birim ismi فَعْلَة, mansûb)"
        elif lemma == "munziliyn":
            if (s, a) == (12, 59):
                return "Gelen konukları en cömert ve eksiksiz biçimde ağırlayıp yerleştirenlerin (IV. bab etken ortaç çoğul, mecrûr)"
            if (s, a) == (23, 29):
                return "Güvenli ve bereketli konak yerine indirenlerin (IV. bab etken ortaç çoğul, mecrûr)"
            if (s, a) == (56, 69):
                return "Buluttan yaşam suyunu aşağıya yağdıranlar ve indirenler (IV. bab etken ortaç çoğul, merfû)"
            if 'NOM' in f:
                return "Yıkım ve uyarıcı karşılığı yukarıdan indirenler (IV. bab etken ortaç çoğul, merfû)"
            return "Destek veya uyarıcı güç olarak yukarıdan indirenler (IV. bab etken ortaç çoğul, mansûb)"
        elif lemma == "munzal":
            if (s, a) == (23, 29):
                return "Güvenli ve bereketli bir iniş / konaklama yerine (IV. bab mîm'li masdar/ism-i mekân, mansûb)"
            return "Yardım için ardı ardına indirilmiş güçler halinde (IV. bab edilgen ortaç çoğul, mansûb)"
        elif lemma == "munaz~il":
            return "Bunu gökten sofrayla birlikte size kademeli ve kesin olarak indirecek olanım (II. bab etken ortaç, merfû)"
        elif lemma == "munaz~al":
            return "Aşamalı biçimde ve gerçeklik üzere indirilmiş olandır (II. bab edilgen ortaç, merfû)"
        elif lemma == "tanaz~alato":
            if 'PERF' in f:
                return "O bildirimle aşağıya inip yanaştı (V. bab mâzî fiil, 3. tekil dişil)"
            if '1P' in f:
                return "Ancak üstten gelen buyrukla peş peşe ineriz (V. bab muzâri fiil, 1. çoğul)"
            if '3MS' in f:
                return "Kozmik düzen buyruğu katmanlar arasında sürekli inip işler (V. bab muzâri fiil, 3. tekil eril)"
            return "Üstten peş peşe inip kararlı biçimde yerleşirler/üşüşürler (V. bab muzâri fiil, 3. tekil dişil)"
        elif lemma == "nazala":
            if 'IMPF' in f:
                return "Gökten aşağıya sürekli inen ve yeryüzüne ulaşan (I. bab muzâri fiil, 3. tekil eril)"
            return "Doğrudan aşağıya indi, temas edip yerine ulaştı (I. bab mâzî fiil, 3. tekil eril)"
        elif lemma == "naz~ala":
            if 'PASS' in f:
                if 'IMPF' in f:
                    return "Aşama aşama indirilir / belirli aralıklarla gönderilir (II. bab edilgen muzâri fiil, 3. tekil)"
                return "Zaman içinde parça parça ve aşamalı olarak indirildi (II. bab edilgen mâzî fiil, 3. tekil)"
            if 'IMPF' in f:
                if 'SUBJ' in f:
                    return "Aşama aşama indirmesi / göndermesi için (II. bab muzâri mansûb fiil)"
                if 'JUS' in f:
                    return "Hakkında hiçbir kanıt ve yetki indirmediği halde / indirmesin (II. bab muzâri meczûm fiil)"
                return "Ölçülü, dengeli ve aşamalı biçimde indirir (II. bab muzâri fiil, etken)"
            return "Zamana yayarak bölüm bölüm ve pekiştirerek indirdi (II. bab mâzî fiil, etken)"
        elif lemma == ">anzala":
            if 'IMPV' in f:
                return "Güvenle indir / gökten sofra indir (IV. bab emir fiili, 2. tekil eril)"
            if 'PASS' in f:
                if 'IMPF' in f:
                    return "Yukarıdan ölçülü olarak indirilir (IV. bab edilgen muzâri fiil)"
                return "Üst kaynaktan indirildi / ortaya konup ulaştırıldı (IV. bab edilgen mâzî fiil)"
            if 'IMPF' in f:
                return "Yakında ben de benzerini indiririm iddiasında (IV. bab muzâri fiil, 1. tekil)"
            return "Yukarıdan aşağıya doğru yöneltip indirdi / yaşam ya da rehberlik olarak ulaştırdı (IV. bab mâzî fiil, etken)"

    elif root_ar == 'ق-ب-ل':
        if lemma == "qabol":
            if pos == 'T':
                if 'NOM' in f:
                    return "Daha önceki aşamada ve öncesinde (mebnî zaman zarfı, merfû konumda)"
                return "Bundan önceki zaman diliminde veya önceden (zaman zarfı, mansûb)"
            if (s, a) == (30, 4):
                return "Olaylar zincirinin en başından, öncesinden beri (harf-i cer ile mebnî isim, mecrûr konum)"
            return "Senden / onlardan veya bu olaydan önce gelen evrelerden (harf-i cer sonrası mecrûr isim)"
        elif lemma == "taqab~ala":
            if 'PASS' in f:
                if 'IMPF' in f:
                    return "Özenle kabul edilip karşılığı verilir (V. bab edilgen muzâri fiil)"
                return "Sunulan emek ve yaklaşım rıza ile kabul edildi (V. bab edilgen mâzî fiil)"
            if 'IMPV' in f:
                return "Bizden bu hizmeti ve çağrıyı hoşnutlukla kabul buyur (V. bab emir fiili, 2. tekil eril)"
            if 'IMPF' in f:
                return "İçtenlikle sunulanı özenle kabul eder ve karşılığını verir (V. bab muzâri fiil)"
            return "Gönüllü bir özenle kabul edip kucakladı (V. bab mâzî fiil)"
        elif lemma == "yaqobalu":
            if 'PASS' in f:
                if 'SUBJ' in f:
                    return "Kendilerinden hiçbir fidye veya özür kesinlikle kabul edilmez (I. bab edilgen muzâri mansûb fiil)"
                return "Ondan ne bir fidye ne de aracılık kabul edilir (I. bab edilgen muzâri fiil)"
            if 'JUS' in f:
                return "Onların tanıklığını asla geçerli sayıp kabul etmeyin (I. bab muzâri meczûm fiil, 2. çoğul eril)"
            return "İçten geri dönüşü geri çevirmeyip kabul eder (I. bab muzâri fiil, etken)"
        elif lemma == ">aqobala":
            if 'IMPV' in f:
                return "Korkup kaçmayı bırak ve yüzünü dönüp öne gel (IV. bab emir fiili, 2. tekil eril)"
            return "Yüzünü çevirip karşı tarafa doğru yöneldi veya ilerledi (IV. bab mâzî fiil)"
        elif lemma == "qibolap":
            if 'GEN' in f:
                return "Yüzlerini döndükleri ortak odak yönünden (tekil dişil isim, mecrûr)"
            return "Bireylerin veya toplumun yüzünü çevirdiği ortak odak ve yöneliş merkezi (tekil dişil isim, mansûb)"
        elif lemma == "qibal":
            if pos == 'LOC':
                if (s, a) == (2, 177):
                    return "Doğu ve batı yönü tarafına (mekân zarfı, mansûb)"
                return "Senin bulunduğun öne ve karşı tarafa doğru (mekân zarfı, mansûb)"
            if (s, a) == (27, 37):
                return "Karşısında durup direnebilecekleri bir güç ve cephe (tekil eril isim, mansûb)"
            return "Surun ön ve dış cephesi tarafından gelen sonuç (tekil eril isim, mecrûr)"
        elif lemma == "m~utaqa`biliyn":
            return "Karşılıklı olarak birbirinin yüzüne bakışır biçimde oturanlar (VI. bab etken ortaç çoğul eril, mansûb)"
        elif lemma == "qubul":
            if (s, a) == (12, 26):
                return "Gömleğin ön yüzünden ve karşı taraftan (tekil eril isim, mecrûr)"
            return "Doğrudan gözlerinin önünde ve yüz yüze karşıdan (tekil eril isim, mansûb)"
        elif lemma == "qabiyl":
            if 'NOM' in f:
                return "Aynı cephede saf tutan eşlikçi topluluğu ve tayfası (tekil eril isim, merfû)"
            return "Yüz yüze kefil, tanık veya hep birlikte saf tutmuş topluluk halinde (tekil eril isim, mansûb)"
        elif lemma == "qabuwl":
            return "Özenli, gönül alıcı ve güzel bir kucaklayışla / kabul ile (tekil isim, mecrûr)"
        elif lemma == "qaAbil":
            return "Hatadan pişmanlıkla geri dönüşü geri çevirmeyip kabul edenin (I. bab etken ortaç, mecrûr)"
        elif lemma == "m~usotaqobil":
            return "Vadilerine doğru karşıdan ilerleyip sokulmakta olan (X. bab etken ortaç, mansûb)"
        elif lemma == "qabaA^}il":
            return "Birbiriyle yüz yüze gelip tanışan insan boyları ve topluluklar (kırık çoğul isim, mansûb)"

    elif root_ar == 'ذ-ك-ر':
        if lemma == "*akara":
            if 'IMPV' in f:
                if '2MP' in f:
                    return "Zihninizde canlı tutun, anın ve unutmadan dile getirin (I. bab emir fiili, 2. çoğul eril)"
                if '2FS' in f:
                    return "Gerçeği ve nimetleri zihninde canlı tutup an (I. bab emir fiili, 2. tekil dişil)"
                return "Unutmadan hatırla, an ve adını bilinçle gündemde tut (I. bab emir fiili, 2. tekil eril)"
            if 'PASS' in f:
                if 'IMPF' in f:
                    return "Adı açıkça anılır veya anılmasına izin verilir (I. bab edilgen muzâri fiil)"
                return "Yüce ad anıldığı veya tek başına dile getirildiği zaman (I. bab edilgen mâzî fiil)"
            if 'IMPF' in f:
                if 'SUBJ' in f:
                    return "Bilinçle anması ve zihinde canlı tutması için (I. bab muzâri mansûb fiil)"
                if 'JUS' in f:
                    return "Sakın aklından çıkarıp anmasın / adını andığında (I. bab muzâri meczûm fiil)"
                return "Zihninde canlı tutar, anar ve unutulmasına izin vermez (I. bab muzâri fiil, etken)"
            return "Unutmadan aklında tuttu, adını andı veya gündeme getirdi (I. bab mâzî fiil, etken)"
        elif lemma == "*ikor":
            if 'NOM' in f:
                return "Zihni diri tutan canlı anış, uyarıcı bildirim veya kalıcı şan (tekil eril isim, merfû)"
            if 'ACC' in f:
                return "Bilinçli anışı, uyarıcı mesajı veya kalıcı itibarı (tekil eril isim, mansûb)"
            return "Zihinde diri tutulan anış, onurlu ün veya uyarıcı bildirim (tekil eril isim, mecrûr)"
        elif lemma == "ta*ak~ara":
            if 'PERF' in f:
                return "Durup derinlemesine düşündü, ibret alıp bilincini topladı (V. bab mâzî fiil)"
            if 'SUBJ' in f:
                return "İyi düşünsünler, ders çıkarıp bilinçlensinler diye (V. bab muzâri mansûb fiil)"
            if 'JUS' in f:
                return "Belki durup düşünür ve ibret alarak uyanırsın(ız) (V. bab muzâri meczûm fiil)"
            return "Derinlemesine düşünür, ders çıkarır ve bilincini tazeler (V. bab muzâri fiil)"
        elif lemma == "*ikoraY`":
            if 'NOM' in f:
                return "Zihne çakılıp kalan keskin, sarsıcı hatırlatma ve öğüt (tekil dişil isim, merfû)"
            if 'ACC' in f:
                return "Kalbi uyandıran etkili bir öğüt ve kalıcı ibret olarak (tekil dişil isim, mansûb)"
            return "Zihni uyandıran keskin hatırlatma ve ders verici ibret (tekil dişil isim, mecrûr)"
        elif lemma == "*uk~ira":
            if 'PASS' in f:
                if 'IMPF' in f:
                    return "Kendilerine somut biçimde hatırlatılıp uyarılır (II. bab edilgen muzâri fiil)"
                return "Kendilerine tekrar hatırlatıldı, uyarıldı ve bildirildi (II. bab edilgen mâzî fiil)"
            if 'IMPV' in f:
                return "Gerçeği bıkmadan hatırlat ve bilinci diri tut (II. bab emir fiili, 2. tekil eril)"
            if 'IMPF' in f:
                return "Biri unutursa diğeri ona sözleşme gerçeğini hatırlatsın (II. bab muzâri fiil, etken)"
            return "Tekrar tekrar hatırlatıp zihinleri uyardı (II. bab mâzî fiil, etken)"
        elif lemma == "*akar":
            if 'MD' in f:
                return "Çiftleşen iki erkek / eril cins hayvan (ikil eril isim, mansûb)"
            if 'MP' in f:
                if 'NOM' in f:
                    return "Erkek bireyler / erkek evlatlar (kırık çoğul isim, merfû)"
                if 'ACC' in f:
                    return "Erkekleri veya eril evlatları (kırık çoğul isim, mansûb)"
                return "Erkek bireylerden veya oğullardan (kırık çoğul isim, mecrûr)"
            if 'NOM' in f:
                return "Eril cinsiyetteki insan veya canlı birey (tekil eril isim, merfû)"
            if 'ACC' in f:
                return "Erkek veya eril cinsiyeti (tekil eril isim, mansûb)"
            return "Eril cinsiyet ve biyolojik erkeklik açısından (tekil eril isim, mecrûr)"
        elif lemma == "ta*okirap":
            if 'ACC' in f:
                return "Görünce hemen aklı başına getiren somut bir hatırlatma nişanı olarak (tekil dişil isim, mansûb)"
            if 'GEN' in f:
                return "İbret alıp unutulmaması gereken somut uyarıcı belgeden (tekil dişil isim, mecrûr)"
            return "Okundukça zihni uyandıran somut bir hatırlatıcı belge (tekil dişil isim, merfû)"
        elif lemma == "m~ud~akir":
            return "Gafletten uyanıp gerçeği hatırlayacak ve ibret alacak kimse (VIII. bab idgamlı etken ortaç, merfû)"
        elif lemma == "*~a`kiriyn":
            if 'GEN' in f:
                return "Gerçeği düşünüp bilincini diri tutanlar için (I. bab etken ortaç çoğul eril, mecrûr)"
            if 'NOM' in f:
                return "Gerçeği ve kaynağı zihninde canlı tutanlar (I. bab etken ortaç çoğul eril, merfû)"
            return "Zihninde hakikati çokça anıp diri tutan erkekleri (I. bab etken ortaç çoğul eril, mansûb)"
        elif lemma == "ta*okiyr":
            return "Aynı gerçeği tekrar tekrar hatırlatıp zihninizi uyarmam (II. bab masdar, merfû)"
        elif lemma == "{d~akara":
            return "Uzun bir süreden sonra birden hatırlayıp aklına getirdi (VIII. bab idgamlı mâzî fiil)"
        elif lemma == "*~a`kira`t":
            return "Hakikati zihninde çokça anıp bilincini diri tutan kadınları (I. bab etken ortaç çoğul dişil, mansûb)"
        elif lemma == "m~a*okuwr":
            return "Adı anılmaya, kayda geçmeye ve hatırlanmaya değer bir varlık (I. bab edilgen ortaç sıfat, mansûb)"
        elif lemma == "mu*ak~ir":
            return "Baskıcı bir denetçi değil, yalnızca bilinç uyandıran sade bir hatırlatıcı (II. bab etken ortaç, merfû)"

    elif root_ar == 'ح-ق-ق':
        if lemma == "Haq~":
            if pos == 'ADJ':
                if 'INDEF|ACC' in f:
                    return "Sözde değil, eylemle kanıtlanmış gerçek anlamda ve samimiyetle (tekil eril nekre sıfat, mansûb)"
                if 'NOM' in f:
                    return "Gerçeklikle birebir örtüşen, şaşmaz ve asıl olan (tekil eril sıfat, merfû)"
                return "Hak edilmiş ve gerçeklikle tam örtüşen kesin karşılık (tekil eril sıfat, mansûb)"
            if (s, a) in {(6, 141), (17, 26), (30, 38)}:
                return "Hasat edilen üründen ve servetten ihtiyaç sahibine düşen belgeli pay (tekil eril isim + zamir, mansûb)"
            if (s, a) in {(51, 19), (70, 24)}:
                return "Kazancın içinde yoksul ve yoksun için ayrılmış belgeli, sabit pay (tekil eril nekre isim, merfû)"
            if (s, a) == (10, 53) and 'INDEF|NOM' in f:
                return "Soru veya kesin pekiştirmeyle ortaya konan şaşmaz gerçek (tekil eril nekre isim, merfû)"
            if 'NOM' in f:
                if 'INDEF' in f:
                    return "Kesinleşmiş gerçek, şaşmaz söz veya belgelenmiş hak/pay (tekil eril nekre isim, merfû)"
                return "Dış gerçeklikle birebir örtüşen nesnel hakikat, doğru ve haklı konum (tekil eril marife isim, merfû)"
            if 'ACC' in f:
                if 'INDEF' in f:
                    return "Tam bir doğruluk, gerçek bir zorunluluk ve şaşmaz ölçü olarak (tekil eril nekre isim, mansûb)"
                return "Örtüşen sabit gerçeği, adalet ölçüsünü ve hak sahibinin payını (tekil eril isim, mansûb)"
            if 'INDEF' in f:
                return "Gerçek temele, yetkiye ve haklı gerekçeye dayalı olarak (tekil eril nekre isim, mecrûr)"
            return "Ölçülü gerçeklikle, adalet ilkesiyle ve nesnel hakikatten (tekil eril isim, mecrûr)"
        elif lemma == "Haq~a":
            if 'PASS' in f:
                return "Boyun eğip yasaya uyması kendisine kaçınılmaz görev ve doğal kural kılındı (I. bab edilgen mâzî fiil, 3. tekil dişil)"
            if 'IMPF' in f:
                return "Gerçeğin üzerini örtenlerin üzerine doğal yargı sonucunun kesinleşmesi için (I. bab muzâri mansûb fiil, 3. tekil eril)"
            if '3FS' in f:
                return "Verilen karar ve seçilen yolun doğal sonucu kaçınılmaz olarak sabitlenip kesinleşti (I. bab etken mâzî fiil, 3. tekil dişil)"
            return "Söz, yargı veya seçilen yolun sonucu sorumluların üzerine kaçınılmaz biçimde kesinleşti (I. bab etken mâzî fiil, 3. tekil eril)"
        elif lemma == ">aHaq~":
            if 'ACC' in f:
                return "O bilinç ve tutarlılık sözüne herkesten daha layık, daha yetkili ve hak sahibi (ism-i tafdîl, mansûb)"
            return "Karşılaştırmada herkesten daha haklı, daha yetkin, öncelikli ve daha layık (ism-i tafdîl, merfû)"
        elif lemma == "yuHiq~a":
            if 'SUBJ' in f:
                return "Somut olaylarla gerçeği fiilen doğrulayıp sahteyi geçersiz kılmak için (IV. bab etken muzâri mansûb fiil)"
            return "Sözü ve yasasıyla gerçeği dış dünyada bizzat doğrulayıp ayakta tutar (IV. bab etken muzâri fiil)"
        elif lemma == "HaA^q~ap":
            return "Tüm maskeleri düşürüp gerçeği ve karşılığını tartışmasız ortaya döken kesin gerçekleşme saati (I. bab etken ortaç dişil isim, merfû)"
        elif lemma == "{sotaHaq~a":
            if '3MD' in f:
                return "İkisinin de haksızlığa ve sorumluluğa hak kazandığı ortaya çıkarsa (X. bab etken mâzî fiil, 3. ikil eril)"
            return "Hakları çiğnenen ve vebal üzerlerine düşen en yakın mirasçılardan (X. bab etken mâzî fiil, 3. tekil eril)"
        elif lemma == "Haqiyq":
            return "Konumu ve iç tutarlılığı gereği yalnızca gerçeği söylemeye yaraşır ve bununla yükümlü (tekil eril isim, merfû)"

    elif root_ar == 'ك-ذ-ب':
        if lemma == "ka*~aba":
            if 'PASS' in f:
                if 'IMPF' in f:
                    return "Yalancılıkla suçlanır ve sözleriniz geri çevrilirseniz (II. bab edilgen muzâri mansûb fiil, 2. çoğul eril)"
                if '3FS' in f:
                    return "Kendilerinden önceki elçiler ve uyarılar da asılsız ilan edilip yalanlandı (II. bab edilgen mâzî fiil, 3. tekil dişil)"
                if '3MP' in f:
                    return "Kendilerine yalancı damgası vurulup reddedildiler (II. bab edilgen mâzî fiil, 3. çoğul eril)"
                return "Gelen elçi ve mesaj asılsız sayılıp yalanlandı (II. bab edilgen mâzî fiil, 3. tekil eril)"
            if 'IMPF' in f:
                if '2D' in f:
                    return "İkinizin de gözleri önünde duran hangi denge ve nimeti yalanlayabilirsiniz (II. bab etken muzâri fiil, 2. ikil)"
                if 'SUBJ' in f:
                    return "Açık gerçeği ve kanıtı yalanlayıp boşa çıkarmaları için (II. bab etken muzâri mansûb fiil)"
                if '2MP' in f:
                    return "Hangi açık kanıtı ve uyarıyı yalanlayıp görmezden geliyorsunuz (II. bab etken muzâri fiil, 2. çoğul eril)"
                return "Açık kanıtı ve sorumluluğu asılsız sayıp yalanlar(lar) (II. bab etken muzâri fiil)"
            if '3MP' in f or '2MP' in f:
                return "Önyargı ile açık belgeleri ve uyarıları yalanlayıp asılsız saydılar/saydınız (II. bab etken mâzî fiil)"
            return "Karşısına çıkan açık kanıtı ve uyarıyı yalanlayıp asılsız saydı (II. bab etken mâzî fiil)"
        elif lemma == "ka*aba":
            if 'PASS' in f:
                return "Kendilerine verilen sözün boşa çıkıp yanıltıldıklarını sandılar (I. bab edilgen mâzî fiil, 3. çoğul eril)"
            if (s, a) == (53, 11):
                return "Kalp ve bilinç gördüğü açık gerçekliği asla çarpıtmadı (I. bab etken mâzî fiil, 3. tekil eril)"
            if 'IMPF' in f:
                return "Gerçeğe aykırı biçimde yalan söyler ve çarpıtır(lar) (I. bab etken muzâri fiil)"
            if '3FS' in f:
                return "Kanıt karşısında beyanı gerçeğe aykırı çıktı ve yalan söyledi (I. bab etken mâzî fiil, 3. tekil dişil)"
            return "Gerçekliğe ve vicdana aykırı biçimde yalan söyledi (I. bab etken mâzî fiil)"
        elif lemma == "ka*ib":
            if (s, a) == (12, 18):
                return "Üzerine sürülmüş uydurma, sahte ve aldatıcı bir kan iziyle (tekil eril nekre isim, mecrûr)"
            if 'NOM' in f:
                return "Kişinin ürettiği yalan ve gerçek dışı beyanı (tekil eril isim, merfû)"
            if 'GEN' in f:
                return "Gerçek dışı uydurma söz ve çarpıtmaya doğru / yalan üzerine (tekil eril isim, mecrûr)"
            return "Gerçeklikle örtüşmeyen uydurma söz, sahte iddia ve çarpıtmayı (tekil eril isim, mansûb)"
        elif lemma == "ka`*ib":
            if pos == 'ADJ':
                return "Gerçeği çarpıtıp yalan üreten karar merkezi (I. bab etken ortaç sıfat, mecrûr)"
            if (s, a) == (56, 2):
                return "Onun gerçekleşmesini yalanlayıp boşa çıkaracak kimse veya durum (I. bab etken ortaç dişil isim, merfû)"
            if 'MP' in f:
                if 'NOM' in f:
                    return "Gerçek dışı beyanda bulunup olguyu çarpıtan yalancılar (I. bab etken ortaç çoğul eril, merfû)"
                if 'GEN' in f:
                    return "Gerçeği gizleyip sözünü çarpıtan yalancılardan (I. bab etken ortaç çoğul eril, mecrûr)"
                return "Sözü gerçeğe uymayan yalancıları (I. bab etken ortaç çoğul eril, mansûb)"
            if 'ACC' in f:
                return "Yalan söyleyen ve gerçeğe aykırı konuşan bir kimse (I. bab etken ortaç tekil eril, mansûb)"
            return "Kesinlikle gerçek dışı konuşan bir yalancı (I. bab etken ortaç tekil eril, merfû)"
        elif lemma == "m~uka*~ibiyn":
            if 'NOM' in f:
                return "Açık kanıtları ve gerçeği asılsız sayıp reddedenler (II. bab etken ortaç çoğul eril, merfû)"
            if 'ACC' in f:
                return "Uyarıyı ve açık belgeleri yalanlayanları (II. bab etken ortaç çoğul eril, mansûb)"
            return "Gerçeği ve açık belgeleri sürekli yalanlayıp reddeden kimselere (II. bab etken ortaç çoğul eril, mecrûr)"
        elif lemma == "ka*~aAb":
            if pos == 'N' and 'INDEF' not in f:
                return "Şımarıkça alışkanlıkla yalan üreten asıl yalancı (mübalağa ismi, merfû)"
            return "Yalanı ve çarpıtmayı alışkanlık haline getirmiş azılı yalancı (mübalağa sıfatı/ismi, merfû)"
        elif lemma == "ki*~aAb":
            if (s, a) == (78, 35):
                return "İnsanların birbirine yönelttiği yalancılık, boş söz ve itham gerginliğini (II. bab yoğunluk masdarı, mansûb)"
            return "Büyük bir inat ve şiddetle yalanlayarak (II. bab pekiştirmeli masdar, mansûb)"
        elif lemma == "mako*uwb":
            return "Boşa çıkıp kurumamış, yalanlanmayacak gerçek ve kesin söz (I. bab edilgen ortaç, mecrûr)"
        elif lemma == "tako*iyb":
            return "Gerçekleri araştırmadan sürü psikolojisiyle sürekli bir yalanlama halini (II. bab masdar, mecrûr)"

    elif root_ar == 'ج-ي-أ':
        if (s, a) == (19, 23):
            return "Onu hurma ağacının gövdesine doğru zorlayıp sürükledi (anlamca IV. bab ettirgen mâzî fiil, 3. tekil eril; derlem kök ayrımında I. bab ile kodlanır)"
        if lemma == "jaA^'a":
            if 'PASS' in f:
                return "Ağırlığıyla ortaya getirilip huzura çıkarıldı (I. bab edilgen mâzî fiil, 3. tekil eril)"
            if '2FS' in f:
                return "Doğrusu sen hiç beklenmedik, ağır ve şaşırtıcı bir iş ile geldin (I. bab mâzî fiil, 2. tekil dişil)"
            if '3FS' in f:
                return "Ağırlığıyla gelip çattı / kesin biçimde ortaya çıktı (I. bab mâzî fiil, 3. tekil dişil)"
            if '3MP' in f:
                return "Geldiler / ağırlıklı bir sonuçla çıkıp geldiler (I. bab mâzî fiil, 3. çoğul eril)"
            if '2MP' in f:
                return "Geldiniz / bir iş veya sonuçla çıkıp geldiniz (I. bab mâzî fiil, 2. çoğul eril)"
            if '2MS' in f:
                return "Sen geldin / bir durumla çıkageldin (I. bab mâzî fiil, 2. tekil eril)"
            if '1P' in f:
                return "Biz geldik / kesin bir delille huzura vardık (I. bab mâzî fiil, 1. çoğul)"
            if '1S' in f:
                return "Ben geldim / açık bir gerçekle huzura çıktım (I. bab mâzî fiil, 1. tekil)"
            return "Ağırlığıyla gelip vardı / somut bir sonuç veya gerçekle çıkageldi (I. bab mâzî fiil, 3. tekil eril)"

    elif root_ar == 'ع-ب-د':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        if lemma == "Eab~ad":
            return "Bir toplumu zorla boyunduruk altına alıp köleleştirerek çalıştırdın (II. bab ettirgen mâzî fiil, 2. tekil eril)"
        elif lemma == "Ea`bida`t":
            return f"İçtenlikle uyum sağlayıp hizmet ve bağlılık sunan kadınlar (dişil çoğul sıfat, nekre, {irab})"
        elif lemma == "EibaAdat":
            return f"Gönüllü boyun eğiş, emek ve bilinçli hizmet bağlılığı (dişil isim/masdar, {irab})"
        elif lemma == "EaAbid":
            if pos == 'ADJ':
                return f"Bilinçle boyun eğip hizmet ve bağlılık sunan kimseler (etken ortaç sıfat, eril çoğul, {irab})"
            if '|MP|' not in f:
                return f"Bir otoriteye boyun eğip hizmet sunan kimse (tekil etken ortaç isim, nekre, {irab})"
            return f"Bir merkeze boyun eğip hizmet ve bağlılık sunanlar (eril çoğul etken ortaç isim, {irab})"
        elif lemma == "Eabod":
            if (s, a) in {(3, 182), (8, 51), (22, 10), (41, 46), (50, 29)}:
                return f"Evrensel adalet kapsamındaki bütün sorumlulara ve bağımlı çalışanlara (عَبِيد çoğul isim, {irab})"
            if '|MD|' in f:
                return f"Hizmet ve sorumluluk bağıyla bağlı iki kişi (ikil isim, {irab})"
            if '|MP|' in f:
                return f"Bir otorite veya yaşam düzenine bağlı görevliler ve gönüllü hizmetliler (عِبَاد çoğul isim, {irab})"
            indef = ", nekre" if 'INDEF' in f else ", marife"
            return f"Emek üreten bağımlı çalışan, köle veya bilinçli görevli (عَبْد tekil isim{indef}, {irab})"
        elif lemma == "Eabada":
            if 'PASS' in f:
                return "Kendilerine boyun eğilip hizmet sunulan varlıklar/odaklar (I. bab edilgen muzâri fiil, 3. çoğul eril)"
            if 'IMPV' in f:
                pers = "2. çoğul eril" if '2MP' in f else "2. tekil eril"
                return f"Pürüzsüz uyumla boyun eğ ve yalnızca tek kaynağa hizmet et (I. bab emir fiil, {pers})"
            if 'PERF' in f:
                pers_map = {'3MS': '3. tekil eril', '1P': '1. çoğul', '2MP': '2. çoğul eril'}
                pers = next((v for k, v in pers_map.items() if k in f), '3. tekil')
                return f"Geçmişte boyun eğip hizmet etti / bağlılık sundu (I. bab mâzî fiil, {pers})"
            pers_map = {
                '2MP': '2. çoğul eril',
                '3MP': '3. çoğul eril',
                '1S': '1. tekil',
                '1P': '1. çoğul',
                '3MS': '3. tekil eril',
                '2MS': '2. tekil eril',
                '3FS': '3. tekil dişil',
            }
            pers = next((v for k, v in pers_map.items() if k in f), 'muzâri')
            return f"Boyun eğip hizmet eder / bütün emeğiyle bağlanır (I. bab muzâri fiil, {pers})"

    elif root_ar == 'أ-خ-ذ':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'), ('3FP', '3. çoğul dişil'),
            ('3FS', '3. tekil dişil'), ('2FS', '2. tekil dişil'), ('3MS', '3. tekil eril'),
            ('2MS', '2. tekil eril'), ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        mood_note = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == "{t~ixaA*":
            return f"Kendiniz için yapay bir dayanak edinmeniz (VIII. bab masdar, {irab})"
        elif lemma == "mut~axi*":
            if 'FP' in f:
                return f"Kendi seçimiyle kalıcı olarak edinen kadınlar (VIII. bab etken ortaç, dişil çoğul, {irab})"
            if 'MP' in f:
                return f"Kendi seçimiyle kalıcı olarak edinen erkekler (VIII. bab etken ortaç, eril çoğul, {irab})"
            return f"Bir varlığı yardımcı veya dayanak olarak edinen (VIII. bab etken ortaç, tekil, {irab})"
        elif lemma == "A^xi*":
            if 'MP' in f:
                return f"El uzatıp teslim alanlar (I. bab etken ortaç, eril çoğul, {irab})"
            return f"Perçeminden sımsıkı tutup tam kontrol altında bulunduran (I. bab etken ortaç, tekil nekre, {irab})"
        elif lemma == ">axo*":
            if (s, a) == (69, 10):
                return f"Şiddeti artarak katlanan tek darbeli yakalayış (I. bab dişil birlik masdarı, nekre, {irab})"
            if 'INDEF' in f:
                return f"Ağır ve sarsıcı bir tutuş/yakalayış (I. bab masdar, nekre, {irab})"
            return f"Somut alma, haksız ele geçirme veya yıkıcı yakalayış (I. bab masdar, {irab})"
        elif lemma == "yu&aAxi*u":
            return f"Bilinçli ihlal nedeniyle anında yakalayıp sorumlu tutar/tutma (III. bab muzâri fiil, {pers}{mood_note})"
        elif lemma == "{t~axa*a":
            if 'IMPV' in f:
                return f"Kendi yaşamın/düzenin için kalıcı olarak seç ve edin (VIII. bab emir fiil, {pers})"
            if 'PERF' in f:
                return f"Kendine kalıcı bir dayanak, yuva veya taraf edindi (VIII. bab mâzî fiil, {pers})"
            return f"Kendine kalıcı bir dayanak, dost/düşman veya yönlendirici edinir (VIII. bab muzâri fiil, {pers}{mood_note})"
        elif lemma == ">axa*a":
            if 'PASS' in f:
                tense = "mâzî" if 'PERF' in f else "muzâri"
                return f"Tutup yakalanır/alınır veya geri alınır (I. bab edilgen {tense} fiil, {pers}{mood_note})"
            if 'IMPV' in f:
                return f"Sımsıkı tut, teslim al ve yürürlüğe koy (I. bab emir fiil, {pers})"
            if 'PERF' in f:
                return f"Uzandı, alıp teslim tuttu, sözleşmeye bağladı veya yakaladı (I. bab mâzî fiil, {pers})"
            return f"El uzatıp alır, geri alır veya sımsıkı yakalar (I. bab muzâri fiil, {pers}{mood_note})"

    elif root_ar == 'خ-ل-ق':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = ", nekre" if 'INDEF' in f else ""
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'), ('3FP', '3. çoğul dişil'),
            ('3FS', '3. tekil dişil'), ('2FS', '2. tekil dişil'), ('3MS', '3. tekil eril'),
            ('2MS', '2. tekil eril'), ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        mood_note = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == "{xotila`q":
            return f"Yapay kurgu ve asılsız yakıştırma (VIII. bab masdar{indef_note}, {irab})"
        elif lemma == "muxal~aqap":
            return f"Tam ölçüsüne göre biçimlendirilmiş (II. bab edilgen ortaç, dişil{indef_note}, {irab})"
        elif lemma == "xuluq":
            return f"Yerleşik huy, tutum veya köklü karakter yapısı (isim{indef_note}, {irab})"
        elif lemma == "xal~a`q":
            return f"Üstün düzeyde sürekli ölçüp biçimlendiren (mübâlağa sıfatı, {irab})"
        elif lemma == "xala`q":
            return f"Hak edilmiş pay, nasip veya sonuç payı (isim{indef_note}, {irab})"
        elif lemma == "xa`liq":
            if pos == 'ADJ':
                return f"Ölçüp planlayarak biçim verici (etken sıfat, tekil eril, {irab})"
            if 'MP' in f:
                return f"Biçim ve düzen veren tasarımcılar (I. bab etken ortaç, eril çoğul, {irab})"
            return f"Ölçüp tasarlayarak biçim veren (I. bab etken ortaç, tekil eril{indef_note}, {irab})"
        elif lemma == "xaloq":
            return f"Ölçülü tasarım, biçimlendirme veya biçim verilmiş varlıklar (I. bab masdar/isim{indef_note}, {irab})"
        elif lemma == "xalaqa":
            if 'PASS' in f:
                tense = "mâzî" if 'PERF' in f else "muzâri"
                return f"Ölçülüp biçimlendirildi / düzenlenip var edilir (I. bab edilgen {tense} fiil, {pers}{mood_note})"
            if 'PERF' in f:
                return f"Ölçüsünü belirleyip pürüzsüz biçimde tasarladı ve şekillendirdi (I. bab mâzî fiil, {pers})"
            return f"Ölçüp biçimlendirir, düzenler veya zihinde kurgular (I. bab muzâri fiil, {pers}{mood_note})"

    elif root_ar == 'و-ق-ي':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'),
            ('3FP', '3. çoğul dişil'), ('2FP', '2. çoğul dişil'),
            ('3FS', '3. tekil dişil'), ('2FS', '2. tekil dişil'),
            ('3MS', '3. tekil eril'), ('2MS', '2. tekil eril'),
            ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        mood_note = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == "tuqaY`p":
            return f"Baskı altında güvenlik için alınan meşru sakınma tedbiri (dişil nekre isim, {irab})"
        elif lemma == ">atoqaY":
            return f"Zarar ve aşırılıktan en çok sakınan, sorumluluk bilinci en yüksek kişi (üstünlük sıfatı, eril tekil, {irab})"
        elif lemma == "waAq":
            return f"Yaklaşan darbeyi göğüsleyip engelleyen bir koruyucu kalkan (I. bab etken ortaç, eril tekil nekre, {irab})"
        elif lemma == "taqiy~":
            if 'FP' in f:
                return f"Hakkıyla eksiksiz koruma kalkanı kuşanma bilinci (masdar-isim, {irab})"
            return f"Ölçüsüzlükten sakınan, zararlı sapmalara karşı korunaklı ve erdemli kimse (sıfat-isim, tekil nekre, {irab})"
        elif lemma == "taqowaY":
            return f"Benliği ve toplumu zarardan koruyan sorumluluk kalkanı / iç zırh (isim, {irab})"
        elif lemma == "mut~aqiyn":
            return f"Kendini zararlı aşırılıktan koruyup adalet ve sorumluluk kalkanı kuşananlar (VIII. bab etken ortaç, eril çoğul, {irab})"
        elif lemma == "waqaY`":
            if 'PASS' in f:
                return f"Kendi iç açgözlülüğünden / bencil cimriliğinden korunup kalkan altına alınır (I. bab edilgen muzâri fiil, {pers}{mood_note})"
            if 'IMPV' in f:
                return f"Koruyucu kalkan ger, araya zırh koy ve yakıcı zararlı sonuçtan uzak tut (I. bab emir fiil, {pers})"
            if 'PERF' in f:
                return f"Araya koruma kalkanı koyup yaklaşan kötülükten veya yakıcı yıkımdan kurtardı (I. bab mâzî fiil, {pers})"
            return f"Sıcaklık, darbe veya kötü sonuca karşı zırh gibi araya girip korur (I. bab muzâri fiil, {pers}{mood_note})"
        elif lemma == "{t~aqaY`":
            if 'IMPV' in f:
                return f"Kendini zarara karşı koruma altına al, sınırını bil ve sorumluluk kalkanını kuşan (VIII. bab emir fiil, {pers})"
            if 'PERF' in f:
                return f"Araya koruyucu bilinç koydu, zararlı yoldan sakınıp sorumlu davrandı (VIII. bab mâzî fiil, {pers})"
            return f"Zararlı sonuçlara karşı kalkan kurup sakınır, sorumlu ve ölçülü davranır (VIII. bab muzâri fiil, {pers}{mood_note})"

    elif root_ar == 'أ-خ-ر':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'),
            ('3FP', '3. çoğul dişil'), ('2FP', '2. çoğul dişil'),
            ('3FS', '3. tekil dişil'), ('2FS', '2. tekil dişil'),
            ('3MS', '3. tekil eril'), ('2MS', '2. tekil eril'),
            ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        mood_note = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == "musota_#oxiriyn":
            return f"Tarih şeridinde arkadan ve sonradan gelen kuşaklar (X. bab etken ortaç, eril çoğul, {irab})"
        elif lemma == "ta>ax~ara":
            if 'PERF' in f:
                return f"Süreyi uzatıp sonraya kaldı veya geride bıraktı (V. bab mâzî fiil, {pers})"
            return f"İleri atılmak yerine geri çekilir ve geride kalır (V. bab muzâri fiil, {pers}{mood_note})"
        elif lemma == "yasota>oxiru":
            return f"Belirlenmiş süreyi geriye atıp erteleyebilir veya gecikme ister (X. bab muzâri fiil, {pers})"
        elif lemma == ">ax~ara":
            if 'PASS' in f:
                return f"Verilen kesin süre bir an bile ertelenir veya geriye bırakılır (II. bab edilgen muzâri fiil, {pers})"
            if 'IMPV' in f:
                return f"Bize kısa bir ek süre daha ver ve sonucu biraz ertele (II. bab emir fiil, {pers})"
            if 'PERF' in f:
                return f"Belirli bir süreye dek mühlet verdi veya ihmalle sonraya bıraktı (II. bab mâzî fiil, {pers})"
            return f"Belirlenmiş vadeye kadar mühlet verip erteler veya geciktirir (II. bab muzâri fiil, {pers}{mood_note})"
        elif lemma == "A^xar":
            kind = "sıfat" if pos == 'ADJ' else "isim"
            if (s, a) == (3, 153):
                return f"Hareket halindeki topluluğun arka cephesi veya artçı safları (dişil tekil isim, {irab})"
            if 'MD' in f:
                return f"Önceki iki kişinin dışında yer alan diğer iki tanık/kişi (eril ikil isim, {irab})"
            if 'MP' in f:
                return f"Birincilerin ardından gelen öteki / başka kimseler (eril çoğul {kind}, {irab})"
            if 'FP' in f:
                return f"İlk grubun yanındaki diğer / öteki birimler (dişil çoğul {kind}, {irab})"
            if 'FS' in f:
                return f"Birincinin ardından gelen öteki / diğer / ikinci birim (dişil tekil {kind}, {irab})"
            return f"İlk örneğin karşısındaki başka bir örnek veya yeni aşama (eril tekil {kind}, {irab})"
        elif lemma == "A^xir":
            if pos == 'T':
                return f"Gündüzün kapanışı, günün son saati (zaman zarfı, {irab})"
            if pos == 'ADJ':
                if 'FS' in f:
                    return f"Birincinin ardından gelen sonraki kalıcı yerleşim ve aşama (dişil tekil sıfat, {irab})"
                return f"Sürecin sonundaki kapanış ve hesap aşamasına ait olan (eril tekil sıfat, {irab})"
            if 'MP' in f:
                return f"Tarih çizgisinde daha sonra gelen kuşaklar / sonuncular (eril çoğul isim, {irab})"
            if 'FS' in f:
                return f"Yakın ve geçici yaşam evresinin ardından gelen uzun vadeli kalıcı sonuç aşaması (dişil tekil isim, {irab})"
            return f"Başlangıcın karşısındaki son nokta veya son halka (eril tekil isim, {irab})"

    elif root_ar == 'أ-م-ر':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'),
            ('3FP', '3. çoğul dişil'), ('2FP', '2. çoğul dişil'),
            ('3FS', '3. tekil dişil'), ('2FS', '2. tekil dişil'),
            ('3MS', '3. tekil eril'), ('2MS', '2. tekil eril'),
            ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        mood_note = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == "<imor":
            return f"Alışılmış ölçüyü aşan sarsıcı, dehşet verici ve olağanüstü (eril tekil belirsiz sıfat, {irab})"
        elif lemma == ">am~aArap":
            return f"Durmadan ısrarla olumsuza yöneltip dürtükleyen baskıcı yapı (dişil tekil belirsiz mübalağa ismi, {irab})"
        elif lemma == "'aAmiruwn":
            return f"Sağduyulu ve yapıcı değerleri ortak akla yönlendiren öncüler (etken ortaç, eril çoğul, {irab})"
        elif lemma == "ya>otamiru":
            if 'IMPV' in f:
                return f"Taraflar olarak karşılıklı danışıp sağduyuyla ortak bir karar oluşturun (VIII. bab emir fiil, {pers})"
            return f"Kendi aralarında gizlice görüşüp ortak bir suikast kararı bağlarlar (VIII. bab muzâri fiil, {pers})"
        elif lemma == ">amara":
            if 'PASS' in f:
                if 'PERF' in f:
                    return f"Kendisine açıkça yönlendirici bir görev ve sorumluluk verildi (I. bab edilgen mâzî fiil, {pers})"
                return f"Açık bir yönlendirme ve görev talimatı verilir (I. bab edilgen muzâri fiil, {pers}{mood_note})"
            if 'IMPV' in f:
                return f"Yapıcı ve sağduyulu olana yönlendir ve yol göster (I. bab emir fiil, {pers})"
            if 'PERF' in f:
                return f"Belirli bir eylem rotası çizip yönlendirdi veya görev verdi (I. bab mâzî fiil, {pers})"
            return f"Belirli bir yöne ve eylem hattına sevk edip yönlendirir (I. bab muzâri fiil, {pers}{mood_note})"
        elif lemma == ">amor":
            if 'MP' in f:
                return f"Sistemdeki tüm süreçler, olay dosyaları ve yönetim konuları (kırık çoğul isim, {irab})"
            if 'INDEF' in f:
                if 'ACC' in f:
                    return f"Belirli bir yönetim kararını, konuyu veya planlanmış süreci (tekil belirsiz isim, {irab})"
                return f"Ortaya çıkan yeni bir durum, gelişme dosyası veya yönlendirici karar (tekil belirsiz isim, {irab})"
            return f"Sistemin işletim komutu, yönlendirici kararı veya üzerinde durulan süreç (eril tekil isim, {irab})"

    elif root_ar == 'ن-و-س':
        if 'NOM' in f:
            return "Hareketli insanlık toplumu veya kamuoyu öznesi (kırık çoğul isim, merfû)"
        if 'ACC' in f:
            return "Bütün insanlık toplumunu veya insan topluluklarını (kırık çoğul isim, mansûb)"
        return "İnsanlık toplumunun, insanların veya insanlar için (kırık çoğul isim, mecrûr)"

    elif root_ar == 'غ-ف-ر':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'),
            ('3FP', '3. çoğul dişil'), ('2FP', '2. çoğul dişil'),
            ('3FS', '3. tekil dişil'), ('2FS', '2. tekil dişil'),
            ('3MS', '3. tekil eril'), ('2MS', '2. tekil eril'),
            ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        mood_note = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == "guforaAn":
            return f"Tam ve kapsamlı koruyucu örtünü/zırhını dileriz (masdar isim, {irab})"
        elif lemma == "{sotigofaAr":
            return f"Başkası adına koruyucu zırh ve onarım talebi (X. bab eylem adı, {irab})"
        elif lemma == "musotagofiriyn":
            return f"Erken saatlerde uyanık bilinçle koruma ve arınma talep edenler (X. bab etken ortaç, eril çoğul, {irab})"
        elif lemma == "gaAfir":
            if 'MP' in f:
                return f"Kusurları örterek koruyanların en hayırlısı (etken ortaç, eril çoğul, {irab})"
            return f"Hatanın yıpratıcı kuyruğunu koruyucu kalkanla örten (etken ortaç, eril tekil, {irab})"
        elif lemma == "gaf~aAr":
            kind = "mübalağa sıfatı" if pos == 'ADJ' else "mübalağa ismi"
            return f"Defalarca tökezlese de bıkmadan tekrar koruyucu zırh açan ({kind}, eril tekil, {irab})"
        elif lemma == "gafuwr":
            kind = "mübalağa sıfatı" if pos == 'ADJ' else "mübalağa ismi"
            return f"Kusurun utancını ve hasarını sürekli örterek koruyan ({kind}, eril tekil, {irab})"
        elif lemma == "m~agofirap":
            return f"Başın üzerindeki miğfer gibi kusuru örten koruma alanı ve anlayışlı kalkan (dişil tekil isim, {irab})"
        elif lemma == "{sotagofara":
            if 'IMPV' in f:
                return f"Hatayı görüp inadı bırakarak koruyucu onarım zırhı iste (X. bab emir fiil, {pers})"
            if 'PERF' in f:
                return f"Yanlışını fark edip koruma ve arınma talep etti (X. bab mâzî fiil, {pers})"
            return f"İçtenlikle hatasını düzeltip koruyucu örtü ve onarım ister (X. bab muzâri fiil, {pers}{mood_note})"
        elif lemma == "gafara":
            if 'PASS' in f:
                return f"Geçmişteki hatası koruma örtüsü altına alınıp kapatılır (I. bab edilgen muzâri fiil, {pers}{mood_note})"
            if 'IMPV' in f:
                return f"Kusurumuzun üzerine koruyucu zırh geçirip darbeden koru (I. bab emir fiil, {pers})"
            if 'PERF' in f:
                return f"Hatasının üzerini koruyucu kalkanla örterek onardı (I. bab mâzî fiil, {pers})"
            return f"Kusurun zararlı sonucunu koruyucu örtüyle kapatır (I. bab muzâri fiil, {pers}{mood_note})"

    elif root_ar == 'و-ل-ي':
        case_note = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'),
            ('3FP', '3. çoğul dişil'), ('2FP', '2. çoğul dişil'),
            ('3FS', '3. tekil dişil'), ('2FS', '2. tekil dişil'),
            ('3MS', '3. tekil eril'), ('2MS', '2. tekil eril'),
            ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        mood_note = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == 'waliY~':
            indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
            if 'MP' in f:
                return f"Yakından sahip çıkanlar, koruyucu müttefikler ve ittifak ortakları (çoğul isim `أَوْلِيَاء`, {indef_note}{case_note})"
            return f"Bitişik yakın, sırt dayanan dost, koruyucu hami ve arka çıkan (tekil isim `وَلِيّ`, {indef_note}{case_note})"

        elif lemma == 'tawal~aY`':
            if 'IMPV' in f:
                return f"Gerginliği bırakıp oradan çekil / dikkatini başka tarafa yönelt (V. bab emir fiili, {pers})"
            if (s, a) == (28, 24):
                return f"İyilik yaptıktan sonra sakin bir köşeye, gölgeye doğru yönelip çekildi (V. bab mâzî fiil, {pers})"
            if (s, a) == (7, 196):
                return f"Dürüst ve yararlı işler üretenlerin sorumluluğunu yakından sahiplenip üstlenir (V. bab muzâri fiil, {pers}{mood_note})"
            if (s, a) == (24, 11):
                return f"Yalan kampanyasının en ağır payını ve baş sorumluluğunu üstlendi (V. bab mâzî fiil, {pers})"
            if (s, a) == (4, 115):
                return f"Kendi yönelip benimsediği ve bağlandığı yola yüzünü verdi (V. bab mâzî fiil, {pers})"
            if (s, a) == (47, 22):
                return f"Yetkiyi devralıp iş başına geçerseniz veya ilkelerden sırt dönerseniz (V. bab çift yönlü mâzî fiil, {pers})"
            if (s, a) in ((5, 51), (5, 56), (5, 80), (9, 23), (16, 100), (22, 4), (58, 14), (60, 9), (60, 13)):
                if 'PERF' in f:
                    return f"Yakınına çekip dost edindi / ittifak bağıyla sahiplenip omuz verdi (V. bab geçişli mâzî fiil, {pers})"
                return f"Yakınlık kurup yandaş edinir / ittifakla sahiplenir (V. bab geçişli muzâri fiil, {pers}{mood_note})"
            if 'PERF' in f:
                return f"Aradaki bağı çözüp sırtını döndü / geri çekilip uzaklaştı (V. bab mâzî fiil, {pers})"
            return f"Bağını koparıp sırt döner / yüz çevirip uzaklaşır (V. bab muzâri fiil, {pers}{mood_note})"

        elif lemma == 'wal~aY`':
            if 'IMPV' in f:
                return f"Yüzünü ve dikkat odağını belirlenen merkeze çevirip sabitle (II. bab emir fiili, {pers})"
            if (s, a) == (2, 142):
                return f"Onları alıştıkları önceki yöneliş merkezinden döndüren sebep neydi (II. bab mâzî fiil, {pers})"
            if (s, a) == (2, 144):
                return f"Seni hoşnut kalacağın bir yöneliş merkezine mutlaka döndürüp odaklayacağız (II. bab pekiştirmeli muzâri fiil, {pers})"
            if (s, a) in ((2, 115), (2, 177)):
                return f"Yüzünüzü ve yönelişinizi o tarafa çevirirsiniz (II. bab muzâri fiil, {pers}{mood_note})"
            if (s, a) == (4, 115):
                return f"Kişiyi kendi yönelip seçtiği yola çevirip onunla baş başa bırakırız (II. bab meczûm muzâri fiil, {pers})"
            if (s, a) == (6, 129):
                return f"Haksızlık üreten kesimleri birbirinin başına geçirip yakından musallat ederiz (II. bab muzâri fiil, {pers})"
            if (s, a) == (46, 29):
                return f"Dinledikten sonra uyarıcı olarak kendi topluluklarına geri döndüler (II. bab mâzî fiil, {pers})"
            if 'PERF' in f:
                return f"Arkasını çevirip geri döndü / kaçıp uzaklaştı (II. bab mâzî fiil, {pers})"
            return f"Arkasını dönüp geri çekilir / sırtını çevirir (II. bab muzâri fiil, {pers}{mood_note})"

        elif lemma == 'mawolaY`':
            indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
            if (s, a) == (16, 76):
                return f"Sorumluluğu ve bakımı üstlenen hami, yönetici ve sahiplenici (tekil isim `مَوْلَى`, {case_note})"
            if (s, a) == (57, 15):
                return f"Kendi ürettiği acı sonucun yakasını bırakmayıp yanında duracağı barınak (tekil isim `مَوْلَى`, {case_note})"
            return f"İşleri yakından çekip çeviren en yakın hami, destekçi ve sahiplenici otorite (tekil isim `مَوْلَى`, {indef_note}{case_note})"

        elif lemma == '>awolaY`':
            if (s, a) in ((47, 20), (75, 34), (75, 35)):
                return f"Kaçınılmaz sarsıntı artık kapına dayandı, senin için en yakın akıbet budur (ism-i tafdîl uyarı kalıbı `أَوْلَى`, {case_note})"
            if pos == 'ADJ':
                return f"Yakınlık, yetki ve koruma sorumluluğunda herkesten daha öncelikli olan (ism-i tafdîl sıfat `أَوْلَى`, {case_note})"
            return f"Öncelikli bağda daha yakın ve daha çok hak sahibi olan (ism-i tafdîl isim `أَوْلَى`, {case_note})"

        elif lemma in ('mawa`liY', 'mawa`liy'):
            if lemma == 'mawa`liy':
                return f"Aynı değer bağı içinde omuz omuza duran yakın koruyucu kardeş ve yoldaşlar (çoğul isim `مَوَالِي`, {case_note})"
            return f"Kişinin ardında bıraktığı sorumluluk alanını ve mirası devralacak yakın varisler (çoğul isim `مَوَالِي`, {case_note})"

        elif lemma == 'wala`yat':
            if (s, a) == (8, 72):
                return f"Somut göç ve yerleşme bağıyla aktif hale gelen karşılıklı koruma ve destek hukuku (tekil dişil isim `وَلَايَة`, {case_note})"
            return f"Nihai yetki, koruma otoritesi ve mutlak sahiplenme gücü (tekil dişil isim `وَلَايَة`, {case_note})"

        elif lemma == 'muwal~iy':
            return f"Her kesimin kendi yönünü çevirip odaklandığı taraf (II. bab etken ortaç `مُوَلِّيهَا`, {case_note})"

        elif lemma == '>awolaya`n':
            return f"Akrabalık veya hak yakınlığı bakımından en önde duran iki kişi (ikil isim `ٱلْأَوْلَيَانِ`, {case_note})"

        elif lemma == 'yalu':
            return f"Mekân ve sınır bakımından size hemen bitişik en yakın konumda bulunanlar (I. bab muzâri fiil `يَلُونَ`, {pers})"

        elif lemma == 'waAl':
            return f"Araya girip yıkıcı sonucu savabilecek yakın hami ve koruyucu yönetici (I. bab nekre etken ortaç `وَالٍ`, {case_note})"

    elif root_ar == 'ب-ع-د':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim/zarf"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        kind = "sıfat" if pos == 'ADJ' else "isim"
        if lemma == 'baEod':
            if pos == 'T':
                if 'ACC' not in f:
                    if (s, a) in ((2, 181), (8, 6), (13, 37)):
                        return "Bir olay veya açık bilgi ortaya konduktan hemen sonraki kesitte (bitişik zaman zarfı `بَعْدَمَا`)"
                    return "Anlatılan tüm aşamalardan sonra, bunun hemen ardından (kesilmiş zaman zarfı `بَعْدُ`, ötre üzerine mebnî)"
                return "Belirli bir olay, sözleşme veya aşamanın ardından gelen sonraki süreçte (zaman zarfı `بَعْدَ`, mansûb)"
            if (s, a) in ((2, 133), (7, 150), (38, 35), (61, 6)):
                return "Benden sonraki dönemde / benim ardımdan (harf-i cerli mecrûr isim ve 1. tekil iyelik `بَعْدِى`)"
            return f"Belirtilen eşikten, durumdan veya zamandan sonraki evrede (harf-i cerli mecrûr isim `بَعْدِ / بَعْدُ`, {irab})"

        elif lemma == 'baEiyd':
            if (s, a) in ((11, 83), (11, 89), (27, 22), (50, 31)):
                return f"Uzak olmayıp aksine hemen yanı başında duran yakın mesafe (`بِبَعِيدٍ / غَيْرَ بَعِيدٍ`, {indef_note}{irab} {kind})"
            if (s, a) in ((2, 176), (4, 60), (4, 116), (4, 136), (4, 167), (14, 3), (14, 18), (22, 12), (22, 53), (34, 8), (41, 52), (42, 18), (50, 27)):
                return f"Doğru eksenden kopup çok uzağa düşmüş derin savrulma ve yarılma (mecâzi mesafe nitelemesi `بَعِيد`, {indef_note}{irab})"
            return f"Mekân veya zaman bakımından araya geniş boşluk girmiş uzak nokta ({indef_note}{irab} {kind} `بَعِيد`)"

        elif lemma == 'buEod':
            if (s, a) == (43, 38):
                return "Doğu ile batı arasındaki aşılmaz mekân açıklığı ve uzaklığı (tekil tamlamalı isim `بُعْدَ`, mansûb)"
            return "Merkezden ve hayattan tamamen kopup tarihten silinme uzaklığı (nekre mastar/mef'ûl-i mutlak `بُعْدًا`, mansûb)"

        elif lemma == 'baEudato':
            if (s, a) == (9, 42):
                return "Aşılacak yol ve zahmet gözlerinde büyüyüp çok uzak göründü (I. bab `بَعُدَ` mâzî fiil, 3. tekil dişil)"
            return "Yaşam ağından tamamen kopup silindi, uzağa savruldu (I. bab `بَعِدَ` mâzî fiil, 3. tekil dişil)"

        elif lemma == 'muboEaduwn':
            return "Yakıcı sonuçtan güvenli bir mesafe açarak uzağa alınıp korunanlar (IV. bab edilgen ortaç `مُبْعَدُونَ`, eril çoğul merfû)"

        elif lemma == 'ba`Eido':
            return "Konak yerlerimiz ve yolculuklarımız arasındaki mesafeyi aç, aramızı uzaklaştır (III. bab emir fiili `بَاعِدْ`, 2. tekil eril)"

    elif root_ar == 'د-ع-و':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'),
            ('3FP', '3. çoğul dişil'), ('2FP', '2. çoğul dişil'),
            ('3FS', '3. tekil dişil'), ('2FS', '2. tekil dişil'),
            ('3MD', '3. ikil eril'), ('2MD', '2. ikil eril'),
            ('3MS', '3. tekil eril'), ('2MS', '2. tekil eril'),
            ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        mood_note = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == 'daEaA':
            if (s, a) == (2, 186):
                return "Bana doğrudan yönelip seslendiğinde (`دَعَانِ`, I. bab mâzî fiil + 1. tekil nesne zamiri, 3. tekil eril)"
            if 'PASS' in f:
                if 'PERF' in f:
                    return f"Bir merkeze, hükme, tanıklığa veya sofraya çağrıldı (I. bab edilgen mâzî fiil, {pers})"
                return f"Hesaba, paylaşıma, eğilmeye veya açık gerçeğe çağrılır (I. bab edilgen muzâri fiil, {pers}{mood_note})"
            if 'IMPV' in f:
                if (s, a) == (33, 5):
                    return f"Onları kendi öz babalarının adıyla çağırıp künyelendirin (I. bab emir fiili, {pers})"
                if (s, a) == (16, 125):
                    return f"Bilgelikle ve gönle dokunan güzel sözle doğru yola çağır (I. bab emir fiili, {pers})"
                return f"Seslenerek çağır, yönelip iste veya davet et (I. bab emir fiili, {pers})"
            if 'PERF' in f:
                return f"Seslenip yanına çağırdı, adlandırdı veya içtenlikle istedi (I. bab mâzî fiil, {pers})"
            return f"Seslenip kendine çeker, yardım ister, davet eder veya adlandırır (I. bab muzâri fiil, {pers}{mood_note})"

        elif lemma == "duEaA^'":
            if 'MP' in f:
                return f"Kendi öz çocuğuymuş gibi adlandırıp sahiplenilen evlatlıklar (çoğul isim `أَدْعِيَاء`, {irab})"
            return f"Anlamlı yöneliş çağrısı, yardım isteği veya ismiyle sesleniş ({indef_note}tekil isim `دُعَاء`, {irab})"

        elif lemma == 'daEowap':
            return f"Tek bir somut çağrı, içten istek veya yönlendirici davet hamlesi ({indef_note}dişil tekil isim `دَعْوَة`, {irab})"

        elif lemma == 'daEowaY`':
            return f"Ağızdan dökülen kalıcı iddia, son pişmanlık itirafı veya ortak minnet ve övgü seslenişi (tekil isim `دَعْوَى`, {irab})"

        elif lemma == 'daAEiY':
            return f"İnsanları belirli bir yöne veya gerçeğe seslenerek çağıran davetçi ({indef_note}etken ortaç `دَاعِى / الدَّاعِى`, {irab})"

        elif lemma == 'd~aAE':
            return f"Seslenen, içtenlikle yönelip çağrı yapan kimse (kısa yazılışlı etken ortaç `الدَّاعِ`, {irab})"

        elif lemma == 'yad~aEu':
            if (s, a) == (67, 27):
                return "Alayla meydan okuyup hemen gelmesini talep ettiğiniz sonuç (VIII. bab muzâri fiil `تَدَّعُونَ`, 2. çoğul eril)"
            return f"Hak sahibi olarak dileyip kendilerine çekebildikleri her arzu ve nimet (VIII. bab muzâri fiil `يَدَّعُونَ`, {pers})"

    elif root_ar == 'ح-ك-م':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'),
            ('3FP', '3. çoğul dişil'), ('2FP', '2. çoğul dişil'),
            ('3FS', '3. tekil dişil'), ('2FS', '2. tekil dişil'),
            ('3MD', '3. ikil eril'), ('2MD', '2. ikil eril'),
            ('3MS', '3. tekil eril'), ('2MS', '2. tekil eril'),
            ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        mood_note = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == 'Hakiym':
            if (s, a) in ((3, 58), (10, 1), (31, 2), (36, 2), (44, 4)):
                return f"Bozulmaya ve boşluğa kapatılarak tüm parçaları sağlam kilitle kurulmuş metin veya iş sıfatı ({indef_note}eril tekil sıfat `حَكِيم`, {irab})"
            tag_desc = "eril tekil isim" if pos == 'N' else "eril tekil sıfat"
            return f"Her işi ve ölçüyü hata ile taşkınlıktan alıkoyarak yerli yerine sağlam oturtan ({indef_note}{tag_desc} `حَكِيم`, {irab})"

        elif lemma == 'Hakama':
            if (s, a) == (39, 46):
                return "Kulların ayrılığa düştüğü meselelerde son ayrım kararını Sen verirsin (`تَحْكُمُ`, I. bab muzâri fiil, 2. tekil eril; morfoloji dosyasında sehven `3FS` etiketli)"
            if (s, a) == (21, 78):
                return "İkisi tarlaya giren sürünün verdiği zarar konusunda ölçü koyup hüküm veriyorlardı (`يَحْكُمَانِ`, I. bab muzâri fiil, 3. ikil eril)"
            if (s, a) in ((6, 136), (10, 35), (16, 59), (29, 4), (37, 154), (45, 21), (68, 36), (68, 39)):
                return f"Dayanaksız ve keyfî biçimde yargı üretip kural kesiyorlar veya kesiyorsunuz (I. bab muzâri fiil, {pers})"
            if 'IMPV' in f:
                return f"Adalet, denge ve açık gerçek ölçüsüyle aralarında karar ver (I. bab emir fiili, {pers})"
            if 'PERF' in f:
                return f"İnsanlar ve taraflar arasında sınır çizip nihai kararı verdi veya verdiniz (I. bab mâzî fiil, {pers})"
            return f"Anlaşmazlık ve uyuşmazlık alanlarında sınırı belirleyip bağlayıcı karar verir (I. bab muzâri fiil, {pers}{mood_note})"

        elif lemma == 'Hukom':
            if (s, a) == (5, 50) and 'INDEF' not in f:
                return f"Bilgisizliğin ve keyfîliğin kural kesme düzeni ({indef_note}eril tekil isim `حُكْم`, {irab})"
            if (s, a) in ((12, 22), (19, 12), (21, 74), (21, 79), (26, 21), (26, 83), (28, 14)):
                return f"Denge kurma, doğruyla yanlışı ayırma ve isabetli karar üretme olgunluğu ({indef_note}eril tekil isim `حُكْم`, {irab})"
            return f"Keyfiliğe gem vurarak düzeni ve adil sınırı belirleyen kesin ölçü veya karar ({indef_note}eril tekil isim `حُكْم`, {irab})"

        elif lemma == 'Hikomap':
            return f"Bilgi ile aklı birleştirip cehaletten ve savrulmadan alıkoyan sağduyu ve isabetli karar ustalığı ({indef_note}dişil tekil isim `حِكْمَة`, {irab})"

        elif lemma == 'Ha`kimiyn':
            return f"Karar verip hüküm kuran hakemler ve yöneticiler (çoğul etken ortaç `ٱلْحَٰكِمِينَ`, {irab})"

        elif lemma == 'Hakam':
            if (s, a) == (4, 35):
                return f"Eşler arasındaki dağılmayı önleyip uzlaşma zemini arayan tarafsız aile hakemi ({indef_note}eril tekil isim `حَكَم`, {irab})"
            return f"Taraflar arasındaki anlaşmazlığı sonuca bağlayan nihai hakem ({indef_note}eril tekil isim `حَكَم`, {irab})"

        elif lemma == 'yuHak~imu':
            return f"Çekişmeli konuda seni yetkili hakem kılıp karar vermeni istemeleri (II. bab muzâri fiil `يُحَكِّمُ`, {pers}{mood_note})"

        elif lemma == '>uHokimato':
            if 'PASS' in f:
                return "Ayetleri gevşemeye, tutarsızlığa ve bozulmaya kapatılarak sarsılmaz biçimde sağlam kılındı (`أُحْكِمَتْ`, IV. bab edilgen mâzî fiil, 3. tekil dişil)"
            return f"Dış paraziti ayıklayıp kendi işaretlerini sağlamlaştırarak pekiştirir (IV. bab muzâri fiil `يُحْكِمُ`, {pers})"

        elif lemma == '>aHokam':
            return f"Karar kuranların ve adalet ölçüsü koyanların en sağlamı, en üstünü (üstünlük adı `أَحْكَم`, {irab})"

        elif lemma == 'Huk~aAm':
            return f"Toplumda yargı ve dağıtım yetkisini elinde tutan hakimler ve yöneticiler (çoğul sıfat/isim `ٱلْحُكَّامِ`, {irab})"

        elif lemma == 'm~uHokama`t':
            return f"Anlam sınırları kesinleştirilmiş, keyfî yorumla eğilip bükülmeye kapatılmış ana ilkeler (IV. bab edilgen ortaç dişil çoğul sıfat `مُحْكَمَٰت`, {indef_note}{irab})"

        elif lemma == 'yataHaAkamu':
            return f"Karşılıklı olarak davalı biçimde karar ve yargı istemeye başvurmaları (VI. bab muzâri fiil `يَتَحَاكَمُوٓا۟`, {pers}{mood_note})"

        elif lemma == 'm~uHokamap':
            return f"Uygulama sınırı açıkça konmuş, yoruma ve kaçamağa yer bırakmayan kesin bölüm (IV. bab edilgen ortaç dişil tekil isim `مُحْكَمَة`, {indef_note}{irab})"

    elif root_ar == 'م-ل-ك':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'),
            ('3FP', '3. çoğul dişil'), ('2FP', '2. çoğul dişil'),
            ('3FS', '3. tekil dişil'), ('2FS', '2. tekil dişil'),
            ('3MD', '3. ikil eril'), ('2MD', '2. ikil eril'),
            ('3MS', '3. tekil eril'), ('2MS', '2. tekil eril'),
            ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        mood_note = ", mansûb" if 'SUBJ' in f else (", meczûm" if 'JUS' in f else "")
        if lemma == 'malak':
            if 'MP' in f:
                return f"Evrensel düzende buyruk iletip görev yürüten kozmik görevliler ({indef_note}kırık çoğul isim `ٱلْمَلَٰٓئِكَة`, {irab})"
            if 'MD' in f:
                return f"Evrensel görev taşıyan iki kozmik görevli (ikil isim `مَلَكَيْنِ`, {irab})"
            if (s, a) in ((69, 17), (89, 22)):
                return f"Evren düzenini sıra sıra kuşatan kozmik görevliler topluluğu (topluluk tekili isim `ٱلْمَلَكُ`, {irab})"
            if (s, a) == (32, 11):
                return f"Can alma görevini devralan yetkili kozmik görevli (tekil isim `مَلَكُ`, {irab})"
            return f"Evrensel sistemde görev yürüten tekil kozmik görevli ({indef_note}tekil isim `مَلَك`, {irab})"

        elif lemma == 'mulok':
            return f"Tüm sistemi çekip çeviren egemenlik, yönetim gücü ve yetki alanı ({indef_note}eril tekil isim `مُلْك`, {irab})"

        elif lemma == 'malakato':
            if 'PERF' in f:
                if (s, a) == (24, 61):
                    return "Anahtarlarını elinizde tutup yönettiğiniz veya sorumluluğunu üstlendiğiniz evler (`مَلَكْتُم`, I. bab mâzî fiil, 2. çoğul eril)"
                return "Yönetim ve koruma sorumluluğu altına alıp himayenizde bulundurduğunuz kimseler (`مَلَكَتْ`, I. bab mâzî fiil, 3. tekil dişil)"
            if (s, a) == (27, 23):
                return "O topluluğu yönetip düzenini elinde tutan kadın yönetici (`تَمْلِكُهُمْ`, I. bab muzâri fiil, 3. tekil dişil)"
            if (s, a) == (82, 19):
                return "Hiçbir bireyin bir başkasına karşı güç yetirip fayda sağlayamadığı durum (`تَمْلِكُ`, I. bab muzâri fiil, 3. tekil dişil)"
            return f"Güç yetirir, elinde tutar, kontrol edip sahip olur (I. bab muzâri fiil, {pers}{mood_note})"

        elif lemma == 'malik':
            if 'MP' in f:
                return f"Toplumlara yön verip yönetim gücü üstlenen hükümdarlar ve önderler ({indef_note}kırık çoğul isim `ٱلْمُلُوك`, {irab})"
            tag_desc = "eril tekil sıfat" if pos == 'ADJ' else "eril tekil isim"
            return f"Tüm düzeni elinde tutan hükümdar ve mutlak yönetici ({indef_note}{tag_desc} `مَلِك`, {irab})"

        elif lemma == 'malakuwt':
            return f"Gökleri ve yeri saran kapsamlı egemenlik ve yönetim ağı (mübalağa ismi `مَلَكُوت`, {irab})"

        elif lemma == 'ma`lik':
            if 'MP' in f:
                return f"Varlıklar üzerinde fiilen tasarruf ve sahiplik hakkı kullananlar (çoğul etken ortaç `مَٰلِكُونَ`, {irab})"
            return f"Sistemin ve hesap alanının mutlak sahibi, yöneticisi (etken ortaç `مَٰلِك`, {irab})"

        elif lemma == 'm~amoluwk':
            return f"Kendi irade ve tasarruf gücü olmayan, başkasının denetimi altındaki bağımlı kişi (edilgen ortaç `مَّمْلُوكًا`, {indef_note}{irab})"

        elif lemma == 'malok':
            return f"Kendi elimizdeki irade gücümüz, kendi tercih ve yetkimiz (mastar isim `مَلْك`, {irab})"

        elif lemma == 'ma`lik2':
            return f"Yıkım alanının kapısında görev yapan baş nöbetçi (`مَٰلِكُ`, özel görev adı, {irab})"

        elif lemma == 'maliyk':
            return f"Gücü kesintisiz süren sarsılmaz hükümdar ve yönetici (`مَلِيكٍ`, mübalağa sıfat/isim, {indef_note}{irab})"

    elif root_ar == 'ج-ن-ن':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        worldly_gardens = {
            (2, 265), (2, 266), (6, 99), (6, 141), (13, 4), (17, 91),
            (18, 32), (18, 33), (18, 35), (18, 39), (18, 40), (23, 19),
            (25, 8), (26, 57), (26, 134), (26, 147), (34, 15), (34, 16),
            (36, 34), (44, 25), (50, 9), (68, 17), (71, 12), (78, 16),
        }
        adem_gardens = {(2, 35), (7, 19), (7, 22), (7, 27), (20, 117), (20, 121)}
        if lemma == 'jan~ap':
            if (s, a) in adem_gardens:
                return f"İlk insan çiftinin barınıp sınandığı korunaklı ve gölgeli bahçe alanı (özel yer adı `ٱلْجَنَّة`, {irab})"
            if pos == 'PN':
                return f"Gelecek yaşamda iyilikle donatılmış serin, korunaklı esenlik bahçesi (özel yer adı `ٱلْجَنَّة`, {irab})"
            if (s, a) in worldly_gardens:
                if 'FD' in f:
                    if (s, a) == (34, 16) and 'NOM' in f:
                        return "Arim seli sonrası acı yemişli ve ılgınlı hale dönüşen iki çorak bahçe (`جَنَّتَيْنِ`, ikil dişil isim, nesne/mansûb, korpus `NOM` etiketli)"
                    return f"Yeryüzünde yan yana uzanan verimli iki bağ ve meyve bahçesi (ikil dişil isim `جَنَّتَانِ / جَنَّتَيْنِ`, {irab})"
                if 'FP' in f:
                    return f"Sık ağaç yapraklarıyla toprağı örten verimli bağ ve meyve bahçeleri ({indef_note}çoğul dişil isim `جَنَّٰت`, {irab})"
                return f"Ağaçları toprağı örten korunaklı dünyevi meyve ve hurma bahçesi ({indef_note}tekil dişil isim `جَنَّة`, {irab})"
            if (s, a) == (57, 21):
                return f"Eni gökle yerin arası kadar geniş olan korunaklı esenlik bahçesi (`جَنَّةٍ`, belirsiz tekil dişil isim, korpus `FP` etiketli, {irab})"
            if 'FD' in f:
                return f"Karşılık olarak hazırlanan iki ayrı esenlik ve nimet bahçesi (ikil dişil isim `جَنَّتَانِ / جَنَّتَيْنِ`, {irab})"
            if 'FP' in f:
                return f"Altlarından nehirler akan serin ve korunaklı esenlik bahçeleri ({indef_note}çoğul dişil isim `جَنَّٰت`, {irab})"
            return f"Her türlü acı ve zarardan korunmuş yüksek esenlik bahçesi ({indef_note}tekil dişil isim `جَنَّة`, {irab})"

        elif lemma == 'jin~':
            return f"İnsan gözüne örtülü ve duyulara gizli kalan bilinçli varlık topluluğu (`ٱلْجِنّ / جِنّ`, eril topluluk ismi, {irab})"

        elif lemma == 'majonuwn':
            return f"Aklı örtülmüş, zihin dengesini yitirmiş kimse ithamı (edilgen ortaç sıfat/isim `مَجْنُون`, {indef_note}{irab})"

        elif lemma == 'jin~ap':
            if 'INDEF' in f:
                return f"Aklın örtülmesi, zihin tutulması ve dengesizlik hali (belirsiz dişil mastar isim `جِنَّة`, {irab})"
            return f"Duyulardan gizli bilinçli varlıklar topluluğu (belirli topluluk ismi `ٱلْجِنَّة`, {irab})"

        elif lemma == 'jaA^n~':
            if (s, a) in ((27, 10), (28, 31)):
                return f"Yuvasına gizlenip şimşek gibi kıvrılarak hareket eden çevik yılan (etken ortaç isim `جَآنٌّ`, {indef_note}{irab})"
            return f"İnsan duyularından gizli, dumansız saf ateş enerjisinden var edilmiş bilinçli varlık türü (`ٱلْجَآنّ / جَآنّ`, {indef_note}{irab})"

        elif lemma == 'jun~ap':
            return f"Kötülüğü ve gerçek niyeti gizlemek için öne sürülen koruyucu kalkan ve siper (belirsiz tekil isim `جُنَّةً`, {irab})"

        elif lemma == 'jan~a':
            return "Gündüz ışığının üzerine karanlığıyla örtü serip her yanı gizledi (`جَنَّ`, I. bab mâzî fiil, 3. tekil eril)"

        elif lemma == '>ajin~ap':
            return f"Ana rahminin karanlık duvarları içinde örtülüp korunan henüz doğmamış ceninler (çoğul isim `أَجِنَّةٌ`, {indef_note}{irab})"

    elif root_ar == 'خ-ي-ر':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        p_pairs = [
            ('3MP', '3. çoğul eril'), ('2MP', '2. çoğul eril'),
            ('3MS', '3. tekil eril'), ('1P', '1. çoğul'), ('1S', '1. tekil'),
        ]
        pers = next((v for k, v in p_pairs if k in f), 'genel')
        wealth_ayahs = {(2, 180), (2, 272), (2, 273), (11, 84), (100, 8)}
        elative_nom_ayahs = {
            (3, 54), (3, 150), (5, 114), (6, 57), (7, 87), (7, 89), (7, 155),
            (8, 30), (10, 109), (12, 59), (12, 80), (21, 89), (22, 58), (23, 29),
            (23, 72), (23, 109), (23, 118), (34, 39), (62, 11), (98, 7),
        }
        if lemma == 'xayor':
            if 'MP' in f:
                tag_desc = "kırık çoğul sıfat" if pos == 'ADJ' else "kırık çoğul isim"
                return f"Erdem ve dürüstlükte öne çıkmış seçkin iyi kimseler ({tag_desc} `ٱلْأَخْيَارِ`, {irab})"
            if pos == 'ADJ':
                if 'F|' in f:
                    return f"Öncekilerden daha nitelikli, daha uyumlu ve daha iyi olan eşler (dişil uyumlu üstünlük sıfatı `خَيْرًا`, {indef_note}{irab})"
                if (s, a) == (38, 32):
                    return f"Yönetim ve koruma gücünü hatırlatan seçkin ve soylu atlar (tekil sıfat `ٱلْخَيْرِ`, {irab})"
                if (s, a) == (41, 49):
                    return f"İnsanın hiç bıkmadan talep edip durduğu yarar, refah ve iyilik (tekil sıfat `ٱلْخَيْرِ`, {irab})"
                return f"Kıyaslanan seçenekler arasında açıkça daha üstün, daha verimli ve daha hayırlı olan (`خَيْر`, üstünlük sıfatı, {indef_note}{irab})"
            if (s, a) in wealth_ayahs:
                return f"Elde tutulan yahut paylaşıma sokulan somut mal, servet ve geçim nimeti (`خَيْر`, {indef_note}isim, {irab})"
            if (s, a) in elative_nom_ayahs and 'INDEF' not in f:
                if (s, a) == (98, 7):
                    return f"İçinde bulunduğu tüm varlık türlerinin en değerlisi ve en seçkini (`خَيْرُ ٱلْبَرِيَّةِ`, isim tamlaması üstünlük adı, {irab})"
                return f"Söz konusu alanda en üstün, en yetkin ve en adil sonuç verici (`خَيْرُ`, isim tamlaması üstünlük adı, {irab})"
            if (s, a) == (70, 21):
                return f"Eline geçen yarar, varlık ve kolaylık imkânı (`ٱلْخَيْرُ`, belirli tekil isim, {irab})"
            if (s, a) == (24, 33):
                return f"Kendi sorumluluğunu üstlenebilecek liyakat, dürüstlük ve geçim kabiliyeti (`خَيْرًا`, {indef_note}isim, {irab})"
            if (s, a) == (28, 24):
                return f"Acil barınma, aş ve yaşam desteği olarak inen somut yarar (`خَيْر`, {indef_note}isim, {irab})"
            if (s, a) == (22, 36):
                return f"Beslenme, paylaşım ve ortak fayda üreten kalıcı yarar (`خَيْر`, {indef_note}isim, {irab})"
            if 'INDEF' not in f:
                return f"Her kesimin faydasına olan toplumsal iyilik, değer ve nimet birikimi (`ٱلْخَيْر`, belirli eril tekil isim, {irab})"
            return f"Hem somut fayda ve yarar sağlayan iyi sonuç hem kıyaslamada daha üstün olan (`خَيْر`, {indef_note}isim, {irab})"

        elif lemma == 'xayora`t':
            if (s, a) == (55, 70):
                return f"Ahlakça seçkin, huyları temiz ve uyumlu eşler (belirsiz dişil çoğul isim/sıfat `خَيْرَٰتٌ`, {irab})"
            return f"İyilik ve fayda üreten seçkin davranışlar, erdemli değerler ve kalıcı iyi sonuçlar (çoğul isim `ٱلْخَيْرَٰت`, {irab})"

        elif lemma == '{xotaAra':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Nitelik veya görev ehliyeti bakımından birini yahut bir topluluğu özenle seçip ayırır/seçti (VIII. bab {tense} fiil `ٱخْتَارَ / يَخْتَارُ`, {pers})"

        elif lemma == 'xiyarap':
            return f"Alternatifler arasında serbestçe karar verip seçme ve onaylama hakkı (tekil dişil isim `ٱلْخِيَرَة`, {irab})"

        elif lemma == 'yataxay~aru':
            return f"Sunulan alternatifler içinden kendi beğenisiyle dilediğini seçerler/seçeceksiniz (V. bab muzâri fiil `يَتَخَيَّرُونَ / تَخَيَّرُونَ`, {pers})"

    elif root_ar == 'ع-ن-د':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim/zarf"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        if lemma == 'Eind':
            if pos == 'LOC':
                if 'ACC' not in f:
                    if (s, a) == (28, 78):
                        return "Bende, kendi yanımda ve kişisel birikimimde bulunan bilgi (`عِندِى`, 1. tekil iyelik zamirli yer/aidiyet zarfı)"
                    if (s, a) == (12, 60):
                        return "Yanımda, çevremde ve benim gözetim alanım içinde bulunma hali (`عِندِى`, 1. tekil iyelik zamirli yer zarfı)"
                    return "Benim elimde, tasarrufum altında ve kendi yanımda bulunması (`عِندِى`, 1. tekil iyelik zamirli mekân/yetki zarfı)"
                if (s, a) in ((2, 191), (9, 7), (53, 14)):
                    return f"Fiziksel bir merkezin veya sınır noktasının hemen bitişik yanı başında (`عِندَ`, mekân zarfı, {irab})"
                if (s, a) in ((7, 29), (7, 31)):
                    return f"Her yöneliş ve toplanma mekânında, tam bulunulan yer ve anda (`عِندَ`, yer-zaman eşiği zarfı, {irab})"
                if (s, a) in ((16, 96), (27, 40), (28, 60)):
                    return f"Bir tarafın elinde tuttuğu imkân, kaynak ya da hemen yakınındaki konum (`عِندَ`, sahiplik ve konum zarfı, {irab})"
                return f"Yüce otoritenin veya bir öznenin katında, nezdinde, huzurunda ve değerlendirme ölçüsünde (`عِندَ`, mekân ve değer zarfı, {irab})"
            return f"Doğrudan bir kaynaktan, otorite katından yahut kişilerin kendi içinden gelme hali (`مِن عِندِ`, `مِنْ` sonrası mecrûr isim, {irab})"

        elif lemma == 'Eaniyd':
            tag_desc = "mübalağa sıfatı" if pos == 'ADJ' else "niteleyici isim"
            return f"Gerçeği bildiği halde doğru hizadan yana sapıp inatla direnen dik kafalı kimse ({indef_note}{tag_desc} `عَنِيد`, {irab})"

    elif root_ar == 'ن-و-ر':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        if lemma == 'nuwr':
            if (s, a) in ((10, 5), (71, 16)):
                return f"Güneşin yakıcı parıltısından farklı olarak gözü yormadan vakti, yönü ve düzeni gösteren yansımış duru aydınlık (`نُورًا`, {indef_note}eril tekil isim, {irab})"
            if (s, a) in ((2, 17), (24, 35), (24, 40), (39, 22), (39, 69)):
                return f"Görüş ufkunu açan, katmanlı berraklık veren ve yaşam yolunu seçilebilir kılan tekil ışık kaynağı (`نُور`, {indef_note}eril tekil isim, {irab})"
            if (s, a) in ((57, 12), (57, 13), (57, 19), (57, 28), (66, 8)):
                return f"Dürüst seçimlerin ürettiği ve önü açarak sahibini güvenle ilerleten kalıcı içsel aydınlık (`نُور`, {indef_note}eril tekil isim, {irab})"
            return f"Parçalı karanlıklardan çıkarıp hakikati, düzeni ve doğru rotayı görünür kılan tekil aydınlık (`نُور / ٱلنُّور`, {indef_note}eril tekil isim, {irab})"

        elif lemma == 'm~uniyr':
            tag_desc = "IV. bab etken ortaç sıfat" if pos == 'ADJ' else "IV. bab etken ortaç isim"
            if (s, a) == (25, 61):
                return f"Kendi kendine kavurmadan etrafa düzenli ışık yayan aydınlatıcı gök cismi, ay (`مُّنِيرًا`, {indef_note}{tag_desc}, {irab})"
            if (s, a) == (33, 46):
                return f"İnsanları yakıp korkutmadan önlerini açan aydınlatıcı kandil niteliği (`مُّنِيرًا`, {indef_note}{tag_desc}, {irab})"
            return f"Karanlıkta bırakmayıp bilgisiz tartışmalara son veren aydınlatıcı ve berraklaştırıcı yazılı rehber sıfatı (`مُنِير`, {indef_note}{tag_desc}, {irab})"

        elif lemma == 'naAr':
            if (s, a) in ((2, 17), (18, 96), (20, 10), (24, 35), (27, 7), (27, 8), (28, 29), (36, 80), (56, 71)):
                return f"Isıtan, eriten, parlayan yahut yol göstermek için tutuşturulan fiziksel ateş enerjisi (`نَار / ٱلنَّار`, {indef_note}dişil isim, {irab})"
            if (s, a) in ((2, 266), (3, 183), (5, 64), (13, 17), (21, 69), (29, 24), (85, 5)):
                return f"Maden eritmeden savaş yıkımına ve yakma girişimine dek somut maddi güç olarak çalışan ateş (`نَار / ٱلنَّار`, {indef_note}dişil isim, {irab})"
            if (s, a) in ((7, 12), (15, 27), (38, 76), (55, 15), (55, 35)):
                return f"Çamur ya da toprak gibi yoğun maddeden ayrı olarak hızlı, yakıcı ve akışkan enerji tabiatı (`نَار`, {indef_note}dişil isim, {irab})"
            if (s, a) in ((2, 174), (3, 103), (4, 10), (104, 6)):
                return f"Hak yiyenlerin kendi içine yığdığı yahut toplumu çökerten yakıcı yıkım ve vicdan ateşi (`نَار / ٱلنَّار`, {indef_note}dişil isim, {irab})"
            return f"Çarpık, yıkıcı ve inatçı seçimlerin kaçınılmaz sonucu olarak kuşatan yakıcı yıkım ve arınma ateşi (`نَار / ٱلنَّار`, {indef_note}dişil isim, {irab})"

    elif root_ar == 'ح-س-ن':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim/sıfat"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        hsn_p = [('1S', '1. tekil'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MP', '3. çoğul eril')]
        h_pers = next((v for k, v in hsn_p if k in f), 'genel')
        h_mood = ", meczûm" if 'JUS' in f else ""
        if lemma == 'muHosin':
            num_note = "çoğul" if 'MP' in f else "eril tekil"
            return f"İşi baştan savmadan en sağlam, özenli ve iyilik üreten biçimde yapan kimse (`مُحْسِن / مُحْسِنِينَ`, IV. bab etken ortaç {indef_note}{num_note} isim, {irab})"
        elif lemma == 'muHosina`t':
            return f"Dürüst, özenli ve yapıcı iyilik üreten kadınlar (`ٱلْمُحْسِنَٰتِ`, IV. bab dişil çoğul etken ortaç, {irab})"
        elif lemma == '<iHosa`n':
            return f"Soğuk eşitliğin de ötesine geçip incelik, özen ve gönüllü artı değer katma eylemi (`إِحْسَان`, IV. bab masdar isim, {irab})"
        elif lemma == '>aHosana':
            if 'IMPV' in f:
                return f"Yaptığın işi kusursuz, özenli ve başkasına faydalı kıl (`أَحْسِن / أَحْسِنُوا`, IV. bab emir fiili, {h_pers})"
            if 'IMPF' in f:
                return f"İlişkiyi ve işi yapıcı biçimde en güzel yola koyarlar/koyarsınız (`يُحْسِنُ / تُحْسِنُ`, IV. bab muzâri fiil, {h_pers}{h_mood})"
            return f"Parçaları en sağlam uyuma kavuşturup kusursuz biçim verdi veya iyiliği en güzel yoldan işledi (`أَحْسَنَ`, IV. bab mâzî fiil, {h_pers})"
        elif lemma == 'Hasuna':
            return f"Bütün unsurlarıyla sağlam, uyumlu, huzurlu ve güzel oldu (`حَسُنَ / حَسُنَتْ`, I. bab mâzî fiil, {h_pers})"
        elif lemma == '>aHosan':
            tag_desc = "eril üstünlük sıfatı" if pos == 'ADJ' else "eril üstünlük (af‘al) ismi"
            return f"Kıyaslamada en sağlam, en dengeli, en yetkin ve en güzel olan (`أَحْسَن`, {tag_desc}, {irab})"
        elif lemma == 'Huson':
            return f"Çirkinlik ve bozukluktan arınmış dengeli uyum, zerafet ve güzel yaşam sonu (`حُسْن`, eril isim, {irab})"
        elif lemma == 'Hasan':
            tag_desc = "temel isim (kötülüğü güzel sanma bağlamı)" if pos == 'N' else ("çoğul sıfat (`حِسَان`)" if 'MP' in f else "eril sıfat (`حَسَن`)")
            return f"İç ve dış dengesi yerinde, sağlam, gönül açıcı ve kaliteli olan (`حَسَن`, {indef_note}{tag_desc}, {irab})"
        elif lemma == 'Hasanap':
            tag_desc = "örnek/niteleyici dişil sıfat" if pos == 'ADJ' else "somut güzel eylem ve refah hali ismi"
            return f"Tek bir somut iyileştirici davranış, ferahlık veya uyulacak güzel örnek (`حَسَنَة`, {indef_note}{tag_desc}, {irab})"
        elif lemma == 'Hasana`t':
            return f"Kötü izleri ve dengesizlikleri onarıp silen çoğul yapıcı işler veya ferah dönemler (`حَسَنَٰت`, dişil çoğul isim, {irab})"
        elif lemma == 'HusonaY`':
            tag_desc = "dişil üstünlük sıfatı" if pos == 'ADJ' else "dişil üstünlük ismi"
            return f"En yetkin, en parlak ve varılabilecek en güzel nitelik veya sonuç (`ٱلْحُسْنَىٰ`, {tag_desc}, {irab})"
        elif lemma == 'Husonayayon':
            return f"Onurlu direnç ve zaferden oluşan iki en güzel sonuçtan biri (`ٱلْحُسْنَيَيْنِ`, dişil ikil üstünlük sıfatı, {irab})"

    elif root_ar == 'ض-ل-ل':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim/sıfat"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        dll_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MD', '3. ikil eril'), ('3FP', '3. çoğul dişil'), ('3MP', '3. çoğul eril')]
        d_pers = next((v for k, v in dll_p if k in f), 'genel')
        d_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == 'Dal~a':
            if 'PASS' in f:
                return f"Yanlış çıkar ve keyfî takvim oyunlarıyla yolları şaşırtılıp saptırılırlar (`يُضَلُّ`, I. bab edilgen muzâri fiil, {d_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) == (2, 282):
                return f"Tanıklardan birinin zihni karışıp hafızasını yitirmesi veya yanılması (`تَضِلَّ`, I. bab {tense} fiil, {d_pers}{d_mood})"
            if (s, a) == (20, 52):
                return f"Hiçbir veri ve ölçüyü yitirip şaşırmaz (`لَّا يَضِلُّ`, I. bab {tense} fiil, {d_pers})"
            if (s, a) == (32, 10):
                return f"Toprak içinde dağılıp izimiz tamamen silindiğinde (`ضَلَلْنَا`, I. bab {tense} fiil, {d_pers})"
            if (s, a) == (18, 104):
                return f"Dünya yaşamında bütün emek ve çabaları hedefi ıskalayıp boşa gitti (`ضَلَّ`, I. bab {tense} fiil, {d_pers})"
            return f"Doğru rotayı, izi veya pusulayı kaybedip yönsüz biçimde yoldan saptı/sapar (`ضَلَّ / يَضِلُّ`, I. bab {tense} fiil, {d_pers}{d_mood})"
        elif lemma == '>aDal~a':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) in ((47, 1), (47, 4), (47, 8)):
                return f"Yapılan eylemlerin ve çabaların etkisini sıfırlayıp boşa çıkardı/çıkarır (`أَضَلَّ / يُضِلَّ`, IV. bab {tense} fiil, {d_pers}{d_mood})"
            return f"Kişinin kendi tercihine uyarak yahut aldatıcı etkiyle pusulasını kaybettirir/saptırdı (`أَضَلَّ / يُضِلُّ`, IV. bab {tense} fiil, {d_pers}{d_mood})"
        elif lemma == 'Dala`l':
            if (s, a) in ((12, 8), (12, 30), (12, 95)):
                return f"Aşırı duygusal bağlılık veya yargı ölçüsünde dengeyi yitirme hali (`ضَلَٰل`, {indef_note}eril masdar isim, {irab})"
            return f"Ana rotadan kopup yönsüzlük, şaşkınlık ve çıkmaza düşme hali (`ضَلَٰل`, {indef_note}eril masdar isim, {irab})"
        elif lemma == 'Dala`lap':
            return f"Bilinçli veya ısrarlı tercih sonucu yerleşen yanlış yönelim ve sapma hali (`ضَلَٰلَة`, {indef_note}dişil isim, {irab})"
        elif lemma == 'DaA^l~':
            tag_desc = "etken ortaç sıfat" if pos == 'ADJ' else "etken ortaç isim"
            if (s, a) == (93, 7):
                return f"Henüz yol haritasını bulamamış, yön arayan halde (`ضَآلًّا`, {indef_note}tekil {tag_desc}, {irab})"
            if (s, a) == (68, 26):
                return f"Bağın yerini ve yönünü şaşırmış kimseler (`ضَآلُّونَ`, çoğul {tag_desc}, {irab})"
            return f"Doğru rotayı kaybetmiş, şaşkınlık veya yanlış yönelim içindeki kimseler (`ضَآلّ / ٱلضَّآلِّينَ`, {indef_note}{tag_desc}, {irab})"
        elif lemma == '>aDal~':
            return f"Yönünü, sağduyusunu ve dengesini diğerlerinden daha ağır biçimde kaybetmiş olan (`أَضَلُّ`, eril üstünlük ismi, {irab})"
        elif lemma == 'm~uDil~':
            return f"İnsanları aldatıcı telkinlerle yanlış rotaya sürükleyip yönünü kaybettiren (`مُضِلّ / مُضِلِّينَ`, IV. bab {indef_note}etken ortaç isim, {irab})"
        elif lemma == 'taDoliyl':
            return f"Kurulan bütün tuzakların ve güç gösterisinin iz bırakmadan tamamen boşa çıkarılışı (`تَضْلِيل`, II. bab {indef_note}masdar isim, {irab})"

    elif root_ar == 'س-م-ع':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim/sıfat"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        sm_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MP', '3. çoğul eril')]
        s_pers = next((v for k, v in sm_p if k in f), 'genel')
        s_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == 'samiEa':
            if 'IMPV' in f:
                if (s, a) == (4, 46):
                    return "Sözü çarpıtarak veya içtenlikle yönelerek «şimdi dikkatle dinle» çağrısı (`ٱسْمَعْ`, I. bab emir fiili, 2. tekil eril)"
                return f"Söylenen söze ve çağrıya hemen odaklanıp kulak verin veya kulak ver (`وَٱسْمَعُوا۟ / فَٱسْمَعُونِ`, I. bab emir fiili, {s_pers})"
            if 'PERF' in f:
                if (s, a) in ((2, 93), (4, 46)):
                    return f"Sözü kulağımızla aldık ardından ya bile bile direndik ya da uyum sağladık (`سَمِعْنَا`, I. bab mâzî fiil, {s_pers})"
                if (s, a) in ((2, 285), (5, 7), (24, 51)):
                    return f"Çağrıyı zihin ve gönül açıklığıyla duyduk ve uyuma geçtik (`سَمِعْنَا`, I. bab mâzî fiil, {s_pers})"
                if (s, a) == (58, 1):
                    return "Hakkını arayan ve sıkıntısını dile getiren kadının sözünü bizzat işitti (`سَمِعَ`, I. bab mâzî fiil, 3. tekil eril)"
                return f"Sesi, haberi veya çağrıyı kulak yoluyla algılayıp aldı (`سَمِعَ / سَمِعُوا۟ / سَمِعْنَا`, I. bab mâzî fiil, {s_pers})"
            if (s, a) in ((19, 98), (20, 108)):
                return f"Hafif bir adım tıkırtısı ya da fısıltı düzeyindeki en cılız sesi yakalarsın (`تَسْمَعُ`, I. bab muzâri fiil, {s_pers})"
            if (s, a) == (20, 46):
                return "Korkmayın, ben sizinleyim, hem konuşulan her şeyi işitir hem her anı görürüm (`أَسْمَعُ`, I. bab muzâri fiil, 1. tekil)"
            if (s, a) in ((6, 36), (8, 21), (21, 45), (35, 14), (67, 10)):
                return f"Sesi yalnız mekanik olarak değil akıl ve bilinç süzgecinden geçirerek algılayıp karşılık verirler (`يَسْمَعُونَ / نَسْمَعُ`, I. bab muzâri fiil, {s_pers}{s_mood})"
            return f"Çevreden gelen sözü, sesi veya bildiriyi kulağıyla yakalar (`يَسْمَعُ / تَسْمَعُ / يَسْمَعُونَ`, I. bab muzâri fiil, {s_pers}{s_mood})"
        elif lemma == '{sotamaEa':
            if 'IMPV' in f:
                if (s, a) == (7, 204):
                    return "Metin okunduğunda dış gürültüyü kesip dikkatinizi bilinçle ona verin (`فَٱسْتَمِعُوا۟`, VIII. bab emir fiili, 2. çoğul eril)"
                return f"Aktarılan önemli bildirime veya örneğe iradeyle dikkat kesil/kulak kesilin (`فَٱسْتَمِعْ / فَٱسْتَمِعُوا۟`, VIII. bab emir fiili, {s_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) == (72, 9):
                return f"Yüksek katmandan gizlice bilgi yakalayıp dinlemeye yeltenen (`يَسْتَمِعِ`, VIII. bab {tense} fiil, {s_pers}{s_mood})"
            return f"Rastgele duymayıp kasten yönelerek ve dikkat kesilerek dinler/dinledi (`يَسْتَمِعُ / ٱسْتَمَعَ`, VIII. bab {tense} fiil, {s_pers}{s_mood})"
        elif lemma == '>asomaEa':
            if 'IMPV' in f:
                return "Ne kusursuz işitir, ya da o büyük yüzleşme günü nasıl da keskin duyacaklar (`أَسْمِعْ / وَأَسْمِعْ`, IV. bab hayret ünlemi kalıbı)"
            if '3FS' in f:
                return "Bilincini ve iradesini kilitlemiş kimselere sözü içe işleyecek şekilde duyurabilir misin (`تُسْمِعُ`, IV. bab muzâri fiil, 2. tekil eril, korpusta şeklen `3FS` etiketli)"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Sözü yalnızca fiziksel ses olarak değil kavrayışa nüfuz edecek biçimde işittirir/işittirdi (`أَسْمَعَ / يُسْمِعُ / تُسْمِعُ`, IV. bab {tense} fiil, {s_pers})"
        elif lemma == 'yas~am~aEu':
            return "Yüce yönetim meclisinden gizlice kulak hırsızlığı yapmaya çabalarlar (`يَسَّمَّعُونَ`, aslı `يَتَسَمَّعُونَ` olan V. bab idğamlı muzâri fiil, 3. çoğul eril)"
        elif lemma == 'samoE':
            if (s, a) in ((16, 78), (17, 36), (23, 78), (32, 9), (46, 26), (67, 23)):
                return f"Her yönden gelen sesleri tek ortak havuzda toplayan işitme kanalı ve duyma donanımı (`سَمْع`, daima tekil eril masdar isim, {irab})"
            if (s, a) in ((2, 7), (16, 108), (45, 23)):
                return f"İnatçı kapanış yüzünden gerçeğe karşı kilitlenmiş işitme kapasitesi (`سَمْعِهِمْ / سَمْعِهِۦ`, tekil eril isim, {irab})"
            if (s, a) in ((41, 20), (41, 22)):
                return f"Hayat boyu alınan bütün ses kayıtlarını ortaya döken tanık işitme duyusu (`سَمْعُهُمْ / سَمْعُكُمْ`, tekil eril isim, {irab})"
            return f"Ses sinyallerini yakalama gücü, işitme yetisi ve kulak verme kanalı (`سَمْع`, {indef_note}daima tekil eril isim, {irab})"
        elif lemma == 'samiyE':
            tag_desc = "eril tekil sıfat" if pos == 'ADJ' else "mübalağalı ortaç isim"
            if (s, a) == (76, 2):
                return f"Çevresindeki sesleri duyan ve söyleneni algılayıp karşılık verebilen donanımlı varlık (`سَمِيعًۢا`, {indef_note}{tag_desc}, {irab})"
            if (s, a) == (11, 24):
                return f"Hakikat çağrısını sağlıklı biçimde işitip kavrayan kişi (`ٱلسَّمِيعِ`, {tag_desc}, {irab})"
            if (s, a) in ((3, 38), (14, 39)):
                return f"En sessiz yakarışı ve yardım çağrısını dahi anında eksiksiz işiten (`سَمِيعُ`, {tag_desc}, {irab})"
            return f"Açık sözü de en gizli fısıltıyı da kaçırmadan kesintisiz işiten (`سَمِيع / ٱلسَّمِيعُ`, {indef_note}{tag_desc}, {irab})"
        elif lemma == 'sam~a`Euwn':
            return f"Yalan haberlere, dedikoduya ve bozguncu telkinlere hevesle kulak kesilen sürekli dinleyiciler (`سَمَّٰعُونَ`, çoğul mübalağalı etken ortaç isim, {irab})"
        elif lemma == 'musotamiE':
            if (s, a) == (26, 15):
                return "Sizinle birlikte her konuşmayı ve tepkiyi anlık dinleyip izleyenler (`مُّسْتَمِعُونَ`, VIII. bab çoğul etken ortaç isim, merfû)"
            return "Üst boyuttan bilgi sızdırıp dinlediğini ileri süren o dinleyicileri (`مُسْتَمِعُهُم`, VIII. bab tekil etken ortaç isim, merfû)"
        elif lemma == 'musomaE':
            return "Sözüne hiç kimsenin kulak asmayacağı yahut işitmesi istenmeyen kişi imasıyla kullanılan alaylı ifade (`غَيْرَ مُسْمَعٍ`, IV. bab belirsiz edilgen ortaç isim, mecrûr)"
        elif lemma == 'musomiE':
            return "Ölüp gitmiş ve tüm alıcıları kapanmış kimselere çağrıyı işittirebilen kimse (`مُسْمِع`, IV. bab belirsiz etken ortaç isim, mecrûr)"

    elif root_ar == 'ب-ن-ي':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        bn_p = [('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3MP', '3. çoğul eril')]
        b_pers = next((v for k, v in bn_p if k in f), 'genel')
        if lemma == 'banaY`':
            if 'IMPV' in f:
                if (s, a) == (40, 36):
                    return "Bana gök kapılarına ulaşacak yüksek bir kule inşa et (`ٱبْنِ`, I. bab emir fiili, 2. tekil eril)"
                if (s, a) == (66, 11):
                    return "Baskı düzeninden uzakta, kendi katında bana kalıcı ve güvenli bir ev kur (`ٱبْنِ`, I. bab emir fiili, 2. tekil eril)"
                if (s, a) == (18, 21):
                    return "Mağara arkadaşlarının üzerine anıtlık bir yapı örün (`ٱبْنُوا۟`, I. bab emir fiili, 2. çoğul eril)"
                return "Onun için yüksek bir ocak veya ateş duvarı örüp yükseltin (`ٱبْنُوا۟`, I. bab emir fiili, 2. çoğul eril)"
            if 'IMPF' in f:
                return f"Her yüksek geçide boşuna gösteriş anıtları mı dikip kuruyorsunuz (`أَتَبْنُونَ`, I. bab muzâri fiil, {b_pers})"
            if (s, a) == (9, 110):
                return f"Çıkar ve fitne amaçlı gizli yapı kurdular (`بَنَوْا۟`, I. bab mâzî fiil, {b_pers})"
            return f"Üstündeki gök kubbeyi çatlaksız, sağlam ölçülü dev bir kozmik yapı halinde inşa etti/ettik (`بَنَىٰ / بَنَيْنَا`, I. bab mâzî fiil, {b_pers})"
        elif lemma == 'bunoya`n':
            if (s, a) == (61, 4):
                return f"Parçaları harçla sımsıkı kaynatılmış sarsılmaz tek parça duvar gibi saf düzeni (`بُنْيَٰنٌ`, {indef_note}eril isim, {irab})"
            if (s, a) in ((9, 109), (9, 110), (16, 26)):
                return f"Sağlam ilke veya kaypak uçurum kenarı üzerine yükseltilmiş yapı ve düzen (`بُنْيَٰن`, tekil eril isim, {irab})"
            return f"Taş ve tuğladan yükseltilmiş somut bina ve duvar örgüsü (`بُنْيَٰن`, {indef_note}eril isim, {irab})"
        elif lemma == "binaA^'":
            return f"Yeryüzü döşeğinin üstünü kuşatıp koruyan gökyüzü yapısı ve sağlam çatı (`بِنَآءً`, {indef_note}tekil eril isim, {irab})"
        elif lemma == "ban~aA^'":
            return f"Büyük yapılar ören usta inşaatçı ve mimar (`بَنَّآءٍ`, {indef_note}mübalağalı etken ortaç isim, {irab})"
        elif lemma == 'm~aboniy~ap':
            return f"Kat kat yükseltilip özenle örülmüş yüksek yaşam mekanları (`مَّبْنِيَّةٌ`, {indef_note}dişil edilgen ortaç isim, {irab})"
        elif lemma == 'bunaY~':
            if 'MP' not in f:
                return "Sevgi ve koruyucu şefkatle seslenilen canım yavrum, sevgili evladım (`يَٰبُنَىَّ`, tekil eril küçültme/sevgi nidası)"
            if (s, a) in ((7, 26), (7, 27), (7, 31), (7, 35), (7, 172), (17, 70), (36, 60)):
                return f"İlk insandan türeyip yeryüzünü imar eden insanlık ailesinin fertleri (`بَنِىٓ ءَادَمَ`, çoğul eril isim, {irab})"
            israil_refs = {
                (2, 40), (2, 47), (2, 83), (2, 122), (2, 211), (2, 246), (3, 49), (3, 93),
                (5, 12), (5, 32), (5, 70), (5, 72), (5, 78), (5, 110), (7, 105), (7, 134),
                (7, 137), (7, 138), (10, 90), (10, 93), (17, 2), (17, 4), (17, 101), (17, 104),
                (20, 47), (20, 80), (20, 94), (26, 17), (26, 22), (26, 59), (26, 197), (27, 76),
                (32, 23), (40, 53), (43, 59), (44, 30), (45, 16), (46, 10), (61, 6), (61, 14),
            }
            if (s, a) in israil_refs:
                return f"Yakup soyunun tarihsel sürekliliğini ve toplumsal sorumluluğunu taşıyan İsrailoğulları (`بَنِىٓ إِسْرَٰٓءِيلَ`, çoğul eril isim, {irab})"
            if (s, a) == (24, 31):
                return f"Aile içi mahremiyet sınırındaki erkek ve kız kardeşlerin oğulları (`بَنِىٓ`, çoğul eril isim, {irab})"
            return f"Soyu, emeği ve aile kurumunu ileri taşıyan oğullar ve yeni kuşaklar (`بَنُونَ / بَنِينَ / بَنِيهِ`, çoğul eril isim, {irab})"
        elif lemma == '{bon':
            if 'MD' in f:
                return "İnsanlığın ilk atası Âdem'in iki oğlu (`ٱبْنَىْ`, ikil eril isim, mecrûr)"
            if (s, a) in ((2, 177), (2, 215), (4, 36), (8, 41), (9, 60), (17, 26), (30, 38), (59, 7)):
                return f"Memleketinden uzakta kalmış ve yolun himayesine muhtaç düşmüş yolcu (`ٱبْنَ ٱلسَّبِيلِ`, tekil eril isim, {irab})"
            if 'MP' in f:
                return f"Aile yapısını ve nesil zincirini sürdüren oğullar veya çocuklar (`أَبْنَآء`, çoğul eril isim, {irab})"
            return f"Ana babadan doğup bir soy veya tarih hattını temsil eden oğul (`ٱبْن`, tekil eril isim, {irab})"
        elif lemma == 'banaAt':
            if (s, a) in ((6, 100), (16, 57), (37, 149), (37, 153), (43, 16), (52, 39)):
                return f"Kız evladı küçümseyip Yaratıcıya kız isnat eden çelişkili zihniyet eleştirisindeki kız çocuklar (`بَنَات`, {indef_note}dişil çoğul isim, {irab})"
            return f"Aile yapısını kuran kız evlatlar ve akrabalar (`بَنَات`, dişil çoğul isim, {irab})"
        elif lemma == '{bonat':
            if 'FD' in f:
                return "Kendi hanesinden yetişen iki kız evladım (`ٱبْنَتَىَّ`, dişil ikil isim, merfû)"
            return "İmran ailesinden yetişen erdemli kız evlat (`ٱبْنَتَ`, dişil tekil isim, mansûb)"

    elif root_ar == 'ح-ي-ي':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim/sıfat"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        hy_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3MP', '3. çoğul eril')]
        h_pers = next((v for k, v in hy_p if k in f), 'genel')
        h_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == 'Hayaw`p':
            if (s, a) == (2, 179):
                return f"Adaletli karşılık yasasıyla korunan ortak toplumsal yaşam ve güvenlik (`حَيَوٰةٌ`, {indef_note}tekil dişil isim, {irab})"
            if (s, a) == (16, 97):
                return f"Huzurlu, verimli ve içi dışı arınmış nitelikli güzel yaşam (`حَيَوٰةً`, {indef_note}tekil dişil isim, {irab})"
            if (s, a) == (2, 96):
                return f"Ne kadar uzarsa uzasın tutunulan çıplak biyolojik yaşam (`حَيَوٰةٍ`, {indef_note}tekil dişil isim, {irab})"
            if (s, a) == (25, 3):
                return f"Varlığa kendi iradesiyle canlılık ve yaşam bahşetme yetkisi (`حَيَوٰةً`, {indef_note}tekil dişil isim, {irab})"
            if (s, a) == (67, 2):
                return f"Nitelikli eylemi açığa çıkarmak üzere kurulan sınama ve dirilik evresi (`ٱلْحَيَوٰةَ`, belirli tekil dişil isim, {irab})"
            if (s, a) == (89, 24):
                return f"Keşke önden hazırlık yapsaydım denilen asıl kalıcı hayatım (`لِحَيَاتِى`, harf-i cerli ve 1. tekil iyelikli dişil isim, {irab})"
            if (s, a) in ((6, 29), (23, 37), (45, 24), (46, 20)):
                return f"Ötesini tanımayanların bağlandığı şu geçici dünya yaşamımız/yaşamınız (`حَيَاتُنَا / حَيَاتِكُمُ`, iyelik zamirli dişil isim, {irab})"
            if (s, a) in ((17, 75), (20, 97)):
                return f"Yaşam sürecinin kendisi veya dünya sürgünü boyunca katlanılacak hayat (`ٱلْحَيَوٰةِ`, belirli tekil dişil isim, {irab})"
            return f"Yakın, geçici ve sınama alanı olarak yaşanılan dünya hayatı (`ٱلْحَيَوٰة`, belirli tekil dişil isim, {irab})"
        elif lemma == '>aHoyaA':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) in ((2, 164), (16, 65), (25, 49), (29, 63), (30, 19), (30, 24), (30, 50), (35, 9), (36, 33), (41, 39), (45, 5), (50, 11), (57, 17)):
                return f"Yağmurla susuz ve ölü toprağı yeniden yeşertip canlandırdı/canlandırır (`أَحْيَا / يُحْىِ`, IV. bab {tense} fiili, {h_pers}{h_mood})"
            if (s, a) == (5, 32):
                return f"Ölümden kurtararak bir canın yaşamını sürdürmesini sağladı (`أَحْيَا / أَحْيَاهَا`, IV. bab mâzî fiili, {h_pers})"
            if (s, a) in ((6, 122), (8, 24)):
                return f"Bilinç ve kavrayış durgunluğunu aydınlıkla diriltir/dirilttik (`أَحْيَيْنَٰهُ / يُحْيِيكُمْ`, IV. bab {tense} fiili, {h_pers})"
            if (s, a) == (16, 97):
                return "Onu temiz, dingin ve verimli bir yaşamla mutlaka yaşatırız (`فَلَنُحْيِيَنَّهُۥ`, IV. bab tekitli muzâri fiil, 1. çoğul)"
            return f"Durağanlık ve ölümden çıkarıp yeniden işlevsel dirilik ve yaşam verir/verdi (`أَحْيَا / يُحْىِۦ`, IV. bab {tense} fiili, {h_pers}{h_mood})"
        elif lemma == 'Hay~':
            tag_desc = "eril tekil belirsiz sıfat" if pos == 'ADJ' else ("kırık çoğul isim (`أَحْيَآء`)" if 'MP' in f else "tekil eril isim/sıfat")
            if pos == 'ADJ':
                return f"Sudan var edilen her işlevsel canlı varlık (`حَىٍّ`, {tag_desc}, {irab})"
            if (s, a) in ((2, 255), (3, 2), (20, 111), (25, 58), (40, 65)):
                return f"Ölümün ve zaafın değmediği, her şeyi ayakta tutan mutlak diri (`ٱلْحَىُّ / لِلْحَىِّ`, belirli tekil isim, {irab})"
            if (s, a) in ((3, 27), (6, 95), (10, 31), (30, 19)):
                return f"Ölü/cansız olandan çıkan veya ölüme devredilen canlı organizma (`ٱلْحَىَّ / ٱلْحَىِّ`, belirli tekil isim, {irab})"
            if (s, a) in ((2, 154), (3, 169)):
                return f"Biyolojik ölüme rağmen başka bir boyutta rızıklanıp yaşamını sürdüren diriler (`أَحْيَآءٌ`, {indef_note}çoğul isim, {irab})"
            if (s, a) == (36, 70):
                return f"Algısı açık, işitip düşünebilen diri bilinçli kimse (`حَيًّا`, {indef_note}tekil isim, {irab})"
            return f"Yaşamakta olan diri varlık veya diriler (`حَيًّا / أَحْيَآء / ٱلْأَحْيَآءُ`, {indef_note}{tag_desc}, {irab})"
        elif lemma == 'yasotaHoYi.^':
            if 'IMPV' in f:
                return "Erkek çocuklarını öldürüp kadınlarını sağ bırakın (`وَٱسْتَحْيُوا۟`, X. bab emir fiili, 2. çoğul eril)"
            if (s, a) in ((2, 49), (7, 127), (7, 141), (14, 6), (28, 4)):
                return f"Zorbalık düzeninde kadınların canına dokunmayıp hayatta bırakırlar/bırakacağız (`يَسْتَحْيُونَ / نَسْتَحْىِۦ`, X. bab muzâri fiili, {h_pers})"
            if (s, a) == (33, 53):
                return f"Saygı/nezaket sınırından dolayı çekinir veya gerçeği bildirmekten geri durmaz (`يَسْتَحْىِۦ`, X. bab muzâri fiili, {h_pers})"
            return f"Hakikati ve örneği ortaya koymaktan çekinip geri durmaz (`يَسْتَحْىِۦٓ`, X. bab muzâri fiili, {h_pers})"
        elif lemma == 'HaY~a':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) == (8, 42):
                return f"Açık kanıt ve sağduyu temeli üzerinde ayakta kalıp yaşadı/yaşasın (`حَىَّ / يَحْيَىٰ`, I. bab {tense} fiili, {h_pers}{h_mood})"
            if (s, a) in ((20, 74), (87, 13)):
                return "Ne ölüp kurtulur ne de rahat içinde gerçekten yaşayabilir (`لَا يَمُوتُ فِيهَا وَلَا يَحْيَىٰ`, I. bab muzâri fiili, 3. tekil eril)"
            return f"Yeryüzünde biyolojik yaşam sürdürürsünüz/sürdürürüz (`تَحْيَوْنَ / وَنَحْيَا`, I. bab muzâri fiili, {h_pers}{h_mood})"
        elif lemma == 'taHiy~ap':
            return f"Karşılıklı dirilik, sağlık ve tam esenlik dileği sunan selamlaşma (`تَحِيَّة`, II. bab masdar {indef_note}dişil isim, {irab})"
        elif lemma == 'Hay~a':
            if 'PASS' in f:
                return "Size dirilik ve esenlik dileğiyle selam verildiğinde (`حُيِّيتُم`, II. bab edilgen mâzî fiili, 2. çoğul eril)"
            if 'IMPV' in f:
                return "Verilen selamı daha güzel ve kapsamlı esenlik dileğiyle karşılayın (`فَحَيُّوا۟`, II. bab emir fiili, 2. çoğul eril)"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Yüce merciin onaylamadığı sahte veya saptırıcı bir esenlik selamıyla selamladılar/selamlar (`حَيَّوْكَ / يُحَيِّكَ`, II. bab {tense} fiili, {h_pers}{h_mood})"
        elif lemma == 'm~aHoyaA':
            return f"İnsanın bütün yaşadığı hayat süreci ve eylem çizgisi (`مَحْيَا`, mîmli masdar isim, {irab})"
        elif lemma == 'muHoY':
            return f"Ölü ve dağılmış olanları mutlaka yeniden diriltip hayata döndüren (`لَمُحْىِ`, IV. bab etken ortaç isim, {irab})"
        elif lemma == 'Hay~ap':
            return f"Kıvrak ve hızlı biçimde akıp devinen canlı bir yılan (`حَيَّةٌ`, {indef_note}dişil tekil isim, {irab})"
        elif lemma == "{sotiHoyaA^'":
            return f"Canlı ve duyarlı edep bilinciyle ölçülü çekingenlik üzere (`عَلَى ٱسْتِحْيَآءٍ`, X. bab {indef_note}masdar isim, {irab})"
        elif lemma == 'HayawaAn':
            return f"Sönmeyen, kesintisiz ve eksiksiz hareket halindeki gerçek hayat yurdu (`ٱلْحَيَوَانُ`, fe'alân kalıbı belirli masdar isim, {irab})"

    elif root_ar == 'خ-ر-ج':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        xr_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MD', '3. ikil eril'), ('3MP', '3. çoğul eril'), ('3FP', '3. çoğul dişil')]
        x_pers = next((v for k, v in xr_p if k in f), 'genel')
        x_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == '>axoraja':
            if 'PASS' in f:
                tense = "mâzî" if 'PERF' in f else "muzâri"
                if (s, a) == (3, 110):
                    return f"İnsanların iyiliği için sahneye ve öne çıkarılmış örnek topluluk (`أُخْرِجَتْ`, IV. bab edilgen {tense} fiili, {x_pers})"
                if (s, a) in ((7, 25), (19, 66), (30, 19), (43, 11), (46, 17)):
                    return f"Toprağın içinden ve ölüm durağanlığından yeniden hayata çıkarılır/çıkarılacağım (`تُخْرَجُونَ / أُخْرَجُ`, IV. bab edilgen {tense} fiili, {x_pers}{x_mood})"
                if (s, a) == (45, 35):
                    return "Yakıcı yıkım alanından artık dışarı çıkarılmazlar (`لَا يُخْرَجُونَ`, IV. bab edilgen muzâri fiili, 3. çoğul eril)"
                return f"Yurtlarından ve evlerinden zorla sürgün edilip çıkarıldılar/çıkarılırsınız (`أُخْرِجُوا۟ / أُخْرِجْتُمْ`, IV. bab edilgen {tense} fiili, {x_pers})"
            if 'IMPV' in f:
                if (s, a) in ((4, 75), (23, 107), (35, 37)):
                    return "Bizi bu baskı beldesinden veya azap çukurundan dışarı çıkar (`أَخْرِجْنَا`, IV. bab emir fiili, 2. tekil eril)"
                if (s, a) == (17, 80):
                    return "Beni girdiğim yerden doğruluk ve onurla dışarı çıkar (`وَأَخْرِجْنِى`, IV. bab emir fiili, 2. tekil eril)"
                if (s, a) == (14, 5):
                    return "Topluluğunu koyu karanlıklardan aydınlığa çıkar (`أَخْرِجْ`, IV. bab emir fiili, 2. tekil eril)"
                if (s, a) == (6, 93):
                    return "Canlarınızı beden kafesinden kendiniz dışarı çıkarın (`أَخْرِجُوٓا۟`, IV. bab emir fiili, 2. çoğul eril)"
                return f"Hakkınız olan yerden sizi çıkaranları çıkarın veya dışarı sürün (`أَخْرِجُوهُم`, IV. bab emir fiili, {x_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) in ((2, 257), (5, 16), (14, 1), (14, 5), (33, 43), (57, 9), (65, 11)):
                return f"Parçalı karanlıklardan çıkarıp berrak aydınlığa yöneltir/yöneltmek için (`يُخْرِجُهُم / لِيُخْرِجَكُم`, IV. bab {tense} fiili, {x_pers}{x_mood})"
            if (s, a) in ((2, 22), (2, 61), (2, 267), (6, 99), (7, 57), (14, 32), (20, 53), (32, 27), (35, 27), (36, 33), (39, 21), (48, 29), (78, 15), (79, 31), (87, 4)):
                return f"Suyla tohumun ve toprağın içinden ürün, filiz ve rızık çıkarır/çıkardı (`أَخْرَجَ / نُخْرِجُ`, IV. bab {tense} fiili, {x_pers}{x_mood})"
            if (s, a) in ((47, 29), (47, 37)):
                return f"Kalplerin derinliğinde saklanan gizli kinleri dışarı çıkarıp açığa vurur (`يُخْرِجَ / وَيُخْرِجْ`, IV. bab {tense} fiili, {x_pers}{x_mood})"
            return f"Bulunduğu kapalı ortamdan, topraktan, rahimden veya yurttan dışarı çıkarır/çıkardı (`أَخْرَجَ / يُخْرِجُ`, IV. bab {tense} fiili, {x_pers}{x_mood})"
        elif lemma == 'xaraja':
            if 'IMPV' in f:
                if (s, a) in ((7, 13), (7, 18), (15, 34), (38, 77)):
                    return "Bulunduğun yüksek konumdan kınanmış halde hemen dışarı çık (`فَٱخْرُجْ / ٱخْرُجْ`, I. bab emir fiili, 2. tekil eril)"
                if (s, a) == (12, 31):
                    return "Kadınların toplandığı salona görünmek üzere dışarı çık (`ٱخْرُجْ`, I. bab emir fiili, 2. tekil eril)"
                if (s, a) == (28, 20):
                    return "Canını kurtarmak için bu şehirden hemen dışarı çık (`فَٱخْرُجْ`, I. bab emir fiili, 2. tekil eril)"
                return f"Evlerinizden ve yurtlarınızdan ayrılıp dışarı çıkın (`ٱخْرُجُوا۟`, I. bab emir fiili, {x_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) in ((20, 22), (27, 12), (28, 32)):
                return f"Koynundan kusursuz ve bembeyaz parlayarak dışarı çıkar (`تَخْرُجْ`, I. bab muzâri fiili, 3. tekil dişil, meczûm)"
            if (s, a) in ((2, 74), (7, 58), (16, 69), (23, 20), (24, 43), (30, 48), (34, 2), (41, 47), (55, 22), (57, 4), (86, 7)):
                return f"Kayadan su, buluttan yağmur, kabuktan ürün, arıdan bal veya bünyeden sıvı doğal olarak dışarı çıkar (`يَخْرُجُ / تَخْرُجُ`, I. bab {tense} fiili, {x_pers})"
            if (s, a) in ((30, 25), (54, 7), (70, 43)):
                return f"Çağrıyı duyduklarında kabirlerden hızla dışarı çıkarlar/çıkacaksınız (`تَخْرُجُونَ / يَخْرُجُونَ`, I. bab muzâri fiili, {x_pers})"
            return f"Kendi iradesiyle veya çağrı/korku üzerine içeriden dışarıya çıkar/çıktı (`خَرَجَ / يَخْرُجُ`, I. bab {tense} fiili, {x_pers}{x_mood})"
        elif lemma == '<ixoraAj':
            if (s, a) == (71, 18):
                return f"Topraktan sizi kesin ve güçlü bir yeniden çıkarışla dışarı çıkarma (`إِخْرَاجًا`, IV. bab {indef_note}mef'ûl-i mutlak masdar isim, {irab})"
            return f"İnsanları yurtlarından, dokunulmaz merkezden veya yuvasından zorla çıkarma eylemi (`إِخْرَاج`, IV. bab {indef_note}masdar isim, {irab})"
        elif lemma == 'xuruwj':
            if (s, a) in ((50, 11), (50, 42)):
                return f"Ölüm sonrası topraktan dirilip dışarı çıkış günü/olayı (`ٱلْخُرُوج`, I. bab masdar isim, {irab})"
            if (s, a) == (40, 11):
                return f"Bu yakıcı azap yurdundan dışarı çıkışa bir yol (`خُرُوجٍ`, I. bab {indef_note}masdar isim, {irab})"
            return f"Toplumsal mücadele veya sefer için yola çıkış (`ٱلْخُرُوج`, I. bab masdar isim, {irab})"
        elif lemma == 'muxoraj':
            if (s, a) == (17, 80):
                return f"Doğruluk, güvenlik ve onurla gerçekleştirilen çıkış şekli/noktası (`مُخْرَجَ`, IV. bab mîmli masdar/mekân isim, {irab})"
            if (s, a) == (15, 48):
                return f"Esenlik bahçesinden asla dışarı çıkarılacak olmayanlar (`بِمُخْرَجِينَ`, IV. bab çoğul edilgen ortaç isim, {irab})"
            if (s, a) == (26, 167):
                return f"Şehirden sürülüp dışarı atılanlardan biri (`ٱلْمُخْرَجِينَ`, IV. bab çoğul edilgen ortaç isim, {irab})"
            return f"Öldükten sonra topraktan kesinlikle dışarı çıkarılacak olanlar (`مُّخْرَجُونَ / لَمُخْرَجُونَ`, IV. bab çoğul edilgen ortaç isim, {irab})"
        elif lemma == '{sotaxoraja':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Gizlenmiş, gömülü veya denizin derinliğindeki değeri çabayla çekip çıkardı/çıkarırlar (`ٱسْتَخْرَجَ / يَسْتَخْرِجُ`, X. bab {tense} fiili, {x_pers}{x_mood})"
        elif lemma == 'muxorij':
            if (s, a) == (6, 95):
                return f"Canlı organizmadan cansız tohumu ve yumurtayı düzenli çıkaran (`وَمُخْرِجُ`, IV. bab etken ortaç isim, {irab})"
            return f"Gizlenmeye çalışılan suçu ve içteki hesabı kesinlikle dışarı çıkarıp açığa vuran (`مُخْرِجٌ`, IV. bab {indef_note}etken ortaç isim, {irab})"
        elif lemma == 'xaArij':
            return f"İçine düştüğü karanlıktan veya yıkım ateşinden asla kendi başına çıkabilen değil (`بِخَارِجٍ / بِخَٰرِجِينَ`, I. bab {indef_note}etken ortaç isim, {irab})"
        elif lemma == 'xaroj':
            return f"Hizmet ve koruma karşılığında toplumdan istenen veya sunulan maddi ücret/vergi (`خَرْجًا`, {indef_note}tekil eril isim, {irab})"
        elif lemma == 'xaraAj':
            return f"Yaradan'ın kullarına sürekli çıkardığı tertemiz rızık, verim ve ödül karşılığı (`فَخَرَاجُ`, tekil eril isim, {irab})"
        elif lemma == 'maxoraj':
            return f"Her türlü kuşatma ve darboğazdan kurtulup feraha ulaştıran çıkış kapısı (`مَخْرَجًا`, {indef_note}mekân/çıkış ismi, {irab})"

    elif root_ar == 'ص-ل-ح':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        sl_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3MD', '3. ikil eril'), ('3MP', '3. çoğul eril')]
        s_pers = next((v for k, v in sl_p if k in f), 'genel')
        s_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == '>aSolaHa':
            if 'IMPV' in f:
                if (s, a) in ((8, 1), (49, 9), (49, 10)):
                    return f"Aralarındaki bozulan ilişkiyi ve çekişmeyi hakkaniyetle düzeltip barıştırın (`أَصْلِحُوا۟`, IV. bab emir fiili, {s_pers})"
                if (s, a) == (7, 142):
                    return "Topluluğun içindeki düzeni koru, bozulanı onar ve düzelt (`وَأَصْلِحْ`, IV. bab emir fiili, 2. tekil eril)"
                return "Soyumu ve ardımdan gelecek kuşağı işlevsel, uyumlu ve sağlam kıl (`وَأَصْلِحْ`, IV. bab emir fiili, 2. tekil eril)"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) in ((10, 81), (26, 152), (27, 48)):
                return f"Bozguncuların işini amacına ulaştırıp düzene kavuşturmaz / yeryüzünü onarmazlar (`يُصْلِحُ / يُصْلِحُونَ`, IV. bab muzâri fiili, {s_pers})"
            if (s, a) in ((21, 90), (33, 71), (47, 2), (47, 5)):
                return f"Eşinin yapısını, amellerini veya iç dünyasını/halini onarıp dengeye kavuşturdu/kavuşturur (`أَصْلَحَ / يُصْلِحُ`, IV. bab {tense} fiili, {s_pers}{s_mood})"
            if (s, a) in ((2, 182), (2, 224), (4, 128), (4, 129), (42, 40)):
                return f"Taraflar arasındaki kırgınlığı ve haksızlık riskini giderip arayı düzeltti/düzeltir (`فَأَصْلَحَ / يُصْلِحَا`, IV. bab {tense} fiili, {s_pers}{s_mood})"
            return f"Hatadan döndükten sonra bozulmuş olanı eylemle telafi edip onardı (`أَصْلَحَ / أَصْلَحُوا۟`, IV. bab {tense} fiili, {s_pers}{s_mood})"
        elif lemma == 'SalaHa':
            return "Kendi hali, seçimi ve eylemiyle dengeye erişip uyumlu/elverişli olan (`صَلَحَ`, I. bab mâzî fiili, 3. tekil eril)"
        elif lemma == 'S~a`liHa`t':
            if (s, a) == (4, 34):
                return f"Güven ve sorumluluk bağını koruyup uyum sağlayan kadınlar (`فَٱلصَّٰلِحَٰتُ`, çoğul dişil etken ortaç isim, {irab})"
            if (s, a) in ((18, 46), (19, 76)):
                return f"Geçip giden süslerin aksine kalıcı değer ve yarar üreten yapıcı eylemler (`ٱلصَّٰلِحَٰتُ`, çoğul dişil isim, {irab})"
            return f"Bozulmayı gideren, yaşama ve topluma kalıcı yarar sağlayan yapıcı işler (`ٱلصَّٰلِحَٰتِ`, çoğul dişil isim, {irab})"
        elif lemma == 'Sa`liH':
            word_kind = "etken ortaç sıfat" if pos == 'ADJ' else "etken ortaç isim"
            if (s, a) in ((7, 189), (7, 190)):
                return f"Kusursuz, sağlıklı ve uyumlu bir çocuk/evlat (`صَٰلِحًا`, {indef_note}{word_kind}, {irab})"
            if (s, a) == (11, 46):
                return f"Gerçeklik ve sorumluluk ölçüsüne uygun düşen doğru bir iş (`صَٰلِحٍ`, {indef_note}{word_kind}, {irab})"
            if (s, a) == (18, 82):
                return f"Dürüst, güvenilir ve düzeni gözeten bir insan (`صَٰلِحًا`, {indef_note}{word_kind}, {irab})"
            if (s, a) == (66, 10):
                return f"Görev ve sorumluluk bilincini koruyan iki uyumlu kul (`صَٰلِحَيْنِ`, ikil {indef_note}{word_kind}, {irab})"
            if 'MP' in f:
                return f"Bozulmamış, dengeli, güvenilir ve yapıcı kimseler (`ٱلصَّٰلِحِينَ / ٱلصَّٰلِحُونَ`, çoğul {word_kind}, {irab})"
            return f"Yapıcı, onarıcı, dengeli ve yaşama faydalı olan iş/nitelenen (`صَٰلِحًا / ٱلصَّٰلِحُ`, tekil {indef_note}{word_kind}, {irab})"
        elif lemma == 'Sa`liH2':
            return f"Semûd toplumuna gönderilen elçi Sâlih (`صَٰلِح / يَٰصَٰلِحُ`, özel isim, {irab})"
        elif lemma == '<iSola`H':
            if (s, a) in ((7, 56), (7, 85)):
                return f"Yeryüzünün yaşamaya elverişli, sağlıklı ve dengeli düzenle kurulup onarılması (`إِصْلَٰحِهَا`, IV. bab masdar isim, {irab})"
            return f"Bozulmuş durumu, aile bağını, yetim hakkını veya toplum düzenini onarma niyeti ve eylemi (`إِصْلَاح`, IV. bab {indef_note}masdar isim, {irab})"
        elif lemma == 'muSoliH':
            return f"Bozulmayı fiilen durdurup çevresini ve toplumu onaran etken özneler (`مُصْلِحُونَ / ٱلْمُصْلِحِينَ`, IV. bab {'' if 'MP' in f or 'NOM' in f or 'ACC' in f else ''}etken ortaç isim, {irab})"
        elif lemma == 'SuloH':
            return f"Çatışmayı ve gerilimi bitiren ortak uzlaşma ve barış zemini (`صُلْحًا / وَٱلصُّلْحُ`, I. bab {indef_note}masdar isim, {irab})"

    elif root_ar == 'س-ب-ل':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        if 'MP' in f:
            if (s, a) in ((16, 15), (16, 69), (20, 53), (21, 31), (43, 10), (71, 20)):
                return f"Yeryüzünde, vadilerde ve canlıların doğasında akış için açılmış geçit ve rotalar (`سُبُلًا / سُبُلَ`, çoğul {indef_note}isim, {irab})"
            if (s, a) == (6, 153):
                return f"Ana eksenden bölünüp dağıtan dağınık yan yollar (`ٱلسُّبُلَ`, çoğul belirli isim, {irab})"
            return f"Barışa, kurtuluşa ve arınmaya açılan uyumlu uygulama yolları (`سُبُلَ / سُبُلَنَا`, çoğul isim, {irab})"
        if (s, a) in ((2, 177), (2, 215), (4, 36), (8, 41), (9, 60), (17, 26), (30, 38), (59, 7)):
            return f"Yolun oğlu terkibinde «yolda kalmış gezgin/yolcu» tamlamasının tamlananı (`ٱلسَّبِيلِ`, tekil belirli isim, {irab})"
        if (s, a) == (4, 43):
            return f"Duraklamadan yalnızca yolundan geçip giden gezgin (`عَابِرِى سَبِيلٍ`, tekil {indef_note}isim, {irab})"
        if (s, a) in ((2, 108), (5, 12), (5, 60), (5, 77), (28, 22), (60, 1)):
            return f"Aşırılık ve eksiklikten uzak, tam ortadaki dengeli ana rota (`سَوَآءَ ٱلسَّبِيلِ`, tekil belirli isim, {irab})"
        if (s, a) in ((3, 75), (4, 34), (4, 90), (4, 141), (9, 91), (9, 93), (42, 41), (42, 42)):
            return f"Üzerine gidilecek hukukî gerekçe, müdahale yetkisi ve kınama kapısı (`سَبِيلٌ / مِن سَبِيلٍ / ٱلسَّبِيلُ`, tekil {indef_note}isim, {irab})"
        if (s, a) in ((4, 76), (7, 146)):
            return f"Hedeflenen veya sakınılan bilinçli yöntem ve taraf rotası (`سَبِيلِ / سَبِيلًا`, tekil {indef_note}isim, {irab})"
        if (s, a) in ((4, 88), (4, 98), (4, 143), (17, 48), (25, 9), (40, 11), (42, 44), (42, 46)):
            return f"Kuşatma veya açmazdan kurtulup ilerlenecek çıkış ve çözüm yolu (`سَبِيلًا / مِن سَبِيلٍ`, tekil {indef_note}isim, {irab})"
        if (s, a) in ((4, 22), (17, 32)):
            return f"Davranış ve toplumsal sonuç bakımından varılan en kötü gidişat (`سَبِيلًا`, tekil {indef_note}isim / temyîz, {irab})"
        if (s, a) in ((18, 61), (18, 63)):
            return f"Balığın suyun içini yararak kendisine açtığı kaygan akış izi (`سَبِيلَهُۥ`, tekil isim + iyelik zamiri, {irab})"
        if (s, a) in ((15, 76), (29, 29), (3, 97), (80, 20)):
            return f"Hâlâ işlek duran fiziksel güzergâh, yolculuk imkânı veya yaşam geçiş yolu (`لَبِسَبِيلٍ / ٱلسَّبِيلَ`, tekil {indef_note}isim, {irab})"
        if (s, a) in ((2, 217), (3, 99), (4, 160), (4, 167), (6, 116), (6, 117), (7, 45), (7, 86), (8, 36), (8, 47), (9, 9), (9, 34), (10, 88), (11, 19), (13, 33), (14, 3), (14, 30), (16, 88), (16, 94), (16, 125), (22, 9), (22, 25), (27, 24), (29, 38), (31, 6), (33, 67), (38, 26), (39, 8), (40, 37), (43, 37), (47, 1), (47, 32), (47, 34), (53, 30), (58, 16), (63, 2), (68, 7)):
            return f"Önü tıkamaya çalışılan veya insanların kendisinden saptırıldığı açık ana rota (`سَبِيلِ / ٱلسَّبِيلِ / ٱلسَّبِيلَا۠`, tekil isim, {irab})"
        if (s, a) in ((17, 72), (17, 84), (25, 34), (25, 42), (25, 44)):
            return f"Gidişat, tutum ve yönelme bakımından izlenen rota (`سَبِيلًا`, tekil {indef_note}isim / temyîz, {irab})"
        return f"Engelsiz akışla yürünülen amaç koridoru, açık geçiş yolu veya tutulan yöntem (`سَبِيلِ / سَبِيلًا`, tekil {indef_note}isim, {irab})"

    elif root_ar == 'ت-ب-ع':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        tb_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MP', '3. çoğul eril')]
        t_pers = next((v for k, v in tb_p if k in f), 'genel')
        t_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == '{t~abaEa':
            if 'PASS' in f:
                tense = "mâzî" if 'PERF' in f else "muzâri"
                return f"Başkaları tarafından önder edinilip peşinden gidildi/gidilmeye layık olan (`ٱتُّبِعُوا۟ / يُتَّبَعَ`, VIII. bab edilgen {tense} fiili, {t_pers}{t_mood})"
            if 'IMPV' in f:
                if (s, a) in ((2, 168), (2, 208), (6, 142), (6, 153), (24, 21)):
                    return f"Bölünüp dağıtan yan yolları ve saptırıcı gücün adımlarını değil, tek ana rotayı takip edin (`ٱتَّبِعُوا۟ / لَا تَتَّبِعُوا۟`, VIII. bab emir fiili, {t_pers})"
                if (s, a) == (75, 18):
                    return "Vahiy okunuşu tamamlandığında adım adım o metni ve düzenini izle (`فَٱتَّبِعْ`, VIII. bab emir fiili, 2. tekil eril)"
                return f"Vahyi, elçiyi, en güzel sözü veya hakikat yolunu bilinçle izle/izleyin (`ٱتَّبِعْ / ٱتَّبِعُوا۟`, VIII. bab emir fiili, {t_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) in ((2, 120), (2, 145), (4, 135), (5, 48), (5, 49), (5, 77), (6, 56), (6, 150), (7, 176), (13, 37), (18, 28), (20, 16), (23, 71), (28, 50), (30, 29), (38, 26), (42, 15), (45, 18), (47, 14), (47, 16), (54, 3)):
                return f"Keyfî, bilgisiz veya tutkulu arzuların (`أَهْوَآء`) ardından gidiyor/gitti (`ٱتَّبَعَ / تَتَّبِعْ`, VIII. bab {tense} fiili, {t_pers}{t_mood})"
            if (s, a) in ((6, 116), (6, 148), (10, 36), (10, 66), (53, 23), (53, 28)):
                return f"Kesin kanıt yerine yalnızca sanının (`ٱلظَّنّ`) ardından giderler (`يَتَّبِعُونَ`, VIII. bab {tense} fiili, {t_pers})"
            return f"Seçtiği yolun, elçinin, vahyin veya topluluğun izini adım adım sürdü/sürer (`ٱتَّبَعَ / يَتَّبِعُ`, VIII. bab {tense} fiili, {t_pers}{t_mood})"
        elif lemma == '>atobaEa':
            if 'PASS' in f:
                return f"İşledikleri haksızlığın peşine bu dünyada da lanet ve dışlanmışlık takılıp yetiştirildi (`أُتْبِعُوا۟`, IV. bab edilgen mâzî fiili, {t_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) in ((18, 85), (18, 89), (18, 92)):
                return f"Amacına ulaşmak için imkân ve araç zincirinin peşinden yetişip onu işletti (`أَتْبَعَ / فَأَتْبَعَ`, IV. bab mâzî fiili, 3. tekil eril)"
            if (s, a) == (2, 262):
                return f"Yaptıkları paylaşımın peşine başa kakma ve incitici tutum eklemezler (`يُتْبِعُونَ`, IV. bab muzâri fiili, {t_pers})"
            return f"Kaçanın veya hedefin hemen arkasından hızla yetişip peşine taktı/takar (`فَأَتْبَعَهُ / نُتْبِعُهُمُ`, IV. bab {tense} fiili, {t_pers})"
        elif lemma == 'tabiEa':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) == (2, 263):
                return "Yaptığı bağışın arkasından incitici tutum gelmesi (`يَتْبَعُهَآ`, I. bab muzâri fiili, 3. tekil eril)"
            if (s, a) == (79, 7):
                return "İlk kozmik sarsıntının hemen ardından ikinci sarsıcı dalga gelir (`تَتْبَعُهَا`, I. bab muzâri fiili, 3. tekil dişil)"
            return f"Öndeki çağrının, kıblenin veya önderin ardından gidip izledi (`تَبِعَ / تَبِعُوا۟`, I. bab {tense} fiili, {t_pers})"
        elif lemma == 'taAbiE':
            if (s, a) == (24, 31):
                return f"Ev halkının hizmet ve bakımına bağlı erkek yardımcılar (`ٱلتَّٰبِعِينَ`, çoğul etken ortaç isim, {irab})"
            return f"Ötekinin yönelişini ve kıblesini kabul edip arkasından giden (`بِتَابِعٍ`, {indef_note}etken ortaç isim, {irab})"
        elif lemma == '{t~ibaAE':
            if (s, a) == (2, 178):
                return f"Kısasta hak sahibinin örfe uygun iyilikle talebi takip etmesi (`فَٱتِّبَاعٌۢ`, VIII. bab {indef_note}masdar isim, {irab})"
            return f"Kesin bilgiden yoksun olarak yalnızca kuruntunun peşinden gitme (`ٱتِّبَاعَ`, VIII. bab masdar isim, {irab})"
        elif lemma == 'mutataAbiEayon':
            return f"Aralarına kesinti ve boşluk girmeden art arda sıralanan iki ay (`مُتَتَابِعَيْنِ`, VI. bab ikil etken ortaç sıfat, {irab})"
        elif lemma == 'tabaE':
            return f"Önder sandıkları kimselerin iradesiz izleyicileri ve uydu kitlesi (`تَبَعًا`, {indef_note}tekil isim, {irab})"
        elif lemma == 'm~ut~abaEuwn':
            return f"Silahlı kuvvet tarafından arkanızdan kovalanıp adım adım izlenenlersiniz (`مُّتَّبَعُونَ`, VIII. bab çoğul edilgen ortaç isim, {irab})"
        elif lemma == 'tabiyE':
            return f"Hesap ve destek için bizim peşimize düşüp hak arayacak takipçi (`تَبِيعًا`, {indef_note}mübalağa/sıfat-isim, {irab})"

    elif root_ar == 'أ-و-ل':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        if lemma == '>aw~al':
            if pos == 'T':
                return "İlk ve başlangıç seferi/zamanı anlamında zaman zarfı (`أَوَّلَ`, tekil eril zaman zarfı, mansûb)"
            kind = "sıfat" if pos == 'ADJ' else "isim"
            if '|F|' in f or f.endswith('|F') or (s, a) in ((7, 38), (7, 39), (17, 5)):
                if (s, a) in ((28, 70), (53, 25), (79, 25), (92, 13), (93, 4)):
                    return f"Şu ilk ve geçici dünya evresi (`ٱلْأُولَىٰ`, dişil tekil {kind}, {irab})"
                if (s, a) in ((20, 133), (87, 18)):
                    return f"Önceki zamanlarda indirilmiş ilk yazılı sahifeler (`ٱلْأُولَىٰ`, dişil tekil {kind}, {irab})"
                return f"İlk hal, ilk yaratılış, önceki dönemler veya ilk ölüm (`ٱلْأُولَىٰ / أُولَىٰهُمْ / أُولَىٰهُمَا`, dişil tekil {kind}, {irab})"
            if 'MP' in f:
                return f"Önceki nesiller, geçmiş kuşaklar veya en önce öne atılan öncüler (`ٱلْأَوَّلِينَ / ٱلْأَوَّلُونَ`, çoğul eril {kind}, {irab})"
            return f"Başlangıç noktası, zamanın ilk halkası veya ilk adım atan özne (`أَوَّلُ / أَوَّلَ / لِأَوَّلِ`, tekil eril {kind}, {irab})"
        elif lemma == '>uwliY':
            if 'FP' in f:
                return f"Rahminde çocuk yükü taşıyan gebe kadınlar (`أُو۟لَٰتُ / أُو۟لَٰتِ`, dişil çoğul isim, {irab})"
            if (s, a) in ((2, 179), (2, 197), (2, 269), (3, 7), (3, 190), (5, 100), (12, 111), (13, 19), (14, 52), (38, 29), (38, 43), (39, 9), (39, 18), (39, 21), (40, 54), (65, 10)):
                return f"Olayların kabuğunu aşıp özüne eren derin akıl sahipleri (`أُو۟لُوا۟ / أُو۟لِى`, çoğul isim tamlaması başı, {irab})"
            if (s, a) in ((3, 13), (20, 54), (20, 128), (24, 44), (59, 2), (3, 18), (38, 45), (46, 35)):
                return f"Bilgi, derin kavrayış, kararlılık ve basiret donanımı sahipleri (`أُو۟لُوا۟ / أُو۟لِى`, çoğul isim, {irab})"
            return f"Belirli bir yakınlık, yetki, imkân, yükümlülük veya güç niteliğini kendinde taşıyanlar (`أُو۟لُوا۟ / أُو۟لِى`, çoğul isim, {irab})"
        elif lemma == "'aAl":
            if (s, a) in ((2, 49), (2, 50), (3, 11), (7, 130), (7, 141), (8, 52), (8, 54), (14, 6), (28, 8), (40, 28), (40, 45), (40, 46), (54, 41)):
                return f"Firavun iktidar çevresi, yönetimi ve hanedan kadrosu (`ءَالِ / ءَالَ / ءَالُ`, tekil isim tamlaması başı, {irab})"
            return f"Ortak bir başlangıç kaynağına ve elçilik çizgisine bağlı soy/hanedan çevresi (`ءَالَ / ءَالِ / ءَالُ`, tekil isim tamlaması başı, {irab})"
        elif lemma == 'ta>owiyl':
            if (s, a) in ((12, 6), (12, 21), (12, 36), (12, 37), (12, 44), (12, 45), (12, 100), (12, 101)):
                return f"Rüyaların ve tarihî olayların dönüp varacağı gerçek karşılık ve sonuç bilgisi (`تَأْوِيل`, II. bab masdar isim, {irab})"
            if (s, a) in ((7, 53), (10, 39)):
                return f"Haber verilen sonucun bizzat ortaya çıkıp gerçekleşme anı (`تَأْوِيلُهُۥ`, II. bab masdar isim, {irab})"
            if (s, a) in ((4, 59), (17, 35)):
                return f"Sonucu ve dönüşü bakımından en güzel akıbet ve hayırlı netice (`تَأْوِيلًا`, II. bab {indef_note}masdar isim / temyîz, {irab})"
            if (s, a) in ((18, 78), (18, 82)):
                return f"Görünüşte tahammül sınırını zorlayan eylemlerin perde arkasındaki nihai anlamı ve gayesi (`تَأْوِيل`, II. bab masdar isim, {irab})"
            return f"Sözün veya benzetmeli anlatımın asıl hakikatine döndürülüp açılması (`تَأْوِيلِهِۦ / تَأْوِيلَهُۥٓ`, II. bab masdar isim, {irab})"

    elif root_ar == 'ق-ت-ل':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        qt_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MD', '2. ikil'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MD', '3. ikil eril'), ('3MP', '3. çoğul eril'), ('3FP', '3. çoğul dişil')]
        q_pers = next((v for k, v in qt_p if k in f), 'genel')
        q_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == 'qatala':
            if 'PASS' in f:
                tense = "mâzî" if 'PERF' in f else "muzâri"
                if (s, a) in ((51, 10), (74, 19), (74, 20), (80, 17), (85, 4)):
                    return f"Asılsız kuruntuları ve inatları yüzünden ağır kınamayla devreden çıkarıldı (`قُتِلَ / فَقُتِلَ`, I. bab edilgen mâzî fiili, {q_pers})"
                return f"Can bağı kesilerek öldürüldü veya haksız/hakkaniyet yolunda öldürülür (`قُتِلَ / يُقْتَلُ`, I. bab edilgen {tense} fiili, {q_pers}{q_mood})"
            if 'IMPV' in f:
                if (s, a) == (2, 54):
                    return "Ağır sapmanın ardından birbirinizi arındırıcı yaptırımla cezalandırın (`فَٱقْتُلُوٓا۟`, I. bab emir fiili, 2. çoğul eril)"
                if (s, a) == (4, 66):
                    return "Sınav gereği canınızı feda edin (`ٱقْتُلُوٓا۟`, I. bab emir fiili, 2. çoğul eril)"
                return f"Size savaş açıp saldıran veya masuma kasteden kimseyi etkisiz kılıp öldürün (`ٱقْتُلُوا۟ / وَٱقْتُلُوهُمْ`, I. bab emir fiili, {q_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) == (4, 157) and '33' not in f:
                return f"Gerçeklikten kopuk sanıyla «öldürdük» dediler, oysa gerçekte öldürmediler ve kesin bilgiyle kuşatamadılar (`قَتَلْنَا / قَتَلُوهُ`, I. bab mâzî fiili, {q_pers})"
            return f"Canlı bir varlığın yaşam bağını keserek öldürdü veya öldürür (`قَتَلَ / يَقْتُلُ`, I. bab {tense} fiili, {q_pers}{q_mood})"
        elif lemma == 'qa`tala':
            if 'PASS' in f:
                tense = "mâzî" if 'PERF' in f else "muzâri"
                return f"Saldırıya ve savaşa maruz bırakıldılar/bırakılırsanız (`يُقَٰتَلُونَ / قُوتِلُوا۟`, III. bab edilgen {tense} fiili, {q_pers})"
            if 'IMPV' in f:
                return f"Saldıran, antlaşmayı bozan veya azgınlık eden karşı güce karşı savunma savaşı verin (`قَٰتِلُوا۟ / فَقَٰتِلْ`, III. bab emir fiili, {q_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) in ((9, 30), (63, 4)):
                return "Yaratıcı onların saptırıcı düzenini ve iddiasını boşa çıkarıp saf dışı bıraksın (`قَٰتَلَهُمُ`, III. bab mâzî fiili, 3. tekil eril)"
            return f"Karşı tarafla silahlı çarpışmaya girer veya savaştı (`قَٰتَلَ / يُقَٰتِلُ`, III. bab {tense} fiili, {q_pers}{q_mood})"
        elif lemma == 'qitaAl':
            return f"İki taraf arasındaki karşılıklı savunma veya saldırı savaşı (`ٱلْقِتَال / قِتَالًا`, III. bab {indef_note}masdar isim, {irab})"
        elif lemma == 'qatol':
            return f"Bir canı, çocuğu veya elçiyi doğrudan öldürme eylemi (`ٱلْقَتْل / قَتْلَ`, I. bab masdar isim, {irab})"
        elif lemma == '{qotatala':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Aynı topluluk içindeki veya iki kişi arasındaki karşılıklı boğuşup çatışma (`ٱقْتَتَلَ / يَقْتَتِلَانِ`, VIII. bab {tense} fiili, {q_pers})"
        elif lemma == 'qut~ilu':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            voice = "edilgen " if 'PASS' in f else ""
            return f"Toplu, sistemli ve ağır biçimde kıyılıp öldürülür/öldürüldüler (`يُقَتِّلُونَ / وَقُتِّلُوا۟`, II. bab {voice}{tense} fiili, {q_pers}{q_mood})"
        elif lemma == 'qatolaY':
            return f"Haksız yere öldürülüp yaşamı sonlandırılan kimseler (`ٱلْقَتْلَى`, çoğul isim, {irab})"
        elif lemma == 'taqotiyl':
            return f"Bozguncuların hiçbir boşluk bırakmadan tam ve ağır biçimde ortadan kaldırılması (`تَقْتِيلًا`, II. bab {indef_note}mef'ûl-i mutlak masdar isim, {irab})"

    elif root_ar == 'م-ث-ل':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        if lemma == 'tamav~ala':
            return "Gönderilen mesaj ve dirilik elçisi Meryem'in karşısında dengeli, tam bir insan görünümüne/suretine büründü (`فَتَمَثَّلَ`, V. bab mâzî fiili, 3. tekil eril)"
        elif lemma == 't~amaAviyl':
            return f"Canlı veya görkemli biçimlere benzetilerek yontulmuş temsili heykeller (`ٱلتَّمَاثِيلُ / تَمَٰثِيلَ`, çoğul isim, {irab})"
        elif lemma == 'mavula`t':
            return f"Önceki toplumların başına gelip gelecek nesillere ibret numunesi olmuş tarihsel yıkım örnekleri (`ٱلْمَثُلَٰتُ`, dişil çoğul isim, {irab})"
        elif lemma == 'muvolaY`':
            return f"Örnek alınmaya en uygun, en üstün ve seçkin görülen düzen/yöntem (`ٱلْمُثْلَىٰ`, dişil elatif sıfat, {irab})"
        elif lemma == '>amoval':
            return f"Görüş, denge ve anlayış bakımından topluluğun örneğe en yakın ve en aklı başında olanı (`أَمْثَلُهُمْ`, eril tekil elatif isim, {irab})"
        elif lemma == 'maval':
            kind = "sıfat" if pos == 'ADJ' else "isim"
            if (s, a) in ((16, 60), (30, 27)) and ('ٱلْمَثَلُ' in f or (s, a) in ((16, 60), (30, 27))):
                if (s, a) == (30, 27):
                    return f"Yaratıcıya özgü en yüce, eşsiz ve kusursuz niteleme/temsil (`ٱلْمَثَلُ`, tekil eril isim, {irab})"
                return f"Zihni hakikate yükselten en yüce niteleme yahut tutarsız kıyas modeli (`مَثَلُ / ٱلْمَثَلُ`, tekil eril isim, {irab})"
            if 'MP' in f:
                if (s, a) == (6, 160):
                    return f"Yapılan güzel eylemin tam on katı denk karşılıklar (`أَمْثَالِهَا`, kırık çoğul isim, {irab})"
                if pos == 'ADJ':
                    return f"Sizler gibi birer canlı ve sorumlu topluluklar/benzerler (`أَمْثَالُكُم`, kırık çoğul sıfat, {irab})"
                return f"Hakikati somutlaştıran örnek tablolar veya sizler/onlar gibi aynı nitelikteki benzer nesiller (`ٱلْأَمْثَالَ / أَمْثَالُكُم`, kırık çoğul isim, {irab})"
            return f"Soyut hakikati veya bir topluluğun halini zihinde canlandıran örnek model ve benzetme (`مَثَلُ / مَثَلًا / كَمَثَلِ`, tekil eril {indef_note}{kind}, {irab})"
        elif lemma == 'mivol':
            if 'MD' in f:
                return f"Görünen sayısının veya yaşanan sonucun tam iki katı/iki misli (`مِّثْلَيْهِمْ / مِّثْلَيْهَا`, ikil isim, {irab})"
            if (s, a) == (42, 11):
                return f"Yaratıcıya özdeş, eş veya denk hiçbir varlık yokluğunda tekil denk kavram (`كَمِثْلِهِۦ`, tekil isim, {irab})"
            if (s, a) in ((11, 27), (14, 10), (14, 11), (18, 110), (21, 3), (23, 24), (23, 33), (23, 34), (23, 47), (26, 154), (26, 186), (36, 15), (41, 6)):
                return f"İnsani yapı ve yaradılış bakımından sizinle eşit olan ölümlü insan (`مِّثْلُكُمْ / مِّثْلُنَا`, tekil isim, {irab})"
            if (s, a) in ((2, 194), (2, 228), (2, 233), (4, 11), (4, 176), (5, 95), (6, 160), (10, 27), (16, 126), (22, 60), (40, 40), (42, 40), (60, 11)):
                return f"Ölçü, hak, ceza ve tazminatta taşmayan birebir denk karşılık (`مِثْلُ / بِمِثْلِ / مِثْلَهَا`, tekil isim, {irab})"
            return f"Nitelik, yapı, söz veya güç bakımından birebir eşdeğer benzeri (`مِثْلُ / مِّثْلِ`, tekil isim, {irab})"

    elif root_ar == 'ق-ل-ب':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        ql_p = [('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MP', '3. çoğul eril'), ('1P', '1. çoğul')]
        q_pers = next((v for k, v in ql_p if k in f), 'genel')
        q_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == 'qalob':
            if 'FD' in f:
                return f"Aynı gövde içinde iki ayrı karar merkezi/kalp (`قَلْبَيْنِ`, ikil {indef_note}isim, {irab})"
            if 'FP' in f:
                return f"Düşünce, kavrayış, niyet, duygu ve karar değişiminin merkezi olan kalpler (`قُلُوب / ٱلْقُلُوب`, çoğul {indef_note}isim, {irab})"
            return f"İçsel biliş, akletme ve karar dönüşümünün merkezi olan kalp (`قَلْب / قَلْبُكَ / بِقَلْبٍ`, tekil {indef_note}isim, {irab})"
        elif lemma == '{nqalaba':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) in ((2, 143), (3, 144), (3, 149), (5, 21), (22, 11)):
                return f"Tuttuğu yoldan yüz veya topukları üstüne gerisin geri döner/döndü (`يَنقَلِبُ / ٱنقَلَبَ`, VII. bab {tense} fiili, {q_pers}{q_mood})"
            return f"Yaşadığı sınavdan hüsran, nimet yahut akıbetle geri döner/döndü (`ٱنقَلَبَ / يَنقَلِبُونَ`, VII. bab {tense} fiili, {q_pers}{q_mood})"
        elif lemma == 'qal~abu':
            if 'PASS' in f:
                return f"Yüzleri yakıcı azap içinde evrilip çevrilir (`تُقَلَّبُ`, II. bab edilgen muzâri fiili, {q_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Gönülleri, bedenleri, gece-gündüzü, avuçları veya işleri halden hale evirip çevirir/çevirdi (`يُقَلِّبُ / قَلَّبُوا۟`, II. bab {tense} fiili, {q_pers})"
        elif lemma == 'taqal~ub':
            return f"Beldelerdeki, zaman içindeki veya yöneliş anındaki gidip gelme ve hal değiştirme hareketliliği (`تَقَلُّب`, V. bab masdar isim, {irab})"
        elif lemma == 'munqalibuwn':
            return f"Bütün dönüşümün ardından kesinlikle Yaratıcımıza geri dönüp varacak olanlarız (`مُنقَلِبُونَ`, VII. bab çoğul etken ortaç isim, {irab})"
        elif lemma == 'munqalab':
            return f"Sürecin sonunda ters yüz edilip varılan devrilme ve akıbet yeri (`مُنقَلَب`, VII. bab {indef_note}mekân/masdar isim, {irab})"
        elif lemma == 'tataqal~abu':
            return f"Kalplerin ve gözlerin dehşetle halden hale evrilip döneceği (`تَتَقَلَّبُ`, V. bab muzâri fiili, 3. tekil dişil)"
        elif lemma == 'tuqolabu':
            return f"Zaman dolduğunda bütünüyle O'nun huzuruna döndürülüp çevrileceksiniz (`تُقْلَبُونَ`, I. bab edilgen muzâri fiili, 2. çoğul eril)"
        elif lemma == 'mutaqal~ab':
            return f"Gündüz boyu dönüp dolaştığınız yaşam ve hareket alanınız (`مُتَقَلَّبَكُمْ`, V. bab mekân/masdar isim, {irab})"

    elif root_ar == 'ش-ر-ك':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        sr_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MP', '3. çoğul eril'), ('3FP', '3. çoğul dişil')]
        s_pers = next((v for k, v in sr_p if k in f), 'genel')
        s_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == '>a$oraka':
            if 'PASS' in f:
                return f"Tek Yaratıcıya ikinci bir yetki veya varlık paydaş kılınır/koşulur (`يُشْرَكَ / يُشْرَكْ`, IV. bab edilgen muzâri fiili, {s_pers}{s_mood})"
            if 'IMPV' in f or (s, a) == (20, 32):
                return f"Kardeşim Harun'u da yürüttüğüm tebliğ ve yönetim görevine ortak kıl (`وَأَشْرِكْهُ`, IV. bab emir fiili, {s_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Tek ve eşsiz olana başka odakları yetki, dua veya sadakat bakımından paydaş koşar/koştu (`يُشْرِكُ / أَشْرَكَ`, IV. bab {tense} fiili, {s_pers}{s_mood})"
        elif lemma == 'mu$orik':
            if 'MP' in f:
                return f"Tek Yaratıcının yetki ve yöneliş alanına başka paydaşlar katanlar (`ٱلْمُشْرِكُونَ / ٱلْمُشْرِكِينَ`, IV. bab çoğul eril etken ortaç isim, {irab})"
            return f"Tek Yaratıcıya başka otoriteleri paydaş koşan tekil erkek özne (`مُشْرِكٌ / مُّشْرِكٍ`, IV. bab {indef_note}tekil eril etken ortaç isim, {irab})"
        elif lemma == '$ariyk':
            if 'MP' in f:
                if (s, a) == (4, 12):
                    return f"Mirasın üçte bir payı üzerinde eşit hak sahibi ortaklar (`شُرَكَآءُ`, {indef_note}kırık çoğul isim, {irab})"
                if (s, a) == (7, 190):
                    return f"Sağlıklı evlat nimetine kavuşunca o nimetin şükrüne kattıkları düzmece ortaklar (`شُرَكَآءَ`, {indef_note}kırık çoğul isim, {irab})"
                if (s, a) == (30, 28):
                    return f"Size verilen rızık ve mülklerde aynı hakla paydaş saydığınız eşit ortaklar (`شُرَكَآءُ`, {indef_note}kırık çoğul isim, {irab})"
                if (s, a) == (39, 29):
                    return f"Birbirleriyle sürekli çekişen ve uyuşamayan çok başlı ortak sahipler (`شُرَكَآءُ`, {indef_note}kırık çoğul isim, {irab})"
                if (s, a) == (42, 21):
                    return f"İlâhî izin olmaksızın yaşam düzeninde yeni kurallar koyan yetki ortakları (`شُرَكَٰٓؤُا۟`, kırık çoğul isim, {irab})"
                if (s, a) in ((6, 136), (6, 137), (6, 139)):
                    return f"Tarım ve hayvan ürünlerinden pay ayırarak düzmece hak sahibi saydıkları sahte ortakları (`لِشُرَكَآئِهِمْ / شُرَكَآؤُهُمْ`, kırık çoğul isim, {irab})"
                return f"Yetki, dua, kurtuluş yahut mülkiyette paydaş varsayılan düzmece ortaklar (`شُرَكَآء`, {indef_note}kırık çoğul isim, {irab})"
            return f"Yönetim, mülk ve ilâhîlıkta yanında bulunan hiçbir tekil ortak/paydaş (`شَرِيك / شَرِيكٌ`, {indef_note}tekil eril isim, {irab})"
        elif lemma == '$irok':
            if (s, a) == (31, 13):
                return f"Eşsiz Yaratıcıya paydaş yakıştırma eylemi (`ٱلشِّرْكَ`, belirli masdar isim, {irab})"
            if (s, a) == (35, 14):
                return f"Dünyada kendilerine kurduğunuz yetki ve paydaşlık bağını (`بِشِرْكِكُمْ`, iyelikli harf-i cerli masdar isim, {irab})"
            return f"Göklerde yahut yerde yaratma ve mülkiyete dair en küçük bir pay/ortaklık hissesi (`شِرْكٍ / شِرْكٌ`, {indef_note}masdar isim, {irab})"
        elif lemma == 'mu$orika`t':
            return f"Tek olana başka paydaşlar katan kadınlar (`ٱلْمُشْرِكَٰت`, IV. bab dişil çoğul etken ortaç isim, {irab})"
        elif lemma == 'mu$orikap':
            return f"Tek Yaratıcıya başka paydaşlar katan tekil kadın özne (`مُشْرِكَةٍ / مُشْرِكَةٌ`, IV. bab {indef_note}tekil dişil etken ortaç isim, {irab})"
        elif lemma == 'mu$otarikuwn':
            return f"Yanlış tercihlerinin ardından kaçınılmaz azapta birbirine eşit ortak düşenler (`مُشْتَرِكُونَ`, VIII. bab çoğul eril etken ortaç isim, {irab})"
        elif lemma == '$aAriko':
            return f"Mal birikiminde ve nesil süreçlerinde onlara sızıp ortaklık kur (`وَشَارِكْهُمْ`, III. bab emir fiili, 2. tekil eril)"

    elif root_ar == 'ك-ث-ر':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        if lemma == '>akovar':
            if pos == 'ADJ':
                if (s, a) == (18, 54):
                    return f"Çekişme ve tartışma üretmede her şeyden daha fazla ve ileri olan (`أَكْثَرَ`, tekil eril ism-i tafdîl sıfat, {irab})"
                return f"Üzerinde görüş ayrılığına düştüklerinin pek çoğunu ve en büyük kısmını (`أَكْثَرَ`, tekil eril ism-i tafdîl sıfat, {irab})"
            if (s, a) == (4, 12):
                return f"Sayıca bundan/ikiden daha fazla olan anne-bir kardeşler (`أَكْثَرَ`, tekil eril ism-i tafdîl isim, {irab})"
            if (s, a) in ((9, 69), (17, 6), (18, 34), (34, 35)):
                return f"Mal, nesil ve destekçi sayısı bakımından daha kalabalık ve kabarık (`أَكْثَرَ / أَكْثَرُ`, tekil eril ism-i tafdîl isim, {irab})"
            if (s, a) == (58, 7):
                return f"Üçten veya beşten sayıca daha fazla olan gizli topluluk (`أَكْثَرَ`, tekil eril ism-i tafdîl isim, {irab})"
            return f"İnsanların veya anılan grubun sayısal çoğunluğu ve baskın kesimi (`أَكْثَرُ / أَكْثَرَ`, tekil eril ism-i tafdîl isim, {irab})"
        elif lemma == 'kaviyr':
            pos_tr = "sıfat" if pos == 'ADJ' else "isim"
            if (s, a) in ((2, 269), (4, 19)):
                return f"Sayıca geniş ve kapsamlı hayır/iyilik (`كَثِيرًا`, tekil eril {indef_note}{pos_tr}, {irab})"
            if (s, a) in ((3, 41), (20, 33), (20, 34), (33, 35), (33, 41)):
                return f"Durmaksızın tekrarlanan yoğun ve çokça anış/tesbih (`كَثِيرًا`, tekil eril {indef_note}{pos_tr}, {irab})"
            if (s, a) == (4, 82):
                return f"İçinde birbiriyle çelişen pek çok tutarsızlık (`كَثِيرًا`, tekil eril {indef_note}{pos_tr}, {irab})"
            if (s, a) == (4, 100):
                return f"Yeryüzünde genişlik ve bol sığınak alanı (`كَثِيرًا`, tekil eril {indef_note}{pos_tr}, {irab})"
            if (s, a) in ((4, 1), (25, 49), (36, 62)):
                return f"Sayıca kabarık ve kalabalık insan kitleleri/nesilleri (`كَثِيرًا`, tekil eril {indef_note}{pos_tr}, {irab})"
            return f"Sayı, hacim, çeşitlilik veya etki bakımından pek çok olan (`كَثِيرًا / كَثِيرٌ / كَثِيرٍ`, tekil eril {indef_note}{pos_tr}, {irab})"
        elif lemma == 'kaviyrap':
            if (s, a) == (2, 245):
                return f"Kat kat artırılan sayısız karşılık/katlamalar (`كَثِيرَةً`, tekil dişil belirsiz sıfat, {irab})"
            if (s, a) == (2, 249):
                return f"Sayıca kabarık ve görkemli topluluk (`كَثِيرَةًۢ`, tekil dişil belirsiz sıfat, {irab})"
            if (s, a) == (9, 25):
                return f"Pek çok önceki buluşma ve saha meydanları (`كَثِيرَةً`, tekil dişil belirsiz sıfat, {irab})"
            if (s, a) in ((4, 94), (48, 19), (48, 20)):
                return f"Bol ekonomik ve saha kazanımları (`كَثِيرَةً`, tekil dişil belirsiz sıfat, {irab})"
            return f"Sayısız ve bereketli meyveler yahut çok sayıda yarar (`كَثِيرَةٌ / كَثِيرَةٍ`, tekil dişil belirsiz sıfat, {irab})"
        elif lemma == '{sotakovaro':
            if (s, a) == (6, 128):
                return f"İnsan topluluklarından pek çoğunu peşinize takıp sömürerek çoğalttınız (`ٱسْتَكْثَرْتُم`, X. bab mâzî fiili, 2. çoğul eril)"
            if (s, a) == (7, 188):
                return f"Elbette iyilikten/hayırdan bolca devşirir çoğaltırdım (`لَٱسْتَكْثَرْتُ`, X. bab mâzî fiili, 1. tekil)"
            return f"Verdiğini gözünde büyütüp karşılığında daha fazlasını bekleyerek iyilik yapma (`تَسْتَكْثِرُ`, X. bab muzâri fiili, 2. tekil eril)"
        elif lemma == 'kavura':
            if (s, a) == (4, 7):
                return f"Bırakılan malın az olmasına karşın miktarca çok olması (`كَثُرَ`, I. bab mâzî fiili, 3. tekil eril)"
            return f"Sayıca kalabalıklaşıp kabarsa bile (`كَثُرَتْ`, I. bab mâzî fiili, 3. tekil dişil)"
        elif lemma == 'kavorap':
            if (s, a) == (5, 100):
                return f"Değersiz ve kirli olanın göz alıcı sayısal çokluğu (`كَثْرَةُ`, tekil dişil masdar isim, {irab})"
            return f"Kendinize güvendiğiniz sayısal kalabalığınız (`كَثْرَتُكُمْ`, iyelikli tekil dişil masdar isim, {irab})"
        elif lemma == '>akovaru':
            if (s, a) == (11, 32):
                return f"Bizimle tartışmayı gereğinden fazla uzatıp çoğalttın (`فَأَكْثَرْتَ`, IV. bab mâzî fiili, 2. tekil eril)"
            return f"Oralarda bozgunculuk ve yozlaşmayı yaygınlaştırıp çoğalttılar (`فَأَكْثَرُوا۟`, IV. bab mâzî fiili, 3. çoğul eril)"
        elif lemma == 't~akaAvur':
            if (s, a) == (57, 20):
                return f"Mal ve evlat sayısında birbirini geçip çoğaltma yarışı (`وَتَكَاثُرٌ`, VI. bab belirsiz masdar isim, {irab})"
            return f"Sayısal biriktirme ve birbirine üstünlük taslama yarışı (`ٱلتَّكَاثُرُ`, VI. bab belirli masdar isim, {irab})"
        elif lemma == 'kav~ara':
            return f"Az bir toplulukken sizi çoğaltıp sayıca büyüttü (`فَكَثَّرَكُمْ`, II. bab mâzî fiili, 3. tekil eril)"
        elif lemma == 'kawovar':
            return f"Tükenmez bereket, duru kaynak ve taşkın hayır bütünlüğü (`ٱلْكَوْثَرَ`, belirli tekil eril mübalağa ismi, {irab})"

    elif root_ar == 'س-و-أ':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        sw_p = [('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MP', '3. çoğul eril')]
        sw_pers = next((v for k, v in sw_p if k in f), 'genel')
        sw_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == "suw^'":
            if (s, a) in ((20, 22), (27, 12), (28, 32)):
                return f"Hastalık, alaca leke veya hiçbir bedensel kusur olmaksızın (`مِنْ غَيْرِ سُوٓءٍ`, tekil eril {indef_note}isim, {irab})"
            if (s, a) in ((2, 49), (7, 141), (7, 167), (14, 6)):
                return f"Katlanılması zor, yüz buruşturan en ağır baskı ve yıkıcı ceza (`سُوٓءَ`, tekil eril isim, {irab})"
            if (s, a) in ((12, 24), (12, 25), (12, 51), (12, 53)):
                return f"İffet sınırını çiğneyen yakışıksız saldırı veya dürtü (`سُوٓء`, tekil eril {indef_note}isim, {irab})"
            if (s, a) in ((7, 73), (11, 64), (26, 156)):
                return f"Canlıya zarar ve eziyet dokundurma (`بِسُوٓءٍ`, harf-i cerli tekil eril {indef_note}isim, {irab})"
            if (s, a) in ((4, 17), (4, 110), (4, 123), (6, 54), (16, 119), (27, 11)):
                return f"Düşüncesizce veya bilgisizce işlenen zarar verici ve çirkin davranış (`سُوٓءًا`, tekil eril {indef_note}isim, {irab})"
            if (s, a) in ((4, 148), (4, 149)):
                return f"Kırıcı, çirkin ve zarar verici söz veya davranış (`ٱلسُّوٓءِ / سُوٓءٍ`, tekil eril {indef_note}isim, {irab})"
            return f"İnsanı kedere boğan çirkinlik, zarar, kusur yahut olumsuz sonuç (`سُوٓء / ٱلسُّوٓء`, tekil eril {indef_note}isim, {irab})"
        elif lemma == 'say~i_#aAt':
            num_tr = "dişil çoğul" if 'FP' in f else "dişil"
            if (s, a) in ((2, 271), (3, 193), (3, 195), (4, 18), (4, 31), (5, 12), (5, 65), (7, 153), (7, 168), (8, 29), (25, 70), (29, 7), (46, 16), (47, 2), (48, 5), (64, 9), (65, 5), (66, 8)):
                return f"Güzellik ve bağışla üstü örtülüp temizlenen çirkin davranış izleri (`سَيِّـَٔات`, {num_tr} isim, {irab})"
            if (s, a) == (11, 114):
                return f"Güzel ve dürüst eylemlerin silip götürdüğü olumsuz işler (`ٱلسَّيِّـَٔاتِ`, {num_tr} isim, {irab})"
            return f"Kişinin işlediği ve karşılığı açığa çıkan çirkin eylemler (`سَيِّـَٔات`, {num_tr} isim, {irab})"
        elif lemma == "saA^'a":
            if 'PASS' in f:
                if (s, a) == (67, 27):
                    return f"Yüzleri derin keder ve dehşetle kararıp bozuldu (`سِيٓـَٔتْ`, I. bab edilgen mâzî fiili, {sw_pers})"
                return f"İçine ağır bir sıkıntı ve keder çöktü (`سِىٓءَ`, I. bab edilgen mâzî fiili, {sw_pers})"
            if 'IMPF' in f:
                if (s, a) == (17, 7):
                    return f"Yüzlerinizi keder ve bozgunla karartıp çirkinleştirsinler (`لِيَسُـُٔوا۟`, I. bab muzâri fiili, {sw_pers}{sw_mood})"
                return f"Sizi veya onları kederlendirip üzecek (`تَسُؤْ`, I. bab muzâri fiili, {sw_pers}{sw_mood})"
            return f"Ne çirkin, yakışıksız ve keder verici oldu (`سَآءَ / سَآءَتْ`, yergi bildiren I. bab mâzî fiili, {sw_pers})"
        elif lemma == 'say~i}ap':
            if pos == 'ADJ':
                return f"Zararlı, çirkin ve haksız bir aracılık/yönlendirme (`سَيِّئَةً`, tekil dişil belirsiz sıfat, {irab})"
            if (s, a) in ((6, 160), (10, 27), (13, 22), (23, 96), (28, 54), (28, 84), (40, 40), (41, 34), (42, 40)):
                return f"İyilikle dengelenip dönüştürülen yahut denk karşılık getiren çirkin davranış (`سَيِّئَة`, tekil dişil {indef_note}isim, {irab})"
            return f"İnsana isabet eden sıkıntı, bozulma yahut olumsuz davranış (`سَيِّئَة`, tekil dişil {indef_note}isim, {irab})"
        elif lemma == "sawo'":
            if (s, a) in ((9, 98), (48, 6), (48, 12)):
                return f"İnsanın içine düştüğü yıkım döngüsü veya çarpık karamsar zan (`ٱلسَّوْءِ`, tekil eril isim, {irab})"
            if (s, a) in ((19, 28), (21, 74), (21, 77)):
                return f"Ahlaken yozlaşmış, yakışıksız ve çirkin tutumlu (`سَوْءٍ`, tekil eril belirsiz isim, {irab})"
            if (s, a) == (16, 60):
                return f"Hakikatten kopanlara özgü en çirkin niteleme (`ٱلسَّوْءِ`, tekil eril isim, {irab})"
            return f"Yıkıcı ve dehşet verici felaket (`ٱلسَّوْءِ`, tekil eril isim, {irab})"
        elif lemma == "sawo'a`t":
            n_tr = "dişil çoğul" if 'FP' in f else "dişil"
            return f"Açığa çıktığında insanı mahcup edip üzen çıplaklık ve beden bölgeleri (`سَوْءَٰت`, {n_tr} isim, {irab})"
        elif lemma == ">asaA^'a":
            return f"Bilinçli olarak çirkin, bozuk ve zarar verici iş işledi/işlediniz (`أَسَآءَ / أَسَٰٓـُٔوا۟ / أَسَأْتُمْ`, IV. bab mâzî fiili, {sw_pers})"
        elif lemma == 'say~i}':
            if pos == 'ADJ':
                if (s, a) == (9, 102):
                    return f"Dürüst eyleme karıştırılmış bozuk ve çirkin iş (`سَيِّئًا`, tekil eril {indef_note}sıfat, {irab})"
                return f"Sahibini kuşatan hain ve çirkin tuzak (`ٱلسَّيِّئُ / ٱلسَّيِّئِ`, tekil eril sıfat, {irab})"
            return f"Bu sayılan tüm davranışların çirkin ve hoş görülmeyen yönü (`سَيِّئُهُۥ`, tekil eril isim, {irab})"
        elif lemma == "sawo'ap":
            return f"Kardeşinin açıkta kalması insanı dehşete düşüren cansız bedeni (`سَوْءَةَ`, tekil dişil isim, {irab})"
        elif lemma == '>asowa>':
            if (s, a) == (39, 35):
                return f"Yaptıkları davranışların en çirkin ve kusurlu olanını dahi (`أَسْوَأَ`, tekil eril ism-i tafdîl isim, {irab})"
            return f"Yapageldiklerinin en çirkin ve ağır karşılığını (`أَسْوَأَ`, tekil eril ism-i tafdîl isim, {irab})"
        elif lemma == 's~uw^>aY`^':
            return f"Çirkinlikte ısrar edenlerin varacağı en nahoş ve yakıcı akıbet (`ٱلسُّوٓأَىٰٓ`, `فُعْلَى` en üstünlük ismi, {irab})"
        elif lemma == "musiY^'":
            return f"Yolunu bilinçli olarak bozgun, zarar ve çirkinlik üretmeye çeviren kimse (`ٱلْمُسِىٓءُ`, IV. bab etken ortaç isim, {irab})"

    elif root_ar == 'م-و-ت':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        mw_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MP', '3. çoğul eril')]
        m_pers = next((v for k, v in mw_p if k in f), 'genel')
        m_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == 'mawot':
            if (s, a) in ((2, 164), (16, 65), (29, 63), (30, 19), (30, 24), (30, 50), (35, 9), (45, 5), (57, 17)):
                return f"Toprağın yağmursuz kalıp bitki çıkaramaz hale gelmesi ve kuruma evresi (`مَوْتِهَا / مَوْتِهِ`, tekil eril isim, {irab})"
            if (s, a) == (67, 2):
                return f"Yaşamla birlikte kimin daha güzel iş yapacağını sınamak üzere yaratılan ölüm olgusu (`ٱلْمَوْتَ`, tekil eril isim, {irab})"
            if (s, a) in ((3, 185), (21, 35), (29, 57)):
                return f"Her canlı özün mutlaka tadıp içinden geçeceği kaçınılmaz ölüm eşiği (`ٱلْمَوْتِ`, tekil eril isim, {irab})"
            if (s, a) == (39, 42):
                return f"Canlının bedensel gücünün tamamen çekilip uykudan ayrılan gerçek ölüm anı (`مَوْتِهَا / ٱلْمَوْتَ`, tekil eril isim, {irab})"
            return f"Canlılığın ve bedensel devinimin durduğu geçici ayrılış ve ölüm hali (`ٱلْمَوْت / مَوْت`, tekil eril {indef_note}isim, {irab})"
        elif lemma == 'm~aAta':
            if 'PASS' in f:
                return f"Ölüp toprağa karıştık/karıştınız mı (`مِتْنَا / مِتُّمْ`, I. bab edilgen mâzî fiili, {m_pers})"
            if 'IMPV' in f:
                if (s, a) == (3, 119):
                    return f"Kendi öfke ve kininizle eriyip ölün (`مُوتُوا۟`, I. bab emir fiili, {m_pers})"
                return f"Ölüp yaşam gücünüzü yitirin (`مُوتُوا۟`, I. bab emir fiili, {m_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Yaşam gücünü yitirip bedensel işlevden kesilir/kesildi (`مَاتَ / يَمُوتُ`, I. bab {tense} fiili, {m_pers}{m_mood})"
        elif lemma == 'm~ay~it':
            if pos == 'ADJ':
                if 'P' in f:
                    return f"Ölü durumundaki canlıları veya kurumuş varlıkları diriltilen (`ٱلْمَوْتَىٰ`, çoğul sıfat, {irab})"
                return f"Yağmursuz kalıp ürün verme gücünü yitirmiş kurak belde (`مَّيِّتٍ`, tekil eril {indef_note}sıfat, {irab})"
            if (s, a) in ((2, 154), (3, 169)):
                return f"Bilinç ve canlılık boyutunu bütünüyle yitirmiş ölüler (`أَمْوَٰتٌ / أَمْوَٰتًۢا`, çoğul {indef_note}isim, {irab})"
            if (s, a) in ((6, 36), (27, 80), (30, 52), (35, 22)):
                return f"Çağrıya ve düşünmeye tepki veremeyen bilinç ölüleri (`ٱلْمَوْتَىٰ / ٱلْأَمْوَٰتُ`, çoğul isim, {irab})"
            if (s, a) in ((23, 15), (37, 58), (39, 30)):
                return f"Ölümlü olup vakti gelince yaşam evresini tamamlayacak olan/olanlar (`مَيِّتٌ / مَيِّتُونَ`, {'çoğul' if 'MP' in f else 'tekil eril'} {indef_note}isim, {irab})"
            num_tr = "çoğul" if ('P' in f or 'MP' in f) else "tekil eril"
            return f"Canlılığını ve bedensel devinimini yitirmiş ölü varlık veya toprak (`مَيِّت / مَوْتَىٰ / أَمْوَٰت`, {indef_note}{num_tr} isim, {irab})"
        elif lemma == '>amaAta':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) == (2, 258) and '1S' in f:
                return f"Kendi keyfî gücümle öldürüp yaşam veririm iddiası (`أُمِيتُ`, IV. bab muzâri fiili, {m_pers})"
            return f"Yaşam gücünü çekip ölüm evresini gerçekleştirir/gerçekleştirdi (`يُمِيتُ / أَمَاتَ / نُمِيتُ`, IV. bab {tense} fiili, {m_pers})"
        elif lemma == 'mayotap':
            if pos == 'ADJ':
                return f"Henüz yağmurla buluşmamış ölü ve kurak toprak (`ٱلْمَيْتَةُ`, tekil dişil sıfat, {irab})"
            return f"Kesim ilkesi olmaksızın kendi kendine ölüp sağlığa uygunsuz düşen hayvan leşi (`ٱلْمَيْتَةُ / مَيْتَةً`, tekil dişil {indef_note}isim, {irab})"
        elif lemma == 'm~ayot':
            if pos == 'ADJ':
                if (s, a) == (49, 12):
                    return f"Gıybet benzetmesindeki cansız ve ölmüş kardeş bedeni (`مَيْتًا`, şeddesiz tekil eril {indef_note}sıfat, {irab})"
                return f"Yağmur bekleyen kupkuru ve cansız belde (`مَّيْتًا`, şeddesiz tekil eril {indef_note}sıfat, {irab})"
            return f"Bilinç ve kavrayış işlevi sönmüş halde iken aydınlıkla diriltilen kimse (`مَيْتًا`, şeddesiz tekil eril {indef_note}isim, {irab})"
        elif lemma == 'mamaAt':
            return f"İnsanın yaşamdan sonra girdiği ölüm hali ve sonraki evresi (`مَمَات`, tekil eril mîmî masdar isim, {irab})"
        elif lemma == 'mawotat':
            return f"İnsanın dünyada tattığı tek seferlik ilk ölüm geçişi (`مَوْتَتَنَا / ٱلْمَوْتَةَ`, tekil dişil merre/durum ismi, {irab})"

    elif root_ar == 'ك-ب-ر':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim/sıfat"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        kb_p = [('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MP', '3. çoğul eril'), ('3FP', '3. çoğul dişil')]
        kb_pers = next((v for k, v in kb_p if k in f), 'genel')
        kb_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == '{sotakobara':
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) in ((4, 172), (7, 206), (16, 49), (21, 19), (41, 38)):
                return f"Yaratıcıya yöneliş ve sorumluluktan büyüklük taslayıp kaçınmaz/kaçınmazlar (`يَسْتَكْبِرُ / يَسْتَكْبِرُونَ`, X. bab {tense} fiili, {kb_pers}{kb_mood})"
            return f"Kendini olduğundan üstün sanarak hakikati kabule direnir/direndi (`ٱسْتَكْبَرَ / يَسْتَكْبِرُونَ`, X. bab {tense} fiili, {kb_pers}{kb_mood})"
        elif lemma == 'kabiyr':
            if pos == 'ADJ':
                if (s, a) in ((13, 9), (22, 62), (31, 30), (34, 23), (40, 12)):
                    return f"Güç, bilgi ve egemenlik bakımından sınır tanımaz mutlak Büyük (`ٱلْكَبِيرُ / ٱلْكَبِيرِ`, tekil eril sıfat, {irab})"
                if (s, a) in ((12, 78), (28, 23)):
                    return f"Yaşça çok ilerlemiş ihtiyar kimse (`كَبِيرًا / كَبِيرٌ`, tekil eril {indef_note}sıfat, {irab})"
                if (s, a) in ((2, 219), (4, 2)):
                    return f"Toplumsal ve vicdani dengeleri sarsan büyük, ağır sorumluluk ve yıkım (`كَبِيرٌ / كَبِيرًا`, tekil eril {indef_note}sıfat, {irab})"
                return f"Ölçü, etki, değer veya sonuç bakımından büyük ve kapsamlı olan (`كَبِيرًا / كَبِيرٌ`, tekil eril {indef_note}sıfat, {irab})"
            if (s, a) in ((2, 282), (54, 53)):
                return f"Ölçeği küçük olsun veya büyük olsun kaydedilen her birim/olgu (`كَبِيرًا / كَبِيرٍ`, tekil eril {indef_note}isim, {irab})"
            if (s, a) in ((12, 80), (20, 71), (26, 49), (21, 58), (21, 63)):
                return f"Kardeşlerin yaşça en büyüğü, önde gelen usta yahut heykellerin en irisi (`كَبِيرُهُمْ / لَكَبِيرُكُمُ`, tekil eril isim, {irab})"
            return f"Kapsamlı, önemli ve büyük bağış/lütuf (`كَبِيرًا`, tekil eril {indef_note}isim, {irab})"
        elif lemma == '>akobar':
            if 'MP' in f:
                return f"Topluluk içinde haksız işlerin başını çeken en önde gelen elebaşları (`أَكَٰبِرَ`, kırık çoğul isim, {irab})"
            pos_tr = "sıfat" if pos == 'ADJ' else "isim"
            if (s, a) in ((10, 61), (34, 3)):
                return f"Zerre ağırlığından daha küçük yahut daha büyük hiçbir şey (`أَكْبَرَ`, tekil eril ism-i tafdîl {pos_tr}, {irab})"
            return f"Derece, şiddet, etki veya tanıklık gücü bakımından daha büyük / en büyük (`أَكْبَرُ / أَكْبَرِ / أَكْبَرَ`, tekil eril ism-i tafdîl {pos_tr}, {irab})"
        elif lemma == 'kabura':
            if (s, a) == (4, 6):
                return f"Yetimlerin yaşça büyüyüp olgunluk çağına ulaşmalarına kadar (`يَكْبَرُوا۟`, `فَعِلَ` babı muzâri fiili, {kb_pers}{kb_mood})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"İnsana, kalbe yahut ilkeye göre çok ağır, büyük ve tahammülsüz gelir/geldi (`كَبُرَ / كَبُرَتْ / يَكْبُرُ`, `فَعُلَ` babı {tense} fiili, {kb_pers})"
        elif lemma == 'kabiyrap':
            if 'FP' in f:
                return f"Ölçü ve ahlakı derinden zedeleyen en büyük ve ağır ihlaller (`كَبَآئِرَ`, kırık dişil çoğul isim, {irab})"
            if (s, a) in ((9, 121), (18, 49)):
                return f"Kayıt altına alınan en büyük ölçekli eylem/katkı (`كَبِيرَةً`, tekil dişil {indef_note}isim, {irab})"
            return f"İçsel saygı ve kararlılık taşımayanlara çok ağır ve büyük gelen sorumluluk (`كَبِيرَةٌ / كَبِيرَةً`, tekil dişil {indef_note}isim, {irab})"
        elif lemma == 'mutakab~ir':
            if pos == 'ADJ':
                return f"Her türlü eksiklikten münezzeh olup hakiki ve mutlak büyüklüğün tek sahibi olan (`ٱلْمُتَكَبِّرُ`, V. bab etken ortaç sıfat, {irab})"
            num_tr = "çoğul" if 'MP' in f else "tekil eril"
            return f"Hak etmediği üstünlük iddiasıyla kendini dev aynasında görüp diklenen (`مُتَكَبِّرٍ / ٱلْمُتَكَبِّرِينَ`, V. bab {indef_note}{num_tr} etken ortaç isim, {irab})"
        elif lemma == 'kuboraY`':
            if pos == 'N':
                return f"Sarsıcı en büyük uyarı gerçeklerinden biri (`ٱلْكُبَرِ`, çoğul isim, {irab})"
            return f"En büyük ve kapsamlı kanıt, sarsıntı, yakalayış veya yakıcı azap (`ٱلْكُبْرَىٰ`, müennes ism-i tafdîl sıfat, {irab})"
        elif lemma == 'kibar':
            return f"Beden gücünün azaldığı ileri yaş ve ihtiyarlık evresi (`ٱلْكِبَر`, tekil eril isim, {irab})"
        elif lemma == 'musotakobir':
            num_tr = "çoğul" if 'MP' in f else "tekil eril"
            return f"Kendini gerçeğin üstünde görüp haksızca büyüklük taslayan/taslayanlar (`ٱلْمُسْتَكْبِرُونَ / مُسْتَكْبِرًا`, X. bab {indef_note}{num_tr} etken ortaç isim, {irab})"
        elif lemma == 'kab~iro':
            mood_tr = "emir" if 'IMPV' in f else "muzâri"
            return f"Evrenin Sahibinin eşsiz büyüklüğünü dille ve bilinçle ilan eder/et (`كَبِّرْ / تُكَبِّرُوا۟`, II. bab {mood_tr} fiili, {kb_pers}{kb_mood})"
        elif lemma == 'yatakab~aru':
            return f"Haksız yere ve ölçüsüzce büyüklük taslar/taslarsın (`تَتَكَبَّرَ / يَتَكَبَّرُونَ`, V. bab muzâri fiili, {kb_pers}{kb_mood})"
        elif lemma == "kiboriyaA^'":
            return f"Egemenlik, mutlak otorite ve en yüce büyüklük (`ٱلْكِبْرِيَآءُ`, tekil dişil isim, {irab})"
        elif lemma == 'kibor':
            if (s, a) == (24, 11):
                return f"Yürütülen karalamanın en büyük payı ve baş sorumluluğu (`كِبْرَهُۥ`, tekil eril isim, {irab})"
            return f"Kalplerdeki temelsiz büyüklük kuruntusu ve kibir iddiası (`كِبْرٌ`, belirsiz tekil eril isim, {irab})"
        elif lemma == '{sotikobaAr':
            return f"Yeryüzünde gerçeği küçümseyip haksızca büyüklük taslama tutkusu (`ٱسْتِكْبَارًا`, X. bab belirsiz masdar isim, {irab})"
        elif lemma == '>akobaro':
            return f"Onu görünce gözlerinde olağanüstü yücelttiler ve hayranlığa kapıldılar (`أَكْبَرْنَهُۥ`, IV. bab mâzî fiili, 3. çoğul dişil)"
        elif lemma == 'takobiyr':
            return f"Eksiklikten uzak tutarak tam bir tazim ve ululamayla yüceltme (`تَكْبِيرًۢا`, II. bab belirsiz masdar isim, {irab})"
        elif lemma == "kubaraA^'":
            return f"Peşinden gittiğimiz önde gelen söz sahipleri ve yöneticilerimiz (`كُبَرَآءَنَا`, kırık çoğul isim, {irab})"
        elif lemma == 'kub~aAr':
            return f"Akıl almaz ölçüde devasa ve yıkıcı tuzak (`كُبَّارًا`, `فُعَّال` mübalağa belirsiz sıfatı, {irab})"

    elif root_ar == 'ش-ه-د':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim/sıfat"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        sh_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MP', '3. çoğul eril')]
        sh_pers = next((v for k, v in sh_p if k in f), 'genel')
        sh_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == '$ahiyd':
            pos_tr = "sıfat" if pos == 'ADJ' else "isim"
            if 'MD' in f:
                return f"Adalet ve hukuk belgesi için gereken iki tanık (`شَهِيدَيْنِ`, ikil eril isim, {irab})"
            if 'MP' in f:
                return f"Olayı bizzat gözlemleyen hukuk tanıkları veya hakkı yaşamıyla tescil eden örnek tanıklar (`شُهَدَآء / ٱلشُّهَدَآء`, kırık çoğul {pos_tr}, {irab})"
            if (s, a) == (50, 37):
                return f"Dikkati dağılmadan zihnen ve bilfiil orada hazır bulunan kimse (`شَهِيدٌ`, tekil eril {indef_note}{pos_tr}, {irab})"
            return f"Hiçbir yerden uzak kalmadan doğrudan hazır olup gözetleyen tanık (`شَهِيدٌ / شَهِيدًا`, tekil eril {indef_note}{pos_tr}, {irab})"
        elif lemma == '$ahida':
            if 'IMPV' in f:
                return f"Bu söz ve gerçeğin önünde hazır bulunup tanıklık edin (`ٱشْهَدْ / ٱشْهَدُوا۟`, I. bab emir fiili, {sh_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            if (s, a) == (2, 185):
                return f"O aya sağ salim yetişip içinde hazır bulunursa (`شَهِدَ`, I. bab {tense} fiili, {sh_pers})"
            if (s, a) in ((24, 24), (36, 65), (41, 20), (41, 21), (41, 22)):
                return f"İnsanın kendi işitme, görme, el, ayak ve derilerinin bizzat tanıklık etmesi (`تَشْهَدُ / شَهِدَ`, I. bab {tense} fiili, {sh_pers}{sh_mood})"
            return f"Yerinde hazır bulunup bildiği gerçeğe kesin beyanla tanıklık eder/etti (`شَهِدَ / يَشْهَدُ`, I. bab {tense} fiili, {sh_pers}{sh_mood})"
        elif lemma == '$aha`dap':
            if (s, a) in ((6, 73), (9, 94), (9, 105), (13, 9), (23, 92), (32, 6), (39, 46), (59, 22), (62, 8), (64, 18)):
                return f"Saklı olanın (`ٱلْغَيْب`) karşısında duyulara, akla ve gözleme açık görünen âlem (`ٱلشَّهَٰدَةِ`, tekil dişil masdar isim, {irab})"
            return f"Görüp kesinleştirdiği gerçeği hukuk veya adalet önünde eksiksiz bildirme beyanı (`شَهَٰدَة / ٱلشَّهَٰدَة`, tekil dişil {indef_note}isim, {irab})"
        elif lemma == '$aAhid':
            pos_tr = "sıfat" if pos == 'ADJ' else "isim"
            if 'MP' in f:
                return f"Olay yerinde hazır duran yahut hakikate katılan görgü tanıkları (`ٱلشَّٰهِدِينَ / شُهُودًا / أَشْهَٰدُ`, çoğul {indef_note}{pos_tr}, {irab})"
            return f"Olayı bizzat görüp aktaran hazır gözlemci ve tanık (`شَاهِد / شَٰهِدًا`, tekil eril {indef_note}{pos_tr}, {irab})"
        elif lemma == '>a$ohada':
            if 'IMPV' in f:
                return f"İşlemlerinizde güvenilir şahitleri hazır bulundurup tanık tutun (`أَشْهِدُوٓا۟`, IV. bab emir fiili, {sh_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Bir başkasını veya kendi özünü gerçeğin tanığı yapıp onaylatır/onaylattı (`أَشْهَدَ / يُشْهِدُ / أُشْهِدُ`, IV. bab {tense} fiili, {sh_pers})"
        elif lemma == 'ma$ohuwd':
            if (s, a) == (17, 78):
                return f"Sabah fecri okunuşunun yüksek görevli tanıklarca bizzat hazır bulunulup izlenişi (`مَشْهُودًا`, I. bab edilgen ortaç isim, {irab})"
            return f"Bütün varlıkların toplanıp yerinde hazır bulunarak tanık olduğu gün/sahne (`مَّشْهُودٌ / مَشْهُودٍ`, I. bab edilgen ortaç isim, {irab})"
        elif lemma == '$aha`da`t':
            return f"Karşılıklı verilen birden fazla hukukî tanıklık beyanları (`شَهَٰدَٰت`, dişil çoğul {indef_note}isim, {irab})"
        elif lemma == '{sota$ohidu':
            return f"Hukukî belirlilik için yanınızdan güvenilir tanıklar çağırıp belirleyin (`وَٱسْتَشْهِدُوا۟ / فَٱسْتَشْهِدُوا۟`, X. bab emir fiili, 2. çoğul eril)"
        elif lemma == 'm~a$ohad':
            return f"Tüm insanların aynı anda toplanıp hazır bulunacağı büyük buluşma sahnesi (`مَشْهَدِ`, tekil eril mekân/zaman ismi, {irab})"

    elif root_ar == 'ن-ب-أ':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        nb_p = [('1S', '1. tekil'), ('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('3MS', '3. tekil eril'), ('3FS', '3. tekil dişil'), ('3MP', '3. çoğul eril')]
        nb_pers = next((v for k, v in nb_p if k in f), 'genel')
        nb_mood = ", meczûm" if 'JUS' in f else ""
        if lemma == 'n~abiY~':
            if 'MP' in f:
                return f"İlâhî kaynaktan büyük hakikat haberini alıp insanlığa ulaştıran haber elçileri (`ٱلنَّبِيِّـۧنَ / ٱلْأَنۢبِيَآءَ / ٱلنَّبِيُّونَ`, çoğul isim, {irab})"
            if (s, a) == (33, 40):
                return f"Haber elçileri zincirini mühürleyip tamamlayan elçi (ilgili bağlam; `ٱلنَّبِىّ` tekil eril {indef_note}isim, {irab})"
            return f"Yaratıcıdan büyük haberi ve vahyi alarak insanlara bildiren seçkin elçi (`ٱلنَّبِىُّ / نَبِيًّا / نَبِىٍّ`, tekil eril {indef_note}isim, {irab})"
        elif lemma == 'nab~a>a':
            if 'PASS' in f:
                return f"Önceki kitaplarda geçenler yahut yapıp ettiklerinin tamamı kendisine eksiksiz haber verilir (`يُنَبَّأْ / لَتُنَبَّؤُنَّ / يُنَبَّؤُا۟`, II. bab edilgen muzâri fiili, {nb_pers}{nb_mood})"
            if 'IMPV' in f:
                return f"Gerçeği açık delille bildirin / müjde ve uyarıyı haber ver (`نَبِّئْ / نَبِّـُٔونِى`, II. bab emir fiili, {nb_pers})"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Kapsamlı, kesin ve derin bilgiye dayanarak her ayrıntıyı haber verir/verdi (`نَبَّأَ / يُنَبِّئُ / أُنَبِّئُكُم`, II. bab {tense} fiili, {nb_pers})"
        elif lemma == 'naba>':
            if 'MP' in f:
                return f"Gözleme kapalı geçmiş veya gelecek gerçeklerine dair ibretlik büyük haberler (`أَنۢبَآءِ / أَنۢبَٰٓؤُا۟`, kırık çoğul isim, {irab})"
            return f"Sonucu herkesi ilgilendiren ciddi, önemli ve sarsıcı haber (`نَبَأ / ٱلنَّبَإِ`, tekil eril {indef_note}isim, {irab})"
        elif lemma == 'n~ubuw~ap':
            return f"İlâhî kaynaktan haber alıp kitap ve hikmetle insanlara yol gösterme görevi (`ٱلنُّبُوَّةَ`, tekil dişil isim, {irab})"
        elif lemma == '>an[ba>a':
            if 'IMPV' in f:
                return f"Bildiğiniz varlık adlarını ve işlevlerini aktarıp haber verin (`أَنۢبِـُٔونِى / أَنۢبِئْهُم`, IV. bab emir fiili, {nb_pers})"
            return f"Gizli veya açık bir bilgiyi muhataba aktarıp bildirdi (`أَنۢبَأَ / أَنۢبَأَكَ`, IV. bab mâzî fiili, {nb_pers})"
        elif lemma == 'yasotan[bi_#u':
            return f"Verilen büyük haberin gerçekten hak olup olmadığını senden sorup öğrenmek isterler (`وَيَسْتَنۢبِـُٔونَكَ`, X. bab muzâri fiili, 3. çoğul eril)"

    elif root_ar == 'ب-ع-ض':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        if lemma == 'baEuwDap':
            return f"Bölünmüş en küçük canlı birim misali incecik tek bir sivrisinek (`بَعُوضَةً`, tekil dişil belirsiz isim, {irab})"
        elif lemma == 'baEoD':
            if (s, a) in ((2, 85), (4, 150)):
                return f"Yekpare bütünden işine geldiği gibi koparılıp seçilen bir parça/kısım (`بَعْضِ / بَعْضٍ`, tekil eril {indef_note}isim, {irab})"
            if (s, a) in ((2, 36), (7, 24), (20, 123), (43, 67), (49, 12)):
                return f"Aynı insanlık bütününün içinde birbirine karşıt düşen veya zedelenen bir kesim/diğeri (`بَعْضُكُمْ / بَعْضٍ / بَعْضًا`, tekil eril {indef_note}isim, {irab})"
            if (s, a) in ((3, 195), (4, 25), (9, 67), (9, 71)):
                return f"Aynı kök ve değer yapısından gelen birbirinin tamamlayıcı parçaları (`بَعْضُكُم / بَعْضُهُمْ`, tekil eril {indef_note}isim, {irab})"
            if (s, a) in ((2, 259), (18, 19), (23, 113)):
                return f"Zaman bütününün yalnızca kısmi bir dilimi/saatleri (`بَعْضَ`, tekil eril isim, {irab})"
            if (s, a) == (24, 40):
                return f"Katman katman birbirinin üstüne binmiş kısımlar (`بَعْضُهَا / بَعْضٍ`, tekil eril {indef_note}isim, {irab})"
            if (s, a) in ((2, 253), (6, 165), (16, 71), (17, 21), (17, 55), (43, 32)):
                return f"Görev, imkân veya derece bakımından birbirinden farklılaştırılan kesimler (`بَعْضَهُمْ / بَعْضٍ`, tekil eril {indef_note}isim, {irab})"
            return f"Bir bütünün, topluluğun yahut konunun ayrılmış bir parçası / karşılıklı bir tarafı (`بَعْض`, tekil eril {indef_note}isim, {irab})"

    elif root_ar == 'ن-ص-ر':
        irab = "merfû" if 'NOM' in f else ("mansûb" if 'ACC' in f else ("mecrûr" if 'GEN' in f else "isim/sıfat"))
        indef_note = "belirsiz/nekre " if 'INDEF' in f else ""
        ns_p = [('1P', '1. çoğul'), ('2MS', '2. tekil eril'), ('2MP', '2. çoğul eril'), ('2D', '2. ikil'), ('3MS', '3. tekil eril'), ('3MP', '3. çoğul eril')]
        ns_pers = next((v for k, v in ns_p if k in f), 'genel')
        ns_mood = ", meczûm" if 'JUS' in f else (", mansûb" if 'SUBJ' in f else "")
        if lemma == 'naSara':
            if 'PASS' in f:
                return f"Zor ve hesap anında kendilerine dışarıdan hiçbir destek ulaştırılmaz (`يُنصَرُونَ / تُنصَرُونَ`, I. bab edilgen muzâri fiili, {ns_pers})"
            if 'IMPV' in f:
                if (s, a) == (21, 68):
                    return f"Sahte güç ve otoritelerinize koşup arka çıkın (`وَٱنصُرُوٓا۟`, I. bab emir fiili, 2. çoğul eril)"
                return f"Bize veya bana hak yolunda aktif destek verip üstün kıl (`ٱنصُرْ`, I. bab emir fiili, 2. tekil eril)"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Zorda kalana güç, koruma ve başarı ulaştırarak destekler/destekledi (`نَصَرَ / يَنصُرُ`, I. bab {tense} fiili, {ns_pers}{ns_mood})"
        elif lemma == 'naSiyr':
            if pos == 'ADJ':
                return f"Haklı duruşu sahada koruyup güçlendiren destekleyici bir yetki (`نَّصِيرًا`, tekil eril {indef_note}sıfat, {irab})"
            if 'MP' in f:
                if (s, a) in ((3, 52), (61, 14)):
                    return f"İsa elçinin çağrısına uyup hakikat davasına omuz veren destekçiler (`أَنصَار`, kırık çoğul isim, {irab})"
                if (s, a) in ((9, 100), (9, 117)):
                    return f"Zor şartlarda göç edenlere kucak açıp destek olan Medineli yardımcılar (`ٱلْأَنصَارِ`, kırık çoğul isim, {irab})"
                return f"Haksızları ve yanlış yoldakileri kurtarıp koruyacak destekçiler (`أَنصَار`, kırık çoğul {indef_note}isim, {irab})"
            return f"Kriz ve tehlike anında imdada yetişen güçlü destekçi (`نَصِير`, tekil eril {indef_note}isim, {irab})"
        elif lemma == 'naSor':
            return f"Düşeni ayağa kaldırıp üstün kılan aktif yardım, koruma ve zafer (`نَصْر / ٱلنَّصْرُ`, tekil eril {indef_note}masdar isim, {irab})"
        elif lemma == 'naSoraAniy~':
            num_tr = "çoğul" if 'P' in f else f"tekil {indef_note}"
            return f"İsa elçinin yolunu sürdürdüğünü belirten tarihsel topluluk mensubu/mensupları (`ٱلنَّصَٰرَىٰ / نَصْرَانِيًّا`, {num_tr}özel topluluk ismi, {irab})"
        elif lemma == 'naASir':
            num_tr = "çoğul" if 'MP' in f else f"tekil eril {indef_note}"
            return f"Yardıma koşup kişiyi tehlikeden koruyan destekçi/yardımcılar (`نَاصِر / ٱلنَّٰصِرِينَ`, I. bab {num_tr}etken ortaç isim, {irab})"
        elif lemma == '{ntaSara':
            if 'IMPV' in f:
                return f"Zorbalık karşısında yenik düştüm, müdahale edip hakkımı kurtar (`فَٱنتَصِرْ`, VIII. bab emir fiili, 2. tekil eril)"
            tense = "mâzî" if 'PERF' in f else "muzâri"
            return f"Uğradığı saldırı ve haksızlıktan sonra kendini savunup hakkını alır/aldı (`ٱنتَصَرَ / يَنتَصِرُونَ / تَنتَصِرَانِ`, VIII. bab {tense} fiili, {ns_pers})"
        elif lemma == 'm~untaSir':
            num_tr = "çoğul" if 'MP' in f else f"tekil eril {indef_note}"
            return f"Kendi öz gücüne güvenip saldırıyı savuşturarak kurtulabilen (`مُنتَصِر / مُنتَصِرِينَ`, VIII. bab {num_tr}etken ortaç isim, {irab})"
        elif lemma == '{sotanSara':
            return f"Sıkıntı ve tehdit altında dışarıdan acil yardım ve destek talep etti/ettiler (`ٱسْتَنصَرَ / ٱسْتَنصَرُوكُمْ`, X. bab mâzî fiili, {ns_pers})"
        elif lemma == 'manSuwr':
            num_tr = "çoğul" if 'MP' in f else f"tekil eril {indef_note}"
            return f"Hakkı korunduğu için ilâhî destekle güçlendirilip zafere erdirilen (`مَنصُورًا / ٱلْمَنصُورُونَ`, I. bab {num_tr}edilgen ortaç isim, {irab})"
        elif lemma == 'tanaASaru':
            return f"Neden şimdi birbirinize arka çıkıp karşılıklı destekleşmiyorsunuz (`تَنَاصَرُونَ`, VI. bab muzâri fiili, 2. çoğul eril)"

    elif root_ar == 'ص-د-ق':
        if lemma == 'SaAdiq':
            if 'MP|ACC' in f:
                if (s, a) in ((3, 17), (33, 8), (33, 24), (33, 35)):
                    return "Sözü eylemiyle sağlam ve tutarlı kimseleri / kimselerle (ismi fâil, eril çoğul mansûb)"
                elif (s, a) == (5, 119):
                    return "Sözünde ve özünde sağlam duranlara (ismi fâil, eril çoğul mansûb mef'ûl)"
                return "İddianızda gerçekten sağlam ve tutarlı kimselerseniz (ismi fâil, eril çoğul mansûb kâne haberi)"
            elif 'MP|GEN' in f:
                if (s, a) == (9, 119):
                    return "Sözü özüne uyan sağlam kimselerin yanında (ismi fâil, eril çoğul mecrûr)"
                return "Gerçeği söyleyen sağlam kimselerden (ismi fâil, eril çoğul mecrûr)"
            elif 'MP|NOM' in f:
                if (s, a) in ((49, 15), (59, 8)):
                    return "İşte sözünü eylemiyle doğrulayan gerçek ve sağlam kimseler (ismi fâil, eril çoğul merfû')"
                return "Şüphesiz biz sözümüzde ve haberimizde gerçeği söyleyenleriz (ismi fâil, eril çoğul merfû')"
            elif 'M|ACC' in f and (s, a) == (19, 54):
                return "Verdiği sözü eksiksiz yerine getiren (`صَادِقَ ٱلْوَعْدِ`, ismi fâil muzâf mansûb)"
            elif 'M|INDEF|ACC' in f:
                return "Eğer doğru ve tutarlı bir kimse ise (`صَادِقًا`, tekil eril nekra mansûb)"
            return "Söz ve vaat mutlaka gerçeğe çıkacak olandır (`لَصَادِقٌ`, tekil eril nekra merfû')"
        elif lemma == 'S~a`diqa`t':
            return "Sözünü ve özünü sağlam tutan dürüst kadınları (ismi fâil, dişil çoğul mansûb)"
        elif lemma == 'muSad~iq':
            if pos == 'ADJ':
                if 'M|NOM' in f and 'INDEF' not in f:
                    return "Kendinden önceki mesajları doğrulayıcı niteliği taşıyan (`مُّصَدِّقُ ٱلَّذِى بَيْنَ يَدَيْهِ`, II. bab ismi fâil sıfat/muzâf merfû')"
                return "Kendinden önceki mesajla uyuşup onu doğrulayıcı olarak gelen (`مُصَدِّقٌ`, II. bab ismi fâil sıfat, tekil eril merfû')"
            elif 'MP|GEN' in f:
                return "Ölümden sonraki dirilişi onaylayıp doğrulayan kimselerden (`ٱلْمُصَدِّقِينَ`, II. bab ismi fâil çoğul mecrûr)"
            elif 'M|INDEF|NOM' in f:
                return "Öncekilerle uyuşup onları doğrulayan (`مُّصَدِّقٌ`, II. bab ismi fâil tekil merfû')"
            return "Kendinden öncekileri / sözü doğrulayıp geçerli kılıcı hâlde (`مُصَدِّقًا`, II. bab ismi fâil tekil mansûb hâl)"
        elif lemma == 'Sadaqa':
            if '3MS' in f:
                if (s, a) in ((3, 152), (33, 22), (39, 74), (48, 27)):
                    return "Verdiği sözü / müjdeyi / rüyayı fiilen gerçekleştirdi (`صَدَقَ`, I. bab mâzî fiili, 3. tekil eril)"
                return "En sağlam ve eksiksiz gerçeği söyledi / hükmetti (`صَدَقَ`, I. bab mâzî fiili, 3. tekil eril)"
            elif '3MP' in f:
                return "Sözlerini ve ahitlerini eylemle sağlamca yerine getirdiler (`صَدَقُوا۟`, I. bab mâzî fiili, 3. çoğul eril)"
            elif '2MS' in f:
                if (s, a) == (27, 27):
                    return "Acaba gerçeği mi söyledin (`أَصَدَقْتَ`, I. bab mâzî fiili, 2. tekil eril)"
                return "Senin bize söylediğinin gerçekten doğru olduğunu bilelim (`صَدَقْتَنَا`, I. bab mâzî fiili, 2. tekil eril)"
            elif '3FS' in f:
                return "Kadın doğru söylemiştir (`فَصَدَقَتْ`, I. bab mâzî fiili, 3. tekil dişil)"
            return "Sözümüzü ve vaadimizi onlara fiilen gerçekleştirdik (`صَدَقْنَٰهُمُ`, I. bab mâzî fiili, 1. çoğul)"
        elif lemma == 'Sidoq':
            if 'NOM' in f:
                return "Kendi doğrulukları ve iç tutarlılıkları (`صِدْقُهُمْ`, masdar/isim merfû')"
            elif 'INDEF|ACC' in f:
                return "Doğruluk, sapmasızlık ve tam tutarlılık bakımından (`صِدْقًا`, nekra mansûb temyiz)"
            elif 'INDEF|GEN' in f:
                return "Sağlamlık, doğruluk ve kalıcı onur niteliğinde (`صِدْقٍ`, nekra muzâfun ileyh mecrûr)"
            return "Sapmasız doğruluk / ahde bağlılıkları sebebiyle (`بِٱلصِّدْقِ / صِدْقِهِمْ`, marife/muzâf mecrûr)"
        elif lemma == 'Sad~aqa':
            if 'PERF' in f:
                if '2MS' in f:
                    return "Gördüğün rüyayı eyleminle doğrulayıp gerçekleştirdin (`صَدَّقْتَ`, II. bab mâzî fiili, 2. tekil eril)"
                elif '3FS' in f:
                    return "Rabbinin sözlerini ve yazılarını bütünüyle doğrulayıp benimsedi (`وَصَدَّقَتْ`, II. bab mâzî fiili, 3. tekil dişil)"
                elif (s, a) == (34, 20):
                    return "Üzerlerindeki zannını fiilen haklı ve geçerli çıkardı (`صَدَّقَ`, II. bab mâzî fiili, 3. tekil eril)"
                return "Gerçeği ve güzeli kalben ve fiilen onaylayıp doğruladı (`صَدَّقَ`, II. bab mâzî fiili, 3. tekil eril)"
            elif '3MS' in f:
                return "Benim sözümü destekleyip doğrulayacak (`يُصَدِّقُنِىٓ`, II. bab muzâri fiili, 3. tekil eril)"
            elif '2MP' in f:
                return "Neden yaratılış gerçeğini onaylayıp doğrulamıyorsunuz (`تُصَدِّقُونَ`, II. bab muzâri fiili, 2. çoğul eril)"
            return "Karşılık ve hesap gününü içtenlikle doğrulayanlar (`يُصَدِّقُونَ`, II. bab muzâri fiili, 3. çoğul eril)"
        elif lemma == 'Sadaqa`t':
            if 'NOM' in f:
                return "Gönüllü ve toplumsal dayanışma payları (`ٱلصَّدَقَٰتُ`, çoğul isim merfû')"
            elif 'GEN' in f:
                return "Yardımlaşma ve dayanışma bağışları konusunda (`ٱلصَّدَقَٰتِ`, çoğul isim mecrûr)"
            elif 'INDEF|ACC' in f:
                return "Önceden vereceğiniz gönüllü bağışlar (`صَدَقَٰتٍ`, çoğul nekra mansûb)"
            return "Gönüllü paylaşımlarınızı / dayanışma bağışlarını (`صَدَقَٰتِكُم / ٱلصَّدَقَٰتِ`, çoğul isim mansûb)"
        elif lemma == 'taSad~aqa':
            if 'IMPV' in f:
                return "Bize fazladan gönüllü bağışta bulunup lütfet (`وَتَصَدَّقْ`, V. bab emir fiili, 2. tekil eril)"
            elif 'PERF' in f:
                return "Kim kısas hakkından karşılıksız vazgeçip bağışlarsa (`تَصَدَّقَ`, V. bab mâzî fiili, 3. tekil eril)"
            elif '2MP' in f:
                return "Alacağınızdan vazgeçip bağışlamanız (`أَن تَصَدَّقُوا۟`, V. bab muzâri mansûb fiili, 2. çoğul eril)"
            elif '3MP' in f:
                return "Öldürülenin yakınlarının diyet hakkından bağışlayarak vazgeçmeleri dışında (`يَصَّدَّقُوا۟`, V. bab idğamlı muzâri mansûb fiili, 3. çoğul eril)"
            elif '1P' in f:
                return "Andolsun ki kesinlikle bolca bağış ve paylaşımda bulunuruz (`لَنَصَّدَّقَنَّ`, V. bab idğamlı tekitli muzâri fiili, 1. çoğul)"
            return "Böylece ben de hemen gönülden paylaşımda bulunayım (`فَأَصَّدَّقَ`, V. bab idğamlı muzâri mansûb fiili, 1. tekil)"
        elif lemma == 'Sadaqap':
            if 'ACC' in f:
                return "Gönülden bir bağış / arındırıcı paylaşım (`صَدَقَةً`, tekil nekra mansûb)"
            return "İhtiyaçlıya yapılan bir gönül paylaşımı / bağış (`صَدَقَةٍ`, tekil nekra mecrûr)"
        elif lemma == 'Sid~iyq':
            if 'MP|NOM' in f:
                return "Sözünü eylemiyle hiç çatlak bırakmadan doğrulayan yüksek şahsiyetler (`ٱلصِّدِّيقُونَ`, mübalağa kalıbı çoğul merfû')"
            elif 'MP|GEN' in f:
                return "Sözü eylemiyle birebir bütünleşen özü sağlam kimselerle (`وَٱلصِّدِّيقِينَ`, mübalağa kalıbı çoğul mecrûr)"
            elif 'M|NOM' in f:
                return "Ey özü sözü şaşmaz biçimde sağlam Yusuf! (`ٱلصِّدِّيقُ`, mübalağa kalıbı tekil merfû' nida)"
            return "Sözünde ve doğrulamasında son derece sağlam ve köklü (`صِدِّيقًا`, mübalağa kalıbı tekil nekra mansûb)"
        elif lemma == '>aSodaq':
            return "Sözü ve hükmü Allah'tan daha sağlam ve daha doğru olan (`أَصْدَقُ`, ism-i tafdîl tekil merfû')"
        elif lemma == 'taSodiyq':
            return "Kendinden önceki vahiylerle uyuşup onları doğrulayan (`تَصْدِيقَ`, II. bab masdar mansûb)"
        elif lemma == 'mutaSad~iqiyn':
            return "Gönülden bağış ve paylaşımda bulunan erkekleri / kimseleri (`ٱلْمُتَصَدِّقِينَ`, V. bab ismi fâil çoğul mansûb)"
        elif lemma == 'mutaSad~iqa`t':
            return "Gönülden bağış ve paylaşımda bulunan kadınları (`وَٱلْمُتَصَدِّقَٰتِ`, V. bab ismi fâil dişil çoğul mansûb)"
        elif lemma == 'muS~ad~iqiyn':
            return "İçtenlikle bağışta bulunup malından paylaşan erkekler (`ٱلْمُصَّدِّقِينَ`, V. bab idğamlı ismi fâil çoğul mansûb)"
        elif lemma == 'muS~ad~iqa`t':
            return "İçtenlikle bağışta bulunup malından paylaşan kadınlar (`وَٱلْمُصَّدِّقَٰتِ`, V. bab idğamlı ismi fâil dişil çoğul mansûb)"
        elif lemma == 'Sadiyq':
            if 'INDEF' in f:
                return "İçi dışı bir gerçek ve sıcak bir dost (`صَدِيقٍ`, sıfat-ı müşebbehe tekil mecrûr)"
            return "Güvendiğiniz samimi dostunuzun evinde (`صَدِيقِكُمْ`, isim muzâf mecrûr)"
        elif lemma == 'Saduqa`t':
            return "Kadınların evlilik güvencesi olan haklarını / mehirlerini (`صَدُقَٰتِهِنَّ`, çoğul isim muzâf mansûb)"
        elif lemma == 'Sid~iyqap':
            return "Sözü, tutumu ve teslimiyetiyle bütünüyle özü sağlam bir kadın (`صِدِّيقَةٌ`, dişil mübalağa kalıbı merfû')"

    elif root_ar == 'غ-ي-ر':
        if lemma == 'yugay~iru':
            if (s, a) == (4, 119):
                return "Kesinlikle fıtrî yaratılış düzenini bozup başkalaştıracaklar (`فَلَيُغَيِّرُنَّ`, II. bab tekitli muzâri fiili, 3. çoğul eril)"
            elif '3MS' in f:
                return "Bir topluluğun hâlini ve nizamını dönüştürmez (`يُغَيِّرُ`, II. bab muzâri fiili, 3. tekil eril)"
            return "Kendi iç dünyalarında ve tutumlarında olanı dönüştürmedikçe (`يُغَيِّرُوا۟`, II. bab mansûb muzâri fiili, 3. çoğul eril)"
        elif lemma == 'mugay~ir':
            return "Verdiği nimeti durup dururken bozup geri alan / değiştiren (`مُغَيِّرًا`, II. bab ismi fâil tekil nekra mansûb)"
        elif lemma == 'yatagay~aro':
            return "Tadı ve tazeliği hiç bozulup başkalaşmamış (`لَمْ يَتَغَيَّرْ`, V. bab meczûm muzâri fiili, 3. tekil eril)"
        elif lemma == 'mugiyra`t':
            return "Sabah vakti hızla baskın yapıp ortamı altüst edenlere (`فَٱلْمُغِيرَٰتِ`, IV. bab ismi fâil dişil çoğul mecrûr)"
        elif lemma == 'gayor':
            if pos == 'ADJ':
                if 'GEN' in f:
                    return "Ekini ve bitkisi bulunmayan / ondan yoksun (`غَيْرِ`, sıfat konumunda mübhem isim mecrûr)"
                return "Engel veya kesinti sınırının dışında kalan (`غَيْرُ`, sıfat konumunda mübhem isim merfû')"
            if 'NOM' in f:
                if (s, a) in ((26, 29), (28, 38)):
                    return "Benim dışımda / benden büsbütün başka (`غَيْرِى`, mütekellim yâsına muzâf takdîren merfû' sıfat)"
                elif (s, a) in ((6, 46), (7, 59), (7, 65), (7, 73), (7, 85), (11, 50), (11, 61), (11, 84), (23, 23), (23, 32), (28, 71), (28, 72), (35, 3), (52, 43)):
                    return "O'nun / Allah'ın sınırının dışında hiçbir başka merci (`غَيْرُهُۥ / غَيْرُ ٱللَّهِ`, sıfat/bedel mübhem isim merfû')"
                elif (s, a) in ((41, 8), (95, 6)):
                    return "Kesintiye uğramayan ve başa kakılmayan (`غَيْرُ مَمْنُونٍ`, olumsuz niteleyici sıfat merfû')"
                elif (s, a) in ((23, 6), (70, 30)):
                    return "Hiçbir biçimde kınanmayan / sınır içinde korunan (`غَيْرُ مَلُومِينَ`, cümle haberi mübhem isim merfû')"
                return "Nitelenen özelliğin tamamen dışında / aksine olan (`غَيْرُ`, haber veya sıfat mübhem isim merfû')"
            elif 'GEN' in f:
                if (s, a) in ((2, 61), (3, 21), (3, 112), (3, 181), (4, 155), (7, 33), (7, 146), (10, 23), (22, 40), (28, 39), (40, 75), (41, 15), (42, 42), (46, 20)):
                    return "Hak ve meşruiyet sınırının dışına taşarak / haksız yere (`بِغَيْرِ ٱلْحَقِّ / حَقٍّ`, câr ve mecrûr mübhem isim)"
                elif (s, a) in ((2, 212), (3, 27), (3, 37), (24, 38), (38, 39), (39, 10), (40, 40)):
                    return "Sayı ve ölçü sınırının ötesinde hesapsızca (`بِغَيْرِ حِسَابٍ`, câr ve mecrûr mübhem isim)"
                elif (s, a) in ((6, 100), (6, 108), (6, 119), (6, 140), (6, 144), (16, 25), (22, 3), (22, 8), (28, 50), (30, 29), (31, 6), (31, 20), (40, 35), (40, 56), (48, 25)):
                    return "Bilgi, hidayet veya yetkili kanıt olmaksızın (`بِغَيْرِ عِلْمٍ / هُدًى / سُلْطَٰنٍ`, câr ve mecrûr mübhem isim)"
                elif (s, a) in ((13, 2), (31, 10)):
                    return "Sizin görebildiğiniz fiziki direkler olmaksızın (`بِغَيْرِ عَمَدٍ`, câr ve mecrûr mübhem isim)"
                elif (s, a) in ((2, 173), (5, 3), (6, 145), (16, 115)):
                    return "Allah'ın dışındaki bir odak adına (`لِغَيْرِ ٱللَّهِ`, lâm harf-i cerriyle mecrûr mübhem isim)"
                elif (s, a) in ((20, 22), (27, 12), (28, 32)):
                    return "Hiçbir hastalık ve kusur olmaksızın (`مِنْ غَيْرِ سُوٓءٍ`, câr ve mecrûr mübhem isim)"
                elif (s, a) in ((4, 82), (4, 140), (6, 68), (10, 15)):
                    return "Onun / Allah'ın dışında bambaşka bir söz veya kaynaktan (`غَيْرِ / غَيْرِهِۦ`, muzâfun ileyh mecrûr)"
                return "Belirtilen sınırın, niteliğin veya grubun tamamen dışında (`غَيْرِ`, mecrûr mübhem isim)"
            else:
                if (s, a) in ((3, 83), (6, 14), (6, 40), (6, 114), (6, 164), (7, 140), (16, 52), (39, 64)):
                    return "Yoksa Allah'tan büsbütün başka birini mi (`أَغَيْرَ / أَفَغَيْرَ ٱللَّهِ`, öne geçmiş mef'ûl mansûb)"
                elif (s, a) in ((2, 173), (5, 3), (6, 145), (16, 115)):
                    return "Taşkınlık etmeyen ve haddi aşmayan bir hâlde (`غَيْرَ بَاغٍ وَلَا عَادٍ`, mansûb hâl)"
                elif (s, a) in ((9, 39), (11, 57), (47, 38)):
                    return "Sizin yerinize sizden bambaşka bir topluluğu (`قَوْمًا غَيْرَكُمْ`, sıfat/muzâf mansûb)"
                elif (s, a) in ((2, 59), (4, 56), (4, 81), (7, 162), (14, 48), (17, 73), (35, 37)):
                    return "Mevcut olandan büsbütün farklı başka birini (`غَيْرَ / غَيْرَهُۥ`, mef'ûl veya mef'ûlün sânî mansûb)"
                elif (s, a) in ((11, 108), (11, 109), (68, 3)):
                    return "Kesintisiz, eksiksiz ve başa kakılmayan (`غَيْرَ مَجْذُوذٍ / مَنقُوصٍ / مَمْنُونٍ`, sıfat/hâl mansûb)"
                elif (s, a) == (39, 28):
                    return "İçinde hiçbir eğrilik ve çarpıklık barındırmayan (`غَيْرَ ذِى عِوَجٍ`, hâl mansûb)"
                return "Söz konusu durumun dışında / aksi bir hâlde (`غَيْرَ`, hâl, sıfat veya mef'ûl mansûb)"

    elif root_ar == 'و-ع-د':
        if lemma == 'waEada':
            if 'PASS' in f:
                if 'PERF' in f:
                    if '1P' in f:
                        return "Biz ve atalarımız bununla uyarıldık / bize bu bildirildi (`وُعِدْنَا`, I. bab meçhul mâzî fiili, 1. çoğul)"
                    return "Sorumluluk bilinciyle korunanlara önceden söz verilen (`وُعِدَ`, I. bab meçhul mâzî fiili, 3. tekil eril)"
                if '2MP' in f:
                    return "Size açıkça söz verilen / uyarıldığınız (`تُوعَدُونَ`, I. bab meçhul muzâri fiili, 2. çoğul eril)"
                return "Kendilerine açıkça söz verilen / uyarıldıkları (`يُوعَدُونَ`, I. bab meçhul muzâri fiili, 3. çoğul eril)"
            if 'IMPV' in f:
                return "Onlara boş vaatlerde bulun / beklenti kur (`وَعِدْهُمْ`, I. bab emir fiili, muhatap tekil)"
            if 'PERF' in f:
                if '1S' in f:
                    return "Ben de size söz verdim [sonra caydım] (`وَوَعَدتُّكُمْ`, I. bab malûm mâzî fiili, 1. tekil)"
                elif '1P' in f:
                    return "Kendisine veya kendilerine söz verdiğimiz (`وَعَدْنَا`, I. bab malûm mâzî fiili, 1. çoğul)"
                elif '2MS' in f:
                    return "Elçilerin üzerinden kesin söz verdiğin (`وَعَدتَّ`, I. bab malûm mâzî fiili, 2. tekil eril)"
                elif '3MP' in f:
                    return "O'na verdikleri söz (`وَعَدُوهُ`, I. bab malûm mâzî fiili, 3. çoğul eril)"
                if (s, a) in ((9, 68), (22, 72)):
                    return "Yaptırım olarak yakıcı yıkım yurdunu kesin bildirdi (`وَعَدَ`, I. bab malûm mâzî fiili, 3. tekil eril)"
                return "Geleceğe bağlayıcı kesin söz ve hedef bildirdi (`وَعَدَ`, I. bab malûm mâzî fiili, 3. tekil eril)"
            if 'IMPF' in f:
                if '1P' in f:
                    return "Kendilerine bildirdiğimiz yaptırım veya sonuç (`نَعِدُهُمْ`, I. bab malûm muzâri fiili, 1. çoğul)"
                elif '2MS' in f:
                    return "Bizi uyarıp bildirdiğin sonuç (`تَعِدُنَآ`, I. bab malûm muzâri fiili, 2. tekil eril)"
                elif (s, a) == (46, 17):
                    return "İkiniz bana topraktan çıkarılacağımı mı bildiriyorsunuz (`أَتَعِدَانِنِىٓ`, istifhamlı muzâri fiili; korpus etiketi `3FD`, bağlamda `2MD`)"
                elif 'JUS' in f:
                    return "Size güzel bir söz ve hedef vermedi mi (`يَعِدْكُمْ`, I. bab meczûm muzâri fiili, 3. tekil eril)"
                return "Geleceğe dönük beklenti, sonuç veya uyarı bildirir (`يَعِدُ`, I. bab malûm muzâri fiili, 3. tekil eril)"
        elif lemma == 'wa`Eado':
            if 'IMPF' in f:
                return "Onlarla gizlice karşılıklı buluşma ve evlilik sözü bağlamayın (`تُوَاعِدُوهُنَّ`, III. bab nehyedilmiş meczûm muzâri fiili, 2. çoğul eril)"
            return "Karşılıklı buluşma vakti ve yeri tayin ettik (`وَٰعَدْنَا / وَوَٰعَدْنَٰكُمْ`, III. bab mâzî fiili, 1. çoğul)"
        elif lemma == 'tuwEidu':
            return "Yolları kesip gözdağı vererek tehdit savuruyorsunuz (`تُوعِدُونَ`, IV. bab malûm muzâri fiili, 2. çoğul eril)"
        elif lemma == 'tawaAEad':
            return "Karşılıklı buluşma zamanı kararlaştırmaya kalksaydınız (`تَوَاعَدتُّمْ`, VI. bab mâzî fiili, 2. çoğul eril)"
        elif lemma == 'waEod':
            if 'NOM' in f:
                return "Kesinleşmiş söz / gerçekleşecek sonuç bildirimi (`وَعْد / ٱلْوَعْدُ`, merfû' isim)"
            elif 'GEN' in f:
                return "Verilen kesin sözün / taahhüdün (`وَعْدِهِۦ / ٱلْوَعْدِ`, muzâfun ileyh mecrûr)"
            elif 'INDEF' in f:
                if (s, a) in ((9, 111), (16, 38), (21, 104)):
                    return "Üstlenilmiş bağlayıcı bir hak ve söz olarak (`وَعْدًا`, mef'ûl-i mutlak / tekitli masdar mansûb)"
                return "Mutlaka gerçekleşecek bir söz ve sonuç olarak (`وَعْدًا`, mansûb masdar / isim)"
            else:
                if (s, a) in ((4, 122), (10, 4), (30, 6), (31, 9)):
                    return "Allah'ın şaşmaz gerçek sözü gereğince (`وَعْدَ ٱللَّهِ`, mansûb masdar / muzâf)"
                return "Verilen kesin sözü / vaadi (`وَعْد / ٱلْوَعْدَ`, mansûb mef'ûl veya isim)"
        elif lemma == 'm~awoEid':
            if 'NOM' in f:
                return "Belirlenmiş buluşma zamanı, mekânı veya akıbet durağı (`مَوْعِد`, merfû' isim)"
            return "Belirlenmiş bir vade, buluşma anı veya yer (`مَوْعِد`, mansûb isim / zarf)"
        elif lemma == 'm~awoEidap':
            return "Ona vermiş olduğu tekil bir sözden dolayı (`مَّوْعِدَةٍ`, harf-i cerli tekil isim mecrûr)"
        elif lemma == 'm~iyEaAd':
            if 'NOM' in f:
                return "Şaşmaz biçimde tayin edilmiş buluşma günü (`مِّيعَادُ`, merfû' mübtedâ)"
            elif 'GEN' in f:
                return "Belirlenen buluşma vaktinde (`ٱلْمِيعَٰدِ`, harf-i cerli mecrûr isim)"
            return "Belirlenmiş kesin vadeden ve sözden (`ٱلْمِيعَادَ`, mef'ûl bih mansûb)"
        elif lemma == 'waEiyd':
            if 'ACC' in f:
                return "Benim yaptırım ve uyarı bildirimimden (`وَعِيدِ`, mahzuf mütekellim yâlı mef'ûl bih mansûb)"
            return "Kesinleşmiş yaptırım uyarısının / uyarı gününün (`وَعِيدِ / ٱلْوَعِيدِ`, mecrûr isim)"
        elif lemma == 'mawoEuwd':
            return "Gerçekleşeceği önceden bildirilip söz verilmiş [güne] (`ٱلْمَوْعُودِ`, ismi mef'ûl sıfat mecrûr)"

    elif root_ar == 'ب-ص-ر':
        if lemma == 'baSurato':
            if '1S' in f:
                return "Onların fark etmediği şeyi içten sezerek gördüm (`بَصُرْتُ`, I. bab malûm mâzî fiili, 1. tekil; `بِـ` ile geçişli)"
            elif '3FS' in f:
                return "Uzaktan onu gözetleyip fark etti (`فَبَصُرَتْ`, I. bab malûm mâzî fiili, 3. tekil dişil; `بِـ` ile geçişli)"
            return "Onların görmediği / fark edemediği (`يَبْصُرُوا۟`, I. bab meczûm muzâri fiili, 3. çoğul eril)"
        elif lemma == '>aboSara':
            if 'IMPV' in f:
                if (s, a) in ((18, 26), (19, 38)):
                    return "O ne mükemmel görür! / O gün neler görecekler! (`أَبْصِرْ بِـ`, IV. bab taaccüb kipinde emir fiili)"
                return "Onları veya sonucu gözle (`أَبْصِرْ / أَبْصِرْهُمْ`, IV. bab emir fiili, muhatap tekil)"
            elif 'PERF' in f:
                if '1P' in f:
                    return "Biz gerçeği apaçık gördük (`أَبْصَرْنَا`, IV. bab malûm mâzî fiili, 1. çoğul)"
                return "Gerçeği seçip gördüyse (`أَبْصَرَ`, IV. bab malûm mâzî fiili, 3. tekil eril)"
            else:
                if '2MP' in f:
                    return "Görüyor musunuz / görmez misiniz (`تُبْصِرُونَ`, IV. bab malûm muzâri fiili, 2. çoğul eril)"
                elif '2MS' in f:
                    return "Yakında sen de göreceksin (`فَسَتُبْصِرُ`, IV. bab istikbal sinli muzâri fiili, 2. tekil eril)"
                elif '3MS' in f:
                    return "Hiç görmeyen [putlar] (`يُبْصِرُ`, IV. bab malûm muzâri fiili, 3. tekil eril)"
                return "Gerçeği seçip görürler / görecekler (`يُبْصِرُونَ`, IV. bab malûm muzâri fiili, 3. çoğul eril)"
        elif lemma == 'yubaS~aru':
            return "Birbirlerine açıkça gösterilirler (`يُبَصَّرُونَهُمْ`, II. bab meçhul muzâri fiili, 3. çoğul eril + zamir)"
        elif lemma == 'baSar':
            if 'MP' in f:
                if 'NOM' in f:
                    return "Gözler / görme duyuları (`أَبْصَٰر / ٱلْأَبْصَٰرُ`, çoğul isim merfû')"
                elif 'ACC' in f:
                    return "Gözleri / görme duyularını (`أَبْصَٰر / ٱلْأَبْصَٰرَ`, çoğul isim mansûb)"
                return "Gözlerin / anlayış ve idrak sahiplerinin (`أَبْصَٰر / ٱلْأَبْصَٰرِ`, çoğul isim mecrûr)"
            else:
                if 'NOM' in f:
                    return "Bakış / görme yetisi (`بَصَر / ٱلْبَصَرُ`, tekil isim merfû')"
                elif 'ACC' in f:
                    return "Bakışı / gözü (`ٱلْبَصَرَ`, tekil isim mansûb)"
                return "Gözünün / bakışının (`بَصَرِهِۦ / ٱلْبَصَرِ`, tekil isim mecrûr)"
        elif lemma == 'baSiyr':
            if (s, a) in ((6, 50), (11, 24), (13, 16), (35, 19), (40, 58)):
                return "Seçik gören ve basiret sahibi kimse (`ٱلْبَصِير`, mübâlağalı sıfat-isim)"
            elif (s, a) in ((12, 93), (12, 96), (20, 125), (76, 2)):
                return "Gözleri açılıp gören / görür hâlde olan (`بَصِيرًا`, hâl veya mef'ûl mansûb isim-sıfat)"
            elif 'ACC' in f:
                return "Her şeyi eksiksiz ve seçik gören (`بَصِيرًا`, haberi kâne/inne veya hâl mansûb)"
            return "Her yaptığınızı ve kullarını en ince ayrıntısına dek gören (`بَصِيرٌ / ٱلْبَصِيرُ`, merfû' sıfat-haber)"
        elif lemma == 'baSiyrap':
            if 'MP' in f:
                if 'NOM' in f:
                    return "Zihni aydınlatan açık kanıtlar ve basiret belgeleri (`بَصَآئِرُ`, çoğul isim merfû')"
                return "İnsanların önünü aydınlatan açık belgeler (`بَصَآئِرَ`, çoğul isim mansûb)"
            elif 'GEN' in f:
                return "Kesin bilgi ve açık içgörü üzere (`عَلَىٰ بَصِيرَةٍ`, harf-i cerli tekil isim mecrûr)"
            return "Kendi özünün apaçık gözlemci kanıtı (`بَصِيرَةٌ`, tekil haber merfû')"
        elif lemma == 'muboSir':
            if 'MP' in f:
                return "Gerçeği bir anda seçip görenler / uyananlar (`مُّبْصِرُونَ`, IV. bab ismi fâil çoğul merfû')"
            return "Gözle görmeyi sağlayan aydınlık ve seçik (`مُبْصِرًا`, IV. bab ismi fâil tekil mansûb hâl)"
        elif lemma == 'muboSirap':
            return "Gözler önüne apaçık serilen, görüp kavranan (`مُبْصِرَةً`, IV. bab dişil ismi fâil mansûb hâl)"
        elif lemma == 'taboSirap':
            return "Zihin ve görüş açıcı bir aydınlatma penceresi olarak (`تَبْصِرَةً`, II. bab masdar mef'ûlün leh mansûb)"
        elif lemma == 'musotaboSiriyn':
            return "Gerçeği açıkça görüp kavrayacak donanımda oldukları hâlde (`مُسْتَبْصِرِينَ`, X. bab ismi fâil çoğul mansûb)"

    elif root_ar == 'ر-و-د':
        if lemma == '>araAda':
            if 'PASS' in f:
                if 'PERF' in f:
                    return "Onlar hakkında bir kötülük mü murad edildi (`أُرِيدَ`, IV. bab meçhul mâzî fiili, 3. tekil eril)"
                return "Sizden istenen ve yönelinen amaç (`يُرَادُ`, IV. bab meçhul muzâri fiili, 3. tekil eril)"
            if 'PERF' in f:
                if '1S' in f:
                    return "Ben ... istedim / yöneldim (`أَرَدتُّ`, IV. bab malûm mâzî fiili, 1. tekil)"
                elif '1P' in f:
                    return "Biz ... istedik / yöneldik (`أَرَدْنَا`, IV. bab malûm mâzî fiili, 1. çoğul)"
                elif '2MP' in f:
                    return "Siz ... istediniz / niyetlendiniz (`أَرَدتُّمْ`, IV. bab malûm mâzî fiili, 2. çoğul eril)"
                elif '3MD' in f:
                    return "İkisi ... isterse (`أَرَادَا`, IV. bab malûm mâzî fiili, 3. ikil eril)"
                elif '3MP' in f:
                    return "Onlar ... istediler / giriştiler (`أَرَادُوا۟`, IV. bab malûm mâzî fiili, 3. çoğul eril)"
                elif '3FP' in f:
                    return "Onlar (kadınlar) ... isterlerse (`أَرَدْنَ`, IV. bab malûm mâzî fiili, 3. çoğul dişil)"
                return "O ... istedi / yönelip murad etti (`أَرَادَ`, IV. bab malûm mâzî fiili, 3. tekil eril)"
            else:
                if '1S' in f:
                    return "Ben ... isterim / yönelirim (`أُرِيدُ`, IV. bab malûm muzâri fiili, 1. tekil)"
                elif '1P' in f:
                    return "Biz ... istiyoruz / amaçlıyoruz (`نُرِيدُ`, IV. bab malûm muzâri fiili, 1. çoğul)"
                elif '2MS' in f:
                    return "Sen ... istiyorsun (`تُرِيدُ`, IV. bab malûm muzâri fiili, 2. tekil eril)"
                elif '2MP' in f:
                    return "Siz ... istiyorsunuz (`تُرِيدُونَ`, IV. bab malûm muzâri fiili, 2. çoğul eril)"
                elif '2FP' in f:
                    return "Siz (kadınlar) ... istiyorsanız (`تُرِدْنَ`, IV. bab malûm muzâri fiili, 2. çoğul dişil)"
                elif '3MD' in f:
                    if 'JUS' in f:
                        return "İkisi (hakemler) düzeltmek isterlerse (`يُرِيدَآ`, IV. bab meczûm muzâri fiili, 3. ikil eril)"
                    return "İkisi ... istiyorlar (`يُرِيدَانِ`, IV. bab malûm muzâri fiili, 3. ikil eril)"
                elif '3MP' in f:
                    if 'JUS' in f:
                        return "Onlar ... isterlerse (`يُرِيدُوا۟`, IV. bab meczûm muzâri fiili, 3. çoğul eril)"
                    return "Onlar ... isterler / amaçlarlar (`يُرِيدُونَ`, IV. bab malûm muzâri fiili, 3. çoğul eril)"
                else:
                    if (s, a) == (18, 77):
                        return "Yıkılmaya yüz tutmuş / devrilmeye meyletmiş (`يُرِيدُ`, IV. bab muzâri fiili, 3. tekil eril — cansız duvarın fiziksel eğilimi)"
                    elif 'JUS' in f:
                        return "O ... isterse / dilerse (`يُرِدْ / يُرِدِ`, IV. bab meczûm muzâri fiili, 3. tekil eril)"
                    return "O ... ister / amaçlar / yönelir (`يُرِيدُ`, IV. bab malûm muzâri fiili, 3. tekil eril)"
        elif lemma == 'ra`wadu':
            if 'IMPF' in f:
                if '1P' in f:
                    return "Ondan (babasından) onu yumuşaklıkla ikna edip koparmaya çalışacağız (`سَنُرَٰوِدُ`, III. bab istikbal muzâri fiili, 1. çoğul)"
                return "Onu (öz benliğinden) döndürüp kendine çekmeye çalışıyor (`تُرَٰوِدُ`, III. bab malûm muzâri fiili, 3. tekil dişil)"
            elif '1S' in f:
                return "Onu kendisinden döndürüp elde etmeye çalıştım (`رَٰوَدتُّهُۥ`, III. bab mâzî fiili, 1. tekil)"
            elif '2FP' in f:
                return "Yusuf'u öz benliğinden döndürmeye kalktığınızda (`رَٰوَدتُّنَّ`, III. bab mâzî fiili, 2. çoğul dişil)"
            elif '3MP' in f:
                return "Konukları konusunda onu zorlayıp döndürmeye çalıştılar (`رَٰوَدُوهُ`, III. bab mâzî fiili, 3. çoğul eril)"
            return "Onu öz duruşundan döndürüp kendine çekmeye çalıştı (`رَٰوَدَتْهُ / رَٰوَدَتْنِى`, III. bab mâzî fiili, 3. tekil dişil)"
        elif lemma == 'ruwayod':
            return "Azıcık, yavaşça ve yumuşak adımla (`رُوَيْدًۢا`, küçültme kalıbında mef'ûl-i mutlak / hal mansûb isim)"

    elif root_ar == 'ل-ق-ي':
        if lemma == 'laqu':
            if 'PERF' in f:
                if '1P' in f:
                    return "Biz ... ile karşılaştık / bulduk (`لَقِينَا`, I. bab malûm mâzî fiili, 1. çoğul)"
                elif '2MP' in f:
                    return "Siz ... ile karşılaştığınızda (`لَقِيتُمُ / لَقِيتُمْ`, I. bab malûm mâzî fiili, 2. çoğul eril)"
                elif '3MD' in f:
                    return "İkisi ... ile karşılaşınca (`لَقِيَا`, I. bab malûm mâzî fiili, 3. ikil eril)"
                return "Onlar ... ile karşılaştıklarında (`لَقُوا۟ / لَقُوكُمْ`, I. bab malûm mâzî fiili, 3. çoğul eril)"
            else:
                if '2MP' in f:
                    return "Siz onunla karşılaşmadan önce (`تَلْقَوْهُ`, I. bab mansûb muzâri fiili, 2. çoğul eril)"
                elif '3MP' in f:
                    return "Onlar karşılaşırlar / kavuşurlar (`يَلْقَوْنَ / يَلْقَوْنَهُۥ`, I. bab malûm muzâri fiili, 3. çoğul eril)"
                elif 'JUS' in f:
                    return "Karşılığını bulur / karşılaşır (`يَلْقَ`, I. bab meczûm muzâri fiili, 3. tekil eril)"
                return "Açılmış olarak bulacağı / karşılaşacağı (`يَلْقَىٰهُ`, I. bab malûm muzâri fiili, 3. tekil eril)"
        elif lemma == 'laq~aY`':
            if 'PASS' in f:
                if '2MS' in f:
                    return "Sana ulaştırılıp verilmektedir (`لَتُلَقَّى`, II. bab meçhul muzâri fiili, 2. tekil eril)"
                elif '3MP' in f:
                    return "Onlar (esenlik dileğiyle) karşılanırlar (`وَيُلَقَّوْنَ`, II. bab meçhul muzâri fiili, 3. çoğul eril)"
                return "Ona kavuşturulur / ulaştırılır (`يُلَقَّىٰهَآ`, II. bab meçhul muzâri fiili, 3. tekil eril)"
            return "Onlara (parlaklık ve sevinç) verip karşıladı (`وَلَقَّىٰهُمْ`, II. bab malûm mâzî fiili, 3. tekil eril)"
        elif lemma == 'yula`qu':
            return "Onlar (o günle) karşılaşıp buluşuncaya kadar (`يُلَٰقُوا۟`, III. bab mansûb muzâri fiili, 3. çoğul eril)"
        elif lemma == '>aloqaY`^':
            if 'PASS' in f:
                if 'PERF' in f:
                    if '3MP' in f:
                        return "Oraya atıldıklarında (`أُلْقُوا۟`, IV. bab meçhul mâzî fiili, 3. çoğul eril)"
                    return "Bırakıldı / atıldı / indirildi (`أُلْقِىَ / أُلْقِىَ`, IV. bab meçhul mâzî fiili, 3. tekil eril)"
                elif '2MS' in f:
                    return "Kınanmış hâlde atılırsın (`فَتُلْقَىٰ`, IV. bab meçhul muzâri fiili, 2. tekil eril)"
                return "Atılır / bırakılır / indirilir (`يُلْقَىٰٓ`, IV. bab meçhul muzâri fiili, 3. tekil eril)"
            elif 'IMPV' in f:
                if '2FS' in f:
                    return "Onu (sandığı) suya bırak (`فَأَلْقِيهِ`, IV. bab emir fiili, 2. tekil dişil)"
                elif '2MD' in f:
                    return "İkiniz atın (`أَلْقِيَا / فَأَلْقِيَاهُ`, IV. bab emir fiili, 2. ikil)"
                elif '2MP' in f:
                    return "Siz atın / ortaya koyun (`أَلْقُوا۟`, IV. bab emir fiili, 2. çoğul eril)"
                return "At / bırak (`أَلْقِ / أَلْقِهَا`, IV. bab emir fiili, 2. tekil eril)"
            elif 'PERF' in f:
                if '1S' in f:
                    return "Üzerine (sevgi) bıraktım / saldım (`وَأَلْقَيْتُ`, IV. bab mâzî fiili, 1. tekil)"
                elif '1P' in f:
                    return "Yerleştirdik / attık / saldık (`أَلْقَيْنَا`, IV. bab mâzî fiili, 1. çoğul)"
                elif '3FS' in f:
                    return "İçindekileri dışarı attı (`وَأَلْقَتْ`, IV. bab mâzî fiili, 3. tekil dişil)"
                elif '3MP' in f:
                    return "Attılar / bıraktılar / teklif ettiler (`أَلْقَوْا۟`, IV. bab mâzî fiili, 3. çoğul eril)"
                return "Attı / bıraktı / ulaştırdı (`أَلْقَىٰ`, IV. bab mâzî fiili, 3. tekil eril)"
            else:
                if '1S' in f:
                    return "Kalplerine salacağım (`سَأُلْقِى`, IV. bab istikbal muzâri fiili, 1. tekil)"
                elif '1P' in f:
                    return "Üzerine bırakacağız / salacağız (`سَنُلْقِى`, IV. bab istikbal muzâri fiili, 1. çoğul)"
                elif '2MS' in f:
                    return "Sen ortaya koyarsın (`تُلْقِىَ`, IV. bab mansûb muzâri fiili, 2. tekil eril)"
                elif '2MP' in f:
                    if 'JUS' in f:
                        return "Kendinizi atmayın (`وَلَا تُلْقُوا۟`, IV. bab nehiy meczûm muzâri fiili, 2. çoğul eril)"
                    return "Onlara (sevgiyle bilgi) ulaştırıyorsunuz (`تُلْقُونَ`, IV. bab muzâri fiili, 2. çoğul eril)"
                elif '3MP' in f:
                    if 'JUS' in f:
                        return "Size barış bırakıp teslim olurlarsa (`وَيُلْقُوٓا۟`, IV. bab meczûm muzâri fiili, 3. çoğul eril)"
                    return "Atarlar / kulak verirler (`يُلْقُونَ`, IV. bab muzâri fiili, 3. çoğul eril)"
                elif 'JUS' in f:
                    return "Onu (kıyıya) bıraksın (`فَلْيُلْقِهِ`, IV. bab emir lâm'lı meczûm muzâri fiili, 3. tekil eril)"
                return "Atar / bırakır / indirir (`يُلْقِى`, IV. bab malûm muzâri fiili, 3. tekil eril)"
        elif lemma == 'talaq~aY`^':
            if 'PERF' in f:
                return "Alıp kabul etti (`فَتَلَقَّىٰٓ`, V. bab malûm mâzî fiili, 3. tekil eril)"
            elif '2MP' in f:
                return "Dilden dile alıp aktarıyordunuz (`تَلَقَّوْنَهُۥ`, V. bab malûm muzâri fiili, 2. çoğul eril)"
            elif (s, a) == (21, 103):
                return "Kozmik görevliler onları karşılar (`وَتَتَلَقَّىٰهُمُ`, V. bab muzâri fiili; korpus etiketi `2MS`, bağlamda `3FS`)"
            return "Karşılayıp kaydeder (`يَتَلَقَّى`, V. bab malûm muzâri fiili, 3. tekil eril)"
        elif lemma == '{lotaqaY':
            if 'IMPF' in f:
                return "İkisi birbirine kavuşur / karşılaşır (`يَلْتَقِيَانِ`, VIII. bab muzâri fiili, 3. ikil eril)"
            elif '2MP' in f:
                return "Siz karşı karşıya geldiğinizde (`ٱلْتَقَيْتُمْ`, VIII. bab mâzî fiili, 2. çoğul eril)"
            elif '3FD' in f:
                return "İki topluluk karşı karşıya geldi (`ٱلْتَقَتَا`, VIII. bab mâzî fiili, 3. ikil dişil)"
            return "Karşı karşıya geldi / birleşti (`ٱلْتَقَى`, VIII. bab mâzî fiili, 3. tekil eril)"
        elif lemma == "liqaA^'":
            if 'GEN' in f:
                return "Karşılaşmaya / kavuşmaya / huzura çıkmaya (`بِلِقَآءِ / لِقَآئِهِۦ`, III. bab masdar mecrûr)"
            return "Karşılaşmayı / kavuşmayı (`لِقَآءَ`, III. bab masdar mansûb)"
        elif lemma == "tiloqaA^'":
            if 'GEN' in f:
                return "Kendi yanımdan / yönümden (`مِن تِلْقَآئِ نَفْسِىٓ`, harf-i cerli isim mecrûr)"
            return "Yönüne doğru / karşısına (`تِلْقَآءَ`, mekân zarfı mansûb isim)"
        elif lemma in ('m~ula`quwA', 'mula`qiy', 'mula`q', 'la`qiy'):
            return "Karşılaşacak / kavuşacak olan (`مُلَٰقُوا۟ / مُلَٰقِيهِ / مُلَٰقٍ / لَٰقِيهِ`, III. bab ismi fâil merfû')"
        elif lemma == 'm~uloquwn':
            if 'ACC' in f:
                return "İlk ortaya koyanlar / atanlar (`ٱلْمُلْقِينَ`, IV. bab ismi fâil çoğul mansûb)"
            return "Ortaya koyup atanlar (`مُّلْقُونَ`, IV. bab ismi fâil çoğul merfû')"
        elif lemma == 'muloqiya`t':
            return "Öğüt ve hatırlatma bırakan/indiren güçlere (`فَٱلْمُلْقِيَٰتِ`, IV. bab dişil çoğul ismi fâil mecrûr)"
        elif lemma == 'mutalaq~iyaAn':
            return "Karşılıklı kayıt alan iki gözlemci (`ٱلْمُتَلَقِّيَانِ`, V. bab ikil ismi fâil merfû')"
        elif lemma == 't~alaAq':
            return "Herkesin yüz yüze buluşacağı günün (`يَوْمَ ٱلتَّلَاقِ`, VI. bab masdar muzâfun ileyh mecrûr)"

    elif root_ar == 'د-و-ن':
        if pos == 'LOC':
            if (s, a) in ((4, 48), (4, 116)):
                return "Bu sınırın altında ve berisinde kalan [diğer her şeyi] (`دُونَ`, mansûb derece-mekân zarfı)"
            elif (s, a) in ((7, 168), (72, 11)):
                return "O düzeyin berisinde ve daha aşağısında olanlar (`دُونَ`, mansûb derece zarfı)"
            elif (s, a) == (7, 205):
                return "Yüksek sesin berisinde, daha alçak ve içten bir tonda (`وَدُونَ`, mansûb zarf)"
            elif (s, a) in ((21, 82), (52, 47)):
                return "Bunun berisinde ve bundan başka [işler/yaptırım] (`دُونَ`, mansûb zarf)"
            elif (s, a) == (32, 21):
                return "En büyük hesap yaptırımının berisinde ve öncesinde (`دُونَ`, mansûb zaman-derece zarfı)"
            return "Allah'ın berisinde ve O'nun düzeyinin tamamen altında (`دُونَ`, mansûb mekân-konum zarfı)"
        else:
            if (s, a) in ((3, 28), (4, 139), (4, 144), (33, 50)):
                return "Güvene erenlerin berisinde / onların dışında (`مِن دُونِ ٱلْمُؤْمِنِينَ`, câr ve mecrûr isim)"
            elif (s, a) in ((2, 94), (62, 6)):
                return "Diğer bütün insanların berisinde / onlar hariç tutularak (`مِن دُونِ ٱلنَّاسِ`, câr ve mecrûr isim)"
            elif (s, a) in ((7, 81), (27, 55)):
                return "Kadınların berisinde / kadınları bırakıp (`مِن دُونِ ٱلنِّسَآءِ`, câr ve mecrûr isim)"
            elif (s, a) in ((23, 63), (48, 27)):
                return "Bunun berisinde ve öncesinde (`مِن دُونِ ذَٰلِكَ`, câr ve mecrûr isim)"
            elif (s, a) == (3, 118):
                return "Kendi çevrenizin berisinde / sizden olmayanlardan (`مِن دُونِكُمْ`, câr ve mecrûr isim)"
            elif (s, a) in ((8, 60), (19, 17), (28, 23), (34, 41)):
                return "Onların berisinde / dışında / önünde (`مِن دُونِهِمْ`, câr ve mecrûr isim)"
            elif (s, a) in ((18, 90), (18, 93), (55, 62)):
                return "Onun / o ikisinin berisinde ve ötesinde (`مِن دُونِهَا / دُونِهِمَا`, câr ve mecrûr isim)"
            elif (s, a) in ((16, 86), (17, 2), (18, 50), (18, 102), (21, 43), (25, 18)):
                return "Beni / Seni / Bizi bırakıp O'nun düzeyinin altında kalan (`مِن دُونِى / دُونِكَ / دُونِنَا`, câr ve mecrûr isim)"
            return "Yegâne Yüce Yaratıcı'yı bırakıp O'nun düzeyinin altında ve berisinde kalan (`مِن دُونِ ٱللَّهِ / دُونِهِۦ`, câr ve mecrûr isim)"

    if root_ar == 'ن-ع-م':
        if lemma == 'naE~ama':
            return "Sınamak için imkânlarını bollaştırıp konfor içinde yaşattı (`نَعَّمَ`, II. bab mâzî fiil `3MS`)"
        if lemma == 'n~aAEimap':
            return "Tazelik, iç huzur ve dingin refahla parlayan yüzler (`نَّاعِمَةٌ`, müennes ism-i fâil merfû)"
        if lemma == "naEomaA^'":
            return "Darlık sonrası gelen yumuşak refah, bolluk ve esenlik hâli (`نَعْمَآءَ`, sıfat-isim mansûb)"
        if lemma == 'n~aEomap':
            if 'INDEF|GEN' in features:
                return "Keyif ve dünyevî konfor/refah ortamı (`وَنَعْمَةٍ`, müennes isim mecrûr — kesreli `نِعْمَة`ten farklı olarak fethalı)"
            return "Dünyevî varlık, lüks ve refah içinde yüzenler (`ٱلنَّعْمَةِ`, müennes isim mecrûr)"
        if lemma == 'niEoma':
            if (s, a) in ((2, 271), (4, 58)):
                return "Ne güzel / ne mükemmel şeydir o! (`فَنِعِمَّا / نِعِمَّا`, övgü bildiren câmid mâzî fiil + `مَا`)"
            if (s, a) in ((16, 30), (37, 75)):
                return "Andolsun ne güzel / ne mükemmeldir! (`وَلَنِعْمَ / فَلَنِعْمَ`, tekit lâmı + övgü bildiren câmid mâzî fiil `3MS`)"
            return "Ne güzel, ne iyi, ne mükemmeldir! (`نِعْمَ / فَنِعْمَ / وَنِعْمَ`, övgü bildiren câmid mâzî fiil `3MS`)"
        if lemma == '>anoEama':
            if '2MS' in features:
                return "İyilik, imkân ve refah bahşettin (`أَنْعَمْتَ`, IV. bab mâzî fiil `2MS` — `عَلَى` ile)"
            if '1S' in features:
                return "İyilik, imkân ve koruma bahşettim (`أَنْعَمْتُ`, IV. bab mâzî fiil `1S` — `عَلَى` ile)"
            if '1P' in features:
                return "İyilik ve imkân bahşettik (`أَنْعَمْنَا`, IV. bab mâzî fiil `1P` — `عَلَى` ile)"
            return "İyilik, yön ve ayrıcalık bahşetti (`أَنْعَمَ`, IV. bab mâzî fiil `3MS` — `عَلَى` ile)"
        if lemma == 'naEiym':
            if 'INDEF|NOM' in features:
                return "Kesintisiz, kalıcı hoşluk ve huzur hâli (`نَعِيمٌ`, müzekker isim merfû)"
            if 'INDEF|ACC' in features:
                return "Sürekli huzur, ferahlık ve nimet hâli (`نَعِيمًا`, müzekker isim mansûb)"
            if 'INDEF|GEN' in features:
                return "Kesintisiz refah, ferahlık ve mutluluk hâli (`نَعِيمٍ`, nekre isim mecrûr)"
            return "Sürekli ve köklü huzur, ferahlık ve nimet (`ٱلنَّعِيمِ`, marife isim mecrûr)"
        if lemma == 'n~aEam':
            if (s, a) == (5, 95):
                return "Evcil yumuşak huylu besi hayvanları (`ٱلنَّعَمِ`, topluluk ismi mecrûr)"
            if 'NOM' in features:
                return "Yumuşak huylu evcil sürü ve besi hayvanları (`أَنْعَٰمٌ / ٱلْأَنْعَٰمُ`, kırık çoğul isim merfû)"
            if 'ACC' in features:
                return "Evcil sürü ve besi hayvanları (`أَنْعَٰمًا / ٱلْأَنْعَٰمَ`, kırık çoğul isim mansûb)"
            return "Evcil sürü ve besi hayvanları (`ٱلْأَنْعَٰمِ / أَنْعَٰمٍ`, kırık çoğul isim mecrûr)"
        if lemma == 'niEomap':
            if (s, a) in ((16, 112), (16, 121)):
                return "Az ve özel değerli nimetler (`بِأَنْعُمِ / لِّأَنْعُمِهِ`, kıllet çoğulu `أَفْعُل` vezni mecrûr)"
            if (s, a) == (31, 20):
                return "Sayısız bol nimetler (`نِعَمَهُۥ`, kesret çoğulu `فِعَل` vezni mansûb)"
            if 'INDEF|NOM' in features:
                return "Bir iyilik, bağış veya nimet (`نِعْمَةٌ`, müennes isim merfû)"
            if 'INDEF|ACC' in features:
                return "Bir iyilik, imkân veya nimet (`نِعْمَةً`, müennes isim mansûb)"
            if 'INDEF|GEN' in features:
                return "Bir iyilik, hoşluk veya minnet borcu (`نِعْمَةٍ`, müennes isim mecrûr)"
            if 'F|NOM' in features:
                return "Rabbimin iyiliği ve koruyucu lütfu (`نِعْمَةُ`, müennes isim merfû)"
            if 'F|GEN' in features:
                return "Koruyucu iyilik, nimet ve lütuf (`بِنِعْمَتِ / بِنِعْمَةِ`, müennes isim mecrûr)"
            return "Verilen iyilik, lütuf ve imkân nimeti (`نِعْمَتَ / نِعْمَةَ / نِعْمَتِى / نِعْمَتَهُۥ / نِعْمَتَكَ`, müennes isim mansûb)"

    if root_ar == 'س-ل-م':
        if lemma == 'sa`limuwn':
            return "Henüz engelden ve arızadan uzak, sapasağlam ve esenlik içinde olanlar (`سَٰلِمُونَ`, I. bab ism-i fâil cem-i müzekker merfû)"
        if lemma == 'musotasolimuwn':
            return "Çaresizce el-kol indirip tamamen pes ederek teslim olanlar (`مُسْتَسْلِمُونَ`, X. bab ism-i fâil çoğul merfû)"
        if lemma == 's~ilom':
            return "Topyekûn barış, güvenlik ve esenlik bütünlüğü (`ٱلسِّلْمِ`, kesreli masdar-isim mecrûr)"
        if lemma == 's~alom':
            return "Barış, ateşkes ve karşılıklı saldırmazlık uzlaşısı (`لِلسَّلْمِ / ٱلسَّلْمِ`, fethalı masdar-isim mecrûr)"
        if lemma == 'sul~am':
            if 'ACC' in features:
                return "Yukarıya güvenle ulaştıran merdiven (`سُلَّمًا`, müzekker isim mansûb)"
            return "Yükseğe sağ salim çıkaran merdiven (`سُلَّمٌ`, müzekker isim merfû)"
        if lemma == 'saliym':
            return "Her türlü arızadan, bölünmeden ve hastalıktan arınmış sapasağlam/duru (`سَلِيمٍ`, `فَعِيل` sıfat-isim mecrûr)"
        if lemma == 'm~usal~amap':
            if (s, a) == (2, 71):
                return "Kusurdan, leke ve arızadan tamamen arındırılmış sapasağlam (`مُسَلَّمَةٌ`, II. bab ism-i mef'ûl merfû)"
            return "Hak sahibine eksiksiz ve sağ salim teslim edilecek olan (`مُّسَلَّمَةٌ`, II. bab ism-i mef'ûl merfû)"
        if lemma == 'tasoliym':
            return "Tam bir içtenlikle eksiksiz teslim oluş / esenlik dileği sunuş (`تَسْلِيمًا`, II. bab mef'ûl-i mutlak masdar mansûb)"
        if lemma == 'sal~ama':
            if 'IMPV' in features:
                return "Esenlik, dirlik ve barış dileği sunun (`فَسَلِّمُوا۟ / وَسَلِّمُوا۟`, II. bab emir `2MP`)"
            if (s, a) == (2, 233):
                return "Eksiksiz ve sorunsuz biçimde teslim ettiğinizde (`سَلَّمْتُم`, II. bab mâzî fiil `2MP`)"
            if (s, a) == (8, 43):
                return "Dağılmadan koruyup esenliğe çıkardı (`سَلَّمَ`, II. bab mâzî fiil `3MS`)"
            if (s, a) == (4, 65):
                return "İçtenlikle tam teslimiyet göstersinler (`وَيُسَلِّمُوا۟`, II. bab mansûb muzâri `3MP`)"
            return "Esenlik ve barış dileği sunasınız (`وَتُسَلِّمُوا۟`, II. bab mansûb muzâri `2MP`)"
        if lemma == 'salam':
            if (s, a) == (39, 29):
                return "Tek bir merkeze bölünmeden pürüzsüz ve tam bağlı olan (`سَلَمًا`, `فَعَل` sıfat-isim mansûb)"
            return "Barış, esenlik ve boyun eğiş teklifi (`ٱلسَّلَمَ`, `فَعَل` isim mansûb)"
        if lemma == '<isola`m':
            if (s, a) in ((9, 74), (49, 17)):
                return "Dışa dönük teslimiyet beyanı ve barış anlaşmasına giriş (`إِسْلَٰمِهِمْ / إِسْلَٰمَكُم`, IV. bab masdar)"
            return "Kendini kusursuz Yaratıcı'ya arızasız adama ve esenlik düzeni (`ٱلْإِسْلَٰم`, IV. bab masdar)"
        if lemma == 'm~usolimap':
            return "Yalnızca Sana içtenlikle teslim olmuş uyumlu (`مُّسْلِمَةً`, IV. bab dişil ism-i fâil mansûb)"
        if lemma == 'musolima`t':
            return "Kendini hakka ve esenliğe teslim etmiş kadınlar (`وَٱلْمُسْلِمَٰتِ / مُسْلِمَٰتٍ`, IV. bab dişil çoğul ism-i fâil mansûb)"
        if lemma == '>asolama':
            if 'IMPV' in features:
                return "İçtenlikle teslim ol / bütün benliğini esenlik düzenine ada (`أَسْلِمْ / أَسْلِمُوا۟`, IV. bab emir)"
            if '1S' in features:
                return "Kendimi bütünüyle teslim ettim (`أَسْلَمْتُ`, IV. bab mâzî `1S`)"
            if '1P' in features:
                return "Teslimiyet gösterip boyun eğdik (`أَسْلَمْنَا / لِنُسْلِمَ`, IV. bab `1P`)"
            if '2MP' in features:
                return "Teslim olup esenliğe girdiniz (`ءَأَسْلَمْتُمْ / تُسْلِمُونَ`, IV. bab `2MP`)"
            if '3MD' in features:
                return "İkisi birden tam teslim oldu (`أَسْلَمَا`, IV. bab tesniye mâzî `3MD`)"
            if '3MP' in features:
                return "İçten teslimiyet gösterip esenlik düzenine girdiler (`أَسْلَمُوا۟ / يُسْلِمُونَ`, IV. bab `3MP`)"
            return "Bütün yönelişini ve varlığını teslim etti (`أَسْلَمَ / يُسْلِمْ`, IV. bab `3MS`)"
        if lemma == 'musolim':
            if 'MD' in features:
                return "Sana içtenlikle teslim olmuş iki kişi (`مُسْلِمَيْنِ`, IV. bab ism-i fâil tesniye mansûb)"
            if 'MS' in features:
                return "Kendini hakka teslim edip eğriden uzaklaşan biri (`مُّسْلِمًا / مُسْلِمًا`, IV. bab ism-i fâil tekil mansûb)"
            if 'NOM' in features:
                return "Kendini Yaratıcı'ya ve barış bütünlüğüne tam adayanlar (`مُسْلِمُونَ / ٱلْمُسْلِمُونَ`, IV. bab ism-i fâil merfû)"
            return "Kendini içtenlikle hakka ve esenliğe teslim edenler (`مُسْلِمِينَ / ٱلْمُسْلِمِينَ / لِلْمُسْلِمِينَ`, IV. bab ism-i fâil mecrûr/mansûb)"
        if lemma == 'sala`m':
            if (s, a) == (59, 23):
                return "Her türlü kusur, noksanlık ve bozulmadan arınmış Mutlak Esenlik Kaynağı (`ٱلسَّلَٰمُ`, sıfat merfû)"
            if (s, a) in ((5, 16), (6, 127), (10, 25)):
                return "Her türlü yıkımdan korunmuş mutlak esenlik ve dirlik (`ٱلسَّلَٰمِ`, marife isim mecrûr)"
            if (s, a) == (4, 94):
                return "Size barış ve dokunulmazlık selamını/güvencesini (`ٱلسَّلَٰمَ`, marife isim mansûb)"
            if 'ACC' in features:
                return "Barış, güvenlik, zarar vermeme ve esenlik dileği (`سَلَٰمًا`, nekre mansûb)"
            if 'GEN' in features:
                return "Tam bir güvenlik, sağ salimlik ve esenlik içinde (`بِسَلَٰمٍ`, mecrûr)"
            return "Esenlik, güvenlik, arızasızlıktan doğan huzur ve dirlik (`سَلَٰمٌ / ٱلسَّلَٰمُ`, merfû)"

    if root_ar == 'د-ن-و':
        if lemma == 'daAn':
            return "El uzatacak kadar yaklaşmış ve kolayca erişilebilir olan (`دَانٍ`, nakıs ism-i fâil merfû — son yâ düşmüş)"
        if lemma == 'daAniyap':
            if 'ACC' in features:
                return "Üzerine doğru eğilip iyice yaklaşmış (`وَدَانِيَةً`, dişil ism-i fâil mansûb)"
            return "Uzanılıp tutulacak ölçüde hemen yakında sarkmış (`دَانِيَةٌ`, dişil ism-i fâil merfû)"
        if lemma == 'danaA':
            if '3FP' in features:
                return "Üzerlerine doğru iyice yaklaştırıp sarkıtsınlar (`يُدْنِينَ`, IV. bab muzâri `3FP`)"
            return "Hemen yakına geldi, yaklaştı (`دَنَا`, I. bab mâzî fiil `3MS`)"
        if lemma == '>adonaY`':
            if (s, a) == (73, 20):
                return "Zaman olarak daha yakın / biraz daha az bir kısmında (`أَدْنَىٰ`, mansûb zaman zarfı)"
            if (s, a) == (53, 9):
                return "İki yay aralığından bile daha yakın (`أَدْنَىٰ`, ism-i tafdîl mansûb)"
            if (s, a) == (32, 21):
                return "Hemen yakında gerçekleşen (`ٱلْأَدْنَىٰ`, marife sıfat merfû-mecrûr)"
            if 'GEN' in features:
                return "En yakın bölgede / bundan daha azında (`أَدْنَى / ٱلْأَدْنَىٰ`, mecrûr ism-i tafdîl)"
            return "Daha yakın, daha elverişli veya değer/sayıca daha aşağı/az (`أَدْنَىٰ / وَأَدْنَىٰٓ`, ism-i tafdîl)"
        if lemma == 'd~unoyaA':
            if (s, a) == (8, 42):
                return "Size mesafece en yakın yamaç/taraf (`ٱلدُّنْيَا`, dişil sıfat mecrûr — `ٱلْقُصْوَىٰ` zıddı)"
            if (s, a) in ((37, 6), (41, 12), (67, 5)):
                return "Yerküreye en yakın gök katmanı (`ٱلدُّنْيَا`, dişil sıfat mansûb)"
            if pos == 'ADJ':
                if 'NOM' in features:
                    return "Şu hemen yakın olan geçici yaşam aşaması (`ٱلدُّنْيَا`, dişil tafdîl sıfatı merfû)"
                if 'ACC' in features:
                    return "Şu yakın ve ilk yaşam aşamasını (`ٱلدُّنْيَا`, dişil tafdîl sıfatı mansûb)"
                return "Şu yakın ve ilk yaşam aşamasının (`ٱلدُّنْيَا`, dişil tafdîl sıfatı mecrûr)"
            if 'NOM' in features:
                return "Hemen yakındaki ilk dünya aşaması (`ٱلدُّنْيَا`, dişil tafdîl isim merfû)"
            return "Şu hemen yakındaki ilk dünya aşaması (`ٱلدُّنْيَا`, dişil tafdîl isim mecrûr)"

    if root_ar == 'ق-د-ر':
        if lemma == 'quduwr':
            return "Yerinden kıpırdamayan büyük pişirme kazanları (`وَقُدُورٍ`, `قِدْر` kırık çoğulu mecrûr)"
        if lemma == 'm~aqoduwr':
            return "Ölçüsü, sınırları ve planı kesinleşmiş olan (`مَّقْدُورًا`, I. bab ism-i mef'ûl mansûb)"
        if lemma == 'miqodaAr':
            if 'GEN' in features:
                return "Kesin bir ölçek ve belirlenmiş ölçü ile (`بِمِقْدَارٍ`, `مِفْعَال` ölçü ismi mecrûr)"
            return "Zaman ve süreç ölçeği / ölçüsü (`مِقْدَارُهُۥ`, `مِفْعَال` ölçü ismi merfû)"
        if lemma == 'm~uqotadir':
            if 'ACC' in features:
                return "Her şey üzerinde mutlak kudret ve tasarruf sahibi (`مُّقْتَدِرًا`, VIII. bab ism-i fâil mansûb)"
            if 'MP' in features:
                return "Kesin tasarruf ve uygulama gücünü elinde tutan (`مُّقْتَدِرُونَ`, VIII. bab ism-i fâil çoğul merfû)"
            return "Mutlak güç, kapasite ve hüküm sahibi (`مُّقْتَدِرٍ`, VIII. bab ism-i fâil mecrûr)"
        if lemma == 'taqodiyr':
            if 'ACC' in features:
                return "Kusursuzca ölçülendirip oranlayarak (`تَقْدِيرًا`, II. bab mef'ûl-i mutlak masdar mansûb)"
            return "İnce hesaplı kozmik ölçülendirme ve düzenlemesi (`تَقْدِيرُ`, II. bab masdar merfû)"
        if lemma == 'qador':
            if (s, a) in ((97, 1), (97, 2), (97, 3)):
                return "Ölçü, değer ve hüküm gecesi (`ٱلْقَدْرِ`, marife isim mecrûr)"
            if (s, a) in ((6, 91), (22, 74), (39, 67)):
                return "Gerçek değeri, kıymeti ve kudret ölçüsü (`قَدْرِهِۦ`, cezimli dâl `قَدْر` mecrûr)"
            return "Belirli bir ölçü, sınır ve zaman aralığı (`قَدْرًا`, cezimli dâl `قَدْر` mansûb)"
        if lemma == 'qadar':
            if (s, a) == (2, 236):
                return "Mâlî imkânı, gücü ve kapasitesi ölçüsü (`قَدَرُهُۥ`, fethalı dâl `قَدَر` merfû)"
            if 'ACC' in features:
                return "Kesin belirlenmiş ölçü ve düzenleme olarak (`قَدَرًا`, fethalı dâl `قَدَر` mansûb)"
            return "Hassas miktar, taşıma kapasitesi ve ölçülü oran (`بِقَدَرٍ / بَقَدَرِهَا / قَدَرٍ`, fethalı dâl `قَدَر` mecrûr)"
        if lemma == 'qaAdir':
            if 'M|NOM' in features:
                return "Üstten, alttan ve toplum içinden sarsıntı indirmeye gücü yeten (`ٱلْقَادِرُ`, I. bab marife ism-i fâil merfû)"
            if 'MP|NOM' in features:
                return "Yeniden var etmeye ve hesabı gerçekleştirmeye kesin gücü yetenler (`قَٰدِرُونَ / لَقَٰدِرُونَ`, I. bab ism-i fâil merfû)"
            if 'ACC' in features:
                return "İşlerini diledikleri gibi yürütmeye kesin gücü yetenler sanısıyla (`قَٰدِرِينَ`, I. bab ism-i fâil mansûb)"
            return "Ölçüsüyle yaratıp yeniden diriltmeye tamamen gücü yeten (`قَادِرٌ / بِقَٰدِرٍ`, I. bab ism-i fâil)"
        if lemma == 'qad~ara':
            if (s, a) in ((74, 18), (74, 19), (74, 20)):
                return "Zihninde kurgulayıp ölçüp biçti (`قَدَّرَ`, II. bab mâzî fiil `3MS`)"
            if (s, a) == (34, 11):
                return "Halkaların aralığını ve dengesini tam ölçüsünde ayarla (`وَقَدِّرْ`, II. bab emir `2MS`)"
            if '3MP' in features:
                return "Ölçüsünü gümüş kapta tam ayarladılar (`قَدَّرُوهَا`, II. bab mâzî `3MP`)"
            if '3MS' in features and 'IMPF' in features:
                return "Ölçüsünü dengeli biçimde ayarlar (`يُقَدِّرُ`, II. bab muzâri `3MS`)"
            if '1P' in features:
                return "Ölçüsünü, menzilini veya akıbetini hesaplayıp belirledik (`قَدَّرْنَا`, II. bab mâzî `1P`)"
            return "Ölçülü biçti, yörünge/kapsam ve orantı belirledi (`قَدَّرَ`, II. bab mâzî `3MS`)"
        if lemma == 'qadara':
            if (s, a) in ((6, 91), (22, 74), (39, 67)):
                return "Kıymetini, ölçüsünü ve yüceliğini hakkıyla takdir ettiler (`قَدَرُوا۟`, I. bab mâzî `3MP`)"
            if (s, a) in ((13, 26), (17, 30), (28, 82), (29, 62), (30, 37), (34, 36), (34, 39), (39, 52), (42, 12), (65, 7), (89, 16)):
                return "Ölçüyü daraltır, rızkı belli bir sınıra kısar (`يَقْدِرُ / قُدِرَ / فَقَدَرَ`, I. bab `3MS`)"
            if (s, a) == (21, 87):
                return "Kendisine darlık ve sıkıştırma ölçüsü uygulamayacağımızı sandı (`نَّقْدِرَ`, I. bab mansûb muzâri `1P`)"
            if (s, a) == (54, 12):
                return "Önceden ölçüsü ve vakti belirlenmişti (`قُدِرَ`, I. bab meçhul mâzî `3MS`)"
            return "Ölçüsüne güç yetirebilir / hâkimiyet kurabilir (`يَقْدِرُ / تَقْدِرُوا۟ / فَقَدَرْنَا`, I. bab fiil)"
        if lemma == 'qadiyr':
            if (s, a) == (30, 54):
                return "Her aşamayı ölçüsüyle kuran mutlak kudret sahibi (`ٱلْقَدِيرُ`, marife `فَعِيل` sıfat merfû)"
            if 'ACC' in features:
                return "Her şeye gücü ve kapasitesi eksiksiz yeten (`قَدِيرًا`, `فَعِيل` sıfat mansûb)"
            return "Her şeye karşı kusursuz ölçü ve tam güç sahibi olan (`قَدِيرٌ`, `فَعِيل` sıfat merfû)"

    if root_ar == 'ن-ذ-ر':
        if lemma == 'nu*or':
            return "Her türlü bahaneyi kesen kesin uyarı ve hatırlatma olarak (`نُذْرًا`, masdar-isim mansûb)"
        if lemma == 'nu*uwr':
            return "Kendi üzerlerine aldıkları bağlayıcı sorumluluk adakları (`نُذُورَهُمْ`, kırık çoğul mansûb)"
        if lemma == 'n~a*or':
            return "Kişinin gönüllü olarak üstlendiği bağlayıcı adak ve sorumluluk (`نَّذْرٍ / بِٱلنَّذْرِ`, isim mecrûr)"
        if lemma == 'na*aro':
            if 'PASS' in features:
                return "Kendilerine uyarı ulaştırılıp ikaz edilirler (`يُنذَرُونَ`, meçhul muzâri `3MP`)"
            if '2MP' in features:
                return "Bağlayıcı bir adak olarak üstlendiniz (`نَذَرْتُم`, I. bab mâzî `2MP`)"
            return "Gönüllü bir adakla kendimi veya emaneti bağlayıp adadım (`نَذَرْتُ`, I. bab mâzî `1S`)"
        if lemma == 'mun*ariyn':
            return "Önceden açıkça uyarılıp tehlikeden haberdar edilmiş olanlar (`ٱلْمُنذَرِينَ`, IV. bab ism-i mef'ûl mecrûr)"
        if lemma == 'mun*ir':
            if 'MP|ACC' in features:
                return "Tehlikeyi önceden haber verip uyaran elçiler olarak (`مُنذِرِينَ`, IV. bab ism-i fâil mansûb)"
            if 'MP|GEN' in features:
                return "Önceden uyaranların safından (`ٱلْمُنذِرِينَ`, IV. bab ism-i fâil mecrûr)"
            if 'MP|NOM' in features:
                return "Önceden tehlikeyi duyurup uyaranlar (`مُنذِرُونَ`, IV. bab ism-i fâil merfû)"
            if 'INDEF' not in features:
                return "Yaklaşan hesap tehlikesinin uyarıcısı (`مُنذِرُ`, IV. bab marife/muzâf ism-i fâil merfû)"
            return "Açıkça uyaran, tehlikeyi haber veren bir uyarıcı (`مُنذِرٌ`, IV. bab nekre ism-i fâil merfû)"
        if lemma == '>an*ara':
            if 'PASS' in features:
                return "Önceden kendilerine uyarı yapılmış (`أُنذِرَ / أُنذِرُوا۟ / يُنذَرُوا۟`, IV. bab meçhul)"
            if 'IMPV' in features:
                return "Yaklaşan sonuca karşı uyar ve uyandır (`أَنذِرْ / فَأَنذِرْ / أَنذِرُوا۟`, IV. bab emir)"
            if 'JUS' in features:
                return "Uyarmasan da (`تُنذِرْهُمْ`, IV. bab meczûm muzâri)"
            if 'SUBJ' in features:
                return "Önceden uyarmak ve ikaz etmek için (`لِتُنذِرَ / لِيُنذِرَ`, IV. bab mansûb muzâri)"
            if '1S' in features:
                return "Ben sizi açıkça uyarıyorum / uyardım (`أُنذِرُكُم / أَنذَرْتُكُم`, IV. bab `1S`)"
            if '1P' in features:
                return "Biz sizi kesinlikle uyardık (`أَنذَرْنَٰكُم`, IV. bab `1P`)"
            if '3MS' in features and 'PERF' in features:
                return "Önceden haber verip uyardı (`أَنذَرَ`, IV. bab mâzî `3MS`)"
            return "Tehlikeye karşı önceden uyarır / uyardın (`ءَأَنذَرْتَهُمْ / يُنذِرُ / يُنذِرُونَ`, IV. bab fiil)"
        if lemma == 'na*iyr':
            if 'MP|GEN' in features:
                return "Önceden gönderilen uyarıcılar ve uyarılar (`ٱلنُّذُرِ / بِٱلنُّذُرِ`, kırık çoğul mecrûr)"
            if 'MP|NOM' in features:
                return "Gönderilen uyarıcılar ve uyarılar (`ٱلنُّذُرُ`, kırık çoğul merfû)"
            if (s, a) in ((54, 16), (54, 18), (54, 21), (54, 30), (54, 37), (54, 39), (67, 17)):
                return "Benim önceden yaptığım uyarı (`وَنُذُرِ / نَذِيرِ`, mütekellim yâsı düşmüş uyarı masdarı)"
            if 'M|NOM' in features:
                return "O beklenen gerçek uyarıcı (`ٱلنَّذِيرُ`, marife isim merfû)"
            if 'ACC' in features:
                return "Bir uyarıcı ve tehlike habercisi olarak (`نَذِيرًا / وَنَذِيرًا`, nekre mansûb)"
            if 'GEN' in features:
                return "Bir uyarıcı (`نَذِيرٍ`, nekre mecrûr)"
            return "Açıkça uyaran, tehlikeyi haber veren bir uyarıcı (`نَذِيرٌ / وَنَذِيرٌ`, nekre merfû)"

    if root_ar == 'ج-م-ع':
        if lemma == 'jumuEap':
            return "Topluluğun bir araya gelme günü (`ٱلْجُمُعَةِ`, özel isim mecrûr)"
        if lemma == 'm~ujotamiEuwn':
            return "Bir yerde toplanıp bir araya gelenler (`مُّجْتَمِعُونَ`, VIII. bab ism-i fâil çoğul merfû)"
        if lemma == 'majomaE':
            return "İki akıntının/denizin buluştuğu kavuşma yeri (`مَجْمَعَ`, `مَفْعَل` mekân ismi mansûb)"
        if lemma == '{jotamaEu':
            return "Kendi iradeleriyle bir araya gelip güç birliği yapsalar (`ٱجْتَمَعَتِ / ٱجْتَمَعُوا۟`, VIII. bab mâzî)"
        if lemma == 'm~ajomuwE':
            if 'MP' in features:
                return "Kesinlikle bir araya toplanacak olanlar (`لَمَجْمُوعُونَ`, I. bab ism-i mef'ûl çoğul merfû)"
            return "Bütün insanların bir araya toplandığı (`مَّجْمُوعٌ`, I. bab ism-i mef'ûl merfû)"
        if lemma == 'jaAmiE':
            if 'GEN' in features:
                return "Toplumu ilgilendiren ortak ve toplayıcı (`جَامِعٍ`, I. bab sıfat-ism-i fâil mecrûr)"
            return "Bütün insanları veya gerçeği örtenleri mutlaka bir araya toplayacak olan (`جَامِعُ`, I. bab ism-i fâil merfû)"
        if lemma == '>ajomaEu':
            if 'IMPV' in features:
                return "Kararınızı ve planınızı tek noktada kesinleştirin (`فَأَجْمِعُوا۟`, IV. bab emir `2MP`)"
            return "Tek bir ortak kararda kararlılıkla birleştiler (`أَجْمَعُوٓا۟ / وَأَجْمَعُوٓا۟`, IV. bab mâzî `3MP`)"
        if lemma == 'jamoE':
            if 'MD' in features:
                return "Karşı karşıya gelen iki büyük topluluk/ordu (`ٱلْجَمْعَانِ`, tesniye merfû)"
            if (s, a) == (75, 17):
                return "Vahiy metninin eksiksiz derlenip toplanması (`جَمْعَهُۥ`, masdar mansûb)"
            if 'GEN' in features:
                return "Büyük toplanmanın / bir araya getirilişin (`ٱلْجَمْعِ / جَمْعِهِمْ`, isim-masdar mecrûr)"
            if 'NOM' in features:
                return "O kalabalık topluluk / birikmiş birlik (`ٱلْجَمْعُ / جَمْعُكُمْ`, isim merfû)"
            return "Toplu hâlde, yığınla ve bütün olarak (`جَمْعًا`, masdar/hal mansûb)"
        if lemma == 'jamaEa':
            if 'PASS' in features:
                return "Bir araya getirildi / kavuşturuldu (`فَجُمِعَ / وَجُمِعَ`, I. bab meçhul mâzî `3MS`)"
            if (s, a) in ((3, 157), (10, 58), (43, 32), (70, 18), (104, 2)):
                return "Mal ve serveti hırsla biriktirip yığar / yığdı (`جَمَعَ / يَجْمَعُونَ`, I. bab fiil)"
            if '1P' in features:
                return "Hepsini bir araya getirip toplayalım (`جَمَعْنَٰهُمْ / نَّجْمَعَ / جَمَعْنَٰكُمْ`, I. bab `1P`)"
            if '2MP' in features:
                return "İkisini bir nikâhta bir araya getiresiniz (`تَجْمَعُوا۟`, I. bab mansûb muzâri `2MP`)"
            if '3MP' in features:
                return "Güçlerini bir araya getirdiler (`جَمَعُوا۟`, I. bab mâzî `3MP`)"
            return "Bütün insanları veya parçaları tek yerde bir araya toplar / topladı (`جَمَعَ / يَجْمَعُ / لَيَجْمَعَنَّكُمْ`, I. bab `3MS`)"
        if lemma == '>ajomaEiyn':
            if 'NOM' in features:
                return "İstisnasız tamamı, hep birlikte (`أَجْمَعُونَ`, cem-i müzekker mânevî tevkîd merfû)"
            return "Tek kişi kalmamacasına istisnasız tamamını / tamamının (`أَجْمَعِينَ`, cem-i müzekker mânevî tevkîd)"
        if lemma == 'jamiyE':
            if 'NOM' in features:
                return "Topyekûn bir arada hazır bulunanlar / dayanışan topluluk (`جَمِيعٌ / لَجَمِيعٌ`, `فَعِيل` sıfat merfû)"
            return "Hep birlikte, topluca ve istisnasız bütünüyle (`جَمِيعًا`, hal/zarf mansûb)"

    if root_ar == 'ن-ظ-ر':
        if lemma == 'naZar':
            return "Korku ve dehşet dolu bakış (`نَظَرَ`, `فَعَل` masdar-isim mansûb)"
        if lemma == 'naZorap':
            return "Tek bir defa göz atış / bir bakış (`نَظْرَةً`, `فَعْلَة` merre ismi mansûb)"
        if lemma == 'naZirap':
            return "Eli genişleyinceye dek borçluya süre ve mühlet tanıma (`فَنَظِرَةٌ`, `فَعِلَة` isim merfû)"
        if lemma == 'naAZirap':
            if (s, a) == (27, 35):
                return "Elçilerin neyle döneceğini gözleyip bekleyen (`فَنَاظِرَةٌۢ`, dişil ism-i fâil merfû)"
            return "Rabbine sevgi ve umutla yönelip bakan (`نَاظِرَةٌ`, dişil ism-i fâil merfû)"
        if lemma == 'na`Ziriyn':
            if (s, a) == (33, 53):
                return "Yemeğin pişmesini bekleyip gözleyenler olmaksızın (`نَٰظِرِينَ`, I. bab ism-i fâil çoğul mecrûr)"
            return "Gözleriyle seyredip bakanlar (`ٱلنَّٰظِرِينَ / لِلنَّٰظِرِينَ`, I. bab ism-i fâil çoğul)"
        if lemma == 'munZaruwn':
            if 'NOM' in features:
                return "Süre ve mühlet verilip ertelenenler (`مُنظَرُونَ`, IV. bab ism-i mef'ûl merfû)"
            return "Kendilerine erteleme ve süre tanınanlar (`مُّنظَرِينَ / ٱلْمُنظَرِينَ`, IV. bab ism-i mef'ûl)"
        if lemma == 'muntaZiruwn':
            return "Sonucu dikkatle gözleyip bekleyenler (`مُنتَظِرُونَ / ٱلْمُنتَظِرِينَ`, VIII. bab ism-i fâil çoğul)"
        if lemma == 'yantaZiru':
            if 'IMPV' in features:
                return "Gözünüzü dikip sonucu bekleyin / gözetle (`ٱنتَظِرُوٓا۟ / فَٱنتَظِرُوٓا۟ / وَٱنتَظِرْ`, VIII. bab emir)"
            return "Sonucun gelmesini gözleyip bekliyor / bekliyorlar (`يَنتَظِرُ / يَنتَظِرُونَ`, VIII. bab muzâri)"
        if lemma == 'yunZaru':
            if 'IMPV' in features:
                return "Bana süre ve mühlet tanı (`أَنظِرْنِىٓ / فَأَنظِرْنِىٓ`, IV. bab emir `2MS`)"
            if 'JUS' in features:
                return "Bana hiç göz açtırmayıp süre tanımayın (`تُنظِرُونِ`, IV. bab meczûm muzâri `2MP` — son `-î` düşmüş)"
            return "Kendilerine süre ve ek mühlet tanınır (`يُنظَرُونَ`, IV. bab meçhul muzâri `3MP`)"
        if lemma == 'n~aZara':
            if (s, a) in ((2, 210), (6, 158), (7, 53), (16, 33), (35, 43), (36, 49), (38, 15), (43, 66), (47, 18), (57, 13)):
                return "Gözlerini dikip gelmesini bekliyor / bekler (`يَنظُرُ / يَنظُرُونَ / ٱنظُرُونَا`, I. bab 'beklemek' kullanımı)"
            if (s, a) in ((2, 104), (4, 46)):
                return "Bizi gözet, hâlimize ve ihtiyacımıza bak (`ٱنظُرْنَا / وَٱنظُرْنَا`, I. bab emir `2MS`)"
            if 'IMPV' in features:
                return "Dikkatle bak, incele ve ibretle değerlendir (`ٱنظُرْ / فَٱنظُرُوا۟ / فَٱنظُرِى`, I. bab emir)"
            if 'JUS' in features:
                return "Bakıp görsün / bakayım / incelesin (`فَلْيَنظُرْ / وَلْتَنظُرْ / أَنظُرْ / نَنظُرْ`, I. bab meczûm muzâri)"
            if 'SUBJ' in features:
                return "Bakıp ibret alsınlar / incelesinler diye (`فَيَنظُرُوا۟ / لِيَنظُرَ / لِنَنظُرَ`, I. bab mansûb muzâri)"
            if 'PERF' in features:
                return "Dönüp dikkatle baktı / süzdü (`نَظَرَ / فَنَظَرَ`, I. bab mâzî `3MS`)"
            return "Gözleriyle bakar / canlı tanık olur (`يَنظُرُونَ / تَنظُرُونَ / سَنَنظُرُ`, I. bab muzâri)"

    if root_ar == 'س-أ-ل':
        if lemma == 'su&aAl':
            return "Haksız yere katılmasını isteyip talep etmesi (`بِسُؤَالِ`, `فُعَال` masdarı mecrûr)"
        if lemma == 'su&ol':
            return "İsteyip talep ettiğin her arzun (`سُؤْلَكَ`, `فُعْل` masdar-isim mansûb)"
        if lemma == 'maso_#uwl':
            if 'MP' in features:
                return "Hesaba çekilip sorgulanacak olanlar (`مَّسْـُٔولُونَ`, I. bab ism-i mef'ûl çoğul merfû)"
            return "Kesinlikle sorulup hesabı aranacak sorumluluk (`مَسْـُٔولًا / مَّسْـُٔولًا`, I. bab ism-i mef'ûl mansûb)"
        if lemma == 'saA^}il':
            if (s, a) in ((12, 7), (70, 1)):
                return "Merakla araştırıp soran / soruyu yönelten (`لِّلسَّآئِلِينَ / سَآئِلٌۢ`, I. bab ism-i fâil)"
            return "Bilgi veya ihtiyaç talep edip yardım isteyenler (`ٱلسَّآئِلَ / لِّلسَّآئِلِ / وَٱلسَّآئِلِينَ`, I. bab ism-i fâil)"
        if lemma == "yatasaA^'alu":
            if (s, a) == (4, 1):
                return "Birbirinizden hak ve yardım istemekte kullandığınız (`تَسَآءَلُونَ`, VI. bab muzâri `2MP`)"
            return "Birbirlerine sorup duruyorlar / karşılıklı soruşurlar (`يَتَسَآءَلُونَ / لِيَتَسَآءَلُوا۟`, VI. bab muzâri `3MP`)"
        if lemma == 'sa>ala':
            if 'PASS' in features:
                if '3FS' in features:
                    return "Hangi suçla öldürüldüğü sorulduğunda (`سُئِلَتْ`, I. bab meçhul mâzî `3FS`)"
                if (s, a) in ((2, 108), (33, 14)):
                    return "Kendilerinden istendi / kendisine sorulduğu gibi (`سُئِلَ / سُئِلُوا۟`, I. bab meçhul mâzî)"
                return "Yaptıklarınızdan / yapıp ettiklerinden kesinlikle sorguya çekilirsiniz (`تُسْـَٔلُونَ / يُسْـَٔلُ / لَتُسْـَٔلُنَّ`, I. bab meçhul)"
            if 'IMPV' in features:
                return "Sorup öğren veya ihtiyacını iste (`سَلْ / فَسْـَٔلْ / فَسْـَٔلُوٓا۟ / وَسْـَٔلُوا۟`, I. bab emir)"
            if '1S' in features:
                return "Sizden istemiyorum / size sordum (`أَسْـَٔلُكُم / سَأَلْتُكُم`, I. bab `1S`)"
            if '1P' in features:
                return "Hepsini mutlaka sorguya çekip soracağız (`فَلَنَسْـَٔلَنَّ / لَنَسْـَٔلَنَّهُمْ`, I. bab `1P`)"
            if '2MS' in features:
                return "Sorma veya istedin (`تَسْـَٔلْنِى / سَأَلْتَ`, I. bab `2MS`)"
            if '2MP' in features:
                return "Sorarsınız / istersiniz / sordunuz (`تَسْـَٔلُوا۟ / سَأَلْتُم`, I. bab `2MP`)"
            if 'PERF' in features:
                return "Sordu veya açıkça istedi (`سَأَلَ / سَأَلُوا۟ / سَأَلْتَهُم`, I. bab mâzî)"
            return "Sana soruyorlar / istiyor / haklarını sorarlar (`يَسْـَٔلُونَكَ / يَسْـَٔلُ`, I. bab muzâri)"

    if root_ar == 'ط-و-ع':
        if lemma == 'm~uTaAE':
            return "Orada sözüne gönülden uyulan, itibarlı (`مُّطَاعٍ`, IV. bab ism-i mef'ûl mecrûr)"
        if lemma == 'TaA^}iEiyn':
            return "Zorlanmaksızın gönüllüce uyum içinde olanlar (`طَآئِعِينَ`, I. bab ism-i fâil çoğul mansûb)"
        if lemma == 'muT~aw~iEiyn':
            return "Gönlünden koparak bağışta bulunan gönüllüler (`ٱلْمُطَّوِّعِينَ`, V. bab idğamlı ism-i fâil mansûb)"
        if lemma == 'Taw~aEato':
            return "Kötülüğü ona kolay ve cazip gösterip uydurdu (`فَطَوَّعَتْ`, II. bab mâzî `3FS`)"
        if lemma == 'yuTaAEu':
            return "Sözü ve yetkisi gönülden dinlenip uyulur (`لِيُطَاعَ / يُطَاعُ`, IV. bab meçhul muzâri `3MS`)"
        if lemma == 'taTaw~aEa':
            return "Zorunluluk ötesinde gönlünden koparak iyilik işledi (`تَطَوَّعَ`, V. bab mâzî `3MS`)"
        if lemma == 'TaAEap':
            return "Sözde değil eylemde belli olan bilinçli uyum (`طَاعَةٌ`, masdar-isim merfû)"
        if lemma == 'TawoE':
            return "Zorlamasız olarak, isteyerek ve gönüllüce (`طَوْعًا`, masdar-hal mansûb — `كَرْهًا` zıddı)"
        if lemma == '{sotaTaAEa':
            if (s, a) == (18, 97):
                return "Aşmaya veya delmeye imkân bulup güç yetiremediler (`ٱسْطَٰعُوٓا۟ / ٱسْتَطَٰعُوا۟`, X. bab mâzî `3MP`)"
            if 'PERF' in features:
                return "İmkân ve kapasite bularak güç yetirebildi / yetirebildiniz (`ٱسْتَطَعْتُم / ٱسْتَطَاعَ`, X. bab mâzî)"
            return "İmkânı el verir, yapmaya güç yetirebilir (`يَسْتَطِيعُونَ / تَسْتَطِع / تَسْطِع`, X. bab muzâri)"
        if lemma == '>aTaAEa':
            if 'IMPV' in features:
                return "Bilinçle ve gönüllüce uyun (`أَطِيعُوا۟ / وَأَطِيعُونِ / وَأَطِعْنَ`, IV. bab emir)"
            if '1P' in features:
                return "Uyup itaat ettik / uyarız (`أَطَعْنَا / نُطِيعُ`, IV. bab `1P`)"
            if 'JUS' in features:
                return "Eğer gönülden uyarsa / uymayın (`يُطِعِ / تُطِعْ / تُطِعْهُمَا`, IV. bab meczûm)"
            if 'SUBJ' in features:
                return "Bilinçli biçimde uyasınız diye (`تُطِيعُوا۟ / تُطِيعُوهُ`, IV. bab mansûb)"
            if 'PERF' in features:
                return "Gönüllü uyum gösterip uydu (`أَطَاعَ / أَطَعْتُمُوهُمْ`, IV. bab mâzî)"
            return "Sizi dinleyip uyuyorlar / uyacağız (`يُطِيعُونَ / سَنُطِيعُكُمْ`, IV. bab muzâri)"

    if root_ar == 'ع-ظ-م':
        if lemma == 'yuEoZimo':
            return "Karşılık ve ödülünü büyütüp katlar (`وَيُعْظِمْ`, IV. bab meczûm muzâri `3MS`)"
        if lemma == 'yuEaZ~imo':
            return "Saygı duyup değerini yüceltirse (`يُعَظِّمْ`, II. bab meczûm muzâri `3MS`)"
        if lemma == 'EaZom':
            if 'NOM' in features:
                return "İskeletin taşıyıcı kemik yapısı (`ٱلْعَظْمُ`, tekil isim merfû)"
            return "Kemiğe bitişen / kemik (`بِعَظْمٍ`, tekil isim mecrûr)"
        if lemma == '>aEoZam':
            if 'ACC' in features:
                return "Değer ve karşılık bakımından daha büyük (`وَأَعْظَمَ`, ism-i tafdîl mansûb)"
            return "Derece ve konum bakımından çok daha büyük (`أَعْظَمُ`, ism-i tafdîl merfû)"
        if lemma == 'EaZiym':
            if 'MP' in features:
                if 'GEN' in features:
                    return "Çürümüş iskeletin kemikleri (`ٱلْعِظَامِ`, `عَظْم` kırık çoğulu mecrûr)"
                return "Sert ve dayanıklı kemikler (`عِظَٰمًا / ٱلْعِظَٰمَ / عِظَامَهُۥ`, `عَظْم` kırık çoğulu mansûb)"
            if 'INDEF' not in features:
                if 'NOM' in features:
                    return "Sarsılmaz büyüklük ve yücelik sahibi (`ٱلْعَظِيمُ`, marife `فَعِيل` sıfat merfû)"
                if 'ACC' in features:
                    return "Eşsiz büyüklükteki yüce (`ٱلْعَظِيمَ`, marife `فَعِيل` sıfat mansûb)"
                return "Sarsılmaz büyüklüğün sahibi (`ٱلْعَظِيمِ`, marife `فَعِيل` sıfat mecrûr)"
            if 'ACC' in features:
                return "Çok büyük, ağır veya yüksek kıymetli (`عَظِيمًا`, nekre `فَعِيل` sıfat/isim mansûb)"
            if 'GEN' in features:
                return "Sarsılmaz, muazzam ve yüce (`عَظِيمٍ`, nekre `فَعِيل` sıfat mecrûr)"
            return "Çok büyük, sarsılmaz ve muazzam (`عَظِيمٌ`, nekre `فَعِيل` sıfat/isim merfû)"

    if root_ar == 'خ-ل-ف':
        if lemma == 'm~usotaxolafiyn':
            return "Kendilerine emanet ve yönetim devredilen geçici temsilciler (`مُّسْتَخْلَفِينَ`, X. bab ism-i mef'ûl mansûb)"
        if lemma == 'xilofap':
            return "Biri giderken diğeri arkasından gelip yerini alan dönüşümlü düzen (`خِلْفَةً`, isim mansûb)"
        if lemma == 'muxolif':
            return "Verdiği sözden dönüp aksini yapan (`مُخْلِفَ`, IV. bab ism-i fâil mansûb)"
        if lemma == 'yataxal~afu':
            return "Sorumluluktan kaçıp geride kalsınlar (`يَتَخَلَّفُوا۟`, V. bab mansûb muzâri `3MP`)"
        if lemma == 'xul~ifu':
            return "Hakemlik süreci için kararsızca geride bırakıldılar (`خُلِّفُوا۟`, II. bab meçhul mâzî `3MP`)"
        if lemma == 'xa`lifiyn':
            return "Göreve çıkmayıp geride oturanlar (`ٱلْخَٰلِفِينَ`, I. bab ism-i fâil çoğul mecrûr)"
        if lemma == 'yuxaAlifu':
            if '1S' in features:
                return "Size ters düşerek yasağın arkasına geçip çiğneyeyim (`أُخَالِفَكُمْ`, III. bab mansûb `1S`)"
            return "Buyruğun aksine gidip muhalefet edenler (`يُخَالِفُونَ`, III. bab muzâri `3MP`)"
        if lemma == 'xawaAlif':
            return "Evde oturup geride kalan kadın/çekinen kimseler (`ٱلْخَوَالِفِ`, kırık çoğul mecrûr)"
        if lemma == 'muxal~afuwn':
            return "Görev dışı bırakılıp geride kalanlar (`ٱلْمُخَلَّفُونَ / لِّلْمُخَلَّفِينَ`, II. bab ism-i mef'ûl)"
        if lemma == 'xalafa':
            if 'IMPV' in features:
                return "Yokluğumda ardımdan yerime geçip gözet (`ٱخْلُفْنِى`, I. bab emir `2MS`)"
            if '2MP' in features:
                return "Ardımdan yerimi çok kötü temsil ettiniz (`خَلَفْتُمُونِى`, I. bab mâzî `2MP`)"
            if 'IMPF' in features:
                return "Sizin yerinize geçip ardıl olurlar (`يَخْلُفُونَ`, I. bab muzâri `3MP`)"
            return "Onların ardından yeni bir nesil geldi (`فَخَلَفَ`, I. bab mâzî `3MS`)"
        if lemma == '{sotaxolafa':
            if 'PERF' in features:
                return "Öncekilerin ardından yerlerine geçirip emanet sahibi kıldı (`ٱسْتَخْلَفَ`, X. bab mâzî `3MS`)"
            return "Yerlerine yenilerini geçirir ve emanetçi kılar (`يَسْتَخْلِفُ / لَيَسْتَخْلِفَنَّهُمْ`, X. bab muzâri `3MS`)"
        if lemma == 'xila`f':
            if (s, a) in ((5, 33), (7, 124), (20, 71), (26, 49)):
                return "Sağlı-sollu ters ve çapraz yönlerden (`خِلَٰفٍ`, isim mecrûr)"
            return "Arkasında kalarak / ardın sıra yokluğunda (`خِلَٰفَ / خِلَٰفَكَ`, zarf-isim mansûb)"
        if lemma == '{xotila`f':
            if (s, a) == (4, 82):
                return "İç çelişki, tutarsızlık ve farklılık (`ٱخْتِلَٰفًا`, VIII. bab masdar mansûb)"
            if (s, a) == (30, 22):
                return "Dillerinizin ve renklerinizin zengin çeşitliliği (`وَٱخْتِلَٰفُ`, VIII. bab masdar merfû)"
            return "Gece ile gündüzün birbirini izleyerek dönüşümü (`ٱخْتِلَٰفِ / ٱخْتِلَٰفُ`, VIII. bab masdar)"
        if lemma == 'xaliyfap':
            if 'MP' in features:
                return "Öncekilerin ardından yeryüzünü ve sorumluluğu devralan nesiller (`خَلَٰٓئِفَ / خُلَفَآءَ`, kırık çoğul mansûb)"
            return "Yeryüzünde sorumluluk ve karar emanetini üstlenen temsilci (`خَلِيفَةً`, tekil isim mansûb)"
        if lemma == 'm~uxotalif':
            if (s, a) in ((11, 118), (51, 8), (78, 3)):
                return "Ayrı görüşlere bölünmüş ve çekişme hâlinde (`مُخْتَلِفِينَ / مُّخْتَلِفٍ / مُخْتَلِفُونَ`, VIII. bab ism-i fâil)"
            return "Renk, tat ve tür bakımından birbirinden farklı çeşitli (`مُّخْتَلِفًا / مُّخْتَلِفٌ`, VIII. bab ism-i fâil)"
        if lemma == '>axolafu':
            if (s, a) == (34, 39):
                return "Paylaşılan malın arkasına geçip yerine yenisini verir (`يُخْلِفُهُۥ`, IV. bab muzâri `3MS`)"
            if 'PASS' in features:
                return "Asla bozulmayacak / cayılmayacak olan (`لَّن تُخْلَفَهُۥ`, IV. bab meçhul muzâri)"
            return "Verdiği sözden ve vaatten caydı / caymaz (`يُخْلِفُ / أَخْلَفْنَا / فَأَخْلَفْتُم`, IV. bab fiil)"
        if lemma == 'xalof':
            if (s, a) in ((7, 169), (19, 59)):
                return "Emaneti zayi eden yozlaşmış arka nesil (`خَلْفٌ`, cezimli lâm merfû)"
            return "Arka taraf / kendilerinden sonra gelecek olanlar (`خَلْفَهُمْ / خَلْفِهِۦ / خَلْفَكَ`, mekân-zaman ismi)"
        if lemma == '{xotalafa':
            if 'PASS' in features:
                return "Onda görüş ayrılığına düşüldü (`فَٱخْتُلِفَ`, VIII. bab meçhul mâzî `3MS`)"
            if 'PERF' in features:
                return "Bilgi geldikten sonra ayrışıp anlaşmazlığa düştüler (`ٱخْتَلَفُوا۟ / ٱخْتَلَفَ / ٱخْتَلَفَا`, VIII. bab mâzî)"
            return "Üzerinde ayrışıp farklı yönlere çekişirler (`يَخْتَلِفُونَ / تَخْتَلِفُونَ`, VIII. bab muzâri)"

    if root_ar == 'أ-ه-ل':
        if (s, a) in ((4, 58), (48, 26), (74, 56)):
            return "Emanete, ilkeye veya yüce niteliğe tamamen lâyık ve ehil olanlar (`أَهْلَهَا / أَهْلُ`, muzâf isim)"
        if (s, a) in ((5, 89), (39, 15), (42, 45), (48, 11), (48, 12), (66, 6)):
            return "Bakımından sorumlu olunan aileler ve yakınlar (`أَهْلُونَا / أَهْلِيكُمْ / أَهْلِيهِمْ`, `أَهْلُون` müzekker sâlim çoğul)"
        if 'NOM' in features:
            return "Evin, şehrin veya kitabın mensubu ve halkı (`أَهْلُ / أَهْلُهُۥ / وَأَهْلُهَا`, muzâf isim merfû)"
        if 'GEN' in features:
            return "Ailesinin, halkının veya belirli niteliğin mensubuna/mensubundan (`أَهْلِ / أَهْلِهِۦ / بِأَهْلِكَ`, muzâf isim mecrûr)"
        return "Aileyi, ev halkını, şehir sakinlerini veya kitap ehlini (`أَهْلَ / يَٰٓأَهْلَ / أَهْلَهَا / وَأَهْلَهُۥ`, muzâf isim mansûb)"

    if root_ar == 'د-خ-ل':
        if lemma == 'mud~axal':
            return "İçine girilip saklanılacak yer veya yeraltı kovuğu (`مُدَّخَلًا`, VIII. bab ism-i mef'ûl/mekân mansûb `t→d` idğamlı)"
        if lemma == 'daxal':
            return "Anlaşmaların içine sokulan gizli hile, tuzak ve iç çürüme (`دَخَلًۢا`, isim mansûb)"
        if lemma == 'm~udoxal':
            return "İçeri sokulan/girilen yer ve hal (`مُدْخَلَ / مُّدْخَلًا`, IV. bab mimli masdar / mekân ismi mansûb)"
        if lemma == 'da`xiluwn':
            if 'GEN' in features:
                return "İçeri giren kimselerle birlikte olanlar (`ٱلدَّٰخِلِينَ`, I. bab ism-i fâil çoğul mecrûr)"
            return "Oraya kesinlikle giren kimseler (`دَٰخِلُونَ`, I. bab ism-i fâil çoğul merfû)"
        if lemma == '>udoxila':
            if 'PASS' in features:
                if 'IMPF' in features:
                    return "İçeri konulur / sokulur (`يُدْخَلَ`, IV. bab edilgen muzâri mansûb `3MS`)"
                return "İçeri konuldu / sokuldular (`أُدْخِلَ / فَأُدْخِلُوا۟`, IV. bab edilgen mâzî)"
            if 'IMPV' in features:
                if '2MP' in features:
                    return "İçeri sokun / atın (`أَدْخِلُوٓا۟`, IV. bab emir `2MP`)"
                return "Beni/onları içeri al, yerleştir (`أَدْخِلْنِى / وَأَدْخِلْهُمْ / أَدْخِلْ`, IV. bab emir `2MS`)"
            if 'PERF' in features:
                return "Onları içeri aldık / yerleştirdik (`فَأَدْخَلْنَٰهُمْ`, IV. bab mâzî `1P`)"
            if '2MS' in features:
                return "Sen içeri sokarsın / atarsın (`تُدْخِلِ`, IV. bab muzâri `2MS`)"
            if '1S' in features:
                return "İçeri alırım / sokarım (`لَأُدْخِلَنَّكُمْ`, IV. bab tekitli muzâri `1S`)"
            return "İçeri alır / alırız / girdirecektir (`سَنُدْخِلُهُمْ / لَيُدْخِلَنَّهُمْ / يُدْخِلُ`, IV. bab muzâri)"
        if lemma == 'daxala':
            if 'PASS' in features:
                return "Üzerlerine şehrin içinden baskınla girilmiş olsa (`دُخِلَتْ`, I. bab edilgen mâzî `3FS`)"
            if 'IMPV' in features:
                if '2MD' in features:
                    return "İkiniz birlikte girin (`ٱدْخُلَا`, I. bab emir ikil `2MD`)"
                if '2FS' in features:
                    return "İçeri gir (`ٱدْخُلِى`, I. bab emir dişil `2FS`)"
                if '2MS' in features:
                    return "Gir! (`ٱدْخُلِ`, I. bab emir tekil `2MS`)"
                return "İçeri girin! (`ٱدْخُلُوا۟ / فَٱدْخُلُوا۟`, I. bab emir çoğul `2MP`)"
            if 'PERF' in features:
                return "İçeri girdi / girdiler / girdiniz (`دَخَلَ / دَخَلُوا۟ / دَخَلْتُم / دَخَلَتْ`, I. bab mâzî)"
            return "İçeri girer / girersiniz / girmeyin / girsinler (`يَدْخُلُ / تَدْخُلُوا۟ / لِيَدْخُلُوا۟`, I. bab muzâri)"

    if root_ar == 'خ-و-ف':
        if lemma == 'taxaw~uf':
            return "Uçlardan/kenarlardan azar azar kırpılıp eksiltilerek veya korku sarmalı içinde (`عَلَىٰ تَخَوُّفٍ`, V. bab masdar mecrûr)"
        if lemma == 'taxowiyf':
            return "Caydırıcı uyarı ve dehşetli korkutma amacıyla (`تَخْوِيفًا`, II. bab masdar mansûb)"
        if lemma == 'yuxaw~ifu':
            return "Gözdağı verip korkutuyor / korkutur (`يُخَوِّفُ / وَنُخَوِّفُهُمْ / وَيُخَوِّفُونَكَ`, II. bab muzâri)"
        if lemma == 'xiyfap':
            if 'GEN' in features:
                return "İçten ürpertisinin ve çekincesinin şiddetinden (`خِيفَتِهِۦ / كَخِيفَتِكُمْ`, fi'le kalıbı isim mecrûr)"
            return "İçinde beliren bir çekince ve ürperti (`خِيفَةً`, fi'le kalıbı `v→y` dönüşümlü isim mansûb)"
        if lemma == 'xaA^}if':
            if 'MP' in features:
                return "İçeri ancak korkuyla çekinerek girebilenler (`خَآئِفِينَ`, I. bab ism-i fâil çoğul mansûb)"
            return "Çevresini kollayarak ürküntü içinde (`خَآئِفًا`, I. bab ism-i fâil tekil mansûb)"
        if lemma == 'xawof':
            if (s, a) in ((7, 56), (13, 12), (30, 24), (32, 16)):
                return "Hem korku hem de umut besleyerek (`خَوْفًا وَطَمَعًا`, masdar-hal mansûb)"
            if 'GEN' in features:
                return "Tehlike ve korku hâlinden/ortamından (`ٱلْخَوْفِ / خَوْفٍۭ / خَوْفِهِمْ`, isim mecrûr)"
            if (s, a) == (33, 19):
                return "O gerçek savaş korkusu ve tehlikesi (`ٱلْخَوْفُ`, marife isim merfû)"
            return "Üzerlerinde hiçbir endişe ve korku (`لَا خَوْفٌ`, nekre isim merfû)"
        if lemma == 'xaAfa':
            if (s, a) == (26, 21):
                return "Sizden korkup çekindiğimde (`خِفْتُكُمْ`, I. bab ecvef vâvî mâzî `1S` malum; zahirî kesre sebebiyle `PASS` etiketlenmiştir)"
            if 'IMPV' in features:
                return "Yalnız Benden korkup çekinin (`وَخَافُونِ`, I. bab emir `2MP` + gizli `1S` zamiri)"
            if '2FS' in features:
                return "Başına bir şey gelmesinden korktuğunda / korkma! (`خِفْتِ / وَلَا تَخَافِى`, I. bab dişil çekim `2FS`)"
            if 'PERF' in features:
                return "Korktu / çekindiler / endişe ettiniz (`خَافَ / خِفْتُمْ / خَافَتْ`, I. bab ecvef mâzî)"
            return "Korkarım / korkarlar / korkma! / korkmayın! (`أَخَافُ / لَا تَخَفْ / يَخَافُونَ`, I. bab ecvef muzâri)"

    if root_ar == 'ر-ز-ق':
        if lemma == 'r~az~aAq':
            return "Sürekli ve sınırsız biçimde tüm varlıklara rızık ve geçim payı sağlayan (`ٱلرَّزَّاقُ`, fa'âl mübalağa sıfatı merfû)"
        if lemma == 'r~a`ziqiyn':
            if (s, a) == (15, 20):
                return "Siz onlara yaşam payı/rızık sağlayanlar değilsiniz (`بِرَٰزِقِينَ`, I. bab ism-i fâil çoğul mecrûr)"
            return "Rızık ve yaşam payı verenlerin en hayırlısı (`ٱلرَّٰزِقِينَ`, I. bab ism-i fâil çoğul mecrûr)"
        if lemma == 'rizoq':
            if 'NOM' in features:
                return "Yaşam payı, geçim tayını ve tahsisat (`رِزْقٌ / رِزْقُهَا / وَرِزْقُ`, isim merfû)"
            if 'GEN' in features:
                return "Geçim payının, rızkın veya tahsisatın (`ٱلرِّزْقِ / رِزْقٍ / رِزْقِهِمْ`, isim mecrûr)"
            return "Geçim payını, rızkı ve nasibi (`رِزْقًا / ٱلرِّزْقَ / رِزْقَكُمْ`, isim mansûb)"
        if lemma == 'razaqa':
            if 'PASS' in features:
                if '2MD' in features:
                    return "İkinize tayın olarak verilen rızık (`تُرْزَقَانِهِ`, I. bab edilgen muzâri ikil `2MD`)"
                if 'IMPF' in features:
                    return "Sürekli rızıklandırılıp yaşatılırlar (`يُرْزَقُونَ`, I. bab edilgen muzâri `3MP`)"
                return "Rızık ve nimetlerle beslendiklerinde / beslendik (`رُزِقُوا۟ / رُزِقْنَا`, I. bab edilgen mâzî)"
            if 'IMPV' in features:
                if '2MP' in features:
                    return "Ondan kendilerine geçim payı ayırıp verin (`وَٱرْزُقُوهُمْ / فَٱرْزُقُوهُم`, I. bab emir `2MP`)"
                return "Bizi/onları rızıklandır, geçim payı ver (`وَٱرْزُقْ / وَٱرْزُقْنَا / وَٱرْزُقْهُم`, I. bab emir `2MS`)"
            if 'PERF' in features:
                return "Size/onlara/bana rızık ve geçim payı verdik (`رَزَقْنَٰكُمْ / رَزَقْنَٰهُمْ / رَزَقَهُمُ`, I. bab mâzî)"
            return "Rızık ve geçim payı verir / veririz / rızıklandıracağız (`يَرْزُقُ / نَرْزُقُكَ / لَيَرْزُقَنَّهُمُ`, I. bab muzâri)"

    if root_ar == 'ب-ش-ر':
        if lemma == 'm~usotabo$irap':
            return "Sevinçten yüzünün derisi parıldayıp gülümseyen (`مُّسْتَبْشِرَةٌ`, X. bab dişil ism-i fâil merfû)"
        if lemma == '>abo$iru':
            return "Büyük sevinçle müjdelenin (`وَأَبْشِرُوا۟`, IV. bab emir `2MP`)"
        if lemma == 'muba$~ira`t':
            return "Yağmuru ve bereketi müjdeleyip getiren rüzgârlar (`مُبَشِّرَٰتٍ`, II. bab dişil çoğul ism-i fâil mansûb)"
        if lemma == 'bu$or':
            return "Rahmetin önünde müjde taşıyıcısı olarak gönderilen (`بُشْرًۢا`, çoğul-isim mansûb)"
        if lemma == 'ba`$iru':
            if 'IMPV' in features:
                return "Eşlerinizle ten tene fiziksel birliktelikte bulunun (`بَٰشِرُوهُنَّ`, III. bab emir `2MP`)"
            return "İtikafta iken eşlerinize cinsel anlamda yaklaşmayın (`تُبَٰشِرُوهُنَّ`, III. bab nehiy meczûm `2MP`)"
        if lemma == 'yasotabo$iru':
            if 'IMPV' in features:
                return "Yaptığınız bu kazançlı sözleşmeye sevinin / bayram edin (`فَٱسْتَبْشِرُوا۟`, X. bab emir `2MP`)"
            return "Sevinçle yüzleri parıldar / müjdelenirler (`يَسْتَبْشِرُونَ / وَيَسْتَبْشِرُونَ`, X. bab muzâri `3MP`)"
        if lemma == 'muba$~ir':
            if 'MP' in features:
                return "Sevindirici haber taşıyıcıları (`مُبَشِّرِينَ`, II. bab ism-i fâil çoğul mansûb)"
            return "Sevindirici haber veren (`مُبَشِّرًا / وَمُبَشِّرًا`, II. bab ism-i fâil tekil mansûb)"
        if lemma == 'ba$iyr':
            if 'GEN' in features:
                return "Sevindirici müjde getiren hiçbir kimse (`بَشِيرٍ`, fa'îl sıfatı mecrûr)"
            if 'NOM' in features:
                return "Müjde getirici (`ٱلْبَشِيرُ / وَبَشِيرٌ`, fa'îl sıfatı merfû)"
            return "Müjde getirici (`بَشِيرًا`, fa'îl sıfatı mansûb)"
        if lemma == 'bu$oraY`':
            if 'GEN' in features:
                return "Sevindirici müjdeli haberle (`بِالْبُشْرَىٰ`, fu'lâ ismi mecrûr)"
            if 'NOM' in features:
                return "Sevindirici müjde (`ٱلْبُشْرَىٰ / وَبُشْرَىٰ / بُشْرَاكُمُ`, fu'lâ ismi merfû)"
            return "İç ferahlatan müjde olarak (`بُشْرَىٰ / وَبُشْرَىٰ`, fu'lâ ismi mansûb)"
        if lemma == 'ba$ar':
            if 'MD' in features:
                return "Bizim gibi etten-deriden iki ölümlü insana (`لِبَشَرَيْنِ`, ikil isim mecrûr)"
            if (s, a) == (74, 29):
                return "İnsanların derisini/yüzünü kavurup değiştiren (`لِلْبَشَرِ`, mecrûr isim)"
            if 'GEN' in features:
                return "Ölümlü insanın / ten sahibi varlığın (`لِبَشَرٍ / ٱلْبَشَرِ`, tekil cins ismi mecrûr)"
            if 'ACC' in features:
                return "Düzgün görünümlü ölümlü bir insan (`بَشَرًا`, cins ismi mansûb)"
            return "Sizin gibi ölümlü insan (`بَشَرٌ`, cins ismi merfû)"
        if lemma == 'bu$~ira':
            if 'PASS' in features:
                return "Kendisine kız çocuğu haberi verildiğinde (`بُشِّرَ`, II. bab edilgen mâzî `3MS`)"
            if 'IMPV' in features:
                return "Müjdele / onlara acı sonucu bildir (`وَبَشِّرِ / فَبَشِّرْهُمْ / فَبَشِّرْ`, II. bab emir `2MS`)"
            if 'PERF' in features:
                return "Müjdeledik / müjdelediniz mi (`فَبَشَّرْنَٰهَا / بَشَّرْنَٰكُمْ / أَبَشَّرْتُمُونِى`, II. bab mâzî)"
            return "Müjdeler / haber veriyorsunuz (`يُبَشِّرُ / تُبَشِّرُونَ`, II. bab muzâri)"

    if root_ar == 'ي-د-ي':
        if (s, a) == (9, 29):
            return "Kendi elleriyle boyun eğip ödeme gücüyle (`عَن يَدٍ`, tekil müennes semâî isim mecrûr)"
        if (s, a) == (38, 45):
            return "Eylem gücü, irade ve kudret sahipleri (`ٱلْأَيْدِى`, kırık çoğul isim)"
        if (s, a) == (38, 75):
            return "Bizzat iki elimle / kendi özel kudret ve özenimle (`بِيَدَىَّ`, ikil isim mecrûr + `1S` iyelik)"
        if (s, a) == (111, 1):
            return "İki eli / tüm kurduğu gücü ve düzeni (`يَدَآ`, ikil müennes isim merfû)"
        if 'FP' in features:
            if 'GEN' in features:
                return "Ellerinin / önlerindeki zaman-mekânın (`بِأَيْدِيهِمْ / بَيْنَ أَيْدِيهِمْ`, kırık çoğul mecrûr)"
            if 'ACC' in features:
                return "Ellerini / önlerindeki durumları (`أَيْدِيَهُمْ / أَيْدِيكُمْ`, kırık çoğul mansûb)"
            return "Eller / elleri (`أَيْدِيهِمْ / أَيْدِيهِمَا`, kırık çoğul merfû)"
        if 'FD' in features:
            if 'NOM' in features:
                return "İki eli (`يَدَاهُ / يَدَاكَ`, ikil müennes isim merfû)"
            return "İki elin arası yani önü/öncesi veya iki eliyle (`بَيْنَ يَدَيْهِ / يَدَىْ`, ikil muzâf ilayh)"
        if 'NOM' in features:
            return "Eli / yetkisi ve kudreti (`يَدُ ٱللَّهِ`, tekil müennes isim merfû)"
        if 'GEN' in features:
            return "Elinde / tasarruf ve yetkisi altında (`بِيَدِهِۦ / بِيَدِكَ / بِيَدِ`, tekil isim mecrûr)"
        return "Elini (`يَدَهُۥ / يَدَكَ / يَدَى`, tekil müennes isim mansûb)"

    if root_ar == 'أ-م-م':
        if lemma == 'A^m~iyn':
            return "Kutsal Ev'e doğru yönelip kastederek gelen kimseler (`ءَآمِّينَ`, I. bab muzâaf ism-i fâil çoğul mansûb)"
        if lemma == '>amaAm':
            return "Kendi önünü ve geleceğini hesaba katmadan (`أَمَامَهُۥ`, zaman-mekân zarfı mansûb)"
        if lemma == '>um~iY~':
            if (s, a) in ((7, 157), (7, 158)):
                return "Okuryazarlık/kitap geleneği dışı fıtrat üzere yetişen (`ٱلْأُمِّىَّ / ٱلْأُمِّيِّ`, nispet sıfatı)"
            return "Önceki vahiy kitaplarına erişimi olmayan veya ana çizgisinden kalma halklar (`أُمِّيُّونَ / ٱلْأُمِّيِّينَ`, çoğul nispet ismi)"
        if lemma == '<imaAm':
            if (s, a) in ((15, 79), (36, 12)):
                return "Apaçık göz önündeki ana yol veya kapsamlı ana kayıt sicili (`بِإِمَامٍ مُّبِينٍ / إِمَامٍ مُّبِينٍ`, tekil isim mecrûr)"
            if (s, a) in ((9, 12), (21, 73), (28, 5), (28, 41), (32, 24)):
                return "Peşinden gidilen öncüler, önderler (`أَئِمَّةً / أَئِمَّةَ`, kırık çoğul isim)"
            return "Örnek rehber, öncü kitap veya çağrı sicili (`إِمَامًا / بِإِمَٰمِهِمْ`, tekil isim)"
        if lemma == '>um~ap':
            if (s, a) in ((11, 8), (12, 45)):
                return "Belirli ve sayılı bir zaman dilimi / uzunca bir süre (`أُمَّةٍ مَّعْدُودَةٍ / بَعْدَ أُمَّةٍ`, isim mecrûr)"
            if (s, a) == (16, 120):
                return "Tek başına başlı başına bir örnek topluluk/model şahsiyet (`أُمَّةً`, tekil isim mansûb)"
            if 'FP' in features:
                return "Topluluklar, kuşaklar ve canlı türleri (`أُمَمٌ / أُمَمٍ / أُمَمًا`, kırık çoğul)"
            return "Ortak bir yöneliş, inanç veya yaşam yolu etrafında birleşen topluluk (`أُمَّةٌ / أُمَّةً / أُمَّتُكُمْ`, tekil isim)"
        if lemma == '>um~':
            if (s, a) in ((3, 7), (13, 39), (43, 4), (6, 92), (42, 7), (101, 9)):
                return "Kitabın veya kentlerin ana merkezi/kaynağı yahut sarılacak kucak (`أُمُّ ٱلْكِتَٰبِ / أُمَّ ٱلْقُرَىٰ / أُمُّهُۥ هَاوِيَةٌ`, tekil isim)"
            if 'FP' in features:
                return "Anneler / doğuran gerçek analar (`أُمَّهَٰتُكُمْ / أُمَّهَٰتُهُمْ`, çoğul isim)"
            return "Doğuran anne / ana (`أُمِّهِ / أُمَّهُۥ / أُمُّكَ`, tekil isim)"

    if root_ar == 'ع-ز-ز':
        if lemma == 'tuEiz~u':
            return "Dilediğini sarsılmaz onura ve üstünlüğe erdirirsin (`وَتُعِزُّ`, IV. bab muzâri `2MS`)"
        if lemma == 'Eaz~azo':
            return "Üçüncü bir elçiyle güçlendirip pekiştirdik (`فَعَزَّزْنَا`, II. bab mâzî `1P`)"
        if lemma == 'Eaz~a':
            return "Tartışma ve söz yarışında beni bastırıp üstün geldi (`وَعَزَّنِى`, I. bab muzâaf mâzî `3MS`)"
        if lemma == 'Eiz~':
            return "Kendilerine dayanak ve koruyucu güç (`عِزًّا`, yalın masdar isim mansûb)"
        if lemma == '>aEaz~':
            return "Daha üstün, sayıca daha güçlü ve daha saygın (`أَعَزُّ / ٱلْأَعَزُّ`, ismi-tafdîl merfû)"
        if lemma == 'Eiz~ap':
            if 'GEN' in features:
                return "Kibirli direnişinin / üstün kudretinin (`بِعِزَّةِ / عِزَّةٍ / فَبِعِزَّتِكَ`, dişil isim mecrûr)"
            if 'ACC' in features:
                return "Onuru, sarsılmaz üstünlük ve saygınlığı (`ٱلْعِزَّةَ`, dişil isim mansûb)"
            return "Gerçek onur ve sarsılmaz izzet (`ٱلْعِزَّةُ`, dişil isim merfû)"
        if lemma == 'Eaziyz':
            if (s, a) in ((5, 54), (27, 34)):
                return "Baş eğmez onurlu kimseler (`أَعِزَّةٍ / أَعِزَّةَ`, kırık çoğul `MP`)"
            if (s, a) in ((12, 30), (12, 51), (12, 78), (12, 88)):
                return "Mısır'ın yüksek yöneticisi, güçlü veziri (`ٱلْعَزِيزُ / ٱلْعَزِيزِ`, lakap-unvan)"
            if (s, a) in ((14, 20), (35, 17)):
                return "Allah için erişilmez, zor ve imkânsız olan (`بِعَزِيزٍ`, güçlük/nadirlik sıfatı mecrûr)"
            if (s, a) == (11, 91):
                return "Gözümüzde güçlü, dokunulmaz ve saygın biri (`بِعَزِيزٍ`, isim mecrûr)"
            if (s, a) == (9, 128):
                return "İçine pek ağır ve zor gelen (`عَزِيزٌ`, sıfat merfû)"
            if (s, a) == (41, 41):
                return "Her türlü bozulmaya karşı yenilmez ve eşsiz kitap (`عَزِيزٌ`, sıfat merfû)"
            return "Mutlak yenilmez, aşılmaz kudret sahibi (`ٱلْعَزِيزُ / عَزِيزًا / بِعَزِيزٍ`, fa'îl sıfatı)"

    if root_ar == 'ج-ز-ي':
        if lemma == 'nuja`ziY^':
            return "Nankörlükte direnenlere eylemlerinin tam denk karşılığını veririz (`نُجَٰزِىٓ`, III. bab mufâale muzâri `1P`)"
        if lemma == 'jaAz':
            return "Babası adına bir bedel ödeyip yerine geçebilecek kimse (`جَازٍ`, I. bab nâkıs ism-i fâil mecrûr)"
        if lemma == 'jizoyap':
            return "Koruma ve barış düzeni karşılığı ödenen güvence bedeli (`ٱلْجِزْيَةَ`, fi'le kalıbı isim mansûb)"
        if lemma == 'jazaA^`'[0:0] or lemma == "jazaA^'":
            if (s, a) == (53, 41):
                return "Eksiksiz ve tastamam karşılığı (`ٱلْجَزَآءَ`, tek marife mansûb masdar)"
            if 'ACC' in features:
                return "Yaptıklarının tam karşılığı olarak (`جَزَآءً`, mef'ûl-i mutlak / le-eclih nekre mansûb)"
            return "Eyleminin sonucu ve tam karşılığı (`جَزَآءُ / جَزَآؤُهُمْ / جَزَآؤُكُمْ`, masdar merfû)"
        if lemma == 'jazaY`':
            if 'PASS' in features:
                return "Eyleminizce eksiksiz karşılık görürsünüz / karşılık verilir (`تُجْزَوْنَ / يُجْزَوْنَ / يُجْزَىٰ`, I. bab edilgen muzâri)"
            if (s, a) in ((2, 48), (2, 123), (31, 33)):
                return "Kimse kimsenin yerine geçip yükünü ödeyemez (`تَجْزِى / يَجْزِى`, I. bab muzâri 'yerine geçmek/yeterli olmak')"
            if 'PERF' in features:
                return "Yaptıklarına karşılık verdik / verdim (`جَزَيْنَٰهُمْ / جَزَيْتُهُمُ / وَجَزَىٰهُم`, I. bab mâzî)"
            return "Herkesin eylemine denk karşılığını veririz / verecektir (`نَجْزِى / سَيَجْزِي / لِيَجْزِىَ`, I. bab muzâri)"

    if root_ar == 'أ-ب-و':
        if lemma == '>abawaAn':
            if 'GEN' in features:
                return "Anne ve babasının her ikisinin (`وَلِأَبَوَيْهِ / أَبَوَيْهِ`, tağlîb ikil mecrûr)"
            if 'NOM' in features:
                return "Anne ve babası her ikisi (`أَبَوَاهُ`, tağlîb ikil merfû)"
            return "Anne ve babasını (`أَبَوَيْهِ`, tağlîb ikil mansûb)"
        if lemma == 'A^baA\'':
            if 'GEN' in features:
                return "Babalarının ve atalarının (`ءَابَآئِكُمْ / ءَابَآئِهِمْ / لِءَابَآئِهِمْ`, kırık çoğul mecrûr)"
            if 'ACC' in features:
                return "Babalarını / geçmiş atalarını (`ءَابَآءَكُمْ / ءَابَآءَنَا`, kırık çoğul mansûb)"
            return "Ataları / babaları (`ءَابَآؤُكُمْ / ءَابَآؤُنَا / ءَابَآؤُهُمْ`, kırık çoğul merfû)"
        if lemma == '>abN':
            if 'INDEF' in features:
                return "Çok yaşlı bir babayı (`أَبًا`, nekre tenvinli isim mansûb)"
            if (s, a) in ((12, 4), (12, 100), (19, 42), (19, 43), (19, 44), (19, 45), (28, 26), (37, 102)) and 'GEN' not in features:
                return "Ey babacığım! (`يَٰٓأَبَتِ`, `تاء التعويض` bitişik samimi münâdâ)"
            if 'GEN' in features:
                return "Babasının / babamın / babanızın (`لِأَبِيهِ / أَبِيكُمْ / أَبِى`, Esma-i Hamse mecrûr)"
            if 'NOM' in features:
                return "Babası / babaları / babamız (`أَبُوهُمْ / أَبُونَا / أَبِى`, Esma-i Hamse merfû)"
            return "Babamızı / babanızı / babasını (`أَبَانَا / أَبَاكُمْ / أَبَآ`, Esma-i Hamse mansûb)"

    if root_ar == 'ن-ه-ر':
        if lemma == 'tanoharo':
            return "Taşkınlık edip tersleyerek azarlama (`تَنْهَرْهُمَا / فَلَا تَنْهَرْ`, I. bab nehiy meczûm `2MS`)"
        if lemma == 'nahaAr':
            if (s, a) == (41, 37):
                return "Aydınlık gündüz (`وَٱلنَّهَارُ`, tüm kökte tek marife merfû `نَهَار`)"
            if (s, a) == (46, 35):
                return "Gündüzün yalnızca bir anı (`نَّهَارٍۭ`, tüm kökte tek nekre mecrûr)"
            if 'ACC' in features:
                return "Aydınlık gündüzü / gündüz boyunca (`ٱلنَّهَارَ / نَهَارًا / وَنَهَارًا`, zaman ismi/zarfı mansûb)"
            return "Gündüzün / gündüz vakti (`ٱلنَّهَارِ / بِالنَّهَارِ`, zaman ismi mecrûr)"
        if lemma == 'nahar':
            if (s, a) == (54, 54):
                return "Geniş akan sular, ferahlık ve kesintisiz aydınlık (`وَنَهَرٍ`, nekre tekil mecrûr)"
            if (s, a) in ((2, 249), (18, 33)):
                return "Toprağı yarıp akan akarsu/nehir (`بِنَهَرٍ / نَهَرًا`, nekre tekil)"
            if 'ACC' in features:
                return "Irmakları / akan su yataklarını (`ٱلْأَنْهَٰرَ / وَأَنْهَٰرًا / أَنْهَٰرًا`, kırık çoğul mansûb)"
            return "Altından akıp duran ırmaklar (`ٱلْأَنْهَٰرُ / أَنْهَٰرٌ`, kırık çoğul merfû)"

    if root_ar == 'أ-ك-ل':
        if lemma == 'm~a>okuwl':
            return "Yenilip tüketilmiş, içi kemirilmiş (`مَّأْكُولٍۭ`, ism-i mef'ûl nekre sıfat mecrûr)"
        if lemma == '>ak~a`luwn':
            return "Oburca ve sürekli yiyip sömürenler (`أَكَّٰلُونَ`, mübalağa ism-i fâil çoğul merfû)"
        if lemma == "'aAkiluwn":
            if 'GEN' in features:
                return "Yiyenler ve katık edinenler için (`لِّلْءَاكِلِينَ`, ism-i fâil çoğul mecrûr)"
            return "Elbette yiyecek olanlardır (`لَءَاكِلُونَ`, tekit lâm'lı ism-i fâil çoğul merfû)"
        if lemma == '>akol':
            if 'INDEF' in features:
                return "Toptan süpürürcesine bir tüketişle (`أَكْلًا`, mef'ûl-i mutlak masdar mansûb)"
            return "Haksızca yiyip tüketmeleri (`وَأَكْلِهِمْ`, masdar mecrûr)"
        if lemma == '>ukul':
            if 'INDEF' in features:
                return "Buruk ve kekre bir ürün/yemiş (`أُكُلٍ`, nekre isim mecrûr)"
            if 'GEN' in features:
                return "Yenilebilir tat ve ürün verimi bakımından (`فِى ٱلْأُكُلِ`, marife isim mecrûr)"
            if 'ACC' in features:
                return "Yenilebilir ürününü / meyve verimini (`أُكُلَهَا`, isim mansûb)"
            return "Yenilebilir ürünü / kesintisiz verimi (`أُكُلُهُۥ / أُكُلُهَا`, isim merfû)"
        if 'IMPV' in features:
            if '2D' in features or '2MD' in features:
                return "İkiniz de bol bol yiyip faydalanın (`وَكُلَا / فَكُلَا`, I. bab emir ikil)"
            if '2FS' in features:
                return "Ye ve beslen (`كُلِى / فَكُلِى`, I. bab emir 2. tekil dişil)"
            return "Yiyin, helal ve temiz verimden faydalanıp tüketin (`كُلُوا۟ / فَكُلُوا۟ / وَكُلُوا۟ / فَكُلُوهُ`, I. bab emir 2. çoğul)"
        if 'PERF' in features:
            if '3MD' in features:
                return "İkisi de ondan yedi (`فَأَكَلَا`, I. bab mâzî 3. ikil eril)"
            if '3MP' in features:
                return "Elbette her yönden yer ve bolluğa ererlerdi (`لَأَكَلُوا۟`, I. bab cevap lâm'lı mâzî 3. çoğul)"
            return "Yedi / parçalayıp tüketti (`أَكَلَ / أَكَلَهُ / فَأَكَلَهُ`, I. bab mâzî 3. tekil eril)"
        if '1P' in features:
            return "Ondan yemeyi (`نَّأْكُلَ`, I. bab mansûb muzâri 1. çoğul)"
        if '3MD' in features:
            return "İkisi de yiyecek yerlerdi (`يَأْكُلَانِ`, I. bab muzâri 3. ikil eril)"
        if '3FP' in features:
            return "Yiyip tüketirler (`يَأْكُلْنَ`, I. bab muzâri 3. çoğul dişil)"
        if '3FS' in features:
            if 'MOOD:JUS' in features:
                return "Otlasın / yiyip beslensin (`تَأْكُلْ`, I. bab meczûm muzâri 3. tekil dişil)"
            return "Yer / yakıp tüketir / kemirip aşındırır (`تَأْكُلُ / فَتَأْكُلُ / تَأْكُلُهُ`, I. bab muzâri 3. tekil dişil)"
        if '3MS' in features:
            if 'MOOD:JUS' in features:
                return "Ölçüsünce yesin (`فَلْيَأْكُلْ`, emir lâm'lı meczûm muzâri 3. tekil eril)"
            if 'MOOD:SUBJ' in features:
                return "Yemesini / yemesinden (`يَأْكُلَهُ / يَأْكُلَ`, mansûb muzâri 3. tekil eril)"
            return "Yer / tüketir (`يَأْكُلُ / يَأْكُلُهُنَّ / يَأْكُلُهُۥٓ`, I. bab muzâri 3. tekil eril)"
        if '2MP' in features:
            if 'MOOD:JUS' in features:
                return "Yemeyin / tüketmeyin (`تَأْكُلُوا۟ / تَأْكُلُوهَآ`, I. bab nehiy meczûm muzâri 2. çoğul)"
            if 'MOOD:SUBJ' in features:
                return "Yemeniz / yemek için (`لِتَأْكُلُوا۟ / تَأْكُلُوا۟`, mansûb muzâri 2. çoğul)"
            return "Yiyorsunuz / yersiniz (`تَأْكُلُونَ / وَتَأْكُلُونَ`, I. bab muzâri 2. çoğul)"
        if 'MOOD:SUBJ' in features:
            return "Yesinler / yemeleri için (`يَأْكُلُوا۟ / لِيَأْكُلُوا۟`, I. bab mansûb muzâri 3. çoğul)"
        return "Yerler / tüketirler (`يَأْكُلُونَ / لَيَأْكُلُونَ / وَيَأْكُلُونَ`, I. bab muzâri 3. çoğul)"

    if root_ar == 'ح-س-ب':
        if lemma == 'Ha`sibiyn':
            if 'GEN' in features:
                return "Hesap görenlerin en hızlısı (`ٱلْحَٰسِبِينَ`, ism-i fâil çoğul mecrûr)"
            return "Hesap görenler olarak (`حَٰسِبِينَ`, ism-i fâil çoğul mansûb hâl)"
        if lemma == 'Hasiyb':
            return "Eksiksiz hesap görücü ve gözetici (`حَسِيبًا`, mübalağa sıfat/isim mansûb)"
        if lemma == 'HusobaAn':
            if 'GEN' in features:
                return "Şaşmaz bir hesap ve ölçü düzeniyle (`بِحُسْبَانٍ`, nekre isim mecrûr)"
            if (s, a) == (18, 40):
                return "Gökten hesaplı ve ölçülü bir darbe (`حُسْبَانًا`, nekre isim mansûb)"
            return "Kozmik bir hesap ve vakit ölçüsü (`حُسْبَانًا`, nekre mef'ûl mansûb)"
        if lemma == 'Hasob':
            if 'ACC' in features:
                return "Sana eksiksiz yeten (`حَسْبَكَ`, ism-i inne mansûb)"
            return "Bize / sana / onlara tam yeten (`حَسْبُنَا / حَسْبِىَ / حَسْبُكَ / حَسْبُهُمْ`, mübtedâ/haber merfû)"
        if lemma == 'HisaAb':
            if 'ADJ' in features:
                return "Hesaplı ve doyurucu derecede yeterli (`حِسَابًا`, III. bab masdar kökenli sıfat mansûb)"
            if 'INDEF' in features:
                if 'ACC' in features:
                    return "Çetin / kolay bir hesap / karşılık (`حِسَابًا`, nekre isim/mef'ûl mansûb)"
                return "Sınırsız ve hesapsız (`بِغَيْرِ حِسَابٍ`, nekre isim mecrûr)"
            if (s, a) == (69, 20):
                return "Kendi hesabımla (`حِسَابِيَهْ`, sekte he'li mef'ûl mansûb)"
            if (s, a) == (69, 26):
                return "Kendi hesabımın ne olduğunu (`حِسَابِيَهْ`, sekte he'li merfû)"
            if 'GEN' in features:
                return "Hesap görmenin / hesapların (`ٱلْحِسَابِ / حِسَابِهِم / حِسَابِكَ`, mecrûr)"
            if 'ACC' in features:
                return "Hesabı / hesaplarını (`وَٱلْحِسَابَ / حِسَابَهُۥ / حِسَابَهُم`, mansûb)"
            return "Hesap ve muhasebe (`ٱلْحِسَابُ / حِسَابُهُمْ / حِسَابُهُۥ`, merfû)"
        if lemma == 'HaAsabo':
            if 'PASS' in features:
                return "Muhasebeye ve hesaba çekilir (`يُحَاسَبُ`, III. bab meçhul muzâri 3. tekil eril)"
            if 'PERF' in features:
                return "Onu çetin bir muhasebeye çektik (`فَحَاسَبْنَٰهَا`, III. bab mâzî 1. çoğul)"
            return "Onunla sizi muhasebeye çeker (`يُحَاسِبْكُم`, III. bab meczûm muzâri 3. tekil eril)"
        if lemma == 'yaHotasibu':
            if 'MOOD:JUS' in features:
                return "Hesaplarına katıp öngörmedikleri (`يَحْتَسِبُوا۟`, VIII. bab meczûm muzâri 3. çoğul)"
            if '3MP' in features:
                return "Hesaplarına katıp bekledikleri (`يَحْتَسِبُونَ`, VIII. bab muzâri 3. çoğul)"
            return "Kendi hesabına katıp beklediği (`يَحْتَسِبُ`, VIII. bab muzâri 3. tekil eril)"
        if 'PERF' in features:
            if '2MP' in features:
                return "Yoksa ... mı hesabedip sandınız (`حَسِبْتُمْ / أَفَحَسِبْتُمْ`, I. bab mâzî 2. çoğul)"
            if '2MS' in features:
                return "Sandın / onları ... saydın (`حَسِبْتَ / حَسِبْتَهُمْ`, I. bab mâzî 2. tekil eril)"
            if '3FS' in features:
                return "Onu ... sandı (`حَسِبَتْهُ`, I. bab mâzî 3. tekil dişil)"
            if '3MP' in features:
                return "Sandılar / hesabettiler (`وَحَسِبُوٓا۟`, I. bab mâzî 3. çoğul)"
            return "Yoksa ... mı sandı (`أَحَسِبَ / أَفَحَسِبَ / حَسِبَ`, I. bab mâzî 3. tekil eril)"
        if '2MP' in features:
            if 'MOOD:JUS' in features:
                return "Onu ... saymayın / sanmayın (`تَحْسَبُوهُ`, I. bab nehiy meczûm muzâri 2. çoğul)"
            if 'MOOD:SUBJ' in features:
                return "Onu ... sanasınız diye (`لِتَحْسَبُوهُ`, I. bab mansûb muzâri 2. çoğul)"
            return "Onu ... sanıyorsunuz (`وَتَحْسَبُونَهُۥ`, I. bab muzâri 2. çoğul)"
        if '2MS' in features:
            if (s, a) in ((3, 169), (3, 188), (14, 42), (14, 47), (24, 57)):
                return "Sakın ... sanma (`تَحْسَبَنَّ / تَحْسَبَنَّهُم`, tekit nûnlu nehiy I. bab muzâri 2. tekil)"
            return "Onları / onu ... sanırsın (`تَحْسَبُ / تَحْسَبُهُمْ / وَتَحْسَبُهُمْ`, I. bab muzâri 2. tekil)"
        if '3FS' in features:
            return "Onu ... sanırsın (`تَحْسَبُهَا`, I. bab muzâri)"
        if '3MP' in features:
            return "Sanırlar / sayarlar (`يَحْسَبُونَ / أَيَحْسَبُونَ / وَيَحْسَبُونَ`, I. bab muzâri 3. çoğul)"
        if (s, a) in ((3, 178), (3, 180), (8, 59)):
            return "Sakın ... sanmasınlar (`يَحْسَبَنَّ`, tekit nûnlu nehiy I. bab muzâri)"
        return "Yoksa ... sanıyor mu / sanır (`أَيَحْسَبُ / يَحْسَبُ / يَحْسَبُهُ`, I. bab muzâri 3. tekil eril)"

    if root_ar == 'ف-ع-ل':
        if lemma == 'fiEol':
            return "Hayırları fiilen yapmayı / icra etmeyi (`فِعْلَ`, I. bab masdar mansûb muzâf)"
        if lemma == 'faEolat':
            return "Yaptığın o tekil eylemini (`فَعْلَتَكَ`, binâ-yı merre masdar mef'ûl-i mutlak)"
        if lemma == 'faE~aAl':
            return "Dilediğini kesintisiz ve mutlaka yapandır (`فَعَّالٌ`, mübalağa sıfat/isim nekre merfû)"
        if lemma == 'mafoEuwl':
            return "Kesinlikle yapılmış / gerçekleşip olguya dönüşmüş olan (`مَفْعُولًا / لَمَفْعُولًا`, ism-i mef'ûl nekre mansûb)"
        if lemma == 'faAEil':
            if 'INDEF' in features:
                return "Yarın bunu yapacak olan (`فَاعِلٌ`, ism-i fâil nekre tekil merfû)"
            if 'NOM' in features:
                return "Elbette yapacak / fiilen uygulayanlardır (`فَٰعِلُونَ / لَفَٰعِلُونَ`, ism-i fâil çoğul merfû)"
            return "Eğer gerçekten yapacak kimselerseniz / yapanlar (`فَٰعِلِينَ`, ism-i fâil çoğul mansûb)"
        if 'PASS' in features:
            if 'PERF' in features:
                return "Benzerlerine yapıldığı gibi (`فُعِلَ`, I. bab meçhul mâzî 3. tekil eril)"
            if 'MOOD:SUBJ' in features:
                return "Kendisine ... yapılacağını (`يُفْعَلَ`, I. bab meçhul mansûb muzâri 3. tekil eril)"
            return "Bana ve size ne yapılacağını (`يُفْعَلُ`, I. bab meçhul muzâri 3. tekil eril)"
        if 'IMPV' in features:
            if '2MS' in features:
                return "Emrolunduğunu fiilen yap (`ٱفْعَلْ`, I. bab emir 2. tekil eril)"
            return "Emrolunanı / iyiliği fiilen yapın (`فَٱفْعَلُوا۟ / وَٱفْعَلُوا۟`, I. bab emir 2. çoğul)"
        if 'PERF' in features:
            if '1S' in features:
                return "Onu yaptım (`فَعَلْتُهَآ / فَعَلْتُهُۥ`, I. bab mâzî 1. tekil)"
            if '1P' in features:
                return "Onlara nasıl yaptık (`فَعَلْنَا`, I. bab mâzî 1. çoğul)"
            if '2MS' in features:
                return "Bunu sen mi yaptın / yaptıysan (`فَعَلْتَ / وَفَعَلْتَ`, I. bab mâzî 2. tekil eril)"
            if '2MP' in features:
                return "Ne yaptığınızı (`فَعَلْتُمْ / فَعَلْتُم`, I. bab mâzî 2. çoğul)"
            if '3FP' in features:
                return "Kendi haklarında yaptıklarında (`فَعَلْنَ`, I. bab mâzî 3. çoğul dişil)"
            if '3MP' in features:
                return "Onlar bunu yaptılar / onu yaptılar (`فَعَلُوا۟ / فَعَلُوهُ`, I. bab mâzî 3. çoğul)"
            return "Yaptı / nasıl müdahale etti (`فَعَلَ / فَعَلَهُۥ`, I. bab mâzî 3. tekil eril)"
        if '1P' in features:
            if 'MOOD:SUBJ' in features:
                return "İstediğimizi yapmamızı (`نَّفْعَلَ`, I. bab mansûb muzâri 1. çoğul)"
            return "İşte böyle yaparız (`نَفْعَلُ`, I. bab muzâri 1. çoğul)"
        if '2MS' in features:
            return "Eğer bunu yapmazsan (`تَفْعَلْ`, I. bab meczûm muzâri 2. tekil eril)"
        if '2MP' in features:
            if 'MOOD:JUS' in features:
                return "Yapmazsanız / yapacağınız her iyilik (`تَفْعَلُوا۟`, I. bab meczûm muzâri 2. çoğul)"
            if 'MOOD:SUBJ' in features:
                return "Asla yapamayacaksınız / yapmanız (`تَفْعَلُوا۟ / تَفْعَلُوهُ / تَفْعَلُوٓا۟`, mansûb muzâri 2. çoğul)"
            return "Yapmıyorsunuz / yaptıklarınız (`تَفْعَلُونَ`, I. bab muzâri 2. çoğul)"
        if '3MP' in features:
            if 'MOOD:JUS' in features:
                return "Yapacakları her iyilik / yapmadıkları (`يَفْعَلُوا۟`, I. bab meczûm muzâri 3. çoğul)"
            return "Yaparlar / yaptıkları (`يَفْعَلُونَ / وَيَفْعَلُونَ`, I. bab muzâri 3. çoğul)"
        if 'MOOD:JUS' in features:
            return "Kim bunu yaparsa / yapmazsa (`يَفْعَلْ / يَفْعَلْهُ`, I. bab meczûm muzâri 3. tekil eril)"
        return "Yapar / dilediğini gerçekleştirir (`يَفْعَلُ / وَيَفْعَلُ`, I. bab muzâri 3. tekil eril)"

    if root_ar == 'أ-ج-ر':
        if lemma == 'ta>ojura':
            return "Ücret ve hak karşılığı bana çalışman (`تَأْجُرَنِى`, I. bab mansûb muzâri 2. tekil eril)"
        if lemma == '{sota_#ojaro':
            if 'IMPV' in features:
                return "Onu emek bedeliyle çalıştır (`ٱسْتَـْٔجِرْهُ`, X. bab emir 2. tekil eril)"
            return "Bedel karşılığı çalıştırdığın kimselerin (`ٱسْتَـْٔجَرْتَ`, X. bab mâzî 2. tekil eril)"
        if 'MP' in features:
            if (s, a) in ((4, 24), (4, 25), (5, 5), (33, 50), (60, 10)):
                return "Evlilik akdinden doğan hak bedellerini (`أُجُورَهُنَّ`, çoğul isim mansûb)"
            if (s, a) == (65, 6):
                return "Emzirme emeği ücretlerini (`أُجُورَهُنَّ`, çoğul isim mansûb)"
            return "Hak edilmiş emek karşılıklarını (`أُجُورَهُمْ / أُجُورَكُمْ`, çoğul isim mansûb)"
        if 'INDEF' in features:
            if 'GEN' in features:
                return "Herhangi bir ücret veya bedel (`أَجْرٍ / وَأَجْرٍ`, nekre tekil isim mecrûr)"
            if 'ACC' in features:
                return "Büyük / güzel / kesintisiz bir karşılık ve ücret (`أَجْرًا / لَأَجْرًا / وَأَجْرًا`, nekre tekil isim mansûb)"
            return "Büyük / kesintisiz bir hak ediş (`أَجْرٌ / وَأَجْرٌ`, nekre tekil isim merfû)"
        if 'ACC' in features:
            return "Hak edilmiş karşılığını / ecrini (`أَجْرَ / أَجْرَهُم / أَجْرَهُۥ / أَجْرَهَا`, muzâf tekil isim mansûb)"
        return "Hak edilmiş karşılığı / ecrim (`أَجْرُ / أَجْرِىَ / أَجْرُهُمْ / وَلَأَجْرُ`, muzâf tekil isim merfû)"

    if root_ar == 'و-ج-د':
        if lemma == 'wujod':
            return "Maddî güç ve imkân genişliğinizden (`مِن وُجْدِكُمْ`, tekil isim mecrûr)"
        if 'PASS' in features:
            return "Kimin yükünde bulunursa (`وُجِدَ`, I. bab meçhul mâzî 3. tekil eril)"
        if 'PERF' in features:
            if '1P' in features:
                if (s, a) == (38, 44):
                    return "Onu gerçekten ... bulduk (`وَجَدْنَٰهُ`, I. bab mâzî 1. çoğul)"
                if (s, a) == (72, 8):
                    return "Derhal onu ... dolmuş bulduk (`فَوَجَدْنَٰهَا`, I. bab mâzî 1. çoğul)"
                return "Üzerinde / katında ... bulduk (`وَجَدْنَا`, I. bab mâzî 1. çoğul)"
            if '1S' in features:
                return "Buldum / onu ... halde buldum (`وَجَدتُّ / وَجَدتُّهَا`, I. bab mâzî 1. tekil)"
            if '2MP' in features:
                return "Buldunuz / onları nerede bulursanız (`وَجَدتُّم / وَجَدتُّمُوهُمْ`, I. bab mâzî 2. çoğul)"
            if '3MP' in features:
                return "Elbette bulurlardı / hazır buldular (`لَوَجَدُوا۟ / وَجَدُوا۟ / وَوَجَدُوا۟`, I. bab mâzî 3. çoğul)"
            if '3MD' in features:
                return "İkisi birden orada buldu (`فَوَجَدَا`, I. bab mâzî 3. ikil)"
            return "Buldu / onu buldu / seni ... halde buldu (`وَجَدَ / وَجَدَهَا / وَوَجَدَكَ`, I. bab mâzî 3. tekil eril)"
        if '1S' in features:
            if 'MOOD:SUBJ' in features:
                return "Asla başka bir sığınak bulamam (`أَجِدَ`, I. bab mansûb muzâri 1. tekil)"
            return "Buluyorum / bulamam / elbette bulurum (`أَجِدُ / لَأَجِدُ / لَأَجِدَنَّ`, I. bab muzâri 1. tekil)"
        if '1P' in features:
            return "Onda kararlı bir irade bulamadık (`نَجِدْ`, I. bab meczûm muzâri 1. çoğul)"
        if '2MS' in features:
            if 'MOOD:SUBJ' in features:
                return "Asla yol, yardımcı veya değişiklik bulamazsın (`تَجِدَ`, I. bab mansûb muzâri 2. tekil eril)"
            if (s, a) in ((18, 69), (28, 27), (37, 102)):
                return "Yakında beni ... halde bulacaksın (`سَتَجِدُنِىٓ`, I. bab muzâri 2. tekil eril)"
            return "Onları mutlaka bulursun / bulamazsın (`وَلَتَجِدَنَّهُمْ / لَتَجِدَنَّ / تَجِدُ`, I. bab muzâri 2. tekil eril)"
        if '2MP' in features:
            if 'MOOD:JUS' in features:
                return "Bulursunuz / bulamazsanız (`تَجِدُوا۟ / تَجِدُوهُ`, I. bab meczûm muzâri 2. çoğul)"
            return "Yakında başkalarını da bulacaksınız (`سَتَجِدُونَ`, I. bab muzâri 2. çoğul)"
        if '3FS' in features:
            return "Her benlik yaptığını hazır bulacaktır (`تَجِدُ`, I. bab muzâri 3. tekil dişil)"
        if '3MS' in features:
            return "Bulursa / bulamazsa / seni bulup (`يَجِدْ / يَجِدِ / يَجِدْهُ / يَجِدْكَ`, I. bab meczûm muzâri 3. tekil eril)"
        if '3MP' in features:
            if 'MOOD:JUS' in features:
                return "Bulamazlar / sertlik bulsunlar (`يَجِدُوا۟ / وَلْيَجِدُوا۟`, I. bab meczûm muzâri 3. çoğul)"
            if 'MOOD:SUBJ' in features:
                return "Bulamadıkları için / sığınak bulamazlar (`يَجِدُوا۟`, I. bab mansûb muzâri 3. çoğul)"
            return "Bulurlar / bulamazlar (`يَجِدُونَ / يَجِدُونَهُۥ`, I. bab muzâri 3. çoğul)"

    if root_ar == 'ع-د-و':
        if lemma == 'EaAdayo':
            return "Karşıt safa geçip düşmanlaştıklarınız (`عَادَيْتُم`, III. bab mâzî 2. çoğul)"
        if lemma == 'yataEad~a':
            return "Kim Allah'ın sınırlarını aşarsa (`يَتَعَدَّ / وَيَتَعَدَّ`, V. bab meczûm muzâri 3. tekil eril)"
        if lemma == 'yaEodu':
            if '3FS' in features:
                return "Gözlerin öteye kayıp uzaklaşmasın (`تَعْدُ`, I. bab meczûm muzâri 3. tekil dişil)"
            if '2MP' in features:
                return "Cumartesi sınırını aşmayın (`تَعْدُوا۟`, I. bab meczûm muzâri 2. çoğul)"
            return "Sınırı aşıyorlardı (`يَعْدُونَ`, I. bab muzâri 3. çoğul)"
        if lemma == '{EotadaY`':
            if 'IMPV' in features:
                return "Aynı ölçüyle karşılık verin (`فَٱعْتَدُوا۟`, VIII. bab emir 2. çoğul)"
            if 'PERF' in features:
                if '1P' in features:
                    return "Biz haddi aştık (`ٱعْتَدَيْنَآ`, VIII. bab mâzî 1. çoğul)"
                if '3MP' in features:
                    return "Sınırı çiğneyip aştılar (`ٱعْتَدَوْا۟`, VIII. bab mâzî 3. çoğul)"
                return "Kim sınırı çiğneyip saldırırsa (`ٱعْتَدَىٰ`, VIII. bab mâzî 3. tekil eril)"
            if 'MOOD:SUBJ' in features:
                return "Haksızca haddi aşmanız / aşasınız (`لِّتَعْتَدُوا۟ / تَعْتَدُوا۟`, VIII. bab mansûb muzâri 2. çoğul)"
            if 'MOOD:JUS' in features:
                return "Sınırı aşmayın / çiğnemeyin (`تَعْتَدُوٓا۟ / تَعْتَدُوهَا`, VIII. bab meczûm muzâri 2. çoğul)"
            return "Sürekli haddi aşıyorlardı (`يَعْتَدُونَ`, VIII. bab muzâri 3. çoğul)"
        if lemma == 'Ea`diya`t':
            return "Soluk soluğa ileri atılıp koşanlara (`وَٱلْعَٰدِيَٰتِ`, dişil çoğul ism-i fâil mecrûr)"
        if lemma == 'EaAd':
            if 'MP' in features:
                return "Meşru sınırı aşıp ötesine geçenlerdir (`ٱلْعَادُونَ / عَادُونَ`, çoğul ism-i fâil merfû)"
            return "Zaruret ölçüsünü aşmaksızın (`عَادٍ`, tekil nâkıs ism-i fâil mecrûr)"
        if lemma == 'muEotadiyn':
            if (s, a) == (9, 10):
                return "İşte sınırı aşanlar bunlardır (`ٱلْمُعْتَدُونَ`, çoğul ism-i fâil merfû)"
            if 'GEN' in features:
                return "Haddi aşanları / azgınları (`بِٱلْمُعْتَدِينَ / ٱلْمُعْتَدِينَ`, çoğul ism-i fâil mecrûr)"
            return "Sınırı aşan taşkınları (`ٱلْمُعْتَدِينَ`, çoğul ism-i fâil mansûb)"
        if lemma == 'muEotad':
            return "Her sınır tanımaz taşkın (`مُعْتَدٍ`, VIII. bab tekil nâkıs ism-i fâil mecrûr)"
        if lemma == 'Eudowap':
            return "Vadinin yakın / uzak kenarında (`بِٱلْعُدْوَةِ`, tekil mekân ismi mecrûr)"
        if lemma == 'Eadow':
            return "Bilgisizce / taşkın bir düşmanlıkla (`عَدْوًۢا / وَعَدْوًا`, nekre masdar mansûb)"
        if lemma == 'Eudowa`n':
            if 'GEN' in features:
                return "Sınır tanımaz düşmanlık ve taşkınlık (`وَٱلْعُدْوَٰنِ`, masdar mecrûr)"
            return "Düşmanlık ve taşkınlık olarak (`عُدْوَٰنَ / عُدْوَٰنًا`, masdar mansûb)"
        if lemma == 'Eada`wap':
            if 'INDEF' in features and 'ACC' in features:
                return "Düşmanlık yönünden (`عَدَٰوَةً`, nekre dişil isim mansûb)"
            if 'ACC' in features:
                return "Aranızdaki kalıcı düşmanlığı (`ٱلْعَدَاوَةَ / ٱلْعَدَٰوَةَ`, dişil isim mansûb)"
            return "Düşmanlık ortaya çıktı (`عَدَٰوَةٌ / ٱلْعَدَٰوَةُ`, dişil isim merfû)"
        if 'MP' in features:
            if 'GEN' in features:
                return "Düşmanlarınızı / Allah'ın düşmanlarının (`بِأَعْدَآئِكُمْ / أَعْدَآءِ`, kırık çoğul mecrûr)"
            if 'ACC' in features:
                return "Düşmanlar / düşmanları (`أَعْدَآءً / ٱلْأَعْدَآءَ`, kırık çoğul mansûb)"
            return "Allah'ın düşmanları (`أَعْدَآءُ`, kırık çoğul merfû)"
        if 'GEN' in features:
            return "Düşmanınız / düşmanı / bir düşman (`عَدُوِّكُمْ / عَدُوِّهِۦ / عَدُوِّهِمْ / عَدُوٍّ`, tekil isim/sıfat mecrûr)"
        if 'ACC' in features:
            return "Apaçık düşman / düşmanınız (`عَدُوًّا / عَدُوَّ / وَعَدُوَّكُمْ / عَدُوِّى`, tekil isim mansûb)"
        return "Karşı safa geçen düşman (`عَدُوٌّ / عَدُوٌّۢ / ٱلْعَدُوُّ`, tekil isim merfû)"

    if root_ar == 'ر-ج-ع':
        if lemma == 'yataraAjaEa':
            return "Karşılıklı rızayla birbirlerine yeniden dönmeleri (`يَتَرَاجَعَآ`, VI. bab mansûb muzâri 3. ikil)"
        if lemma == 'r~ujoEaY`^':
            return "Mutlak dönüş (`ٱلرُّجْعَىٰٓ`, fualâ vezninde masdar/isim)"
        if lemma == 'rajoE':
            if (s, a) == (50, 3):
                return "Akıldan uzak bir geri dönüş (`رَجْعٌۢ`, tekil nekre isim merfû)"
            return "Döngülü geri döndürüşü / yağmuru (`رَجْعِهِۦ / ٱلرَّجْعِ`, tekil isim mecrûr)"
        if lemma == 'ra`jiEuwn':
            return "Şüphesiz O'na dönenleriz / dönecekler (`رَٰجِعُونَ`, çoğul ism-i fâil merfû)"
        if lemma == 'marojiE':
            if 'ACC' in features:
                return "Dönüş yerleri (`مَرْجِعَهُمْ`, mekân/masdar ismi mansûb)"
            return "Dönüşünüz / dönüşleri (`مَرْجِعُكُمْ / مَرْجِعُهُمْ`, mekân/masdar ismi merfû)"
        if 'IMPV' in features:
            if '2FS' in features:
                return "Rabbine gönül hoşnutluğuyla dön (`ٱرْجِعِىٓ`, I. bab emir 2. tekil dişil)"
            if '2MS' in features:
                return "Geri dön / bizi geri çevir / gözünü çevir (`ٱرْجِعْ / فَٱرْجِعْنَا / فَٱرْجِعِ / ٱرْجِعِ`, I. bab emir 2. tekil eril)"
            return "Geri dönün / beni geri çevirin (`ٱرْجِعُوا۟ / فَٱرْجِعُوا۟ / ٱرْجِعُونِ`, I. bab emir 2. çoğul)"
        if 'PASS' in features:
            if 'PERF' in features:
                return "Eğer Rabbime geri döndürülürsem (`رُّجِعْتُ`, I. bab meçhul mâzî 1. tekil)"
            if '3FS' in features:
                return "Bütün işler O'na geri döndürülür (`تُرْجَعُ`, I. bab meçhul muzâri 3. tekil dişil)"
            if '3MS' in features:
                return "Bütün iş O'na geri döndürülür (`يُرْجَعُ`, I. bab meçhul muzâri 3. tekil eril)"
            if '3MP' in features:
                return "O'na geri döndürülürler (`يُرْجَعُونَ`, I. bab meçhul muzâri 3. çoğul)"
            return "O'na geri döndürüleceksiniz (`تُرْجَعُونَ`, I. bab meçhul muzâri 2. çoğul)"
        if 'PERF' in features:
            if '1P' in features:
                return "Seni annene geri verdik / Medine'ye dönersek (`فَرَجَعْنَٰكَ / رَّجَعْنَآ`, I. bab mâzî 1. çoğul)"
            if '2MP' in features:
                return "Seferden döndüğünüzde (`رَجَعْتُمْ`, I. bab mâzî 2. çoğul)"
            if '3MP' in features:
                return "Döndüler / içlerine döndüler (`رَجَعُوٓا۟ / فَرَجَعُوٓا۟`, I. bab mâzî 3. çoğul)"
            return "Döndü / seni geri döndürdüğünde (`رَجَعَ / فَرَجَعَ / رَّجَعَكَ`, I. bab mâzî 3. tekil eril)"
        if '1S' in features:
            return "İnsanlara geri döneyim (`أَرْجِعُ`, I. bab muzâri 1. tekil)"
        if '2MP' in features:
            if 'MOOD:JUS' in features:
                return "Onları geri göndermeyin (`تَرْجِعُوهُنَّ`, I. bab meczûm muzâri 2. çoğul)"
            return "O canı geri çevirsenize (`تَرْجِعُونَهَآ`, I. bab muzâri 2. çoğul)"
        if '3MS' in features:
            if 'MOOD:SUBJ' in features:
                return "Bize geri dönünceye kadar (`يَرْجِعَ`, I. bab mansûb muzâri 3. tekil eril)"
            return "Söz veya sonuç geri döndürür / döner (`يَرْجِعُ`, I. bab muzâri 3. tekil eril)"
        return "Geri dönerler / dönmezler (`يَرْجِعُونَ`, I. bab muzâri 3. çoğul)"

    if root_ar == 'ف-ض-ل':
        if lemma == 'yatafaD~ala':
            return "Size karşı artı statü ve üstünlük elde etsin (`يَتَفَضَّلَ`, V. bab mansûb muzâri 3. tekil eril)"
        if lemma == 'tafoDiyl':
            return "Gerçek bir derece ve donanım farkıyla (`تَفْضِيلًا`, II. bab masdar mef'ûl-i mutlak mansûb)"
        if lemma == 'faD~ala':
            if 'PASS' in features:
                return "Kendilerine fazladan pay verilenler (`فُضِّلُوا۟`, II. bab meçhul mâzî 3. çoğul)"
            if 'IMPF' in features:
                return "Ürün ve tatta kimini kiminden farklı/artı kılarız (`وَنُفَضِّلُ`, II. bab muzâri 1. çoğul)"
            if '1S' in features:
                return "Sizi diğer toplumlara göre artı sorumlulukla donattım (`فَضَّلْتُكُمْ`, II. bab mâzî 1. tekil)"
            if '1P' in features:
                return "Bir kısmını diğerinden işlev ve payca ayırıp üstün kıldık (`فَضَّلْنَا / وَفَضَّلْنَٰهُمْ`, II. bab mâzî 1. çoğul)"
            return "Bir kısmını diğerinden farklı ve artı imkânla donattı (`فَضَّلَ / وَفَضَّلَ / فَضَّلَكُمْ / فَضَّلَنَا`, II. bab mâzî 3. tekil eril)"
        if 'INDEF' in features:
            if 'NOM' in features:
                return "Allah'tan bir artı nimet ve açılım (`فَضْلٌ`, nekre tekil isim merfû)"
            if 'ACC' in features:
                return "Rabbinizden gelen bir artı kazanç ve açılım (`فَضْلًا / وَفَضْلًا`, nekre tekil isim mansûb)"
            return "Büyük artı nimet ve açılım (`فَضْلٍ / وَفَضْلٍ / فَضْلٍۭ`, nekre tekil isim mecrûr)"
        if 'NOM' in features:
            return "Allah'ın artı nimeti ve koruması (`فَضْلُ / ٱلْفَضْلُ`, marife/muzâf tekil isim merfû)"
        if 'ACC' in features:
            return "Ayrılık anındaki fazladan iyiliği / artı açılımı (`ٱلْفَضْلَ / فَضْلَهُۥ`, marife/muzâf tekil isim mansûb)"
        return "Onun artı bolluğu / büyük açılımı (`فَضْلِهِۦ / ٱلْفَضْلِ / بِفَضْلِ / لِفَضْلِهِۦ`, marife/muzâf tekil isim mecrûr)"

    if root_ar == 'ص-ب-ر':
        if lemma == '{SoTabiro':
            return "Bilinçli çabayla sebatla kenetlen (`وَٱصْطَبِرْ`, VIII. bab `ت -> ط` kalbli emir 2. tekil eril)"
        if lemma == 'SaAbiru':
            return "Karşı taraftan daha dirençli ve sarsılmaz durun (`وَصَابِرُوا۟`, III. bab emir 2. çoğul)"
        if lemma == 'Sab~aAr':
            return "Zorlukta çok dirençli olan herkes (`صَبَّارٍ`, mübalağa sıfatı nekre mecrûr)"
        if lemma == 'S~a`bira`t':
            return "Sebat ve direnç sahibi kadınlar (`وَٱلصَّٰبِرَٰتِ`, dişil çoğul ism-i fâil mansûb)"
        if lemma == 'SaAbirap':
            return "Dirençli yüz kişilik birlik (`صَابِرَةٌ`, dişil tekil ism-i fâil merfû)"
        if lemma == 'SaAbir':
            if 'POS:ADJ' in features:
                return "Sebatla direnen yirmi kişi (`صَٰبِرُونَ`, çoğul sıfat merfû)"
            if 'MP|NOM' in features:
                return "Ancak sebat edip direnenler (`ٱلصَّٰبِرُونَ`, çoğul ism-i fâil merfû)"
            if 'M|INDEF|ACC' in features:
                return "Beni sebatkâr ve dirençli olarak (`صَابِرًا`, tekil nekre ism-i fâil mansûb)"
            if 'MP|ACC' in features:
                return "Sebat edip direnenleri (`ٱلصَّٰبِرِينَ / وَٱلصَّٰبِرِينَ`, çoğul ism-i fâil mansûb)"
            return "Sebat edip direnenlerle beraber / onlar için (`ٱلصَّٰبِرِينَ / لِّلصَّٰبِرِينَ`, çoğul ism-i fâil mecrûr)"
        if lemma == 'Sabor':
            if 'INDEF|NOM' in features:
                return "Artık güzel bir sebat ve irade tutumu gerekir (`فَصَبْرٌ`, tekil nekre masdar merfû)"
            if 'INDEF|ACC' in features:
                return "Üstün direnç / dayanma gücü (`صَبْرًا`, tekil nekre masdar mansûb)"
            if 'NOM' in features:
                return "Senin direnç ve sebatın (`صَبْرُكَ`, muzâf masdar merfû)"
            return "Direnç ve sebat ile (`بِٱلصَّبْرِ`, marife masdar mecrûr)"
        if 'IMPV' in features:
            if '2MS' in features:
                return "Sebat edip diren / benliğini tut (`ٱصْبِرْ / فَٱصْبِرْ / وَٱصْبِرْ`, I. bab emir 2. tekil eril)"
            return "Sebat edip direnin (`ٱصْبِرُوا۟ / فَٱصْبِرُوا۟ / وَٱصْبِرُوٓا۟`, I. bab emir 2. çoğul)"
        if 'PERF' in features:
            if (s, a) == (2, 175):
                return "Ateşe karşı ne kadar da cüretkâr dayanıyorlar (`أَصْبَرَهُمْ`, taaccüb IV. vezinli fiil)"
            if '3MS' in features:
                return "Kim direnir ve bağışlarsa / onların direndiği gibi (`صَبَرَ`, I. bab mâzî 3. tekil eril)"
            if '1P' in features:
                return "Dirensek de / ilahlarımız üzerinde direndik (`صَبَرْنَا`, I. bab mâzî 1. çoğul)"
            if '2MP' in features:
                return "Direndiniz / direnirseniz (`صَبَرْتُمْ`, I. bab mâzî 2. çoğul)"
            return "Zorluğa göğüs gerip direndiler (`صَبَرُوا۟ / فَصَبَرُوا۟ / وَصَبَرُوٓا۟ / صَبَرُوٓا۟`, I. bab mâzî 3. çoğul)"
        if '1P' in features:
            if 'MOOD:SUBJ' in features:
                return "Tek bir yiyeceğe asla dayanıp kalamayız (`نَّصْبِرَ`, I. bab mansûb muzâri 1. çoğul)"
            return "Eziyetinize elbette direneceğiz (`وَلَنَصْبِرَنَّ`, I. bab te'kidli muzâri 1. çoğul)"
        if '2MS' in features:
            return "Nasıl dayanabilirsin (`تَصْبِرُ`, I. bab muzâri 2. tekil eril)"
        if '2MP' in features:
            if 'MOOD:SUBJ' in features:
                return "Kendinizi tutmanız / direnmeniz (`تَصْبِرُوا۟`, I. bab mansûb muzâri 2. çoğul)"
            if 'MOOD:JUS' in features:
                return "Direnirseniz / direnmeseniz de (`تَصْبِرُوا۟`, I. bab meczûm muzâri 2. çoğul)"
            return "Dayanıp direnecek misiniz (`أَتَصْبِرُونَ`, I. bab soru muzârisi 2. çoğul)"
        if '3MP' in features:
            return "Eğer direnirlerse (`يَصْبِرُوا۟`, I. bab meczûm muzâri 3. çoğul)"
        return "Kim sakınır ve direnirse (`وَيَصْبِرْ`, I. bab meczûm muzâri 3. tekil eril)"

    if root_ar == 'أ-ذ-ن':
        if lemma == '<i*on':
            return "İzni / onayı ile (`بِإِذْنِ / بِإِذْنِهِۦ / بِإِذْنِى / إِذْنِهِۦ / فَبِإِذْنِ`, masdar isim mecrûr)"
        if lemma == '>a*a`n':
            return "Açık bir duyuru ve bildirim (`وَأَذَٰنٌ`, nekre tekil masdar merfû)"
        if lemma == 'mu&a*~in':
            return "Yüksek sesle ilân eden duyurucu (`مُؤَذِّنٌۢ / مُؤَذِّنٌ`, II. bab ism-i fâil merfû)"
        if lemma == '>u*unN':
            if 'FD' in features:
                return "İki kulağında (`أُذُنَيْهِ`, ikil isim mecrûr)"
            if 'FP' in features:
                if 'ACC' in features:
                    return "Hayvanların kulaklarını (`ءَاذَانَ`, kırık çoğul isim mansûb)"
                if 'NOM' in features:
                    return "İşitecek kulakları (`ءَاذَانٌ`, kırık çoğul isim merfû)"
                return "Kulaklarında / kulaklarına (`ءَاذَانِهِم / ءَاذَانِهِمْ / ءَاذَانِنَا`, kırık çoğul isim mecrûr)"
            if 'INDEF' in features:
                return "Anlayışlı / hayra açık bir kulak (`أُذُنٌ`, tekil nekre isim merfû)"
            if 'ACC' in features:
                return "Kulağa karşılık kulağı (`وَٱلْأُذُنَ`, marife tekil isim mansûb)"
            if 'GEN' in features:
                return "Kulakla (`بِٱلْأُذُنِ`, marife tekil isim mecrûr)"
            return "Hayır kulağıdır (`أُذُنُ`, muzâf tekil isim merfû)"
        if lemma == "'aA*an":
            if '1P' in features:
                return "Sana açıkça bildirdik (`ءَاذَنَّٰكَ`, IV. bab mâzî 1. çoğul)"
            return "Size eşit biçimde duyurup bildirdim (`ءَاذَنتُكُمْ`, IV. bab mâzî 1. tekil)"
        if lemma == 'ta>a*~ana':
            return "Kesin biçimde duyurup ilân etti (`تَأَذَّنَ`, V. bab mâzî 3. tekil eril)"
        if lemma == '>a*~ana':
            if 'IMPV' in features:
                return "İnsanlar arasında açıkça ilân et (`وَأَذِّن`, II. bab emir 2. tekil eril)"
            return "Yüksek sesle duyurup bağırdı (`فَأَذَّنَ / أَذَّنَ`, II. bab mâzî 3. tekil eril)"
        if lemma == '{sota_#o*ana':
            if 'PERF' in features:
                if '3MP' in features:
                    return "Senden izin istediler (`فَٱسْتَـْٔذَنُوكَ / ٱسْتَـْٔذَنُوكَ`, X. bab mâzî 3. çoğul)"
                return "Senden / ondan izin istedi (`ٱسْتَـْٔذَنَكَ / ٱسْتَـْٔذَنَ`, X. bab mâzî 3. tekil eril)"
            if '3MP|MOOD:JUS' in features:
                return "Her girişte izin istesinler (`فَلْيَسْتَـْٔذِنُوا۟`, X. bab emir lâmlı meczûm 3. çoğul)"
            if '3MP|MOOD:SUBJ' in features:
                return "Ondan izin isteyinceye kadar (`يَسْتَـْٔذِنُوهُ`, X. bab mansûb muzâri 3. çoğul)"
            if '3MP' in features:
                return "Senden izin isteyenler (`يَسْتَـْٔذِنُونَكَ`, X. bab muzâri 3. çoğul)"
            if 'MOOD:JUS' in features:
                return "Üç vakitte sizden izin istesinler (`لِيَسْتَـْٔذِنكُمُ`, X. bab emir lâmlı meczûm 3. tekil eril)"
            return "Senden izin ister / istiyor (`يَسْتَـْٔذِنُكَ / وَيَسْتَـْٔذِنُ`, X. bab muzâri 3. tekil eril)"
        if 'PASS' in features:
            if 'PERF' in features:
                return "Savunma izni verildi (`أُذِنَ`, I. bab meçhul mâzî 3. tekil eril)"
            if 'MOOD:SUBJ' in features:
                return "Size izin verilinceye kadar / izin verilmesi için (`يُؤْذَنَ / لِيُؤْذَنَ`, I. bab meçhul mansûb muzâri 3. tekil eril)"
            return "Kendilerine izin verilmez (`يُؤْذَنُ`, I. bab meçhul muzâri 3. tekil eril)"
        if 'IMPV' in features:
            if '2MP' in features:
                return "Savaşı bilin / duyurun (`فَأْذَنُوا۟`, I. bab emir 2. çoğul)"
            return "İzin ver (`ٱئْذَن / فَأْذَن`, I. bab emir 2. tekil eril)"
        if 'PERF' in features:
            if '2MS' in features:
                return "Niçin onlara izin verdin (`أَذِنتَ`, I. bab mâzî 2. tekil eril)"
            if '3FS' in features:
                return "Rabbine kulak kesilip onay vererek uydu (`وَأَذِنَتْ`, I. bab mâzî 3. tekil dişil)"
            return "İzin verdi (`أَذِنَ`, I. bab mâzî 3. tekil eril)"
        if '1S' in features:
            return "Ben size izin vermeden (`ءَاذَنَ`, I. bab mansûb muzâri 1. tekil)"
        if 'MOOD:JUS' in features:
            return "Allah'ın izin vermediği (`يَأْذَنۢ`, I. bab meczûm muzâri 3. tekil eril)"
        return "İzin verinceye kadar (`يَأْذَنَ`, I. bab mansûb muzâri 3. tekil eril)"

    if root_ar == 'ش-د-د':
        if lemma == '{$otad~ato':
            return "Üzerine rüzgâr şiddetle bastırdı (`ٱشْتَدَّتْ`, VIII. bab mâzî 3. tekil dişil)"
        if lemma == '$adado':
            if 'IMPV' in features:
                if '2MP' in features:
                    return "Bağı sımsıkı düğümleyin (`فَشُدُّوا۟`, I. bab emir 2. çoğul)"
                return "Kalplerini sımsıkı bağla / sırtımı güçlendir (`وَٱشْدُدْ / ٱشْدُدْ`, I. bab çözülmüş mudâaf emir 2. tekil eril)"
            if 'IMPF' in features:
                return "Pazunu sımsıkı bağlayıp pekiştireceğiz (`سَنَشُدُّ`, I. bab muzâri 1. çoğul)"
            return "İktidarını / eklem bağlarını sımsıkı kurduk (`وَشَدَدْنَا / وَشَدَدْنَآ`, I. bab çözülmüş mudâaf mâzî 1. çoğul)"
        if lemma == '>a$ud~':
            return "Tam olgunluk ve sağlamlık çağına (`أَشُدَّهُۥ / أَشُدَّهُۥٓ / أَشُدَّكُمْ / أَشُدَّهُمَا`, muzâf isim mansûb)"
        if lemma == '>a$ad~':
            if (s, a) == (2, 200):
                return "Daha güçlü ve yoğun bir anışla (`أَشَدَّ`, sıfat-isim memnu' mine's-sarf atıflı mecrûr)"
            if 'GEN' in features:
                return "En şiddetli ve ağırına (`أَشَدِّ`, ism-i tafdîl mecrûr)"
            if 'ACC' in features:
                return "Daha sağlam / daha şiddetli / daha çetin (`أَشَدَّ / وَأَشَدَّ`, ism-i tafdîl mansûb)"
            return "Daha kuvvetli / daha katı / daha tesirli (`أَشَدُّ / وَأَشَدُّ`, ism-i tafdîl merfû)"
        if 'MP|NOM' in features:
            if (s, a) == (48, 29):
                return "Karşı tarafa karşı sert ve tavizsizler (`أَشِدَّآءُ`, kırık çoğul isim merfû)"
            return "Çetin / zorlu ve sağlam (`شِدَادٌ`, kırık çoğul sıfat merfû)"
        if 'MP|INDEF|ACC' in features:
            return "Yedi sağlam örülü gök (`شِدَادًا`, kırık çoğul sıfat mansûb)"
        if 'MS|GEN' in features:
            return "Çetin karşılık ve şiddetli azabın (`شَدِيدِ / ٱلشَّدِيدِ`, tekil sıfat mecrûr)"
        if 'MS|ACC' in features:
            return "O çetin azabı (`ٱلشَّدِيدَ`, marife tekil sıfat mansûb)"
        if 'INDEF|GEN' in features:
            return "Sağlam / çetin ve sıkı bir (`شَدِيدٍ`, nekre tekil sıfat mecrûr)"
        if 'INDEF|ACC' in features:
            return "Şiddetli / çetin ve yoğun bir (`شَدِيدًا`, nekre tekil sıfat mansûb)"
        if 'INDEF|NOM' in features:
            return "Çetin / sıkı ve tavizsizdir (`شَدِيدٌ / شَدِيدٌۢ / لَشَدِيدٌ`, nekre tekil isim/sıfat merfû)"
        return "Hesabı ve karşılığı çetindir (`شَدِيدُ / لَشَدِيدُ`, muzâf isim/sıfat merfû)"

    elif root_ar == 'و-ل-د':
        if lemma == 'walada':
            if 'PERF|PASS|3MS' in features:
                return "Doğurulduğu / dünyaya getirildiği (`وُلِدَ`, I. bab meçhul mâzî, 3. tekil eril)"
            if 'PERF|PASS|1S' in features:
                return "Doğurulduğum / dünyaya getirildiğim (`وُلِدتُّ`, I. bab meçhul mâzî, 1. tekil)"
            if 'PERF|3FP' in features:
                return "Onları bizzat doğuranlar (`وَلَدْنَهُمْ`, I. bab mâlûm mâzî, 3. çoğul dişil + zamir)"
            if 'PERF|3MS' in features:
                return "Doğurdu / dünyaya getirdi (`وَلَدَ`, I. bab mâlûm mâzî, 3. tekil eril)"
            if 'IMPF|PASS|3MS' in features:
                return "Doğurulmadı (`يُولَدْ`, I. bab meçhul muzârî meczûm — düşen `و` geri döner)"
            if 'IMPF|1S' in features:
                return "Ben mi doğuracağım (`ءَأَلِدُ`, I. bab mâlûm muzârî merfû, 1. tekil — baş `و` düşer)"
            if 'IMPF|3MP' in features:
                return "Doğurmazlar / dünyaya getirmezler (`يَلِدُوٓا۟`, I. bab mâlûm muzârî meczûm, 3. çoğul eril)"
            return "Doğurmadı (`يَلِدْ`, I. bab mâlûm muzârî meczûm, 3. tekil eril — baş `و` düşer)"

        if lemma == 'walad':
            if 'MP|NOM' in features:
                return "Çocukları / doğan evlatları (`أَوْلَٰدُهُمْ / أَوْلَٰدُكُمْ`, kırık çoğul eril isim merfû)"
            if 'MP|INDEF|ACC' in features:
                return "Çocuklar / çokça evlat (`أَوْلَٰدًا`, nekre kırık çoğul eril isim mansûb)"
            if 'MP|ACC' in features:
                return "Çocuklarınızı / çocuklarını (`أَوْلَٰدَهُنَّ / أَوْلَٰدَكُمْ`, kırık çoğul eril isim mansûb)"
            if 'MP|GEN' in features:
                return "Çocuklarınız / çocuklar (`أَوْلَٰدِكُمْ / ٱلْأَوْلَٰدِ`, kırık çoğul eril isim mecrûr)"
            if 'M|INDEF|ACC' in features:
                return "Bir çocuk / evlat (`وَلَدًا`, nekre tekil eril isim mansûb)"
            if 'M|INDEF|NOM' in features:
                return "Bir çocuk / evlat (`وَلَدٌ`, nekre tekil eril isim merfû)"
            if 'M|INDEF|GEN' in features:
                return "Bir çocuk / evlat (`وَلَدٍ`, nekre tekil eril isim mecrûr)"
            if 'M|NOM' in features:
                return "Çocuğu / soyu (`وَلَدُهُۥٓ`, muzâf tekil eril isim merfû)"
            return "Çocuğu sebebiyle / çocuğundan (`بِوَلَدِهَا / بِوَلَدِهِۦ / وَلَدِهِۦ`, muzâf tekil eril isim mecrûr)"

        if lemma == 'waAlid':
            if 'MD|NOM' in features:
                return "Anne ve baba (iki ebeveyn) (`ٱلْوَٰلِدَانِ`, marife ikil eril isim merfû)"
            if 'MD|GEN' in features:
                return "Anne ve babaya / iki ebeveyne (`ٱلْوَٰلِدَيْنِ / لِلْوَٰلِدَيْنِ / بِٱلْوَٰلِدَيْنِ`, marife ikil eril isim mecrûr)"
            if 'F|GEN' in features:
                return "Doğuran anneme (`بِوَٰلِدَتِى`, tekil dişil isim mecrûr + 1. tekil iyelik zamiri)"
            if 'INDEF|NOM' in features:
                return "Bir baba / doğuran (`وَالِدٌ`, nekre tekil eril ism-i fâil merfû)"
            if 'INDEF|GEN' in features:
                return "Bir babaya / doğurana (`وَوَالِدٍ`, nekre tekil eril ism-i fâil mecrûr)"
            return "Babasının / doğuranının (`وَالِدِهِۦ`, muzâf tekil eril ism-i fâil mecrûr)"

        if lemma == 'wa`liday':
            return "Anne ve babasına / iki ebeveyne (`وَٰلِدَيْهِ / وَٰلِدَيْكَ / وَٰلِدَىَّ`, ikil muzâf isim mecrûr)"

        if lemma == 'waliyd':
            if 'M|INDEF|ACC' in features:
                return "Henüz yeni doğmuş küçük çocukken (`وَلِيدًا`, nekre tekil eril isim mansûb / hâl)"
            if 'MP|INDEF|NOM' in features:
                return "Gençlikleri solmayan delikanlılar/çocuklar (`وِلْدَٰنٌ`, nekre kırık çoğul eril isim merfû)"
            if 'MP|ACC' in features:
                return "Küçük çocukları (`ٱلْوِلْدَٰنَ`, marife kırık çoğul eril isim mansûb)"
            return "Çaresiz küçük çocukların (`ٱلْوِلْدَٰنِ`, marife kırık çoğul eril isim mecrûr)"

        if lemma == 'mawoluwd':
            if 'M|GEN' in features:
                return "Kendisi için çocuk doğurulan baba (`ٱلْمَوْلُودِ`, marife mef'ûl kalıbında tekil eril isim mecrûr)"
            if s == 2:
                return "Kendisi için çocuk doğurulan baba (`مَوْلُودٌ`, nekre mef'ûl kalıbında tekil eril isim merfû)"
            return "Doğan hiçbir çocuk (`مَوْلُودٌ`, nekre mef'ûl kalıbında tekil eril isim merfû)"

        if lemma == 'wa`lidap':
            if 'F|INDEF|NOM' in features:
                return "Doğuran hiçbir anne (`وَٰلِدَةٌۢ`, nekre tekil dişil ism-i fâil merfû)"
            return "Seni doğuran annen (`وَٰلِدَتِكَ`, muzâf tekil dişil ism-i fâil mecrûr)"

        if lemma == 'wa`lida`t':
            return "Doğuran anneler (`ٱلْوَٰلِدَٰتُ`, marife cemi müennes sâlim isim merfû)"

    elif root_ar == 'د-ي-ن':
        if lemma == 'tadaAyan':
            return "Karşılıklı vadeli borç akdine girdiğinizde (`تَدَايَنتُم`, VI. bab müşâreke mâzî, 2. çoğul eril)"
        if lemma == 'yadiynu':
            return "Boyun eğip yasa edinmezler (`يَدِينُونَ`, I. bab ecvef-i yâî muzârî merfû, 3. çoğul eril)"
        if lemma == 'dayon':
            return "Vadeli bir borç / malî yükümlülükle (`دَيْنٍ / بِدَيْنٍ`, nekre tekil eril isim mecrûr)"
        if lemma == 'madiyniyn':
            if 'MP|NOM' in features:
                return "Elbette borçlandırılıp hesaba çekilecek miyiz (`لَمَدِينُونَ`, cemi müzekker sâlim ism-i mef'ûl merfû)"
            return "Hesaba çekilip borcunu ödemeye mecbur olmayanlar (`مَدِينِينَ`, cemi müzekker sâlim ism-i mef'ûl)"

        if lemma == 'diyn':
            if 'M|INDEF|ACC' in features:
                return "Bir yaşam ve itaat düzeni olarak (`دِينًا`, nekre tekil eril isim mansûb — temyiz/hâl)"
            if 'M|GEN' in features:
                if (s, a) in ((1, 4), (15, 35), (26, 82), (37, 20), (38, 78), (51, 12), (56, 56), (70, 26), (74, 46), (82, 15), (82, 17), (82, 18), (83, 11)):
                    return "Hesap ve denk karşılık gününün (`يَوْمِ ٱلدِّينِ`, marife muzâfun ileyh tekil isim mecrûr)"
                if (s, a) in ((82, 9), (95, 7), (107, 1)):
                    return "Hesap ve denk karşılık düzenini (`بِٱلدِّينِ`, marife harf-i cerrli isim mecrûr)"
                if (s, a) == (10, 104):
                    return "Benim bağlı olduğum itaat ve yaşam sistemimden (`مِن دِينِى`, 1. tekil iyelik zamirli mecrûr)"
                if (s, a) in ((10, 105), (30, 30), (30, 43)):
                    return "Dosdoğru itaat ve fıtrat düzenine (`لِلدِّينِ`, lâm edatlı marife isim mecrûr)"
                if (s, a) in ((2, 217), (3, 24), (4, 171), (5, 3), (5, 54), (5, 77), (9, 12), (49, 16)):
                    return "Bağlı oldukları/olduğunuz itaat ve yaşam düzeninden (`دِينِكُمْ / دِينِهِۦ / دِينِهِمْ`, zamire muzâf tekil mecrûr)"
                return "İtaat, yasa ve yaşam düzeninde/düzenine (`ٱلدِّينِ`, harf-i cerrli marife tekil isim mecrûr)"
            if features.endswith('|GEN'):
                if (s, a) == (12, 76):
                    return "Kralın yargı ve yasa sisteminde (`فِى دِينِ`, muzâf tekil isim mecrûr)"
                if (s, a) == (24, 2):
                    return "Belirlenen ceza ve yargı ölçüsünde (`فِى دِينِ`, muzâf tekil isim mecrûr)"
                return "Hak ve itaat düzeni (`دِينِ`, muzâf tekil isim mecrûr)"
            if 'M|ACC' in features:
                if (s, a) in ((51, 6), (24, 25)):
                    return "Kesinleşmiş hesap ve denk karşılığı (`ٱلدِّينَ / دِينَهُمُ`, tekil eril isim mansûb)"
                if (s, a) in ((7, 29), (10, 22), (29, 65), (31, 32), (39, 2), (39, 11), (40, 14), (40, 65), (98, 5)):
                    return "İtaat ve yöneliş bağını yalnız O'na arındırarak (`ٱلدِّينَ`, marife mef'ûl bih mansûb)"
                if (s, a) in ((2, 132), (3, 19), (42, 13)):
                    return "Bilinçli teslimiyet ve uyum sistemini (`ٱلدِّينَ`, marife isim mansûb)"
                return "Yaşam ve itaat düzenini (`دِينَهُمْ / دِينَكُمْ / دِينَ`, muzâf mef'ûl bih mansûb)"
            if (s, a) == (109, 6):
                return "Sizin bağlı olduğunuz yol ve benim bağlı olduğum sistem (`دِينُكُمْ / دِينِ`, muzâf mübteda/haber merfû — 1. tekil `ى` yazıda düşer)"
            if (s, a) == (39, 14):
                return "Yöneliş ve itaat bağımı (`دِينِى`, 1. tekil iyelik zamirli isim)"
            if (s, a) == (8, 49):
                return "Bağlı oldukları sistem (`دِينُهُمْ`, muzâf fâil merfû)"
            if (s, a) == (98, 5):
                return "Dosdoğru ayakta duran yaşam yasası (`دِينُ`, muzâf haber merfû)"
            return "İtaat, hüküm ve uyum düzeni (`ٱلدِّينُ`, marife tekil isim merfû)"

    elif root_ar == 'ص-ح-ب':
        if lemma == 'yuSoHabu':
            return "Bizden yana sahiplenilip korunmazlar (`يُصْحَبُونَ`, I. bab meçhul muzârî merfû, 3. çoğul eril)"
        if lemma == 'tuSa`Hibo':
            if 'IMPV' in features:
                return "İkisine güzelce arkadaşlık et (`وَصَاحِبْهُمَا`, III. bab emir, 2. tekil eril + ikil zamir)"
            return "Bana yol arkadaşlığı etme (`تُصَٰحِبْنِى`, III. bab muzârî meczûm, 2. tekil eril + kaynaştırma `ن` + 1. tekil)"
        if lemma == 'SaY`Hib':
            return "Ey iki zindan arkadaşım (`يَٰصَىٰحِبَىِ`, nida + ikil muzâf isim — `ى` kürsülü çekerle yazılır)"
        if lemma == 'Sa`Hibap':
            if 'F|INDEF|NOM' in features:
                return "Bir dişi ömür eşi (`صَٰحِبَةٌ`, nekre tekil dişil isim merfû)"
            if 'F|INDEF|ACC' in features:
                return "Bir dişi ömür eşi (`صَٰحِبَةً`, nekre tekil dişil isim mansûb)"
            return "Hayat yoldaşı olan eşinden (`وَصَٰحِبَتِهِۦ`, zamire muzâf tekil dişil isim mecrûr)"
        if lemma == 'SaAHib':
            if 'NOM' in features:
                return "Yakın arkadaşınız / arkadaşı (`صَاحِبُهُۥ / صَاحِبُكُمْ`, zamire muzâf ism-i fâil merfû)"
            if 'ACC' in features:
                return "İçlerinden çağırdıkları adamlarını/arkadaşlarını (`صَاحِبَهُمْ`, zamire muzâf ism-i fâil mansûb)"
            if s == 4:
                return "Hemen yanı başındaki yol/meclis arkadaşına (`وَٱلصَّاحِبِ`, marife tekil eril ism-i fâil mecrûr)"
            if s == 68:
                return "Balığın yoldaşı / yanındaki gibi (`كَصَاحِبِ`, muzâf ism-i fâil mecrûr)"
            return "Yakın arkadaşlarına / arkadaşının (`بِصَاحِبِهِم / لِصَٰحِبِهِۦ / بِصَاحِبِكُم`, zamire muzâf ism-i fâil mecrûr)"
        if lemma == '>aSoHa`b':
            if 'MP|INDEF|NOM' in features:
                return "Kendisine seslenen yol arkadaşları (`أَصْحَٰبٌ`, nekre kırık çoğul isim merfû)"
            if 'MP|NOM' in features:
                return "Sürekli eşlik edenleri / ayrılmaz ehli (`أَصْحَٰبُ / وَأَصْحَٰبُ / فَأَصْحَٰبُ`, kırık çoğul muzâf merfû)"
            if 'MP|ACC' in features:
                return "Ayrılmaz eşlikçilerini / halkını (`أَصْحَٰبَ / وَأَصْحَٰبَ`, kırık çoğul muzâf mansûb)"
            return "Sürekli beraberindeki ehlinin / yoldaşlarının (`أَصْحَٰبِ / لِأَصْحَٰبِ / بِأَصْحَٰبِ`, kırık çoğul muzâf mecrûr)"

    elif root_ar == 'أ-ن-س':
        if lemma == '<insiy~':
            return "Kendisiyle konuşulup ünsiyet kurulacak bir insan (`إِنسِيًّا`, nekre tekil eril nisbet ismi mansûb)"
        if lemma == 'musota_#onisiyn':
            return "Sözlü sohbete ve ünsiyete dalarak oyalananlar (`مُسْتَـْٔنِسِينَ`, X. bab ism-i fâil cemi müzekker sâlim — `ـٔ` hemze yazımı)"
        if lemma == 'tasota>onisu':
            return "Seslenip yabancılığı gidererek onay alıncaya kadar (`تَسْتَأْنِسُوا۟`, X. bab muzârî mansûb, 2. çoğul eril)"
        if lemma == "'aAnasa":
            if '1S' in features:
                return "Açıkça gördüm / uzaktan fark ettim (`ءَانَسْتُ`, IV. bab mâzî, 1. tekil)"
            if '2MP' in features:
                return "Onlarda olgunluk sezdiğinizde / gözlemlediğinizde (`ءَانَسْتُم`, IV. bab mâzî, 2. çoğul eril)"
            return "Uzaktan açıkça gördü / seçti (`ءَانَسَ`, IV. bab mâzî, 3. tekil eril)"
        if lemma == '<ins':
            if 'M|INDEF|NOM' in features:
                return "Hiçbir görünür insan (`إِنسٌ`, nekre cins ismi merfû)"
            if 'M|NOM' in features:
                return "Görünür insan zümresi (`ٱلْإِنسُ`, marife cins ismi merfû)"
            if 'M|ACC' in features:
                return "Görünür insan türünü (`وَٱلْإِنسَ`, marife cins ismi mansûb)"
            return "Görünür insan zümresinden/türünün (`ٱلْإِنسِ / وَٱلْإِنسِ`, marife cins ismi mecrûr)"
        if lemma == '<insa`n':
            if 'MP|INDEF|NOM' in features:
                return "İnsanlar / ayrı duran topluluk (`أُنَاسٌ`, nekre kırık çoğul isim merfû)"
            if 'MP|INDEF|GEN' in features:
                return "İnsan boyunun / topluluğunun (`أُنَاسٍ / أُنَاسٍۭ`, nekre kırık çoğul isim mecrûr)"
            if 'MP|ACC' in features:
                return "Kalabalık insan topluluklarını (`وَأَنَاسِىَّ`, kırık çoğul isim mansûb)"
            if 'M|INDEF|GEN' in features:
                return "Her bir insanın (`إِنسَٰنٍ`, nekre tekil eril isim mecrûr)"
            if 'M|NOM' in features:
                return "İnsan (`ٱلْإِنسَٰنُ`, marife tekil eril isim merfû)"
            if 'M|ACC' in features:
                return "İnsanı / şüphesiz insan (`ٱلْإِنسَٰنَ`, marife tekil eril isim mansûb)"
            return "İnsana / insanın (`لِلْإِنسَٰنِ / ٱلْإِنسَٰنِ`, marife tekil eril isim mecrûr)"

    elif root_ar == 'ق-ر-ب':
        if lemma == 'yaqorabu':
            if '2D' in features:
                return "İkiniz yaklaşmayın (`تَقْرَبَا`, I. bab muzârî meczûm nehy, 2. ikil)"
            if '3MP' in features:
                return "Yaklaşmasınlar (`يَقْرَبُوا۟`, I. bab muzârî meczûm nehy, 3. çoğul eril)"
            if (s, a) == (12, 60):
                return "Bana yaklaşmayın (`تَقْرَبُونِ`, I. bab muzârî meczûm nehy + kaynaştırma `ن` + hazifli `ى`)"
            return "Yaklaşmayın (`تَقْرَبُوا۟ / تَقْرَبُوهَا / تَقْرَبُوهُنَّ`, I. bab muzârî meczûm nehy, 2. çoğul eril)"
        if lemma == 'qar~aba':
            if '3MD' in features:
                return "İkisi yaklaştırıp takdim ettiler (`قَرَّبَا`, II. bab mâzî, 3. ikil eril)"
            if '1P' in features:
                return "Onu yaklaştırdık (`وَقَرَّبْنَٰهُ`, II. bab mâzî, 1. çoğul + zamir)"
            if '3FS' in features:
                return "Sizi yaklaştıracak değildir (`تُقَرِّبُكُمْ`, II. bab muzârî merfû, 3. tekil dişil + zamir)"
            if '3MP' in features:
                return "Bizi yaklaştırsınlar diye (`لِيُقَرِّبُونَآ`, II. bab muzârî mansûb, 3. çoğul eril + zamir)"
            return "Onu (yemeği) önlerine yaklaştırdı (`فَقَرَّبَهُۥٓ`, II. bab mâzî, 3. tekil eril + zamir)"
        if lemma == '{qotaraba':
            if 'IMPV' in features:
                return "Yaklaş / yakınlık kur (`وَٱقْتَرِب`, VIII. bab emir, 2. tekil eril)"
            if '3FS' in features:
                return "İyice yaklaştı (`ٱقْتَرَبَتِ`, VIII. bab mâzî, 3. tekil dişil)"
            return "Yaklaştı / kapıya dayandı (`ٱقْتَرَبَ`, VIII. bab mâzî, 3. tekil eril)"
        if lemma == 'quruba`t':
            return "Yakınlaşma basamakları / vesileleri (`قُرُبَٰتٍ`, nekre cemi müennes sâlim isim — `9:99` hapaxı)"
        if lemma == 'qurobap':
            return "Gerçek bir yakınlaşma vesilesidir (`قُرْبَةٌ`, nekre tekil dişil isim merfû — `9:99` hapaxı)"
        if lemma == 'maqorabap':
            return "Soy ve yakınlık bağı bulunan (`مَقْرَبَةٍ`, nekre mîmli isim mecrûr — `90:15` hapaxı)"
        if lemma == 'qurobaAn':
            if 'GEN' in features:
                return "Bir yakınlaşma takdimi / sunusuyla (`بِقُرْبَانٍ`, nekre tekil eril isim mecrûr)"
            if s == 5:
                return "İki ayrı sunu / yakınlık takdimi (`قُرْبَانًا`, nekre tekil eril isim mansûb)"
            return "Yakınlaşma aracı olarak (`قُرْبَانًا`, nekre tekil eril isim mansûb — hâl)"
        if lemma == 'muqar~abuwn':
            if 'NOM' in features:
                return "En yakına çekilmiş seçkinler (`ٱلْمُقَرَّبُونَ`, II. bab ism-i mef'ûl cemi müzekker sâlim merfû)"
            return "Yakına alınmış seçkinlerden (`ٱلْمُقَرَّبِينَ`, II. bab ism-i mef'ûl cemi müzekker sâlim mecrûr)"
        if lemma == 'qurobaY`':
            if 'ACC' in features:
                return "Yakınlık bağı sahipleri (`قُرْبَىٰ`, tekil dişil maksûr isim — mahallen mansûb)"
            if 'NOM' in features:
                return "Kan ve yakınlık bağı sahibinin/sahibine (`ٱلْقُرْبَىٰ / قُرْبَىٰٓ`, tekil dişil maksûr isim)"
            return "Yakınlık bağı / hısımlık (`ٱلْقُرْبَىٰ / قُرْبَىٰ`, tekil dişil maksûr isim mecrûr)"
        if lemma == '>aqorab':
            if 'MP|NOM' in features:
                return "Ve en yakın hısımların (`وَٱلْأَقْرَبُونَ`, çoğul ism-i tafdîl merfû)"
            if 'MP|GEN' in features:
                return "Ve en yakın hısımlara (`وَٱلْأَقْرَبِينَ`, çoğul ism-i tafdîl mecrûr)"
            if 'MP|ACC' in features:
                return "En yakın olan topluluğunu (`ٱلْأَقْرَبِينَ`, çoğul ism-i tafdîl mansûb)"
            if 'MS|NOM' in features:
                return "Daha yakındır / en yakın olanı (`أَقْرَبُ`, tekil eril ism-i tafdîl merfû)"
            if 'MS|ACC' in features:
                return "Daha yakın olarak (`أَقْرَبَ / وَأَقْرَبَ`, tekil eril ism-i tafdîl mansûb)"
            return "Daha yakın olana (`لِأَقْرَبَ`, gayr-ı munsarif ism-i tafdîl mecrûr — fethalı)"
        if lemma == 'qariyb':
            if 'NOM' in features:
                return "Yakındır / yakın mıdır (`قَرِيبٌ / أَقَرِيبٌ`, sıfat-ı müşebbehe tekil eril merfû)"
            if 'ACC' in features:
                return "Yakın / pek yakında (`قَرِيبًا`, sıfat-ı müşebbehe tekil eril mansûb)"
            return "Yakın (bir zaman/yerden) (`قَرِيبٍ / بِقَرِيبٍ`, sıfat-ı müşebbehe tekil eril mecrûr)"

    elif root_ar == 'ب-غ-ي':
        if lemma == 'yan[bagiY':
            return "Yaraşır / uygun düşer (`يَنۢبَغِى`, VII. bab muzârî merfû, 3. tekil eril)"
        if lemma == 'bagiy~':
            return "İffet sınırını ihlal etmiş kadın (`بَغِيًّا`, sıfat-ı müşebbehe nekre mansûb)"
        if lemma == "bigaA^'":
            return "İffet dışı fuhşa/kazanca (`ٱلْبِغَآءِ`, marife I. bab mastar mecrûr)"
        if lemma == 'baAg':
            return "Keyfî taşkınlık ve arzu güden (`بَاغٍ`, nâkıs ism-i fâil merfû/mecrûr — `ى` düşerek tenvin alır)"
        if lemma == 'bagoy':
            if 'M|INDEF|ACC' in features:
                return "Haksız taşkınlık / çekişme yüzünden (`بَغْيًا / بَغْيًۢا`, nekre I. bab mastar mansûb — mef'ûlün leh)"
            if 'M|NOM' in features:
                return "Taşkınlıkları / haksız saldırı (`بَغْيُكُمْ / ٱلْبَغْىُ`, I. bab mastar merfû)"
            if 'M|ACC' in features:
                return "Ve haksız taşkınlığı (`وَٱلْبَغْىَ`, marife I. bab mastar mansûb)"
            return "Taşkınlıklarından ötürü / haksız taşkınlıktan (`بِبَغْيِهِمْ / وَٱلْبَغْىِ`, I. bab mastar mecrûr)"
        if lemma == "{botigaA^'":
            if 'M|NOM' in features:
                return "Ve (lütuftan) aramanız (`وَٱبْتِغَآؤُكُم`, VIII. bab mastar + zamir merfû)"
            if 'M|GEN' in features:
                return "Arayıp takip etmede (`ٱبْتِغَآءِ`, VIII. bab mastar mecrûr)"
            return "Aramak / elde etmek amacıyla (`ٱبْتِغَآءَ / وَٱبْتِغَآءَ`, VIII. bab mastar mansûb — mef'ûlün leh)"
        if lemma == 'bagaY`':
            if 'PERF|PASS' in features:
                return "Haksız saldırıya uğradı (`بُغِىَ`, I. bab meçhul mâzî, 3. tekil eril)"
            if 'PERF' in features and '3MP' in features:
                return "Elbette yeryüzünde azıp taşarlardı (`لَبَغَوْا۟`, I. bab mâzî, 3. çoğul eril)"
            if 'PERF' in features and '3FS' in features:
                return "Haksız yere saldırdı (`بَغَتْ`, I. bab mâzî, 3. tekil dişil)"
            if 'PERF' in features:
                return "Sınırı taşıp haksız baskı kurdu (`بَغَىٰ / فَبَغَىٰ`, I. bab mâzî, 3. tekil eril)"
            if '3MD' in features:
                return "Birbirinin sınırına taşmazlar (`يَبْغِيَانِ`, I. bab muzârî merfû, 3. ikil)"
            if '3FS' in features:
                return "Saldırısını sürdüreni (`تَبْغِى`, I. bab muzârî merfû, 3. tekil dişil)"
            if '2MP|MOOD:JUS' in features:
                return "Aleyhlerine bahane/yol aramayın (`تَبْغُوا۟`, I. bab muzârî meczûm nehy, 2. çoğul eril)"
            if '2MS|MOOD:JUS' in features:
                return "Bozgunculuk arama/çıkarma (`تَبْغِ`, I. bab muzârî meczûm nehy, 2. tekil eril — `ى` düşer)"
            if '3MP' in features:
                return "Taşkınlık yaparlar / eğrilik veya başka merci ararlar (`يَبْغُونَ / وَيَبْغُونَهَا / يَبْغُونَكُمُ`, I. bab muzârî merfû, 3. çoğul eril)"
            if '2MP' in features:
                return "Eğriltmek istiyorsunuz (`تَبْغُونَهَا / وَتَبْغُونَهَا`, I. bab muzârî merfû, 2. çoğul eril)"
            if '1S' in features:
                return "Mı arayayım (`أَبْغِى / أَبْغِيكُمْ`, I. bab muzârî merfû, 1. tekil)"
            if '1P' in features:
                return "Aradığımız / başka ne isteyelim (`نَبْغِى / نَبْغِ`, I. bab muzârî merfû, 1. çoğul — `18:64`te `ى` yazıda düşer)"
            return "Elbette birbirinin hakkına taşar (`لَيَبْغِى`, I. bab muzârî merfû, 3. tekil eril)"
        if lemma == '{botagaY`':
            if 'IMPV' in features and '2MP' in features:
                return "Emekle arayın / isteyin (`وَٱبْتَغُوا۟ / فَٱبْتَغُوا۟`, VIII. bab emir, 2. çoğul eril)"
            if 'IMPV' in features:
                return "Ara / yönünü belirle (`وَٱبْتَغِ`, VIII. bab emir, 2. tekil eril — `ى` düşer)"
            if 'PERF' in features and '3MP' in features:
                return "Aradılar / yol ararlardı (`ٱبْتَغَوُا۟ / لَّٱبْتَغَوْا۟`, VIII. bab mâzî, 3. çoğul eril)"
            if 'PERF' in features and '2MS' in features:
                return "Yeniden yanına almak istediğin (`ٱبْتَغَيْتَ`, VIII. bab mâzî, 2. tekil eril)"
            if 'PERF' in features:
                return "Ötesini aradıysa (`ٱبْتَغَىٰ`, VIII. bab mâzî, 3. tekil eril)"
            if '3MS|MOOD:JUS' in features:
                return "Kim ararsa (`يَبْتَغِ`, VIII. bab muzârî meczûm, 3. tekil eril — `ى` düşer)"
            if '2MS|MOOD:SUBJ' in features:
                return "Arayıp bulabilsen (`تَبْتَغِىَ`, VIII. bab muzârî mansûb, 2. tekil eril)"
            if '2MP|MOOD:SUBJ' in features:
                return "Arayasınız diye (`لِتَبْتَغُوا۟ / تَبْتَغُوا۟`, VIII. bab muzârî mansûb, 2. çoğul eril)"
            if '3MP' in features:
                return "Ararlar / mı arıyorlar (`يَبْتَغُونَ / أَيَبْتَغُونَ`, VIII. bab muzârî merfû, 3. çoğul eril)"
            if '2MP' in features:
                return "Arayarak (`تَبْتَغُونَ`, VIII. bab muzârî merfû, 2. çoğul eril)"
            if '2MS' in features:
                return "Hoşnutluk arayarak (`تَبْتَغِى`, VIII. bab muzârî merfû, 2. tekil eril)"
            if '1S' in features:
                return "Mı arayayım (`أَبْتَغِى`, VIII. bab muzârî merfû, 1. tekil)"
            return "Aramayız / peşine düşmeyiz (`نَبْتَغِى`, VIII. bab muzârî merfû, 1. çoğul)"

    elif root_ar == 'أ-خ-و':
        if lemma == '<ixowapN':
            if 'P|INDEF|NOM' in features:
                return "Erkek ve kız kardeşler / sıkı kardeşlerdir (`إِخْوَةٌ`, nekre kırık çoğul isim merfû)"
            if 'P|INDEF|ACC' in features:
                return "Çokça erkek ve kız kardeşler (`إِخْوَةً`, nekre kırık çoğul isim mansûb)"
            if 'P|NOM' in features:
                return "Yûsuf'un kardeşleri / öz kardeşlerim (`إِخْوَةُ / إِخْوَتِىٓ`, muzâf kırık çoğul isim)"
            return "Kardeşlerine / kardeşleriyle (`إِخْوَتِكَ / إِخْوَتِهِۦٓ`, zamire muzâf kırık çoğul mecrûr)"

        if lemma == '>uxot':
            if 'FD|GEN' in features:
                return "İki kız kardeşi (`ٱلْأُخْتَيْنِ`, marife ikil dişil isim mecrûr)"
            if 'FP|NOM' in features:
                return "Ve kız kardeşleriniz (`وَأَخَوَٰتُكُمْ`, çoğul dişil isim merfû — yazıda elif hazifli)"
            if 'FP|GEN' in features:
                return "Kız kardeşlerinizin / kız kardeşlerinin (`أَخَوَٰتِكُمْ / أَخَوَٰتِهِنَّ`, çoğul dişil isim mecrûr — yazıda elif hazifli)"
            if 'FS|INDEF|NOM' in features:
                return "Bir kız kardeşi (`أُخْتٌ`, nekre tekil dişil isim merfû)"
            if 'FS|NOM' in features:
                return "Kız kardeşin (`أُخْتُكَ`, zamire muzâf tekil dişil isim merfû)"
            if 'FS|ACC' in features:
                return "Benzerini / ey kardeşi (`أُخْتَهَا / يَٰٓأُخْتَ`, tekil dişil isim mansûb)"
            return "Kız kardeşin / kız kardeşine / benzerinden (`ٱلْأُخْتِ / لِأُخْتِهِۦ / أُخْتِهَا`, tekil dişil isim mecrûr)"

        if lemma == '>ax':
            if 'MD|NOM' in features:
                return "İki kardeşinizin (`أَخَوَيْكُمْ`, ikil + `كُمْ`, `بَيْنَ` ardında mecrûr)"
            if 'MP|INDEF|ACC' in features:
                return "Gönülden kardeşler olarak (`إِخْوَٰنًا`, nekre kırık çoğul isim mansûb — yazıda elif hazifli)"
            if 'MP|NOM' in features:
                return "Kardeşleriniz / kardeşleri (`إِخْوَٰنُكُمْ / إِخْوَٰنُهُمْ / إِخْوَٰنُ`, kırık çoğul merfû — yazıda elif hazifli)"
            if 'MP|ACC' in features:
                return "Kardeşlerinizi / yoldaş kardeşleri (`إِخْوَٰنَكُمْ / إِخْوَٰنَ / إِخْوَٰنَهُمْ`, kırık çoğul mansûb — yazıda elif hazifli)"
            if 'MP|GEN' in features:
                return "Kardeşlerine / kardeşlerinizin (`إِخْوَٰنِهِمْ / إِخْوَٰنِكُمْ / إِخْوَٰنِهِنَّ`, kırık çoğul mecrûr — yazıda elif hazifli)"
            if 'MS|INDEF|NOM' in features:
                return "Bir erkek kardeşi (`أَخٌ`, nekre tekil eril isim merfû)"
            if 'MS|INDEF|GEN' in features:
                return "Bir erkek kardeşinizi (`بِأَخٍ`, nekre tekil eril isim mecrûr)"
            if 'MS|ACC' in features:
                if s in (5, 20):
                    return "Erkek kardeşimi / kardeşim (`أَخِى`, 1. tekil iyelik zamirli tekil isim)"
                return "Kardeşlerini / kardeşini (`أَخَاهُمْ / أَخَاهُ / أَخَا`, Esmâ-i Hamse `ا` ile mansûb)"
            if 'MS|GEN' in features:
                return "Kardeşinin / kardeşine / öz kardeşinden (`أَخِيهِ / لِأَخِيهِ / أَخِى / بِأَخِيكَ`, `ى` ile mecrûr)"
            if (s, a) == (12, 69):
                return "Kardeşini / senin öz kardeşin (`أَخَاهُ / أَخُوكَ`, Esmâ-i Hamse mansûb ve `و` ile merfû)"
            if (s, a) in ((12, 8), (20, 42), (26, 106), (26, 124), (26, 142), (26, 161)):
                return "Kardeşi / kardeşin / soydaş kardeşleri (`أَخُوهُ / أَخُوكَ / أَخُوهُمْ`, Esmâ-i Hamse `و` ile merfû)"
            if (s, a) in ((5, 31), (12, 90), (28, 34), (38, 23)):
                return "Kardeşimin / öz kardeşim (`أَخِى`, 1. tekil iyelik zamirli tekil isim)"
            return "Soydaş/öz kardeşlerini / kardeşini (`أَخَاهُمْ / أَخَاهُ / أَخَانَا`, Esmâ-i Hamse `ا` ile mansûb)"

    elif root_ar == 'ح-ب-ب':
        if lemma == 'Hab~aba':
            return "Gönlünüze sevdirdi / bağladı (`حَبَّبَ`, II. bab mâzî, 3. tekil eril)"
        if lemma == 'maHab~ap':
            return "Derin bir sevgi / gönül bağı (`مَحَبَّةً`, nekre mîmli mastar mansûb — `20:39` hapaxı)"
        if lemma == '>aHib~a`^&':
            return "Ve O'nun sevgili dostları (`وَأَحِبَّٰٓؤُهُۥ`, kırık çoğul isim merfû — hemze `و` üzerinde `وأحبؤه`)"
        if lemma == '{sotaHab~u':
            if 'PERF' in features:
                return "Tercih edip üstün tuttular (`ٱسْتَحَبُّوا۟ / فَٱسْتَحَبُّوا۟`, X. bab mâzî, 3. çoğul eril)"
            return "Tercih edip severler (`يَسْتَحِبُّونَ`, X. bab muzârî merfû, 3. çoğul eril)"
        if lemma == '>aHab~':
            if 'ACC' in features:
                return "Daha sevgili / öncelikli (`أَحَبَّ`, ism-i tafdîl mansûb)"
            return "Daha sevgili / daha yakın (`أَحَبُّ`, ism-i tafdîl merfû)"
        if lemma == 'Hab~ap':
            return "Bir tek tohum / hardal tanesinin (`حَبَّةٍ`, nekre tekil dişil birim ismi mecrûr)"
        if lemma == 'Hab~':
            if 'M|NOM' in features:
                return "Ve daneler / başaklı tahıl (`وَٱلْحَبُّ`, marife cins ismi merfû)"
            if 'M|GEN' in features:
                return "Daneyi / tohumu (`ٱلْحَبِّ`, marife cins ismi mecrûr)"
            if 'M|INDEF|ACC' in features:
                return "Daneler / ekin tohumu (`حَبًّا`, nekre cins ismi mansûb)"
            return "Ve biçilen ekin danesini (`وَحَبَّ`, muzâf cins ismi mansûb)"
        if lemma == 'Hub~':
            if 'M|NOM' in features:
                return "Şiddetli tutkusu / sevgisi (`حُبُّ`, muzâf mastar merfû)"
            if 'M|INDEF|ACC' in features:
                return "Sevgi bakımından / aşkla / aşırı sevgiyle (`حُبًّا`, nekre mastar mansûb)"
            if 'M|ACC' in features:
                return "İyi cins mal/at sevgisini (`حُبَّ`, muzâf mastar mansûb)"
            return "Sevgisine rağmen / sevgisi gibi / mal tutkusuyla (`كَحُبِّ / حُبِّهِۦ / لِحُبِّ`, mastar mecrûr)"
        if lemma == '>aHobabo':
            if '3MS|MOOD:JUS' in features:
                return "Sizi sever (`يُحْبِبْكُمُ`, IV. bab mudâaf meczûm — şart cevabında idğam çözülür)"
            if '2MP|MOOD:SUBJ' in features:
                return "Sevesiniz (`تُحِبُّوا۟`, IV. bab muzârî mansûb, 2. çoğul eril)"
            if 'PERF' in features and '1S' in features:
                return "Elbette sevdim / kaptırdım (`أَحْبَبْتُ`, IV. bab mâzî, 1. tekil — idğam çözülür)"
            if 'PERF' in features and '2MS' in features:
                return "Sevdiğin / gönül verdiğin (`أَحْبَبْتَ`, IV. bab mâzî, 2. tekil eril — idğam çözülür)"
            if '1S' in features:
                return "Sevmem / gönülden bağlanmam (`أُحِبُّ`, IV. bab muzârî merfû, 1. tekil)"
            if '3MS' in features:
                return "Sever / onaylayıp sahip çıkar (`يُحِبُّ / أَيُحِبُّ / يُحِبُّهُمْ`, IV. bab muzârî merfû, 3. tekil eril)"
            if '2MP' in features:
                return "Seversiniz / arzuluyorsunuz (`تُحِبُّونَ / تُحِبُّونَهَا / تُحِبُّونَهُمْ`, IV. bab muzârî merfû, 2. çoğul eril)"
            return "Severler (`يُحِبُّونَ / يُحِبُّونَهُمْ / يُحِبُّونَكُمْ`, IV. bab muzârî merfû, 3. çoğul eril)"

    elif root_ar == 'س-ب-ح':
        if lemma == 'suboHa`n':
            if s == 17 and a == 93:
                return "Her eksiklikten uzak ve aşkındır (`سُبْحَانَ`, aşkınlık mastarı mansûb — 41 geçiş içinde tam elif yazımlı tek örnek)"
            return "Her eksiklikten uzak ve aşkındır (`سُبْحَٰنَ / سُبْحَٰنَكَ / سُبْحَٰنَهُۥ`, hazifli elif yazımlı aşkınlık mastarı mansûb)"
        if lemma == 'tasobiyH':
            return "Aşkınlıkla arındırma / tesbîh okuyuşu (`تَسْبِيحَهُمْ / وَتَسْبِيحَهُۥ`, II. bab mastar mansûb + zamir)"
        if lemma == 'saboH':
            if s == 73 and a == 7:
                return "Engin meşguliyet / gündüz akışı içinde ilerleyiş (`سَبْحًا`, I. bab belirsiz mastar mansûb)"
            return "Hızla yüzüşle / engin akışla (`سَبْحًا`, I. bab mef'ûl-i mutlak, belirsiz mastar mansûb)"
        if lemma == "s~a`biHa`t":
            return "Yüzerek akıp gidenler / yörüngede süzülenler (`وَٱلسَّٰبِحَٰتِ`, I. bab ism-i fâil dişil çoğul mecrûr)"
        if lemma == 'yasobaHu':
            return "Yüzerler / yörüngede akıp süzülürler (`يَسْبَحُونَ`, I. bab muzârî merfû, 3. çoğul eril)"
        if lemma == 'musab~iHuwn':
            if 'NOM' in features:
                return "Aşkınlığıyla anıp uzak tutanlarız (`ٱلْمُسَبِّحُونَ`, II. bab ism-i fâil merfû çoğul eril)"
            if 'GEN' in features:
                return "Aşkınlığıyla anıp uzak tutanlardan (`ٱلْمُسَبِّحِينَ`, II. bab ism-i fâil mecrûr çoğul eril)"
            return "Aşkınlığıyla anıp arındıranlar (`ٱلْمُسَبِّحُونَ / ٱلْمُسَبِّحِينَ`, II. bab ism-i fâil çoğul eril)"
        if lemma == 'sab~aHa':
            if 'IMPV' in features:
                if '2MP' in features:
                    return "Aşkınlığıyla anın / arındırın (`سَبِّحُوا / وَسَبِّحُوهُ`, II. bab emir, 2. çoğul eril)"
                return "Aşkınlığıyla an / kusursuzlukla yücelt (`سَبِّحْ / فَسَبِّحْ / وَسَبِّحْ / وَسَبِّحْهُ / فَسَبِّحْهُ`, II. bab emir, 2. tekil eril)"
            if 'PERF' in features:
                if '3MP' in features:
                    return "Aşkınlığıyla andılar / kusurdan uzak tuttular (`سَبَّحُوا`, II. bab mâzî, 3. çoğul eril)"
                return "Aşkınlığıyla andı / bütün varlığıyla yöneldi (`سَبَّحَ`, II. bab mâzî, 3. tekil eril)"
            if '3MS' in features:
                return "Aşkınlığıyla anar / yüceltir (`يُسَبِّحُ / وَيُسَبِّحُ`, II. bab muzârî merfû, 3. tekil eril)"
            if '3FS' in features:
                return "Aşkınlığıyla anar / kusurdan uzak tutar (`تُسَبِّحُ`, II. bab muzârî merfû, 3. tekil dişil)"
            if '3MP' in features:
                return "Aşkınlığıyla anarlar (`يُسَبِّحُونَ / وَيُسَبِّحُونَهُۥ`, II. bab muzârî merfû, 3. çoğul eril)"
            if '3FP' in features:
                return "Aşkınlığıyla anarlar / eşlik ederek yönelirler (`يُسَبِّحْنَ`, II. bab muzârî, 3. çoğul dişil)"
            if '2MP' in features:
                if 'MOOD:SUBJ' in features:
                    return "O'nu aşkınlığıyla anasınız diye (`وَتُسَبِّحُوهُ`, II. bab muzârî mansûb, 2. çoğul eril)"
                return "Aşkınlığıyla anıyordunuz (`تُسَبِّحُونَ`, II. bab muzârî merfû, 2. çoğul eril)"
            if '1P' in features:
                if 'MOOD:SUBJ' in features:
                    return "Seni aşkınlıkla analım diye (`نُسَبِّحَكَ`, II. bab muzârî mansûb, 1. çoğul)"
                return "Seni aşkınlıkla anarız / arındırırız (`نُسَبِّحُ`, II. bab muzârî merfû, 1. çoğul)"

    elif root_ar == 'ل-ي-ل':
        if lemma == 'layolap':
            if pos == 'T':
                return "Öz denetim gecesi boyunca (`لَيْلَةَ`, belirli muzâf zaman zarfı mansûb, tekil dişil)"
            if 'INDEF' in features and 'ACC' in features:
                return "Sayılı birim gece (`لَيْلَةً`, belirsiz temyiz/zarf mansûb, tekil dişil)"
            if 'INDEF' in features and 'GEN' in features:
                return "Mübarek bir gecede (`لَيْلَةٍ`, harf-i cerr ile belirsiz mecrûr, tekil dişil)"
            if 'GEN' in features:
                return "Kadir gecesinde (`لَيْلَةِ`, harf-i cerr ile muzâf mecrûr, tekil dişil)"
            if 'NOM' in features:
                return "Kadir gecesi (`لَيْلَةُ`, merfû tekil dişil)"
        if lemma == 'layol':
            if pos == 'T':
                return "Geceleyin / uzun bir gece boyu (`لَيْلًا`, belirsiz zaman zarfı mansûb, POS:T)"
            if 'P|INDEF|GEN' in features or 'MP|INDEF|GEN' in features:
                return "Geceler / gecelere (`لَيَالٍ / وَلَيَالٍ`, mankûs kırık çoğul belirsiz mecrûr, son `ي` tenvîn-i ivazla hazifli)"
            if 'P|ACC' in features:
                return "Geceler boyunca (`لَيَالِىَ`, kırık çoğul zaman zarfı mansûb, son `ى` fetha ile açık)"
            if 'INDEF|ACC' in features:
                return "Bir gece vakti (`لَيْلًا`, belirsiz zaman zarfı mansûb, tekil eril)"
            if 'INDEF|GEN' in features:
                return "Dinleneceğiniz bir geceyi (`بِلَيْلٍ`, harf-i cerr ile belirsiz mecrûr, tekil eril)"
            if 'NOM' in features:
                return "Gece (`ٱلَّيْلُ`, merfû mübtedâ/fâil; Rasm-ı Osmânî'de tek lâm ile `ٱليل` yazımlı)"
            if 'ACC' in features:
                if s == 79 and a == 29:
                    return "Gecesini (`لَيْلَهَا`, mef'ûl-i bih mansûb + zamir, tekil eril)"
                return "Geceyi (`ٱلَّيْلَ`, mef'ûl-i bih/zarf mansûb; Rasm-ı Osmânî'de tek lâm ile `ٱليل` yazımlı)"
            if 'GEN' in features:
                return "Gece / gecede / geceye (`ٱلَّيْلِ / بِٱلَّيْلِ / وَٱلَّيْلِ / وَبِٱلَّيْلِ`, izâfet/cerr/kasem mecrûru; tek lâm yazımlı)"

    elif root_ar == 'ل-ي-س':
        if '2FP' in features:
            return "Herhangi bir kadın gibi değilsiniz (`لَسْتُنَّ`, câmid nakıs mâzî fiil, 2. çoğul dişil — orta `ي` düşümüyle tekil örnek)"
        if '1S' in features:
            if s == 7 and a == 172:
                return "Ben Rabbiniz değil miyim (`أَلَسْتُ`, soru hemzesi + câmid nakıs fiil, 1. tekil; `بَلَىٰ` yanıtlı sözleşme sorusu)"
            return "Ben ... değilim (`لَّسْتُ`, câmid nakıs mâzî fiil, 1. tekil; orta `ي` düşümü)"
        if '3MP' in features:
            return "Değildirler / ... değiller (`لَيْسُوا۟`, câmid nakıs mâzî fiil, 3. çoğul eril, elif-i fârika yazımlı)"
        if '2MP' in features:
            return "Sizler ... değilsiniz (`لَسْتُمْ / وَلَسْتُم`, câmid nakıs mâzî fiil, 2. çoğul eril, orta `ي` düşmüş)"
        if '3FS' in features:
            return "Değildir (`لَيْسَتِ / وَلَيْسَتِ`, câmid nakıs mâzî fiil, 3. tekil dişil, kesralı geçiş tâ'sı)"
        if '2MS' in features:
            return "Sen ... değilsin (`لَسْتَ / لَّسْتَ`, câmid nakıs mâzî fiil, 2. tekil eril, orta `ي` düşmüş)"
        if (s, a) in {(6, 30), (6, 53), (11, 78), (11, 81), (29, 10), (29, 68), (36, 81), (39, 32), (39, 36), (39, 37), (39, 60), (43, 51), (46, 34), (75, 40), (95, 8)}:
            return "Değil midir / olmaz mı (`أَلَيْسَ / أَوَلَيْسَ`, soru hemzesi + câmid nakıs fiil, 3. tekil eril; kesin olumlu itiraf sorusu)"
        return "Değildir / yoktur (`لَيْسَ / لَّيْسَ / فَلَيْسَ / وَلَيْسَ`, câmid nakıs mâzî fiil, 3. tekil eril)"

    elif root_ar == 'ش-ط-ن':
        if pos == 'N':
            if 'MP|GEN' in features:
                return "Kendi azgın elebaşıları (`شَيَٰطِينِهِمْ`, cins isim kırık çoğul mecrûr + zamir, elif hazifli)"
            if 'MP|ACC' in features:
                return "Azgın saptırıcı güçler (`شَيَٰطِينَ`, cins isim kırık çoğul mansûb muzâf, elif hazifli)"
            if 'INDEF|GEN' in features:
                return "Kovulmuş / azılı her saptırıcı yıkıcı güçten (`شَيْطَٰنٍ`, cins isim belirsiz mecrûr, elif hazifli)"
            return "Azgın / yoldaş bir saptırıcı yıkıcı güce (`شَيْطَٰنًا`, cins isim belirsiz mansûb, elif hazifli)"
        if 'MP' in features:
            if 'NOM' in features:
                return "Taşkın saptırıcı güçler (`ٱلشَّيَٰطِينُ`, kırık çoğul merfû, elif hazifli)"
            if 'GEN' in features:
                return "Taşkın saptırıcı güçlerden / güçlere (`ٱلشَّيَٰطِينِ / لِّلشَّيَٰطِينِ`, kırık çoğul mecrûr, elif hazifli)"
            return "Taşkın saptırıcı güçleri / odakları (`ٱلشَّيَٰطِينَ / وَٱلشَّيَٰطِينَ`, kırık çoğul mansûb, elif hazifli)"
        if 'NOM' in features:
            return "Merkezden uzaklaşan saptırıcı yıkıcı güç (`ٱلشَّيْطَٰنُ`, tekil merfû, elif hazifli)"
        if 'GEN' in features:
            return "Saptırıcı yıkıcı güç / güce / güçten (`ٱلشَّيْطَٰنِ / لِلشَّيْطَٰنِ`, tekil mecrûr, elif hazifli)"
        return "Saptırıcı yıkıcı gücü / güce (`ٱلشَّيْطَٰنَ`, tekil mansûb, elif hazifli)"

    elif root_ar == 'ق-ر-أ':
        if lemma == "quruw^'":
            return "Üç döngüsel evre (`قُرُوٓءٍ`, kırık çoğul cins isim belirsiz muzâfun ileyh mecrûr — rahimde toplanıp boşalan devre)"
        if lemma == "quro'aAn":
            if pos == 'N':
                return "Onun birleştirilip okunuşunu (`وَقُرْءَانَهُۥ / قُرْءَانَهُۥ`, mastar/cins isim mansûb + zamir)"
            if 'INDEF|ACC' in features:
                if (s, a) in {(12, 2), (43, 3)}:
                    return "Arapça bir okuyuş / Kur'an olarak (`قُرْءَٰنًا`, belirsiz mansûb; Rasm-ı Osmânî'de `قرءنا` elif hazifli)"
                return "Okunup kavranan bir Kur'an olarak (`قُرْءَانًا / وَقُرْءَانًا`, belirsiz mansûb, açık elifli `قرءانا`)"
            if 'INDEF|GEN' in features:
                return "Bir Kur'an / Kur'an'dan (`بِقُرْءَانٍ / قُرْءَانٍ / وَقُرْءَانٍ`, belirsiz mecrûr)"
            if 'INDEF|NOM' in features:
                return "Apaçık / şerefli bir Kur'an (`وَقُرْءَانٌ / لَقُرْءَانٌ / قُرْءَانٌ`, belirsiz merfû haber)"
            if 'NOM' in features:
                return "Kur'an (`ٱلْقُرْءَانُ`, merfû mübtedâ/nâib-i fâil)"
            if 'GEN' in features:
                return "Kur'an'da / Kur'an'a (`ٱلْقُرْءَانِ / وَٱلْقُرْءَانِ / بِٱلْقُرْءَانِ`, harf-i cerr/izâfet/kasem mecrûru)"
            return "Derlenip okunan Kur'an'ı (`ٱلْقُرْءَانَ / وَٱلْقُرْءَانَ / قُرْءَانَ`, mansûb mef'ûl/muzâf)"
        if lemma == 'nuqori}u':
            return "Sana Biz okutturacağız (`سَنُقْرِئُكَ`, IV. bab ettirgen muzârî merfû, 1. çoğul + zamir)"
        # lemma == 'qara>a'
        if 'IMPV' in features:
            if '2MP' in features:
                return "Okuyun (`ٱقْرَءُوا۟ / فَٱقْرَءُوا۟`, I. bab emir, 2. çoğul eril, elif-i fârikalı)"
            return "Oku / bir araya getirip kavra (`ٱقْرَأْ`, I. bab mehmûzu'l-lâm emir, 2. tekil eril)"
        if 'PASS' in features:
            return "Okunduğu zaman (`قُرِئَ`, I. bab meçhul mâzî, 3. tekil eril)"
        if 'PERF' in features:
            if '1P' in features:
                return "Biz onu derleyip okuduğumuzda (`قَرَأْنَٰهُ`, I. bab mâzî, 1. çoğul + zamir)"
            if '3MS' in features:
                return "Okusaydı (`فَقَرَأَهُۥ`, I. bab mâzî, 3. tekil eril + zamir)"
            return "Okuyacağın / okuduğun zaman (`قَرَأْتَ`, I. bab mâzî, 2. tekil eril)"
        if '3MP' in features:
            return "Okurlar (`يَقْرَءُونَ`, I. bab muzârî merfû, 3. çoğul eril)"
        if '1P' in features:
            return "Okuyacağımız (`نَّقْرَؤُهُۥ`, I. bab muzârî merfû, 1. çoğul + zamir)"
        return "Okuman için (`لِتَقْرَأَهُۥ`, I. bab muzârî mansûb, 2. tekil eril)"

    elif root_ar == 'خ-ل-د':
        if lemma == '>axolada':
            if s == 7 and a == 176:
                return "Yere yapıştı / toprağa çakılıp kaldı (`أَخْلَدَ`, IV. bab mâzî, 3. tekil eril)"
            return "Kendisini ölümsüz ve kalıcı kıldı (`أَخْلَدَهُۥ`, IV. bab müteaddî mâzî, 3. tekil eril + zamir)"
        if lemma == 'yaxoludo':
            if 'JUS' in features:
                return "Orada alçaltılarak kalır (`وَيَخْلُدْ`, I. bab muzârî meczûm, 3. tekil eril — İbn Âmir'de merfû)"
            return "Temelli kalırsınız diye (`تَخْلُدُونَ`, I. bab muzârî merfû, 2. çoğul eril)"
        if lemma == 'm~uxal~aduwn':
            if pos == 'ADJ':
                return "Yaşlanmadan taze tutulanlar (`مُّخَلَّدُونَ`, II. bab ism-i mef'ûl sıfat çoğul merfû)"
            return "Tazeliğinde sabit bırakılmış gençler (`مُّخَلَّدُونَ`, II. bab ism-i mef'ûl isim çoğul merfû)"
        if lemma == 'xuluwd':
            return "Bozulmaz kalıcılık / sonsuzluk (`ٱلْخُلُودِ`, I. bab `فُعُول` mastarı mecrûr — Kur'an'da tekil)"
        if lemma == 'xulod':
            if 'ACC' in features:
                return "Ölümsüz kalıcılığı (`ٱلْخُلْدَ`, I. bab mastar mansûb mef'ûl)"
            return "Kalıcılık / sonsuzluk (`ٱلْخُلْدِ`, I. bab mastar mecrûr muzâfun ileyh)"
        # lemma == "xa`lid"
        if 'MD' in features:
            return "İkisi birden temelli kalıcı olarak (`خَٰلِدَيْنِ`, I. bab ism-i fâil ikil [müsennâ] mansûb — tek ikil örnek)"
        if 'MP|GEN' in features:
            return "Kalıcılardan (`ٱلْخَٰلِدِينَ`, I. bab ism-i fâil eril çoğul mecrûr, elif hazifli)"
        if 'MP|NOM' in features:
            return "Temelli ve kalıcı olanlardır (`خَٰلِدُونَ / ٱلْخَٰلِدُونَ`, I. bab ism-i fâil eril çoğul merfû haber, elif hazifli)"
        if 'MP|ACC' in features:
            return "Orada temelli kalanlar olarak (`خَٰلِدِينَ`, I. bab ism-i fâil eril çoğul mansûb hâl, elif hazifli)"
        if 'INDEF|NOM' in features:
            return "Ateşte temelli kalacak kimse (`خَٰلِدٌ`, I. bab ism-i fâil tekil belirsiz merfû)"
        return "İçinde temelli kalıcı olarak (`خَٰلِدًا`, I. bab ism-i fâil tekil belirsiz mansûb hâl)"

    elif root_ar == 'ت-و-ب':
        if lemma == 't~awob':
            return "Dönüşü / yönelişi (`ٱلتَّوْبِ`, I. bab soyut cins mastar mecrûr muzâfun ileyh — Kur'an'da tek örnek)"
        if lemma == 'mataAb':
            if 'GEN' in features:
                return "Benim dönüş yerim / merciim (`مَتَابِ`, mîmli mastar/mekân mecrûr — yâ-i mütekellim hazifli Rasm)"
            return "Gerçek ve tam bir dönüşle (`مَتَابًا`, mîmli mastar mef'ûl-i mutlak mansûb)"
        if lemma == 't~a`^}ibuwn':
            return "Yanlıştan dönüp yönelenler (`ٱلتَّٰٓئِبُونَ`, I. bab ism-i fâil çoğul merfû, elif hazifli)"
        if lemma == 'ta`^}iba`t':
            return "Dönüp yönelen kadınlar (`تَٰٓئِبَٰتٍ`, I. bab ism-i fâil dişil çoğul mansûb, elif hazifli)"
        if lemma == 'tawobap':
            if 'NOM' in features:
                return "Dönüş (kabulü) (`ٱلتَّوْبَةُ / تَوْبَتُهُمْ`, birim mastar dişil merfû)"
            if 'INDEF' in features:
                return "Bir dönüş / katışıksız dönüşle (`تَوْبَةً`, birim mastar belirsiz mansûb)"
            return "Dönüşü (`ٱلتَّوْبَةَ`, birim mastar mansûb mef'ûl)"
        if lemma == 'taw~aAb':
            if 'MP' in features:
                return "Sık sık doğruluk yoluna dönenleri (`ٱلتَّوَّٰبِينَ`, mübâlağa ism-i fâil çoğul mansûb, elif hazifli)"
            if pos == 'ADJ':
                return "Dönüşleri çokça kabul edendir (`تَوَّابٌ`, mübâlağa sıfat merfû)"
            if 'ACC' in features:
                return "Dönüşleri daima kabul edendir (`تَوَّابًا / تَوَّابًۢا`, mübâlağa ism-i fâil mansûb)"
            return "Dönüşleri çokça kabul eden (`ٱلتَّوَّابُ / تَوَّابٌ`, mübâlağa ism-i fâil merfû)"
        # lemma == 'taAba'
        god_turn_3ms = {(2, 37), (2, 54), (2, 187), (5, 71), (9, 117), (9, 118), (20, 122), (58, 13), (73, 20)}
        if 'IMPV' in features:
            if '2MS' in features:
                return "Bize rahmetle dönüp kabul et (`وَتُبْ`, I. bab emir 2. tekil eril — orta `و` düşmüş, `عَلَى` ile)"
            return "Yaratıcınıza dönün (`تُوبُوٓا۟ / فَتُوبُوٓا۟ / وَتُوبُوٓا۟`, I. bab emir 2. çoğul eril, `إِلَى` ile)"
        if 'PERF' in features:
            if '1S' in features:
                return "Döndüm (`تُبْتُ`, I. bab mâzî 1. tekil — orta `و` düşmüş)"
            if '2MP' in features:
                return "Eğer dönerseniz (`تُبْتُمْ`, I. bab mâzî 2. çoğul eril — orta `و` düşmüş)"
            if '3MD' in features:
                return "İkisi dönüp düzeltirse (`تَابَا`, I. bab mâzî 3. ikil eril)"
            if '3MP' in features:
                return "Döndüler / yön değiştirdiler (`تَابُوا۟`, I. bab mâzî 3. çoğul eril)"
            if (s, a) in god_turn_3ms:
                return "Rahmet ve kolaylaştırmayla kuluna geri döndü (`تَابَ / فَتَابَ / وَتَابَ / تَّابَ`, I. bab mâzî 3. tekil eril — `عَلَى` ile)"
            return "Yanlıştan dönüp yöneldi (`تَابَ`, I. bab mâzî 3. tekil eril)"
        if 'JUS' in features:
            if '2D' in features:
                return "İkiniz Allah'a dönerseniz (`تَتُوبَآ`, I. bab muzârî meczûm 2. ikil — `إِلَى` ile)"
            if '3MP' in features:
                return "Dönmezlerse (`يَتُوبُوا۟`, I. bab muzârî meczûm 3. çoğul eril)"
            return "Kim dönmezse (`يَتُبْ`, I. bab muzârî meczûm 3. tekil eril — orta `و` düşmüş)"
        if 'SUBJ' in features:
            if '3MP' in features:
                return "Dönsünler diye / dönerlerse (`لِيَتُوبُوٓا۟ / يَتُوبُوا۟`, I. bab muzârî mansûb/meczûm 3. çoğul eril)"
            return "Rahmetiyle dönüp kabul etmesi (`يَتُوبَ / وَيَتُوبَ`, I. bab muzârî mansûb 3. tekil eril — `عَلَى` ile)"
        if '1S' in features:
            return "Rahmetimle dönüşlerini kabul ederim (`أَتُوبُ`, I. bab muzârî merfû 1. tekil — `عَلَى` ile)"
        if '3MP' in features:
            return "Dönerler (`يَتُوبُونَ`, I. bab muzârî merfû 3. çoğul eril)"
        if (s, a) == (25, 71):
            return "Allah'a yönelip döner (`يَتُوبُ`, I. bab muzârî merfû 3. tekil eril — `إِلَى` ile)"
        return "Rahmetiyle döner / dönüşü kabul eder (`يَتُوبُ / وَيَتُوبُ`, I. bab muzârî merfû 3. tekil eril — `عَلَى` ile)"

    if root_ar == 'م-و-ل':
        if (s, a) == (69, 28):
            return "Benim malım (`مَالِيَهْ`, hâ-i sekt ile sonlanan izâfetli merfû tekil isim — tekilde med elifi korunur; `69:29`a geçişte Hafs'ta öncelikle hafif sekt okunur)"
        if 'MP|INDEF|NOM' in features:
            return "Mallar (`أَمْوَٰلٌ`, nekre merfû kırık çoğul `أَفْعَال` ismi — tüm kırık çoğullarda olduğu gibi `و` sonrası med elifi Rasm'da hazfedilir)"
        if 'MP|INDEF|ACC' in features:
            return "Mallar / malları (`أَمْوَٰلًا`, nekre mansûb kırık çoğul isim — elif-hazifli Rasm)"
        if 'MP|INDEF|GEN' in features:
            return "Mallarla (`بِأَمْوَٰلٍ`, nekre mecrûr kırık çoğul isim — `بِـ` harf-i cerriyle; elif-hazifli Rasm)"
        if 'MP|NOM' in features:
            return "Malları / mallarınız (`أَمْوَٰلُهُمْ / أَمْوَٰلُكُمْ / أَمْوَٰلُنَا`, merfû kırık çoğul isim — elif-hazifli Rasm)"
        if 'MP|ACC' in features:
            return "Malları / mallarınızı (`أَمْوَٰلَهُمْ / أَمْوَٰلَكُمْ / أَمْوَٰلَ`, mansûb kırık çoğul isim — elif-hazifli Rasm)"
        if 'MP|GEN' in features:
            return "Mallarından / mallarıyla (`بِأَمْوَٰلِهِمْ / مِنْ أَمْوَٰلِهِمْ / ٱلْأَمْوَٰلِ / أَمْوَٰلِكُمْ`, mecrûr kırık çoğul isim — elif-hazifli Rasm)"
        if 'M|INDEF|NOM' in features:
            return "Herhangi bir mal (`مَالٌ`, nekre merfû tekil isim — `لَا يَنفَعُ` öznesi; tekilde med elifi yazılır)"
        if 'M|INDEF|ACC' in features:
            return "Mal / bolca mal (`مَالًا`, tenvinli nekre mansûb tekil isim — tekilde med elifi yazılır)"
        if 'M|INDEF|GEN' in features:
            return "Bir mal / malla (`بِمَالٍ / مَالٍ`, nekre mecrûr tekil isim — tekilde med elifi yazılır)"
        if 'M|NOM' in features:
            return "Mal / onun malı (`ٱلْمَالُ / مَالُهُۥ`, merfû tekil isim — tekilde med elifi yazılır)"
        if 'M|ACC' in features:
            if (s, a) == (89, 20):
                return "Malı (`ٱلْمَالَ`, marife mansûb tekil isim — `تُحِبُّونَ` mef'ûlü)"
            return "Malı / onun malını (`مَالَهُۥ / مَالَ`, mansûb tekil isim — tekilde med elifi yazılır)"
        if 'M|GEN' in features:
            return "Maldan (`ٱلْمَالِ / مَالِ ٱللَّهِ`, mecrûr tekil isim — `مِنَ` harf-i cerriyle)"

    if root_ar == 'أ-ح-د':
        if lemma == '<iHodaY':
            if (s, a) == (28, 27):
                return "Kızlarımdan birini (`إِحْدَى`, takdirî fetha ile mansûb dişil `فِعْلَى` tekil ismi — imâleye elverişli maksûr `ى` ile yazılır)"
            if (s, a) == (74, 35):
                return "Büyük uyarıcı olaylardan biri (`لَإِحْدَى`, te'kit `لَـ` harfiyle merfû takdirî dişil `فِعْلَى` ismi)"
            if 'F|NOM' in features:
                return "İki taraftan/kadından biri (`إِحْدَىٰهُمَا / إِحْدَى`, takdirî zamme ile merfû dişil `فِعْلَى` ismi — zamire bitiştiğinde dahi Osmânî Rasm'da maksûr `ى` korunur)"
            if 'F|ACC' in features:
                return "İki topluluktan/eşlerden birini (`إِحْدَى / إِحْدَىٰهُنَّ`, takdirî fetha ile mansûb dişil `فِعْلَى` ismi — Osmânî Rasm'da `ى` korunur)"
            if 'F|GEN' in features:
                return "Topluluklardan biri (`مِنْ إِحْدَى`, `مِنْ` sonrası takdirî kesra ile mecrûr dişil `فِعْلَى` ismi)"
        else:
            if (s, a) == (112, 1):
                return "Eşsiz, bölünmez ve benzersiz Bir/Tek (`أَحَدٌ`, `هُوَ ٱللَّهُ` cümlesinin nekre merfû mutlak haberi — `112:2`ye vaslda cumhur `أَحَدُنِ ٱللَّهُ` kesra ile, Ebû Amr tenvîn hazfiyle `أَحَدُ ٱللَّهُ` okur)"
            if (s, a) == (112, 4):
                return "Hiçbir denk/kimse (`أَحَدٌۢ`, `لَمْ يَكُن` ismi, nekre merfû eril isim — besmele geçiş işaretiyle küçük `م` taşır)"
            if (s, a) == (18, 110):
                return "Hiç kimseyi (`أَحَدًۢا`, nehy bağlamında nekre mansûb eril mef'ûl — besmele geçiş işaretiyle küçük `م` taşır)"
            if (s, a) == (12, 4):
                return "On bir (`أَحَدَ` `عَشَرَ` ile bileşik, fetha üzere mebnî mansûb isim — `رَأَيْتُ` mef'ûlü)"
            if 'M|INDEF|NOM' in features:
                return "Herhangi bir kimse (`أَحَدٌ`, olumsuz/şart/istifham bağlamında nekre merfû eril isim)"
            if 'M|INDEF|ACC' in features:
                return "Hiç kimseyi / herhangi birini (`أَحَدًا`, olumsuz/şart/istifham bağlamında nekre mansûb eril isim)"
            if 'M|INDEF|GEN' in features:
                return "Hiç kimseden / kimseye / herhangi birinden (`مِنْ أَحَدٍ / بَيْنَ أَحَدٍ / لِأَحَدٍ / كَأَحَدٍ`, nekre mecrûr eril isim)"
            if 'M|NOM' in features:
                return "Onlardan/ikinizden/ikisinden biri (`أَحَدُهُمْ / أَحَدُكُمْ / أَحَدُهُمَا / أَحَدُكُمَا`, zamire muzâf merfû eril isim)"
            if 'M|ACC' in features:
                return "Birinizi/birini (`أَحَدَكُمْ / أَحَدَهُمْ / أَحَدَنَا`, zamire muzâf mansûb eril isim)"
            if 'M|GEN' in features:
                return "İkisinden/onlardan birinin (`لِأَحَدِهِمَا / مِنْ أَحَدِهِمَا / أَحَدِهِمْ`, zamire muzâf mecrûr eril isim)"

    if root_ar == 'ن-ج-و':
        if lemma == 'najaA':
            if '2MS' in features:
                return "Kurtuldun (`نَجَوْتَ`, I. bab nâkıs-ı vâvî mâzî 2. tekil eril — aslî `و` görünür)"
            return "Kurtulan (`نَجَا`, I. bab nâkıs-ı vâvî mâzî 3. tekil eril)"
        if lemma == 'naAj':
            return "Kurtulacak olan (`نَاجٍ`, I. bab ism-i fâil, nekre mecrûr — son `ي` düşüp tenvîne dönmüş)"
        if lemma == 'munaj~uw':
            return "Mutlaka kurtaracak olanlar (`لَمُنَجُّوهُمْ / مُنَجُّوكَ`, II. bab ism-i fâil çoğul eril merfû — izâfetle `ن` düşmüş)"
        if lemma == 'n~ajaw`p':
            return "Kurtuluşa (`ٱلنَّجَوٰةِ`, `إِلَى` ile mecrûr dişil isim — vav üzerine hançer elifli Osmânî yazım)"
        if lemma == 'najiy~':
            return "Baş başa gizlice konuşan / özel görüşmeci (`نَجِيًّا`, `فَعِيل` kalıbında nekre mansûb hâl ismi)"
        if lemma == 'najowaY`^':
            if (s, a) == (17, 47):
                return "Gizlice fısıldaşan topluluk (`نَجْوَىٰٓ`, masdarın topluluğa ad olduğu merfû haber)"
            if 'M|NOM' in features:
                return "Gizli konuşma / fısıltıları (`نَجْوَىٰ / نَجْوَىٰهُمْ / نَجْوَىٰكُمْ`, takdirî zamme ile merfû masdar — maksûr `ى` zamir önünde korunur)"
            if 'M|ACC' in features:
                return "Gizli konuşmayı (`ٱلنَّجْوَىٰ / نَجْوَىٰكُمْ`, takdirî fetha ile mansûb masdar)"
            return "Gizli konuşmadan / fısıltısından (`مِن نَّجْوَىٰ / عَنِ ٱلنَّجْوَىٰ`, takdirî kesra ile mecrûr masdar)"
        if lemma == 'na`jayo':
            return "Baş başa gizlice konuştuğunuzda (`نَٰجَيْتُمُ`, III. bab mâzî 2. çoğul eril — bâb elifi Rasm'da hazfedilmiş)"
        if lemma == 'tana`jayo':
            if 'IMPV' in features:
                return "Birbirinizle gizlice konuşun (`وَتَنَٰجَوْا۟`, VI. bab emir 2. çoğul eril)"
            if 'JUS' in features:
                return "Birbirinizle gizlice konuşmayın (`فَلَا تَتَنَٰجَوْا۟`, VI. bab nehy meczûm 2. çoğul eril)"
            if 'PERF' in features:
                return "Birbirinizle gizlice konuştuğunuzda (`تَنَٰجَيْتُمْ`, VI. bab mâzî 2. çoğul eril)"
            return "Birbirleriyle gizlice fısıldaşırlar (`وَيَتَنَٰجَوْنَ`, VI. bab muzârî merfû 3. çoğul eril)"
        if lemma == '>anjaY`':
            if (s, a) == (21, 88):
                return "Kurtarırız (`نُۨجِى`, IV. bab muzârî merfû 1. çoğul — Osmânî hatta tek nûn + küçük nûn; İbn Âmir ve Şu'be `نُجِّىَ` II. bab meçhûl okur)"
            if (s, a) == (10, 103):
                return "Kurtarırız (`نُنجِ`, IV. bab muzârî 1. çoğul — son `ي` Osmânî hatta hazfedilmiş)"
            if 'IMPF' in features:
                if '3FS' in features:
                    return "Sizi kurtaracak (`تُنجِيكُم`, IV. bab muzârî merfû 3. tekil dişil — `تِجَٰرَة` sıfatı)"
                return "Onu kurtarsın (`يُنجِيهِ`, IV. bab muzârî 3. tekil eril)"
            if '2MS' in features:
                return "Bizi kurtarırsan (`أَنجَيْتَنَا`, IV. bab mâzî 2. tekil eril — şart cümlesi)"
            if '3MS' in features:
                return "Kurtardı (`أَنجَىٰ / أَنجَىٰنَا / أَنجَىٰهُمْ / فَأَنجَىٰهُ`, IV. bab mâzî 3. tekil eril)"
            return "Kurtardık / çekip çıkardık (`أَنجَيْنَا / أَنجَيْنَٰكُم / فَأَنجَيْنَٰهُ`, IV. bab mâzî 1. çoğul)"
        if lemma == 'naj~aY`':
            if 'PASS' in features:
                return "Kurtarıldı (`فَنُجِّىَ`, II. bab meçhûl mâzî 3. tekil eril)"
            if 'IMPV' in features:
                return "Kurtar (`نَجِّنِى / وَنَجِّنَا`, II. bab emir/dua 2. tekil eril — nâkıs fiilde son harf düşmüş)"
            if 'IMPF' in features:
                if '1P' in features:
                    if (s, a) == (10, 92):
                        return "Bedeninle çıkarıp kurtaracağız (`نُنَجِّيكَ`, II. bab muzârî 1. çoğul)"
                    if (s, a) == (29, 32):
                        return "Onu mutlaka kurtaracağız (`لَنُنَجِّيَنَّهُۥ`, II. bab muzârî 1. çoğul, ağır te'kit nûnlu)"
                    return "Kurtarırız (`نُنَجِّى`, II. bab muzârî merfû 1. çoğul)"
                return "Sizi/onları kurtarır (`يُنَجِّيكُم / وَيُنَجِّى`, II. bab muzârî merfû 3. tekil eril)"
            if '3MS' in features:
                return "Kurtardı (`نَجَّىٰنَا / نَجَّىٰكُمْ / نَجَّىٰهُمْ`, II. bab mâzî 3. tekil eril)"
            return "Kurtardık (`نَجَّيْنَا / نَجَّيْنَٰكُم / نَجَّيْنَٰهُ / نَجَّيْنَٰهُمْ`, II. bab mâzî 1. çoğul)"

    if root_ar == 'س-و-ي':
        if lemma == '{sotawaY`^':
            if (s, a) == (43, 13) and 'IMPF' in features:
                return "Dengeli kurulmanız için (`لِتَسْتَوُوا۟`, VIII. bab mansûb mudâri 2. çoğul eril — `لِ` ile hazf-i nûn)"
            if (s, a) == (43, 13) and 'PERF' in features:
                return "Dengeli kurulduğunuzda (`ٱسْتَوَيْتُمْ`, VIII. bab mâzî 2. çoğul eril)"
            if (s, a) == (23, 28):
                return "Dengeli kurulup yerleştiğinde (`ٱسْتَوَيْتَ`, VIII. bab mâzî 2. tekil eril)"
            if (s, a) == (11, 44):
                return "Dengeli oturdu (`وَٱسْتَوَتْ`, VIII. bab mâzî 3. tekil dişil — Cûdî üzerine)"
            if (s, a) in {(11, 24), (39, 29)}:
                return "Bir / denk olurlar mı (`يَسْتَوِيَانِ`, VIII. bab merfû mudâri tesniye eril — sâbit nûn)"
            if (s, a) in {(9, 19), (16, 75), (32, 18)}:
                return "Eşit / denk olurlar (`يَسْتَوُۥنَ`, VIII. bab merfû mudâri 3. çoğul eril — Osmânî hatta tek vavlı)"
            if (s, a) in {(13, 16), (41, 34)} and '3FS' in features:
                return "Bir / denk olur mu (`تَسْتَوِى`, VIII. bab merfû mudâri 3. tekil dişil)"
            if 'IMPF' in features:
                return "Bir / denk olur mu (`يَسْتَوِى`, VIII. bab merfû mudâri 3. tekil eril — takdirî zamme)"
            if (s, a) == (28, 14):
                return "Olgunluk ve denge kıvamına erdi (`وَٱسْتَوَىٰ`, VIII. bab mâzî 3. tekil eril — zihinsel/ahlaki denge)"
            if (s, a) == (53, 6):
                return "Kendi zatında dengeli doğrulup belirdi (`فَٱسْتَوَىٰ`, VIII. bab mâzî 3. tekil eril)"
            if (s, a) == (48, 29):
                return "Sapı üzerinde dimdik dengelendi (`فَٱسْتَوَىٰ`, VIII. bab mâzî 3. tekil eril — botanik dikleşme)"
            if (s, a) in {(2, 29), (41, 11)}:
                return "Dosdoğru yöneldi (`ٱسْتَوَىٰٓ إِلَى`, VIII. bab mâzî 3. tekil eril — göğe düz hatla yönelme)"
            if (s, a) in {(7, 54), (10, 3), (13, 2), (20, 5), (25, 59), (32, 4), (57, 4)}:
                return "Egemenlik makamına sarsılmaz dengeyle kuruldu (`ٱسْتَوَىٰ عَلَى ٱلْعَرْشِ`, VIII. bab mâzî 3. tekil eril)"
            return "Dengeli kuruldu / yöneldi (`ٱسْتَوَىٰ`, VIII. bab mâzî 3. tekil eril)"

        if lemma == 'saw~aY`':
            if (s, a) in {(15, 29), (38, 72)}:
                return "Onu tam kıvamına getirip orantıladığımda (`سَوَّيْتُهُۥ`, II. bab mâzî 1. tekil — insani yapının donatımı)"
            if (s, a) == (26, 98):
                return "Sizi denk tutuyorduk (`نُسَوِّيكُم بِـ`, II. bab muzârî 1. çoğul — ortak koşulanları denk sayma)"
            if (s, a) == (75, 4):
                return "Yeniden orantılamaya (`أَن نُّسَوِّىَ`, `أَنْ` ile mansûb II. bab muzârî 1. çoğul — parmak uçlarının düzenlenmesi)"
            if (s, a) == (91, 14):
                return "Onları yerle bir düzledi (`فَسَوَّىٰهَا`, II. bab mâzî 3. tekil eril — Semûd şehrinin yıkımı)"
            if (s, a) == (91, 7):
                return "Onu dengeli bir bütün kılıp donatana (`وَمَا سَوَّىٰهَا`, II. bab mâzî 3. tekil eril — benliğin yetenek uyumu)"
            return "Eksiksiz orantı ve uyuma kavuşturdu (`سَوَّىٰ / فَسَوَّىٰ`, II. bab mâzî 3. tekil eril)"

        if lemma == 'tusaw~aY`':
            return "Yerle bir düzlense (`تُسَوَّىٰ`, II. bab meçhûl muzârî 3. tekil dişil — toprakla aynı hizaya inme)"

        if lemma == 'saAwaY`':
            return "İki tarafı aynı seviyeye getirdiğinde (`سَاوَىٰ بَيْنَ`, III. bab mâzî 3. tekil eril — iki dağ arasını demirle eşitleme)"

        if lemma == "sawaA^'":
            if (s, a) in {(2, 6), (7, 193), (13, 10), (14, 21), (16, 71), (26, 136), (30, 28), (36, 10), (52, 16), (63, 6)}:
                return "Birdir / eşittir (`سَوَآءٌ`, tenvinli merfû masdar isim — mukaddem veya muahhar haber)"
            if (s, a) in {(2, 108), (5, 12), (5, 60), (5, 77), (28, 22), (37, 55), (38, 22), (44, 47), (60, 1)}:
                return "Düz orta yoluna / tam ortasına (`سَوَآءَ ٱلسَّبِيلِ / فِى سَوَآءِ`, izâfetle mansûb mef'ûl veya harf-i cerle mecrûr isim)"
            if (s, a) == (3, 64):
                return "Ortak ve adil bir ilkeye (`كَلِمَةٍ سَوَآءٍ`, mecrûr mevsûfa tâbi sıfat isim)"
            return "Eşit düzeyde / ortak olarak (`سَوَآءً / عَلَىٰ سَوَآءٍ`, mansûb hâl veya mecrûr zarf)"

        if lemma == 'sawiy~':
            if (s, a) == (19, 10):
                return "Sağlığı ve organları yerinde olarak (`سَوِيًّا`, mansûb hâl ismi — konuşma engeli ve sakatlığı olmaksızın)"
            if (s, a) == (19, 17):
                return "Kusursuz orantılı bir insan (`بَشَرًا سَوِيًّا`, mansûb mevsûfa tâbi sıfat)"
            if (s, a) in {(19, 43), (20, 135)}:
                return "Dengeli ve pürüzsüz doğru yol (`صِرَٰطًا سَوِيًّا`, mansûb/mecrûr sıfat — tökezletmeyen orta güzergâh)"
            return "Dik ve dengeli yürüyen (`يَمْشِى سَوِيًّا`, fiilin durumunu bildiren mansûb hâl)"

        if lemma == 'suwFY':
            return "İki tarafa da eşit mesafede açık bir orta meydan (`مَكَانًا سُوًى`, maksûr elifle mansûb sıfat)"

    if root_ar == 'ك-ي-ف':
        if (s, a) in {(3, 6), (5, 64), (30, 48)}:
            return "Dilediği biçim ve düzende (`كَيْفَ يَشَآءُ`, fetha üzerine mebnî hâl/tarz ismi — soru anlamı olmadan fiilin biçimlendirme tarzını belirleyen hâl)"
        if (s, a) in {(3, 25), (4, 41), (4, 62), (47, 27)}:
            return "Peki ya ... geldiğinde hâlleri nasıl olacak (`فَكَيْفَ إِذَا`, `فَـ` sonuç bağlacıyla fetha üzerine mebnî soru ismi — örtük fiille keskin yüzleştirme)"
        if (s, a) in {(13, 32), (22, 44), (34, 45), (35, 26), (40, 5), (54, 16), (54, 18), (54, 21), (54, 30), (67, 18)}:
            return "Peki nasıldı (`فَكَيْفَ كَانَ`, `فَـ` sonuç bağlacıyla fetha üzerine mebnî soru ismi — `كَانَ` nâkıs fiilinin öncelenmiş haberi)"
        if (s, a) in {(7, 93), (73, 17)}:
            return "Öyleyse nasıl (`فَكَيْفَ`, `فَـ` sonuç bağlacıyla fetha üzerine mebnî soru ismi — tam fiilin önünde öncelenmiş hâl)"
        if (s, a) in {(3, 101), (4, 21), (5, 43), (6, 81), (18, 68)}:
            return "Ve nasıl / hangi mantıkla (`وَكَيْفَ`, `وَ` bağlacıyla fetha üzerine mebnî soru ismi — hâl cümlesi eşliğinde mantıksal çelişki yüzleştirmesi)"
        if (s, a) == (9, 8):
            return "Nasıl olabilir ki (`كَيْفَ وَإِن`, fetha üzerine mebnî soru ismi — örtük fiil/haberle mantıksal imkânsızlık sorgusu)"
        if (s, a) in {(3, 137), (6, 11), (7, 84), (7, 86), (7, 103), (9, 7), (10, 39), (10, 73), (12, 109), (16, 36), (27, 14), (27, 51), (27, 69), (28, 40), (30, 9), (30, 42), (35, 44), (37, 73), (40, 21), (40, 82), (43, 25), (47, 10), (67, 17)}:
            return "Nasıl oldu / nasıldır (`كَيْفَ`, fetha üzerine mebnî soru ismi — `كَانَ / يَكُونُ` veya isim cümlesi önünde öncelenmiş haber)"
        if (s, a) in {(14, 45), (74, 19), (74, 20), (89, 6), (105, 1)}:
            return "Hangi tarz ve biçimde (`كَيْفَ`, fetha üzerine mebnî soru ismi — eylemin yapılış biçimini belirten mef'ûl-i mutlak nâibi)"
        return "Nasıl / hangi biçim ve işleyişle (`كَيْفَ`, fetha üzerine mebnî soru ismi — tam fiilin önünde öncelenmiş hâl)"

    if root_ar in DYNAMIC_ROOT_SPECS:
        spec = DYNAMIC_ROOT_SPECS[root_ar]
        for rule in spec.get('irab_rules', []):
            if _rule_matches(rule, lemma, pos, features, s, a):
                return rule['label']
        if spec.get('irab_default'):
            return spec['irab_default']

    raise ValueError(f"Eşleşmeyen lemma: root={root_ar}, lemma={lemma}, ref={s}:{a}")


def generate_contextual_explanation(root_ar, word_uthmani, word_rasm, lemma, pos, features, s, a, surah_name):
    """Kökün tek çekirdek mekanizması, lemması ve ayet bağlamına göre açıklamasını üretir."""
    f = features

    if root_ar == 'أ-ل-ه':
        if lemma == '<ila`h':
            if (s, a) == (21, 22):
                return "Göklerde ve yerde Allah'tan başka sığınak/otorite odakları olsaydı kozmik düzenin çatışmayla bozulacağı gerçeği."
            if (s, a) == (23, 91):
                return "Birden fazla sığınak odağı olsaydı her birinin kendi yarattığıyla çekilip üstünlük kurma savaşına gireceği; tek sığınağın zorunluluğu."
            if (s, a) in [(25, 43), (45, 23)]:
                return "Kişinin kendi keyfî arzusunu (hevâsını) mutlak merci ve sığınak edinerek onun buyruğuna teslim olması."
            if (s, a) == (43, 84):
                return "Hem gökteki sistemde hem yerdeki düzende tek ve mutlak sığınak merciinin O olduğu ilkesi."
            if (s, a) == (114, 3):
                return "İnsanların en nihai sığınağı, acziyet anında mutlak teslimiyetle yöneldiği tek koruyucu otorite."
            return "Kendisine yönelinen, sığınak edinilen ve yüceliği karşısında boyun eğilen otorite odağı."
        if lemma == '{ll~ahum~a':
            return "Doğrudan yüce sığınağa yakarış; varlığın tüm mülk ve tasarrufunun O'na ait olduğunu tescil eden iltica nidası."
        return "Varlıkların tüm sarsıntı ve muhtaçlık anında yöneldiği yegâne mutlak sığınak ve evrenin tek otoritesi."

    elif root_ar == 'ق-و-ل':
        if (s, a) == (73, 5):
            return "Vahyin zihne, kalbe ve hayata yüklediği büyük sorumluluk, taşınması gereken ağır ilke ve bildiri."
        if (s, a) == (33, 70):
            return "Hedefe kilitli, hiçbir eğrilik ve çelişki barındırmayan sağlam ve adil söz."
        if (s, a) == (20, 44):
            return "Muhatabın savunma refleksini kırmayı, kalbine dokunmayı amaçlayan yumuşak ve nezaketli üslup."
        if (s, a) == (17, 23):
            return "Anne babaya karşı hürmet, şefkat ve onurlandırıcı bir dil kullanımı."
        if (s, a) == (4, 63):
            return "Muhatabın iç dünyasına, vicdanına derinlemesine tesir eden özlü ve beliğ ifade."
        if (s, a) in [(16, 40), (36, 82)]:
            return "Varlığı yokluktan varlığa çıkaran, iradenin anında maddeleşmesini sağlayan ontolojik yaratım buyruğu (kün fe yekûn)."
        if (s, a) == (58, 8):
            return "Ağızdan telaffuz edilmeksizin zihinde kurgulanan iç düşünce, niyet ve sessiz iddia (ve yekûlûne fî enfusihim)."
        if (s, a) in [(61, 2), (61, 3)]:
            return "Eyleme dökülmeyen, arkasında fiil bulunmayan ve derin tepki doğuran kuru iddia ve boş lafız."
        if (s, a) == (50, 18):
            return "İnsanın ağzından fırlatıp çıkardığı (lafz), kayda ve hesaba tabi tutulan sorumlu beyan."
        if (s, a) == (69, 44):
            return "Vahiy adına kendi arzusundan asılsız söz uydurup yakıştırma girişimi."
        if (s, a) == (22, 30):
            return "Gerçeği çarpıtan, haksızlığı meşrulaştıran düzmece ve yalan söz."
        if (s, a) == (6, 112):
            return "Aldatmak ve hakikatin üzerini örtmek amacıyla süslenip yaldızlanan çekici söylemler."
        if lemma == 'qaAla' and 'IMPV' in f:
            return f"Elçiye veya muhataba birlik, hakikat ve adalet ilkelerini doğrudan ilan etme ve bildirme buyruğu ({s}:{a})."
        if lemma == 'qawol':
            return f"Zihindeki düşünce veya hükmün somut bir beyana, ilkeye veya metne dönüştürülmüş hali ({s}:{a})."
        if '3MP' in f and 'PERF' in f:
            return f"Muhatap topluluğun geçmişte dile getirdiği tez, itiraz, soru veya kabul beyanı ({s}:{a})."
        if '3MP' in f and 'IMPF' in f:
            return f"İnsanların veya grupların ileri sürdüğü genel kanaat, iddia veya gerekçe ({s}:{a})."
        return f"Zihindeki niyet ve düşüncenin lafza veya tavra dökülerek muhataba beyan edilmesi ({s}:{a})."

    elif root_ar == 'ص-ل-و':
        if lemma == 'Salaw`p':
            if (s, a) == (2, 3):
                return "Vahye ve hakikate sırt dönmeyip yüzünü dönerek kurulan irtibat ve sorumluluk bağı; bu bağın ayakta tutulması ve kurumsallaştırılması."
            elif (s, a) in [(2, 43), (2, 83), (2, 110), (4, 77), (9, 71), (22, 41), (24, 56), (58, 13), (73, 20)]:
                return "Sorumluluk ve yöneliş bağının ayakta tutulması (arınma ve toplumsal dayanışma payı ile bütünlenişi)."
            elif (s, a) == (2, 157):
                return "Rablerinden gelen yakınlık, sahiplenme, manevi destek ve koruma bağları."
            elif (s, a) == (2, 238):
                return "İrtibat ve yöneliş bağlarının titizlikle korunması ve aksatılmaksızın sürdürülmesi."
            elif (s, a) in [(4, 101), (4, 102)]:
                return "Güvenlik riski ve çatışma ortamında irtibat ve yöneliş ritminin kısaltılarak ve nöbetleşe icra edilmesi."
            elif (s, a) in [(9, 99), (9, 103)]:
                return "Elçinin destek, sahiplenme ve esenlik duası; güvene erenler için manevi sükûnet kaynağı olan irtibat bağı."
            elif (s, a) == (22, 40):
                return "İçinde Allah'ın adının anıldığı ve bağlılık gösterilen toplanma ve yöneliş odakları."
            elif (s, a) == (62, 9):
                return "Toplumsal toplanma gününde (Cuma) ilahi çağrıya yönelerek kurulan ortak sorumluluk bağı."
            elif (s, a) == (107, 5):
                return "Yöneliş ve irtibat bağlarının özünden habersiz olan, onu sadece şekilsel gösterişe alet edenlerin gafleti."
            return "Bilinçli yöneliş, irtibat ve hakikate karşı kesintisiz sorumluluk bağı."
        elif lemma == 'Sal~aY`':
            if (s, a) == (33, 43):
                return "Allah'ın ve kozmik görevlilerinin kullarını karanlıklardan aydınlığa çıkarmak için onlara yönelip arkalarında durması ve desteklemesi."
            elif (s, a) == (33, 56):
                return "Allah'ın ve kozmik görevlilerin elçinin arkasında durup destek vermesi; güvene erenlerin de ona sırt dönmeyip tam bir bağlılıkla yanında durma çağrısı."
            elif (s, a) == (75, 31):
                return "Sırtını dönüp kaçmanın (tevellâ) zıddı olarak hakikate yönelip davanın arkasında durmama hali."
            elif (s, a) == (96, 10):
                return "Bir kulun yüce iradeye yüzünü dönüp bağlanmasını engellemeye kalkışan zorba tavır."
            elif (s, a) in [(87, 15), (108, 2)]:
                return "Yüzünü yalnızca Rabbine dönüp bağ kurdu, O'nun davasının arkasında durdu."
            return "Yüzünü dönerek yöneldi, irtibat kurdu, arkasında durup sahiplendi."
        elif lemma == 'muSal~iyn':
            return "Hakikate sırt dönmeyip sürekli yönelen, sorumluluk bağını diri tutan kimseler."
        elif lemma == 'muSal~FY':
            return "İrtibat, yöneliş ve odaklanma makamı / duruş alanı."
        return "Yöneliş, yakarış ve kesintisiz irtibat mekanizması."

    elif root_ar == 'س-ج-د':
        if lemma == 'sajada':
            if (s, a) in [(2, 34), (7, 11), (15, 29), (15, 30), (17, 61), (18, 50), (20, 116), (38, 72), (38, 73)]:
                return "Kibre ve dikleşmeye karşılık, yüce buyruğa ve insanın yeryüzü sorumluluğuna boyun eğip teslim olma emri."
            elif (s, a) == (12, 100):
                return "Yûsuf'un ailesinin onun ulaştığı ilahi lütuf ve makam önünde saygıyla boyun eğip tevazu göstermesi."
            elif (s, a) in [(13, 15), (16, 49), (22, 18), (55, 6)]:
                return "Göklerdeki ve yerdeki tüm varlıkların ve gölgelerinin kozmik nizama tam bir teslimiyetle boyun eğişi."
            elif (s, a) in [(3, 43), (4, 102), (9, 112), (22, 77), (48, 29)]:
                return "Zihinsel ve kalbî teslimiyetin bedensel tevazu ve boyun eğişle somutlaşması."
            return "Kendi benliğini ve direncini sıfırlayarak yüce iradeye ve emre teslim oldu, boyun eğdi."
        elif lemma == 'masojid':
            return "Benliğin sıfırlandığı, evrensel yasaya teslimiyetin ve yönelişin icra edildiği odak mekânı."
        elif lemma == 'saAjid':
            return "Kibir ve direncini kırıp yüce iradeye teslimiyet halinde olan kimseler."
        elif lemma == 's~ujuwd':
            return "Tam bir boyun eğiş ve teslimiyet durumu."
        return "Koşulsuz boyun eğme ve teslimiyet mekanizması."

    elif root_ar == 'ق-و-م':
        if lemma in ['>aqaAma', '<iqaAmat', '<iqaAm', 'm~uqiym']:
            return "İrtibatı, adaleti, ölçüyü veya sistemi çöküşten kurtarıp diri tutma, ayağa kaldırma ve kurumsallaştırma."
        elif lemma == 'qaAma':
            if (s, a) in [(2, 275), (4, 142), (17, 79), (72, 19), (73, 2), (74, 2)]:
                return "Uyuşukluğu bırakıp ayağa kalktı, harekete geçti, duruş sergiledi."
            return "Ayağa kalktı, duruş sergiledi, varlık gösterdi."
        elif lemma == 'qawom':
            return "Ortak bir davada, ilkede veya eylemde birlikte duruş sergileyen insan topluluğu."
        elif lemma == 'qiya`map':
            return "Büyük diriliş, nihai hesaplaşma ve tüm varlığın yüce huzurda ayağa kalkış anı."
        elif lemma in ['qay~uwm', 'qay~im', 'qay~imap']:
            return "Kendi varlığıyla ayakta duran, tüm mevcudatı ayakta tutan; dosdoğru, pürüzsüz ve sarsılmaz."
        elif lemma in ['maqaAm', 'muqaAm', 'muqaAmap']:
            return "Duruş yeri, onurlu makam, kalıcı yurt veya saygın mertebe."
        elif lemma in ['m~usotaqiym', '{sotaqa`mu']:
            return "Hiçbir sapma ve eğrilik göstermeksizin dosdoğru duran, istikamet üzere olan."
        elif lemma in ['qaw~a`miyn', 'qawaAm', 'qiyam', '>aqowam', 'taqowiym', 'qaA^}im', 'qaA^}imap']:
            return "Ölçüyü, dengeyi ve adaleti titizlikle ayakta tutan, sarsılmaz duruş sergileyen."
        return "Ayağa kalkış, sebat ve diriltme mekanizması."

    elif root_ar == 'ر-ك-ع':
        if lemma == 'yarokaEu':
            if (s, a) == (77, 48):
                return "Çağrıya kibirlenmeksizin boyun büküp eğilme emri (ve buna kibirle direnenlerin zıtlığı)."
            elif (s, a) == (38, 24):
                return "Dâvûd'un hatasını anlayıp kibrini kırması ve tevazu ile boyun eğerek af dilemesi."
            return "Kibir yapmayıp ortak iradeye boyun bükerek katıldı, tevazu gösterdi."
        elif lemma == 'raAkiE':
            return "Bireysel kibrini kırıp hakikate boyun eğerek ortak eyleme ve yönelişe katılanlar."
        return "Tevazu ile boyun eğme mekanizması."

    elif root_ar == 'ك-ف-ر':
        if lemma == 'kaAfuwr':
            return "Kokusuyla ve serinliğiyle diğer tüm tatları örten kâfûr karışımlı pınar (kökün fiziksel 'örtme' aslına bağlı özel isim)."
        elif lemma == '>akofara':
            return "İnsanın gerçeğin ve verilen nimetlerin üzerini örtmede ne kadar ileri ve nankör davrandığını vurgulayan taaccüp ifadesi (80:17)."
        elif lemma in ['kaf~ara', 'kaf~a`rap']:
            return "Kusurların ve sapmaların üzerini örtüp silme, telafi etme ve görünmez kılma."
        elif (s, a) == (57, 20):
            return "Tohumu toprağın altına gömüp üzerini örten çiftçiler (kökün ilk çıplak fiziksel anlamı)."
        elif lemma in ['kaAfir', 'ka`firuwn', 'kaAfirap', 'kawaAfir']:
            return "Apaçık olan gerçeğin, fıtratın veya verilen nimetin üzerini bilinçli olarak örtüp yok sayan kimse."
        elif lemma in ['kafuwr', 'kaf~aAr', 'kufuwr']:
            return "Nimetin değerini bilmeyip üzerini örtmekte son derece inatçı, nankör ve direngen olan."
        elif lemma in ['kufor', 'kuforaAn']:
            return "Gerçeğin üzerini örtme, nankörlük ve hakikati yok sayma durumu."
        return "Apaçık gerçeğin, fıtratın veya verilen nimetin üzerini örtüp gizleme, yok sayma."

    elif root_ar == 'ش-ك-ر':
        if lemma in ['$akuwr', '$aAkir']:
            return "Nimetin hakkını tam verip açığa vuran; az iyiliğe katbekat fazlasıyla karşılık veren."
        elif lemma in ['$ukor', '$ukuwr', 'm~a$okuwr']:
            return "Nimetin kıymetini bilip gereğini yapma; karşılığı verilmiş ve takdir edilmiş olan."
        elif lemma == '$akara':
            return "Nimetin üzerini örtmeyip hakkını vererek değerini açığa çıkardı ve gereğini yaptı."
        return "Nimetin değerini bilip açığa vurma mekanizması."

    elif root_ar == 'أ-م-ن':
        if lemma == "'aAmana":
            if 'li' in f or 'P:l' in f or (s, a) == (9, 61):
                return "Ona güvendi, sözünü doğru kabul edip itimat etti."
            return "Şüpheden kurtulup içsel güvene girdi, kalben emin olup bağlandı."
        elif lemma == '>amina':
            return "Korkudan ve tehditten uzaklaşıp tam bir emniyet ve güvende olma haline kavuştu."
        elif lemma == '{&otumina':
            return "Güven bağıyla kendisine emanet edilen sorumluluğu koruma altına aldı (2:283)."
        elif lemma in ['mu&omin', 'm~u&omina`t', 'm~u&ominap']:
            return "Kendisi güvene giren ve çevresine güven veren, şüpheden arınmış emin kimse."
        elif lemma in ['>ama`nat', '>ama`na`t']:
            return "Güvene dayalı olarak korunan emanet ve sorumluluk."
        elif lemma in ['>amon', '>amanap']:
            return "Korku ve tehditten kurtulup emin olma, içsel ve toplumsal güvenlik hali."
        elif lemma == 'ma>oman':
            return "Kişinin her türlü saldırı ve korkudan emin kılındığı güvenli sığınak (9:6)."
        elif lemma in ["'aAmin", "'aAminiyn", "'aAminap"]:
            return "Her türlü korku ve tehlikeden emin, güvende olan."
        elif lemma in ['>amiyn', 'ma>omuwn']:
            return "Kendisine tam itimat edilen, güvenilir olan."
        elif lemma == '<iyma`n':
            return "Korkudan ve şüpheden arınmış sarsılmaz içsel emniyet ve güven bağı."
        return "Korkudan kurtulup güvende olma ve eminlik mekanizması."

    elif root_ar == 'ن-ف-ق':
        if lemma in ['>anfaqa', '<infaAq', 'munfiqiyn', 'nafaqap', 'nafaqa`t']:
            return "Eldeki değeri istifleyip dondurmayarak dolaşıma sokma, toplumun faydasına akıtma."
        elif lemma in ['naAfaqu', 'muna`fiquwn', 'muna`fiqa`t', 'nifaAq']:
            return "Tünelin iki ucundan girip çıkar gibi çift taraflı oynama, iki çıkışlı kaypaklık sergileme."
        elif (s, a) == (6, 35) or lemma == 'nafaq':
            return "Yerin derinliklerine inen tünel / gizli geçit (kökün ilk fiziksel anlamı)."
        return "Tedavüle sokulan pay, harcama veya gizli tünel mekanizması."

    elif root_ar == 'ك-و-ن':
        if lemma == 'makaAnat':
            return "Öznenin sahip olduğu sabit duruş seviyesi, konum ve elindeki imkân zemini üzere eyleme geçmesi."
        elif lemma == 'm~akaAn':
            if (s, a) == (10, 28):
                return "Hesap gününde herkesin yerinden kımıldamadan kendi duruş konumunda sabitlenmesi buyruğu (10:28)."
            elif (s, a) in [(4, 20), (16, 101)]:
                return "Bir unsurun veya önceki hükmün yerine yeni bir unsurun ikame edilip yerleştirilmesi."
            elif (s, a) == (7, 143):
                return "Dağın kendi zemininde sarsılmadan sabit kalıp kalamayacağı üzerinden kozmik sınama (7:143)."
            elif 'POS:LOC' in f:
                return "Kişinin çevreden ayrılıp belirli bir yönde/noktada yer tuttuğu somut konum (mekân zarfı)."
            return "Varlığın veya eylemin yerleşip yer tuttuğu somut mevki, duruş noktası ya da konum."
        elif lemma == 'kaAna':
            if (s, a) in [(2, 117), (3, 47), (3, 59), (6, 73), (16, 40), (19, 35), (36, 82), (40, 68)]:
                return "İlahi iradenin soyut tasarımdan somut varlık sahasına geçiş buyruğu ve anında vuku buluşu (kün feyekûn)."
            elif (s, a) == (2, 280):
                return "Tâm kullanım: Darlık içine düşen borçlu ortaya çıkıp bulunursa kolaylık süresi tanınması."
            elif (s, a) in [(2, 148), (4, 78)]:
                return "Tâm kullanım: Öznelerin nerede ve hangi noktada yer tutup bulunuyor olurlarsa olsunlar aynı kuşatma içinde olmaları."
            elif (s, a) in [(2, 193), (8, 39), (5, 71), (8, 73)]:
                return "Tâm kullanım: Toplumda baskı ve karmaşanın (fitnenin) baş gösterip yer tutması ya da tamamen ortadan kaldırılması."
            elif (s, a) in [(5, 116), (7, 13), (7, 89), (24, 16)]:
                return "Aidiyet/tâm kullanım: Bir iddia, yetki veya sözün o özneye düşmemesi, onun alanında vuku bulamayacağı."
            elif (s, a) == (2, 143):
                return "İnsanlığa örnek bir orta/denge topluluğu olarak konumlandırılma ve güven bağının sınanması bağlamı."
            elif (s, a) in [(14, 44), (14, 46), (35, 41)]:
                return "Mesânî zıddı 'zeval' (yerinden kayıp dağılma) ile aynı ayette köklü sabitlik ve gerçekleşme karşılaştırması."
            elif (s, a) == (19, 20):
                return "Kısa cezm 'lem eku': Hiçbir beşer teması ve iffet dışı durum vuku bulmamışken yeni bir varlığın doğuşu."
            elif (s, a) in [(19, 67), (76, 1)]:
                return "İnsanın henüz hiçbir somut varlık ve yer tutmadığı yokluk evresinden varlık sahnesine çıkarılışı."
            elif (s, a) == (21, 69):
                return "Dişil emir 'kûnî': Yakıcı ateşin doğasında serinlik ve esenlik halinin doğrudan kurulması."
            elif (s, a) in [(74, 43), (74, 44)]:
                return "Kısa cezm 'lem neku': Yönelip irtibat kuranlardan ve yoksulu doyuranlardan olma sorumluluğunu terk ediş itirafı."
            elif (s, a) == (75, 37):
                return "Kısa cezm 'e-lem yeku': İnsanın başlangıçta atılan bir damla sıvı halinden aşama aşama varlık kazanması."
            elif (s, a) == (112, 4):
                return "Mutlak Tevhid ilkesi: O'na denk ve eşdeğer hiçbir varlığın vuku bulmamış olması."
            elif 'IMPV' in f:
                return "Belirli bir duruş, nitelik veya eylem konumuna geçip orada sağlamca yer tutma buyruğu."
            elif 'MOOD:JUS' in f:
                return "Şart, nehiy veya olumsuzlama altında bir durumun vuku bulup bulmamasını kesinleyen mecmû oluş çekimi."
            elif 'MOOD:SUBJ' in f:
                return "Amaç, beklenti veya gelecekteki bir oluşun gerçekleşme zeminini kuran nasb edilmiş muzâri çekim."
            elif 'IMPF' in f:
                return "Bir durumun ya da niteliğin süreç içinde süreklilikle vuku bulması ve gerçekleşmesi."
            return "Bir olayın fiilen vuku bulması veya öznenin zamanlı ya da zaman-üstü bir nitelik içinde sağlamca sabitlenmesi."

    elif root_ar == 'ر-ب-ب':
        if lemma == 'rab~a`niy~in':
            if (s, a) == (3, 79):
                return "Kuran içi tanım: Kitabı öğretip müzakere ederek toplumu aşama aşama eğiten ve olgunlaştıran bilginler olun çağrısı (3:79)."
            return "Kitap emanetini koruyup toplumu adalet ve bilgiyle eğitip denetlemekle yükümlü önderler (5:44, 5:63)."
        elif lemma == 'rib~iy~uwn':
            return "Ortak ilke ve terbiye ocağında birbirine kenetlenerek zorluğa karşı dik duran kalabalık topluluklar (3:146)."
        elif lemma == 'raba`^}ib':
            return "Kişinin doğrudan kendi himayesi ve kucağında besleyip büyüttüğü üvey kız çocukları (4:23)."
        elif lemma == 'rab~':
            if (s, a) == (12, 39):
                return "Mesânî zıtlığı: Birbiriyle çekişen parçalı sahte efendiler (erbâb) ile tek bütünleştirici merkez karşılaştırması (12:39)."
            elif (s, a) in [(3, 64), (3, 80), (9, 31)]:
                return "İnsanların, elçilerin veya öğreti önderlerinin dokunulmaz sahte otorite ve efendiler (erbâb) konumuna çıkarılmasının reddi."
            elif (s, a) in [(12, 23), (12, 41), (12, 42)] or ((s, a) == (12, 50) and 'GEN' in f):
                return "Yûsuf anlatısında 'rabb' kavramının doğrudan beşerî bakıcı, ev sahibi veya ülke hükümdarı anlamında somut kullanımı."
            elif (s, a) in [(6, 76), (6, 77), (6, 78), (53, 49), (79, 24)]:
                return "Sönüp kaybolan gök cisimlerinin veya kibirli yöneticinin gerçek besleyici-yetiştirici otorite (Rabb) olamayacağının vurgulanması."
            elif (s, a) in [(1, 2), (114, 1)]:
                return "Varlıkları sadece ilk başta kurmakla kalmayıp aşama aşama besleyip geliştirerek kemâle erdiren bütünleştirici otorite (1:2, 114:1)."
            elif (s, a) in [(25, 30), (43, 88)]:
                return "Elçinin doğrudan kendi yetiştiricisiyle kurduğu derin yakınlık ve içten yakınma nidası (yâ rabbi)."
            elif (s, a) in [(4, 65), (6, 30), (15, 92), (19, 68), (51, 23), (64, 7)] and 'GEN' in f:
                return "Varlığı besleyip ayakta tutan Rabb'in otoritesini tanık göstererek kesin gerçekliğin vurgulanması."
            elif (s, a) in [(96, 1), (96, 3)]:
                return "İlk vahyedilen surede okumanın, bilginin ve insan gelişiminin doğrudan 'seni yetiştiren Rabb' ile bağlanması."
            return "Varlığını iyelik bağıyla sahiplenip bırakmayan, kesintisiz besleyip onararak aşama aşama olgunluğa ulaştıran koruyucu otorite."

    elif root_ar == 'ع-ل-م':
        if lemma == 'Eala`ma`t':
            return "Kökün ilk fiziksel anlamı: Yolcuların kara ve denizde yönünü bulması için dikilmiş somut işaretler ve belirtiler (16:16)."
        elif lemma == '>aEola`m':
            return "Kökün somut fiziksel anlamı: Denizde süzülen dev gemilerin benzetildiği yüksek dağlar ve ufuktaki nişan kuleleri (42:32, 55:24)."
        elif lemma == 'muEal~am':
            return "Eleştiricilerin elçiye attığı 'başkalarından gizlice eğitilmiş/sufle almış' iftirası (44:14)."
        elif lemma in ['m~aEoluwm', 'm~aEoluwma`t']:
            if (s, a) in [(2, 197), (22, 28)]:
                return "Vakti, günleri ve kuralları önceden açık nişanlarla sabitlenip belirlenmiş büyük yöneliş dönemleri."
            return "Ölçüsü, vakti, payı veya eceli kesin sınırlarla işaretlenip belirlenmiş olan (15:21, 70:24, 77:22)."
        elif lemma == 'Ea`lamiyn':
            return "Üzerindeki düzenli iz ve işaretlerle Yaratıcısının varlığını ve yasalarını tanıtan tüm varlık ve yaşam katmanları."
        elif lemma in ['Eal~a`m', 'Ea`lim']:
            if lemma == 'Ea`lim' and 'MP' in f:
                return "Olayların içindeki izleri ve anlamı bilip ayırt edenler."
            return "Duyuların ötesindeki görünmeyen alanlar dahil bütün iz ve gerçekleri eksiksiz kuşatıp bilen."
        elif lemma == '>aEolam':
            return "Kimin hangi konumda, gizlide ve açıkta ne taşıdığını diğer tüm öznelerden üstün biçimde ayırt eden."
        elif lemma == 'Ealiym':
            if 'MP' in f:
                return "Varlıktaki düzen işaretlerini derinden okuyup çözümleyen bilginler ve hakikat arayıcıları (26:197, 35:28)."
            return "Hiçbir belirtiyi ve iç niyeti kaçırmadan varlığın tüm ayrıntılarını köklü biçimde bilen."
        elif lemma == 'yataEal~amu':
            return "Bozguncu odakların öğrettiği zararlı bilgi ve ayırıcı yöntemleri kendi çabasıyla öğrenip edinme süreci (2:102)."
        elif lemma == 'Eal~ama':
            if (s, a) in [(96, 4), (96, 5)]:
                return "İnsana kalem aracılığıyla ve bilmediği her yeni aşamada zihne iz bırakarak bilgi kazandırılması (96:4-5)."
            elif (s, a) == (2, 31):
                return "İnsana tüm varlıkları ayırt edici ad ve kavramlarıyla tanıma donanımının kazandırılması (2:31-32)."
            elif (s, a) == (5, 4):
                return "Kökün fiziksel iz bırakma yönü: Eğitilen av hayvanlarının dahi yöntem öğretimiyle (tüallimûnehünne) eğitilmesi (5:4)."
            elif (s, a) == (49, 16):
                return "İnsanların kendi yaşam düzenleri ve iç dünyaları hakkında her şeyi zaten bilen Yaratıcıya bilgi taslamasının eleştirisi (49:16)."
            elif 'PASS' in f:
                return "Kişiye özel bir hikmet, dil veya ayırt edici yetenek kazandırılıp öğretilmiş olması (6:91, 18:66, 27:16)."
            return "Başkasına ayırt edici iz, yöntem, yazı veya kavram aktararak öğretme ve eğitme eylemi (Form II)."
        elif lemma == 'Eilom':
            return "Zan, tahmin ve ölçüsüz körü körüne tepkinin (cehl) karşıtı olarak sağlam iz ve kanıtlara dayanan kesin kavrayış."
        elif lemma == 'Ealima':
            if (s, a) == (24, 31):
                return "Saklı tutulan çekici süslerin dışarıdan bilinip dikkat çekmemesi ölçüsü (meçhul çekim: li-yu'leme)."
            elif (s, a) in [(10, 36), (11, 46), (2, 146), (27, 65), (30, 7), (31, 34)]:
                return "Mesânî ve Furûk bağlamı: Zan, cehalet, yüzeysel farkındalık ve gizlemenin karşısında kesin bilgi ve kavrayış ölçüsü."
            elif 'IMPV' in f:
                return "Gerçeğin ve sorumluluğun açık kanıtını kesin olarak bilip ona göre duruş alma çağrısı."
            return "Bir şeyin üzerindeki ayırt edici izi, delili ve niyeti algılayıp tereddütsüz kavramak ve bilmek."

    elif root_ar == 'أ-ت-ي':
        if lemma == 'ma>otiy~N':
            return "Kesinleşen vaadin vaktine mutlaka gelinip varılacağının ve fiilen gerçekleşmiş sayılacağının ilanı (19:61)."
        elif lemma in ['mu&otuwn', "<iytaA'N"]:
            return "Bireyin ve toplumun arınma ile dayanışma payını aksatmadan hak sahiplerinin önüne akıtıp teslim etmesi."
        elif lemma == 'A^tiy':
            return "Saatin, hesabın veya her bireyin hiçbir engel tanımadan doğrudan huzura yürüyüp gelmekte olması."
        elif lemma == 'A^taY':
            if 'PASS' in f:
                return "Bilgi, kitap, hikmet, yönetim veya nimet payının kişiye yahut topluluğa ulaştırılıp emanet edilmiş olması."
            elif (s, a) in [(17, 26), (30, 38), (59, 7)]:
                return "Hak sahibinin ve toplumun meşru payını oyalamadan ve cimrilik etmeden doğrudan önüne getirip teslim etmek."
            return "Form IV: Bir değeri, belgeyi, bilgiyi veya toplumsal arınma payını muhatabın önüne akıtıp eksiksiz teslim etmek."
        elif lemma == '>ataY':
            if (s, a) == (2, 25):
                return "Form I meçhul: Bahçedeki rızıkların önceki nimetlere görünümce benzer biçimde önlerine getirilip sunulması (2:25)."
            elif (s, a) == (41, 11):
                return "Gökler ve yerin yaratılış yasasına ister uyumla ister zorunlu olarak yönelip gelmesi ve itaatle cevap vermesi (41:11)."
            elif (s, a) == (2, 189):
                return "İşlere ve mekânlara arkadan dolanarak değil doğrudan doğru kapısından ve meşru usulünden girme ilkesi (2:189)."
            elif (s, a) in [(4, 15), (7, 80)]:
                return "Doğrudan geçişli kullanım: Çirkin ve sınırı aşan bir eyleme kasıtla yönelip onu bilfiil işlemek."
            elif (s, a) in [(2, 23), (27, 38)]:
                return "بِـ edatı ile geçişli: Somut bir kanıt, söz veya nesneyi bizzat getirip ortaya koymak."
            elif (s, a) == (20, 60):
                return "Mesânî karşıtlığı: Firavun'un önce sırt dönüp uzaklaşmasının ardından tüm düzenini toplayıp tekrar karşıya çıkması."
            return "Suyun kanalından engelsizce akması gibi; bir vaktin, olayın veya öznenin hedefe dosdoğru yönelip gelmesi."

    elif root_ar == 'ش-ي-أ':
        if lemma == "$aYo'":
            if (s, a) == (5, 101):
                return "Gayr-ı munsarıf çoğul kullanım (عَنْ أَشْيَآءَ): Açıklanınca kişilere ağır gelecek gereksiz mesele ve olguları kurcalamama uyarısı (5:101)."
            elif (s, a) in [(7, 85), (11, 85), (26, 183)]:
                return "Çoğul kullanım (أَشْيَآءَهُمْ): Ölçü ve tartıda insanların hak ettikleri somut malları, eşyayı ve ekonomik değerleri eksiltmeme ilkesi."
            elif (s, a) == (18, 23):
                return "Rasm anomalisi (لِشَا۟ىْءٍ - fazla elif-i zâide): Gelecekte gerçekleşecek herhangi bir iş veya olay hakkında mutlak kesinlik iddiasında bulunmama uyarısı (18:23)."
            elif (s, a) in [(16, 40), (36, 82)]:
                return "Aynı ayette Furûk (أَرَادَ + شَيْء): Bir nesne veya olgunun oluşmaya yöneltilmesiyle (irâde) somut 'şey' olarak varlık kazanması arasındaki bağ."
            elif (s, a) == (42, 11):
                return "لَيْسَ كَمِثْلِهِۦ شَىْءٌ: Evrendeki tüm sonlu varlık birimlerinden (şey) bütünüyle benzersiz ve aşkın olma yasası (42:11)."
            elif (s, a) == (19, 67):
                return "وَلَمْ يَكُ شَيْـًٔا: Yokluktan ve henüz belirgin bir birim olmamaktan somut varlık birimine (şey) geçişin hatırlatılması (19:67)."
            elif '|NOM' in f:
                return "Nekre merfû kullanım (Kuran'da الـ takısı hiç almaz): Sınırları işaret edilebilen her türlü varlık birimi, nesne veya durum."
            return "Kuran boyunca istisnasız nekre kalan bu isim, zerreden kozmosa kadar işaret edilip hükme konu olan en yalın 'varlık birimi / pay / olgu' anlamını taşır."
        elif lemma == "$aA^'a":
            if (s, a) == (10, 99):
                return "Çift yönlü Mesânî karşıtlığı (شَاءَ ↔ ك-ر-ه): Yaratıcı dileseydi herkesi tek çizgiye çekerdi; irade alanı açık bırakıldığı için insanlara zorlama uygulanamaz (10:99)."
            elif (s, a) == (18, 29):
                return "Bireysel tercih özgürlüğü: Gerçeği güvenle onaylama veya üzerini örtme konusunda kişiye tanınan seçme iradesi ve bunun sorumluluğu (18:29)."
            elif (s, a) in [(2, 35), (7, 19)]:
                return "İkil mâzî (حَيْثُ شِئْتُمَا): İlk insan çiftine yasaklı sınır dışında sunulan geniş ve özgür seçim alanı."
            elif (s, a) == (7, 156):
                return "Kuran'daki tek 1. tekil şahıs muzari (أَشَآءُ) ile كُلَّ شَىْءٍ kapsamının aynı cümlede buluşması: Sarsıcı yaptırımın seçili alana, koruyucu şefkatin ise her varlık birimine yayılması (7:156)."
            elif (s, a) == (11, 87):
                return "Rasm anomalisi (نَشَٰٓؤُا۟): Topluluğun kendi mal ve kaynakları üzerinde sorumsuzca dilediğini yapma iddiası (11:87)."
            elif (s, a) == (28, 68):
                return "Aynı ayet içi Furûk: يَخْلُقُ مَا يَشَآءُ (iradesiyle var edip oldurmak) ile وَيَخْتَارُ (var edilenler arasından en uygun olanı seçmek) ayrımı (28:68)."
            elif (s, a) in [(76, 30), (81, 29)]:
                return "İnsan seçiminin (تَشَآءُونَ) evrensel düzen ve Yaratıcı iradesi (أَن يَشَآءَ ٱللَّهُ) çerçevesi içinde anlam bulması."
            elif (s, a) in [(6, 39), (42, 24)]:
                return "Rasm özelliği (يَشَإِ): Meczûm fiilin geçiş kesresiyle yâ harfi üzerine hamze alarak yazıldığı özel şart cümlesi."
            elif '|2MP' in f and 'PERF' in f:
                return "Muhataplara yöneltilen iradî seçim veya eylem sorumluluğu alanı (şartlı ya da uyarıcı serbestlik)."
            elif 'MOOD:JUS' in f:
                return "Şart cümlesinde meczûm meşîet: Bir durumun gerçekleşmesinin doğrudan seçip oldurma iradesine bağlanması."
            return "Form I aktif meşîet fiili: Belirsiz ihtimaller içinden bir yönü tercihle seçmek veya kudretle fiilen oldurup varlık sahasına çıkarmak."

    elif root_ar == 'ب-ي-ن':
        if lemma == 'bayon':
            if (s, a) in [(16, 66), (86, 7)]:
                return "Fiziksel kök örneği (مِنۢ بَيْنِ): İki bedensel katman veya doku arasındaki aralıktan süzülüp dışarı çıkma."
            elif (s, a) == (6, 94):
                return "İsimleşmiş kullanım (بَيْنَكُمْ): Tarafları birbirine bağlayan ara mesafenin ve dayanışma bağının tamamen kopması (6:94)."
            elif (s, a) == (18, 78):
                return "Ayrılık eşiği (بَيْنِى وَبَيْنِكَ): İki yol arkadaşının ortak yolculuğunun bittiği kesin sınır çizgisi (18:78)."
            elif (s, a) == (2, 68):
                return "Sayısal/niteliksel ara konum: İki uç özellik (çok yaşlı ve çok genç) arasındaki orta denge noktası (2:68)."
            elif pos == 'N':
                return "İki kişi, kütle veya cephe arasındaki sınır boşluğu ve etkileşim eşiği."
            return "İki taraf, nesne veya zaman eşiği arasındaki ara mesafe, ortak alan ya da ön cephe."
        elif lemma == 'yubiynu':
            return "Form IV (43:52): Sözü karıştırmadan tane tane ve akıcı biçimde dışa vurup anlaşılır kılmak üzerine kurulu alaycı küçümseme."
        elif lemma == 'tasotabiyna':
            return "Form X (6:55): Olgular tek tek ayrıştırıldığında suçlu ve yıkıcı yolun sınırının keskin biçimde ortaya çıkıp belirginleşmesi."
        elif lemma == 'musotabiyn':
            return "Form X sıfat (37:117): Hakkı yanlıştan bütünüyle ayırarak anlamı berraklaşmış yazılı belge."
        elif lemma == 'tiboya`n':
            return "Yoğunlaştırma mastarı (16:89): Yaşamın her temel alanındaki ilkeleri karıştırmadan ayrıştırıp ortaya seren kapsamlı açıklama."
        elif lemma == 'bayaAn':
            if (s, a) == (55, 4):
                return "İnsanın zihnindekini ayırt edip anlaşılır sembollerle ifade etme ve gerçeği dışa vurma yetisi (55:4)."
            elif (s, a) == (75, 19):
                return "Metnin parçaları arasındaki anlam sınırlarını açığa çıkarıp bütünlük içinde açıklama güvencesi (75:19)."
            return "Tarihsel olgulardan çıkarılan açık ve belirgin hakikat sunumu (3:138)."
        elif lemma == 'bay~in':
            return "Tekil sıfat (18:15): İddiayı ayakta tutabilecek, kuşkuya yer bırakmayan açık ve sağlam dayanak (18:15)."
        elif lemma in ['m~ubay~inap', 'm~ubay~ina`t']:
            if (s, a) in [(4, 19), (33, 30), (65, 1)]:
                return "Form II ism-i fâil (بِفَٰحِشَةٍ مُّبَيِّنَةٍ): Üstü örtülemeyecek biçimde açığa çıkmış ve sınırları dışa vurmuş ağır taşkınlık."
            return "Form II ism-i fâil (مُّبَيِّنَٰتٍ): Bulanıklığı dağıtarak yönü ve gerçeği doğrudan açığa çıkaran açık işaretler."
        elif lemma == 'm~ubiyn':
            return "Form IV ism-i fâil (119 geçiş): Kendi içinde tutarlı ve açık olduğu gibi muhatabın önündeki belirsizliği de kesip atan netlik niteliği."
        elif lemma == 'bay~inap':
            if (s, a) == (2, 185):
                return "Aynı ayet içi Furûk (هُدًى + بَيِّنَٰت + فُرْقَان): Doğru yönü gösteren rehberliğin somut kanıtları ve haklı-haksız ayıracı (2:185)."
            return "Kişiyi veya toplumu kararsızlıktan kurtaran, doğruluğu nesnel biçimde ayırt edilen açık kanıt ve belge."
        elif lemma == 'bay~anu':
            if (s, a) in [(2, 159), (3, 187)]:
                return "Mesânî zıtlığı (بَيَّنَ ↔ كَتَمَ): Gerçeği insanlara açıp netleştirmek ile onu gizleyip saklamak arasındaki mutlak karşıtlık."
            elif (s, a) == (5, 15):
                return "Mesânî zıtlığı (يُبَيِّنُ ↔ تُخْفُونَ): Yazılı metinde saklanıp örtülen esasları gün yüzüne çıkarıp açmak (5:15)."
            elif (s, a) in [(2, 68), (2, 69), (2, 70)]:
                return "Teşâbüh zıddı (يُبَيِّن ↔ تَشَٰبَهَ): Birbirine benzeyip karışan seçeneklerin niteliklerini ayırarak netleştirmek."
            elif (s, a) == (43, 63):
                return "Tek 1. tekil şahıs Form II: Üzerinde ayrılığa düşülen düğümleri açıp taraflara netleştirmek (43:63)."
            return "Form II: Karışmış veya gizli kalmış bir ilkenin sınırlarını ayırarak herkes için görünür ve anlaşılır kılmak."
        elif lemma == 'tabay~ana':
            if (s, a) == (2, 187):
                return "Fiziksel ayraç tanımı: Şafak vaktinde beyaz çizginin siyah çizgiden gözle seçilip ayrışması (2:187)."
            elif (s, a) == (2, 256):
                return "Zorlamasız seçim ilkesi: Sağduyulu doğrultunun sapkınlıktan kesinkes ayrışıp netleşmesi (2:256)."
            elif (s, a) in [(4, 94), (49, 6)]:
                return "Form V emir (فَتَبَيَّنُوٓا۟): Gelen bir habere veya karşıdaki insana karşı hüküm vermeden önce kanıtları araştırıp netleştirin."
            elif (s, a) == (34, 14):
                return "Gizli güçlerin gerçek sınırının olayların sonucunda açığa çıkıp herkesçe netleşmesi (34:14)."
            return "Form V: Taraflar arasındaki belirsizliğin dağılması ve gerçeğin kendi sınırlarıyla seçilir hale gelmesi."

    elif root_ar == 'ر-س-ل':
        if lemma == 'murosala`t':
            return "Fiziksel kök (77:1): Peş peşe dizilmiş dalgalar halinde salınıp akıtılan rüzgâr veya doğa akımları."
        elif lemma in ['murosil', 'murosilap']:
            if (s, a) == (35, 2):
                return "Mutlak Mesânî karşıtlığı (يُمْسِكْ ↔ مُرْسِل): Tutup alıkonulan bir nimeti sonradan salıverip serbest bırakabilecek hiçbir güç yoktur (35:2)."
            elif (s, a) == (27, 35):
                return "Siyasi ve sivil diplomatik kullanım: Sebe kraliçesinin hediye paketiyle elçi heyeti göndermesi ve dönüşünü gözlemesi (27:35)."
            elif (s, a) == (54, 27):
                return "Sınama aracı olarak dişi deveyi toplumun içine serbest bırakıp salıverme eylemi (54:27)."
            return "Merkezden mesaj, elçi veya görev akımını başlatıp hedefe doğru salıveren otorite."
        elif lemma in ['risaAlap', 'risa`la`t']:
            return "Elçinin değiştirmeden hedefe iletmekle yükümlü olduğu yazılı veya sözlü görev bildirisi ve ilke paketi."
        elif lemma == 'm~urosal':
            if '|ADJ|' in f:
                return "Merkezden görevli kılınmış taşıyıcılara önceden verilmiş değişmez karar güvencesi (37:171)."
            elif (s, a) == (27, 35):
                return "Diplomasi elçilerinin karşı taraftan hangi sonuç ve yanıtla geri döneceğinin beklenmesi (27:35)."
            return "Form IV ism-i mef'ûl: Bir otorite veya kaynak adına mesaj, uyarı ya da destek ulaştırmak üzere gönderilmiş elçi."
        elif lemma == 'rasuwl':
            if (s, a) == (12, 50):
                return "Sivil/saray kullanımı: Kralın zindana çağrı için gönderdiği saray görevlisi (12:50)."
            elif (s, a) == (20, 47):
                return "İkil kullanım (رَسُولَا رَبِّكَ): Ortak bir özgürleştirme göreviyle aynı merkeze gönderilen iki elçi (20:47)."
            elif (s, a) in [(22, 52), (33, 40)]:
                return "Aynı ayet içi Furûk (رَسُول vs نَبِيّ): Önemli bilgi alan haberci ile o bilgiyi topluma taşımak üzere gönderilen görevli elçi farkı."
            elif (s, a) in [(22, 75), (35, 1), (6, 61), (19, 19)]:
                return "Kapsayıcı kullanım: Yalnız insanlar değil, evrensel düzeni ve yaşam süresini yöneten göksel görevliler de bu unvanla adlandırılır."
            return "Kaynak ile hedef arasında mesajı, yasayı veya görevi eksiksiz taşıyan güvenilir görevli elçi."
        elif lemma == '>arosala':
            if (s, a) in [(7, 57), (15, 22), (25, 48), (27, 63), (30, 48), (30, 51), (35, 9), (11, 52), (71, 11)]:
                return "Doğa yasalarıyla fiziksel salınım: Rüzgârları, bulutları ve sağanak yağmuru gökyüzünden yeryüzüne serbest bırakıp akıtmak."
            elif (s, a) in [(7, 133), (13, 13), (17, 68), (17, 69), (54, 19), (54, 31), (54, 34), (55, 35), (67, 17), (105, 3)]:
                return "Doğal sarsıntı akımı: Tufan, yıldırım, taş yağmuru, alev dalgası, dondurucu fırtına veya kuş sürülerini hedef üzerine salmak."
            elif (s, a) in [(12, 19), (12, 31), (12, 45), (12, 66)]:
                return "Beşerî ve günlük yaşam kullanımı: Kuyuya sucu göndermek, eve davetçi yollamak veya kardeşi yol arkadaşlarıyla beraber salıvermek."
            elif (s, a) == (19, 83):
                return "Kışkırtıcı ve yıkıcı güçlerin, bile isteye o yolu seçen bozguncuların üzerine serbest bırakılıp salınması (19:83)."
            elif 'PASS' in f:
                return "Edilgen Form IV: Belirli bir bildiri, kanıt ya da uyarı göreviyle merkezden muhatapların üzerine gönderilmiş olmak."
            return "Form IV: Bir görevliyi, elçiyi veya kuvveti tutulu olduğu yerden serbest bırakıp belirlenen amaca yöneltmek."

    elif root_ar == 'أ-ر-ض':
        if (s, a) in [(2, 22), (20, 53), (55, 10), (71, 19), (78, 6), (79, 30), (88, 20)]:
            return "Yaşam döşeği ve denge yatağı: Canlıların üzerinde barınması ve yürümesi için serilip düzlenen temel yaşam zemini."
        elif (s, a) == (11, 44):
            return "Mesânî eşleşmesi (يَٰٓأَرْضُ ↔ يَٰسَمَآءُ): Tufan suyunu içine çekmesi emredilen alt taban ile yağışını kesen üst katmanın uyumlu hareketi (11:44)."
        elif (s, a) == (41, 11):
            return "Kozmik yasa uyumu: Üst duman/gaz katmanıyla birlikte varoluş yasasına ister istemez yönelip katılan yer tabanı (41:11)."
        elif (s, a) == (65, 12):
            return "Yedi gök katmanı ile tekil kalarak benzer yasalarla işleyen alt yer düzlemi (65:12)."
        elif (s, a) == (14, 48):
            return "Evrensel dönüşüm: Mevcut yer düzeninin ve göklerin bambaşka bir yeni yapıya dönüştürülmesi (14:48)."
        elif (s, a) == (34, 14):
            return "Küçük toprak/yer canlısı (دَآبَّةُ ٱلْأَرْضِ): Çürümüş ahşap dayanağı kemirerek gerçeği açığa çıkaran yer böceği (34:14)."
        elif (s, a) == (12, 9):
            return "Nekre kullanım (أَرْضًا): Kişinin çevresinden uzaklaştırılıp atılacağı belirsiz, ıssız bir diyar (12:9)."
        elif (s, a) == (31, 34):
            return "Nekre kullanım (بِأَىِّ أَرْضٍ): Hiçbir insanın hangi toprak parçasında yaşamını tamamlayacağını önceden kestirememesi (31:34)."
        elif (s, a) == (33, 27):
            return "Aynı ayette katman farkı: Yaşanan yer ve yerleşik evlerden hemen sonra gelen, henüz ayak basılmamış yeni coğrafya (33:27)."
        elif (s, a) in [(4, 97), (29, 56), (39, 10)]:
            return "Baskı altındaki dar çevreye karşı hareket imkânı sunan geniş ve açık yaşam alanı (أَرْضٌ وَٰسِعَةٌ)."
        elif (s, a) in [(99, 1), (99, 2)]:
            return "Büyük sarsıntı anında yer kabuğunun sarsılıp kendi içindeki birikmiş ağırlıkları dışa atması (99:1-2)."
        return "Üstteki gök katmanlarının karşısındaki temel alt zemin; kozmik yeryüzü veya toplumların üzerinde eylem ürettiği coğrafî alan."

    elif root_ar == 'ي-و-م':
        if (s, a) == (1, 4):
            return "Bütün eylemlerin karşılığının eksiksiz hesaplandığı nihai denetim ve karşılık döneminin mutlak sahibi (1:4)."
        elif (s, a) == (2, 85):
            return "Dünya yaşamında rüsva olma ve büyük hesaplaşma gününde en ağır yaptırımla karşılaşma durumu (2:85)."
        elif (s, a) == (2, 184):
            return "Sağlık veya yolculuk durumu olanlar için başka belirli, sayılı günler boyunca telafi edilmesi gereken zaman dilimi (2:184)."
        elif (s, a) == (2, 203):
            return "Sınırlı günlerde anma ve bu alanı iki gün içinde veya sonrasında acele etmeden tamamlama esnekliği (2:203)."
        elif (s, a) == (2, 259):
            return "Uzun bir ölüm uykusundan uyananın zaman algısının 'bir gün ya da günün bir bölümü' şeklinde yanıltıcı hissedilmesi ve yüz yıllık süreçle yüzleşmesi (2:259)."
        elif (s, a) == (3, 24):
            return "Ateşin kendilerine yalnızca 'sayılı birkaç gün' dokunacağı yönündeki temelsiz ve seçici dokunulmazlık iddiası (3:24)."
        elif (s, a) == (3, 140):
            return "Tarihin dönüm noktası olan zafer ve yenilgi günlerinin insanlar ve toplumlar arasında nöbetleşe döndürülmesi yasası (3:140)."
        elif (s, a) == (5, 3):
            return "Hakikat karşıtlarının umudunu kestiği ve ilahi yaşam düzeninin tamamlandığı kesin dönüm noktası olarak 'bugün' vurgusu (5:3)."
        elif (s, a) == (10, 45):
            return "Yeniden dirilişle toplanılacak gün, kişinin dünyadaki tüm ömrünü sanki 'gündüzün yalnızca bir saati' kadar kısa algılaması (10:45)."
        elif (s, a) == (14, 5):
            return "Toplumu karanlıklardan aydınlığa çıkarma göreviyle, Allah'ın tarihteki lütuf ve deneme dönemlerini (eyyâmullah) hatırlatma çağrısı (14:5)."
        elif (s, a) in [(22, 47), (32, 5)]:
            return "Kozmik düzendeki bir dönemin (yevm), insanlığın sayısal takvimine göre bin yıla denk geldiği zaman göreliliği (22:47 ve 32:5)."
        elif (s, a) == (30, 55):
            return "Büyük hesap saati kurulduğunda, hakikatten sapanların yeryüzünde yalnızca tek bir saat kaldıklarını kesin bir dille öne sürmesi (30:55)."
        elif (s, a) in [(41, 9), (41, 10), (41, 12)]:
            return "Yerin ve çok katmanlı gök sisteminin ikişer ve dörder kozmik evrede ölçülüp düzenlendiği yaratılış aşamaları (41:9-12)."
        elif (s, a) == (45, 14):
            return "Allah'ın geçmişteki müdahale ve hesap günlerini ummayanların taşkınlıklarına karşı, dirençli kalarak bağışlayıcı tutum sergileme uyarısı (45:14)."
        elif (s, a) == (55, 29):
            return "Evrendeki her varlığın O'na muhtaç olduğu ve yaratıcının 'her an ve her gün' yeni bir kozmik icraat ve oluş içinde bulunduğu gerçeği (55:29)."
        elif (s, a) == (69, 7):
            return "Büyük yıkım fırtınasının Âd toplumunun üzerine aralıksız 'yedi gece ve sekiz gün' boyunca kesintisiz sürdürülmesi (69:7)."
        elif (s, a) == (70, 4):
            return "Görevli elçi varlıkların ve ilahi mesaj taşıyıcı gücün, insan ölçüsüyle elli bin yıl uzunluğundaki bir dönem (yevm) içinde merkeze yükselmesi (70:4)."
        if pos == 'T':
            return "Bir eylemin, dönüşümün veya büyük hesabın gerçekleştiği belirli zaman kesiti ya da 'bugün' vurgusu."
        if 'MP' in f or 'FP' in f:
            return "Tarihsel süreçleri, ardışık aydınlık dönemleri veya belirli gün sayılarını ifade eden çoğul zaman birimi."
        if 'MD' in f:
            return "İki ayrı zaman dilimini, iki günlük süreyi veya iki kozmik oluş aşamasını ifade eden ikil zaman ölçüsü."
        return "Doğadaki aydınlık döngüyü, insan veya toplum tarihindeki kritik dönemi ya da büyük hesaplaşma evresini ifade eden temel zaman birimi."

    elif root_ar == 'أ-ي-ي':
        if (s, a) == (2, 106):
            return "Önceki bir bildiri birimini veya dönemsel işareti yürürlükten kaldırıp ya da unutturup yerine daha hayırlısını veya benzerini getirme ilkesi (2:106)."
        elif (s, a) == (2, 164):
            return "Göklerin, yerin, gece-gündüz döngüsünün, gemilerin, yağmurun ve rüzgârların akıl yürüten insanlar için somut doğa kanıtları olması (2:164)."
        elif (s, a) == (2, 248):
            return "Yöneticilik yetkisini doğrulayan, içinde güven duygusu ve geçmişten kalan tarihî hatıralar barındıran somut sandık göstergesi (2:248)."
        elif (s, a) == (3, 7):
            return "Kayıtlı metindeki göstergelerin (âyetlerin) bir kısmının temel taşıyıcı niteliğinde açık ve kesin hükümler (muhkem), diğer kısmının ise benzeşimli ve çok katmanlı ifadeler (müteşâbih) olarak ikiye ayrılması (3:7)."
        elif (s, a) == (3, 13):
            return "Karşı karşıya gelen iki topluluğun sahada yaşadığı tarihî kırılmanın, sağduyu ve basiret sahipleri için ibretlik bir gösterge oluşturması (3:13)."
        elif (s, a) in [(3, 41), (19, 10)]:
            return "Zekeriyya için üç gün boyunca yalnızca el ve yüz işaretiyle (remz) iletişim kurmasını sağlayan özel davranışsal belirteç (3:41 ve 19:10)."
        elif (s, a) == (7, 73):
            return "Semûd toplumuna gönderilen dişi devenin, toplumun kaynak paylaşımını ve etik tutumunu test eden canlı, somut bir kanıt olarak sunulması (7:73)."
        elif (s, a) in [(10, 15), (10, 21)]:
            return "Rasm-ı Osmânî yazımında bütün çoğul örneklerden ayrılarak açık uzun elifle (ءَايَاتُنَا / ءَايَاتِنَا) yazılan; okunan açık delillere itiraz ve hileli tutumları vurgulayan iki istisna ayet (10:15 ve 10:21)."
        elif (s, a) in [(11, 96), (23, 45), (28, 35), (40, 23)]:
            return "Somut doğrulayıcı göstergelerin (âyât) ikna edici açık güç ve otoriteyle (sultân-ı mübîn) birleşerek Firavun düzenine karşı durması (11:96 ve 23:45)."
        elif (s, a) == (12, 105):
            return "Göklerde ve yeryüzünde sayısız açık gösterge bulunduğu hâlde insanların bunların üzerinden fark etmeden ve yüz çevirerek geçip gitmesi (12:105)."
        elif (s, a) == (17, 1):
            return "Gece yolculuğuyla elçiye büyük evrensel gerçeklerden ve mekânlardan doğrudan bir kesit gösterilmesi (17:1)."
        elif (s, a) == (17, 12):
            return "Bütün verideki tek ikil kullanım (âyeteyn): Gece ve gündüzün iki farklı zaman göstergesi olarak düzenlenip yılların ve hesabın bilinmesi için gündüzün aydınlatıcı kılınması (17:12)."
        elif (s, a) in [(21, 91), (23, 50)]:
            return "Meryem ve oğlunun, insanlığın bütün kesimleri için düşündürücü ve olağanüstü bir toplumsal ve yaratılış göstergesi kılınması (21:91 ve 23:50)."
        elif (s, a) == (29, 49):
            return "Açık kanıtların yalnızca kağıt üzerinde değil, gerçek bilgiye erişen insanların zihin ve bilinç dünyalarında duru göstergeler olarak yerleşmesi (29:49)."
        elif (s, a) in [(30, 20), (30, 21), (30, 22), (30, 23), (30, 24), (30, 25)]:
            return "İnsanın topraktan var edilmesi, eşler arası sevgi-şefkat bağı, dillerin ve renklerin çeşitliliği, uyku döngüsü, şimşek ve gök-yer düzeninin birer evrensel gösterge dizisi olarak sunulması (30:20-25)."
        elif (s, a) in [(36, 33), (36, 37), (36, 41)]:
            return "Kuru toprağın canlanıp ürün vermesi, geceden gündüzün sıyrılması ve insanların gemilerle taşınmasının birbirini izleyen somut doğa ve medeniyet kanıtları sayılması (36:33-41)."
        elif (s, a) == (41, 37):
            return "Gece, gündüz, güneş ve ayın kendilerine tapınılacak kutsal varlıklar değil, yalnızca yaratıcı düzenin işleyişini gösteren doğal işaretler olduğunun vurgulanması (41:37)."
        elif (s, a) == (41, 53):
            return "Hem dış evrenin uçsuz bucaksız ufuklarında hem de insanın kendi iç dünyasında hakikatin adım adım kanıtlarla açığa çıkarılacağı yasası (41:53)."
        elif (s, a) in [(45, 3), (45, 6)]:
            return "Göklerdeki ve yerdeki fiziksel düzenin yanı sıra aktarılan hakikat sözlerinin de doğrudan doğrulanabilir delil niteliği taşıması (45:3-6)."
        elif (s, a) == (51, 20):
            return "Gerçeği arayan ve kesin bilgi peşindeki zihinler için yeryüzünün kendisinde açıkça okunabilir işaretlerin bulunması (51:20)."
        elif (s, a) == (79, 20):
            return "Firavun'a kendi iktidar algısını sarsan en büyük somut göstergenin (el-âyetü'l-kübrâ) doğrudan sergilenmesi (79:20)."
        if 'FD' in f:
            return "Çift yönlü ve birbirini tamamlayan iki somut evrensel gösterge (ikil kullanım)."
        if 'FP' in f:
            return "Doğadaki fiziksel yasalar, tarihsel izler veya metindeki anlamlı ifade birimleri biçiminde kendini gösteren çoklu kanıtlar ve göstergeler."
        return "Görünen bir olay, doğa olgusu, davranışsal belirteç veya sözlü birim üzerinden arkasındaki temel gerçeğe işaret eden somut kanıt ve gösterge."

    elif root_ar == 'س-م-و':
        if (s, a) in [(1, 1), (11, 41), (27, 30)]:
            return "Rasm-ı Osmânî yazımında vasıl elifi düşürülerek (بِسْمِ) yazılan; yolculuğa, yazıya veya önemli bir eyleme mutlak koruyucu ve şefkatli otoritenin adıyla başlama ilkesi (1:1, 11:41 ve 27:30)."
        elif (s, a) in [(56, 74), (56, 96), (69, 52), (96, 1)]:
            return "Rasm-ı Osmânî yazımında elifin açıkça korunduğu (بِٱسْمِ); okumaya, öğrenmeye ve doğayı yüceltmeye yaratıcı otoritenin kimlik adıyla başlama çağrısı (96:1 ve 56:74)."
        elif (s, a) in [(2, 31), (2, 33)]:
            return "İnsana varlıkları kavramsallaştırıp adlandırma yetisinin (esmâ) verilmesi ve bu bilişsel kapasitenin yüksek görevli varlıklara karşı sergilenmesi (2:31-33)."
        elif (s, a) == (2, 22):
            return "Yaşanılan alt zeminin (arz) karşısında gök yapısının bir bina/tavan olarak yükselmesi ve oradan yaşamı besleyen suyun indirilmesi (2:22)."
        elif (s, a) in [(2, 282), (6, 2), (6, 60), (13, 2)]:
            return "Gerek ekonomik borç sözleşmelerinde gerekse gök cisimlerinin yörünge sürelerinde ve insan ömründe sınırı ve adı önceden kesinleştirilmiş vade (ecel-i müsemmâ) ilkesi."
        elif (s, a) == (3, 36):
            return "Annenin yeni doğan kız çocuğuna 'Meryem' adını koyarak onu yüksek koruma altına alma niyazı (3:36)."
        elif (s, a) in [(7, 71), (12, 40), (53, 23)]:
            return "Toplumların kendi hayal güçleriyle uydurup kutsallaştırdığı, arkasında hiçbir nesnel dayanak ve kanıt (sultân) bulunmayan yapay etiketler eleştirisi (7:71, 12:40 ve 53:23)."
        elif (s, a) in [(7, 180), (59, 24)]:
            return "Yaratıcının varlık üzerindeki tüm olumlu, arınmış ve en üstün tanıtıcı sıfatlarının (el-esmâü'l-hüsnâ) bilince sunulması (7:180 ve 59:24)."
        elif (s, a) == (19, 7):
            return "Zekeriyya'ya verilecek çocuğa daha önce kimseye verilmemiş özgün bir ad olan 'Yahya' isminin konması; adaşsızlık vurgusu (19:7)."
        elif (s, a) == (19, 65):
            return "Göklerin, yerin ve ikisi arasındakilerin yöneticisi olan mutlak güce karşı varlık düzleminde denk düşecek hiçbir adaş ve eş (semiyy) bulunmaması (19:65)."
        elif (s, a) == (22, 15):
            return "Kişinin öfkesi içinde evinin üst tavanına (semâ) bir ip uzatıp bağlama teşebbüsü; sözcüğün doğrudan 'üst tavan' anlamında fiziksel kullanımı (22:15)."
        elif (s, a) == (22, 78):
            return "Barışa ve doğru düzene teslim olan topluluğa tarihsel süreklilik içinde ortak kimlik ve ad verilmesi (22:78)."
        elif (s, a) == (41, 12):
            return "Yedi kozmik gök katmanının (سَمَٰوَاتٍ) tam elifle yazıldığı ve tek belirsiz tekil (سَمَآءٍ) formunun geçtiği eşsiz yazım örneği; her katmana kendi işleyiş yasasının yerleştirilmesi (41:12)."
        elif (s, a) == (49, 11):
            return "İnsanların birbirine kırıcı lakaplar takmasının yasaklanması ve olgunluk sonrası bozgunculuk (fısk) adıyla anılmanın kötülüğü (49:11)."
        elif (s, a) == (51, 47):
            return "Üst kozmik yapının büyük bir güçle inşa edilip durmadan genişletilmekte olduğu yasası (51:47)."
        elif (s, a) == (53, 27):
            return "Sonraki hesap bilincinden kopanların yüksek görevli varlıklara gerçek dışı dişil adlandırmalar (tesmiye) yakıştırması (53:27)."
        elif (s, a) in [(67, 3), (71, 15)]:
            return "Yedi gök katmanının hiçbir çatlak veya uyumsuzluk olmadan birbirini tamamlayan tabakalar hâlinde düzenlenmesi (67:3 ve 71:15)."
        elif (s, a) == (76, 18):
            return "Ödül ve esenlik ortamında 'Selsebil' diye adlandırılan berrak kaynak (76:18)."
        if lemma == "samaA^'":
            if 'FP' in f:
                return "Yerin ve tüm alt düzeylerin üzerindeki çok katmanlı gök sistemleri ile uçsuz bucaksız kozmik düzen."
            return "Alt zeminin üzerindeki yüksek tavan, atmosfer katmanı, yağmur kaynağı veya genel uzay kubbesi."
        elif lemma == '{som':
            return "Bir varlığı veya hakikati belirsizlikten çıkararak bilince tanıtan ayırt edici ad, kimlik ve niteleyici başlık."
        elif lemma == 'm~usam~FY':
            return "Adı ve sınırı önceden kesinleştirilmiş belirgin vade veya zaman sınırı (ecel-i müsemmâ)."
        elif 'sam~aY' in lemma or lemma == 'tasomiyap':
            return "Bir şeye kimlik ve ad vermek, nitelemek ya da gerçek dışı etiket yakıştırmak."
        return "Yükselme ve belirginleşme ekseninde aynı ad altında anılan denk veya adaş varlık."

    elif root_ar == 'ع-ذ-ب':
        if (s, a) in [(25, 53), (35, 12)]:
            return "Acı ve tuzlu suya (milh ücâc) zıt olarak susuzluğu kesip dindiren, içimi yumuşak ve ferahlatıcı tatlı su anlamında kökün birincil fiziksel kullanımı (25:53 ve 35:12)."
        elif (s, a) == (2, 49):
            return "Firavun yönetiminin topluma uyguladığı sistematik baskı, erkek çocukların katledilmesi ve ağır zorbalık ıstırabı (2:49)."
        elif (s, a) == (2, 175):
            return "Doğru yol göstericilik ve koruyucu bağışlanma imkânını verip karşılığında körlük ve acı yoksunluk sonucu satın alma tercihi (2:175)."
        elif (s, a) == (4, 147):
            return "İnsanlar değer bilip güven ve doğruluk üzere yürüdükleri sürece yaratıcının onları cezalandırmaktan hiçbir çıkarının bulunmadığı ilkesi (4:147)."
        elif (s, a) == (7, 156):
            return "Yaratıcının yaptırımının yalnızca dilediği sınırlar içinde kalırken şefkat ve merhametinin bütün varlık âlemini kuşattığı gerçeği (7:156)."
        elif (s, a) == (8, 33):
            return "Elçi toplumun içindeyken ve insanlar hatalarını onarıp bağışlanma dilerken toplu yıkıcı yaptırımın yürürlüğe konmaması güvencesi (8:33)."
        elif (s, a) == (9, 101):
            return "İkiyüzlü tutumu alışkanlık hâline getirenlerin henüz yaşamdayken iki kez sarsıcı sonuçla karşılaşması ve ardından daha büyük yaptırıma yönlendirilmesi (9:101)."
        elif (s, a) == (10, 98):
            return "Yûnus toplumunun yaklaşan felaketi görüp topluca doğru tutuma yönelmesi üzerine dünya yaşamındaki utanç verici yaptırımın üzerlerinden kaldırılması (10:98)."
        elif (s, a) == (17, 15):
            return "Açık mesaj taşıyan bir elçi gönderilip uyarma yapılmadan hiçbir toplumun ağır yaptırıma çarptırılmayacağı evrensel adalet yasası (17:15)."
        elif (s, a) in [(18, 86), (18, 87)]:
            return "Siyasi yönetimde halka ya yaptırım uygulama ya da yapıcı ve güzel bir düzen kurma seçeneği; yalnızca zulmeden kesime kademeli ceza uygulanması (18:86-87)."
        elif (s, a) == (24, 2):
            return "Toplumsal hukuk düzeninde belirlenen bedensel cezanın bir izleyici topluluk önünde şeffaflıkla uygulanması (24:2)."
        elif (s, a) == (25, 65):
            return "Sürekli kuşatan yıkım ve ateş ortamının yakasını bırakmayan ağır sonuçlarından korunma bilinci (25:65)."
        elif (s, a) == (27, 21):
            return "Süleyman'ın göreve mazeretsiz gelmeyen hüdhüd kuşunu ağır yaptırımla ya da görevden tamamen uzaklaştırmayla uyarma kararı (27:21)."
        elif (s, a) == (32, 21):
            return "İnsanların büyük nihaî hesap öncesinde, hatalı yönelişlerinden dönmeleri amacıyla dünya hayatında yakın ve uyarıcı sonuçları tatması yasası (32:21)."
        elif (s, a) == (38, 41):
            return "Eyyûb'ün yaşamındaki yıkıcı hastalık ve bedensel yıpranmayla (nusb) birlikte gelen keskin fiziksel acı ve ıstırap hâli (38:41)."
        if lemma == 'Ea*ob':
            return "Susuzluğu kesip ferahlık veren saf, tatlı ve içimi rahat su."
        elif lemma in ['Ea*~aba', 'muEa*~ib']:
            return "Sorumsuzluğun, zulmün veya uyarılara kulak tıkamanın doğal ve ahlaki karşılığı olarak huzurdan kesilip ağır yaptırıma uğratılma süreci."
        elif lemma == 'muEa*~abiyn':
            return "Eylemlerinin sonucu olarak konfordan ve güven ortamından mahrum kılınarak yaptırıma maruz kalanlar."
        return "Konforun, tatlılığın ve güven duygusunun çekilmesiyle ortaya çıkan fiziksel, toplumsal, hukuksal veya nihaî acı ve ağır yaptırım durumu."

    elif root_ar == 'ك-ل-ل':
        if (s, a) == (16, 76):
            return "Kendi başına konuşup iş üretemeyen, nereye yönlendirilse bir hayır getirmeyen ve koruyucusunun omzunda ağır bir yük (kell) olan bağımlı insan örneği (16:76)."
        elif (s, a) in [(4, 12), (4, 176)]:
            return "Arkasında dikey soy bağından ne anne-baba ne de çocuk bırakmaksızın yan çemberdeki kardeş veya yakınlarca mirasçısı olunan kişi durumu (kelâle, 4:12 ve 4:176)."
        elif (s, a) == (19, 95):
            return "Bütün insanların istisnasız tamamının (küllühüm) büyük buluşmaya başkalarının arkasına saklanamadan tek tek birey (ferd) olarak çıkması (19:95)."
        elif (s, a) in [(13, 8), (54, 49)]:
            return "Evrendeki istisnasız her varlık ve olayın rastgelelikten uzak, kesin bir matematiksel ölçü ve oranla (kader / mikdâr) var edilmesi yasası (13:8 ve 54:49)."
        elif (s, a) == (17, 29):
            return "Ekonomik tutumda elini sımsıkı bağlamakla tam anlamıyla sonuna kadar açmak (küllü'l-bast) arasında ölçülü denge kurma uyarısı (17:29)."
        elif (s, a) == (2, 85):
            return "Kayıtlı ilkelerin ve sorumlulukların bir bölümünü kabul edip işine gelmeyen diğer bölümünü yok sayan seçmeci tutuma yönelik eleştiri (2:85)."
        elif (s, a) == (2, 148):
            return "Her topluluk ve bireyin kendine özgü bir yöneliş açısı bulunduğu hâlde iyilik ve erdem yarışında buluşulması çağrısı (2:148)."
        elif (s, a) == (11, 6):
            return "Yeryüzündeki hiçbir canlı hariç kalmamak üzere hepsinin yaşam kaynağı, barınağı ve korunma sürecinin açık bir düzen içinde kayıtlı oluşu (11:6)."
        elif (s, a) == (17, 13):
            return "Her insanın kendi eylem kaydının ve sorumluluk bilançosunun doğrudan kendi boynuna bağlanması ilkesi (17:13)."
        elif (s, a) == (21, 35):
            return "İstisnasız her canlı benliğin ölüm eşiğini tadacağı ve yaşamın hem zorluk hem de rahatlıkla bir sınama alanı olduğu gerçeği (21:35)."
        elif (s, a) == (29, 40):
            return "Haddi aşan geçmiş toplulukların her birinin (küllen) bizzat kendi yıkıcı tercihlerinin doğal sonucu olan karşılıklarla yüzleşmesi (29:40)."
        elif (s, a) == (74, 38):
            return "Her bireyin bizzat kendi kazandığı ve işlediği eylemlerin karşılığına bağlı bir sorumlu olarak durması ilkesi (74:38)."
        elif (s, a) == (4, 91):
            return "Barış anlaşmasına yanaşmayıp her defasında yıkıcı kargaşa ve fitne ortamına geri döndürüldüklerinde başgösteren tekrarlı tutum (4:91)."
        if lemma == 'kul~amaA' or pos == 'T':
            return "Bir durum veya tepkinin her tekrarlandığı anda kesintisiz yeniden ortaya çıkan döngüsel zaman bağı ('ne zaman / her defasında')."
        elif lemma == 'kala`lap':
            return "Üst ve alt dikey soy dalı olmadan yanlardan çevreleyen aile ve miras ilişkisi."
        elif lemma == 'kal~':
            return "Üretken katkı sunamayıp taşıyıcısının omzuna binen ağır yük ve bağımlılık."
        return "Bir kümedeki öğeleri tek tek dışarıda bırakmadan bütünüyle kuşatan kapsayıcı çember veya bir eylemdeki tam bütünlük ölçüsü."

    elif root_ar == 'ع-م-ل':
        if (s, a) == (67, 2):
            return "Varoluş sınavında ölçütün sayı çokluğu değil, yapılan işin nitelik, özen ve iyilik kalitesi (ahsenü amelen) olduğunu bildiren temel ilke (67:2)."
        elif (s, a) == (3, 195):
            return "Kadın veya erkek ayrımı olmaksızın hiçbir üreticinin verdiği emeğin ve ortaya koyduğu işin asla zayi edilmeyeceğini ilan eden eşitlik ilkesi (3:195)."
        elif (s, a) == (34, 11):
            return "Zırh dokumacılığı ve demir mühendisliği gibi somut zanaat üretimini doğrudan toplumsal yararlı işle aynı kökte birleştiren teknik çağrı (34:11)."
        elif (s, a) == (34, 13):
            return "Mimari yapılar, sanat eserleri ve büyük kazanların inşasını (amel) nimetin değerini davranışla açığa vurma pratiğiyle birleştiren anlatım (34:13)."
        elif (s, a) in [(36, 35), (36, 71)]:
            return "Doğal meyve ve ürünlerin yanında insanın kendi elleriyle işleyip yetiştirdiği somut emek payına dikkat çeken ayetler (36:35 ve 36:71)."
        elif (s, a) == (9, 60):
            return "Toplumsal dayanışma fonlarının sahada toplanması ve hak sahiplerine ulaştırılmasında fiilen çalışan görevli personeli (âmilîn) tanımlayan hukuki kullanım (9:60)."
        elif (s, a) == (16, 97):
            return "Güven bağıyla bütünleşen onarıcı ve yapıcı işlerin kişiye temiz, nitelikli ve huzurlu bir yaşam kazandıracağını belirten karşılık ilkesi (16:97)."
        elif (s, a) == (9, 105):
            return "Boş iddialar yerine somut olarak iş üretmeye ve yapılan eylemin bütün toplum önünde şeffafça görünür kılınmasına yapılan çağrı (9:105)."
        elif (s, a) == (18, 103):
            return "Yanlış yön ve pusulayla çok çaba sarf ederek kendini başarılı sanan, ancak emeği yönünden en büyük kayba uğrayanların durumu (18:103)."
        elif (s, a) == (11, 46):
            return "Aile veya soy bağının değil, bizzat kişinin ürettiği eylemin yapıcı ve uyumlu (salih) olup olmadığının temel belirleyici oluşu (11:46)."
        elif (s, a) in [(14, 18), (25, 23)]:
            return "Temelsiz ve çürük bir yöneliş üzerine kurulan çalışmaların fırtınada savrulan kül veya toz zerrecikleri gibi dağılıp boşa çıkması (14:18 ve 25:23)."
        elif (s, a) in [(39, 65), (47, 33)]:
            return "Eksen kayması veya sorumsuzluk yüzünden o ana dek biriktirilen üretken emeklerin bütün değerini yitirmesi tehlikesine karşı uyarı (39:65 ve 47:33)."
        elif (s, a) in [(2, 85), (39, 70)]:
            return "Kişinin sorumlu tutulduğu bilinçli eylem (amel) ile arka plandaki tüm davranış akışı (fiil) arasındaki ince ayrımı gösteren ayet (2:85 ve 39:70)."
        elif (s, a) in [(4, 17), (35, 8)]:
            return "Yanlış bir işin bilgisizlikten mi yoksa algı çarpılmasıyla güzel zannedilerek mi işlendiğini ayırt eden psikolojik analiz (4:17 ve 35:8)."
        elif (s, a) == (21, 94):
            return "Onarıcı işler yapan kişinin gösterdiği yoğun çabanın ve harcadığı emeğin (sa'y) karşılığının kesinlikle örtülmeyeceği garantisi (21:94)."
        elif (s, a) == (30, 41):
            return "İnsanların kendi elleriyle kazanıp biriktirdikleri tercihlerin (kesb), yine kendi yaptıkları eylemlerin (amel) ekolojik ve toplumsal sonucuna dönüşmesi (30:41)."
        elif (s, a) == (88, 3):
            return "Ağır ve tüketici işler altında sürekli uğraşıp didindiği hâlde yapıcı bir huzura ulaşamayan yorgunluk ve bitkinlik hâli (88:3)."
        elif (s, a) in [(99, 7), (99, 8)]:
            return "İster iyilik ister kötülük yönünde olsun, atom zerresi ölçeğindeki her bilinçli işin şaşmaz biçimde görünür sonuç vereceği yasası (99:7-8)."
        if lemma == 'Ea`mil':
            return "Bilinç ve kasıtla işi fiilen yürüten, sahada sorumluluk alan çalışan veya üretici özne."
        elif lemma == 'EaAmilap':
            return "Ağır yük altında aralıksız uğraşıp yorgun ve bitkin düşen özne durumu."
        elif lemma == 'Eamal':
            return "İnsanın özgür iradesiyle ortaya koyduğu somut iş, zanaat ürünü, mesleki çıktı veya bilinçli davranış birimi."
        return "Refleks ya da rastlantı olmaksızın bilinç, amaç ve özgür iradeyle ortaya konulan, doğrudan somut sonuç ve sorumluluk doğuran eylem."

    elif root_ar == 'ج-ع-ل':
        if (s, a) == (6, 1):
            return "Fiziksel göklerin ve yerin var edilmesiyle (halk), onlardan doğan karanlık ve aydınlık döngüsünün işlevselleştirilmesi (ce'l) arasındaki ayrım (6:1)."
        elif (s, a) == (25, 54):
            return "İnsanın biyolojik maddeden yaratılmasının ardından, insanlar arasında soy ve evlilikle kurulan toplumsal ilişki ağına dönüştürülmesi (25:54)."
        elif (s, a) == (2, 22):
            return "Yeryüzünün yaşam döşeği hâline getirilmesiyle, gerçekdışı eş ve ortaklar yakıştırma yasağını aynı kökle karşılaştıran ayet (2:22)."
        elif (s, a) == (2, 30):
            return "İnsanın yeryüzünde temsilci ve sorumlu yönetici konumuna atanmasını bildiren ilk varoluşsal görevlendirme (2:30)."
        elif (s, a) in [(2, 124), (21, 73), (28, 7)]:
            return "Bilge ve sınanmış kişilere toplum içinde öncülük, rehberlik ve mesaj taşıyıcılık görevinin tevdi edilmesi (2:124, 21:73 ve 28:7)."
        elif (s, a) == (2, 143):
            return "Topluluğun dengeli bir merkez eksen ve tanıklık konumuna yerleştirilmesi; yöneliş sınavının işlevsel belirlenişi (2:143)."
        elif (s, a) == (2, 224):
            return "Verilen söz ve bağlayıcı antların, insanların arasını düzeltmeye ve erdemli davranmaya engel hâline getirilmemesi uyarısı (2:224)."
        elif (s, a) in [(10, 5), (78, 9), (78, 10), (78, 11)]:
            return "Güneş ve ayın zaman ölçümüne, uykunun dinlenmeye, gecenin örtüye ve gündüzün üretim zamanına işlevsel kılınması (10:5 ve 78:9-11)."
        elif (s, a) in [(16, 72), (16, 81), (30, 21), (42, 11)]:
            return "Mevcut insan ve doğa dokusundan eşler, koruyucu gölgeler, barınaklar ile sevgi ve şefkat bağlarının türetilmesi (16:72, 16:81, 30:21 ve 42:11)."
        elif (s, a) in [(32, 9), (67, 23)]:
            return "Fiziksel şekilleniş ve büyümenin üzerine insana işitme, görme ve kavrayış donanımlarının işlevsel olarak yerleştirilmesi (32:9 ve 67:23)."
        elif (s, a) == (41, 10):
            return "Yeryüzüne dağ sabitlerinin yerleştirilmesi ve canlıların rızık kapasitesinin dört evrede dengeli biçimde hesaplanması (41:10)."
        elif (s, a) == (16, 124):
            return "Korpusun tamamında ce'l kökünden gelen tek edilgen (cûile) kullanım: Cumartesi günü kısıtının yalnızca o konuda çekişenler için bağlayıcı kılınması (16:124)."
        elif (s, a) == (18, 8):
            return "İnsanları yeryüzü süslerine bağlayan verimli yüzeyin, dönem sonunda kuru ve çorak bir düzlüğe dönüştürülebileceği uyarısı (18:8)."
        elif (s, a) == (43, 3):
            return "Evrensel mesajın akıl yürütülüp kavranabilmesi için açık, anlaşılır Arapça dil koduna ve okunur bir yapıya büründürülmesi (43:3)."
        elif (s, a) in [(6, 100), (6, 136), (13, 16), (43, 15), (43, 19)]:
            return "İnsanların gerçeklikte karşılığı olmadığı hâlde hayalî ortaklar, parçalar veya sıfatlar yakıştırıp bunları hakikat diye sunma yanılgısı (6:100, 6:136, 13:16, 43:15 ve 43:19)."
        elif (s, a) == (27, 34):
            return "İşgalci yönetimlerin girdikleri kentlerin düzenini bozup saygın yurttaşları aşağılık duruma düşüren statü dönüşümü tespiti (27:34)."
        elif (s, a) == (35, 1):
            return "Gökleri ve yeri ilk açılışla var eden (fâtır) iradenin, elçi görevi taşıyan kozmik güçleri (câil) ikişer, üçer ve dörder kanatlı işlevlerle donatması (35:1)."
        if lemma == 'jaAEil':
            return "Var olan bir yapıyı yeni bir işlev, makam, temsilcilik veya dönüşüm durumuna yerleştiren kurucu özne."
        return "Ham maddeyi yoktan yaratmaktan ziyade mevcut bir öğeyi alıp yeni bir işlev, ilişki, konum veya rol içine yerleştirme."

    elif root_ar == 'ر-ح-م':
        if (s, a) in [(1, 1), (1, 3), (27, 30)]:
            return "Tüm varlıkları ön şartsız besleyen kozmik kucaklayıcılık (Rahmân) ile çaba göstereni sürekli iyileştirip koruyan özel şefkat (Rahîm) ikilisi (1:1, 1:3 ve 27:30)."
        elif (s, a) in [(6, 12), (6, 54)]:
            return "Koruyucu şefkat ve onarıcı kucaklamanın dışsal bir zorunluluk değil, bizzat varoluş sisteminin kendi üzerine yazdığı temel anayasal ilke oluşu (6:12 ve 6:54)."
        elif (s, a) in [(7, 156), (40, 7)]:
            return "Yaptırımın belirli hedeflerle sınırlı olmasına karşılık, besleyici şefkat ve bilginin evrendeki istisnasız her şeyi içine alan sonsuz genişliği (7:156 ve 40:7)."
        elif (s, a) == (30, 50):
            return "Yağmur sonrasında kurak ve ölü toprağın yeniden yeşerip canlanmasını doğrudan doğadaki somut rahmet izleri olarak gösteren gözlem çağrısı (30:50)."
        elif (s, a) == (30, 21):
            return "Eşler arasında duygusal yakınlık ve sevginin (meveddet) yanına, zor günlerde ilişkiyi taşıyan koşulsuz koruma ağının (rahmet) kurulması (30:21)."
        elif (s, a) in [(3, 6), (2, 228), (13, 8), (22, 5), (31, 34)]:
            return "Canlının büyüyüp şekillendiği fiziksel ana rahmini (erhâm) ifade eden kök çekirdeği; bütün şefkat kavramının doğduğu biyolojik temel (3:6 ve 22:5)."
        elif (s, a) in [(4, 1), (8, 75), (33, 6), (47, 22), (60, 3)]:
            return "Aynı ana rahminden ve yaşam kaynağından çıkmanın doğurduğu akrabalık ve toplumsal dayanışma bağlarının korunması gereği (4:1 ve 47:22)."
        elif (s, a) == (17, 24):
            return "Küçüklükte koruyup büyüten yaşlı anne-babaya karşı tevazu ve şefkatle (rahmet) destek kanatlarının indirilmesi ilkesi (17:24)."
        elif (s, a) in [(9, 128), (21, 107)]:
            return "İnsan elçinin bizzat şefkatli ve koruyucu (raûf ve rahîm) niteliğiyle bütün toplumlara yönelik iyileştirici bir mesaj taşıması (9:128 ve 21:107)."
        elif (s, a) in [(48, 29), (90, 17)]:
            return "Bireylerin kendi aralarında yatay koruyucu şefkat (rühâmâ) ve karşılıklı merhamet dayanışması (merhame) ağı kurması (48:29 ve 90:17)."
        elif (s, a) in [(2, 143), (16, 7), (24, 20), (57, 27)]:
            return "Anlık şefkat hassasiyeti (re'fet) ile uzun vadeli yapıcı koruma (rahmet) dengesinin insan kalbinde ve toplum düzeninde birlikte işlemesi (24:20 ve 57:27)."
        elif (s, a) == (39, 53):
            return "Hatalarda aşırılığa düşen insanların dahi umutsuzluğa kapanmaması gerektiğini bildiren kapsayıcı dönüş ve onarım çağrısı (39:53)."
        elif (s, a) == (18, 81):
            return "Genç bireyin ailesine yakınlık, şefkat ve merhamet bağı bakımından (ruhm) daha dengeli ve hayırlı bir kuşakla değiştirilmesi anlatımı (18:81)."
        elif (s, a) in [(2, 218), (7, 56), (11, 73), (19, 2), (43, 32)]:
            return "Kuran imlasında (Rasm-ı Osmânî) zamir eki olmadan doğrudan açık Tâ-i Meftûha (ت) harfiyle yazılan özel rahmet tamlamaları (2:218, 7:56, 11:73, 19:2, 43:32)."
        elif (s, a) in [(7, 151), (12, 64), (12, 92), (21, 83), (23, 109), (23, 118)]:
            return "Zorluk ve pişmanlık anlarında yönelinen en kapsayıcı şefkat ve koruma mercii (erhamü'r-râhimîn / hayru'r-râhimîn) vurgusu."
        elif (s, a) == (17, 82):
            return "Vahiy metninin güven duyan zihinler ve toplumlar için iyileştirici bir şifa ve koruyucu destek kaynağı olması (17:82)."
        if lemma == '>aroHaAm':
            return "Canlının büyüdüğü fiziksel ana rahmi veya aynı kökten gelen insanların kurduğu akrabalık sorumluluk ağı."
        elif lemma == 'r~aHoma`n':
            return "Hiçbir ön şart aramadan tüm varlıkları kucaklayıp yaşatan evrensel yaşam ve şefkat kaynağı."
        elif lemma in ['r~aHiym', 'r~a`Himiyn', '>aroHam']:
            return "İlişkisel süreklilikle koruyan, besleyen, onaran ve hataların ardından destek sağlayan şefkatli merci veya birey."
        elif lemma == 'maroHamap':
            return "Toplum bireylerinin birbirini gözeterek karşılıklı şefkat ve dayanışma kültürünü ayakta tutması."
        elif lemma == 'ruHom':
            return "Anne-baba ile evlat arasındaki içten şefkat ve sıcak yakınlık bağı."
        elif pos == 'V':
            if 'PASS' in features:
                return "Olumlu tutum ve dayanışmanın doğal sonucu olarak koruyucu şefkate ve esenliğe kavuşma durumu (türhamûn)."
            return "Bir canlıyı veya topluluğu şefkatle koruma altına almak, eksiklerini onarmak ve esenliğe eriştirmek."
        return "Ana rahminin savunmasız canlıyı koşulsuz koruyup büyütmesi gibi besleyen, onaran ve yaşatan şefkat yasası."

    elif root_ar == 'ر-أ-ي':
        if lemma == "ri}aA^'":
            return "Başkalarının bakışını kazanmak için eylemi samimi niyetten çıkarıp gösterişe dönüştürme (III. bab mastarı)."
        elif lemma == "yuraA^'u":
            return "Sırf insanların gözüne şov yapmak ve beğeni toplamak üzere vitrin davranışı sergileme (III. bab)."
        elif lemma == "taraA^'ati":
            return "İki karşıt grubun aynı görüş sahasına girip birbirini yüz yüze görmesi durumu (VI. bab işteş fiil)."
        elif lemma == "r~u'oyaA":
            return "Uykuda veya derin içsel bilinçte beliren ve sonradan olgularla doğrulanan simgesel görü ve öngörü tablosu."
        elif lemma == "ra>oY":
            if (s, a) == (3, 13):
                return "Somut olayda gözün doğrudan gördüğü sayısal ve fiziksel gerçeklik tanıklığı (re'ye'l-ayn, 3:13)."
            return "Derinlemesine inceleme yapmadan ilk bakışta verilen yüzeysel düşünce ve sığ kanaat eleştirisi (bâdiye'r-re'y, 11:27)."
        elif lemma == "ri'oy":
            return "Geçmiş toplulukların fiziksel konforun yanında sergilediği göz alıcı dış görünüm ve gösteriş ihtişamı (19:74)."
        elif (s, a) in [(3, 152), (8, 43), (8, 44), (41, 53), (79, 20), (17, 1)]:
            return "Karşı tarafın gerçeği kavraması için dış dünyada, tarihsel süreçte veya insanın kendi içinde kanıtları görünür kılma (IV. bab ettirgen)."
        elif (s, a) in [(2, 260), (7, 143), (4, 153)]:
            return "Kişinin akıl ve algı sınırını aşan bir gerçeği doğrudan gözlemle somutlaştırma talebi veya ilahî gözlemin sınırı."
        elif (s, a) in [(7, 198), (10, 43)]:
            return "Gözü bir noktaya çevirip bakmak (nazar) ile olayın içyüzünü gerçekten kavramak (basîret) arasındaki uçurum."
        elif (s, a) in [(53, 11), (53, 13), (53, 18), (81, 23)]:
            return "Duyusal gözlem ile bilincin (fûâd) birebir doğruladığı üst düzey işaret algısı ve Necm suresindeki özel yâ imlası (53:11 ve 53:18)."
        elif (s, a) in [(6, 76), (6, 77), (6, 78)]:
            return "Yıldız, ay ve güneşi gözlemleyip geçiciliklerini keşfederek yanlış mutlaklaştırmalardan arınan rasyonel çıkarım (6:76-78)."
        elif (s, a) in [(21, 30), (25, 45), (24, 43), (2, 243)]:
            return "Doğadaki kozmik süreçleri veya tarihsel örnekleri «hiç görmüyor musunuz?» sorusuyla zihinsel idrak konusu yapma."
        elif (s, a) in [(35, 8), (70, 6), (70, 7), (40, 29)]:
            return "İki nesneli kullanımla dış gerçeği değil öznel değerlendirmeyi, yanılgıyı veya otoriter görüş tekelini ifade etme (35:8, 40:29, 70:6-7)."
        elif (s, a) in [(90, 7), (96, 7), (96, 9), (105, 1), (107, 1)]:
            return "Denetimden kaçtığını sanan bireyi yüzleştiren ve toplumsal sorumluluğu hatırlatan kısa gözlem/muhasebe soruları."
        elif (s, a) in [(46, 25), (53, 40), (99, 6)]:
            return "Yıkım sonrası arta kalan izlerin veya insan emeğinin er geç herkesçe görünür kılınması (edilgen yura / yürav)."
        elif (s, a) in [(4, 105), (9, 105)]:
            return "Doğrudan evrensel adalet ilkesinin ışık tuttuğu çerçevede hüküm vermek (4:105) ve tüm çabanın kayıtlı olarak izlenmesi (9:105)."
        elif (s, a) in [(5, 31), (7, 27)]:
            return "Doğal bir örnekleme veya kışkırtma üzerinden bir sonucu muhataba bilfiil göstermek / sergilemek (IV. bab, 5:31 ve 7:27)."
        elif lemma == '>arayo':
            return "Kendi dışındaki bir bilince delili, yolu, ölçüyü veya yapılacak eylemin sonucunu görünür hale getirmek (IV. bab)."
        elif 'MOOD:JUS' in features:
            return "Muhatabı doğa yasalarını ve geçmiş deneyimleri görüp akıl süzgecinden geçirmeye davet eden soru veya olumsuz gözlem kipi."
        elif 'PERF' in features:
            return "Geçmişte gözle doğrudan tanık olunmuş veya olay örgüsü içinde kesinleşmiş gözlem ve kanaat tespiti."
        return "Gözün nesneyi algılamasından zihnin anlam, kanaat veya değerlendirme üretmesine uzanan bütünsel görme ve idrak eylemi."

    elif root_ar == 'ك-ت-ب':
        if (s, a) in [(6, 12), (6, 54)]:
            return "Besleyici koruma ve şefkat yasasının dıştan bir zorlama değil, bizzat varoluş sisteminin kendi üzerine yazdığı değişmez anayasa oluşu (6:12 ve 6:54)."
        elif (s, a) in [(2, 178), (2, 180), (2, 183), (2, 216), (2, 246), (4, 77)]:
            return "Toplumsal yaşamda adalet, vasiyet, irade eğitimi ve meşru savunma sorumluluklarının «üzerinize yazıldı» (kütibe aleyküm) ifadesiyle bağlayıcı yasalaşması."
        elif (s, a) in [(2, 282), (2, 283), (24, 33)]:
            return "Ekonomik borçlanmaların tarafsız yazıcıyla kayda bağlanması (2:282-283) ve bağımlı kimselerle yazılı özgürlük sözleşmesi (mükâtebe, 24:33) yapılması emri."
        elif (s, a) in [(13, 38), (15, 4), (18, 27), (27, 1)]:
            return "Kuran imlasında (Rasm-ı Osmânî) elifi düşürülmeden tam «كتاب» harfleriyle yazılan yegâne 4 tekil geçiş; belirlenmiş süre yasası ve değişmez mesaj (13:38, 15:4, 18:27, 27:1)."
        elif (s, a) in [(13, 39), (3, 7), (43, 4)]:
            return "Değişken kayıtlar silinip güncellenirken arka planda değişmez duran temel ana yasa ve ilke çekirdeği (ümmü'l-kitâb, 3:7, 13:39, 43:4)."
        elif (s, a) == (2, 79):
            return "Kendi elleriyle yazdıkları metni mutlak otoritenin sözü gibi sunarak çıkar sağlayanların kınanması (2:79)."
        elif (s, a) in [(17, 71), (18, 49), (69, 19), (69, 25), (83, 9), (83, 20)]:
            return "Küçük veya büyük hiçbir davranışı dışarıda bırakmayan şeffaf bireysel ve toplumsal eylem bilançosu / silinmez sicil defteri (18:49, 69:19, 83:9)."
        elif (s, a) in [(6, 59), (56, 78), (52, 2)]:
            return "Doğadaki her yaprağa ve tohum tanesine kadar işleyen bütüncül evren kaydı (6:59), satırlı belge (52:2) ve özenle korunan kaynak (56:78)."
        elif (s, a) in [(3, 145), (4, 103), (4, 24)]:
            return "Ölüm süresinin (kitâben müeccelen, 3:145), düzenli yönelişin (kitâben mevkūten, 4:103) ve aile hukukunun (kitâballâhi, 4:24) yazılı bağlayıcı ölçüsü."
        elif (s, a) in [(27, 28), (27, 29)]:
            return "Süleyman yönetiminin Saba hükümdarına gönderdiği mühürlü resmi mektup / diplomatik belge anlamında somut kitap kullanımı (27:28-29)."
        elif (s, a) in [(5, 32), (5, 45), (21, 105), (57, 27)]:
            return "Can güvenliği ve eşitlik ilkelerinin yazılı kurala bağlanması (5:32, 5:45), yeryüzü mirası kaydı (21:105) ve sonradan uydurulup dayatılmayan kural (57:27)."
        elif (s, a) in [(58, 21), (58, 22), (7, 156), (7, 157)]:
            return "Bilinç ve kalplere köklü güvenin nakşedilmesi (58:22), şefkatin hak edenler lehine kayda geçirilmesi (7:156) ve önceki belgelerde yazılı elçi (7:157)."
        elif (s, a) == (25, 5):
            return "İftiracıların vahiy metnini «eskilerin yazılarını kendine kopyalatmış» (iktetebehâ) iddiasıyla küçümseme girişimi (25:5)."
        elif (s, a) in [(21, 94), (82, 11), (19, 79), (36, 12), (43, 19), (43, 80)]:
            return "Söylenen sözlerin, atılan adımların ve ortaya konan tüm emeklerin kaybolmadan kayda geçirilmesi (21:94, 36:12, 82:11)."
        elif (s, a) in [(21, 104), (34, 44), (98, 3)]:
            return "Yazılı tomarların dürülüp bir kozmik dönemin kapanışı (21:104) veya birden çok yazılı belge bütününü anlatan çoğul kitaplar (34:44, 98:3)."
        elif (s, a) in [(2, 2), (2, 89), (5, 15), (7, 52)]:
            return "Dağınık hükümleri ve evrensel ilkeleri tek bir çelişkisiz sistemde birleştirip insanlığa sunan kılavuz kitap."
        if lemma == "kaAtib":
            return "Sözleşmeleri adaletle yazıya geçiren kâtip veya insan eylemlerini eksiksiz belgeleyen kayıt tutucu."
        elif lemma == "kaAtibu":
            return "Taraflar arasında hak ve özgürlük doğuran karşılıklı yazılı sözleşme düzenlemek (III. bab)."
        elif lemma == "{kotataba":
            return "Başkasına dikte ettirip kendi adına metin kopyası çıkarmak (VIII. bab)."
        elif lemma == "makotuwb":
            return "Mevcut yazılı kaynaklarda açıkça kayıtlı ve görünür bulunan."
        elif lemma == "kita`b":
            return "Dağınık verileri, sözleri ve ilkeleri uçmayacak biçimde kenetleyip sabitleyen yazılı belge, yasa, sicil veya rehber kitap."
        elif 'PASS' in features:
            return "Toplumsal sorumluluk olarak kesin biçimde yasalaştırılması veya bireyin lehine kalıcı kayıt açılması."
        return "Hükmü sabitlemek, hak ve sorumluluk doğuran kural koymak ya da söz ve eylemi kalıcı olarak kayda geçirmek."

    elif root_ar == 'ه-د-ي':
        if (s, a) == (10, 35):
            return "Tek ayette kökün üç katmanının çarpışması: dışarıdan yön gösteren I. bab (`يَهْدِىٓ`), başkasız kendi yönünü bulamayan idgamlı VIII. bab (`يَهِدِّىٓ`) ve dışarıdan yönlendirilmeye muhtaç edilgen (`يُهْدَىٰ`) yapı (10:35)."
        elif (s, a) in [(22, 4), (37, 23)]:
            return "Râgıb el-İsfahânî'nin dikkat çektiği kinayeli ters kullanım: olumsuz yönlendirici güçlerin insanı yakıcı yıkım sonucunun yoluna sevk edip götürmesi (22:4, 37:23)."
        elif (s, a) in [(27, 35), (27, 36)]:
            return "Kökteki «iyi niyet ve yakınlık göstermek için öne sunulan armağan» (`بعثة لطف`) fiziksel çekirdeğinin Sabâ yöneticisinin gönderdiği diplomatik hediyede (`هَدِيَّة`) somutlaşması (27:35-36)."
        elif lemma == "hadoy":
            return "Kökteki «gönül bağı ve dayanışma nişanesi olarak sunulan armağan» çekirdeğinin büyük toplanma merkezine yollanan ikramlık destek hayvanı (`ٱلْهَدْى`) olarak kurumsallaşması."
        elif (s, a) in [(27, 81), (30, 53)]:
            return "Kelimesi kelimesine paralel iki ayette körleşmişlere kılavuzluk sınırının vurgulanması ve Mushaf imlasında `بِهَٰدِى` (27:81) vs son yâ'sı düşmüş `بِهَٰدِ` (30:53) ikili yazımı."
        elif (s, a) in [(7, 178), (17, 97), (18, 17)]:
            return "Yönlendirme ve sapma karşıtlığının ortaçla sabitlenmesi ve Rasm-ı Osmânî'de `ٱلْمُهْتَدِى` (7:178) ile son yâ'sı düşmüş `ٱلْمُهْتَدِ` (17:97, 18:17) imla farkı."
        elif (s, a) in [(28, 56), (42, 52)]:
            return "İki geçişli kullanım sınırının çizilmesi: insan elçinin gönlü ikna edip doğrudan sonuca ulaştıramaması (`لَا تَهْدِى مَنْ`, 28:56), buna karşın `إِلَىٰ` edatıyla ana doğrultuyu açıkça işaret etmesi (`لَتَهْدِىٓ إِلَىٰ صِرَٰطٍ`, 42:52)."
        elif (s, a) in [(20, 50), (76, 3), (90, 10)]:
            return "Evrendeki her varlığa kendi yapısına uygun yaşam işleyişinin (`ثُمَّ هَدَىٰ`, 20:50) ve insana özgür tercihle birlikte iki zıt yolun (`ٱلنَّجْدَيْنِ`, 90:10; `ٱلسَّبِيلَ`, 76:3) gösterilmesi."
        elif (s, a) in [(1, 6), (38, 22)]:
            return "Yolun ortasında dahi savrulmadan ana doğrultuda tutulmayı ve davalar arasında adaletli çözüme yönlendirilmeyi isteyen çağrı (1:6, 38:22)."
        elif lemma in ["{hotadaY`", "m~uhotaduwn", "m~uhotad", "muhotadiY"]:
            return "VIII. bab dönüşlü yapı: sunulan kılavuzluğu kendi özgür iradesiyle benimseyip doğru doğrultuyu bizzat kendi lehine bulmak ve o yolda yürümek."
        elif lemma in ["haAd", "haAdiy", "ha`diY", ">ahodaY`"]:
            return "Önden yürüyüp yön işaret eden kılavuz fail veya doğrultu bakımından daha isabetli yolu gösteren kıyas ölçüsü."
        elif lemma == "hudFY":
            return "İnsana zorlama yapmadan önünü aydınlatan doğrultu haritası, yol göstericilik ve açık kılavuz ilke."
        elif 'PASS' in features:
            return "Dışsal rehberlik ve destek sayesinde kişinin doğru söz ve doğrultu düzlemine ulaştırılması."
        return "Öne geçip yol açmak, zarafet ve incelikle doğrultu işaret etmek (`دلالة بلطف`), hedefe ulaştırmak."

    elif root_ar == 'ظ-ل-م':
        if (s, a) in [(2, 20), (53, 52)] and lemma in [">aZolama", ">aZolam"]:
            return "Tam eşyazımlı iki biçimin ayrımı: 2:20'de yıldırım ışığı kesilince ortalığın kararmasını anlatan IV. bab fiil (`أَظْلَمَ عَلَيْهِمْ`), 53:52'de ise daha ağır karanlık ve haksızlıkta olanları niteleyen üstünlük ismi (`أَظْلَمَ`)."
        elif (s, a) == (18, 33):
            return "İbn Fâris ve Râgıb'ın fiziksel «eksiltme» çekirdeğinin hiçbir mecaza sapmadan görünümü: verimli iki bahçenin ürününden tek bir parçayı bile eksik bırakmaması (`وَلَمْ تَظْلِم مِّنْهُ شَيْـًٔا`, 18:33)."
        elif (s, a) in [(21, 47), (36, 54)] and '3FS' in features:
            return "Denge terazileri ve adalet ölçüsünde hiçbir kişiye zerre kadar hak kaybı yaşatılmayacağının kesin edilgen ifadesi (`تُظْلَمُ`, korpus kodlamasında `3FS|JUS`)."
        elif (s, a) == (2, 279):
            return "Ekonomik ilişkide ve borç hukukunda çift yönlü koruma dengesi: ne karşıdakinin payını eksiltmek (`لَا تَظْلِمُونَ`) ne de kendi hakkını ezdirmek (`لَا تُظْلَمُونَ`)."
        elif (s, a) in [(3, 182), (8, 51), (22, 10), (41, 46), (50, 29)]:
            return "Mübalağalı `بِظَلَّامٍ lıl-ebîd` güvencesi (3:182'de tam elifle `بظلام`, diğer 4 yerde hançer elifle `بظلم`): sistemin tek bir bireye bile en ufak haksızlık yapmayacağı yasası."
        elif (s, a) in [(6, 82), (31, 13)]:
            return "Kuran içi kavram tanımı: 6:82'de iç güveni bozan «zulüm» kavramının 31:13'te «mutlak otoriteye başka bir ortağı denk tutup hakkı yerinden etmek» (`لَظُلْمٌ عَظِيمٌ`) şeklinde açıklanması."
        elif (s, a) in [(17, 33), (4, 148), (22, 39)]:
            return "Haksızlığa uğrayan mağdurun (`مَظْلُومًا` 17:33 / `ظُلِمَ` 4:148 / `ظُلِمُوا۟` 22:39) sesini duyurma, hukuki koruma talep etme ve meşru savunma hakkı."
        elif (s, a) in [(2, 57), (10, 44), (4, 97), (16, 28), (28, 16)]:
            return "İnsanın hakikate karşı direndiğinde aslında mutlak sisteme değil kendi benliğine ve bütünlüğüne zarar verip kendini karartması (`أَنفُسَهُمْ يَظْلِمُونَ`)."
        elif lemma in ["Zuluma`t", "muZolim"]:
            return "Daima çoğul gelen katmanlı karanlıkların (`ظُلُمَٰت`: fiziksel, biyolojik veya düşünsel karanlıklar; `39:6`, `24:40`, `36:37`) daima tekil aydınlık (`ٱلنُّور`) karşısındaki konumu."
        elif lemma == "Zaluwm":
            return "Sorumluluk ve nimetler emanet edilen insanın dengeyi kolayca bozabilen aşırı eğiliminin (`14:34`, `33:72`) uyarılması."
        elif lemma == ">aZolam":
            return "Hakikati gizleyip belgeyi çarpıtmaktan daha büyük bir yerinden etme hatası bulunmadığını gösteren kıyas (`فَمَنْ أَظْلَمُ`)."
        elif lemma in ["ZaAlim", "ZaAlimap", "ZaAlimiY^"]:
            return "Hakkı ait olduğu yerden söküp sınırı aşan, bu yüzden hem toplumsal düzeni (`ظَالِمَةٌ` kentler) hem kendi özünü karartan fail veya zümre."
        elif 'PASS' in features:
            return "Bireyin hakkı veya emeği konusunda dışarıdan hak kaybına, baskıya ya da yerinden edilmeye uğraması (`PASS`)."
        return "Işığı çekip karartmak ya da bir hakkı, ölçüyü veya sorumluluğu ait olduğu gerçek yerin dışına koyup eksiltmek."

    elif root_ar == 'ن-ف-س':
        if (s, a) == (81, 18):
            return "Kökteki temel fiziksel çekirdeğin (nefes alma, tıkanıklığı açıp esinti çıkarma) Kuran'daki tek V. bab fiille şafağın aydınlığa açılışına uygulanması (`وَٱلصُّبْحِ إِذَا تَنَفَّسَ`, 81:18)."
        elif (s, a) == (83, 26):
            return "Kökteki tek VI. bab fiil (`فَلْيَتَنَافَسِ`) ve tek VI. bab ortaç (`ٱلْمُتَنَٰفِسُونَ`) ile kimseyi ezmeden değerli ve kalıcı iyilikler uğruna nefes nefese yarışma çağrısı (83:26)."
        elif (s, a) in [(17, 25), (81, 7)]:
            return "Kuran'daki `153` adet `أَنفُس` çoğuluna karşılık, sonsuz iç niyet derinliğini (17:25) ve bütün canlı benliklerin kümelenmesini (81:7) anlatan yegâne 2 adet `نُفُوس` (`فُعُول`) çoğulu."
        elif (s, a) in [(12, 53), (75, 2), (89, 27), (79, 40), (91, 7)]:
            return "Tek bir insan benliğinin dürtüsel hamlıktan (`أَمَّارَة`), kendini sorgulayan vicdana (`لَوَّامَة`), kör arzuyu frenlemeye (79:40) ve iç huzura (`مُطْمَئِنَّة`) yükselen psikolojik olgunlaşma evreleri."
        elif (s, a) in [(5, 32), (4, 1), (3, 185), (39, 42)]:
            return "Ortak bir canlı özden türeyen insanlığın (4:1), tek bir dokunulmaz can değerinin (5:32), ölümlülüğün (3:185) ve uyku/ölüm anında bilincin geri çekilip salıverilmesinin (39:42) ortaya konması."
        elif (s, a) in [(2, 48), (2, 286), (17, 15)]:
            return "Kimsenin bir başkası yerine yük taşıyamayacağı (2:48) ve hiçbir bireye gücü aşan sorumluluk yüklenmeyeceği (2:286) evrensel adalet ilkesi."
        elif (s, a) in [(5, 116), (50, 16), (24, 61), (59, 9)]:
            return "Görünmeyen gizli iç dünya (5:116), içsel fısıltılar (50:16), aynı insanlık bağını paylaşan yakınlar (`سَلِّمُوا عَلَىٰٓ أَنفُسِكُمْ`, 24:61) ve özverili diğerkâmlık (59:9)."
        elif (s, a) == (2, 87):
            return "Dışarıdan gelip güç veren arındırıcı diriltici soluk ilkesi ile insan benliğinin bencil tepkileri (`بِمَا لَا تَهْوَىٰٓ أَنفُسُكُمُ`) arasındaki ayrımın aynı ayette sergilenmesi (2:87)."
        elif 'FP' in features:
            return "Bireylerin kendi öz varlıkları, iç dünyaları veya eylemlerin doğrudan dönüp dolaşıp kendi benliklerine dokunması («kendileri / kendiniz» dönüşlü öznesi)."
        return "Soluk alıp veren somut canlı birey, dokunulmaz insan canı veya kişinin düşünen, hisseden ve sorumluluk taşıyan içsel özü."

    elif root_ar == 'ن-ز-ل':
        water_ayahs = {
            (2,22), (2,164), (6,99), (7,57), (8,11), (10,24), (13,17), (14,32), (15,22),
            (16,10), (16,65), (18,45), (20,53), (22,5), (22,63), (23,18), (24,43), (25,48),
            (27,60), (29,63), (30,24), (30,49), (31,10), (31,34), (35,27), (39,21), (41,39),
            (42,28), (43,11), (45,5), (50,9), (56,69), (78,14)
        }
        calm_ayahs = {(3,154), (9,26), (9,40), (48,4), (48,18), (48,26)}
        punish_ayahs = {(2,59), (5,115), (7,162), (29,34), (33,26), (36,28), (37,177)}
        if lemma == "nuzul":
            return "Yolculuk sonrasında gidilen yurtta konuk için önceden hazırlanmış ilk ağırlama ve karşılama ikramı (olumlu esenlik ya da acı sonuç ironisi)."
        elif lemma == "manaAzil":
            return "Ay'ın gökyüzü yörüngesinde zaman ve takvim hesabını mümkün kılan düzenli konak noktaları ve evreleri (`10:5`, `36:39`)."
        elif (s, a) == (23, 29):
            return "Tek ayette hem emir (`أَنزِلْنِى`), hem mîm'li yer ismi (`مُنزَلًا`) hem çoğul etken ortaç (`ٱلْمُنزِلِينَ`) olarak gemiden bereketli toprağa güvenli konaklama duası."
        elif (s, a) == (12, 59):
            return "Misafiri eksiksiz ölçüyle ağırlayan cömert konukseverlik (`وَأَنَا۠ خَيْرُ ٱلْمُنزِلِينَ`, 12:59)."
        elif (s, a) in {(15, 21), (42, 27)}:
            return "Evrendeki hiçbir kaynağın ölçüsüz bırakılmadan kesin bir denge hesabıyla (`بِقَدَرٍ مَّعْلُومٍ`) aşama aşama indirilmesi yasası."
        elif (s, a) == (57, 25):
            return "İnsanlığa adalet ölçüsü (`ٱلْكِتَٰبَ وَٱلْمِيزَانَ`) ile birlikte yüksek güç ve fayda barındıran demirin (`ٱلْحَدِيدَ`) donanım olarak indirilmesi."
        elif (s, a) in {(7, 26), (39, 6), (2, 57), (7, 160), (20, 80), (5, 112), (5, 114), (28, 24), (40, 13)}:
            return "Giysi, çiftlik hayvanları, gökten ikram edilen besin ve temiz rızkın insanoğluna üst kaynaktan yararlı donanım olarak ulaştırılması."
        elif (s, a) in {(34, 2), (57, 4), (65, 12)}:
            return "Gök katmanlarından aşağı inen ile yukarı yükselen (`يَنزِلُ ... وَمَا يَعْرُجُ`) arasındaki kesintisiz dikey kozmik akış ve düzen."
        elif (s, a) in {(3, 3), (4, 136), (6, 114), (16, 44), (17, 105), (47, 20)}:
            return "Aynı ayette II. bab (`نَزَّلَ`: parça parça, olaylara göre sindirerek indirmek) ile IV. bab (`أَنزَلَ`: topluca/genel indirmek) veya I. bab (`نَزَلَ`: yeryüzüne değip yerleşmek) arasındaki ince anlam ayrımı."
        elif (s, a) in {(17, 106), (25, 32), (76, 23)}:
            return "Neden tek seferde verilmediğine yanıt olarak kalbi sağlamlaştırmak ve okunuşu sindirtmek için bilinçli biçimde bölüm bölüm indirme (`نَزَّلْنَٰهُ تَنزِيلًا`)."
        elif (s, a) in {(26, 210), (26, 221), (26, 222)}:
            return "Yıkıcı sapkın odakların temiz mesaja ulaşamayacağı, ancak her yalancı ve kusurlu iftiracının üzerine üşüşeceği (`تَنَزَّلُ`) ters kutup yasası."
        elif (s, a) in {(53, 13), (3, 124), (19, 64), (41, 30), (97, 4), (26, 193), (16, 102)}:
            return "Görünmeyen görevlilerin, diriltici soluğun veya destek güçlerinin belirli bir düzen ve buyrukla art arda inip yerleşmesi (`تَتَنَزَّلُ` / `نَزْلَةً`)."
        elif (s, a) in water_ayahs:
            return "Gökten yeryüzüne hayat veren yağmur, su veya dolunun (`24:43`, `31:34`, `56:69`) ölçülü inişi ve ölü toprağın canlandırılması."
        elif (s, a) in calm_ayahs:
            return "Sarsıntılı ve bunaltıcı anlarda insan kalplerine içsel güven, emniyet ve sükunetin (`سَكِينَة` / `أَمَنَة`) indirilmesi."
        elif (s, a) in punish_ayahs:
            return "Uyarıları hiçe sayanların yurtlarına inen sarsıcı yıkım (`37:177`) veya direnenlerin sığınak kalelerinden aşağı indirilmesi (`33:26`)."
        return "Yüksek ve yetkin kaynaktan insan bilincine, rehberlik için yazılı ölçüler, kanıtlar (`سُلْطَٰن`) ve uyarıcı işaretler halinde ulaştırılan bildirim."

    elif root_ar == 'ق-ب-ل':
        if (s, a) in {(2, 142), (2, 143), (2, 144), (2, 145), (10, 87)}:
            return "Yön birliğinin kör şekilcilik değil sınayıcı odak ve güvenli yaşam merkezi (`قِبْلَة`) kılınması; yüz çevirme ile bilinçli yöneliş arasındaki karar anı."
        elif (s, a) == (2, 177):
            return "Yüzünü yalnızca doğu veya batı tarafına (`قِبَلَ`) çevirmenin ötesinde gerçek olgunluğun güven, paylaşım, sözüne sadakat ve direnç olduğu ilkesi."
        elif (s, a) in {(3, 35), (3, 37), (5, 27), (46, 16), (2, 127), (14, 40)}:
            return "Sunulan çabanın, hizmetin ve yaklaşım armağanının dış gösterişe göre değil sorumluluk bilincine göre özenle benimsenmesi (`تَقَبَّلَ` V. bab ve `بِقَبُولٍ`)."
        elif (s, a) in {(9, 104), (40, 3), (42, 25), (3, 90)}:
            return "Hatadan samimi geri dönüşü kabul eden (`يَقْبَلُ` / `قَابِلِ`) yapı ile ölene dek pişmanlığı erteleyenlerde dönüşün artık geçersiz kalması (`3:90`)."
        elif (s, a) == (24, 4):
            return "İftira atıp dört tanık getiremeyenlerin toplumsal güvenilirliğini yitirmesi ve mahkemede tanıklıklarının bir daha kabul edilmemesi (`وَلَا تَقْبَلُوا۟`)."
        elif (s, a) in {(2, 48), (2, 123), (3, 85), (3, 91), (5, 36), (9, 53), (9, 54)}:
            return "Hakikatten kaçınan veya samimiyetsiz davranan kimseden ne bir bedelin, ne aracılığın ne de gönülsüz katkının geçerli sayılıp kabul görmemesi."
        elif (s, a) == (12, 26):
            return "Gömleğin ön yakadan (`مِن قُبُلٍ`) yırtılmasının yüz yüze müdahale kanıtı olarak gerçeği ortaya çıkarması (ön/arka `قُبُل / دُبُر` fiziksel ekseni)."
        elif (s, a) == (28, 31):
            return "Korkuyla sırt çevirip kaçtıktan (`مُدْبِرًا`) sonra güven çağrısıyla yüzünü öne dönüp ileri adım atma (`أَقْبِلْ`) komutu."
        elif (s, a) in {(12, 71), (12, 82), (37, 27), (37, 50), (37, 94), (51, 29), (52, 25), (68, 30)}:
            return "Kişilerin birbirine veya bir topluluğa doğru yüzünü dönüp (`أَقْبَلَ` IV. bab) yaklaşması, şaşkınlık yaşaması veya yüz yüze sorguya/özeleştiriye geçmesi."
        elif (s, a) in {(15, 47), (37, 44), (44, 53), (56, 16)}:
            return "Göğüslerdeki kin sökülüp atıldıktan sonra kardeşçe karşılıklı oturup birbirinin yüzüne huzurla bakışma (`سُرُرٍ مُّتَقَٰبِلِينَ`, VI. bab)."
        elif (s, a) == (49, 13):
            return "İnsanlığın büyük kitlelere (`شُعُوب`) ve yüz yüze iletişim kuran topluluk boylarına (`قَبَآئِلَ`) çatışmak için değil birbirini tanıyıp kaynaşmak üzere ayrılması."
        elif (s, a) == (46, 24):
            return "Vadilere doğru karşıdan ilerleyip yaklaşan bulut kütlesinin (`عَارِضًا مُّسْتَقْبِلَ`, X. bab) yağmur sanılmasına rağmen yıkıcı bir fırtına çıkması."
        elif (s, a) in {(27, 37), (57, 13), (70, 36), (6, 111), (18, 55), (7, 27), (17, 92)}:
            return "Karşı koyacak gücün yetmemesi (`27:37`), surun ön cephesinden gelen sonuç (`57:13`), göz önünde yüz yüze karşılama (`6:111`, `18:55`) ve aynı safta eşlik eden grup (`قَبِيل`)."
        elif (s, a) in {(30, 4), (57, 10)}:
            return "Olaylar dizisinin öncesinde de sonrasında da (`مِن قَبْلُ وَمِنۢ بَعْدُ`) yönetim ve denge ilkesinin tek elde toplanması ile tarihsel öncelik farkı."
        return "Zaman ve olay akışında bakış hattının daha önünde duran geçmiş dönemler, önceki nesiller ve tarihsel öncüller (`قَبْل` / `مِن قَبْلِ`)."

    elif root_ar == 'ذ-ك-ر':
        if lemma == "*akar":
            if (s, a) in {(3, 36), (3, 195), (4, 124), (16, 97), (40, 40), (49, 13), (53, 45), (75, 39), (92, 3)}:
                return "Biyolojik cinsiyet çiftinde (`ٱلذَّكَرُ وَٱلْأُنثَىٰ`) eşit değer ve varoluş yasası; erdem ve eylem karşılığında cinsiyet ayrımının bulunmadığı temel ilke."
            elif (s, a) in {(4, 11), (4, 176), (6, 139), (6, 143), (6, 144), (26, 165), (42, 49), (42, 50)}:
                return "Miras paylaşım dengesi (`4:11`, `4:176`), hayvanların cinsiyet üzerinden yapay yasaklara tabi tutulmasının eleştirisi (`6:139`, `6:143-144`) veya aile soy/cinsiyet dengesi."
            return "Eril cinsiyet tanımı ve biyolojik erkek birey (`ذَكَر`)."
        elif (s, a) == (2, 282):
            return "Yazılı borç sözleşmesinde iki tanığın birbirine hatırlatarak hukuki hafızayı sağlama alması ve unutma riskine karşı birbirini desteklemesi (`2:282`, tek II. bab muzâri geçişi)."
        elif lemma == "{d~akara" or (s, a) in {(12, 42), (12, 45), (18, 24), (18, 63)}:
            return "Unutma ve zihin dağılması (`نَسِيَ`) karşısında hatırlama bilinci: zindan yılları sonrası gelen ani uyanış (`12:42`, `12:45` `وَٱدَّكَرَ`), kayadaki balığın unutulması (`18:63`) ve unutunca hemen bilinci toplama ilkesi (`18:24`)."
        elif lemma == "m~ud~akir":
            return "Kamer sûresinde altı kez yankılanan soru nakaratı: Öğrenilmeye açık ve sade kılınan mesajdan uyanıp ders alacak bilinçli kimse yok mu (`فَهَلْ مِن مُّدَّكِرٍ`, VIII. bab idgamlı ortaç)?"
        elif (s, a) == (88, 21) or lemma == "mu*ak~ir":
            return "Mesajı ileten kişinin zorlayıcı bir baskıcı değil, yalnızca zihni uyandıran özgür bir hatırlatıcı (`فَذَكِّرْ إِنَّمَآ أَنتَ مُذَكِّرٌ`, `88:21`) olduğu temel ilkesi."
        elif (s, a) == (10, 71):
            return "Nuh elçisinin, aynı gerçeği bıkmadan tekrar hatırlatmasının (`وَتَذْكِيرِى`, II. bab masdar) muhataplara ağır gelmesine rağmen kararlılığını sürdürmesi."
        elif (s, a) in {(51, 55), (87, 9), (50, 45)}:
            return "Zorbalık kurmadan yalnızca sarsıcı metinle hatırlatmayı sürdürme emri; hatırlatma güvene erenlere yarar sağlar (`51:55`) ve karşılık verecek açık zihinlere yöneltilir (`87:9`)."
        elif (s, a) == (56, 73):
            return "Doğadaki ateşin yalnızca ısınma değil, yolculuktakiler için yaşamsal kaynağa işaret eden somut bir hatırlatma simgesi (`تَذْكِرَةً وَمَتَٰعًا لِّلْمُقْوِينَ`) kılınması."
        elif lemma == "ta*okirap":
            return "İnsana unuttuğu öz sorumluluğunu anında anımsatan somut uyarı belgesi ve ibret nişanı (`تَذْكِرَة`; özgür iradeyle seçmek isteyen için açık yol göstergesi)."
        elif (s, a) == (39, 45):
            return "Tek yaratıcı güç tek başına anıldığında (`ذُكِرَ ٱللَّهُ وَحْدَهُۥ`) kalpleri daralıp ürperenlerin, O'nun dışındaki sahte odaklar anılınca (`ذُكِرَ ٱلَّذِينَ مِن دُونِهِۦ`) hemen sevinmesiyle sınanan çarpık zihniyet."
        elif (s, a) in {(21, 10), (43, 44), (76, 1)}:
            return "Unutulmaktan kurtaran yüksek itibar, toplumsal onur ve anılmaya değer varlık (`فِيهِ ذِكْرُكُمْ` `21:10`, `لَذِكْرٌ لَّكَ وَلِقَوْمِكَ` `43:44`, `شَيْـًٔا مَّذْكُورًا` `76:1`)."
        elif (s, a) == (2, 152):
            return "Çift yönlü bilinç antlaşması: 'Beni bilinçle anıp unutmayın ki ben de sizi iyilikle anayım; sunulan değerin kıymetini bilin (`فَٱذْكُرُونِىٓ أَذْكُرْكُمْ وَٱشْكُرُوا۟ لِى`).'"
        elif (s, a) in {(7, 205), (13, 28), (18, 28), (24, 37), (25, 62), (33, 35), (62, 9), (62, 10), (3, 191), (8, 2)}:
            return "Gece-gündüz döngüsünde (`25:62`), ticaretin ortasında (`24:37`), içten ve alçak gönüllü biçimde (`7:205`), ayakta/otururken/yan yatarken (`3:191`) kalplere derin huzur (`13:28`) veren kesintisiz bilinç ve kadın-erkek eşitliği (`33:35`)."
        elif (s, a) in {(5, 13), (5, 14), (6, 44), (7, 165), (18, 57), (20, 124), (25, 73), (32, 15), (32, 22), (36, 19), (37, 13), (43, 36), (59, 19), (89, 23)}:
            return "Kendilerine ulaştırılan uyarıları unutarak yüz çevirme (`نَسُوا۟ حَظًّا مِّمَّا ذُكِّرُوا۟ بِهِۦ`) ile işitince sağır ve kör gibi davranmama arasında kurulan sorumluluk sınavı (`25:73`, `20:124`, `89:23`)."
        elif (s, a) in {(2, 114), (6, 118), (6, 119), (6, 121), (22, 35), (22, 36), (22, 40), (24, 36)}:
            return "İnsanların arınmak ve gerçeği anmak için bir araya geldiği mekanlarda (`2:114`, `22:40`, `24:36`) veya temiz besin tüketiminde (`6:118-121`, `22:36`) yüce kaynağın adının açıkça anılması ilkesi."
        elif lemma == "ta*ak~ara":
            return "Göz önündeki işaretler üzerinde durup düşünme, geçmişten ibret alma ve dağılmış bilinci yeniden toplama çağrısı (`يَتَذَكَّرُونَ` / `تَذَكَّرُونَ`, V. bab)."
        elif lemma == "*ikoraY`":
            return "Yüzeysel bir anımsamanın ötesinde, insanın içine işleyip davranışını değiştiren keskin ve kalıcı bilinç darbesi (`ذِكْرَىٰ`, mübalağalı dişil isim)."
        return "Unutulmaya karşı bilinci diri tutan zihinsel odaklanma, sözlü anış ve insanlığa yön veren uyarıcı bildirim (`ذِكْر` / `ذَكَرَ`)."

    elif root_ar == 'ح-ق-ق':
        if lemma == "HaA^q~ap":
            return "Gerçeği tüm çıplaklığıyla ortaya döküp herkesin payına düşeni şaşmaz biçimde kesinleştiren sarsıcı gerçeklik saati (`ٱلْحَآقَّةُ`, `69:1-3`)."
        elif lemma == "{sotaHaq~a":
            return "Vasiyet tanıklığında güveni boşa çıkaran haksızlık (`ٱسْتَحَقَّآ`) ortaya konunca, hakları çiğnenen mirasçıların (`ٱسْتَحَقَّ عَلَيْهِمُ`) öne geçip daha geçerli tanıklık sunması (`5:107`)."
        elif lemma == "Haqiyq":
            return "Elçi Musa'nın iç tutarlılık ilkesi: Yaratıcı hakkında yalnızca nesnel gerçeği söylemeye yaraşır ve bununla sorumlu olma (`حَقِيقٌ عَلَىٰٓ أَن لَّآ أَقُولَ ... إِلَّا ٱلْحَقَّ`, `7:105`)."
        elif lemma == "yuHiq~a":
            return "Soyut iddianın ötesinde somut tarihsel olaylarla gerçeği fiilen doğrulayıp ayağa kaldırma ve temelsiz çürüğü (`ٱلْبَٰطِل`) geçersiz kılma yasası (`IV. bab`, `8:7-8`, `10:82`, `42:24`)."
        elif (s, a) in {(84, 2), (84, 5)}:
            return "Göğün ve yerin kendi yaratıcı yasasını dinleyip uymakla yükümlü ve buna boyun eğmekle hakkını teslim etmiş kılınması (`وَأَذِنَتْ لِرَبِّهَا وَحُقَّتْ`, `84:2`, `84:5`)."
        elif lemma == "Haq~a":
            return "Bireylerin veya toplumların seçtiği yanlış tutum sonrasında uyarının veya doğal yargı sonucunun sorumlular üzerine kaçınılmaz biçimde kesinleşmesi (`حَقَّ / حَقَّتْ ٱلْقَوْلُ`, `36:70`, `17:16`)."
        elif (s, a) in {(6, 73), (10, 5), (14, 19), (15, 8), (15, 85), (16, 3), (29, 44), (30, 8), (39, 5), (44, 38), (44, 39), (45, 22), (46, 3), (64, 3)}:
            return "Evrenin rastgele bir eğlence veya amaçsız oyun için değil, milimetrik ölçü, tutarlılık ve işlevsel gerçeklik yasasıyla (`بِٱلْحَقِّ`) kurulup sürdürüldüğü ilkesi."
        elif (s, a) in {(2, 42), (3, 71), (7, 118), (13, 17), (17, 81), (18, 56), (21, 18), (22, 62), (31, 30), (34, 49), (40, 5), (40, 78), (47, 3)}:
            return "Köpük-maden karşılaştırmasıyla (`13:17`) gerçeğin (`ٱلْحَقّ`) kalıcı ve yararlı öz oluşu karşısında sahte ve çürüğün (`ٱلْبَٰطِل`) dağılıp hükümsüz kalması yasası (`17:81`, `21:18`, `2:42`)."
        elif (s, a) in {(10, 32), (10, 35), (10, 36), (53, 28)}:
            return "Bilgi felsefesi ilkesi: Gerçeğin (`ٱلْحَقّ`) dışında yalnızca yön kaybının kaldığı (`10:32`) ve kanıtsız sanı ile tahminin (`ٱلظَّنّ`) gerçek karşısında sıfır değer taşıdığı (`10:36`, `53:28`)."
        elif (s, a) in {(6, 141), (17, 26), (30, 38), (51, 19), (70, 24), (2, 282)}:
            return "Somut sosyo-ekonomik ve hukuki hak: hasat ürününden (`6:141`), kazançtan yoksul ve yoksun bırakılmışlara düşen belgeli pay (`51:19`, `70:24`) ve yazılı sözleşmede borçlunun borcu dikte etmesi (`2:282`)."
        elif (s, a) in {(38, 22), (38, 26), (23, 71), (4, 105), (5, 48), (2, 213)}:
            return "İnsanlar arasındaki anlaşmazlıklarda bencil hevese (`ٱلْهَوَىٰ`) kapılmadan nesnel hakikat ve adalet ölçüsüne göre hüküm kurma sorumluluğu (`38:26`, `2:213`, `23:71`)."
        elif lemma == ">aHaq~":
            return "Evlilik, toplumsal liderlik, güvenlik, saygı veya tanıklıkta hangi tarafın gerçeklik ve liyakat açısından daha üstün hak sahibi olduğunun (`أَحَقُّ`) belirlenmesi (`2:228`, `2:247`, `6:81`)."
        elif (s, a) in {(18, 29), (10, 53), (10, 108), (39, 41), (103, 3)}:
            return "Gerçeğin dayatma olmadan açıkça ortaya konması (`18:29`), kesinliğin soru-teyitle sabitlenmesi (`10:53`) ve insanların birbirine gerçeği tavsiye ederek dayanışması (`103:3`)."
        elif (s, a) in {(2, 61), (3, 21), (3, 112), (3, 181), (4, 155), (5, 77), (7, 33), (7, 146), (10, 23), (28, 39), (40, 75), (42, 42), (46, 20)}:
            return "Hiçbir haklı yasal veya ahlaki dayanak bulunmaksızın (`بِغَيْرِ ٱلْحَقِّ`) masum canlara kıymak, kibre kapılmak ve yeryüzünde ölçüsüz taşkınlık sergilemek."
        elif (s, a) in {(8, 4), (8, 74), (24, 25), (3, 62), (21, 97)}:
            return "İddianın eylemle örtüştüğü gerçek sadakat (`حَقًّا`), uydurma olmayan tarihsel anlatı (`3:62`) ve herkesin eksiksiz adalet karşılığını alacağı kesin düzen (`24:25`)."
        return "Dış gerçeklikle birebir örtüşen sarsılmaz hakikat, tutarlı sözleşme vaadi (`وَعْدُ ٱللَّهِ حَقٌّ`) ve sapmaz doğruluk ölçüsü (`ٱلْحَقّ` / `بِٱلْحَقِّ`)."

    elif root_ar == 'ك-ذ-ب':
        if (s, a) == (12, 18):
            return "Kardeşlerinin Yusuf'un kurt tarafından parçalandığını öne sürmek için gömleğe sahte kan (`بِدَمٍ كَذِبٍ`, `12:18`) sürmesi: dış görünüşü kandıran uydurma fiziksel kanıt."
        elif (s, a) in {(12, 26), (12, 27)}:
            return "Gömleğin ön veya arka taraftan yırtılmasını inceleyen adli mantık sınaması: gerçeği söyleyen (`ٱلصَّٰدِقِينَ`) ile iftira atıp yalan söyleyen (`كَذَبَتْ` / `ٱلْكَٰذِبِينَ`) somut kanıtla ayrılır."
        elif (s, a) == (53, 11):
            return "Algının göz yanılsamasına ve seraba düşmemesi: Kalbin ve bilincin gördüğü açık gerçekliği asla çarpıtmadığı (`مَا كَذَبَ ٱلْفُؤَادُ مَا رَأَىٰٓ`, `53:11`) duru kavrayış."
        elif (s, a) == (11, 65):
            return "Çölde kuruyup giden kaynakların aksine, verilen üç günlük uyarının asla boşa çıkmayacak kesin ve şaşmaz bir gerçeklik (`وَعْدٌ غَيْرُ مَكْذُوبٍ`, `11:65`) olması."
        elif (s, a) == (12, 110):
            return "Elçilerin en dar anda kendilerine boş söz verilip yanıltıldıklarını (`قَدْ كُذِبُوا۟`, `12:110` edilgen I. bab) sandıkları psikolojik eşikte gelen yardım."
        elif (s, a) == (96, 16):
            return "Gücü elinde tutup iyiliği engelleyen kibirli zihnin, sürekli yalan ve çarpıtma üreten ön karar merkezi (`نَاصِيَةٍ كَٰذِبَةٍ خَاطِئَةٍ`, `96:16`)."
        elif (s, a) in {(56, 2), (78, 28), (78, 35), (85, 19)}:
            return "Hesaplaşma gerçeğini boşa çıkaracak kimse bulunmaması (`56:2`), inatçı yalanlama yoğunluğu (`78:28`), esenlik ortamında karşılıklı yalan ve gerginlik olmaması (`78:35`) ve sürü reddedişi (`85:19`)."
        elif (s, a) == (10, 39):
            return "Temel bilgi etiği kuralı: Bilgiyle kuşatıp incelemedikleri bir şeyi doğrudan asılsız ilan edip yalanlamanın (`كَذَّبُوا۟ بِمَا لَمْ يُحِيطُوا۟ بِعِلْمِهِۦ`, `10:39`) mantıksal körlüğü."
        elif (s, a) in {(39, 32), (40, 28), (6, 21), (11, 18), (16, 116)}:
            return "Çift katlı çarpıtma: Olmayan bir yasa veya söz uydurup (`كَذَبَ` / `ٱفْتَرَىٰ`) aynı anda önündeki doğruyu reddetmek (`كَذَّبَ بِٱلصِّدْقِ`, `39:32`) ve `40:28`'deki akılcı risk analizi."
        elif s == 55 and lemma == "ka*~aba":
            return "Rahman sûresinde evrendeki ekolojik, kozmik ve insani dengeler sıralanarak `31` kez sorulan vicdan sorusu: Hangi açık nimeti yalan sayabilirsiniz (`تُكَذِّبَانِ`)?"
        elif (s, a) in {(5, 41), (5, 42), (9, 43), (9, 77), (9, 90), (29, 3), (58, 14), (2, 10)}:
            return "Toplumsal ilişkilerde samimiyetsizlik: Yalana ve çarpıtmaya kulak kesilme (`5:41-42`), bilerek sahte sözleşme ve bahane üretme (`9:77`, `58:14`) ile zorlukta tutarlı kalanların ayrışması (`29:3`)."
        elif lemma in {"ka*~aba", "m~uka*~ibiyn"}:
            return "Gelen açık belgeleri, uyarıları veya doğa kanıtlarını (`بِـَٔايَٰتِنَا`) araştırmadan «asılsız ve uydurma» ilan ederek sorumluluktan kaçma tavrı (`II. bab` tekzîb)."
        elif lemma == "ka*~aAb":
            return "Gerçeği çarpıtmayı ve muhatabını karalamayı alışkanlık haline getirmiş azılı yalancı nitelemesi (`كَذَّابٌ`, `38:4`, `40:28`, `54:25-26`)."
        return "Dış olgu ve iç vicdanla örtüşmeyerek beklentiyi boşa çıkaran sahte söz, uydurma beyan veya olguyu çarpıtma eylemi (`كَذِب` / `كَذَبَ`)."

    elif root_ar == 'ج-ي-أ':
        if (s, a) == (19, 23):
            return "Meryem'i doğum sancısının hurma gövdesine doğru zorlayıp mecbur bırakması (`فَأَجَآءَهَا`, `19:23`); ağırlıklı varış anlamının 'zorla sürüklemek' yönüne uzanışı."
        if (s, a) == (19, 27):
            return "Aynı olay örgüsünde `أَتَتْ` (kolayca taşıyıp getirme) ile karşıt olarak, çevrenin gözünde sarsıcı, ağır ve alışılmadık bir durumla çıkagelmesi (`لَقَدْ جِئْتِ`, `19:27`, metindeki tek 2. tekil dişil çekim)."
        if (s, a) in ((6, 5), (11, 76), (3, 183)):
            return "Aynı ayetteki akışkan `أَتَى` ile karşıtlık içinde ağırlıklı gelişi, kaçınılmaz hükmü veya sunu/ateş belirtisi gibi somut kanıtı masaya koyma talebini ifade eder (`جَاءَ` / `أَتَى` ayrımı)."
        if (s, a) in ((6, 160), (27, 89), (27, 90), (28, 84)):
            return "Somut eylem yüküyle huzura geliş (`جَآءَ بِـ`): Güzel ve yapıcı eylemle gelene on katından fazlası verilirken yıkıcı eylemle gelen yalnızca ürettiğinin dengiyle yüzleşir (`جَآءَ بِـ` etik karşılık yasası)."
        if (s, a) in ((39, 69), (89, 22), (89, 23)):
            return "Kozmik yargı sahnesinde elçilerin, tanıkların, görevli düzen güçlerinin ve yakıcı yıkım hesaplaşmasının tam ağırlığıyla sahneye getirilmesi (`وَجِا۟ىٓءَ`, tekil edilgen/etken zirve sahneleri)."
        if (s, a) in ((17, 81), (34, 49), (10, 76)):
            return "Sağlam gerçeklik ağırlığıyla ortaya çıktığında temelsiz kurgu ve sahte düzenin tutunamayıp dağılması (`جَآءَ ٱلْحَقُّ`, gerçekliğin yıkıcı etkisi)."
        if (s, a) in ((6, 94), (18, 48)):
            return "İlk varoluştaki gibi tüm yapay dayanaklar, servet ve çevre desteği geride bırakılarak yapayalnız huzura varış (`وَلَقَدْ جِئْتُمُونَا فُرَٰدَىٰ`)."
        if (s, a) in ((79, 34), (80, 33), (110, 1)):
            return "Henüz yaşanmamış büyük sarsıntı, sağır edici çığlık veya kesin açılımın gerçekleşmiş mâzî (`جَآءَتْ` / `جَآءَ`) kipinde kesinleşmiş olay gibi bildirilmesi."
        if (s, a) in ((11, 69), (11, 74), (12, 59)):
            return "Önemli haber ya da erzak yükü taşıyan konukların ve elçilerin somut bir gündemle gelip kapıya dayanması (`جَآءَتْ` / `جَآءَ`)."
        if (s, a) in ((28, 25), (12, 18), (12, 51)):
            return "Haber, kanıt veya sahte bir delil (`بِـ`) getirerek olayın seyrini geri dönülmez biçimde değiştiren somut ortaya çıkış (`جَآءَ`)."
        return "Zahmet, ağırlık veya somut kanıt/sonuç beraberliğiyle geri dönülmez biçimde varıp ortaya çıkmak (`جَآءَ`; kolay ve doğal akışı bildiren `أَتَى`'dan ayrılır)."

    elif root_ar == 'ع-ب-د':
        if (s, a) == (1, 5):
            return "Nesnenin fiil önüne alınmasıyla («yalnızca Sana hizmet eder ve yalnızca Senden destek bekleriz») kurulan çift yönlü sözleşme (`إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ`)."
        if (s, a) == (26, 22):
            return "Kökün tek II. bab kullanımı (`عَبَّدتَّ`): Bir halkı zorla boyunduruk altına alıp köleleştirerek angaryaya koşmanın eleştirilmesi."
        if (s, a) in ((2, 178), (16, 75), (23, 47)):
            return "Kökün somut toplumsal ve ekonomik yüzü: Özgür insanla bağımlı köle ayrımı (`2:178`, `16:75`) ve yöneticilerin bir toplumu kendi çalışanı/tebaası sayması (`لَنَا عَٰبِدُونَ`, `23:47`)."
        if (s, a) in ((3, 182), (8, 51), (22, 10), (41, 46), (50, 29)):
            return "Metindeki tüm `عَبِيد` (`5/5`) geçişlerinin yer aldığı evrensel hukuk güvencesi: Düzen sahibinin hiçbir sorumlu canlıya (`لِّلْعَبِيدِ`) haksızlık etmeyeceği ilkesi."
        if (s, a) in ((4, 172), (7, 206), (21, 19), (40, 60)):
            return "Gönüllü boyun eğiş ile kibir (`يَسْتَكْبِرُونَ / يَسْتَنكِفُ`) karşıtlığı: Gurura kapılmadan hizmet sunanlar ile büyüklenerek alçaltıcı sona sürüklenenlerin ayrışması."
        if (s, a) in ((109, 2), (109, 3), (109, 4), (109, 5)):
            return "109. Sûrede fiil (`أَعْبُدُ` şimdi, `عَبَدتُّمْ` geçmiş) ve kalıcı kimlik (`عَابِدٌ / عَٰبِدُونَ`) ayrımıyla, sahte odaklara bağlılık ile bilinçli bağlılık arasındaki kesin sınır çizgisi."
        if (s, a) in ((19, 93), (43, 19)):
            return "Evrendeki bütün varlıkların ve kozmik görevlilerin ortak varoluş yasasına tabi konumda bulunması (`عَبْدًا` / `عِبَادُ ٱلرَّحْمَٰنِ`)."
        if (s, a) in ((18, 110), (19, 65), (39, 17), (51, 56)):
            return "Azgın otoritelere (`طَاغُوت`) ve ikincil merkezlere köle olmayı reddedip, yararlı eylem (`عَمَلًا صَٰلِحًا`) ve sebatla tek yaratıcı kaynağa bağlanma özgürlüğü."
        if (s, a) in ((10, 29), (19, 82), (43, 20), (43, 45), (46, 6)):
            return "Sahte merkezlere ve geçersiz otoritelere yöneltilen kör bağlılığın, yüzleşme anında bizzat o odakların bile sahiplenmeyip reddettiği sahte bağ oluşu."
        if (s, a) in ((25, 63), (38, 45), (39, 53), (89, 29)):
            return "Yeryüzünde alçakgönüllü ve barışçıl yürüyen (`عِبَادُ ٱلرَّحْمَٰنِ`), hata edip aşırı gitseler bile dönüş kapısı açık tutulan bilinçli hizmet topluluğu."
        if lemma == "EibaAdat":
            return "Düzlenmiş yol gibi egonun engebelerini aşarak tek bir merkeze gösterilen gönüllü boyun eğiş ve bilinçli hizmet bağlılığı (`عِبَادَة`)."
        if lemma in {"EaAbid", "Ea`bida`t"}:
            return "Bir otorite veya yaşam düzenine bilinçle boyun eğip düzenli hizmet sunan bireyler/kadınlar (`عَابِد / عَٰبِدَٰت`)."
        if lemma == "Eabod":
            if '|MP|' in f:
                return "Evrensel düzene veya bir yönetim merkezine bağlı konumda bulunan insanlar ve görevli topluluk (`عِبَاد`)."
            return "Toplumsal statüdeki köle, emeğiyle çalışan görevli ya da mesaj taşıma sorumluluğu üstlenen bilinçli elçi (`عَبْد`)."
        return "Üzerinden geçilip düzlenmiş yol (`طريق معبد`) gibi sertliği kırarak bir merkez veya ilkenin doğrultusunda emek üretmek, hizmet ve bağlılık sunmak (`عَبَدَ / يَعْبُدُ`)."

    elif root_ar == 'أ-خ-ذ':
        if (s, a) == (16, 68):
            return "Arının doğadaki dağlardan, ağaçlardan ve çardaklardan kendine yuva kurması (`ٱتَّخِذِى`, tek `2FS` `VIII. bab`): kökün eldekini kalıcı barınak/yapı haline getirme anlamı."
        if (s, a) in ((25, 43), (45, 23)):
            return "Kendi bencil hevesini yaşamının yönlendirici otorite merkezi (`إِلَٰهَ`) edinme psikolojisi (`ٱتَّخَذَ إِلَٰهَهُۥ هَوَىٰهُ`)."
        if (s, a) in ((7, 150), (11, 56), (55, 41)):
            return "Somut fiziksel kavrayış ve bırakma karşıtlığı: levhaları atıp kardeşin başından yakalama (`7:150`), her canlının perçeminden kontrolle tutma (`11:56`) veya alın ve ayaklardan kıskıvrak yakalanma (`55:41`)."
        if lemma == "yu&aAxi*u" or (s, a) in ((2, 225), (2, 286), (5, 89), (16, 61), (18, 58), (18, 73), (35, 45)):
            return "Kasıtsız hatalar veya unutkanlık (`18:73`) yerine bilerek bozulan ahitler karşısında hesap sorma ve canlılara gelişim için süre/mühlet tanıma dengesi (`يُؤَاخِذُ`, `III. bab`)."
        if (s, a) in ((11, 102), (11, 67), (54, 42), (69, 10), (73, 16)):
            return "Adaletsizlik ve taşkınlıkta direnen toplumların katlanarak gelen yıkıcı darbeyle kıskıvrak yakalanması (`أَخْذ` / `أَخْذَةً رَّابِيَةً`)."
        if (s, a) in ((2, 229), (4, 20), (8, 70), (59, 7)):
            return "Aynı ayette vermek (`ءَاتَى`) ile almak (`أَخَذَ`) eylemlerinin hukuki dengesi: evlilikte verileni geri almamak (`2:229`), kamusal paylaşımı almak (`59:7`) veya alınan kaybın daha hayırlısıyla telafisi (`8:70`)."
        if (s, a) in ((2, 63), (2, 83), (3, 81)):
            return "Karşılıklı bağlayıcı sözleşme ve ahdi teslim alarak ilkeleri ciddiyetle yürürlüğe koymak (`أَخَذْنَا مِيثَٰقَ / خُذُوا۟ بِقُوَّةٍ`)."
        if (s, a) in ((2, 267), (4, 161), (12, 78)):
            return "Ekonomik ve hukuki pratiklerde alma ölçüsü: kalitesiz malı göz yummadan almamak (`2:267`), faiz yoluyla haksız kazanç (`4:161`) veya birini rehin/alıkoymak (`12:78`)."
        if (s, a) in ((2, 51), (2, 54), (2, 92), (35, 6), (73, 9)):
            return "Hayat yönelimi seçimi: sahte put/buzağıyı dayanak edinmenin özeleştirisi (`2:51`, `2:54`) veya yıkıcı eğilimi düşman (`35:6`) ve düzen sahibini vekil (`73:9`) edinme çağrısı."
        if lemma in {"{t~axa*a", "mut~axi*", "{t~ixaA*"}:
            return "Eldeki malzemeyi, ilişkiyi, mekânı veya düşünceyi seçerek kendisi için kalıcı dayanak, yuva ya da yönelim merkezi edinmek (`VIII. bab` `اِتَّخَذَ`)."
        if lemma in {">axo*", "A^xi*"}:
            return "Sıkıca tutma, teslim alma veya haksızlık karşısındaki sarsıcı yakalayış hamlesi (`أَخْذ / ءَاخِذ`)."
        return "Uzanıp sımsıkı kavramak, verilen şeyi teslim almak, bağlayıcı ahde bağlamak veya adaletsizlik anında kıskıvrak yakalamak (`I. bab` `أَخَذَ`)."

    elif root_ar == 'خ-ل-ق':
        if (s, a) == (59, 24):
            return "Üç aşamalı üretim zincirinin ilk halkası: planlayıp ölçülendiren (`ٱلْخَٰلِقُ`), tasarımı kusursuz işleyen biçimde ayırıp sahaya çıkaran (`ٱلْبَارِئُ`) ve her birime özgün dış form kazandıran (`ٱلْمُصَوِّرُ`)."
        if (s, a) in {(54, 49), (25, 2)}:
            return "Her varlığı ve olayı rastgele değil, tam ölçüsü, oranı ve hassas dengesiyle (`قَدَر`) hesaplayarak tasarlamak."
        if (s, a) in {(22, 5), (23, 14), (39, 6)}:
            return "Embriyonik gelişimde biçimlenmiş ile henüz biçimi tamamlanmamış (`مُخَلَّقَةٍ وَغَيْرِ مُخَلَّقَةٍ`) doku aşamalarından karanlık katmanlar boyunca adım adım evrensel oranlarla şekillendirme; `أَحْسَنُ ٱلْخَٰلِقِينَ` ifadesiyle tasarımda en yetkin mertebeyi vurgular."
        if (s, a) in {(29, 17), (38, 7), (3, 49), (5, 110)}:
            return "Kökün «yoktan var etmekten ziyade mevcut malzemeyi ölçüp şekillendirme» anlamını açığa çıkaran pasajlar: eldeki çamuru ölçüp kuş biçimine sokmak (`3:49, 5:110`) veya gerçekliği olmayan sözleri zihinde masa başında yapay kurgu olarak üretmek (`تَخْلُقُونَ إِفْكًا / ٱخْتِلَٰقٌ`)."
        if (s, a) in {(7, 54), (6, 1), (82, 7), (87, 2)}:
            return "Maddeyi ölçüp tasarlamak (`ٱلْخَلْقُ`) ile yönetim ve işleyiş komutasının (`ٱلْأَمْرُ`) aynı bütün içinde buluşması; önce yapılandırmak (`خَلَقَ`), ardından pürüzsüz uyuma (`سَوَّىٰ`) ve dengeli orana (`عَدَلَ / قَدَّرَ`) ulaştırmak."
        if (s, a) in {(2, 102), (2, 200), (3, 77), (9, 69)}:
            return "Kişiye kendi çabasının, tutumunun ve seçimlerinin karşılığı olarak ölçülüp ayrılan pay veya nasip (`خَلَاق` — İbranice pay/kısmet anlamına gelen `ḥēleq` ile ortak Sami kökü)."
        if (s, a) in {(26, 137), (68, 4)}:
            return "İnsanda veya toplumda oturmuş iç karakter, tutarlı ahlaki yapı ve süreklilik kazanmış davranış kalıbı (`خُلُق`)."
        if (s, a) in {(52, 35), (56, 59), (7, 191), (16, 20), (25, 3), (37, 96)}:
            return "Nedensellik sorgulaması: kendi kendini var edip edememe sorusu üzerinden, başkaları tarafından yontulup şekillendirilmiş cansız nesnelerin yeni bir tasarım üretemeyeceğine dikkat çekilir."
        if (s, a) in {(4, 119), (30, 30)}:
            return "Evrensel tasarımdaki özgün doğal yapıyı ve işleyiş dengesini (`خَلْقَ ٱللَّهِ`) yapay müdahalelerle bozup çarpıtmadan koruma ilkesi."
        if lemma == "{xotila`q":
            return "Gerçeklik temeli bulunmayan yapay kurgu ve yakıştırma uydurma (`VIII. bab masdar` `ٱخْتِلَاق`)."
        if lemma == "muxal~aqap":
            return "Biyolojik oluşum sürecinde tam ölçüsüne göre şekillenmiş doku aşaması (`II. bab edilgen ortaç` `مُخَلَّقَة`)."
        if lemma == "xuluq":
            return "Yerleşik huy, tutum veya köklü karakter yapısı (`خُلُق`)."
        if lemma == "xal~a`q":
            return "Her ayrıntıyı eksiksiz bilerek kesintisiz ölçüp yeniden biçimlendiren (`ٱلْخَلَّاق`)."
        if lemma == "xala`q":
            return "Bireye veya topluluğa ölçülüp ayrılmış pay, sonuç hakkı ve kazanım payı (`خَلَاق`)."
        if lemma == "xa`liq":
            return "Mevcut malzemeyi ve düzeni belirli ölçü ve orana göre planlayıp biçim veren tasarımcı (`خَالِق / خَالِقِينَ`)."
        if lemma == "xaloq":
            return "Ölçülü tasarım süreci, pürüzsüz şekillendirme veya belirli oranla yapılandırılmış varlık alemi (`خَلْق`)."
        if 'PASS' in features:
            return "İnsanın veya varlığın belirli bir ölçü, oran ve kırılganlık/dayanıklılık dengesi içinde biçimlendirilmiş olması (`خُلِقَ / يُخْلَقُ`)."
        return "Deri veya hammaddeyi kesmeden önce ölçmek gibi, her şeyi belirli bir plan, ölçü ve pürüzsüz uyumla tasarlayıp biçimlendirmek (`I. bab` `خَلَقَ`)."

    elif root_ar == 'و-ق-ي':
        if (s, a) == (16, 81):
            return "Kökün somut fiziksel temeli: sıcaktan koruyan giysiler (`سَرَٰبِيلَ تَقِيكُمُ ٱلْحَرَّ`) ve çarpışma darbesini savuşturan zırhlar (`تَقِيكُم بَأْسَكُمْ`) — araya gerçek bir kalkan yerleştirerek zararı önlemek."
        if (s, a) == (7, 26):
            return "Beden giysisinin yanına yerleştirilen davranışsal koruyucu kalkan (`لِبَاسُ ٱلتَّقْوَىٰ`) — insanı aşırılıkların açacağı utanç ve yıkımdan örten iç zırh."
        if (s, a) == (91, 8):
            return "İnsan benliğindeki iki zıt eğilim: sınırı yırtıp taşmaya yol açan savrulma (`فُجُور`) ile kendini koruyan denge ve sorumluluk bilinci (`تَقْوَىٰ`)."
        if (s, a) in {(2, 177), (2, 189), (22, 37)}:
            return "Boş şekilcilik yerine gerçek erdem tanımı: yönlere dönmek, garip töreler ya da kesilen hayvanların et ve kanı değil, paylaşım, dürüstlük, zorlukta direnç ve zarar vermekten sakınan bilinç (`ٱلْمُتَّقُونَ`) esastır."
        if (s, a) in {(5, 2), (5, 8)}:
            return "Toplumsal adalet ölçütü: öfke veya düşmanlık duyulan kesimlere karşı bile adaletten ayrılmamak (`ٱعْدِلُوا۟ هُوَ أَقْرَبُ لِلتَّقْوَىٰ`), hata ve saldırganlık yerine yapıcı iyilikte yardımlaşmak."
        if (s, a) in {(49, 13), (92, 17)}:
            return "Soy, kabile veya statü üstünlüğünün reddedilip insanın gerçek değerinin sorumluluk bilinci ve kendini kötülükten koruma düzeyiyle (`أَتْقَىٰكُمْ / ٱلْأَتْقَى`) ölçülmesi."
        if (s, a) in {(59, 9), (64, 16)}:
            return "Edilgen `I. bab` kullanımı (`يُوقَ شُحَّ نَفْسِهِۦ`): bireyin kendi içindeki açgözlülük ve bencil tutuculuk duvarına karşı korunabilmesi sayesinde başarıya ulaşması."
        if (s, a) in {(66, 6), (8, 25)}:
            return "Yalnızca bireyi değil, aileyi (`قُوٓا۟ أَنفُسَكُمْ وَأَهْلِيكُمْ`) ve bütün toplumu sarabilecek büyük yıkım ve kırılmalara (`فِتْنَة`) karşı ortak koruma kalkanı kurma sorumluluğu."
        if (s, a) in {(2, 197), (9, 108), (9, 109)}:
            return "Hayat yolculuğu için alınabilecek en kalıcı kumanya/azık (`خَيْرَ ٱلزَّادِ`) ve toplumsal yapıyı çökmeye hazır uçurum kenarına (`شَفَا جُرُفٍ هَارٍ`) değil sağlam güvenlik temeline oturtmak."
        if (s, a) in {(8, 29), (65, 2)}:
            return "Sorumluluk kalkanı kuşanan kimseye doğruyu yanlıştan ayıran bir iç ölçüt (`فُرْقَانًا`) ve daralan durumlarda beklenmedik bir çıkış yolu (`مَخْرَجًا`) açılması."
        if (s, a) == (3, 28):
            return "Açık baskı ve tehdit altında kişinin kendi can ve güvenliğini korumak üzere aldığı meşru sakınma tedbiri (`تُقَىٰةً`)."
        if (s, a) == (3, 102):
            return "Korunma ve sorumluluk bilincinin gevşetilmeden bütün hakkını vererek yaşanması (`حَقَّ تُقَاتِهِۦ`)."
        if lemma == "waAq":
            return "Yanlış tercihin doğurduğu sonuç karşısında darbeyi durduracak herhangi bir kalkan ve koruyucunun (`وَاقٍ`) bulunmayışı (`13:34`, `13:37`, `40:21`)."
        if lemma == "taqiy~":
            return "Başkasına zarar vermekten özenle sakınan, öz-denetimli ve güven veren karakter yapısı (`تَقِيًّا`)."
        if lemma == "mut~aqiyn":
            return "Tehlikeyi görüp kendi önüne koruyucu sınır çeken, adalet, paylaşım ve sözüne sadakatle sorumlu davranan kimseler (`ٱلْمُتَّقِينَ`)."
        if lemma == "taqowaY":
            return "Zırh veya yol azığı gibi insanı ve toplumu yıpratıcı aşırılıklardan koruyan bilinçli iç sınır (`ٱلتَّقْوَىٰ`)."
        if lemma == "waqaY`":
            return "Araya somut bir kalkan/zırh koyarak yaklaşan sıcaklığı, darbeyi veya yıkıcı sonucu doğrudan savuşturmak (`I. bab` `وَقَى`)."
        return "Taşlı yolda ayağını incitmekten sakınan at gibi, zarar verecek davranışlardan kaçınarak kendini ve çevreni sorumluluk kalkanıyla korumak (`VIII. bab` `ٱتَّقَى`)."

    elif root_ar == 'أ-خ-ر':
        if (s, a) in {(57, 3), (93, 4), (53, 25), (92, 13)}:
            return "Önce gelen ile sonra gelen dengesi: başlangıçtaki ilk aşamaya (`ٱلْأَوَّل / ٱلْأُولَىٰ`) karşılık sürecin son halkası (`ٱلْءَاخِر`) ve gelecek aşamanın her zaman ilkinden daha hayırlı ve kalıcı oluşu (`وَلَلْءَاخِرَةُ خَيْرٌ لَّكَ مِنَ ٱلْأُولَىٰ`)."
        if (s, a) in {(87, 16), (87, 17), (4, 77), (2, 86)}:
            return "Kısa vadeli yakın olan (`ٱلدُّنْيَا`) ile uzun vadeli sonraki sonuç aşaması (`ٱلْءَاخِرَةُ`) arasındaki tercih: anlık geçici olanı seçmek yerine daha iyi ve daha kalıcı olan sonraki evreyi gözetmek."
        if (s, a) in {(75, 13), (82, 5), (74, 37)}:
            return "İnsanın hayatındaki öncelik ve eylem muhasebesi: neleri önemseyip öne aldığı (`قَدَّمَ`) ile neleri ihmal edip geriye bıraktığının (`أَخَّرَ`) ortaya dökülmesi ve ileri atılma ya da geri çekilme (`يَتَقَدَّمَ أَوْ يَتَأَخَّرَ`) seçimi."
        if (s, a) in {(7, 34), (10, 49), (15, 5), (16, 61), (23, 43), (34, 30), (63, 10), (63, 11), (71, 4), (14, 42), (35, 45)}:
            return "Belirlenmiş süre yasası: topluluklara veya bireylere kendilerini toparlamaları için belirli bir vadeye kadar süre tanınıp ertelenmesi (`يُؤَخِّرُهُمْ`), ancak o vade geldiğinde ne bir an gecikme (`لَا يَسْتَأْخِرُونَ`) ne de erkene alma yaşanması."
        if (s, a) == (15, 24):
            return "Zaman şeridi üzerinde tarihte önden geçmiş kuşaklar (`ٱلْمُسْتَقْدِمِينَ`) ile arkadan/sonradan gelen kuşakların (`ٱلْمُسْتَـْٔخِرِينَ`) tamamının bilinmesi."
        if (s, a) == (3, 153):
            return "Kökün somut mekânsal anlamı: dağılıp uzaklaşan grubun tam arkasındaki cephe ve artçı saflar (`فِىٓ أُخْرَىٰكُمْ`)."
        if (s, a) == (3, 72):
            return "Gündüzün ilk yüzü olan sabah saatleri (`وَجْهَ ٱلنَّهَارِ`) karşısında günün son saati ve kapanışı (`ءَاخِرَهُۥ`)."
        if (s, a) in {(2, 184), (2, 185), (2, 282), (3, 7), (5, 106), (23, 14), (39, 42), (53, 47)}:
            return "Aynı dizide birinciyi izleyen öteki/diğer birim (`ءَاخَر / أُخْرَىٰ / أُخَر`): telafi edilecek başka günler, ikinci tanık, paralel benzetmeli anlatımlar veya yeni bir gelişim/inşa aşaması."
        if (s, a) == (2, 203):
            return "Belirli süreçte acele edip erken ayrılanla (`تَعَجَّلَ`) süreyi uzatıp sonraya bırakan (`تَأَخَّرَ`) arasında sorumlu davrandıkça bir kusur bulunmayışı."
        if lemma == "musota_#oxiriyn":
            return "Tarihte arkadan ve sonradan gelen kuşaklar (`ٱلْمُسْتَـْٔخِرِينَ`)."
        if lemma == "ta>ax~ara":
            return "Süreyi uzatıp sonraya kalmak veya ileri adım atmak yerine geri durmak (`V. bab` `تَأَخَّرَ`)."
        if lemma == "yasota>oxiru":
            return "Vade dolduğunda süreci bir an bile geriye atıp erteleme imkânı bulamamak (`X. bab` `يَسْتَأْخِرُ`)."
        if lemma == ">ax~ara":
            return "Öne sürmenin karşısında geriye bırakmak, ertelemek veya belirli bir vadeye kadar mühlet uzatmak (`II. bab` `أَخَّرَ`)."
        if lemma == "A^xar":
            return "Birinciyi izleyen öteki, diğer, ikinci ya da başka konumda yer alan birim (`ءَاخَر / أُخْرَىٰ / أُخَر`)."
        if pos == 'ADJ':
            return "İlk ve yakın aşamayı izleyen sonraki kalıcı evreye veya sürecin kapanış gününe ait (`ٱلْءَاخِر / ٱلْءَاخِرَة`)."
        return "Yakın ve geçici anlık evrenin ardından kalıcı sonuç olarak gelen sonraki uzun vadeli aşama ya da tarihin sonraki kuşakları (`ٱلْءَاخِرَة / ٱلْءَاخِرِينَ`)."

    elif root_ar == 'أ-م-ر':
        if (s, a) in {(7, 54), (10, 3), (13, 2), (32, 5), (65, 12)}:
            return "Fiziksel yapının ölçülü inşası (`خَلْق`) ile o yapıyı gökten yere adım adım çalıştırıp sevk eden evrensel işletim yasası (`أَمْر`) arasındaki ayrılmaz koordinasyon (`أَلَا لَهُ ٱلْخَلْقُ وَٱلْأَمْرُ / يُدَبِّرُ ٱلْأَمْرَ`)."
        if (s, a) in {(2, 117), (3, 47), (19, 35), (40, 68), (54, 50)}:
            return "Bir süreç kesin karara bağlandığında (`قَضَىٰٓ أَمْرًا`) varlık yasasının zaman kaybı olmadan, göz kırpımı hızında (`كَلَمْحٍۭ بِٱلْبَصَرِ`) ve kesinlikle gerçekleşmesi."
        if (s, a) in {(16, 90), (2, 27), (3, 104), (3, 110), (7, 157), (9, 112), (22, 41), (31, 17)}:
            return "Yapıcı yeşil yön oku olan `أَمَرَ`: adaleti, iyiliği, toplumsal bağları korumayı ve ortak sağduyunun onayladığı değerleri (`ٱلْمَعْرُوف`) teşvik edip yaygınlaştırma yönlendirmesi."
        if (s, a) in {(2, 169), (2, 268), (12, 53)}:
            return "Kökün çift yönlü aynası (`Mesânî`): yapıcı düzenin tam karşısında, kişiye korku, yoksulluk kaygısı, aşırılık ve çirkinlik telkin eden yıkıcı dürtünün ya da benliğin iç baskısının (`لَأَمَّارَةٌۢ بِٱلسُّوٓءِ`) olumsuz yönlendirmesi."
        if (s, a) == (4, 83) and 'INDEF' in f:
            return "Güvenlik veya kriz durumunda topluma ulaşan teyitsiz haber ve olay dosyası (`أَمْرٌ مِّنَ ٱلْأَمْنِ أَوِ ٱلْخَوْفِ`)."
        if (s, a) in {(42, 38), (3, 159), (4, 59), (4, 83), (27, 32)}:
            return "Toplumsal ve kamusal işlerin tek taraflı dayatmayla değil, şeffaf danışma (`شُورَىٰ / شَاوِرْهُمْ`), ortak değerlendirme ve ehil uzman koordinasyonuyla (`أُو۟لِى ٱلْأَمْرِ`) yönetilmesi."
        if (s, a) in {(28, 20), (65, 6)}:
            return "Aynı `VIII. bab` kalıbının iki zıt kutbu: şehirdeki iktidar elitlerinin gizli tasfiye kumpası için kendi aralarında karar bağlaması (`يَأْتَمِرُونَ` `28:20`) karşısında ayrılık sonrası tarafların sağduyuyla ortak uzlaşıya varması (`وَأْتَمِرُوا۟` `65:6`)."
        if (s, a) == (18, 71):
            return "Alışılmış düzen ölçüsünü parçalayıp taşan, bakanı sarsıp irkilten olağanüstü ve ürkütücü büyük olay (`شَيْـًٔا إِمْرًا`)."
        if (s, a) in {(17, 85), (42, 52), (97, 4)}:
            return "Evrensel merkezden gelen yönlendirme paketi kapsamında bilince diriltici etki veren bilgi akışı (`مِنْ أَمْرِ رَبِّى / مِنْ أَمْرِنَا`) ve her süreç kararının yere indirildiği zaman dilimi (`مِّن كُلِّ أَمْرٍ`)."
        if (s, a) in {(2, 210), (3, 109), (22, 76), (35, 4), (42, 53), (57, 5)}:
            return "İnsanların elindeki tüm tekil dosyaların, olayların ve karar süreçlerinin (`ٱلْأُمُور`) kaçınılmaz biçimde son muhasebe merkezine geri dönüp bağlanması (`إِلَى ٱللَّهِ تُرْجَعُ ٱلْأُمُورُ`)."
        if (s, a) in {(20, 93), (24, 63), (33, 36)}:
            return "Bütüncül ilke ve ortak sorumluluk rotası belirlendikten sonra gizlice sıyrılmayı veya ters düşmeyi bırakıp tutarlı biçimde hizalanma uyarısı."
        if lemma == "ya>otamiru":
            return "Tarafların bir araya gelip karşılıklı danışma sonucunda ortak bir eylem kararı bağlaması (`VIII. bab` `اِئْتَمَرَ`)."
        if lemma == "'aAmiruwn":
            return "Toplumu yapıcı ve sağduyulu değerlere doğru aktif biçimde yönlendiren öncü kadrolar (`ٱلْءَامِرُونَ`)."
        if lemma == ">am~aArap":
            return "Kişinin iç dünyasından gelen ve durmadan olumsuza doğru baskı kuran yoğun yönlendirici dürtü (`لَأَمَّارَةٌۢ`)."
        if lemma == "<imor":
            return "Normal sınırları parçalayıp şaşkınlık ve sarsıntı uyandıran olağanüstü aşırı iş (`إِمْرًا`)."
        if lemma == ">amara":
            if 'PASS' in f:
                return "Açık ve net bir yönlendirici görev, sorumluluk veya çalışma rotası almış olmak (`أُمِرَ / يُؤْمَرُ`)."
            return "Bireyi veya topluluğu belirli bir eylem hattına doğru harekete geçirmek ve yön göstermek (`أَمَرَ / يَأْمُرُ`)."
        if 'MP' in f:
            return "İnsanların ve toplumun yürüttüğü tüm süreçler, dosyalar ve olaylar bütünü (`ٱلْأُمُور`)."
        return "Sistemin işletim yasası, belirlenmiş yönlendirici karar ya da üzerinde işlem yürütülen durum/dosya (`ٱلْأَمْر`)."

    elif root_ar == 'ن-و-س':
        if (s, a) in {(49, 13), (4, 1)}:
            return "Irk, kabile, soy ve statü duvarlarını yıkan evrensel eşitlik bildirisi: tek bir ortak kökten gelen insanlık ailesinin (`يَٰٓأَيُّهَا ٱلنَّاسُ`) birbirini tanıyıp paylaşması."
        if (s, a) in {(5, 32), (2, 213), (3, 140)}:
            return "Kolektif insanlık onuru ve tarih yasası: tek bir insan canının tüm insanlık (`ٱلنَّاسَ جَمِيعًا`) kadar değerli sayılması, toplumun ortak kökten ayrışması ve tarihsel dönemlerin insanlar arasında döndürülmesi (`نُدَاوِلُهَا بَيْنَ ٱلنَّاسِ`)."
        if (s, a) in {(18, 54), (17, 94), (3, 79)}:
            return "Aynı ayette incelikli kavram ayrımı (`Furûk`): biyolojik et-kemik beden için `بَشَر`, tartışmacı bireysel iç psikoloji için `إِنسَان`, bilinçli sosyal kalabalık için ise `ٱلنَّاس` kelimesinin seçilmesi."
        if (s, a) in {(114, 1), (114, 2), (114, 3), (114, 5), (114, 6)}:
            return "Kitabın kapanış çağrısı: tüm toplumların yöneticisine ve sığınağına yönelerek insanların göğsüne sızan gizli fısıltılara (`فِى صُدُورِ ٱلنَّاسِ`) ve açık ya da örtülü çevre kaynaklı etkilere (`مِنَ ٱلْجِنَّةِ وَٱلنَّاسِ`) karşı zihni korumak."
        if (s, a) in {(11, 119), (32, 13)}:
            return "Göz önündeki açık toplumsal çevreler (`ٱلنَّاس`) ile perde arkasında gizli hareket eden odaklar (`ٱلْجِنَّة`) arasındaki ortak sorumluluk yasası."
        if (s, a) in {(2, 243), (7, 187), (11, 17), (12, 21), (12, 38), (12, 40), (12, 68), (12, 103), (13, 1), (16, 38), (17, 89), (25, 50), (30, 6), (30, 30), (34, 28), (34, 36), (40, 57), (40, 59), (40, 61), (45, 26)}:
            return "Toplumsal çoğunluk uyarısı: nicelik olarak kalabalık olan yığınların (`أَكْثَرُ ٱلنَّاسِ`) çoğu kez araştırmadan, şükretmeden veya gerçeği kavramadan sürü psikolojisiyle hareket etmesi."
        if (s, a) in {(2, 8), (2, 13), (2, 165)}:
            return "Homojen görünse de derin zihniyet ayrılıkları barındıran toplum kesitleri (`وَمِنَ ٱلنَّاسِ مَن ...`): sahte poz alanlar ile sahte güç odaklarına bağlananlar karşısında tutarlı duruş."
        if (s, a) in {(2, 185), (14, 1), (10, 2), (22, 73), (35, 15)}:
            return "Ayrıcalıklı hiçbir zümreye hapsedilmeden doğrudan bütün insanlığa (`لِلنَّاسِ / يَٰٓأَيُّهَا ٱلنَّاسُ`) yönelen evrensel aydınlanma ve güç sınırını hatırlama çağrısı."
        if (s, a) in {(4, 58), (4, 105), (57, 25)}:
            return "İnsan topluluklarının bir arada güvenle yaşamasını sağlayan temel eksen olarak insanlar arasında (`بَيْنَ ٱلنَّاسِ`) adaleti ve hakkaniyeti ayakta tutmak."
        if 'NOM' in f:
            return "Evrensel çağrının muhatabı, tarihsel eylemin öznesi veya çoğunluk eğilimi sergileyen hareketli insanlık toplumu (`ٱلنَّاسُ`)."
        if 'ACC' in f:
            return "Karanlıktan aydınlığa çıkarılmak ya da uyarılmak üzere hedeflenen bütün insanlık ailesi (`ٱلنَّاسَ`)."
        return "Soy ve bölge sınırını aşarak bütün insanlık kamuoyuna yönelen ya da toplum kesimleri arasındaki etkileşimi gösteren kolektif sosyal bütün (`ٱلنَّاسِ / لِلنَّاسِ`)."

    elif root_ar == 'غ-ف-ر':
        if (s, a) in {(64, 14), (24, 22)}:
            return "Üçlü olgunluk basamağı (`Furûk`): yaptırımı silmek (`تَعْفُوا۟`), sitem ve başa kakmayı bırakmak (`تَصْفَحُوا۟`) ve kişinin kusurunu koruyucu zırh gibi örterek onurunu korumak (`تَغْفِرُوا۟`)."
        if (s, a) in {(42, 37), (45, 14), (2, 263)}:
            return "İnsanlar arası ilişkilerde `غ-ف-ر`: öfke anında kırıp dökmek yerine sükûnetle kusur örtmek (`42:37`), farklı yaşam görüşüne sahip insanlara bile tahammülle örtücü kalmak (`45:14`) ve başa kakılan yardım yerine onur koruyan nazik bir anlayış (`مَغْفِرَةٌ` `2:263`)."
        if (s, a) in {(3, 193), (2, 286), (8, 29)}:
            return "Bireysel ve toplumsal temizlik uyumu: doğruyu yanlıştan ayıran sağduyu ölçütüyle (`فُرْقَان`) birlikte yüzeydeki pürüzleri silip (`كَفَّرَ`) hatanın yıkıcı sonuçlarını koruyucu zırh altına almak (`غَفَرَ`)."
        if (s, a) in {(39, 53), (20, 82), (71, 10)}:
            return "Umutsuzluğun kapısını kapatan yasa: sınırları aşanlara bile ümidi kesmeme çağrısı yapılırken (`لَا تَقْنَطُوا۟`), yanlış rotasından dönüp yapıcı eyleme yönelen her insana yeniden koruma kalkanı (`غَفُور / غَفَّار`) açılması."
        if (s, a) in {(3, 135), (8, 38), (11, 3), (11, 90), (110, 3)}:
            return "Korunma zırhının ön koşulu: yanlışı savunmakta direnmeyip inadı kırmak (`وَلَمْ يُصِرُّوا۟`), zararı fiilen durdurmak (`إِن يَنتَهُوا۟`) ve rotayı düzeltme dönüşüyle arınmayı birleştirmek."
        if (s, a) in {(7, 169), (9, 80), (63, 6), (4, 48)}:
            return "Sorumsuz avuntu ve kesin sınır uyarısı: «nasıl olsa üzerimiz örtülür» diyerek yanlış çıkar peşinde koşmanın (`سَيُغْفَرُ لَنَا`) ve tutum değişmeden yapılan 70 kezlik şekli taleplerin geçersiz sayılması, merkeze ortak koşma sapması dışında her eksiğin onarılabilir oluşu."
        if (s, a) in {(3, 133), (57, 21), (2, 221)}:
            return "Pasif bekleyiş değil, değerler dünyasında birbirini teşvik ederek koruyucu zırh alanına (`مَغْفِرَة`) ve güvenli esenlik bahçesine doğru koşup yarışma çağrısı."
        if (s, a) in {(12, 29), (12, 97), (28, 16), (38, 25), (4, 106)}:
            return "Kendi yanlışını veya aile/yönetim krizindeki hatayı dürüstçe kabullenip yadsımadan onarım ve koruma zırhı (`ٱغْفِرْ / ٱسْتَغْفِرْ`) talep etmek."
        if (s, a) == (9, 114):
            return "Yakınlık ve sorumluluk bilincinin ince ayarı: körü körüne tarafgirlik değil, gerçek ortaya çıktığında sağduyulu sınırı çizebilmek (`ٱسْتِغْفَارُ`)."
        if lemma == "guforaAn":
            return "Kapsamlı koruyucu örtü ve onarım zırhı talebi (`غُفْرَانَكَ`)."
        if lemma == "musotagofiriyn":
            return "Günün sessiz erken saatlerinde özeleştiri yaparak koruyucu arınma talep edenler (`ٱلْمُسْتَغْفِرِينَ`)."
        if lemma == "gaAfir":
            return "Kusurun yıkıcı sonucunu koruyucu kalkanla kapatan ve onaran fail (`غَافِر`)."
        if lemma == "gaf~aAr":
            return "İnsan defalarca tökezlese dahi her dönüşte bıkmadan tekrar koruyucu zırh açan (`غَفَّار`)."
        if lemma == "gafuwr":
            return "Kusuru teşhir etmeden sürekli örten ve şefkatli iyileştirmeyle (`رَحِيم`) bütünleşen kalıcı koruyucu nitelik (`غَفُور`)."
        if lemma == "m~agofirap":
            return "İnsan ilişkilerinde anlayışlı örtü (`2:263`) veya ilahi sistemin sunduğu koruma zırhı alanı (`مَغْفِرَة`)."
        if lemma == "{sotagofara":
            return "Kusurunu görerek inadı bırakmak ve bilinçli bir şekilde koruyucu örtü ile onarım istemek (`X. bab` `اِسْتَغْفَرَ`)."
        if 'PASS' in f:
            return "Geçmişteki yanlışların üzerinin koruma örtüsüyle kapatılması (`يُغْفَرُ`, ön koşulu yanlışı sonlandırmak)."
        return "Hatanın yıpratıcı kuyruğunu başa geçirilen bir miğfer gibi koruyucu kalkanla örterek kişiyi darbeden korumak (`غَفَرَ`)."

    elif root_ar == 'و-ل-ي':
        if (s, a) == (9, 123):
            return "Kökün en somut fiziksel anlamını koruyan tek I. bab fiil (`يَلُونَكُم`): sınır hattında hemen yanı başınızda ve bitişiğinizde tehdit üretenlerle öncelikli yüzleşme."
        if (s, a) == (13, 11):
            return "Topluluk kendi iç tutumunu değiştirmedikçe bozulmayacağı, ancak yıkım kesinleştiğinde araya girip bunu savabilecek hiçbir yöneticinin (`وَالٍ`) kalmayacağı yasası."
        if (s, a) == (5, 107):
            return "Miras veya emanette haksızlık şüphesi doğduğunda hak sahibine bağ bakımından en yakın iki kişinin (`ٱلْأَوْلَيَانِ`) öne çıkıp gerçeği kayda geçirmesi."
        if (s, a) == (8, 72):
            return "Fiilen dayanışma göçüne katılanların birbirinin koruyucu ortağı olması (`أَوْلِيَاء`), katılmayanlarla ise ortak yaşam kurulana dek koruma hukukunun (`وَلَايَة`) başlamaması."
        if (s, a) == (18, 44):
            return "Gösterişçi servet ve güç dengeleri dağıldığında mutlak koruma ve sahiplenme yetkisinin (`ٱلْوَلَٰيَةُ`) yalnız gerçek otoriteye ait olduğunun ortaya çıkması."
        if (s, a) == (2, 115):
            return "Doğu da batı da Bütüncül Kaynak'a aittir; yönlerin kör takıntısına sapmadan yüzünüzü nereye çevirirseniz (`فَأَيْنَمَا تُوَلُّوا۟`) orada hakikatin yüzüyle karşılaşırsınız."
        if (s, a) in ((2, 142), (2, 144), (2, 149), (2, 150)):
            return "Toplumsal bütünlüğü ve ortak odağı kurmak adına yüzleri ve dikkati belirli merkeze döndürme (`فَوَلِّ وَجْهَكَ` / `فَوَلُّوا۟`)."
        if (s, a) == (2, 148):
            return "Her topluluğun yönünü çevirip odaklandığı bir taraf bulunduğu (`مُوَلِّيهَا`); asıl değerin şekil tartışmasında değil iyilik yarışında öne geçmekte olduğu."
        if (s, a) == (2, 177):
            return "Asıl erdemin yalnızca yüzü doğuya ya da batıya çevirmekten ibaret olmayıp (`تُوَلُّوا۟ وُجُوهَكُمْ`) zorlukta paylaşım, sözünde durma ve dirençle ölçülmesi."
        if (s, a) == (2, 257):
            return "İnsanın bağlandığı merkeze göre yön değiştirmesi: güven bağı kuranların koruyucusu karanlıklardan aydınlığa, azgınlık odaklarını yakın seçenlerin hizası karanlığa sürükler."
        if (s, a) in ((3, 28), (5, 51), (60, 1), (60, 9), (60, 13)):
            return "Size düşmanlık, şiddet ve sürgün uygulayan saldırgan odakları yakın stratejik müttefik (`أَوْلِيَآءَ` / `تَوَلَّوْهُمْ`) edinmenin kendi varlığınızı tehlikeye atacağı uyarısı."
        if (s, a) in ((4, 75), (2, 107)):
            return "Zalim baskı altında çaresiz kalan insanların, kendi katından hem yakın koruyucu (`وَلِيًّا`) hem sahada aktif destekçi (`نَصِيرًا`) ulaştırması yönündeki çağrısı."
        if (s, a) == (4, 115):
            return "Hakikat açıkça belirdikten sonra bilinçli biçimde kopup başka yöne sapanı kendi seçtiği rotayla baş başa bırakma (`نُوَلِّهِۦ مَا تَوَلَّىٰ`) yasası."
        if (s, a) == (6, 129):
            return "Haksızlık üreten kesimleri kendi kazandıklarının doğal sonucu olarak birbirinin başına geçirip yakından musallat etme (`نُوَلِّى`)."
        if (s, a) == (10, 62):
            return "Doğru değer hattına sadakatle bağlanan yakınların (`أَوْلِيَآءَ ٱللَّهِ`) geleceğe dönük korku ve geçmişe dönük yıkıcı hüzün taşımaması."
        if (s, a) in ((8, 40), (22, 78)):
            return "Kötü niyetliler sırt dönüp uzaklaşsa bile işleri üstlenen, hiç yarı yolda bırakmayan sarsılmaz destekçi ve koruyucu (`مَوْلَى` ve `نَصِير`)."
        if (s, a) in ((4, 33), (19, 5), (33, 5), (33, 6)):
            return "Arda bırakılan miras varisleri (`مَوَالِى`), soyu bilinmeyenlerin kardeş ve yakın yoldaş sayılması (`مَوَٰلِيكُمْ`) ile hukuki öncelik sıralaması (`أَوْلَى`)."
        if (s, a) == (7, 196):
            return "`تَوَلَّى` fiilinin yakınlaştırıp sahiplenme anlamı: Yaratıcı, dürüst ve yararlı işler üretenlerin sorumluluğunu bizzat yakından üstlenip korur (`يَتَوَلَّى ٱلصَّٰلِحِينَ`)."
        if (s, a) == (28, 24):
            return "Başkalarının işini görüp yardım ettikten sonra dinlenmek için sakin gölgeye doğru yönelip çekilmek (`تَوَلَّىٰٓ إِلَى ٱلظِّلِّ`)."
        if (s, a) == (24, 11):
            return "Bir karalama kampanyasının en büyük payını ve baş sorumluluğunu bizzat üstlenmek (`تَوَلَّىٰ كِبْرَهُۥ`)."
        if (s, a) == (46, 29):
            return "Sözleri sessizce dinleyip kavradıktan sonra uyarıcı sorumlulukla kendi topluluklarına geri dönmek (`وَلَّوْا۟ إِلَىٰ قَوْمِهِم`)."
        if (s, a) == (57, 15):
            return "Yapılan tercihlerin doğal sonucu olan ateşin, kaçacak yer bırakmayacak kadar kişiye bitişik ve ayrılmaz hale gelmesi (`هِىَ مَوْلَىٰكُمْ`)."
        if (s, a) in ((75, 34), (75, 35), (47, 20)):
            return "Kaçınılmaz sarsıntı ve hesaplaşmanın kapının eşiğine, hemen yanı başına kadar dayandığını bildiren yakınlık uyarısı (`أَوْلَىٰ لَكَ`)."
        if (s, a) in ((80, 1), (92, 16)):
            return "Yüzünü asıp iletişimi keserek sırt dönmek (`عَبَسَ وَتَوَلَّىٰٓ`) ya da hakikati yalanlayıp bağını koparmak (`كَذَّبَ وَتَوَلَّىٰ`)."
        if lemma == 'waliY~':
            return "Araya yabancı boşluk sokmadan insanın sırtını dayadığı koruyucu yakın, dost ve dayanışma ortağı (`وَلِىّ / أَوْلِيَاء`)."
        if lemma == 'tawal~aY`':
            if (s, a) in ((5, 56), (5, 80), (9, 23), (16, 100), (22, 4), (58, 14)):
                return "Doğrudan nesne alarak bir odağa yaklaşmak, onu dost ve ittifak ortağı edinip tarafında saf tutmak (`تَوَلَّى`)."
            if (s, a) == (47, 22):
                return "Yetki ve yönetim sorumluluğunu devraldığınızda ya da ilkeden yüz çevirdiğinizde toplumda bozgunculuk ve bağ koparma riski doğması."
            return "Aradaki yakınlık temasını çözüp sırtını dönmek, sorumluluktan çekilmek veya iletişimden uzaklaşmak (`تَوَلَّى`)."
        if lemma == 'wal~aY`':
            return "Yüzünü bir yöne çevirmek ya da tam tersine arkasını dönüp hızla geri çekilmek (`وَلَّى`)."
        if lemma == 'mawolaY`':
            return "İnsanı yarı yolda bırakmadan koruyup işlerini çekip çeviren en yakın hami, destekçi ve kader ortağı (`مَوْلَى`)."
        return "Hak, yakınlık veya yaklaşan sonuç bakımından herkesten ve her şeyden önce gelen öncelik durumu (`أَوْلَى`)."

    elif root_ar == 'ب-ع-د':
        if (s, a) == (9, 42):
            return "Hemen ele geçecek yakın bir menfaat (`قَرِيبًا`) olunca koşup, aşılması gereken yol mesafesi uzayıp zahmetli hale gelince (`بَعُدَتْ عَلَيْهِمُ ٱلشُّقَّةُ`) mazeret üreten çıkarcılık."
        if (s, a) == (11, 95):
            return "Medyen ve Semûd topluluklarının kendi zulümleri sebebiyle yaşam merkezinden tamamen kopup tarih sahnesinden silinmesi (`بُعْدًا لِّمَدْيَنَ كَمَا بَعِدَتْ ثَمُودُ`)."
        if (s, a) == (34, 19):
            return "Güvenli ve birbirine bitişik şehirler arasında konforla yaşarken şımarıp «konaklarımız ve seferlerimiz arasındaki mesafeyi aç, aramızı uzaklaştır» (`بَٰعِدْ`) diyenlerin dağılıp parçalanması."
        if (s, a) == (21, 101):
            return "Önceden güzel ve yapıcı davranış yolu seçenlerin, yakıcı sonuç alanından güvenli bir mesafe açılarak tamamen uzak tutulması (`عَنْهَا مُبْعَدُونَ`)."
        if (s, a) in ((11, 83), (11, 89)):
            return "Zulüm üreten kesimlerin geçmiş yıkım örneklerinden ve acı karşılığından hiç de uzak olmadığı (`بِبَعِيدٍ`), sonucun hemen yanı başlarında durduğu uyarısı."
        if (s, a) in ((27, 22), (50, 31)):
            return "Çok uzaklaşmadan kısa aralıkta dönüş (`غَيْرَ بَعِيدٍ`) veya esenlik alanının iyilik sahiplerinin hemen yanı başına yaklaştırılması (`أُزْلِفَتْ ... غَيْرَ بَعِيدٍ`)."
        if (s, a) in ((21, 109), (70, 6)):
            return "Kimi insanların gelecek hesaplaşmayı uzak görüp küçümsemesine (`يَرَوْنَهُۥ بَعِيدًا`) karşılık, ilkenin onu çok yakın bilmesi ve insan için mesafe ölçüsünün saklı olması (`أَقَرِيبٌ أَم بَعِيدٌ`)."
        if (s, a) == (30, 4):
            return "Hem yenilginin önceki evresinde (`مِن قَبْلُ`) hem de beklenen zaferin sonraki evresinde (`مِنۢ بَعْدُ`) bütün yönetim ve düzen kararının aynı ilkeye ait oluşu."
        if (s, a) in ((2, 27), (98, 4)):
            return "Sağlam sözleşme kurulduktan sonra bağı bozmak (`مِنۢ بَعْدِ مِيثَٰقِهِۦ`) ve açık kanıt geldikten hemen sonra ayrılıp parçalanmak (`مِنۢ بَعْدِ مَا جَآءَتْهُمُ`) çelişkisi."
        if (s, a) in ((3, 30), (43, 38)):
            return "Kişinin kendi kötü eylemleriyle ya da kendisini yanlış yola iten arkadaşıyla arasına devasa mesafe (`أَمَدًۢا بَعِيدًا` / `بُعْدَ ٱلْمَشْرِقَيْنِ`) konmasını dileyeceği yüzleşme anı."
        if (s, a) in ((41, 44), (34, 52), (34, 53)):
            return "Anlamaya kulağını kapatanların uzaktan yankı işitir gibi kopuk kalması (`مِن مَّكَانٍۭ بَعِيدٍ`) ve geç kalınmış anda uzanıp gerçeğe yetişememesi."
        if (s, a) == (25, 12):
            return "Kötü tercihin doğurduğu yakıcı alanın suçluları çok uzak bir mesafeden bile fark edip öfkeli bir uğultuyla karşılaması (`مِن مَّكَانٍۭ بَعِيدٍ`)."
        if (s, a) in ((79, 30), (95, 7)):
            return "Kozmik kuruluş aşamalarının ardından yerin yayılıp yaşanır kılınması sırası (`بَعْدَ ذَٰلِكَ`) ve tüm bu açık düzenlerden sonra gerçeği yalanlamanın anlamsızlığı (`فَمَا يُكَذِّبُكَ بَعْدُ`)."
        if (s, a) in ((2, 176), (4, 60), (4, 116), (4, 136), (4, 167), (14, 3), (14, 18), (22, 12), (22, 53), (34, 8), (41, 52), (42, 18), (50, 3), (50, 27)):
            return "Gerçeklik merkezinden kopup giden derin savrulma (`ضَلَالٍ بَعِيدٍ`), toplum içi uzun ayrışma (`شِقَاقٍ بَعِيدٍ`) veya yeniden dirilişi imkânsız uzaklık sayma (`رَجْعٌۢ بَعِيدٌ`) yanılgısı."
        if lemma == 'buEod':
            return "Zulüm ve direnme yüzünden merkezin tamamen dışına, silinme ve yok oluş uzaklığına itilme (`بُعْدًا`)."
        if lemma == 'baEiyd':
            return "Araya geniş zaman, mekân veya anlayış mesafesi girmiş uzaklık durumu (`بَعِيد`)."
        if pos == 'T':
            return "Önceki bir olayın ya da dönemin hemen arkasına düşen sonraki zaman aralığını ve sıralı akışı göstermek (`بَعْدَ / بَعْدُ`)."
        return "Belirtilen bir eşikten, sözleşmeden veya kişiden sonraki aşamada gelişen durumları bağlamak (`مِنۢ بَعْدِ / بَعْدِى`)."

    elif root_ar == 'د-ع-و':
        if (s, a) in ((2, 186), (40, 60)):
            return "Aracısız yakınlık ve çift taraflı iletişim yasası: seslenenin çağrısına anında karşılık verildiği gibi, insanın da hayatın hakiki çağrısına açık yanıt üretmesi."
        if (s, a) in ((13, 14), (22, 73), (35, 14), (46, 5)):
            return "Gerçek kaynağı bırakıp hiçbir karşılık üretemeyen güçsüz odaklara bel bağlamanın, suya avuç açıp suyun ağzına yükselmesini beklemek kadar boş kalması."
        if (s, a) in ((2, 171), (24, 63)):
            return "Anlamlı çağrıyı çobanın ham seslenişinden ayıramayan sağırlık eleştirisi (`دُعَآءً وَنِدَآءً`) ve yönlendirici elçinin çağrısını hafife almama ilkesi."
        if (s, a) in ((33, 4), (33, 5), (33, 37)):
            return "Evlat edinilmiş bireyleri öz çocuk adlandırmasından ayırarak her insanı kendi biyolojik babasının adıyla çağırıp kimlik hakkını koruma ilkesi (`أَدْعِيَآء` / `ٱدْعُوهُمْ`)."
        if (s, a) in ((2, 221), (10, 25), (16, 125), (41, 33)):
            return "İki zıt yaşam daveti: kimileri yıkıcı çatışmaya ve ateşe çekerken, doğru çağrı bilgelikle esenlik ve barış yurduna davet eder (`سَبِيلِ رَبِّكَ`)."
        if (s, a) in ((10, 12), (41, 49), (41, 51)):
            return "Bunalımda yatarken, otururken veya ayakta uzun uzun yardım çağrısı yapıp, rahata kavuştuğu an hiç çağırmamış gibi yan çizen insan psikolojisi."
        if (s, a) in ((17, 11), (84, 11)):
            return "Aceleci insanın iyilik çağırır gibi düşünmeden kendi yıkımını ve zararını çağırması (`وَيَدْعُ ٱلْإِنسَٰنُ بِٱلشَّرِّ` / `يَدْعُوا۟ ثُبُورًا`)."
        if (s, a) in ((2, 282), (24, 48), (24, 51), (33, 53)):
            return "Sözleşmede şahitlik görevine (`2:282`), anlaşmazlıkta adil hakemliğe (`24:48-51`) ve izinle davete icabete (`33:53`) dayalı toplumsal düzen kuralları."
        if (s, a) in ((36, 57), (41, 31), (67, 27)):
            return "`VIII. bab` çekiminde iki kutup: iyilik yurdunda gönülden çekilip istenen her nimetin sunulması (`مَا يَدَّعُونَ`) ile alayla çağrılan hesaplaşmayla yüzleşme (`تَدَّعُونَ`)."
        if (s, a) in ((7, 5), (10, 10), (21, 15)):
            return "`دَعْوَى` kalıbında iki uç beyan: esenlik yurdunda içten övgü ve yüceltme seslenişi (`10:10`), yıkım anında ise yalnızca haksızlık itirafı kalması (`7:5`, `21:15`)."
        if (s, a) in ((25, 77), (30, 25), (71, 5), (71, 7)):
            return "İnsana değer kazandıran içten yöneliş çağrısı (`لَوْلَا دُعَآؤُكُمْ`), parmakla kulak tıkayan inat (`71:7`) ve topraktan tek çağrı ile uyanış (`30:25`)."
        if lemma == 'daAEiY' or lemma == 'd~aAE':
            return "İnsanları gerçeğe, ortak sorumluluğa ve hakiki kurtuluş hattına yönelten seslenici ve davetçi (`ٱلدَّاعِى / الدَّاعِ`)."
        if lemma == 'daEowap':
            return "Belirli bir anda yükselen tek somut çağrı, davet hamlesi veya yönelmiş istek (`دَعْوَة`)."
        if lemma == "duEaA^'":
            return "Ses ve sözle belirli bir merkeze yönelme çağrısı, yardım isteği veya isimle adlandırma (`دُعَاء`)."
        return "Ses ve anlamlı iradeyle bir tarafı kendine çekmek, yardım istemek, adlandırmak veya belirli bir yola davet etmek (`دَعَا`)."

    elif root_ar == 'ح-ك-م':
        if (s, a) == (3, 7):
            return "Anlam sınırları tartışmaya ve keyfî eğip bükmeye kapatılmış olan, kitabın ana omurgasını oluşturan kesin ilkeler (`ءَايَٰتٌ مُّحْكَمَٰتٌ`) ile benzeşen anlamlı ifadeler ayrımı."
        if (s, a) in ((11, 1), (22, 52), (47, 20)):
            return "Önce bozulma ve parazite karşı sağlam kilitle pekiştirme (`أُحْكِمَتْ` / `يُحْكِمُ`), ardından ayrıntılı açıklama veya uygulanması zorunlu açık hüküm (`مُّحْكَمَةٌ`) ilkesi."
        if (s, a) in ((2, 188), (4, 35), (4, 60), (4, 65)):
            return "Toplumsal uyuşmazlıkların yönetimi: rüşvetle yargıcı yanıltma yasağı (`2:188`), ailede tarafsız arabulucular atama (`4:35`), zorba odaklara yargılanmaya gitmeyi reddetme (`4:60`) ve hakemin verdiği karara içten uyum (`4:65`)."
        if (s, a) in ((4, 58), (4, 105), (5, 42), (5, 44), (5, 45), (5, 47), (5, 48), (5, 49), (5, 50), (38, 22), (38, 26)):
            return "Yargı yetkisinin yalnızca keyfî çıkarlara veya bilgisiz töreye (`حُكْمَ ٱلْجَٰهِلِيَّةِ`) değil, açık hakikate, adalet ve eşitlik ölçüsüne (`بِٱلْعَدْلِ / بِٱلْقِسْطِ / بِٱلْحَقِّ`) dayandırılması yasası."
        if (s, a) in ((6, 136), (10, 35), (16, 59), (29, 4), (37, 154), (45, 21), (68, 36), (68, 39)):
            return "Hiçbir akıl, adalet ve kanıt ölçüsüne sığmayan çarpık değerlendirmeleri sorgulayan keskin eleştiri (`سَآءَ مَا يَحْكُمُونَ` / `كَيْفَ تَحْكُمُونَ`)."
        if (s, a) in ((6, 57), (6, 62), (12, 40), (12, 67), (13, 41), (18, 26), (28, 70), (28, 88), (40, 12), (42, 10)):
            return "Nihai belirleme, yasama ve sonuç bağlama otoritesinin hiçbir aracıya ortak edilmeden yalnızca evrenin kurucusuna ait olduğu ilkesi (`إِنِ ٱلْحُكْمُ إِلَّا لِلَّهِ`)."
        if (s, a) in ((7, 87), (10, 109), (11, 45), (12, 80), (52, 48), (68, 48), (76, 24), (95, 8)):
            return "Kriz ve haksızlık anında dağılmayıp en doğru ve sarsılmaz hükmü verecek olan üstün ölçü sahibinin kararının olgunlaşmasını sebatla bekleme ilkesi."
        if (s, a) in ((2, 269), (16, 125), (17, 39), (31, 12), (38, 20), (43, 63), (54, 5)):
            return "İnsanı cehaletten, öfke ve taşkınlıktan frenleyip her sözü ve eylemi yerli yerine oturtan yüksek sağduyu, bilgelik ve derin kavrayış (`ٱلْحِكْمَة`)."
        if (s, a) in ((12, 22), (19, 12), (21, 74), (21, 78), (21, 79), (26, 21), (26, 83), (28, 14)):
            return "Doğruyla yanlışı ayırt edip somut olaylarda ince çözüm üretebilme olgunluğu ve yönetim muhakemesi (`حُكْمًا وَعِلْمًا`)."
        if (s, a) in ((3, 58), (10, 1), (31, 2), (36, 2), (44, 4)):
            return "İçeriği ve kurgusu tutarsızlıktan arındırılmış, her parçası ince hesapla yerli yerine kilitlenmiş sağlam bildirim veya düzen emri (`ٱلْحَكِيم`)."
        if lemma == 'Hikomap':
            return "Bilgi ve aklı birleştirip aşırılığı frenleyerek doğru eylemi yerli yerine koyma ustalığı (`ٱلْحِكْمَة`)."
        if lemma == 'Hakiym':
            return "Hiçbir işi boşuna ve ölçüsüz bırakmayan, kurduğu her düzeni sağlam kilitle yerli yerine oturtan kusursuz denge sahibi (`ٱلْحَكِيم`)."
        if lemma == 'Hukom':
            return "Keyfiliği durdurup düzeni koruyan kesin yargı, karar yetkisi ve doğru muhakeme ölçüsü (`ٱلْحُكْم`)."
        return "Taraflar arasında adalet ölçüsünü kurmak, azgınlığı frenlemek ve düzeni sağlam zemine oturtmak (`حَكَمَ`)."

    elif root_ar == 'م-ل-ك':
        if (s, a) == (1, 4) or (s, a) == (3, 26):
            return "Karşılık gününün ve bütün egemenlik ağının tek sahibi: yönetim yetkisini dilediğine verip günü gelince geri çekebilen mutlak güç (`مَٰلِكُ ٱلْمُلْكِ`)."
        if (s, a) in ((2, 247), (2, 251), (2, 258), (12, 101), (38, 35), (43, 51)):
            return "Toplumsal ve siyasal yönetim yetkisi (`ٱلْمُلْك`): servete değil bilgi ve dayanıklılığa dayanan liderlik (`2:247`), miras/emanet yönetim (`12:101`, `38:35`) ve Firavun ile Nemrut gibi yöneticilerin güç kibri (`2:258`, `43:51`) ayrımı."
        if (s, a) in ((6, 75), (7, 185), (23, 88), (36, 83)):
            return "Göklerde ve yerde işleyen kesintisiz kozmik yönetim ve denetim ağı (`مَلَكُوت`): varlığın başıboş değil tek bir sağlam otorite elinde tutulduğu bilinci."
        if (s, a) in ((17, 111), (25, 2), (25, 26), (35, 13), (67, 1)):
            return "Yönetim ve hükümranlıkta hiçbir ortağı bulunmayan tek düzen kurucu karşısında, sahte odakların bir hurma çekirdeği zarına bile (`قِطْمِير`) söz geçiremeyişi."
        if (s, a) in ((5, 17), (5, 25), (7, 188), (10, 49), (16, 73), (17, 56), (17, 100), (20, 89), (25, 3), (34, 22), (34, 42), (39, 43), (48, 11), (72, 21), (82, 19)):
            return "İnsanların veya uydurma odakların kendi kendine dahi fayda ve zarar üretememesi, sorumluluk gününde kimsenin bir başkasına yetki geçirememesi (`لَا يَمْلِكُونَ`)."
        if (s, a) in ((4, 3), (4, 24), (4, 25), (4, 36), (16, 71), (16, 75), (23, 6), (24, 31), (24, 33), (24, 58), (30, 28), (33, 50), (33, 52), (33, 55), (70, 30)):
            return "Toplumsal yaşamda sorumluluk ve koruma altına alınan bağımlı kesimler (`مَا مَلَكَتْ أَيْمَانُكُمْ`) ile tam yetkili özgür üretici (`16:75` `عَبْدًا مَّمْلُوكًا` karşısında) arasındaki hak, adalet ve eşitlik ölçüsü."
        if (s, a) in ((20, 87), (24, 61)):
            return "Kendi irade gücüyle karar değiştirme (`بِمَلْكِنَا`) veya evin anahtarlarını ve yönetimini elinde bulundurma sorumluluğu (`مَلَكْتُم مَّفَاتِحَهُۥ`)."
        if (s, a) in ((12, 43), (12, 50), (12, 54), (12, 72), (12, 76), (18, 79), (27, 23), (27, 34)):
            return "Tarihsel toplumlarda yasa ve vergi koyan hükümdarların (`مَلِك / مُلُوك`) halk üzerindeki tasarrufları: bazen şehri bozan kaba güç (`18:79`, `27:34`), bazen stratejik krizi çözen yönetim (`12:54`)."
        if (s, a) in ((20, 114), (23, 116), (54, 55), (59, 23), (62, 1), (114, 2)):
            return "İnsanların geçici ve kusurlu iktidarlarının ötesindeki gerçek, arınmış ve sarsılmaz hükümdarlık (`ٱلْمَلِكُ ٱلْحَقُّ` / `مَلِيكٍ مُّقْتَدِرٍۭ`)."
        if (s, a) in ((2, 102), (7, 20), (12, 31), (43, 77)):
            return "Kozmik görevlilerle ilgili yanlış algıların düzeltilmesi (`2:102` Babil, `7:20` ölümsüzlük yanılgısı, `12:31` Yusuf'a hayranlık benzetmesi) ve yıkım alanındaki baş nöbetçi uyarısı (`43:77`)."
        if lemma == 'malak':
            return "Evren işleyişinde ve vahiy akışında buyrukları eksiksiz iletip uygulayan görevli kozmik güçler (`ٱلْمَلَٰٓئِكَة / مَلَك`)."
        if lemma == 'mulok':
            return "Bir alanı, toplumu veya evreni sıkıca tutup yöneten egemenlik ve yönetim yetkisi (`ٱلْمُلْك`)."
        if lemma == 'ma`lik':
            return "Bir varlığı veya dönemi fiilen elinde tutarak yöneten yetkili sahip (`مَٰلِك`)."
        return "Bir şeye sağlamca el koyup onu elinde tutmak, yönetmek, fayda veya zarar üretmeye gücü yetmek (`مَلَكَ`)."

    elif root_ar == 'ج-ن-ن':
        if (s, a) == (6, 76):
            return "Gecenin karanlığı tüm çevreyi bir örtü gibi kapatıp gizlediğinde (`جَنَّ عَلَيْهِ ٱلَّيْلُ`), gökyüzünü gözlemleyerek kalıcı hakikati arama sahnesi."
        if (s, a) == (53, 32):
            return "Her insanın başlangıçta annesinin karnında gözlerden örtülü küçük bir cenin (`أَجِنَّة`) olarak yetiştiği gerçeğini hatırlatıp kimsenin kendini kusursuz saymaması uyarısı."
        if (s, a) in ((58, 16), (63, 2)):
            return "İki yüzlü çıkarcıların verdikleri bağlayıcı sözleri gerçek niyetlerini saklayan bir kalkan ve siper (`جُنَّة`) haline getirerek doğru yoldan alıkoymaları."
        if (s, a) in ((27, 10), (28, 31)):
            return "Asanın tıpkı hızlı kıvrılıp yuvasına saklanan çevik bir yılan (`جَآنّ`) gibi devinmesi karşısında duyulan doğal ürküntünün güvenle aşılması."
        if (s, a) in ((15, 27), (55, 15)):
            return "İnsandan önce, dumansız saf ateş enerjisinden var edilen ve gözle algılanamayan bilinçli varlık türünün (`ٱلْجَآنّ`) kökeni."
        if (s, a) in ((6, 100), (18, 50), (34, 41), (37, 158), (72, 6)):
            return "Gözle görünmeyen bilinçli varlıklara (`ٱلْجِنّ / ٱلْجِنَّة`) korkuyla sığınma veya onlarla uydurma soylu bağlar kurma yanılgısının yıkılması: onların da sorumlu ve aciz varlıklar olduğunun ilanı."
        if (s, a) in ((34, 12), (34, 14), (46, 29), (51, 56), (72, 1), (114, 6)):
            return "Görünmeyen bilinçli varlıkların (`ٱلْجِنّ / ٱلْجِنَّة`) da tıpkı insanlar gibi irade ve sorumluluk taşıdığı, büyük yapılar kurma veya mesajı dinleyip doğru yolu seçme özgürlüğüne sahip olduğu."
        if lemma == 'majonuwn' or (lemma == 'jin~ap' and 'INDEF' in f):
            return "Değişime direnen zorbaların, hakikat getiren elçinin sözünü dinlememek için «aklı örtülmüş, zihin dengesi bozulmuş» (`مَجْنُون / جِنَّة`) yaftası vurması ve bunun akıl kanıtıyla çürütülmesi."
        if (s, a) in ((2, 35), (7, 19), (7, 22), (7, 27), (20, 117), (20, 121)):
            return "İlk insan çiftinin açıkta kalmadan barındığı ve sınır ihlaliyle ayrılmak zorunda kaldığı korunaklı başlangıç bahçesi (`ٱلْجَنَّة`)."
        if (s, a) in ((2, 265), (2, 266), (17, 91), (18, 32), (18, 33), (18, 35), (18, 39), (18, 40), (25, 8), (34, 15), (34, 16), (68, 17)):
            return "Yeryüzündeki verimli, gölgeli meyve bahçesi örneği üzerinden mal kibri, emeğe saygı, paylaşım ve emeğin bir gecede veya selle elden kayıp gidebileceği yasası."
        if (s, a) in ((6, 99), (6, 141), (13, 4), (23, 19), (26, 57), (26, 134), (26, 147), (36, 34), (44, 25), (50, 9), (71, 12), (78, 16)):
            return "Yağmur suyuyla beslenip dalları birbirine dolanarak toprağı örten dünya bağ ve bahçelerinin (`جَنَّٰت`) geçici refah göstergesi ve ekolojik üretim nimeti olarak okunması."
        if (s, a) in ((3, 133), (55, 46), (55, 54), (55, 62), (57, 21)):
            return "Ölçülü, dürüst ve sorumlu yaşamanın nihai ödülü olan, gökle yer arası genişlikteki ikili veya kapsamlı esenlik bahçesi (`جَنَّة / جَنَّتَانِ`)."
        if (s, a) in ((9, 72), (61, 12)):
            return "Altlarından ırmaklar akan serin esenlik bahçeleri ile kalıcı yerleşim yurtlarının (`جَنَّٰتِ عَدْنٍ`) iç içe sunulan huzur ödülü."
        if lemma == 'jaA^n~' or lemma == 'jin~' or (lemma == 'jin~ap' and 'INDEF' not in f):
            return "Duyuların görüş alanına kapalı kaldığı için görünmeyen bilinçli varlık türünün (`ٱلْجِنّ / ٱلْجَآنّ`) insanlarla aynı sorumluluk düzenine tabi oluşu."
        return "Üretilen her güzel emeğin ve korunaklı yaşam duruşunun karşılığı olarak, tüm tehditlerden örtülüp güvenceye alınmış bereketli ve serin esenlik bahçesi (`ٱلْجَنَّة`)."

    elif root_ar == 'خ-ي-ر':
        if (s, a) in ((28, 68), (33, 36)):
            return "Bilinçli seçim ilkesi: evrensel yasayı koyan yaratıcı iradenin en uygun olanı seçmesi (`يَخْتَارُ`) karşısında, adalet ilkesi açıkça bildirildikten sonra kişiye keyfî kaçamak seçme yetkisinin kalmayışı (`ٱلْخِيَرَة`)."
        if (s, a) in ((7, 155), (20, 13), (44, 32)):
            return "Büyük görevler ve tarihsel sorumluluklar için ehliyet ve bilgi temelinde özel seçilip ayrılma (`ٱخْتَارَ`), ayrıca sınamada kalanların en iyi koruyucu merci (`خَيْرُ ٱلْغَٰفِرِينَ`) olması."
        if (s, a) in ((56, 20), (68, 38)):
            return "V. bab seçim iki yönü: emeğinin karşılığına erenlerin kendi istedikleri meyveleri beğenip seçmesi (`يَتَخَيَّرُونَ`) ile sorumluluktan kaçanlara «sanki kendiniz seçip alabilecekmişsiniz gibi mi?» (`تَخَيَّرُونَ`) eleştirisi."
        if (s, a) == (38, 32):
            return "Süleyman'ın yönetimi hatırlama ve güç aracı olarak sevdiği soylu atları (`حُبَّ ٱلْخَيْرِ`) gözden geçirirken sorumluluk vaktini fark edip ölçüyü yeniden kurması."
        if (s, a) in ((2, 180), (2, 215), (2, 272), (2, 273), (11, 84), (22, 36), (28, 24), (100, 8)):
            return "İnsanların meyledip değer verdiği maddi mal, servet, geçim desteği ve paylaşıma açılması gereken somut imkânlar (`خَيْر`), buna karşın mal hırsının (`لِحُبِّ ٱلْخَيْرِ`) insanı bencil kılması uyarısı."
        if (s, a) in ((50, 25), (68, 12), (70, 21)):
            return "İyiliğin ve maddi paylaşımın önünü sürekli tıkayan (`مَّنَّاعٍ لِّلْخَيْرِ`) ve eline refah geçtiğinde çevresinden esirgeyen (`مَنُوعًا`) bencil tutumun kınanması."
        if (s, a) in ((2, 148), (3, 114), (5, 48), (9, 88), (21, 73), (21, 90), (23, 56), (35, 32)):
            return "Farklı toplulukların birbirini karalamak yerine faydalı işlerde ve ortak iyilik üretmede öne geçmek için yarışması yasası (`فَٱسْتَبِقُوا۟ ٱلْخَيْرَٰتِ`)."
        if (s, a) in ((3, 26), (3, 54), (3, 150), (6, 57), (7, 87), (7, 89), (8, 30), (10, 109), (12, 59), (12, 64), (12, 80), (21, 89), (23, 29), (23, 72), (23, 109), (23, 118), (34, 39)):
            return "Tüm iyi imkânların elinde bulunması (`بِيَدِكَ ٱلْخَيْرُ`) ve koruma, yargı, rızık, plan bozma, merhamet ve miras bırakmada mutlak en yetkin sonuç üretici oluş (`خَيْرُ ٱلْحَٰكِمِينَ / ٱلرَّٰزِقِينَ / ٱلْفَٰصِلِينَ`)."
        if (s, a) in ((38, 47), (38, 48), (55, 70), (98, 7)):
            return "Güven ve faydalı iş üretenlerin bütün yaratıklar içinde en seçkin konuma yükselmesi (`خَيْرُ ٱلْبَرِيَّةِ / ٱلْأَخْيَارِ` ve huyları temiz `خَيْرَٰتٌ`)."
        if (s, a) in ((2, 269), (3, 104), (3, 110), (4, 114), (7, 188), (10, 11), (16, 30), (17, 11), (22, 77), (24, 33), (41, 49), (62, 11)):
            return "Bilgeliğin insana çok büyük bir yarar (`خَيْرًا كَثِيرًا`) kazandırması, iyiye çağırma ödevi (`يَدْعُونَ إِلَى ٱلْخَيْرِ`), içten liyakat (`24:33`) ve iyiliği acele isterken ölçüyü koruma gereği."
        if pos == 'ADJ':
            return "Geçici dünya gösterişine, sayıca çokluğa ya da çıkarcı beklentiye kıyasla kalıcı değerin, doğruluğun ve dürüst tercihin açıkça daha üstün ve faydalı oluşu (`خَيْرٌ وَأَبْقَىٰ`)."
        return "Bilinçli tercihle yönelinen somut fayda, kalıcı değer artışı ve iki seçenek arasındaki açıkça daha yararlı olan yol (`خَيْر`)."

    elif root_ar == 'ع-ن-د':
        if lemma == 'Eaniyd':
            return "Doğruyu görüp bildiği halde kibir ve çıkarcılıkla hizadan yana sapıp inatla direnen, gerçeğe sırt dönen dik kafalı zorba tutum (`عَنِيد`)."
        if pos == 'LOC' and 'ACC' not in f:
            if (s, a) == (28, 78):
                return "Elde edilen bütün başarının ve zenginliğin yalnızca «kendi yanımdaki bilgim sayesinde» (`عَلَىٰ عِلْمٍ عِندِى`) geldiğini sanan Kârûn tipi benmerkezci yanılgı."
            if (s, a) == (12, 60):
                return "Güvenlik ve erzak alışverişinde dürüstlük şartı yerine getirilmezse «yanımda artık pay alamaz ve yakınıma gelemezsiniz» (`عِندِى`) diyen ilkeli yönetim sınırı."
            return "Halkın olağanüstü hazine veya hızlı yıkım beklentilerine karşı elçinin «bunlar benim elimde ve yanımda (`عِندِى`) değil, ben yalnızca iletilene uyarım» diyerek sınırını çizmesi."
        if pos == 'N':
            if (s, a) in ((2, 79), (3, 78)):
                return "Kendi elleriyle yazdıkları metni veya eğip büktükleri sözü çıkar sağlamak için «bu, en yüce kaynaktan (`مِنْ عِندِ ٱللَّهِ`) gelmedir» diye pazarlamanın ağır sahtecilik oluşu."
            if (s, a) in ((3, 165), (4, 78)):
                return "Başarıyı sahiplenip krizi başkasından bilen zihniyete karşı ayna tutulması: sonuçların arkasındaki yasayı tek merkezde görüp kendi hatasını da kendinden (`مِنْ عِندِ أَنفُسِكُمْ`) bilme sorumluluğu."
            if (s, a) in ((4, 82), (2, 89), (28, 49)):
                return "Bilgi ve bildirimin tutarlılık ölçütü: eğer sıradan insan elinden (`مِنْ عِندِ غَيْرِ ٱللَّهِ`) çıkmış olsaydı içinde mutlaka derin çelişkiler bulunurdu."
            return "Bir bilginin, yardımın veya kararın hangi kaynaktan (`مِنْ عِندِ`) doğduğunu tespit edip uydurmayı hakiki kaynaktan ayırt etme ilkesi."
        if (s, a) in ((2, 191), (9, 7), (53, 14)):
            return "Somut mekân ve sınır işareti: saygı ve barış merkezinin hemen bitişik yanı (`عِندَ`) yahut varlık sınırının son noktasındaki durak (`عِندَ سِدْرَةِ ٱلْمُنتَهَىٰ`)."
        if (s, a) in ((16, 96), (28, 60)):
            return "İki birikim alanının karşılaştırılması: insanların elinde tutup biriktirdiği her şey (`مَا عِندَكُمْ`) hızla tükenirken, hakikat ve doğruluk katındaki karşılık kalıcıdır (`وَمَا عِندَ ٱللَّهِ بَاقٍ`)."
        if (s, a) in ((6, 59), (7, 187), (27, 40), (31, 34)):
            return "Görünmeyen yasaların anahtarlarının, gelecek saat bilgisinin ve eşyayı kavrayan derin bilginin kimin elinde/katında (`عِندَهُ`) bulunduğu sorusunun yanıtı."
        if (s, a) in ((2, 80), (19, 78), (40, 35), (81, 20)):
            return "Yetkili kat nezdinde uydurma ayrıcalık sözü aldığı iddiasının çürütülmesi ve dürüst emek sahibinin o kat nezdindeki yüksek itibarı (`عِندَ ذِى ٱلْعَرْشِ مَكِينٍ`)."
        return "Her eylemin, niyetin ve iddianın sıradan insan ölçüsünde değil, şaşmaz evrensel adalet ve doğruluk terazisi katında (`عِندَ`) tartılıp değer kazanması."

    elif root_ar == 'ن-و-ر':
        if (s, a) == (2, 17):
            return "İki yönlü ayet içi örnek: karanlıkta çevreye parlasın diye ateş (`نَار`) yakıldığı halde içgörü aydınlığı (`نُور`) çekilince geriye yalnızca koyu karanlık ve şaşkınlığın kalması."
        if (s, a) == (24, 35):
            return "Evrensel aydınlanma tablosu: ateş (`نَار`) değmese dahi kendi saf doğasıyla parlayan ışık kaynağı, gökler ile yerin aydınlık düzeni ve katmanlı ışık üstüne ışık (`نُورٌ عَلَىٰ نُورٍ`) yasası."
        if (s, a) in ((10, 5), (25, 61), (71, 16)):
            return "Kozmik görev bölümü (`Furûk`): Güneş yakıcı enerji kandili iken (`ضِيَاء / سِرَاج`), Ay göz yormadan zaman ve yön hesabı yaptıran yumuşak aydınlıktır (`نُور / مُنِير`)."
        if (s, a) == (33, 46):
            return "Rehberlik modeli: elçinin baskı kuran yahut yakıp kıran bir güç değil, yolu yumuşakça gösteren aydınlatıcı bir kandil (`سِرَاجًا مُّنِيرًا`) olması."
        if (s, a) in ((3, 184), (22, 8), (31, 20), (35, 25)):
            return "Sağlam yazılı belge ölçütü: bilgiye, rehbere ve karanlığı dağıtan aydınlatıcı kitaba (`كِتَابٌ مُنِير`) dayanmadan körü körüne yürütülen tartışmaların geçersizliği."
        if (s, a) in ((2, 257), (5, 16), (14, 1), (14, 5), (33, 43), (57, 9), (65, 11)):
            return "Karanlıktan aydınlığa çıkış yasası: insanı parçalı, dağınık ve çoğul karanlıklardan (`ٱلظُّلُمَاتِ`) çekip her zaman tekil olan berrak aydınlığa (`ٱلنُّورِ`) ulaştıran düzen."
        if (s, a) in ((6, 1), (13, 16), (24, 40), (35, 20), (39, 22), (39, 69), (42, 52)):
            return "Varoluş ve algı yasası: karanlıkla aydınlığın eşit olmayışı, gerçek bilincin sahibinden aldığı ışıkla yol bulması ve o ışık verilmezse hiçbir derinliğin görülememesi."
        if (s, a) in ((9, 32), (61, 8)):
            return "Hakikatin sönmezliği: baskı ve propagandayla (`أَفْوَاهِهِمْ`) evrensel aydınlığı söndürmeye kalkışanların çaresizliği karşısında sistemin kendi ışığını tamamlaması."
        if (s, a) in ((57, 12), (57, 13), (57, 19), (57, 28), (66, 8)):
            return "Önü açan emek ışığı: kimsenin başkasından ödünç alamadığı (`اِقْتَبِسُوا مِن نُورِكُمْ`), herkesin kendi dürüst yaşamıyla kazanıp önünü ve sağını aydınlattığı ışık (`نُورُهُمْ`)."
        if lemma in ('nuwr', 'm~uniyr'):
            return "Düşünce karışıklığını ve cehaleti dağıtarak insana açık yol, sağduyu ve güvenli yön kazandıran aydınlatıcı mesaj ve kavrayış ışığı (`نُور`)."
        if (s, a) in ((18, 96), (20, 10), (27, 7), (27, 8), (28, 29), (36, 80), (56, 71), (13, 17)):
            return "Fiziksel enerji ve uygarlık aracı olarak ateş (`نَار`): yeşil ağaçtaki gizli enerjiden çıkan, madenleri arıtan, soğuk gecede yolcuyla buluşan ısı ve ışık kaynağı."
        if (s, a) in ((21, 69), (29, 24), (85, 5), (5, 64), (2, 266), (3, 183)):
            return "Doğadaki ve tarihteki fiziksel ateş yasası: yakmak için tutuşturulan alev hendeklerinin veya savaş ateşinin yüksek iradeyle söndürülüp «serin ve esenlik» (`بَرْدًا وَسَلَامًا`) kılınması."
        if (s, a) in ((7, 12), (15, 27), (38, 76), (55, 15), (55, 35)):
            return "Varlık hammaddesi olarak ateş (`نَار`): yoğun topraktan ayrı olarak dumansız, yalın ve akışkan enerji tabiatından yaratılan görünmeyen bilinçli varlıkların yapı malzemesi."
        if (s, a) in ((2, 174), (4, 10), (3, 103), (9, 35), (104, 6)):
            return "İçsel ve toplumsal yakıcı dönüşüm: savunmasızların hakkını yemenin karınlara ateş tıkamak oluşu, bölünme çukurunun kenarında uyanış ve doğrudan yüreklere işleyen vicdan ateşi."
        return "Bireysel ve toplumsal düzeyde bile bile sergilenen zulmün, hakikat örtbasının ve sorumsuz tercihlerin kendi elleriyle hazırladığı yakıcı yıkım ve bedel ateşi (`ٱلنَّار`)."

    elif root_ar == 'ح-س-ن':
        if (s, a) in ((23, 14), (32, 7), (37, 125), (40, 64), (64, 3), (95, 4)):
            return "Yaratılış ve tasarım mühendisliği: var edilen her parçanın tesadüfsüz, kusursuz uyumla (`أَحْسَنَ كُلَّ شَىْءٍ`) yerli yerine oturtulması ve insanın en dengeli kıvamda (`فِىٓ أَحْسَنِ تَقْوِيمٍ`) kurulması."
        if (s, a) in ((11, 7), (18, 7), (67, 2)):
            return "Nicelik yerine nitelik sınavı: sistemin insanları sayıca çok iş yapanı değil, kimin işini en sağlam, özenli ve kaliteli yaptığını (`أَيُّكُمْ أَحْسَنُ عَمَلًا`) ortaya çıkarmak için var edilişi."
        if (s, a) == (16, 90):
            return "Toplumsal denge ikilisi (`Furûk`): hak ölçüsünü sıfır haksızlıkla korumak olan adaletin (`ٱلْعَدْل`) üstüne gönüllü zerafet ve fazladan değer katma (`ٱلْإِحْسَٰن`) ilkesi."
        if (s, a) in ((17, 53), (23, 96), (29, 46), (41, 34)):
            return "Kötülüğü dönüştürme stratejisi: kırıcı ve kaba tepkiye eşit sertlikle değil, en yapıcı ve olgun tutumla (`ٱدْفَعْ بِٱلَّتِى هِىَ أَحْسَنُ`) karşılık verip düşmanlığı eritmek."
        if (s, a) in ((39, 18), (39, 23), (39, 55)):
            return "Eleştirel akıl süzgeci: her sözü dinleyip içlerinden en tutarlı, sağlam ve yerinde olanına (`فَيَتَّبِعُونَ أَحْسَنَهُ`) uyma olgunluğu."
        if (s, a) in ((7, 180), (17, 110), (20, 8), (59, 24)):
            return "Yaratıcıyı tanıtan en eksiksiz ve uyum dolu nitelik bütünü (`ٱلْأَسْمَآءُ ٱلْحُسْنَىٰ`) üzerinden doğru kavrayışa ulaşma."
        if (s, a) in ((2, 83), (4, 36), (6, 151), (17, 23), (29, 8), (46, 15)):
            return "Toplumsal ağın temeli: önce anne babaya, ardından akrabalara, yetimlere, yoksullara ve bütün insanlara karşı nazik, özenli ve gönül alan tutum (`إِحْسَان` / `حُسْن`)."
        if (s, a) in ((2, 245), (5, 12), (57, 11), (57, 18), (64, 17), (73, 20)):
            return "Bencilliği kıran paylaşım modeli: darlık içindekilere başa kakmadan, sırf iyilik ve dayanışma bilinciyle sunulan destek (`قَرْضًا حَسَنًا`)."
        if (s, a) in ((9, 107), (35, 8)):
            return "Sahte güzellik yanılgısı uyarısı: yıkıcı tutumu süslü sanıp kendini kandırmak (`35:8`) yahut zarar odağını «biz sadece iyilik istedik» (`ٱلْحُسْنَىٰ`) kılıfıyla gizlemek."
        if (s, a) in ((10, 26), (11, 114), (17, 7), (55, 60)):
            return "Karşılıklı ahlak ve etki-tepki yasası: özenli iyiliğin kendi benliğine dönmesi, iyi işlerin eski lekeleri silmesi ve iyiliğin tek gerçek karşılığının yine iyilik oluşu (`55:60`)."
        if lemma in ('muHosin', 'muHosina`t', '>aHosana', '<iHosa`n'):
            return "Sorumluluğu üstünkörü geçiştirmeden işini sağlam, dürüst ve yapıcı özenle tamamlama bilinci (`إِحْسَان / مُحْسِن`)."
        return "Dengesi yerinde, çirkinlik ve dağınıklıktan arınmış kaliteli söz, güzel örnek (`60:4`), verimli eylem (`حَسَنَة`) ve hak edilmiş kalıcı esenlik sonucu (`حُسْن`)."

    elif root_ar == 'ض-ل-ل':
        if (s, a) in ((2, 282), (20, 52), (32, 10), (68, 26), (93, 7)):
            return "Kökün en somut temel anlamları: yazılı sözleşmede tanığın şaşırıp unutması (`2:282`), mutlak bilginin hiç şaşmaması (`20:52`), bedenin toprakta izini kaybedip dağılması (`32:10`), bahçenin yerini şaşırma (`68:26`) ve elçinin ilk arayış dönemindeki rehbersizlik (`93:7`)."
        if (s, a) in ((12, 8), (12, 30), (12, 95), (26, 20)):
            return "İnsani yargı ve duygusal sapma örnekleri: sevgi ya da telaş yüzünden dengeyi ve ölçüyü kaçırıp yanılgıya düşmek (`ضَلَٰل`)."
        if (s, a) in ((18, 104), (47, 1), (47, 4), (47, 8), (105, 2), (10, 30)):
            return "Çaba ve planların boşa gitmesi (`ضَلَّ / تَضْلِيل`): hakikati ve adaleti ıskalayan hilelerin, uydurulan sahte dayanakların ve yanlış amaçla biriken işlerin iz bırakmadan çöpe gitmesi."
        if (s, a) in ((53, 2), (17, 72), (17, 97), (27, 81), (30, 53), (43, 40)):
            return "Aynı ayet içi ince ayrım (`Furûk`): elçinin ne pusulasını kaybetmesi (`مَا ضَلَّ`) ne de hevese yenilmesi (`مَا غَوَى`), buna karşılık gerçeğe gözünü yuman körlüğün (`عَمًى`) kişiyi daha derin yönsüzlüğe itmesi."
        if (s, a) in ((2, 16), (2, 175), (4, 44), (6, 56), (10, 32), (38, 26)):
            return "Bilinçli seçim ve pusula kaybı yasası: doğruluk dururken çarpıklığı satın almak, kişisel çıkar ve hevese (`ٱلْهَوَىٰ`) uyarak doğrudan sapmak ve gerçeğin dışında yalnızca şaşkınlığın kaldığını görmek."
        if (s, a) in ((7, 30), (16, 36), (16, 125), (39, 37), (53, 30)):
            return "Yönlendirme sınırları: insanı zorla saptıran bir kader değil, herkesin kendi tercihi yönünde pusulasını kaybetmesi yahut doğru yolda olanı da sapanı da yalnızca ana merkezin bilmesi."
        if lemma == '>aDal~':
            return "Duyularını ve aklını işletmediği için yolunu hayvan sürüsünden bile daha ağır biçimde yitirmiş yönsüz karakterler (`أَضَلُّ`)."
        if lemma == 'm~uDil~':
            return "Başkalarını bilinçli algı oyunlarıyla doğru hizadan çıkarıp yanlış rotaya çeken aldatıcı aktör (`مُضِلّ`)."
        return "Ana doğruluk çizgisini, hedef bilincini ve yaşam pusulasını yitirerek boşlukta savrulma, iz kaybetme ve yanlış rotada ısrar etme hali (`ضَلَال / ضَلَّ`)."

    elif root_ar == 'س-م-ع':
        if (s, a) in ((12, 31), (18, 101), (19, 98), (20, 108), (88, 11)):
            return "Doğrudan fiziksel ses ve duyum bağlamı: hafif bir adım sesi ya da tıkırtı yakalamak (`19:98`), sessiz bir fısıltı duymak (`20:108`), kırıcı ve boş gürültüden arınmış ortam (`88:11`), dedikoduyu işitmek (`12:31`) veya uyarı sesine katlanamamak (`18:101`)."
        if (s, a) in ((2, 20), (6, 46), (10, 31), (16, 78), (17, 36), (23, 78), (32, 9), (46, 26), (67, 23), (76, 2)):
            return "İnsanın temel veri alma donanımı: doğuştan bilgisiz gelen insana verilen tekil ve ortak alıcı işitme kanalı (`سَمْع`), çoğul bakış açıları (`أَبْصَار`) ve kavrayış merkezleri (`أَفْئِدَة`). Metin, doğrulanmamış bilginin peşine düşülmemesi kaydıyla kulakla alınan her veriden sorumluluk doğacağını (`17:36`) vurgular."
        if (s, a) in ((2, 93), (2, 285), (4, 46), (5, 7), (6, 36), (8, 21), (8, 22), (8, 23), (24, 51)):
            return "Sözün kulağa çarpmasıyla gerçekten işitmenin ayrımı: sadece dille işittik deyip direnenlerle (`2:93`, `8:21`) sesin gereğini eyleme dönüştürenler (`2:285`, `24:51`) aynı değildir. İçten bir yatkınlık bulunmuyorsa ses fiziksel olarak ulaşsa da bilinç düzeyinde duyurma (`إِسْمَاع`) gerçekleşmez (`8:23`)."
        if (s, a) in ((7, 204), (15, 18), (20, 13), (22, 73), (26, 212), (26, 223), (37, 8), (39, 18), (46, 29), (50, 37), (50, 41), (52, 38), (72, 1), (72, 9)):
            return "Gelişigüzel duymadan öte iradeli biçimde dikkat kesilme (`اسْتِمَاع`) ve gizli bilgi sızdırma girişimleri (`37:8`, `72:9`): dış gürültüyü susturup odaklanmak (`7:204`, `50:37`) ve bütün sözleri dinleyip içinden en tutarlı olanını izlemek (`39:18`) bu alanın temelini oluşturur."
        if (s, a) in ((2, 7), (7, 179), (10, 42), (16, 108), (21, 45), (27, 80), (27, 81), (30, 52), (30, 53), (35, 14), (35, 22), (43, 40), (45, 23), (47, 23), (67, 10)):
            return "Zihinsel sağırlık ve kapanmış alıcılar: ses dalgası kulak zarını titreştirse de akıl ve vicdan kanallarını kapatan kimselere anlam içeriğini duyurmak (`تُسْمِعُ`) mümkün değildir (`27:80`, `35:22`). İnsan kulak verip akletmeyi bıraktığında (`67:10`, `7:179`) algı kapısı kendi tercihiyle mühürlenir (`2:7`, `45:23`)."
        if (s, a) in ((5, 41), (5, 42), (9, 47), (11, 24), (18, 26), (19, 38), (20, 46), (41, 20), (41, 22), (58, 1)):
            return "İşitme duyusunun tanıklığı ve yanlış yönlendirilmiş dinleme: yalana ve bozguncu fısıltılara sürekli kulak kabartanlar (`سَمَّاعُونَ` `5:41-42`, `9:47`) bulunduğu gibi, hesaplaşma günü insanın kendi ses kayıtlarının bizzat tanık çıkması (`41:20-22`) ve dert yanan en sessiz sesin bile anında işitilmesi (`58:1`) anlatılır."
        if lemma == 'samiyE':
            return "Evrendeki açık sözleri de en gizli fısıltıları ve yardım çağrılarını da eksiksiz yakalayan kesintisiz işitme niteliği (`سَمِيع`), sıklıkla ardındaki niyeti tam bilen (`عَلِيم`) ve somut eylemi gören (`بَصِير`) nitelikleriyle birlikte anılır (`58:1`, `3:38`, `14:39`)."
        return "Kulak yoluyla ses dalgalarını algılama (`سَمِعَ`), iradeyle dikkat kesilip odaklanma (`ٱسْتَمَعَ`) ve alınan mesajı zihinde tartıp eylemle yanıtlama süreci (`سَمْع`)."

    elif root_ar == 'ب-ن-ي':
        if (s, a) in ((2, 22), (40, 64), (50, 6), (51, 47), (78, 12), (79, 27), (91, 5)):
            return "Kozmik mimari: insanın yaşadığı yeryüzü döşeğinin üstünü çatlak ve eksik bırakmadan koruyucu bir yapı (`بِنَآء / بَنَىٰ`) olarak kurup yükseltme gerçeği."
        if (s, a) in ((9, 109), (9, 110), (16, 26), (18, 21), (26, 128), (37, 97), (38, 37), (39, 20), (40, 36), (61, 4), (66, 11)):
            return "Sağlam zemin ile kaypak zemine kurulan yapı ayrımı: erdemli ilke üzerinde yükselen dayanışma yapısı (`61:4`, `9:109`) kalıcı olurken çıkarcı bina (`9:110`), kibir kuleleri (`26:128`, `40:36`) ve temelinden çöken düzen (`16:26`) yıkıma gider."
        if (s, a) in ((2, 177), (2, 215), (4, 36), (8, 41), (9, 60), (17, 26), (30, 38), (59, 7)):
            return "Yola bağlanan aidiyet mecazı: kendi toprağından uzakta yalnızca yolun üzerinde tutunduğu için «yolun çocuğu» diye anılan, toplumun destekleyip korumakla yükümlü olduğu muhtaç yolcu (`ٱبْنَ ٱلسَّبِيلِ`)."
        if (s, a) in ((6, 100), (16, 57), (37, 149), (37, 153), (43, 16), (52, 39)):
            return "Çifte standartlı cinsiyetçilik eleştirisi: doğan kız çocuklarına burun kıvırıp Yaratıcıya kız isnat ederken kendilerine erkek çocuk seçmeye kalkışan tutarsız zihniyetin reddi (`بَنَات / بَنِينَ`)."
        if (s, a) in ((3, 14), (11, 42), (11, 45), (11, 46), (12, 5), (18, 46), (31, 13), (31, 16), (31, 17), (37, 102)):
            return "Aile içi şefkat ve gerçek aile tanımı: babanın çocuğuna sevgiyle «yavrucuğum» (`يَٰبُنَىَّ`) diye öğüt vermesi, buna karşılık servet ve çocukların geçici dünya süsü oluşu (`18:46`) ve erdem dışı kalan öz evladın bile gerçek aileden sayılamayışı (`11:45-46`)."
        if (s, a) in ((4, 171), (5, 17), (5, 18), (9, 30), (19, 34)):
            return "İnsani soy sınırı: annesinden dünyaya gelen Meryem oğlu Îsâ'nın insan konumu (`ٱبْنُ مَرْيَمَ`) ve hiçbir topluluğun Mutlak Kaynağın ayrıcalıklı çocuğu olmayıp diğer tüm insanlar gibi yaratılmış varlıklar oluşu (`5:18`)."
        if (s, a) in ((5, 27), (7, 26), (7, 27), (7, 31), (7, 35), (7, 172), (17, 70), (36, 60)):
            return "Ortak insanlık çatısı (`بَنِىٓ ءَادَمَ`): yeryüzünde onurlu kılınan bütün insan neslinin ortak sorumluluğu, ölçülü yaşamı ve ilk iki kardeşten bu yana süren seçim sınavı (`5:27`)."
        if lemma in ('banaAt', '{bonat'):
            return "Aile yapısını kuran kız evlatlar, evlilik sınırlarını belirleyen akrabalık hukuku (`4:23`) ve İmran kızı Meryem gibi dürüst karakter örnekleri (`66:12`)."
        return "Parçaları sağlam temel üstünde birleştirip yapı kurma (`بَنَى / بُنْيَان`) ve aynı aile yahut tarih hattını geleceğe taşıyan evlat ve topluluk bağı (`ٱبْن / بَنِى / بَنَات`)."

    elif root_ar == 'ح-ي-ي':
        if (s, a) in ((2, 164), (16, 65), (25, 49), (29, 63), (30, 19), (30, 24), (30, 50), (35, 9), (36, 33), (41, 39), (45, 5), (50, 11), (57, 17)):
            return "Ekolojik fizik çapa: gökten inen suyla kurak ve ölü toprağın kabarıp yeşertilmesi (`فَأَحْيَا بِهِ ٱلْأَرْضَ بَعْدَ مَوْتِهَا`) üzerinden canlılık ve yeniden diriliş yasasının somut kanıtlanması."
        if (s, a) == (21, 30):
            return "Evrensel biyolojik ilke: gökler ile yerin ayrılışının ardından canlı işlev taşıyan her bir varlık biriminin su temelli (`مِنَ ٱلْمَآءِ كُلَّ شَىْءٍ حَىٍّ`) olarak var edilmesi."
        if (s, a) in ((3, 27), (6, 95), (10, 31)):
            return "Kesintisiz varoluş döngüsü: tohumdan bitki, cansız maddeden canlı organizma ve canlı olandan durgun madde çıkarılarak (`يُخْرِجُ ٱلْحَىَّ مِنَ ٱلْمَيِّتِ`) döngünün sürdürülmesi."
        if (s, a) in ((2, 28), (2, 73), (2, 243), (2, 258), (2, 259), (2, 260), (3, 49), (3, 156), (7, 158), (9, 116), (10, 56), (15, 23), (22, 6), (22, 66), (23, 80), (26, 81), (30, 40), (36, 12), (36, 78), (36, 79), (40, 11), (40, 68), (42, 9), (44, 8), (45, 26), (50, 43), (53, 44), (57, 2), (75, 40)):
            return "Durağanlıktan işlerliğe geçiş yasası: varlığın ilk yokluk/ölüm halinden hayata çıkarılışı, biyolojik ölümün ardından tekrar diriltilişi (`يُحْىِۦ وَيُمِيتُ` / `أَمَتَّنَا ٱثْنَتَيْنِ وَأَحْيَيْتَنَا ٱثْنَتَيْنِ`) ve bu yetkinin tek merkezde oluşu."
        if (s, a) in ((5, 32), (2, 179)):
            return "Toplumsal yaşam hakkı hukuku: haksız öldürmeyi durduran adaletli karşılık yasasında ortak hayat güvencesi bulunması (`فِى ٱلْقِصَاصِ حَيَوٰةٌ`) ve tek bir canı kurtarmanın tüm insanlığı yaşatmakla eş değer tutulması (`وَمَنْ أَحْيَاهَا`)."
        if (s, a) in ((6, 122), (8, 24), (16, 97), (35, 22), (36, 70)):
            return "Bilinç ve erdem diriliği: algısı ölmüş taş gibi donukluktan çıkıp ışıkla canlanma (`مَيْتًا فَأَحْيَيْنَٰهُ`), diriltici çağrıya kulak verme (`لِمَا يُحْيِيكُمْ`), temiz ve huzurlu yaşam (`حَيَوٰةً طَيِّبَةً`) ile uyarının yalnız algısı açık dirilere (`مَن كَانَ حَيًّا`) ulaşması."
        if (s, a) in ((2, 154), (3, 169), (16, 21), (19, 15), (19, 31), (19, 33), (19, 66), (77, 26)):
            return "Ölüm sonrası ve boyutlar arası dirilik: uğruna ölenlerin yok olmayıp yüksek katta diri oluşu (`بَلْ أَحْيَآءٌ عِندَ رَبِّهِمْ`), sahte sığınakların ölü cansızlığı (`أَمْوَٰتٌ غَيْرُ أَحْيَآءٍ`) ve doğum-ölüm-yeniden diriliş hattı."
        if (s, a) in ((2, 255), (3, 2), (20, 111), (25, 58), (40, 65)):
            return "Mutlak dirilik mercii (`ٱلْحَىُّ ٱلْقَيُّومُ`): uyuklama, yorulma ve ölümün dokunamadığı, bütün varlığı ayakta tutan değişmez yaşam kaynağı."
        if (s, a) in ((2, 49), (7, 127), (7, 141), (14, 6), (28, 4), (40, 25)):
            return "X. babın somut sağ bırakma kutbu: zorba yönetimin erkek evlatları kesip kadınların canına dokunmadan hayatta tutması (`يَسْتَحْيُونَ نِسَآءَكُمْ` — İbn Fâris'in 1. aslı olan «خلاف الموت» doğrudan korunur)."
        if (s, a) in ((2, 26), (28, 25), (33, 53)):
            return "X. babın hassas sakınma ve geri durma kutbu: diri bir vicdanın nezaket sınırında çekinmesi (`تَمْشِى عَلَى ٱسْتِحْيَآءٍ` / `فَيَسْتَحْىِۦ مِنكُمْ`) karşısında Mutlak Otoritenin gerçeği ve örneği söylemekten geri çekilmemesi (`لَا يَسْتَحْىِۦ`)."
        if (s, a) in ((4, 86), (10, 10), (14, 23), (24, 61), (25, 75), (33, 44), (58, 8)):
            return "II. bab dirilik ve esenlik dileği (`حَيَّا / تَحِيَّة`): karşılaşmalarda ve kalıcı yurtlarda birbirine sağlıklı yaşam ve esenlik (`سَلَٰم`) dileme ilkesi ile `58:8`'deki ikiyüzlü alay selamı eleştirisi."
        if (s, a) == (20, 20):
            return "Fiziksel canlılık somutlaşması: Mûsâ'nın elindeki cansız asanın yere bırakılınca kıvrak biçimde akıp devinen canlı bir yılana (`حَيَّةٌ تَسْعَىٰ`) dönüşmesi."
        if (s, a) in ((8, 42), (20, 74), (87, 13)):
            return "I. bab yaşama çizgisi: açık kanıt ve tutarlılık üzerinde ayakta kalıp yaşamak (`وَيَحْيَىٰ مَنْ حَىَّ عَنۢ بَيِّنَةٍ` `8:42`) veya sorumsuzluğun sonunda ne ölüp kurtulma ne de rahat yaşama bulamama (`لَا يَمُوتُ فِيهَا وَلَا يَحْيَىٰ`)."
        if (s, a) in ((29, 64), (89, 24), (2, 96), (6, 162), (45, 21), (17, 75), (20, 97)):
            return "Gerçek ve bütünlüklü yaşam ölçüsü: yakın ve geçici yaşam evresinin geçici bir oyun oluşu (`29:64`) karşısında sonraki yurdun sönmeyen asıl yaşam (`لَهِىَ ٱلْحَيَوَانُ` / `لِحَيَاتِى`) olması ve çıplak biyolojik ömrün tek başına değer üretmemesi (`2:96`, `45:21`)."
        if (s, a) in ((7, 25), (23, 37), (45, 24)):
            return "Yeryüzündeki yaşama-ölme sınırları (`7:25`) ile «yalnızca şu geçici dünya hayatımız vardır, ölürüz ve yaşarız» diyen tek boyutlu yaşam algısının eleştirisi (`23:37`, `45:24`)."
        return "Geçici dünya yaşam evresi (`ٱلْحَيَوٰةِ ٱلدُّنْيَا`): insanın kalıcı değerler ile geçici çekicilikler (`لَعِبٌ وَلَهْوٌ / مَتَٰعُ ٱلْغُرُورِ`) arasında sınandığı kısa ve hareketli varoluş aşaması."

    elif root_ar == 'خ-ر-ج':
        if (s, a) in ((2, 74), (24, 43), (30, 48), (41, 47), (55, 22), (79, 29)):
            return "Fiziksel çıkış yasası: sert kayadan su fışkırması (`2:74`), buluttan yağmur dökülmesi (`24:43`), tomurcuktan meyve sıyrılması (`41:47`), denizden inci/mercan çıkması (`55:22`) ve geceden kuşluk aydınlığının doğması (`79:29`)."
        if (s, a) in ((2, 22), (2, 61), (2, 267), (6, 99), (7, 57), (7, 58), (14, 32), (20, 53), (23, 20), (32, 27), (35, 27), (36, 33), (39, 21), (48, 29), (78, 15), (79, 31), (87, 4), (99, 2)):
            return "Toprağın üretim döngüsü: gökten inen suyla yerden rengârenk ürünler, ekin filizleri, otlaklar ve yeraltı ağırlıklarının (`99:2`) dışarı çıkarılması, verimli belde ile çorak belde arasındaki çıktı farkı (`7:58`)."
        if (s, a) in ((16, 69), (16, 78), (22, 5), (40, 67), (86, 7)):
            return "Canlı bünyesinden çıkış yasası: anne rahminden bilgisiz bebek olarak dünyaya çıkış (`16:78`, `22:5`), bedenden fışkıran yaşam sıvısı (`86:7`) ve arıların karnından çıkan rengârenk şifa (`16:69`)."
        if (s, a) in ((2, 257), (5, 16), (6, 122), (14, 1), (14, 5), (33, 43), (57, 9), (65, 11)):
            return "Aydınlanma ekseni: parçalı karanlıkların (`ٱلظُّلُمَٰتِ`) içinden çekilip tekil berrak aydınlığa (`ٱلنُّورِ`) çıkarılma süreci ile o karanlıktan hiç çıkamayan körlük (`6:122`)."
        if (s, a) in ((2, 72), (6, 148), (9, 64), (18, 5), (24, 40), (27, 25), (47, 29), (47, 37)):
            return "Gizlilikten açığa çıkarma: örtbas edilen suçun, kalpteki gizli kinin (`47:29,37`), ağızdan çıkan ölçüsüz sözün (`18:5`) ve yerin-göğün saklılarının (`27:25`) açıkça ortaya konması."
        if (s, a) in ((3, 27), (6, 95), (7, 25), (7, 57), (10, 31), (19, 66), (20, 55), (23, 35), (27, 67), (27, 82), (30, 19), (30, 25), (34, 2), (43, 11), (46, 17), (50, 11), (50, 42), (54, 7), (57, 4), (70, 43), (71, 18)):
            return "Yeniden diriliş çıkışı (`يَوْمُ ٱلْخُرُوجِ`): ölüden diriyi ve diriden ölüyü çıkaran kozmik döngü uyarınca toprağa dönen insanın vakti geldiğinde yerden yeniden çıkarılması."
        if (s, a) in ((2, 84), (2, 85), (2, 191), (2, 217), (2, 240), (2, 246), (3, 195), (4, 75), (7, 82), (7, 88), (7, 110), (7, 123), (8, 30), (9, 13), (9, 40), (14, 13), (17, 76), (20, 57), (20, 63), (22, 40), (26, 35), (26, 167), (27, 37), (27, 56), (47, 13), (59, 2), (59, 8), (59, 11), (59, 12), (60, 1), (60, 8), (60, 9), (63, 8), (65, 1)):
            return "Sürgün ve barınma hakkı hukuku: insanların haksız yere yurtlarından sürülmesinin ağır zulüm olması (`2:217`, `22:40`, `60:9`) ve ayrılık sürecinde bile kadınların evlerinden çıkarılmaması (`2:240`, `65:1`) ilkesi."
        if (s, a) in ((2, 36), (7, 13), (7, 18), (15, 34), (15, 48), (20, 117), (26, 57), (38, 77), (51, 35)):
            return "Korunaklı mekândan çıkış veya kalıcılık: sınır ihlali veya kibir nedeniyle bahçe/mevkiden çıkarılma (`2:36`, `7:13,18`), baskıcı kentten güvene erenlerin çıkarılışı (`51:35`) ve esenlik bahçesinden hiç çıkarılmama (`15:48`)."
        if (s, a) in ((2, 167), (5, 37), (22, 22), (23, 107), (32, 20), (35, 37), (37, 64), (40, 11), (45, 35)):
            return "Çıkışı kapanan yıkım alanı: kendi tercihleriyle vardıkları yakıcı azaptan ne kadar isteseler de dışarı çıkamama hali (`وَمَا هُم بِخَٰرِجِينَ مِنْهَا` / `فَهَلْ إِلَىٰ خُرُوجٍ مِّن سَبِيلٍ`)."
        if (s, a) in ((12, 76), (16, 14), (18, 82), (35, 12)):
            return "X. bab (`ٱسْتَخْرَجَ`): denklerin içindeki gizli kâseyi (`12:76`), duvar altındaki yetim hazinesini (`18:82`) ve denizlerin dibindeki süsleri (`16:14`, `35:12`) bilgi ve emekle çekip çıkarma."
        if (s, a) in ((18, 94), (23, 72), (65, 2), (17, 80), (3, 110)):
            return "Değer ve onurlu çıkış ölçüsü: halktan istenen vergi yerine Yaradan'ın sürekli çıkardığı bereket (`خَرَاج` `23:72`), dürüstlüğe açılan ferah çıkış yolu (`مَخْرَجًا` `65:2`), onurlu giriş-çıkış (`17:80`) ve iyiliği yaygınlaştırmak için öne çıkarılmış toplum (`3:110`)."
        if (s, a) in ((20, 22), (20, 88), (27, 12), (28, 32)):
            return "Elin kusursuz beyazlıkta çıkması göstergesi (`20:22`, `27:12`, `28:32`) ve Sâmirî'nin eritilen takılardan böğüren buzağı heykeli çıkarması (`20:88`)."
        return "Toplumsal görev, sefer, ziyaret veya hakikat uğruna evden/yerinden adım atıp dışarı çıkma (`2:149-150`, `4:100`, `8:5`, `9:46-47`, `12:31`, `19:11`, `28:20-21`, `49:5`, `60:1`)."

    elif root_ar == 'ص-ل-ح':
        if lemma == 'Sa`liH2':
            return "Elçi Sâlih kıssası: Semûd toplumuna yerden beslenen uyumu hatırlatan, bozguncu dokuzlu çetenin tehdidine karşı uyarı getiren Elçi Sâlih (`7:73-77`, `11:61-89`, `26:142`, `27:45`)."
        if (s, a) in ((13, 23), (40, 8)):
            return "I. bab bireysel elverişlilik (`صَلَحَ`): atalardan, eşlerden ve soylardan kendi durumunu sağlam ve uyumlu kılanların aynı kalıcı esenlik bahçesinde buluşması."
        if (s, a) in ((2, 182), (2, 220), (2, 224), (2, 228), (4, 35), (4, 114), (4, 128), (4, 129), (8, 1), (42, 40), (49, 9), (49, 10)):
            return "Toplumsal ve ailevî uzlaşı hukuku (`إِصْلَاح / صُلْح`): vasiyet haksızlığını önleme (`2:182`), yetim işlerini iyileştirme (`2:220`), eşler arası çatlağı (`شِقَاق`) onarma (`2:228`, `4:35`, `4:128`) ve çekişen kardeşlerin arasını hakkaniyetle düzeltme (`8:1`, `49:9-10`)."
        if (s, a) in ((2, 11), (7, 56), (7, 85), (7, 142), (10, 81), (11, 88), (11, 117), (26, 152), (27, 48), (28, 19), (38, 28)):
            return "Bozulma (`فَسَاد`) karşıtı onarım ekseni: yeryüzü dengesi kurulduktan sonra bozmamak (`7:56,85`), bozgun çıkarıp «biz onarıcıyız» diyen sahteciliği reddetmek (`2:11`) ve halkı aktif onarıcı (`مُصْلِحُون`) kalan toplumların korunması (`11:117`)."
        if (s, a) in ((2, 160), (3, 89), (4, 16), (4, 146), (5, 39), (6, 48), (6, 54), (16, 119), (24, 5)):
            return "Dönüşün eylemle tamamlanması (`تَابُوا۟ وَأَصْلَحُوا۟`): yapılan yanlıştan dönmenin tek başına yetmeyip açılan hasarı ve bozulmayı fiilen onarmakla gerçeklik kazanması."
        if (s, a) in ((7, 35), (7, 170), (21, 90), (33, 71), (46, 15), (47, 2), (47, 5)):
            return "İç halin, soyun, eşin ve eylemin onarılması: Zekeriyyâ'nın eşinin doğurganlığının onarılması (`21:90`), doğru sözle amellerin işler kılınması (`33:71`), iç dünyanın dengeye kavuşturulması (`أَصْلَحَ بَالَهُمْ` `47:2,5`) ve nesil duası (`46:15`)."
        if (s, a) in ((4, 34), (7, 189), (7, 190), (11, 46), (18, 82), (66, 4), (66, 10)):
            return "Kişisel tutum ve soy ölçütü: güven bağını koruyan uyumlu kadınlar (`4:34`), sağlıklı evlat beklentisi (`7:189-190`), gerçeğe uymayan eylem (`11:46`), yetimlerin dürüst babası (`18:82`) ve güvene erenlerin yapıcı öncüleri (`66:4`, `66:10`)."
        if (s, a) in ((18, 46), (19, 76), (35, 10), (9, 102), (9, 120), (40, 40), (41, 46), (45, 15)):
            return "Kalıcı değer üreten yapıcı eylem: mal ve gösterişin aksine kalıcı iz bırakan işler (`ٱلْبَٰقِيَٰتُ ٱلصَّٰلِحَٰتُ` `18:46`, `19:76`), güzel sözü yükselten sağlam pratik (`35:10`) ve kişinin kendi lehine ürettiği onarıcı karşılık (`41:46`)."
        if (s, a) in ((2, 130), (3, 39), (3, 46), (3, 114), (4, 69), (5, 84), (6, 85), (7, 168), (7, 196), (9, 75), (12, 9), (12, 101), (16, 122), (17, 25), (21, 72), (21, 75), (21, 86), (21, 105), (24, 32), (26, 83), (27, 19), (28, 27), (29, 9), (29, 27), (37, 100), (37, 112), (63, 10), (68, 50), (72, 11)):
            return "Bozulmamış, dengeli ve güvenilir toplum halkası (`ٱلصَّٰلِحِينَ`): elçilerin içinde yer aldığı ve yeryüzüne mirasçı kılınan (`21:105`) uyumlu, dürüst ve yapıcı kullar safı."
        return "İçten güven bağı (`ءَامَنُوا۟`) ile bütünleşen yapıcı, onarıcı ve yaşama kalıcı yarar üreten eylemler (`وَعَمِلُوا۟ ٱلصَّٰلِحَٰتِ` / `عَمِلَ صَٰلِحًا`)."

    elif root_ar == 'س-ب-ل':
        if (s, a) in ((16, 15), (16, 69), (18, 61), (18, 63), (20, 53), (21, 31), (43, 10), (71, 20), (80, 20)):
            return "Doğal ve biyolojik geçiş yasası: dağların arasında açılan geçit vadiler (`فِجَاجًا سُبُلًا`), arıların boyun eğdiği üretim rotaları (`سُبُلَ رَبِّكِ`), balığın denizde yararak açtığı kaygan iz (`18:61,63`) ve insanın yaşam/doğuş kanalının kolaylaştırılması (`80:20`)."
        if (s, a) in ((2, 177), (2, 215), (4, 36), (4, 43), (8, 41), (9, 60), (17, 26), (30, 38), (59, 7)):
            return "Toplumsal yolcu dayanışması (`وَٱبْنِ ٱلسَّبِيلِ`): evinden uzak düşmüş gezgin ve göçmenin kamusal kaynak ve yardımda doğrudan hak sahibi olması ve `4:43`'teki geçici yolcu kolaylığı."
        if (s, a) in ((2, 108), (5, 12), (5, 60), (5, 77), (28, 22), (60, 1), (16, 9)):
            return "Dengeli merkez ana rota (`سَوَآءُ ٱلسَّبِيلِ` / `قَصْدُ ٱلسَّبِيلِ`): aşırılıktan ve dağılmadan korunan, doğrudan hedefe ulaştıran ölçülü güzergâh."
        if (s, a) in ((3, 75), (4, 34), (4, 90), (4, 141), (9, 5), (9, 91), (9, 93), (42, 41), (42, 42)):
            return "Hukukî yetki ve sorumluluk ölçütü (`عَلَى ... سَبِيلٌ / مِن سَبِيلٍ`): iyilik yapanlara ve barışa yönelenlere karşı zorlama veya suçlama kapısı kapalıyken yalnızca haksızlık ve saldırı üretenlerin yaptırım kapısına muhatap olması (`42:42`)."
        if (s, a) in ((2, 217), (3, 99), (4, 160), (4, 167), (7, 45), (7, 86), (8, 36), (8, 47), (9, 9), (9, 34), (11, 19), (13, 33), (14, 3), (16, 88), (16, 94), (22, 25), (27, 24), (29, 29), (29, 38), (40, 37), (43, 37), (47, 1), (47, 32), (47, 34), (58, 16), (63, 2)):
            return "Geçidin tıkanması (`صَدَّ عَن سَبِيلِ` / `تَقْطَعُونَ ٱلسَّبِيلَ`): açık ve işlek rotanın önünü keserek insanların ilerlemesini engellemek, düz hattı eğri göstermeye çalışmak (`وَيَبْغُونَهَا عِوَجًا`) ve toplumsal güvenliği bozmak."
        if (s, a) in ((4, 44), (4, 88), (4, 98), (4, 137), (4, 143), (6, 116), (6, 117), (10, 88), (14, 30), (17, 48), (17, 72), (17, 84), (22, 9), (25, 9), (25, 17), (25, 34), (25, 42), (25, 44), (31, 6), (33, 67), (38, 26), (39, 8), (40, 11), (42, 44), (42, 46), (53, 30), (68, 7)):
            return "İzi yitirme ve çıkışsızlık (`ضَلَّ سَبِيلًا` / `خُرُوجٍ مِّن سَبِيلٍ`): açık pusulayı bırakıp sapanların hiçbir kurtuluş veya tutunma rotası bulamaması; `33:67`'de ise sorumluluğu önderlere atanların `ٱلسَّبِيلَا۠` yakarışı."
        if (s, a) in ((4, 76), (5, 16), (6, 55), (6, 153), (7, 142), (7, 146), (10, 89), (12, 108), (14, 12), (16, 125), (17, 110), (25, 27), (25, 57), (29, 12), (29, 69), (31, 15), (33, 4), (40, 7), (40, 29), (40, 38), (73, 19), (76, 3), (76, 29)):
            return "Yöntem ve bilinç seçimi: tek bütün rota ile parçalayıcı yan yolların ayrışması (`6:153`), olgunluk ve sapma yollarının farkı (`7:146`), hikmetle davet yöntemi (`12:108`, `16:125`) ve esenlik yollarına (`سُبُلَ ٱلسَّلَٰمِ`) iletilme."
        if (s, a) in ((3, 97), (4, 15), (4, 22), (4, 51), (4, 115), (4, 150), (7, 148), (15, 76), (17, 32), (17, 42)):
            return "Hukukî imkân ve davranış değerlendirmesi: yolculuk gücü bulabilme (`3:97`), hâlâ görünen tarihî güzergâh (`15:76`), tutulan en kötü gidişat eleştirisi (`4:22`, `17:32`) ve yapay ara yol arayışı (`4:150`)."
        return "Engelsiz amaç ve emek koridoru (`فِى سَبِيلِ ٱللَّهِ`): kaynak paylaşımı, göç, dayanışma ve meşru savunma emeğinin çıkar gözetmeden Yaradan'ın hakkaniyet hattında buluşması."

    elif root_ar == 'ت-ب-ع':
        if (s, a) in ((2, 166), (2, 167), (14, 21), (40, 47)):
            return "Körü körüne önder takibinin çöküşü (`تَبَرَّأَ ٱلَّذِينَ ٱتُّبِعُوا۟ مِنَ ٱلَّذِينَ ٱتَّبَعُوا۟` / `تَبَعًا`): iradelerini önderlere teslim edip uydu olanların zor günde birbirini yüzüstü bırakması."
        if (s, a) in ((2, 120), (2, 145), (4, 135), (5, 48), (5, 49), (5, 77), (6, 56), (6, 150), (7, 176), (13, 37), (18, 28), (20, 16), (23, 71), (28, 50), (30, 29), (38, 26), (42, 15), (45, 18), (47, 14), (47, 16), (54, 3)):
            return "Bayağı arzu ve hevâya uyma eleştirisi: gerçek bilgi geldikten sonra kanıt ve adalet yerine keyfî tutkuların (`أَهْوَآء`) peşine takılmanın evreni ve hükmü bozacağı uyarısı (`23:71`, `38:26`)."
        if (s, a) in ((6, 116), (6, 148), (10, 36), (10, 66), (4, 157), (53, 23), (53, 28)):
            return "Zan ve varsayım takibi eleştirisi (`إِن يَتَّبِعُونَ إِلَّا ٱلظَّنَّ`): gerçeği araştırmak yerine çoğunluğun dayanaksız sanılarını ve kuruntularını izlemenin hakikat yerine geçememesi."
        if (s, a) in ((2, 170), (5, 104), (31, 21), (2, 102), (2, 168), (2, 208), (4, 83), (6, 142), (22, 3), (24, 21), (34, 20)):
            return "Atalar taklidi ve saptırıcı güç adımları: aklı çalıştırmadan önceki nesillerin alışkanlıklarını (`ءَابَآءَنَا`) yahut ayartıcı gücün adımlarını (`خُطُوَٰت`) izlemenin yıkıcı sonucu."
        if (s, a) in ((2, 262), (2, 263), (2, 178), (4, 92), (58, 4)):
            return "Toplumsal ilişkide ve arınmada takip disiplini: bağışın peşine başa kakma/eza eklememek (`2:262-263`), kısas anlaşmasını örfle izlemek (`2:178`) ve kesintisiz iki ay (`شَهْرَيْنِ مُتَتَابِعَيْنِ`) tutmak (`4:92`, `58:4`)."
        if (s, a) in ((10, 90), (15, 18), (18, 85), (18, 89), (18, 92), (20, 78), (26, 52), (26, 60), (37, 10), (44, 23), (79, 7)):
            return "Fiziksel yetişme, izleme ve ardışıklık yasası: ordunun gece yürüyenleri kovalaması (`26:52`, `10:90`), kayan alevin yakalaması (`37:10`), Zülkarneyn'in sebebi takip edip işletmesi (`18:85,89,92`) ve sarsıntıların art arda gelişi (`79:7`)."
        if (s, a) in ((7, 175), (11, 60), (11, 99), (17, 69), (23, 44), (28, 42), (77, 17)):
            return "Tarihî akıbet ve peşi sıra gelen karşılık: nimetten sıyrılanı ayartıcı gücün yakalaması (`7:175`), gerçeği örtme zincirlerinin peşine dışlanmışlığın takılması (`11:60,99`) ve hak sorucu takipçi yokluğu (`17:69`)."
        if (s, a) in ((14, 36), (20, 93), (71, 21), (2, 143), (7, 18), (17, 63), (38, 85), (15, 42)):
            return "Mesânî yönelim ayrımı: elçinin veya ayartıcı gücün çağrısına uyup izinden gidenlerle (`فَمَن تَبِعَنِى`) karşı gelip topukları üstüne geri dönenlerin ayrışması (`2:143`, `14:36`, `20:93`)."
        if (s, a) in ((39, 18), (39, 55), (6, 50), (6, 106), (7, 3), (7, 203), (10, 15), (10, 109), (33, 2), (46, 9), (47, 3), (75, 18)):
            return "Vahiy ve en güzel sözü izleme ekseni: sözleri dinleyip en güzeline uymak (`فَيَتَّبِعُونَ أَحْسَنَهُۥٓ` `39:18`), elçinin yalnızca vahyedileni takip etmesi (`6:50`) ve okuma tamamlanınca metni adım adım uygulamak (`75:18`)."
        return "İlke, elçi veya örnek çizginin izinden yürüme: hakikate, güzel örnekliğe (`12:38`, `3:31`, `9:100`) ya da sorumluluk bilinciyle açılan yola (`2:38`, `20:123`, `31:15`, `52:21`) bilinçli bağlılık."

    elif root_ar == 'أ-و-ل':
        if lemma == 'ta>owiyl':
            if (s, a) in ((3, 7), (7, 53), (10, 39)):
                return "Metin ve vaat çözümlemesi (`تَأْوِيل`): benzetmeli (`مُتَشَٰبِهَٰت`) ifadeleri bölücülük amacıyla zorlamak yerine asıl hakikatine döndürmek (`3:7`) ve uyarılan sonucun gerçekleşme anı (`7:53`, `10:39`)."
            if (s, a) in ((4, 59), (17, 35)):
                return "Hukuk ve iktisatta sonuç ölçüsü (`أَحْسَنُ تَأْوِيلًا`): anlaşmazlıkları kitap ve elçi merkezine götürmenin (`4:59`) ve ölçü-tartıda dürüstlüğün (`17:35`) doğuracağı en sağlam nihai netice."
            if (s, a) in ((18, 78), (18, 82)):
                return "Olayların görünmeyen gerçek amacı (`تَأْوِيل`): ilk bakışta anlaşılamayan üç sarsıcı eylemin arkasındaki koruyucu hikmet ve varılan asıl hedef."
            return "Rüya ve işaretlerin gerçekleşen asıl karşılığı (`تَأْوِيلُ ٱلْأَحَادِيثِ`): Yûsuf kıssasında görülen sembollerin zamanı geldiğinde tarih ve yaşam içinde birebir gerçekleşmesi (`12:100`)."
        if lemma == "'aAl":
            if (s, a) in ((2, 49), (2, 50), (3, 11), (7, 130), (7, 141), (8, 52), (8, 54), (14, 6), (28, 8), (40, 28), (40, 45), (40, 46), (54, 41)):
                return "Firavun yönetim ve iktidar çevresi (`ءَالُ فِرْعَوْنَ`): baskı rejiminin kurumsal kadrosu ile bu hanedanın içinden hakikati gizlice savunan dürüst ses (`40:28`)."
            return "Elçilik ve sorumluluk çevresi (`ءَالَ إِبْرَٰهِيمَ / ءَالَ عِمْرَٰنَ / ءَالَ لُوطٍ / ءَالَ دَاوُۥدَ`): aynı ilk kaynak ve şükür ekseninde buluşan seçkin aile, hanedan ve takipçiler."
        if lemma == '>uwliY':
            if 'FP' in f:
                return "Bekleme ve bakım hukuku (`أُو۟لَٰتُ ٱلْأَحْمَالِ`): boşanma sonrasında gebe kadınların süresinin doğumla tamamlanması ve barınma/geçim güvencesi (`65:4,6`)."
            if (s, a) in ((2, 179), (2, 197), (2, 269), (3, 7), (3, 190), (5, 100), (12, 111), (13, 19), (14, 52), (38, 29), (38, 43), (39, 9), (39, 18), (39, 21), (40, 54), (65, 10)):
                return "Öz akıl ve sağduyu sahipleri (`أُو۟لُوا۟ ٱلْأَلْبَٰبِ`): olayların dış yüzeyini yarıp çekirdeğini kavrayan, öğüt alan ve nitelikle niceliği ayırt eden (`5:100`) bilinçler."
            if (s, a) in ((3, 13), (3, 18), (4, 59), (4, 83), (8, 75), (20, 54), (20, 128), (24, 44), (33, 6), (38, 45), (46, 35), (59, 2)):
                return "Basiret, bilgi, yetki ve akrabalık sorumluları: gerçeğe tanıklık eden ilim sahipleri (`3:18`), toplumsal yönetim mercii (`4:59,83`), sebat öncüleri (`46:35`) ve rahim bağları (`8:75`, `33:6`)."
            return "Toplumsal, askerî veya fiziksel imkân sahipleri (`أُو۟لِى قُوَّةٍ / بَأْسٍ / طَوْلٍ / أَجْنِحَةٍ`): mazeret, yetki, imkân veya güç üstünlüğü taşıyan özneler (`4:95`, `9:86`, `27:33`, `35:1`)."
        if (s, a) in ((57, 3), (28, 70), (53, 25), (79, 25), (92, 13), (93, 4)):
            return "Başlangıç ve son simetrisi (`هُوَ ٱلْأَوَّلُ وَٱلْءَاخِرُ` / `ٱلْأُولَىٰ وَٱلْءَاخِرَةِ`): hem varlığın mutlak başlangıcı hem de ilk geçici aşama ile sonraki kalıcı aşamanın tek merkezde buluşması."
        if (s, a) in ((6, 94), (6, 110), (9, 13), (17, 7), (17, 51), (18, 48), (20, 21), (21, 104), (36, 79), (41, 21), (50, 15), (56, 62)):
            return "İlk yaratılış ve ilk durum yasası (`أَوَّلَ مَرَّةٍ / ٱلْخَلْقِ ٱلْأَوَّلِ / سِيرَتَهَا ٱلْأُولَىٰ`): başlangıçta yoktan var eden kudretin, aslına iade ve yeniden diriltmede hiçbir zorluk çekmemesi."
        if (s, a) in ((3, 96), (6, 14), (6, 163), (7, 143), (9, 108), (20, 65), (26, 51), (39, 12), (43, 81), (2, 41), (9, 100), (56, 13), (56, 39), (59, 2)):
            return "Tarihî ve ahlaki öncülük (`أَوَّلَ بَيْتٍ` / `أَوَّلُ ٱلْمُسْلِمِينَ` / `ٱلسَّٰبِقُونَ ٱلْأَوَّلُونَ`): insanlık için kurulan ilk merkez yapı ve hakikati ilk onaylayan yahut ilk örtmeye yeltenen tutum farkı (`2:41`)."
        return "Geçmiş nesiller, ilk sahifeler ve önceki tarihî yasalar (`ٱلْأَوَّلِينَ / ٱلْقُرُونَ ٱلْأُولَىٰ / ٱلصُّحُفِ ٱلْأُولَىٰ / سُنَّةُ ٱلْأَوَّلِينَ`): eski kayıtları «masal» sanan alay karşısında değişmez tarihî yasa (`35:43`, `20:133`, `87:18`)."

    elif root_ar == 'ق-ت-ل':
        if (s, a) in ((5, 32), (6, 151), (17, 33), (25, 68), (4, 29), (4, 92), (4, 93), (2, 72), (2, 178)):
            return "Yaşam dokunulmazlığı ve kısas hukuku: haksız yere tek bir canı öldürmenin bütün insanlığı öldürmekle eşdeğer sayılması (`5:32`), hata ile kasıtlı cinayet ayrımı (`4:92-93`) ve kısasta misilleme aşımının önlenmesi (`17:33`)."
        if (s, a) in ((6, 137), (6, 140), (17, 31), (60, 12), (81, 9)):
            return "Çocuk öldürme vahşetinin kaldırılması: geçim kaygısı veya sahte kutsallık adına evlatların ve diri gömülen kız çocuğunun yaşam hakkının savunulması (`6:151`, `17:31`, `81:9`)."
        if (s, a) in ((2, 61), (2, 87), (2, 91), (3, 21), (3, 112), (3, 181), (3, 183), (4, 155), (5, 70), (4, 157)):
            return "Elçilere ve adalet savunucularına yönelik şiddet (`بِغَيْرِ حَقٍّ`): adaleti ayakta tutmaya çağıranların öldürülmesi eleştirisi ve İsa hakkında kesin bilgiden yoksun öldürme iddiasının reddi (`4:157`)."
        if (s, a) in ((2, 190), (2, 191), (2, 193), (2, 217), (4, 75), (4, 76), (4, 89), (4, 90), (4, 91), (8, 39), (9, 5), (9, 12), (9, 13), (9, 14), (9, 29), (9, 36), (9, 123), (22, 39), (60, 8), (60, 9)):
            return "Meşru savunma, orantılılık ve barış sınırı: yalnızca saldırı başlatan ve insanları yurtlarından çıkaranlara karşı taşkınlık etmeden (`وَلَا تَعْتَدُوٓا۟` `2:190`) çarpışma izni (`22:39`), barış sunulduğunda durma (`4:90`, `60:8`) ve baskı düzeninin (`فِتْنَة`) yıkıcılığı."
        if (s, a) in ((2, 154), (3, 144), (3, 154), (3, 156), (3, 157), (3, 158), (3, 168), (3, 169), (3, 195), (4, 74), (9, 111), (22, 58), (47, 4)):
            return "Ölüm-hayat sınavı ve hakkaniyet yolunda dirilik: doğal ölüm ile öldürülme korkusuna kapılan ikiyüzlü korkaklık (`3:168`) karşısında özgürlük yolunda can verenlerin diri kalışı (`2:154`, `3:169`)."
        if (s, a) in ((2, 253), (28, 15), (49, 9)):
            return "İç çatışma hukuku (`ٱقْتَتَلَ` VIII. bab): aynı inanç veya toplum halkasının birbirine girmesi durumunda önce hakkaniyetle barıştırma, yalnız saldırıda direnene müdahale ilkesi (`49:9`)."
        if (s, a) in ((5, 33), (7, 127), (7, 141), (33, 61), (40, 25)):
            return "Sistematik kıyım ve ağır bozgun yaptırımı: Firavun'un erkek çocukları topluca kıyması (`7:141`) karşısında yeryüzünde şiddet ve bozgun yayan çetelere uygulanan caydırıcı yaptırım (`5:33`, `33:61`)."
        if (s, a) in ((9, 30), (51, 10), (63, 4), (74, 19), (74, 20), (80, 17), (85, 4)):
            return "Kınama ve saf dışı bırakma (`قُتِلَ / قَٰتَلَهُمُ`): tahminle yalan uyduranların, nankör kibrin ve hendek zalimlerinin hükümsüz ve etkisiz bırakılması."
        if (s, a) in ((2, 54), (2, 85), (4, 66), (5, 27), (5, 28), (5, 30), (5, 95), (12, 9), (12, 10), (18, 74), (20, 40), (28, 19), (28, 20), (28, 33), (29, 24), (40, 26), (40, 28)):
            return "Kıssalarda yaşam sınavı ve harem sınırı: Mûsâ ve İbrâhîm'in ölüm kıskacından kurtuluşu (`28:20`, `29:24`), Yûsuf ve Hızır kıssasındaki olaylar (`12:9`, `18:74`), Kâbil-Hâbil (`5:27-30`) ve harem avı (`5:95`)."
        return "Toplumsal savunma hazırlığı (`قِتَال` / `قَٰتِلُوا۟`): baskı ve saldırıya karşı dirayetle mevzilenme (`3:121`, `8:16,65`, `33:25`, `57:10`, `61:4`), savaştan kaçınan gevşekliğin eleştirisi (`2:246`, `4:77`, `47:20`) ve orantılı güç dengesi (`8:17`, `33:26`)."

    elif root_ar == 'م-ث-ل':
        if (s, a) in ((42, 11), (16, 60), (16, 74), (30, 27)):
            return "Mutlak eşsizlik ve yüce niteleme ilkesi: Mutlak Yaratıcının benzeri gibi dahi hiçbir varlığın olmayışı (`لَيْسَ كَمِثْلِهِۦ شَىْءٌ` `42:11`), O'nu mahluklarla kıyaslamanın reddi (`16:74`) ve O'na özgü en yüce niteleme (`ٱلْمَثَلُ ٱلْأَعْلَىٰ`)."
        if (s, a) in ((11, 27), (14, 10), (14, 11), (18, 110), (21, 3), (23, 24), (23, 33), (23, 34), (23, 47), (26, 154), (26, 186), (36, 15), (41, 6), (6, 38), (7, 194)):
            return "İnsani eşitlik ve türsel denklik: elçilerin üstünlük iddiası taşımayan ölümlü insanlar oluşu (`بَشَرٌ مِّثْلُكُمْ`), yapay ilahların aczi (`7:194`) ve yeryüzündeki canlıların insanlık gibi birer topluluk oluşu (`6:38`)."
        if (s, a) in ((2, 194), (2, 228), (2, 233), (2, 275), (4, 11), (4, 176), (5, 95), (6, 160), (10, 27), (16, 126), (22, 60), (40, 40), (42, 40), (60, 11)):
            return "Adalet, hak ve tazminatta denklik ölçüsü: kötülüğe ve saldırıya birebir misliyle karşılık sınırı (`2:194`, `42:40`), iyiliğe on katı karşılık (`6:160`), miras/aile hukuku dengesi (`4:11`, `2:228`) ve ticaret ile faizin eşit tutulamaması (`2:275`)."
        if (s, a) in ((2, 23), (10, 38), (11, 13), (17, 88), (18, 109), (52, 34), (46, 10)):
            return "Vahyin benzersizlik ölçütü (`بِسُورَةٍ مِّثْلِهِۦ` / `بِمِثْلِ هَٰذَا ٱلْقُرْءَانِ`): ilahî söz okyanusunun dengi getirilemeyen derinliği ve önceki kitapla temel tutarlılığı (`46:10`)."
        if (s, a) in ((19, 17), (21, 52), (34, 13), (13, 6), (20, 63), (20, 104), (3, 59), (43, 57), (43, 59)):
            return "Surete bürünme, heykel ve nadir örneklemeler: mesaj elçisinin insan suretine bürünmesi (`19:17`), putlaştırılan vs sanatsal heykeller (`21:52`, `34:13`), İsa'nın yaratılış örneği (`3:59`, `43:59`), ibretlik yıkım örnekleri (`13:6`) ve ideal düzen iddiası (`20:63`)."
        if (s, a) in ((17, 99), (36, 81), (65, 12), (51, 23), (38, 43), (21, 84), (56, 61), (76, 28), (47, 38), (89, 8)):
            return "Kozmik yaratma kapasitesi ve yer değiştirme: gökleri ve yeri yaratan kudretin benzerlerini yeniden yaratmaya gücü (`36:81`), yedi gök ve yedi kat yer paralelliği (`65:12`), sözün konuşma kadar gerçek oluşu (`51:23`) ve yitirilenlerin benzeriyle telafisi (`21:84`)."
        if (s, a) in ((2, 17), (2, 26), (2, 171), (2, 261), (2, 264), (2, 265), (3, 117), (6, 122), (7, 176), (10, 24), (11, 24), (13, 17), (13, 35), (14, 18), (14, 24), (14, 25), (14, 26), (16, 75), (16, 76), (16, 112), (18, 32), (18, 45), (22, 73), (24, 35), (29, 41), (29, 43), (30, 28), (39, 27), (39, 29), (47, 15), (48, 29), (57, 20), (59, 21), (62, 5), (66, 10), (66, 11), (74, 31)):
            return "Kur'anî temsil ve Mesânî pedagojisi (`ضَرَبَ ٱللَّهُ مَثَلًا`): hakikati derin ilim sahiplerinin kavraması için doğadan ve yaşamdan çizilen somut örnek tablolar (`2:261`, `14:24-26`, `24:35`, `29:43`, `59:21`)."
        return "Tarihî ve ahlaki karşılaştırma ölçütü: geçmiş kuşakların tutum ve sonuçlarından bugüne taşınan ibret örneği (`2:214`, `43:8`, `40:30-31`, `59:15`) ve tutarsız iddialarla kurulan çarpık benzetmeler (`17:48`, `25:9`, `36:78`, `43:17`)."

    elif root_ar == 'ق-ل-ب':
        if (s, a) in ((24, 37), (29, 21), (47, 19), (18, 18), (24, 44), (6, 110), (9, 48), (18, 42), (33, 66)):
            return "Evirip çevirme ve halden hale döndürme yasası: kalplerin ve bakışların altüst olduğu gün (`24:37`), gündüzle gecenin devri (`24:44`), uyuyan bedenlerin çevrilmesi (`18:18`), planların karıştırılması (`9:48`) ve varlığın kaynağa döndürülmesi (`29:21`)."
        if (s, a) in ((2, 143), (3, 127), (3, 144), (3, 149), (3, 174), (5, 21), (7, 119), (7, 125), (9, 95), (12, 62), (18, 36), (22, 11), (26, 50), (26, 227), (43, 14), (48, 12), (67, 4), (83, 31), (84, 9)):
            return "Yön değiştirme ve kaynağa dönüş (`ٱنْقِلَاب`): sınamada topukları üzere geriye dönme (`2:143`, `3:144`), yüzüstü devrilme (`22:11`), bakışın yorgun geri dönüşü (`67:4`), zalimlerin devrileceği akıbet (`26:227`) ve nimetle dönüş (`3:174`, `84:9`)."
        if (s, a) in ((2, 144), (3, 196), (16, 46), (26, 219), (40, 4)):
            return "Hareket ve yöneliş devinimi (`تَقَلُّب`): hakikati ararken yüzün göğe çevrilişi (`2:144`), içten saygıyla eğilenler arasında bulunuş (`26:219`) ve toplumların aldatıcı ekonomik/coğrafi hareketliliği (`3:196`, `40:4`)."
        if (s, a) in ((2, 7), (2, 10), (2, 74), (2, 88), (4, 155), (5, 13), (6, 25), (6, 43), (6, 46), (7, 100), (7, 101), (7, 179), (9, 87), (9, 93), (9, 125), (9, 127), (10, 74), (16, 108), (17, 46), (18, 57), (22, 46), (22, 53), (30, 59), (39, 22), (40, 35), (45, 23), (47, 16), (47, 24), (57, 16), (61, 5), (63, 3), (83, 14)):
            return "Kalbin bilişsel kapanması ve taşlaşması: düşünme ve kavrama (`فقه / عقل` `7:179`, `22:46`) işlevini kendi inadıyla körelten kalbin hastalanması, taş kesilmesi (`2:74`, `57:16`), kilitlenmesi (`47:24`) ve pas bağlaması (`83:14`)."
        if (s, a) in ((2, 97), (2, 260), (3, 103), (3, 126), (8, 2), (8, 10), (8, 11), (8, 24), (8, 63), (13, 28), (16, 106), (18, 14), (22, 32), (22, 35), (22, 54), (26, 89), (26, 194), (28, 10), (33, 4), (37, 84), (39, 23), (48, 4), (48, 18), (49, 3), (49, 7), (50, 33), (50, 37), (58, 22), (64, 11)):
            return "Sağlıklı, duyarlı ve yatışmış kalp karargâhı: vahyin indirildiği merkez (`2:97`), anmayla yatışıp sağlamlaşan (`13:28`, `8:11`), aralarında sevgi ve dirlik kurulan (`3:103`, `8:63`), yumuşayan (`39:23`) ve sağlıklı/yönelmiş öz (`قَلْبٍ سَلِيمٍ / مُّنِيبٍ`)."
        return "İçsel niyet, tereddüt ve karar sınavı (`قَلْب`): dış göğüsteki (`ٱلصُّدُور`) görünmeyen iç gerilimler (`3:154`, `9:110`, `33:10`, `40:18`), şüphe eğriliği (`3:7-8`, `9:45`, `24:50`) ve samimiyetin kalbe yazılmış ölçüsü (`2:225`, `2:283`, `33:5`)."

    elif root_ar == 'ش-ر-ك':
        if (s, a) == (4, 12):
            return "Miras hukukunda üçte bir pay üzerinde eşit hak sahibi ortaklık (`شُرَكَآءُ فِى ٱلثُّلُثِ`): kökün günlük mülkiyet ve hukukî hak paylaşımı düzlemindeki bütünüyle nötr ve teknik kullanımı."
        if (s, a) == (20, 32):
            return "Musa elçinin kardeşi Harun'u tebliğ ve yönetim sorumluluğuna ortak kılma duası (`وَأَشْرِكْهُ فِىٓ أَمْرِى`): kökün olumlu iş bölümü ve ekip dayanışması alanındaki eşsiz IV. bab istisnası."
        if (s, a) in ((30, 28), (39, 29)):
            return "Mesânî akıl kıyasları: insanın kendi mülkünde el altındakileri eşit mal ortağı kabul etmeyişiyle (`30:28`) çekişen çok başlı ortaklara bağlı kalanla tek bir bütüne (`سَلَمًا لِّرَجُلٍ`) bağlananın farkını (`39:29`) kıyaslayan temsiller."
        if (s, a) in ((17, 64), (37, 33), (43, 39)):
            return "Saptırıcı ayartının mal ve nesil süreçlerine sızarak ortaklık kurması (`17:64` `شَارِكْهُمْ` III. bab) ile yanlışta buluşanların kaçınılmaz sonuç ve azapta da eşit ortak (`37:33`, `43:39` `مُشْتَرِكُونَ` VIII. bab) kalışı."
        if (s, a) in ((18, 26), (42, 21), (6, 121), (9, 31)):
            return "Hüküm, yasa ve otorite tekeli: Yaratıcının kendi yargı kararına kimseyi ortak etmeyişi (`18:26`), ilâhî onay olmadan yeni düzen kuralı uyduran yetki ortakları (`42:21`) ve bilgin/yönetici önderlerle fısıltıcıları hüküm ortağına çevirme (`9:31`, `6:121`)."
        if (s, a) in ((6, 136), (6, 137), (6, 139), (7, 190)):
            return "Tarım ürünlerinden ve hayvanlardan pay ayırarak düzmece ortakçılar (`لِشُرَكَآئِهِمْ`) icat etme geleneği ile sağlıklı evlat nimetini bile sonradan uydurma ortaklara bağlama tutarsızlığı (`7:190`)."
        if (s, a) in ((6, 22), (6, 94), (10, 28), (10, 34), (10, 35), (16, 27), (16, 86), (18, 52), (28, 62), (28, 64), (28, 74), (30, 13), (30, 40), (34, 27), (35, 14), (41, 47), (68, 41)):
            return "Hesap günü yüzleşmesi: tek tek yalnız (`فُرَادَىٰ` `6:94`) huzura çıkıldığında, dünyada yetki ve kurtuluş umulan yapay ortakların (`شُرَكَآء`) ses vermeyişi, aciz kalışı ve tüm ortaklığı reddedişi (`10:28`, `16:86`, `35:14`)."
        if (s, a) in ((31, 13), (34, 22), (35, 40), (46, 4), (6, 163), (17, 111), (25, 2), (4, 48), (4, 116), (40, 12)):
            return "Yaratılış ve mülkte ortaklık yokluğu (`لَا شَرِيكَ لَهُۥ`, `مِن شِرْكٍ`) ile eşsiz Yaratıcıya paydaş koşmanın bağışlanmayan ağır hak ihlali ve en büyük sapma oluşu (`إِنَّ ٱلشِّرْكَ لَظُلْمٌ عَظِيمٌ` `31:13`)."
        if (s, a) in ((2, 135), (3, 67), (3, 95), (6, 79), (6, 161), (10, 105), (16, 120), (16, 123), (22, 31)):
            return "Eğrilikten yüz çevirip dosdoğru tek eksene hizalanan (`حَنِيفًا`) bütünlüklü yönelişin, çoklu yetki ortaklığı kuranlardan keskin biçimde ayrılması (`وَمَا كَانَ مِنَ ٱلْمُشْرِكِينَ`)."
        if (s, a) in ((2, 221), (24, 3), (9, 1), (9, 3), (9, 4), (9, 5), (9, 6), (9, 7), (9, 17), (9, 28), (9, 33), (9, 36), (9, 113), (33, 73), (48, 6), (60, 12), (98, 1), (98, 6)):
            return "Toplumsal sözleşme, ahit hukuku ve evlilik sınırı: çoklu odaklara paydaşlık kuranlarla evlilik ve ilke sınırı (`2:221`, `24:3`), antlaşma sadakati ve güvenlik sığınağı (`9:4-7`) ile bireysel ahit ilkeleri (`60:12`)."
        return "Mutlak Yaratıcının tek egemenliğine, duaya yahut yaşamsal sadakate başka varlıkları veya iradeleri paydaş kılma hatası (`أَشْرَكَ` IV. bab) ve bu çok odaklı yaklaşımı benimseyenler (`ٱلْمُشْرِكُونَ / شُرَكَآء`)."

    elif root_ar == 'ك-ث-ر':
        if (s, a) in ((4, 7), (4, 12), (2, 249), (7, 86), (8, 19), (8, 43), (9, 82), (38, 24)):
            return "Doğrudan azlık-çokluk ekseni (`ق-ل-ل ↔ ك-ث-ر`): miras payında az veya çok ölçüsü (`4:7,12`), disiplinli küçük topluluğun büyük kalabalığı yenmesi (`2:249`), azdan çoğalma (`7:86`) ve sayıca kabarmanın koruyamayışı (`8:19`)."
        if (s, a) in ((5, 100), (9, 25), (6, 116), (12, 103)):
            return "Sayısal kalabalık yanılsamasının yıkılması: kirli ve bozuk olanın göz alıcı çokluğu (`5:100`), Huneyn kalabalığının etkisizliği (`9:25`) ve çoğunluğa uyarak sapmanın uyarısı (`6:116`, `12:103`)."
        if (s, a) in ((57, 20), (102, 1), (108, 1)):
            return "Mal ve nesil sayısını şişirip övünme yarışının (`ٱلتَّكَاثُرُ` `57:20`, `102:1`) insanı oyalamasına karşılık, elçiye bahşedilen tükenmez iyilik ve bereket kaynağı (`ٱلْكَوْثَرَ` `108:1`)."
        if (s, a) in ((6, 128), (7, 188), (74, 6), (11, 32), (89, 12)):
            return "X. ve IV. bab eylem skalası: insan kitlelerini peşine takıp sömürme (`6:128`), hayır biriktirme (`7:188`), yaptığı iyilikten daha çok karşılık ummama (`74:6`) ve tartışmayı yahut bozgunu yaygınlaştırma (`11:32`, `89:12`)."
        if (s, a) in ((2, 245), (2, 269), (3, 41), (4, 19), (4, 100), (20, 33), (20, 34), (23, 19), (23, 21), (25, 49), (33, 35), (33, 41), (38, 51), (43, 73), (48, 19), (48, 20), (56, 32), (62, 10)):
            return "Nitelikle birleşen bereketli çokluk: katlamalı karşılık (`2:245`), derin hikmet ve hayır (`2:269`), bilinçli anış (`3:41`, `33:41`), yeryüzü genişliği (`4:100`), bol kazanımlar ve ödül yurdu ürünleri (`23:19-21`, `56:32`)."
        if (s, a) in ((4, 1), (4, 82), (18, 54), (27, 76), (58, 7), (9, 69), (17, 6), (18, 34), (34, 35)):
            return "Tek özden çoğalan insanlık (`4:1`), vahiydeki çelişki yokluğu (`4:82`), insanın tartışmacı eğilimi (`18:54`), ayrılık konularının çoğunu açıklama (`27:76`), sayısal servet böbürlenmesi (`18:34`, `34:35`) ve her topluluk sayısını kuşatan bilgi (`58:7`)."
        return "Nicelik, oran ve insan topluluklarındaki sayısal dağılım ölçütü: kalabalık kesimlerin bilgi, şükür ve doğruluk karşısındaki tutumu ile eylemlerdeki yoğunluk ve çokluk (`أَكْثَر / كَثِير`)."

    elif root_ar == 'س-و-أ':
        if (s, a) in ((6, 160), (11, 114), (13, 22), (23, 96), (27, 46), (27, 90), (28, 54), (28, 84), (40, 40), (41, 34), (42, 40)):
            return "Güzelliğin çirkinliği dönüştürme ve dengeleme kanunu (`حَسَنَة ↔ سَيِّئَة`): güzel işlerin çirkin izleri silmesi (`11:114`), saldırıyı en güzel tavırla yatıştırma (`23:96`, `41:34`) ve karşılıkta taşmayan `1:1` denklik (`6:160`, `42:40`)."
        if (s, a) in ((17, 7), (30, 10), (40, 58), (41, 46), (45, 15), (53, 31)):
            return "IV. bab fail sorumluluğu (`أَسَآءَ / ٱلْمُسِىٓءُ / ٱلسُّوٓأَىٰٓ`): kişinin yaptığı çirkinliğin kendi aleyhine dönmesi (`41:46`, `45:15`), güzellik üretenle bozgun üretenin eşit olmaması (`40:58`) ve en çirkin akıbet (`30:10`)."
        if (s, a) in ((5, 31), (7, 20), (7, 22), (7, 26), (7, 27), (20, 121)):
            return "Beden mahremiyeti ve örtünme onuru (`سَوْءَة / سَوْءَٰت`): açığa çıkan çıplaklığın giysi ve yaprakla örtülmesi (`7:22-26`, `20:121`) ve kardeşinin cansız bedenini toprakla örtmeyi öğrenme (`5:31`)."
        if (s, a) in ((20, 22), (27, 12), (28, 32)):
            return "Bedensel kusur ve hastalıktan arınma (`مِنْ غَيْرِ سُوٓءٍ`): Musa elçinin elinin hiçbir alaca leke veya bedensel bozulma taşımadan tertemiz çıkması."
        if (s, a) in ((3, 120), (5, 101), (9, 50), (11, 77), (29, 33), (67, 27)):
            return "İç daralması, keder ve yüz bozulması (`تَسُؤْ / سِىٓءَ / سِيٓـَٔتْ`): başkasının iyiliğine üzülme (`3:120`), konuk baskısı altında içi sıkılma (`11:77`) ve dehşet anında yüzlerin kararması (`67:27`)."
        if (s, a) in ((2, 271), (3, 193), (3, 195), (4, 18), (4, 31), (5, 12), (5, 65), (7, 153), (7, 168), (8, 29), (25, 70), (29, 7), (39, 35), (46, 16), (47, 2), (48, 5), (64, 9), (65, 5), (66, 8)):
            return "Çirkin izlerin örtülüp temizlenmesi (`كَفَّرَ عَنْهُمْ سَيِّـَٔاتِهِمْ`): içten paylaşım, dürüst eylem ve pişmanlık yönelişiyle geçmiş hataların ve en çirkin izlerin (`39:35`) silinip onarılması."
        if (s, a) in ((4, 17), (4, 110), (4, 123), (4, 148), (4, 149), (6, 54), (9, 102), (16, 119), (27, 11)):
            return "Düşüncesizce işlenen hatada düzeltme kapısı (`4:17`, `6:54`, `16:119`), incitici çirkin sözü yaymama (`4:148-149`), güzel ile bozuğu karıştırma (`9:102`) ve sorumluluk karşılığı (`4:123`)."
        if (s, a) in ((9, 98), (16, 60), (19, 28), (21, 74), (21, 77), (25, 40), (35, 43), (48, 6), (48, 12)):
            return "Yıkım döngüsü (`دَآئِرَةُ ٱلسَّوْءِ`), çarpık zan (`ظَنَّ ٱلسَّوْءِ`), bozulmuş topluluk (`قَوْمَ سَوْءٍ` `21:74-77`) ve hain tuzağın başka yere değil yalnızca kurucusuna dolanması (`35:43`)."
        if (s, a) in ((7, 73), (11, 64), (12, 24), (12, 25), (12, 51), (12, 53), (26, 156)):
            return "İffet sınırını aşan saldırıdan korunma (`12:24-51`), canlı güvenliğine zarar vermeme (`7:73`, `11:64`, `26:156`) ve kontrol edilmediğinde çirkinliği emreden benlik dürtüsü (`12:53`)."
        return "Yüz buruşturan bozukluk, yergi (`سَآءَ مَثَلًا` / `سَآءَ سَبِيلًا`), ağır baskı (`سُوٓءَ ٱلْعَذَابِ` `2:49`), bozuk aracılık (`4:85`) veya işlenen zarar verici fiillerin acı sonuç olarak geri dönüşü (`سَيِّـَٔات`)."

    elif root_ar == 'م-و-ت':
        if (s, a) in ((67, 2), (2, 28), (40, 11), (44, 35), (44, 56), (37, 58), (37, 59)):
            return "Ölümün yaratılmış bir sınav ve döngü evresi oluşu (`خَلَقَ ٱلْمَوْتَ وَٱلْحَيَوٰةَ` `67:2`), çift basamaklı diriliş (`2:28`, `40:11`) ve dünyadaki ilk ölümden sonra kalıcı evrede tekrar ölüm bulunmayışı (`44:56`, `37:58-59`)."
        if (s, a) in ((39, 42), (6, 61), (32, 11)):
            return "Uyku ile ölüm ikizliği (`تَوَفَّى`): canlının bilincinin uykuda geçici alıkonması, belirlenen süre dolduğunda ise bedenden tamamen geri çekilmesi (`39:42`, `6:61`, `32:11`)."
        if (s, a) in ((2, 154), (3, 169)):
            return "Hak ve adalet yolunda bedenen öldürülse bile Yaratıcı katında canlılık ve rızık boyutunu sürdürenlerin `أَمْوَٰتٌ` (gücünü yitirmiş ölüler) sayılmayışı (`بَلْ أَحْيَآءٌ`)."
        if (s, a) in ((6, 36), (6, 122), (27, 80), (30, 52), (35, 22)):
            return "Bilişsel sönme ve aydınlıkla diriliş (`أَوَمَن كَانَ مَيْتًا فَأَحْيَيْنَٰهُ` `6:122`): kavrayışını kilitleyen bilinç ölülerinin (`ٱلْمَوْتَىٰ`) işitme duyusunu yitirmesi (`27:80`, `35:22`)."
        if (s, a) in ((2, 164), (7, 57), (16, 65), (25, 49), (29, 63), (30, 19), (30, 24), (30, 50), (35, 9), (36, 33), (41, 39), (43, 11), (45, 5), (50, 11), (57, 17)):
            return "Yağmurla kurak ve ölü toprağın yeniden yeşermesi (`يُحْىِ ٱلْأَرْضَ بَعْدَ مَوْتِهَا` / `بَلْدَةً مَّيْتًا`): doğadaki büyüme döngüsü üzerinden gösterilen yeniden diriliş kanıtı."
        if (s, a) in ((2, 173), (5, 3), (6, 139), (6, 145), (16, 115), (49, 12)):
            return "Doğal biçimde ölmüş ve kanı boşalmamış hayvan etinin beslenmede yasaklanması (`ٱلْمَيْتَةُ`) ile gıybetin ölü kardeş eti yeme tiksintisiyle eş tutulması (`49:12`)."
        if (s, a) in ((3, 185), (21, 34), (21, 35), (29, 57), (31, 34), (39, 30), (62, 8), (63, 10)):
            return "Evrensel ölümlülük kanunu (`كُلُّ نَفْسٍ ذَآئِقَةُ ٱلْمَوْتِ`, `إِنَّكَ مَيِّتٌ وَإِنَّهُم مَّيِّتُونَ` `39:30`): kaçılamayan buluşma (`62:8`), zamanı bilinmeyen sınır (`31:34`) ve geçici bir eşik."
        if (s, a) in ((14, 17), (20, 74), (35, 36), (87, 13)):
            return "Ne kurtarıcı bir sonla ölen ne de işlevli ve huzurlu yaşama kavuşabilen ikili azap sıkışması (`لَا يَمُوتُ فِيهَا وَلَا يَحْيَىٰ`)."
        if (s, a) in ((2, 73), (2, 258), (2, 259), (2, 260), (3, 49), (5, 110)):
            return "Yaşam verme ve ölüm gerçekleştirme kudretinin yalnızca Evrenin Tek Yaratıcısına ait oluşu (`2:258` Nemrut kıssası, `2:259` yüz yıllık geçiş, `2:260` ve `3:49` diriltme kanıtları)."
        return "Canlılık ve işlev gücünün geri çekilerek bir evreden diğerine geçilmesi (`يُحْىِۦ وَيُمِيتُ`), yaşarken sorumluluk bilinciyle yola bağlanmak (`2:132`, `3:102`, `6:162`) ya da hakikati örterek ölüp gitmenin akıbeti."

    elif root_ar == 'ك-ب-ر':
        if (s, a) in ((2, 282), (7, 13), (9, 121), (10, 61), (18, 49), (34, 3), (54, 53)):
            return "Küçüklük-büyüklük Mesânî terazisi (`ص-غ-ر ↔ ك-ب-ر`): küçük-büyük her sözleşme, harcama ve eylemin eksiksiz kaydedilmesi ile haksızca büyüklenenin küçülüp aşağılanması (`7:13`)."
        if (s, a) in ((13, 9), (17, 111), (22, 62), (31, 30), (34, 23), (40, 12), (45, 37), (59, 23), (2, 185), (22, 37), (74, 3)):
            return "Mutlak büyüklük tekeli (`ٱلْكَبِيرُ ٱلْمُتَعَالِ`, `ٱلْمُتَكَبِّرُ`, `وَلَهُ ٱلْكِبْرِيَآءُ`): evrenin tek sahibini her eksiklikten arındırarak yüceltme (`وَكَبِّرْهُ تَكْبِيرًۢا` `17:111`)."
        if (s, a) in ((4, 172), (7, 206), (16, 49), (21, 19), (41, 38)):
            return "Yüksek görevli elçilerin ve evrendeki tüm varlıkların Yaratıcıya yönelişten asla büyüklenmeyip sürekli saygıyla eğilmeleri."
        if (s, a) in ((2, 266), (3, 40), (4, 6), (12, 78), (12, 80), (14, 39), (15, 54), (17, 23), (19, 8), (28, 23)):
            return "Yaşlanma ve olgunluk ölçüsü (`ٱلْكِبَر`): yetimlerin yetişkinlik çağına büyümesi (`4:6`), ana-babaya ihtiyarlıkta özen (`17:23`) ve ileri yaşta gelen umut (`3:40`, `14:39`)."
        if (s, a) in ((2, 34), (7, 146), (14, 21), (33, 67), (35, 43), (38, 74), (38, 75), (40, 27), (40, 35), (40, 47), (40, 56), (40, 60), (41, 15), (71, 7), (71, 22)):
            return "Haksız büyüklük kuruntusu (`ٱسْتِكْبَار` / `كِبْر`): kalplerdeki temelsiz büyüklenme hastalığı (`40:56`), algının kapanması (`7:146`), elebaşı-zayıf yüzleşmesi (`14:21`, `33:67`) ve devasa tuzak (`71:22`)."
        if (s, a) in ((6, 35), (10, 71), (17, 51), (18, 5), (42, 13), (61, 3)):
            return "Kalbe ve ölçüye ağır gelme (`كَبُرَ / كَبُرَتْ`): hak çağrının direnenlere ağır gelmesi (`10:71`, `42:13`), asılsız yakıştırmanın ağırlığı (`18:5`) ve yapmadığını söylemenin doğurduğu büyük öfke (`61:3`)."
        if (s, a) in ((12, 31), (20, 23), (21, 58), (21, 63), (24, 11), (53, 18), (74, 35), (79, 20), (79, 34), (87, 12)):
            return "Özel büyük sahne ve semboller: Yusuf'u hayranlıkla büyük bulma (`12:31`), en büyük heykel kıssası (`21:58-63`), iftiranın ana yükü (`24:11`) ve sarsıcı en büyük kanıtlar/olaylar (`20:23`, `79:20,34`)."
        if (s, a) in ((2, 45), (2, 143), (2, 217), (2, 219), (4, 2), (4, 31), (6, 19), (6, 123), (9, 3), (9, 72), (29, 45), (42, 37), (53, 32)):
            return "Derece ve ağırlık karşılaştırması: büyük sorumluluk ihlallerinden kaçınma (`4:31`, `42:37`), en büyük tanıklık (`6:19`), saygılılara kolay gelen büyük sorumluluk (`2:45`) ve en büyük anış/rıza (`9:72`, `29:45`)."
        return "Haksız üstünlük taslayarak hakikati reddetme (`ٱسْتَكْبَرَ` X. bab) yahut ölçü, ödül ve uyarı bakımından büyük ve kapsamlı olanı bildirme (`كَبِير / أَكْبَر / مُتَكَبِّر`)."

    elif root_ar == 'ش-ه-د':
        if (s, a) in ((6, 73), (9, 94), (9, 105), (12, 81), (13, 9), (23, 92), (32, 6), (39, 46), (59, 22), (62, 8), (64, 18)):
            return "Görünen ile görünmeyenin Mesânî sınırı (`عَٰلِمُ ٱلْغَيْبِ وَٱلشَّهَٰدَةِ` / `مَا شَهِدْنَآ إِلَّا بِمَا عَلِمْنَا`): insan tanıklığının ancak doğrudan hazır bulunup gözlemlediği alanda geçerli olması."
        if (s, a) in ((2, 140), (2, 282), (2, 283), (4, 6), (4, 15), (4, 33), (5, 106), (5, 107), (5, 108), (24, 4), (24, 6), (24, 8), (24, 13), (65, 2), (70, 33)):
            return "Hukukî belgeleme ve adil yargılama disiplini: borç ve mal devrinde tanık tutma (`2:282`, `4:6`, `65:2`), bilgiyi gizlememe (`2:283`), dörtlü ağır suçlama kanıtı (`24:4-8`) ve tanıklık emanetini koruma (`70:33`)."
        if (s, a) in ((2, 143), (3, 140), (4, 69), (4, 135), (5, 8), (22, 78), (39, 69), (57, 19)):
            return "Adaleti ayakta tutan yaşayan örnek tanıklar (`قَوَّٰمِينَ بِٱلْقِسْطِ شُهَدَآءَ لِلَّهِ` `4:135`, `شُهَدَآءَ عَلَى ٱلنَّاسِ` `2:143`, `22:78`): hakkı yaşamı ve duruşuyla belgeleyen bilinçli tanıklık."
        if (s, a) in ((2, 185), (11, 103), (17, 78), (19, 37), (50, 37), (85, 3), (85, 7)):
            return "Zaman, mekân ve dikkat bulunuşu: aya erişip hazır olma (`2:185`), sabah okunuşunun tanık olunan anı (`17:78`), dikkati toplamış uyanık zihin (`50:37`) ve büyük toplanma günü (`11:103`, `19:37`, `85:3`)."
        if (s, a) in ((24, 24), (36, 65), (41, 20), (41, 21), (41, 22)):
            return "Bedensel organların şahitliği: hesap anında insanın kendi dil, el, ayak, kulak, göz ve derilerinin yaptıklarına doğrudan tanık kesilmesi (`تَشْهَدُ عَلَيْهِمْ`)."
        if (s, a) in ((3, 18), (4, 166), (6, 19), (13, 43), (16, 89), (29, 52), (33, 45), (34, 47), (41, 53), (46, 8), (48, 8), (48, 28), (58, 6), (73, 15)):
            return "En büyük ve kesintisiz gözetleyici tanıklık (`أَىُّ شَىْءٍ أَكْبَرُ شَهَٰدَةً` `6:19`, `وَهُوَ عَلَىٰ كُلِّ شَىْءٍ شَهِيدٌ`): evrenin tek sahibinin ve görevli elçilerin hakikat üzerindeki tanıklığı."
        if (s, a) in ((6, 144), (6, 150), (7, 37), (7, 172), (9, 107), (18, 51), (27, 49), (37, 150), (43, 19), (59, 11), (63, 1)):
            return "Görmediği şeye tanıklık taslamanın reddi (`أَشَهِدُوا۟ خَلْقَهُمْ`, `18:51`), fıtrat sözleşmesinde özlerin kendine tanık tutulması (`7:172`) ve ikircikli sahte beyanın ifşası (`9:107`, `63:1`)."
        return "Yerinde bizzat hazır bulunma, duyularla veya basiretle gözlemleme ve bildiği gerçeği gizlemeden beyan edip tescil etme (`شَهِدَ / شَاهِد / شَهِيد / شَهَادَة`)."

    elif root_ar == 'ن-ب-أ':
        if (s, a) in ((2, 31), (2, 33), (66, 3)):
            return "İnbâ (IV. bab `أَنۢبَأَ`) ve Tenbî' (II. bab `نَبَّأَ`) kıyasları: Âdem'in varlık isimlerini aktarıp kanıtlaması (`2:31-33`) ve yüzeysel duyumla her şeyi kuşatan kesin bildirimin (`نَبَّأَنِىَ ٱلْعَلِيمُ ٱلْخَبِيرُ`) ayrımı (`66:3`)."
        if (s, a) in ((3, 79), (6, 89), (29, 27), (45, 16), (57, 26)):
            return "Kitap, hüküm ve elçilik üçlüsü (`ٱلْكِتَٰبَ وَٱلْحُكْمَ وَٱلنُّبُوَّةَ`): ilâhî haberi taşıma görevinin yazılı ilke metni ve bilgelikli yargıyla birlikte verilmesi."
        if (s, a) in ((3, 81), (4, 69), (7, 157), (7, 158), (19, 51), (19, 54), (22, 52), (33, 40)):
            return "Nebî ve Resûl tamamlayıcılığı (`نَبِىّ ↔ رَسُول`): kaynaktan büyük haberi ve vahyi alan haber elçisi ile onu topluma tebliğ eden elçilik görevinin birliği ve zincirin mühürlenişi (`33:40`)."
        if (s, a) in ((3, 44), (11, 49), (11, 100), (11, 120), (12, 102), (20, 99), (27, 22)):
            return "Gözleme kapalı geçmiş olayların ve kesin kanıtlı bilgilerin aktarılması (`أَنۢبَآءِ ٱلْغَيْبِ` / `بِنَبَإٍ يَقِينٍ` `27:22`): vahiy kanalıyla ulaştırılan ibret verici tarih gerçekleri."
        if (s, a) in ((6, 67), (10, 53), (28, 66), (38, 67), (38, 88), (49, 6), (78, 2)):
            return "Haber doğrulama etiği ve Büyük Haber: sorumluluk bilinci taşıyan toplumun haberi araştırıp netleştirmesi (`فَتَبَيَّنُوٓا۟` `49:6`), her haberin vaktinde gerçekleşmesi (`6:67`, `38:88`) ve sarsıcı Büyük Haber (`78:2`)."
        if (s, a) in ((5, 14), (5, 48), (5, 105), (6, 60), (6, 108), (6, 159), (6, 164), (9, 94), (9, 105), (10, 23), (24, 64), (29, 8), (31, 15), (31, 23), (39, 7), (41, 50), (53, 36), (58, 6), (58, 7), (62, 8), (64, 7), (75, 13)):
            return "Eylemlerin iç yüzünün hesap günü eksiksiz bildirilmesi (`فَيُنَبِّئُكُم بِمَا كُنتُمْ تَعْمَلُونَ` / `يُنَبَّؤُا۟`): insanın gizli veya açık yaptığı her davranışla yüzleştirilmesi."
        if (s, a) in ((2, 61), (2, 91), (3, 21), (3, 112), (3, 181), (4, 155), (6, 112), (25, 31)):
            return "Hakikatten haber getiren elçilere (`أَنۢبِيَآء / نَبِىّ`) karşı tarih boyunca çıkar odaklarının sergilediği haksız direnç ve saldırı sınavı."
        if (s, a) in ((33, 6), (33, 28), (33, 30), (33, 32), (33, 38), (33, 45), (33, 50), (33, 53), (33, 56), (33, 59), (49, 2), (60, 12), (65, 1), (66, 1), (66, 8), (66, 9)):
            return "Toplumsal sözleşme, aile hukuku ve haber elçisiyle (`ٱلنَّبِىّ`) sağlıklı iletişim düzenini kuran kurallar."
        return "Yüksek kaynaktan alıcıya taşınan önemli hakikat haberi (`نَبَأ`), derinlemesine kesin bilgi bildirme (`نَبَّأَ`) ya da ilâhî mesajı insanlığa ulaştıran haber elçisi (`نَبِىّ`)."

    elif root_ar == 'ب-ع-ض':
        if (s, a) == (2, 26):
            return "En küçük canlı parça örneği (`بَعُوضَةً فَمَا فَوْقَهَا`): büyüklüğü değil hakikat öğretimini esas alan sivrisinek temsili."
        if (s, a) in ((2, 76), (2, 85), (4, 150), (5, 49), (11, 12)):
            return "Seçmeci parçacılığın reddi (`بِبَعْضِ ٱلْكِتَٰبِ`): bütüncül ilâhî ilkelerden yalnızca işine gelen kısmı alıp öteki kısmı örtme veya elçiler arasında ayrım yapma tutarsızlığı."
        if (s, a) in ((3, 195), (4, 25), (5, 51), (6, 129), (8, 72), (8, 73), (8, 75), (9, 67), (9, 71), (33, 6), (45, 19)):
            return "Aynı öz ve değer dokusundan doğan karşılıklı bağ (`بَعْضُكُم مِّنۢ بَعْضٍ` `3:195`, `بَعْضُهُمْ أَوْلِيَآءُ بَعْضٍ` `9:71`): insanî eşitlik, dayanışma ağı veya yanlışta birbirine benzeyen kesimler."
        if (s, a) in ((2, 36), (6, 112), (6, 128), (7, 24), (20, 123), (29, 25), (34, 31), (34, 42), (37, 27), (37, 50), (43, 67), (49, 12), (52, 25), (68, 30)):
            return "Karşılıklı sürtüşme, gıybet yasağı ve hesap günü yüzleşmesi (`بَعْضُكُمْ لِبَعْضٍ عَدُوٌّ`, `وَلَا يَغْتَب بَّعْضُكُم بَعْضًا` `49:12`): ilkeyi yitiren yakınların birbirine düşman kesilmesi (`43:67`)."
        if (s, a) in ((2, 251), (2, 253), (4, 32), (4, 34), (6, 165), (13, 4), (16, 71), (17, 21), (17, 55), (22, 40), (25, 20), (43, 32)):
            return "Toplumsal denge ve sorumluluk basamakları (`دَفْعُ ٱللَّهِ ٱلنَّاسَ بَعْضَهُم بِبَعْضٍ` `2:251`, `دَرَجَٰتٍ` `6:165`, `43:32`): kibir için değil iş bölümü ve dayanışma sınavı için verilen farklı yetenek ve imkânlar."
        if (s, a) in ((2, 259), (10, 46), (13, 40), (18, 19), (23, 113), (27, 72), (30, 41), (40, 77), (66, 3), (69, 44)):
            return "Zaman, bilgi ve sonuç kesiti: günün bir bölümü (`يَوْمًا أَوْ بَعْضَ يَوْمٍ` `18:19`), bilginin bir kısmını nezaketle paylaşma (`66:3`) ve yapılanların yalnızca bir kısmının uyandırıcı sonucu (`30:41`)."
        if (s, a) in ((3, 34), (3, 64), (17, 88), (23, 91), (24, 40)):
            return "Kozmik teklik ve katman bütünlüğü: birden fazla egemen olsaydı bir kısmının diğerinin üstüne çıkma çabası (`23:91`), katmanlı karanlıklar (`24:40`) ve tek insanî soy çizgisi (`3:34`)."
        return "Bütünden ayrılan kısmi kesit veya aynı bütünü paylaşanların karşılıklı etkileşimi (`بَعْض`): parça-bütün ölçütü ve `birbirine / birbirinden` ilişkisi."

    elif root_ar == 'ن-ص-ر':
        if (s, a) == (3, 160):
            return "Mutlak destek ve yardımsız kalış dengesi (`نَصْر ↔ خَذْل`): Evrenin Sahibi yardım ederse yenilmezlik, yüzüstü bırakırsa (`يَخْذُلْكُمْ`) başka hiçbir destekçinin güç yetiremeyeceği yasası."
        if (s, a) in ((3, 123), (8, 10), (8, 26), (8, 62), (9, 25), (9, 40), (22, 39), (22, 40), (30, 5), (30, 47), (47, 7), (48, 3), (57, 25), (61, 13), (110, 1)):
            return "Aktif ilâhî destek ve açılım kanunu (`إِن تَنصُرُوا۟ ٱللَّهَ يَنصُرْكُمْ` `47:7`, `وَمَا ٱلنَّصْرُ إِلَّا مِنْ عِندِ ٱللَّهِ` `8:10`): sayısal kalabalığa değil haklı davaya omuz verene güç ve zafer ulaştırılması."
        if (s, a) in ((17, 33), (18, 43), (26, 227), (28, 81), (42, 39), (42, 41), (51, 45), (54, 10), (54, 44), (55, 35)):
            return "Zulüm sonrası meşru savunma hakkı ve kibirli direnişin kırılışı (`وَلَمَنِ ٱنتَصَرَ بَعْدَ ظُلْمِهِ` `42:41`, `فَٱنتَصِرْ` `54:10`): mazlumun hakkını savunması meşru iken zalim güçlerin kendini kurtaramaması (`55:35`)."
        if (s, a) in ((3, 52), (7, 157), (8, 72), (8, 74), (9, 100), (9, 117), (61, 14)):
            return "Dayanışma öncüleri (`أَنصَارُ ٱللَّهِ`, `ٱلْأَنصَار`) ve ahitli yardım hukuku (`8:72` `ٱسْتَنصَرُوكُمْ`): zorda kalanlara kucak açıp hak çağrıyı omuzlayan topluluk bilinci."
        if (s, a) in ((2, 62), (2, 111), (2, 113), (2, 120), (2, 135), (2, 140), (3, 67), (5, 14), (5, 18), (5, 51), (5, 69), (5, 82), (9, 30), (22, 17)):
            return "Tarihsel Nasârâ (`نَصَٰرَىٰ`) topluluğu bağlamı: samimi iyilik ve tevhit çizgisini koruyanların hakkı teslim edilirken (`2:62`, `5:69`) mezhepçilik ve tekelleşme iddialarının (`2:111`, `3:67`, `9:30`) düzeltilmesi."
        if (s, a) in ((2, 48), (2, 86), (2, 107), (2, 123), (4, 75), (4, 89), (4, 123), (4, 145), (4, 173), (7, 192), (7, 197), (11, 113), (21, 39), (28, 41), (36, 74), (37, 25), (41, 16), (42, 46), (44, 41), (52, 46), (59, 11), (59, 12), (86, 10)):
            return "Sahte destek odaklarının kriz ve hesap anında çöküşü (`وَلَا هُمْ يُنصَرُونَ`, `مِن وَلِىٍّ وَلَا نَصِيرٍ`, `مَا لَكُمْ لَا تَنَاصَرُونَ` `37:25`): Evrenin Sahibinden başka dayanılan hiçbir odağın yardım yetiştiremeyişi."
        if (s, a) in ((8, 40), (17, 80), (22, 78), (28, 18), (37, 116), (37, 172)):
            return "En güvenilir destekçi (`نِعْمَ ٱلنَّصِيرُ` `8:40`, `22:78`), destekleyici yetki talebi (`سُلْطَٰنًا نَّصِيرًا` `17:80`), sokaktaki yardım çağrısı (`28:18`) ve elçilerin galibiyeti (`37:172`)."
        return "Zorda kalana veya haklı tarafa dışarıdan hayır, güç ve koruma ulaştırarak ayağa kaldırma (`نَصْر / نَصَرَ`), ya da haksızlığa karşı destekten yoksun kalma."

    elif root_ar == 'ص-د-ق':
        if (s, a) == (4, 4):
            return "Evlilik sözleşmesinin kadına bağlanan sağlam hukuki ve maddî güvencesi (`صَدُقَٰتِهِنَّ نِحْلَةً`): heves veya lütuf değil gönülden ve eksiksiz teslim edilen temel hak."
        if (s, a) == (34, 20):
            return "İblis'in insanlar hakkındaki olumsuz öngörüsünün fiilen doğru çıkması (`صَدَّقَ عَلَيْهِمْ إِبْلِيسُ ظَنَّهُۥ`): uyarılara kulak kapatıldığında kurgunun gerçekleşmesi."
        if (s, a) in ((2, 196), (2, 263), (2, 264), (2, 271), (2, 276), (4, 114), (9, 58), (9, 60), (9, 79), (9, 103), (9, 104), (58, 12), (58, 13)):
            return "İçtenliği fiilen belgeleyen gönüllü paylaşım (`صَدَقَة / صَدَقَات`): başa kakma ve incitme ile boşa çıkarılmadığında arındıran (`9:103`), sömürücü faiz erirken toplumsal bereketi büyüten (`2:276`) katkı."
        if (s, a) in ((2, 280), (4, 92), (5, 45), (9, 75), (12, 88), (33, 35), (57, 18), (63, 10)):
            return "Maldan paylaşıp alacak veya kısas hakkından karşılıksız feragat etme (`تَصَدَّقَ / مُتَصَدِّق / مُصَّدِّق`): borçluyu sıkıştırmamak (`2:280`), haklı tazminat veya kısası bağışlamak (`4:92`, `5:45`) ve sürekli bağışla özünü kanıtlamak (`57:18`)."
        if (s, a) in ((2, 41), (2, 89), (2, 91), (2, 97), (2, 101), (3, 3), (3, 39), (3, 50), (3, 81), (4, 47), (5, 46), (5, 48), (6, 92), (10, 37), (12, 111), (35, 31), (46, 12), (46, 30), (61, 6)):
            return "Önceki hakikat birikimiyle tam örtüşme ve onu geçerli kılıp denetleme (`مُصَدِّقًا لِّمَا بَيْنَ يَدَيْهِ`, `تَصْدِيقَ`): yeni mesajın geçmişteki sağlam temeli yok saymak yerine doğrulayıp koruması (`5:48`)."
        if (s, a) in ((4, 69), (5, 75), (12, 46), (19, 41), (19, 56), (24, 61), (26, 101), (57, 19)):
            return "Sözü ile eylemi arasında çatlak bırakmayan yüksek tutarlılık makamı (`صِدِّيق / صِدِّيقَة`) ve maskesiz yakın dost (`صَدِيق`): Yusuf, İbrahim, İdris ve Meryem'in kırılmaz dürüstlüğü ile kriz anında aranan gerçek dostluk (`26:101`)."
        if (s, a) in ((3, 17), (5, 119), (6, 115), (9, 119), (10, 2), (10, 93), (17, 80), (19, 50), (26, 84), (33, 8), (33, 24), (46, 16), (49, 15), (54, 55), (59, 8)):
            return "Eğriliksiz sağlam duruş, onurlu iz ve güvenilir yerleşim (`صِدْق`): giriş ve çıkış doğruluğu (`17:80`), gelecek nesillerde saygın anılış (`19:50`, `26:84`), sarsılmaz huzur makamı (`54:55`) ve sözünün arkasında duranların tutarlılığı."
        if (s, a) in ((2, 177), (3, 95), (3, 152), (4, 87), (4, 122), (5, 113), (6, 146), (9, 43), (12, 26), (12, 27), (12, 51), (12, 82), (15, 64), (19, 54), (21, 9), (24, 6), (24, 9), (27, 27), (27, 49), (28, 34), (29, 3), (33, 22), (33, 23), (36, 52), (37, 37), (37, 52), (37, 105), (39, 32), (39, 33), (39, 74), (47, 21), (48, 27), (51, 5), (56, 57), (66, 12), (70, 26), (75, 31), (92, 6)):
            return "Söz, ahit, rüya ve haberin nesnel olayla birebir gerçekleşip onaylanması (`صَدَقَ / صَدَّقَ / أَصْدَقُ`): verilen vaadin vuku bulması (`3:152`, `48:27`), adlî delil ve tanıklık (`12:26-27`, `24:6-9`), ahdi fiilen tutma (`33:23`) ve hakikati yalanlamadan onaylama (`39:33`, `92:6`)."
        return "Epistemik kanıt ve tutarlılık meydan okuması (`إِن كُنتُمْ صَٰدِقِينَ` / `صَادِقًا`): boş ve dayanaksız iddiaya karşılık ölçülebilir delil ve gerçekçi tutum talep edilmesi (`ص-د-ق` ↔ `ك-ذ-ب`)."

    elif root_ar == 'غ-ي-ر':
        if (s, a) in ((8, 53), (13, 11)):
            return "Tarihsel ve toplumsal değişimin temel yasası (`لَا يُغَيِّرُ مَا بِقَوْمٍ حَتَّىٰ يُغَيِّرُوا۟ مَا بِأَنفُسِهِمْ` / `مُغَيِّرًا`): Yaratıcı'nın verdiği nimeti durduk yere bozmayışı, değişimin ancak insanın kendi iç tutumunu değiştirmesiyle tetiklenmesi."
        if (s, a) == (4, 119):
            return "Fıtratın ve yaratılış dengesinin kasıtlı tahrifi (`فَلَيُغَيِّرُنَّ خَلْقَ ٱللَّهِ`): ayartıcının yönlendirmesiyle canlı doğasının ve öz ayarlarının saptırılması."
        if (s, a) == (47, 15):
            return "Bozulma ve ekşimeyi dışlayan dirilik (`غَيْرِ ءَاسِنٍ`, `لَمْ يَتَغَيَّرْ طَعْمُهُۥ`): kokuşan suya ve ekşiyen süte karşılık ebedî yurtta tadı ve saflığı asla başkalaşmayan akış."
        if (s, a) == (100, 3):
            return "Şafak vakti ortamı altüst eden baskın ivmesi (`فَٱلْمُغِيرَٰتِ صُبْحًا`): sabah aydınlığında hızla atılıp sükûnet hâlini bir anda değiştiren koşucu atlar (`غ-ي-ر` / `غ-و-ر` kök kesişimi)."
        if (s, a) in ((1, 7), (3, 83), (3, 85), (4, 82), (4, 115), (6, 14), (6, 40), (6, 46), (6, 114), (6, 164), (7, 59), (7, 65), (7, 73), (7, 85), (7, 140), (11, 50), (11, 61), (11, 84), (16, 52), (22, 31), (23, 23), (23, 32), (26, 29), (28, 38), (28, 71), (28, 72), (35, 3), (39, 64), (52, 43)):
            return "Tevhit ve yol ayrımında keskin sınır çizimi (`مِنْ إِلَٰهٍ غَيْرُهُۥ`, `أَغَيْرَ ٱللَّهِ`, `غَيْرِ ٱلْمَغْضُوبِ`): tek gerçek otorite ve teslimiyet nizamı dışındaki tüm sahte odakların net sınırla dışlanması."
        if (s, a) in ((2, 61), (3, 21), (3, 112), (3, 154), (3, 181), (4, 155), (5, 32), (5, 77), (6, 93), (7, 33), (7, 146), (10, 23), (18, 74), (22, 40), (28, 39), (33, 58), (40, 75), (41, 15), (42, 42), (46, 20)):
            return "Hak ve adalet ölçüsünü çiğneyen sınır taşımı (`بِغَيْرِ ٱلْحَقِّ`, `غَيْرَ ٱلْحَقِّ`, `بِغَيْرِ نَفْسٍ`): hiçbir meşru gerekçe ve haklılık bulunmadan cana kıymak, yurtlardan sürmek veya böbürlenmek."
        if (s, a) in ((2, 212), (3, 27), (3, 37), (11, 108), (11, 109), (24, 38), (38, 39), (39, 10), (40, 40), (41, 8), (68, 3), (84, 25), (95, 6)):
            return "Ölçü ve kesintiyi aşan sınırsız karşılık (`بِغَيْرِ حِسَابٍ`, `غَيْرُ مَمْنُونٍ`, `غَيْرَ مَجْذُوذٍ`): insanın dar hesaplarını ve başa kakma mantığını aşan eksiksiz ve kalıcı ikram."
        if (s, a) in ((6, 100), (6, 108), (6, 119), (6, 140), (6, 144), (16, 25), (22, 3), (22, 8), (28, 50), (30, 29), (31, 6), (31, 20), (40, 35), (40, 56), (48, 25)):
            return "Bilgi ve geçerli kanıt sınırı dışında kalan kör tutum (`بِغَيْرِ عِلْمٍ / سُلْطَٰنٍ / هُدًى`): sağlam delil ve ilim olmaksızın arzu peşinde hüküm kurmanın uyarısı."
        if (s, a) in ((2, 59), (4, 56), (4, 81), (7, 162), (9, 39), (10, 15), (11, 57), (14, 48), (17, 73), (35, 37), (47, 38)):
            return "Yerini başka bir şeyle doldurma ve kapsam başkalaşımı (`ب-د-ل` + `غ-ي-ر`): emri başka sözle çarpıtma (`2:59`), görevden kaçanın yerine yeni toplum getirme (`47:38`) veya yerkürenin başka hâle tebdili (`14:48`)."
        if (s, a) in ((6, 99), (6, 141), (13, 2), (13, 4), (14, 37), (20, 22), (22, 5), (27, 12), (28, 32), (31, 10), (39, 28), (52, 35)):
            return "Yaratılış ve metin bütünlüğünde çeşitlilik ile kusursuzluk (`بِغَيْرِ عَمَدٍ`, `مُشْتَبِهًا وَغَيْرَ مُتَشَٰبِهٍ`, `مِنْ غَيْرِ سُوٓءٍ`, `غَيْرَ ذِى عِوَجٍ`): direksiz gökler, tek sudan çıkan farklı tatlar ve çarpıklıksız düzen."
        if (s, a) in ((2, 173), (2, 230), (2, 240), (4, 12), (4, 24), (4, 25), (4, 46), (4, 95), (4, 140), (5, 1), (5, 3), (5, 5), (5, 106), (6, 68), (6, 145), (16, 115), (23, 6), (24, 27), (24, 29), (24, 31), (24, 60), (33, 53), (70, 30)):
            return "Toplumsal hukuk, mahremiyet ve zarûret sınırları (`غَيْرَ بَاغٍ وَلَا عَادٍ`, `غَيْرَ مُضَآرٍّ`, `غَيْرُ أُو۟لِى ٱلضَّرَرِ`, `لِغَيْرِ ٱللَّهِ`, `غَيْرَ بُيُوتِكُمْ`): meşru hakları koruyup taşkınlığı ve zararı dışlayan düzen."
        return "Özelliğin veya varlığın sınır dışına çıkarılması (`غَيْرُ مُعْجِزِى / صَٰلِحٍ / مَكْذُوبٍ / مَرْدُودٍ / يَسِيرٍ`): bir durumun aksini, eksik olmayan yanını veya hariç tutulan sınırını kesinleştirme."

    elif root_ar == 'و-ع-د':
        if (s, a) == (2, 268):
            return "Çift kutuplu gelecek projeksiyonu (`ٱلشَّيْطَٰنُ يَعِدُكُمُ ٱلْفَقْرَ ... وَٱللَّهُ يَعِدُكُم مَّغْفِرَةً مِّنْهُ وَفَضْلًا`): saptırıcı yıkıcı gücün yoksulluk korkusuyla cimriliğe itmesine karşılık Yaratıcı'nın bağışlama ve bolluk bildirmesi."
        if (s, a) in ((4, 120), (14, 22), (17, 64), (35, 40)):
            return "Gerçekleşen ilâhî söz ile aldatıcı kuruntu ayrımı (`وَعَدَ ٱللَّهُ حَقًّا ↔ وَمَا يَعِدُهُمُ ... إِلَّا غُرُورًا`): saptırıcı gücün ve zalimlerin sözünün asılsız aldatmaca ve yüzüstü bırakma olarak çıkması."
        if (s, a) in ((3, 9), (3, 194), (13, 31), (14, 47), (22, 47), (30, 6), (39, 20)):
            return "Belirlenmiş vadeden şaşmama yasası (`لَا يُخْلِفُ ٱلْمِيعَادَ` / `لَا يُخْلِفُ ٱللَّهُ وَعْدَهُۥ`): insanî oyalamaların aksine Evrenin Sahibi'nin koyduğu tarihî ve ahiretlik buluşma vaktinin asla ertelenmemesi."
        if (s, a) in ((9, 77), (20, 86), (20, 87), (33, 12)):
            return "İnsanların sözden cayma sınavı (`بِمَآ أَخْلَفُوا۟ ٱللَّهَ مَا وَعَدُوهُ`, `أَفَأَخْلَفْتُم مَّوْعِدِى`, `مَّا وَعَدَنَا ... إِلَّا غُرُورًا`): kalbinde hastalık olanların ve sebat göstermeyip acele edenlerin verdikleri taahhütten dönmesi."
        if (s, a) in ((2, 51), (7, 142), (20, 80)):
            return "Musa elçinin Tur buluşması (`وَٰعَدْنَا` III. bab): kırk gecelik vahiy buluşmasının karşılıklı tayin edilen vakit ve mekânda gerçekleşmesi (Rasm iskeleti `وعدنا` iki okumaya da açıktır)."
        if (s, a) == (2, 235):
            return "Bekleme süresi içindeki evlilik hukuku (`لَا تُوَاعِدُوهُنَّ سِرًّا` III. bab): iddet sürecindeki kadınlarla gizli buluşma ve nikâh sözü bağlamanın yasaklanması."
        if (s, a) == (7, 86):
            return "Yol kesip gözdağı verme yasağı (`تُوعِدُونَ` IV. bab): halkın önüne geçip hak yoldan alıkoymak amacıyla tehdit savurma eylemi (Rasm iskeleti `توعدون`)."
        if (s, a) == (8, 42):
            return "Tarihî akışın insan planını aşması (`وَلَوْ تَوَاعَدتُّمْ لَٱخْتَلَفْتُمْ فِى ٱلْمِيعَٰدِ` VI. bab): tarafların kendi aralarında kararlaştıramayacağı buluşmayı hakikatin belirginleşmesi için ilâhî düzenin kurması."
        if (s, a) in ((9, 114), (19, 54), (20, 58), (20, 59), (28, 13)):
            return "İnsanî buluşma, ahit sadakati ve annenin kucağına dönüş (`مَوْعِدَة`, `صَادِقَ ٱلْوَعْدِ`, `مَوْعِدُكُمْ يَوْمُ ٱلزِّينَةِ`): İbrahim'in verdiği söz, İsmail'in sözünde duruşu, Musa ile Firavun buluşması ve annesine geri veriliş."
        if (s, a) in ((3, 152), (9, 111), (16, 38), (17, 5), (17, 7), (17, 108), (18, 21), (18, 98), (21, 9), (21, 104), (24, 55), (33, 22), (48, 20), (73, 18)):
            return "Tarihte ve gelecekte fiilen gerçekleşen kesin söz (`صَدَقَكُمُ وَعْدَهُۥ` / `وَعْدًا مَّفْعُولًا` / `وَعْدًا عَلَيْهِ حَقًّا`): güvene erenlere güç, tarihsel zafer ve dönüşüm süreçlerinin vaktinde vuku bulması."
        if (s, a) in ((4, 95), (4, 122), (5, 9), (9, 72), (13, 35), (19, 61), (21, 103), (25, 15), (25, 16), (28, 61), (31, 9), (40, 8), (41, 30), (46, 16), (47, 15), (48, 29), (50, 32), (57, 10)):
            return "Sorumluluk bilinciyle yaşayanlara bildirilen esenlik ve ödül vaadi (`وَعَدَ ٱللَّهُ ٱلْحُسْنَىٰ` / `وُعِدَ ٱلْمُتَّقُونَ`): güzel ve yararlı eylemin kaçınılmaz sonucu olan huzur bahçesi ve bağışlanma."
        if (s, a) in ((7, 70), (7, 77), (10, 48), (11, 32), (11, 65), (18, 58), (18, 59), (20, 97), (21, 38), (23, 35), (23, 36), (23, 83), (27, 68), (27, 71), (34, 29), (34, 30), (36, 48), (46, 17), (46, 22), (67, 25), (72, 25)):
            return "Alaycı tarih meydan okuması ve kaçınılmaz vade (`مَتَىٰ هَٰذَا ٱلْوَعْدُ` / `مِّيعَادُ يَوْمٍ` / `مَّوْعِدٌ`): diriliş ve hesap uyarısını masal sayıp acele ettirenlere vaktin şaşmayacağının bildirilmesi."
        if (s, a) in ((9, 68), (10, 46), (11, 17), (11, 81), (13, 40), (14, 14), (15, 43), (19, 75), (20, 113), (22, 72), (26, 206), (36, 63), (40, 28), (40, 77), (43, 42), (50, 14), (50, 20), (50, 28), (50, 45), (54, 46)):
            return "Yaptırım ve azap uyarısı (`وَعِيد` / `فَٱلنَّارُ مَوْعِدُهُۥ` / `يُوعَدُونَ`): zulümde ısrar edenler için önceden açıkça ilan edilmiş kaçınılmaz buluşma ve karşılık günü."
        if (s, a) in ((7, 44), (36, 52), (38, 53), (39, 74)):
            return "Hesap ve diriliş anında verilen sözün birebir doğrulanışı (`وَجَدْنَا مَا وَعَدَنَا رَبُّنَا حَقًّا` / `هَٰذَا مَا وَعَدَ ٱلرَّحْمَٰنُ`): dünyada bildirilen her sonucun göz önünde gerçeğe dönüşmesi."
        return "Geleceğe dönük kesin gerçeklik bildirimi ve şaşmaz buluşma günü (`إِنَّ وَعْدَ ٱللَّهِ حَقٌّ` / `يَوْمُ ٱلْمَوْعُودِ`): verilen sözün hem ödül hem yaptırım yönünden mutlaka gerçekleşeceği yasası."

    elif root_ar == 'ب-ص-ر':
        if (s, a) in ((6, 50), (6, 104), (10, 43), (11, 24), (13, 16), (22, 46), (35, 19), (40, 58)):
            return "Körlük ile seçik görme arasındaki Mesânî ekseni (`ٱلْأَعْمَىٰ ↔ ٱلْبَصِيرُ` / `لَا تَعْمَى ٱلْأَبْصَٰرُ وَلَٰكِن تَعْمَى ٱلْقُلُوبُ`): yalnızca fiziksel göz değil, bilincin gerçeği seçme sorumluluğu (`6:104`)."
        if (s, a) in ((2, 7), (2, 17), (2, 20), (5, 71), (6, 46), (6, 110), (7, 179), (7, 195), (7, 198), (11, 20), (16, 108), (36, 9), (36, 66), (45, 23), (46, 26), (47, 23)):
            return "Duyusal alımın bilinç kilidiyle işlevsizleşmesi (`غِشَٰوَة` / `خَتَمَ` / `أَعْيُنٌ لَّا يُبْصِرُونَ بِهَا` / `يَنظُرُونَ إِلَيْكَ وَهُمْ لَا يُبْصِرُونَ`): bakmak (`ن-ظ-ر`) ile seçik kavramak (`ب-ص-ر`) arasındaki keskin Furûk."
        if (s, a) in ((16, 78), (17, 36), (23, 78), (32, 9), (67, 23)):
            return "Üçlü epistemik donanım ve hesap sorumluluğu (`ٱلسَّمْعَ وَٱلْأَبْصَٰرَ وَٱلْأَفْـِٔدَةَ`): kulak, göz ve kavrayan gönlün insana şükür ve doğruluk sorumluluğu yüklemesi (`17:36`)."
        if (s, a) in ((10, 67), (17, 12), (27, 86), (40, 61)):
            return "Gece-gündüz kozmik düzeninde seçikleştirme yasası (`ٱلنَّهَارَ مُبْصِرًا` / `ءَايَةَ ٱلنَّهَارِ مُبْصِرَةً`): gündüzün her şeyi seçik görülebilir kılışı."
        if (s, a) in ((7, 203), (12, 108), (17, 59), (17, 102), (27, 13), (28, 43), (45, 20), (50, 8)):
            return "Aydınlatıcı kanıt belgeleri (`بَصَآئِرُ` / `مُبْصِرَةً` / `تَبْصِرَةً` / `عَلَىٰ بَصِيرَةٍ`): vahyin ve doğadaki kanıtların insanı kör taklitten kurtarıp açık görgülü bilince çağırması."
        if (s, a) in ((20, 96), (28, 11)):
            return "I. babın ince fark ediş ve gözetleyiş kullanımı (`بَصُرْتُ بِهِ` / `فَبَصُرَتْ بِهِۦ`): başkasının seçemediği ayrıntıyı `بِـ` harf-i cerriyle yakalama."
        if (s, a) in ((7, 201), (29, 38), (75, 14)):
            return "Öz-farkındalık ve zihinsel uyanış (`فَإِذَا هُم مُّبْصِرُونَ`, `مُسْتَبْصِرِينَ`, `عَلَىٰ نَفْسِهِۦ بَصِيرَةٌ`): kişinin kendi gerçeğinin ve seçiminin farkında olması."
        if (s, a) in ((3, 13), (24, 44), (38, 45), (59, 2), (67, 3), (67, 4)):
            return "Derin gözlem ve ibret çıkaran seçik görüş sahipleri (`أُو۟لِى ٱلْأَبْصَٰرِ` / `فَٱرْجِعِ ٱلْبَصَرَ`): olayları ve kozmik kusursuzluğu dikkatle inceleyen akıl."
        if (s, a) in ((12, 93), (12, 96), (15, 15), (16, 77), (20, 125), (24, 30), (24, 31), (53, 17), (54, 50), (68, 51), (76, 2)):
            return "İnsanî görme duyusunun sınırı, iffeti ve keskinliği (`كَلَمْحِ ٱلْبَصَرِ`, `يَغُضُّوا۟ مِنْ أَبْصَٰرِهِمْ`, `مَا زَاغَ ٱلْبَصَرُ`, `فَٱرْتَدَّ بَصِيرًا`)."
        if (s, a) in ((7, 47), (14, 42), (19, 38), (21, 97), (24, 37), (32, 12), (33, 10), (37, 175), (37, 179), (38, 63), (41, 20), (41, 22), (50, 22), (54, 7), (68, 5), (68, 43), (70, 11), (70, 44), (75, 7), (79, 9)):
            return "Kriz, ölüm ve hesap anında perdenin kalkışı (`فَبَصَرُكَ ٱلْيَوْمَ حَدِيدٌ`, `تَشْخَصُ فِيهِ ٱلْأَبْصَٰرُ`, `يُبَصَّرُونَهُمْ`): dünyada örten perdeler kalktığında gözlerin gerçeğe dikilmesi."
        if (s, a) in ((21, 3), (27, 54), (28, 72), (32, 27), (43, 51), (51, 21), (52, 15), (56, 85), (69, 38), (69, 39)):
            return "Görünen ile görünmeyenin sorgulanması (`أَفَلَا تُبْصِرُونَ`, `وَأَنتُمْ تُبْصِرُونَ`, `بِمَا تُبْصِرُونَ وَمَا لَا تُبْصِرُونَ`): göz önünde duran gerçeklere karşı duyarsızlığın eleştirisi."
        if (s, a) in ((6, 103), (18, 26), (42, 11)):
            return "Mutlak gözetleyici kudretin eşsizliği (`لَّا تُدْرِكُهُ ٱلْأَبْصَٰرُ وَهُوَ يُدْرِكُ ٱلْأَبْصَٰرَ`, `أَبْصِرْ بِهِۦ`, `ٱلسَّمِيعُ ٱلْبَصِيرُ`): beşerî gözlerin kuşatamadığı, fakat tüm görüşleri ve eylemleri eksiksiz kuşatan merci."
        return "Mutlak Yaratıcı'nın hiçbir eylemi dışarıda bırakmayan kesintisiz gözlem ve denetimi (`بَصِيرٌ بِمَا تَعْمَلُونَ` / `بِٱلْعِبَادِ` / `سَمِيعٌۢ بَصِيرٌ` / `خَبِيرًۢا بَصِيرًا`)."

    elif root_ar == 'ر-و-د':
        if (s, a) == (18, 77):
            return "Kökün fiziksel hareket çapası (`جِدَارًا يُرِيدُ أَن يَنقَضَّ`): cansız bir duvarın yerçekimiyle yıkılmaya meyledip yüz tutması; `ر-و-د` kökünün yalnızca zihinsel istek değil, nesnel bir yöne doğru meyletme çekirdeğini kanıtlar."
        if (s, a) in ((12, 23), (12, 26), (12, 30), (12, 32), (12, 51), (12, 61), (54, 37)):
            return "III. bab `رَاوَدَ ... عَنْ` çekişme ve döndürme mekaniği: bir kimseyi kendi öz duruşundan (`عَن نَّفْسِهِ`), babasının korumasından (`12:61`) veya konuk emanetinden (`54:37`) ısrarla ve yumuşaklıkla/ayartarak çevirmeye çalışma (Rasm iskeleti elifsiz `رود`)."
        if (s, a) == (86, 17):
            return "Küçültme (`tasğîr`) kalıbıyla mühlet yasası (`أَمْهِلْهُمْ رُوَيْدًۢا`): `م-ه-ل` ile birlikte süreci yumuşakça, aceleye getirmeden azıcık akışına bırakma."
        if (s, a) in ((16, 40), (36, 82), (2, 253), (5, 1), (11, 107), (22, 14), (85, 16)):
            return "Mutlak Yaratıcı'nın yaratma ve hüküm yönelimi (`إِذَآ أَرَادَ شَيْـًٔا` / `فَعَّالٌ لِّمَا يُرِيدُ`): `ش-ي-أ` (oldurma seçimi) ile birleştiğinde arada hiçbir engel kalmadan gerçekleşen kudret."
        if (s, a) in ((2, 185), (4, 26), (4, 27), (4, 28), (5, 6), (33, 33)):
            return "İlâhî teşrîî yönelim ve kolaylık ilkesi (`يُرِيدُ ٱللَّهُ بِكُمُ ٱلْيُسْرَ وَلَا يُرِيدُ بِكُمُ ٱلْعُسْرَ`, `لِيُطَهِّرَكُمْ`, `لِيُخَفِّفَ`): ilâhî düzenin insanı zorlamak değil arıtıp kolaylaştırmak üzere yönelmesi."
        if (s, a) in ((3, 108), (40, 31), (51, 57), (28, 5), (72, 10)):
            return "Adalet, lütuf ve mutlak yeterlilik yönelimi (`وَمَا ٱللَّهُ يُرِيدُ ظُلْمًا`, `مَآ أُرِيدُ مِنْهُم مِّن رِّزْقٍ`, `أَشَرٌّ أُرِيدَ ... أَمْ رَشَدًا`): Yaratıcı'nın kullara zulüm veya geçim beklentisiyle yönelmediği gerçeği."
        if (s, a) in ((2, 26), (5, 41), (5, 49), (6, 125), (9, 55), (9, 85), (10, 107), (11, 34), (13, 11), (17, 16), (22, 16), (33, 17), (36, 23), (39, 4), (39, 38), (48, 11), (74, 31)):
            return "Sınav, karşılık ve takdir yönelimi (`إِن يُرِدْكَ بِخَيْرٍ`, `إِنْ أَرَادَ بِكُمْ ضَرًّا / رَحْمَةً`, `مَاذَآ أَرَادَ ٱللَّهُ بِهَٰذَا مَثَلًا`): insanın tutumuna göre açılan saptırma veya arındırma yasası."
        if (s, a) in ((9, 32), (61, 8), (38, 6)):
            return "Karşıt iradeler çatışması (`يُرِيدُونَ لِيُطْفِـُٔوا۟ نُورَ ٱللَّهِ وَيَأْبَى ٱللَّهُ`): hakikatin ışığını söndürmeye çalışanların yönelimine karşı sistemin bunu kesinlikle reddetmesi (`أ-ب-ي`)."
        if (s, a) in ((3, 145), (3, 152), (4, 134), (8, 67), (11, 15), (17, 18), (17, 19), (18, 28), (28, 79), (28, 83), (30, 38), (30, 39), (33, 28), (33, 29), (35, 10), (42, 20), (53, 29), (76, 9)):
            return "İnsanın hayat hedefi terazisi (`مَن كَانَ يُرِيدُ حَرْثَ ٱلْءَاخِرَةِ ↔ ٱلدُّنْيَا` / `يُرِيدُونَ وَجْهَ ٱللَّهِ`): yalnızca geçici dünyaya veya gösterişe yönelenle Yaratıcı rızasına ve onura yönelenin ayrımı."
        if (s, a) in ((2, 228), (2, 233), (4, 20), (4, 35), (24, 33), (28, 27), (33, 50)):
            return "Aile, nikâh, sözleşme ve toplumsal barış iradesi (`إِنْ أَرَادُوٓا۟ إِصْلَٰحًا`, `أَرَادَا فِصَالًا`, `إِنْ أَرَدْنَ تَحَصُّنًا`): evlilik ve toplum hukukunda karşılıklı rıza ve onarım niyeti."
        if (s, a) in ((6, 52), (11, 88), (18, 79), (18, 81), (18, 82), (25, 62)):
            return "Bilinçli onarım, ibret ve şükür yönelimi (`إِنْ أُرِيدُ إِلَّا ٱلْإِصْلَٰحَ`, `لِمَنْ أَرَادَ أَن يَذَّكَّرَ أَوْ أَرَادَ شُكُورًا`): insanın doğruya ve ıslaha meyletmesi."
        if (s, a) in ((5, 37), (22, 22), (32, 20)):
            return "Azap kıskacından çıkış yöneliminin boşa çıkması (`كُلَّمَآ أَرَادُوٓا۟ أَن يَخْرُجُوا۟ مِنْهَآ`): yaptırım yurdundan dışarı yönelip kurtulma çabasının geri çevrilmesi."
        if (s, a) in ((2, 108), (4, 44), (4, 60), (4, 62), (4, 88), (4, 91), (4, 144), (4, 150), (5, 91), (5, 113), (7, 110), (8, 7), (8, 62), (8, 71), (9, 46), (9, 107), (11, 79), (12, 25), (14, 10), (17, 103), (20, 63), (20, 86), (21, 17), (21, 70), (23, 24), (26, 35), (28, 19), (33, 13), (34, 43), (37, 86), (37, 98), (48, 15), (52, 42), (74, 52), (75, 5)):
            return "Siyasal, ahlâkî ve tarihsel niyet-amaç yönelimi (`يُرِيدُونَ أَن...` / `أَرَادُوا۟ بِهِۦ كَيْدًا`): tarafların gizli veya açık niyetlerle belirli bir sonuca doğru harekete geçmesi."
        return "Bilinçli veya yönelimli olarak bir amaca meyletme (`أَرَادَ` / `يُرِيدُ`): öznenin yöneldiği hedef doğrultusunda irade ortaya koyması (`5:29`, `11:34`)."

    elif root_ar == 'ل-ق-ي':
        if (s, a) in ((2, 46), (2, 223), (2, 249), (6, 31), (6, 130), (6, 154), (7, 51), (7, 147), (9, 77), (10, 7), (10, 11), (10, 15), (10, 45), (11, 29), (13, 2), (18, 105), (18, 110), (23, 33), (25, 21), (29, 5), (29, 23), (30, 8), (30, 16), (32, 10), (32, 14), (32, 23), (33, 44), (39, 71), (40, 15), (41, 54), (45, 34), (84, 6)):
            return "Büyük buluşma ve yüzleşme bilinci (`لِقَآءُ ٱللَّهِ` / `يَوْمُ ٱلتَّلَاقِ` / `مُلَٰقُوا۟ رَبِّهِمْ`): yaratılışın sonunda perdelerin kalkacağı büyük karşılaşmaya inanıp hazırlanma ile bunu yok saymanın ayrımı (`40:15`te vahiy bırakışı `يُلْقِى` ve buluşma günü `ٱلتَّلَاقِ` bir aradadır)."
        if (s, a) in ((2, 14), (2, 76), (3, 119), (3, 143), (8, 15), (8, 45), (43, 83), (47, 4), (52, 45), (62, 8), (69, 20), (70, 42)):
            return "Toplumsal, tarihî veya kaçınılmaz karşılaşma (`لَقُوا۟` / `إِذَا لَقِيتُمْ` / `مُلَٰقِيكُمْ`): ikircikli kişilerin güvene erenlerle buluşunca maske takması (`2:14`), savaş saflarında `فِئَةً` ile yüzleşince dönüp kaçmama (`ف-ر-ر` ↔ `ل-ق-ي`) ve ölümle kesin karşılaşma (`62:8`)."
        if (s, a) in ((3, 13), (3, 155), (3, 166), (8, 41), (8, 44), (54, 12), (55, 19)):
            return "VIII. bab karşılıklı buluşma ve temas (`ٱلْتَقَى ٱلْجَمْعَانِ`, `ٱلْتَقَى ٱلْمَآءُ`, `يَلْتَقِيَانِ`): iki topluluğun veya iki su kütlesinin aynı sınırda yüz yüze gelip buluşması."
        if (s, a) in ((2, 37), (21, 103), (24, 15), (25, 75), (27, 6), (28, 80), (41, 35), (50, 17), (76, 11)):
            return "II. ve V. bab karşılama, aktarım ve kavuşma (`فَتَلَقَّىٰٓ`, `لَتُلَقَّى`, `وَيُلَقَّوْنَ`, `ٱلْمُتَلَقِّيَانِ`): vahyi doğrudan teslim alma (`2:37`, `27:6`), esenlikle karşılanma (`21:103`, `25:75`), sebatla ulaşılan olgunluk (`41:35`) veya sorumsuzca dilden dile aktarma (`24:15`)."
        if (s, a) in ((7, 107), (7, 115), (7, 116), (7, 117), (7, 120), (10, 80), (10, 81), (20, 19), (20, 20), (20, 65), (20, 66), (20, 69), (20, 70), (26, 32), (26, 43), (26, 44), (26, 45), (26, 46), (27, 10), (28, 31)):
            return "Musa ve sihirbazlar sahnesinde IV. bab `أَلْقَى` (yere bırakma ve ortaya koyma): asanın yere bırakılması, sihirbazların iplerini ortaya atması ve hakikat görünce boyun eğme hâline bırakılmaları (`أُلْقِىَ ٱلسَّحَرَةُ سَٰجِدِينَ`)."
        if (s, a) in ((4, 171), (22, 52), (22, 53), (26, 223), (27, 28), (27, 29), (28, 86), (50, 37), (54, 25), (73, 5), (77, 5)):
            return "Vahiy, mesaj, kulak verme ve fısıltı bırakışı (`أَلْقَىٰهَآ إِلَىٰ مَرْيَمَ`, `سَنُلْقِى عَلَيْكَ قَوْلًا ثَقِيلًا`, `أَلْقَى ٱلسَّمْعَ`, `فَٱلْمُلْقِيَٰتِ ذِكْرًا`): vahiy ve yazılı mesajın muhatabın önüne bırakılması veya dikkatle kulak bırakılması (`50:37`)."
        if (s, a) in ((4, 90), (4, 91), (4, 94), (16, 28), (16, 87), (60, 1)):
            return "Barış, teslimiyet veya sevgi uzatma (`أَلْقَى ٱلسَّلَمَ / ٱلسَّلَٰمَ`, `تُلْقُونَ إِلَيْهِم بِٱلْمَوَدَّةِ`): karşı tarafın önüne barış ve uzlaşma bırakma ya da gizlice sevgi iletme."
        if (s, a) in ((15, 19), (16, 15), (31, 10), (50, 7), (84, 4)):
            return "Kozmik denge ve yer hareketi (`أَلْقَىٰ فِيهَا رَوَٰسِىَ`, `وَأَلْقَتْ مَا فِيهَا`): yeryüzüne sarsılmaz dağların yerleştirilmesi ve yerin içindekileri dışarı bırakması."
        if (s, a) in ((7, 47), (28, 22), (10, 15)):
            return "Konumsal yönelme ve yön (`تِلْقَآءَ`): gözlerin veya yolcunun belirli bir yöne doğru çevrilmesi (`7:47`, `28:22`)."
        if (s, a) in ((2, 195), (3, 151), (8, 12), (12, 10), (12, 93), (12, 96), (17, 39), (20, 39), (20, 87), (25, 13), (28, 7), (37, 97), (41, 40), (50, 24), (50, 26), (67, 7), (67, 8)):
            return "Fiziksel veya psikolojik bırakma-atma eylemi (`لَا تُلْقُوا۟ بِأَيْدِيكُمْ`, `سَنُلْقِى فِى قُلُوبِهِمُ ٱلرُّعْبَ`, `أَلْقَيْتُ عَلَيْكَ مَحَبَّةً`, `فَأَلْقُوهُ فِى...`): tehlikeye bırakma, kalbe korku veya sevgi koyma, suya/ateşe atılma."
        return "Yüz yüze karşılaşma veya bir sözü, özrü, durumu ortaya koyup bırakma (`لَقِىَ` / `أَلْقَى` / `مُلَاقٍ`): öznenin ortaya koyduğu söz ve eylemle yüzleşmesi (`16:86`, `17:13`, `18:62`, `18:74`, `19:59`, `25:68`, `75:15`)."

    elif root_ar == 'د-و-ن':
        if (s, a) in ((4, 48), (4, 116), (7, 168), (7, 205), (21, 82), (32, 21), (52, 47), (72, 11)):
            return "Derece, yoğunluk ve zaman-mekân basamağında beride/altta kalma (`دُونَ ذَٰلِكَ` / `دُونَ ٱلْجَهْرِ` / `ٱلْأَدْنَىٰ دُونَ ٱلْأَكْبَرِ`): `32:21`de yakın (`د-ن-و`) ile büyükten beride/aşağıda (`د-و-ن`) basamakları yan yana ayrıştırılır."
        if (s, a) in ((18, 90), (18, 93), (19, 17), (28, 23), (55, 62)):
            return "Somut mekân ve engel konumu (`مِن دُونِهَا سِتْرًا`, `مِن دُونِهِمَا`, `مِن دُونِهِمْ حِجَابًا`, `مِن دُونِهِمُ`): güneşle aralarında perde olmaması, iki setin veya halkın berisindeki alan ya da bahçelerin ötesi."
        if (s, a) in ((2, 94), (3, 28), (3, 118), (4, 139), (4, 144), (7, 81), (8, 60), (23, 63), (27, 55), (33, 50), (48, 27), (62, 6)):
            return "Toplumsal, ahlâkî ve zamansal sınır ayrımı (`مِن دُونِ ٱلْمُؤْمِنِينَ / ٱلنَّاسِ / ٱلنِّسَآءِ / فَتْحًا قَرِيبًا`): belirli bir topluluk, cinsiyet veya süreç sınırı dışına taşma ya da ondan önce gerçekleşen aşama."
        if (s, a) in ((2, 107), (4, 123), (4, 173), (6, 51), (6, 70), (9, 116), (11, 20), (11, 113), (13, 11), (17, 2), (18, 26), (18, 27), (18, 43), (18, 58), (21, 43), (28, 81), (29, 22), (32, 4), (33, 17), (42, 31), (42, 46), (46, 32), (53, 58), (67, 20), (71, 25), (72, 22)):
            return "Tek Mutlak Koruyucu dışında sığınak ve yardımcı yokluğu (`مِن دُونِهِۦ مِن وَلِىٍّ وَلَا نَصِيرٍ / شَفِيعٍ / مُلْتَحَدًا`): Evrenin Sahibi'nin berisinde kalan hiçbir varlığın koruma ve kurtarma gücü taşımaması."
        if (s, a) in ((3, 64), (4, 119), (7, 3), (7, 30), (9, 16), (17, 97), (18, 50), (18, 102), (25, 18), (29, 41), (34, 41), (39, 3), (42, 6), (42, 9), (45, 10)):
            return "Otorite ve dostluk ekseninin kaydırılması (`أَوْلِيَآءَ / أَرْبَابًا مِن دُونِ ٱللَّهِ`): En Yüce Sahip'i bırakıp O'nun seviyesinin altındaki örümcek ağı gibi çürük dayanaklara (`29:41`) bağlanma eleştirisi."
        if (s, a) in ((2, 23), (10, 37), (10, 38), (11, 13), (31, 11), (35, 40), (46, 4)):
            return "Yaratma ve vahiy benzersizliği meydan okuması (`مِن دُونِ ٱللَّهِ` — `31:11`, `35:40`, `46:4`): Yaratıcı dışındaki hiçbir alt odağın zerre kadar dahi yaratma veya denk söz üretme gücü bulunmayışı."
        return "Dikey hiyerarşide En Yüce Otorite'nin (`ٱلْعَلِىّ` `22:62`, `31:30`) berisinde ve altında kalan aciz varlıklara yönelme eleştirisi (`تَدْعُونَ / تَعْبُدُونَ / ٱتَّخَذُوا۟ مِن دُونِ ٱللَّهِ`): kendisine bile fayda-zarar veremeyen alt odakların geçersizliği."

    if root_ar == 'ن-ع-م':
        if lemma == 'naE~ama':
            return "Bolluk ve konforla (`نَعَّمَهُۥ`) sınanma psikolojisi (`89:15`): Refah verilişini ilâhî onay/şeref sanma yanılgısı (`89:16` rızık daraltması zıddıyla Mesânî)."
        if lemma == 'n~aAEimap':
            return "Huzurlu yüz yansıması (`نَّاعِمَةٌ` `88:8`): Sıkıntıdan çökmüş yüzlerin (`خَٰشِعَةٌ` `88:2`) tam karşısında iç ferahlığının ve yumuşak refahın çehrede parlaması."
        if lemma == "naEomaA^'":
            return "Sıkıntı-refah döngüsü (`نَعْمَآءَ` ↔ `ضَرَّآءَ` `11:10`): Zorluk (`ضَرَّآءَ`) ardından tatlandırıcı ferahlık (`نَعْمَآءَ`) gelince şımarıp şükrü bırakma zaafı."
        if lemma == 'n~aEomap':
            return "Fethalı `نَعْمَة` ile geçici dünyevî lüks eleştirisi (`44:27`, `73:11`): Kesreli `نِعْمَة`ten farklı olarak keyif sürüp hakkı yalanlayanların kırılgan varlık konforu."
        if lemma == 'niEoma':
            if (s, a) in ((2, 271), (4, 58)):
                return "Câmid övgü fiili birleşimi (`نِعِمَّا` = `نِعْمَ مَا`): İhtiyaç sahiplerine gizli destek vermenin veya emanet-adalet öğüdünün mükemmelliği."
            if (s, a) in ((38, 30), (38, 44)):
                return "Süleyman ve dirençli Eyyub hakkındaki ilâhî övgü mührü (`نِعْمَ ٱلْعَبْدُ`): Sürekli Yaratıcı'ya yönelen kulun kusursuz uyumu."
            if (s, a) in ((3, 173), (8, 40), (22, 78)):
                return "Çift kutuplu sığınak ve yardım övgüsü (`نِعْمَ ٱلْوَكِيلُ / نِعْمَ ٱلْمَوْلَىٰ وَنِعْمَ ٱلنَّصِيرُ`): En güvenilir vekil, sahip ve yardımcıya yaslanma güvencesi."
            return "Karşılığın, sonucun veya ilâhî kudretin yüce övgüsü (`نِعْمَ` `3:136`, `13:24`, `16:30`, `18:31`, `29:58`, `37:75`, `39:74`, `51:48`, `77:23`)."
        if lemma == '>anoEama':
            if (s, a) == (1, 7):
                return "Fâtiha'nın yol ayrımı (`أَنْعَمْتَ عَلَيْهِمْ ↔ غَيْرِ ٱلْمَغْضُوبِ`): Öfke ve sapkınlık yolundan ayrı duran, ilâhî rehberlik ve iyilik bahşedilmişlerin çizgisi."
            if (s, a) in ((2, 40), (2, 47), (2, 122)):
                return "İsrâiloğullarına tarihi nimet ve sözleşme hatırlatması (`نِعْمَتِىَ ٱلَّتِىٓ أَنْعَمْتُ عَلَيْكُمْ`): Öncelikli ihsana ahde vefa ile karşılık verme çağrısı."
            if (s, a) in ((17, 83), (41, 51)):
                return "Nimet karşısında insanın yüz çevirip büyüklenme zaafı (`إِذَآ أَنْعَمْنَا عَلَى ٱلْإِنسَٰنِ أَعْرَضَ`): Rahatlıkta uzaklaşma, darda yalvarma çelişkisi."
            if (s, a) == (33, 37):
                return "Aynı ayette iki düzeyli iyilik (`أَنْعَمَ ٱللَّهُ عَلَيْهِ` vs `وَأَنْعَمْتَ عَلَيْهِ`): Hem Yaratıcı'nın hidayet nimeti (`3MS`) hem elçinin insanî himayesi (`2MS`)."
            if (s, a) in ((27, 19), (46, 15)):
                return "Nimet bilincini şükür ve olgun eyleme çevirme duası (`نِعْمَتَكَ ٱلَّتِىٓ أَنْعَمْتَ عَلَىَّ`): Ana-babaya ve nesle uzanan sorumluluk duyarlılığı."
            return "Seçkinlere, kurtarılanlara veya elçilere yöneltilen koruyucu nimet (`أَنْعَمَ` `4:69,72`, `5:23`, `8:53`, `19:58`, `28:17`, `43:59`)."
        if lemma == 'naEiym':
            if (s, a) == (102, 8):
                return "Her nimetin hesap sorumluluğu (`لَتُسْـَٔلُنَّ يَوْمَئِذٍ عَنِ ٱلنَّعِيمِ` `102:8`): Tüketilen her refah ve imkânın hesabının sorulacağı nihai yüzleşme."
            return "Ebedî esenlik yurtlarında kesintisiz ve köklü huzur hâli (`جَنَّٰتِ / نَعِيمٌ / نَضْرَةَ ٱلنَّعِيمِ`): `5:65`, `9:21`, `37:43`, `56:12`, `76:20`, `83:22,24`."
        if lemma == 'n~aEam':
            if (s, a) in ((7, 179), (25, 44), (47, 12)):
                return "Akıl-kalp-kulak donanımını işletmeyenlerin benzetmesi (`كَٱلْأَنْعَٰمِ`): Sadece yiyip tüketerek güdüleriyle yaşayan bilinçsizlik eleştirisi."
            if (s, a) in ((4, 119), (5, 1), (5, 95), (6, 136), (6, 138), (6, 139), (6, 142), (22, 28), (22, 30), (22, 34)):
                return "Hayvanların helâl-haram sınırları ve batıl yasakların reddi (`أَنْعَٰم` `6:138-142`): Kulak yarma/hurafe tabularını yıkıp temiz paylaşım (`22:28,34`) ve dokunulmazlık (`5:95`) ilkesi."
            return "Hayvanların beslenme, süt, giyim, binek ve ısıya elverişli yaratılışı (`أَنْعَٰم` `16:5,66,80`, `23:21`, `36:71`, `40:79`, `43:12`, `79:33`, `80:32`)."
        if lemma == 'niEomap':
            if (s, a) in ((16, 112), (16, 121), (31, 20)):
                return "Kıllet ve kesret çoğul ayrımı: Nankörlüğü yüzünden açlık-korku elbisesi giydirilen kentin (`بِأَنْعُمِ` `16:112`) ve İbrahim'in seçkin nimeti (`لِّأَنْعُمِهِ` `16:121`) ile her yere yayılan bol nimetler (`نِعَمَهُۥ` `31:20`)."
            if (s, a) in ((2, 231), (3, 103), (5, 11), (14, 28), (14, 34), (16, 72), (16, 83), (16, 114), (31, 31), (35, 3), (52, 29)):
                return "Rasm-ı Osmânî'de zamirsiz olduğu hâlde açık tâ ile yazılan 11 özel `نِعْمَت` geçişi: nimetin tarihî/toplumsal ve kozmik sürekliliğine yapılan imlâ vurgusu (`16:18`deki kapalı `ة` ile kontrast)."
            if (s, a) in ((39, 8), (39, 49)):
                return "Darlık geçip nimet verilince nankörleşen insan psikolojisi (`نِعْمَةً`): 'Bana kendi bilgimle verildi' diyerek kaynağı unutma yanılgısı."
            if (s, a) in ((16, 53), (16, 71), (16, 81), (26, 22), (92, 19)):
                return "Her nimetin mutlak kaynağı ve karşılıksız iyilik bilinci (`16:53`, `26:22`, `92:19`): İyiliği kimseden nimet karşılığı beklemeden yalnızca Rab rızasıyla yapma olgunluğu."
            return "Topluluklara ve elçilere bahşedilen koruyucu nimet, nankörlük-şükür imtihanı (`2:211`, `3:171,174`, `5:3,6,7,20,110`, `8:53`, `12:6`, `14:6`, `29:67`, `33:9`, `37:57`, `43:13`, `48:2`, `49:8`, `54:35`, `68:2,49`, `93:11`)."

    if root_ar == 'س-ل-م':
        if lemma == 'sa`limuwn':
            return "Ölüm veya darlık çöktüğünde değil, henüz bedenen ve durumca sapasağlam iken (`وَهُمْ سَٰلِمُونَ` `68:43`) sorumluluğa çağrılma gerçeği."
        if lemma == 'musotasolimuwn':
            return "Dünyadaki kibirlerinden sıyrılıp hesap anında çaresizce pes ederek boyun eğiş (`مُسْتَسْلِمُونَ` `37:26`): İradî teslimiyetin tersine zorunlu çöküş."
        if lemma == 's~ilom':
            return "Ayrışma ve düşmanlık adımlarının zıddı olarak topyekûn esenlik ve barış düzenine giriş çağrısı (`ٱدْخُلُوا۟ فِى ٱلسِّلْمِ كَآفَّةً` `2:208`)."
        if lemma == 's~alom':
            if (s, a) == (8, 61):
                return "Karşı taraf barışa ve saldırmazlığa yöneldiğinde (`لِلسَّلْمِ`) güven içinde barışa yönelme ilkesi."
            return "Haklı ve üstün durumda iken gevşeyip aşağılayıcı teslimiyet/ateşkes dilenmeme uyarısı (`وَتَدْعُوٓا۟ إِلَى ٱلسَّلْمِ` `47:35`)."
        if lemma == 'sul~am':
            return "Yüksek katmana sağ salim ve adım adım ulaştıran merdiven (`سُلَّم` `6:35`, `52:38`): Mekânsal güvenle yükseliş aracı."
        if lemma == 'saliym':
            return "Çift kutupluluktan, hileden ve iç arızadan tamamen arınmış sapasağlam kalp (`قَلْبٍ سَلِيمٍ` `26:89`, `37:84`): İbrahim'in tek merkezli duru iç bütünlüğü."
        if lemma == 'm~usal~amap':
            if (s, a) == (2, 71):
                return "Bedenen hiç kusuru, lekesi ve alacası bulunmayan sapasağlam ve eksiksiz nitelik (`مُسَلَّمَةٌ لَّا شِيَةَ فِيهَا` `2:71`)."
            return "Haksız can kaybında mağdur aileye eksiksiz, kesintisiz ve sağ salim teslim edilmesi emredilen tazminat güvencesi (`4:92`)."
        if lemma == 'tasoliym':
            return "İçte hiçbir direnç ve pürüz bırakmadan tam teslim oluş veya saygı-esenlik dileği (`تَسْلِيمًا` `4:65`, `33:22`, `33:56`)."
        if lemma == 'sal~ama':
            if (s, a) == (2, 233):
                return "Anlaşma gereği hak sahibine kararlaştırılan bedeli eksiksiz ve sağlamca teslim etme hukuku (`سَلَّمْتُم` `2:233`)."
            if (s, a) == (8, 43):
                return "Kritik çatışma öncesinde topluluğu bozgun ve kavgadan koruyup sağ salim selâmete çıkarma (`سَلَّمَ` `8:43`)."
            if (s, a) == (4, 65):
                return "Adil hüküm karşısında içten içe sıkıntı duymadan tam bir huzur ve teslimiyetle kabullenme (`وَيُسَلِّمُوا۟` `4:65`)."
            return "Toplumsal güven, izinle giriş ve saygı ortamı kuran esenlik dileği sunma (`24:27`, `24:61`, `33:56`)."
        if lemma == 'salam':
            if (s, a) == (39, 29):
                return "Birbiriyle didişen çoklu ortakların elindeki adam ile tek efendiye bölünmeden pürüzsüz bağlı (`سَلَمًا لِّرَجُلٍ` `39:29`) kimse benzetmesi: Tevhidin psikolojik bütünlüğü!"
            return "Savaş veya hesap anında uzlaşma, barış ve boyun eğme teklifi (`4:90,91`, `16:28,87`)."
        if lemma == '<isola`m':
            if (s, a) in ((9, 74), (49, 17)):
                return "Kişinin kendi iradî teslimiyet beyanını başkasına başa kalkılacak bir lütuf sanması eleştirisi (`9:74`, `49:17`)."
            return "Yaratıcı katındaki tek tutarlı hayat düzeni: tüm parçalarıyla hakka uyup bütünlüğe ve iç barışa erme bilinci (`3:19,85`, `5:3`, `6:125`, `39:22`, `61:7`)."
        if lemma in ('m~usolimap', 'musolima`t'):
            return "Kendini hakikate, adalete ve esenliğe bütünüyle adayan dengeli topluluk ve kadınlar (`2:128`, `33:35`, `66:5`)."
        if lemma == '>asolama':
            if (s, a) == (49, 14):
                return "`أَسْلَمْنَا` ile `ءَامَنَّا` arasındaki ince Furûk (`49:14`): Dıştan barışçıl uyum gösterip katılmak henüz kalbe köklü güven (`إِيمَان`) yerleştiği anlamına gelmez."
            if (s, a) == (3, 83):
                return "Kozmik yasalara uyarak evrendeki bütün varlıkların isteyerek veya zorunlu olarak bütünlüğe boyun eğişi (`أَسْلَمَ` `3:83`)."
            if (s, a) in ((2, 112), (4, 125), (31, 22)):
                return "Yüzünü/bütün yönelişini iyilik üreterek (`مُحْسِن`) tek merkeze arızasız teslim etme (`أَسْلَمَ وَجْهَهُۥ`): bölünmemiş adanma!"
            return "İradeyi, aklı ve yönelişi tek Yaratıcı'nın esenlik yasasına teslim etme (`2:131`, `3:20`, `5:44`, `6:14,71`, `16:81`, `22:34`, `27:44`, `37:103`, `39:54`, `40:66`, `48:16`, `49:17`, `72:14`)."
        if lemma == 'musolim':
            if (s, a) == (68, 35):
                return "Düzen bozan suçlularla (`ٱلْمُجْرِمِينَ`) kendini bütünlüğe ve barışa adayanların (`ٱلْمُسْلِمِينَ`) asla bir tutulmayacağı Mesânî ilkesi (`68:35`)."
            if (s, a) == (3, 67):
                return "Mezhep ve kimlik kalıplarının üstünde İbrahim'in saf niteliği (`حَنِيفًا مُّسْلِمًا` `3:67`): Eğriden uzak, kendini doğrudan hakka teslim etmiş insan."
            return "Tarih boyu elçilerin, öğrencilerin ve uyananların ortak vasfı: mezhepsel değil ahlâkî-varoluşsal teslimiyet ve esenlik elçileri (`2:128-136`, `7:126`, `12:101`, `27:31-42`, `41:33`)."
        if lemma == 'sala`m':
            if (s, a) == (59, 23):
                return "Yaratıcı'nın hiçbir eksiklik, bozulma ve kusurla lekelenmeyen, varlıklara güvenlik yayan `ٱلسَّلَٰمُ` niteliği (`59:23`)."
            if (s, a) == (4, 94):
                return "Size barış ve güven mesajı (`ٱلسَّلَٰمَ`) uzatan kimseyi geçici dünya çıkarı için dışlamama ve hayatını koruma emri (`4:94`)."
            if (s, a) in ((19, 62), (25, 63), (28, 55), (56, 26)):
                return "Boş, kırıcı söz (`لَغْو`) ve cahilce saldırganlık (`ٱلْجَٰهِلِينَ`) karşısında tek karşılık olarak `سَلَٰمًا / سَلَٰمٌ` (zararsızlık ve vakur barış) sunma olgunluğu."
            if (s, a) == (97, 5):
                return "Fecir sökünceye kadar tüm korku ve çalkantıdan arınmış saf esenlik ve huzur gecesi (`سَلَٰمٌ هِىَ` `97:5`)."
            return "Her türlü korku, çöküş ve zarardan arınmış esenlik yurdu (`دَارُ ٱلسَّلَٰمِ`), elçilere tarihî esenlik mührü (`37:79-181`) ve güvenli selâmet (`11:48`, `15:46`, `21:69`, `50:34`)."

    if root_ar == 'د-ن-و':
        if lemma == 'daAn':
            return "Meyvenin hiçbir zahmet gerektirmeden el uzatacak kadar yakın oluşu (`وَجَنَى ٱلْجَنَّتَيْنِ دَانٍ` `55:54`): İkramın mekânsal erişim kolaylığı."
        if lemma == 'daAniyap':
            if (s, a) == (6, 99):
                return "Botanik gözlemde hurma tomurcuklarından sarkan yakın salkımlar (`قِنْوَانٌ دَانِيَةٌ` `6:99`): Kökün fizikî yerçekimi ve yaklaşma çekirdeği."
            return "Esenlik yurtlarında gölgelerin ve meyve salkımlarının zahmetsizce aşağıya doğru yakınlaşması (`69:23`, `76:14`)."
        if lemma == 'danaA':
            if (s, a) == (33, 59):
                return "Dış örtüleri bedene yaklaştırıp örtme (`يُدْنِينَ`) fiili ile tanınıp incitilmemeye en yakın olma (`أَدْنَىٰ`) arasındaki sebep-sonuç bağı (`33:59`)."
            return "Vahiy tanıklığında ufuktan yaklaşıp süzülme (`ثُمَّ دَنَا فَتَدَلَّىٰ` `53:8`): Somut mekânsal yaklaşma hareketi."
        if lemma == '>adonaY`':
            if (s, a) == (32, 21):
                return "Aynı ayette iki yakın kökün keskin Furûk ayrımı (`ٱلْعَذَابِ ٱلْأَدْنَىٰ دُونَ ٱلْعَذَابِ ٱلْأَكْبَرِ` `32:21`): Zaman-mekân yakınlığını (`ٱلْأَدْنَىٰ`) ve derecece önceliği/küçüklüğü (`دُونَ`) ayırt etme."
            if (s, a) == (58, 7):
                return "Üç kişinin fısıltısından daha azında da daha çoğunda da (`وَلَآ أَدْنَىٰ مِن ذَٰلِكَ وَلَآ أَكْثَرَ` `58:7`) Mutlak Bilgi'nin kuşatıcılığı."
            if (s, a) == (53, 9):
                return "İki yay ucu mesafesi kadar, hatta ondan da yakın ölçü (`فَكَانَ قَابَ قَوْسَيْنِ أَوْ أَدْنَىٰ` `53:9`)."
            if (s, a) == (2, 61):
                return "Yüksek ve hayırlı nimeti (`ٱلَّذِى هُوَ خَيْرٌ`) daha aşağı/ucuz olanla (`ٱلَّذِى هُوَ أَدْنَىٰ`) değiştirme yanılgısı (`2:61`)."
            if (s, a) in ((30, 3), (73, 20)):
                return "En yakın bölgede yaşanan tarihî yenilgi (`أَدْنَى ٱلْأَرْضِ` `30:3`) veya gecenin üçte ikisine yakın zaman dilimi (`أَدْنَىٰ` `73:20`)."
            return "Hakkı, adaleti, tanıklığı veya gönül huzurunu korumaya en yakın/en elverişli yol ölçüsü (`أَدْنَىٰ` `2:282`, `4:3`, `5:108`, `7:169`, `33:51`)."
        if lemma == 'd~unoyaA':
            if (s, a) == (8, 42):
                return "`ٱلدُّنْيَا` kelimesinin köksel anlamını mühürleyen tarihî ayet (`بِٱلْعُدْوَةِ ٱلدُّنْيَا ↔ بِٱلْعُدْوَةِ ٱلْقُصْوَىٰ` `8:42`): Kök olumsuz 'bayağı' değil, mekân/zamanca 'en yakın yamaç/aşama'dır."
            if (s, a) in ((37, 6), (41, 12), (67, 5)):
                return "Kozmolojide `ٱلسَّمَآءَ ٱلدُّنْيَا`: Yıldız ve ışık kaynaklarıyla süslenen 'yere en yakın gök katmanı'."
            if (s, a) == (57, 20):
                return "Geçici dünya aşamasının (`ٱلْحَيَوٰةُ ٱلدُّنْيَا`) yağmurla yeşerip kuruyan bitkiye benzeyen geçiciliği (`57:20`): Kısa vadeyi tek hedef sanmama uyarısı."
            return "Zamansal olarak 'ilk ve en yakın aşama' olan şimdiki yaşam (`ٱلدُّنْيَا`) ile onu izleyen sonraki aşama (`ٱلْءَاخِرَة`) dengesi: ikisinin ödülünü de ihmal etmeme (`28:77`, `4:134`, `9:38`, `13:26`)."

    if root_ar == 'ق-د-ر':
        if lemma == 'quduwr':
            return "Zanaat ve kapasite sembolü (`وَقُدُورٍ رَّاسِيَٰتٍ` `34:13`): Süleyman'ın yerleşik büyük kazanları; Semitik dilde 'ölçü kabı / hacim' köküyle somut paralellik."
        if lemma == 'm~aqoduwr':
            return "İnsanî sorumluluk ve elçilik görevi içinde yeri ve sınırları netleştirilmiş düzen (`قَدَرًا مَّقْدُورًا` `33:38`)."
        if lemma == 'miqodaAr':
            if (s, a) == (13, 8):
                return "Evrendeki her varlık ve olayın şaşmaz matematiksel ölçekle bulunması (`وَكُلُّ شَىْءٍ عِندَهُۥ بِمِقْدَارٍ` `13:8`)."
            return "Kozmik ve hesaba dönük göreceli zaman ölçeği (`مِقْدَارُهُۥ` `32:5` bin yıl; `70:4` elli bin yıl)."
        if lemma == 'm~uqotadir':
            return "Yaratılış döngüsünün ve tarihî hesaplaşmanın tam hâkimi (`مُّقْتَدِر` `18:45`, `43:42`, `54:42,55`): Büyüklük tasarrufunu elinde tutan otorite."
        if lemma == 'taqodiyr':
            return "Güneş, ay, yedi gök ve evrenin hassas matematiksel hesapla işleyişi (`تَقْدِيرُ ٱلْعَزِيزِ ٱلْعَلِيمِ` `6:96`, `36:38`, `41:12`, `25:2`, `76:16`)."
        if lemma == 'qador':
            if (s, a) in ((97, 1), (97, 2), (97, 3)):
                return "Vahyin inişiyle kıymet ve ölçü kazanan tarihî dönüm noktası (`لَيْلَةِ ٱلْقَدْرِ` `97:1-3`): Bin aydan daha verimli ve değerli gece."
            if (s, a) in ((6, 91), (22, 74), (39, 67)):
                return "Aynı ayette fiil + isim uyarısı (`مَا قَدَرُوا۟ ٱللَّهَ حَقَّ قَدْرِهِۦ`): Tek Yaratıcı'yı dar insanî/putperest kalıplara sığdırıp değerini küçültme yanılgısı."
            return "Her şeye biçilmiş zaman, sınır ve ölçü yasası (`قَدْ جَعَلَ ٱللَّهُ لِكُلِّ شَىْءٍ قَدْرًا` `65:3`)."
        if lemma == 'qadar':
            if (s, a) == (2, 236):
                return "Hukukî-ekonomik eşitlik değil orantılı hakkaniyet ilkesi (`عَلَى ٱلْمُوسِعِ قَدَرُهُۥ وَعَلَى ٱلْمُقْتِرِ قَدَرُهُۥ` `2:236`): Herkesin kendi mâlî kapasitesi ölçüsünde sorumluluğu."
            return "Yağmurun, sel vadilerinin, rızıkların ve insan yaratılışının kaostan uzak kesin miktar ve kapasiteyle indirilmesi (`13:17`, `15:21`, `23:18`, `42:27`, `43:11`, `54:49`, `77:22`)."
        if lemma == 'qaAdir':
            if (s, a) == (68, 25):
                return "Yoksulları dışlayarak 'ürünü kendi gücümüzle kesin toplarız (`قَٰدِرِينَ` `68:25`)' yanılgısına düşen bahçe sahiplerinin çöküşü."
            return "İlk yaratılışı ve yağmuru kuran aklın, çöküş sonrası insanı parmak uçlarına kadar (`75:4`) yeniden kurmaya da gücü yetmesi (`6:37,65`, `36:81`, `46:33`, `86:8`)."
        if lemma == 'qad~ara':
            if (s, a) == (34, 11):
                return "Zanaatta milimetrik mühendislik (`وَقَدِّرْ فِى ٱلسَّرْدِ` `34:11`): Zırh halkalarının ölçüsünü ve dengesini hassas ayarlama ilkesi."
            if (s, a) in ((74, 18), (74, 19), (74, 20)):
                return "Hakikate karşı bahaneler üreten zihnin iç kurgusu (`فَقُتِلَ كَيْفَ قَدَّرَ` `74:18-20`): İnsanın önyargıyla kendi kendine ölçüp biçmesi."
            return "Ayın evrelerinden yeryüzünün rızıklarına ve gecenin paylaşımına dek evrensel orantı-plan (`10:5`, `25:2`, `36:39`, `41:10`, `73:20`, `80:19`, `87:3`)."
        if lemma == 'qadara':
            if (s, a) in ((13, 26), (17, 30), (28, 82), (29, 62), (30, 37), (34, 36), (34, 39), (39, 52), (42, 12), (65, 7), (89, 16)):
                return "Ekonomik rızkın açılması (`بَسَطَ`) ile kısılıp daraltılması (`قَدَرَ`) arasındaki Mesânî dengesi: bolluk da darlık da sınama ölçüsüdür."
            if (s, a) in ((6, 91), (22, 74), (39, 67)):
                return "Allah'ın evrensel büyüklüğünü hakkıyla ölçüp kavrayamama eleştirisi (`مَا قَدَرُوا۟ ٱللَّهَ حَقَّ قَدْرِهِۦ`)."
            if (s, a) == (21, 87):
                return "Yûnus'un (Balık kıssası) daraldığında Yaratıcı'nın üzerine darlık sıkmayacağını (`نَّقْدِرَ عَلَيْهِ`) sanıp ardından derinlikten yönelişi (`21:87`)."
            return "Çabanın boşa gitmesi ya da hiçbir yetki ortağının/kibirlinin güç yetiremeyişi (`2:264`, `14:18`, `16:75,76`, `57:29`, `77:23`, `90:5`)."
        if lemma == 'qadiyr':
            if (s, a) == (30, 54):
                return "Güçsüzlük-güç-yaşlılık döngüsünü ölçülü kılan tek marife `ٱلْقَدِيرُ` (`30:54`): İnsanın biyolojik evrelerindeki hassas kudret dengesi."
            return "Evrendeki hiçbir olayın sınır dışında kalmadığını bildiren küllî ölçü ve imkân yasası (`عَلَىٰ كُلِّ شَىْءٍ قَدِيرٌ`): `2:20,106,284`, `3:26,189`, `4:149`, `5:120`, `35:44`, `42:9`."

    if root_ar == 'ن-ذ-ر':
        if lemma == 'nu*or':
            return "İlâhî ikazın iki işlevi (`عُذْرًا أَوْ نُذْرًا` `77:6`): Hem mazeret bırakmamak (`عُذْر`) hem de yaklaşan sonuca karşı uyarmak (`نُذْر`)."
        if lemma == 'nu*uwr':
            return "Kişinin gönüllü üstlendiği adak sorumluluklarını (`وَلْيُوفُوا۟ نُذُورَهُمْ` `22:29`) eksiksiz yerine getirme hukuku."
        if lemma == 'n~a*or':
            return "Adak (`نَذْر`) edilen her hayır veya bağlayıcı sözün şeffaflığı (`2:270`) ve sözüne sadık kalmanın (`يُوفُونَ بِٱلنَّذْرِ` `76:7`) övgüsü."
        if lemma == 'na*aro':
            if 'PASS' in features:
                return "Vahiyle uyarma eylemi (`أُنذِرُكُم`) karşısında iç kulağını kapatan sağırların (`يُنذَرُونَ` `21:45`) uyarıyı duyamaması."
            if (s, a) == (2, 270):
                return "Toplumsal katkı (`نَفَقَة`) ve gönüllü adakların (`نَذَرْتُم مِّن نَّذْرٍ` `2:270`) tek bir kaydının bile kaybolmayacağı güvencesi."
            if (s, a) == (3, 35):
                return "İmrân'ın eşinin doğacak çocuğunu çıkar gözetmeyen özgür bir adak (`نَذَرْتُ لَكَ مَا فِى بَطْنِى مُحَرَّرًا` `3:35`) olarak hakikate adaması."
            return "Meryem'in geçici suskunluk ve sözlü perhiz (`صَوْم`) adağı (`نَذَرْتُ` `19:26`): Tören değil özel iradî geri çekilme sözleşmesi."
        if lemma == 'mun*ariyn':
            return "Uyarıya kulak asmayan önceki toplulukların ibretlik akıbeti (`عَٰقِبَةُ ٱلْمُنذَرِينَ` `10:73`, `26:173`, `27:58`, `37:73,177`): İkazdan sonra sorumluluk kesinleşir."
        if lemma == 'mun*ir':
            if (s, a) in ((2, 213), (4, 165), (6, 48), (18, 56)):
                return "Müjdeleyici (`مُبَشِّرِينَ`) ile uyarıcı (`وَمُنذِرِينَ`) arasındaki çift yönlü elçilik dengesi: umutla birlikte tehlike bilinci."
            return "Vahyin korkutma değil uyandırma elçiliği (`مُنذِر` `13:7`, `26:194`, `38:4,65`, `46:29`, `50:2`, `79:45`): İnsanlara mazeret bırakmayan erken ikaz."
        if lemma == '>an*ara':
            if (s, a) in ((2, 6), (36, 10)):
                return "Önyargıyla kalbini kilitleyenler için ikaz döngüsünün eşik duvarı (`ءَأَنذَرْتَهُمْ أَمْ لَمْ تُنذِرْهُمْ`): İçten kapatana dış uyarı tesir etmez."
            if (s, a) in ((36, 6), (42, 7)):
                return "Önceden ikaz edilmemiş bir topluluktan başlayıp bütün merkezlere ve büyük toplanma gününe yayılan çok katmanlı uyarı (`36:6`, `42:7`)."
            if (s, a) in ((26, 214), (74, 2)):
                return "Yakın çevreden (`وَأَنذِرْ عَشِيرَتَكَ ٱلْأَقْرَبِينَ` `26:214`) başlayarak ayağa kalkıp toplumu uyarma çağrısı (`قُمْ فَأَنذِرْ` `74:2`)."
            return "Vahiy bilinciyle yaklaşan tehlike ve sorumluluğa karşı uyarma (`أَنذَرَ` `6:19,51`, `14:44`, `19:39`, `40:18`, `46:21`, `54:36`, `71:1`, `78:40`, `92:14`)."
        if lemma == 'na*iyr':
            if (s, a) in ((54, 16), (54, 18), (54, 21), (54, 30), (54, 37), (54, 39), (67, 17)):
                return "Kamer ve Mülk sûrelerinde nakaratlaşan yalın masdar uyarısı (`فَكَيْفَ كَانَ عَذَابِى وَنُذُرِ` / `كَيْفَ نَذِيرِ`): İmlâda son `-î` düşse de mânâ 'Benim uyarım nasılmış?'dır."
            if (s, a) == (53, 56):
                return "Önceki uyarıcı silsilesinin devamı (`هَٰذَا نَذِيرٌ مِّنَ ٱلنُّذُرِ ٱلْأُولَىٰٓ` `53:56`): Aynı kökün tekili ve çoğulu aynı ayette süreklilik kurar."
            if (s, a) == (35, 37):
                return "Ömür ve akıl verildiği hâlde sorumluluktan kaçanlara 'size beklenen uyarıcı gelmedi mi?' (`وَجَآءَكُمُ ٱلنَّذِيرُ` `35:37`) sorusu."
            if (s, a) in ((5, 19), (7, 188), (11, 2), (25, 1), (34, 46), (35, 24), (41, 4)):
                return "Sevindiren müjde (`بَشِير`) ile tehlikeyi bildiren uyarı (`نَذِير`) arasındaki Mesânî elçilik dengesi."
            return "Mazeretlerin kesildiği, her topluluğa gönderilmiş evrensel tehlike uyarıcısı ve açık ikaz (`نَذِير` `10:101`, `15:89`, `35:23,42`, `54:5,23`, `67:8-9,26`)."

    if root_ar == 'ج-م-ع':
        if lemma == 'jumuEap':
            return "Haftalık toplu buluşma ve kaynaşma günü (`يَوْمِ ٱلْجُمُعَةِ` `62:9`): Çağrı yükselince ticareti bırakıp ortak bilince koşma disiplini."
        if lemma == 'm~ujotamiEuwn':
            return "Gösteri alanında halkın kalabalık hâlde toplanma beklentisi (`مُّجْتَمِعُونَ` `26:39`): Kurumsal yönlendirmenin kitle üzerindeki etkisi."
        if lemma == 'majomaE':
            return "İki büyük su kütlesinin kavuştuğu coğrafî/sembolik birleşme noktası (`مَجْمَعَ ٱلْبَحْرَيْنِ` `18:60,61`)."
        if lemma == '{jotamaEu':
            return "İrade birliği meydan okuması (`17:88` insan ve görünmez tüm bilinçli türler toplansa da, `22:73` bir sineği geri almak için birleşseler de acziyetleri)."
        if lemma == 'm~ajomuwE':
            return "İlklerden sonlara tüm insanlığın tek meydanda mutlaka toplanacağı kesin hesap günü (`11:103`, `56:50`)."
        if lemma == 'jaAmiE':
            if (s, a) == (24, 62):
                return "Bütün toplumu ilgilendiren ortak sorumluluk toplantısı (`عَلَىٰٓ أَمْرٍ جَامِعٍ` `24:62`): İzinsiz dağılmayıp kolektif disiplini koruma."
            return "Gerçeği örtenleri ve ikiyüzlüleri ayırıp tek alanda toplayan (`جَامِعُ` `4:140`) ve kuşku bulunmayan günde insanlığı derleyen (`3:9`)."
        if lemma == '>ajomaEu':
            return "IV. bab `أَجْمَعَ` ile dağınık düşünceleri tek kesin kararda kilitleme (`10:71`, `12:15,102`, `20:64`): Zihinsel ve stratejik icmâ."
        if lemma == 'jamoE':
            if (s, a) in ((3, 155), (3, 166), (8, 41), (26, 61)):
                return "Karşıt iki kitlenin yüz yüze geldiği tarihî buluşma anı (`ٱلْجَمْعَانِ`): Fizikî karşılaşma eşiğinde dirayet sınavı."
            if (s, a) == (75, 17):
                return "Vahyin elçinin hafızasında eksiksiz derlenip bütünlenmesi (`إِنَّ عَلَيْنَا جَمْعَهُۥ وَقُرْءَانَهُۥ` `75:17`)."
            if (s, a) == (54, 45):
                return "Kendisini yenilmez sanan güç birliğinin (`ٱلْجَمْعُ` `54:45`) dağılıp arkasını dönerek kaçacağı tarihî kırılma."
            return "Toplanma günü (`يَوْمِ ٱلْجَمْعِ` `42:7`, `64:9`), atların ordu ortasına dalışı (`100:5`) ve kalabalık yığınların yetersizliği (`7:48`, `18:99`, `28:78`, `42:29`)."
        if lemma == 'jamaEa':
            if (s, a) in ((3, 157), (10, 58), (43, 32), (70, 18), (104, 2)):
                return "Servet yığma eleştirisi (`جَمَعَ فَأَوْعَىٰ` / `جَمَعَ مَالًا وَعَدَّدَهُۥ`): İhtiyaçtan fazlasını istifleyip paylaşmayı kesme eleştirisi."
            if (s, a) == (75, 3):
                return "Dağılmış kemik parçalarını bile tek tek yeniden birleştirme kudreti (`أَلَّن نَّجْمَعَ عِظَامَهُۥ` `75:3`)."
            if (s, a) == (75, 9):
                return "Güneş ile Ay'ın aynı eksende birleştirilmesi (`وَجُمِعَ ٱلشَّمْسُ وَٱلْقَمَرُ` `75:9`): Kozmik düzenin dönüşüm anı."
            if (s, a) == (4, 23):
                return "Aile yapısını koruma hukuku (`وَأَن تَجْمَعُوا۟ بَيْنَ ٱلْأُخْتَيْنِ` `4:23`): İki kız kardeşi aynı nikâh altında birleştirme yasağı."
            return "Tüm insanlığı ve kozmik varlıkları tek günde bir araya toplama (`3:25`, `4:87`, `5:109`, `6:12,35`, `18:99`, `34:26`, `42:15`, `45:26`, `64:9`, `77:38`)."
        if lemma == '>ajomaEiyn':
            return "Hiçbir istisna bırakmayan kapsayıcılık tevkîdi (`أَجْمَعُونَ / أَجْمَعِينَ`): Tüm görevli varlıkların secdeye uyumu (`15:30`, `38:73`) veya sapma/hesap sorumluluğu (`7:18`, `26:95`)."
        if lemma == 'jamiyE':
            if (s, a) == (59, 14):
                return "Aynı ayette çarpıcı Mesânî zıtlığı (`تَحْسَبُهُمْ جَمِيعًا وَقُلُوبُهُمْ شَتَّىٰ` `59:14`): Dıştan derli toplu birleşik görünseler de kalplerinin darmadağın bölünmüşlüğü!"
            if (s, a) == (5, 32):
                return "Evrensel insanlık hukuku ilkesi (`5:32`): Tek bir masumu öldürmenin bütün insanlığı (`ٱلنَّاسَ جَمِيعًا`) öldürmeye, bir canı kurtarmanın bütün insanlığı yaşatmaya denk oluşu."
            return "Evrensel egemenlik (`لِلَّهِ ٱلْأَمْرُ جَمِيعًا` `13:31`), hep birlikte hak ipine sarılma çağrısı (`3:103`) ve herkesin bir arada hazır bulunuşu (`26:56`, `36:32,53`, `54:44`)."

    if root_ar == 'ن-ظ-ر':
        if lemma == 'naZar':
            return "Ölüm baygınlığı geçirmiş birinin donuk bakışı (`نَظَرَ ٱلْمَغْشِىِّ عَلَيْهِ` `47:20`): İçten kaçınanların göz hareketine yansıyan korku psikolojisi."
        if lemma == 'naZorap':
            return "İbrahim'in gökyüzündeki yıldızlara tek bir bakış (`نَظْرَةً فِى ٱلنُّجُومِ` `37:88`): Tekil eylem ismi (`فَعْلَة`) olarak gözlem."
        if lemma == 'naZirap':
            return "Borç ve dayanışma hukuku (`فَنَظِرَةٌ إِلَىٰ مَيْسَرَةٍ` `2:280`): Darlıkta olan borçluya ödeme kolaylığına kadar yasal mühlet tanıma."
        if lemma == 'naAZirap':
            if (s, a) == (27, 35):
                return "Diplomatik nabız yoklaması (`فَنَاظِرَةٌۢ بِمَ يَرْجِعُ ٱلْمُرْسَلُونَ` `27:35`): Hediyeye verilecek cevabı gözleyip bekleme stratejisi."
            return "Parlayan yüzlerin (`نَّاضِرَةٌ`) Rabbine bakışı (`إِلَىٰ رَبِّهَا نَاظِرَةٌ` `75:23`): `ن-ض-ر` ile `ن-ظ-ر` arasında ses-anlam eşleşmesi."
        if lemma == 'na`Ziriyn':
            if (s, a) == (33, 53):
                return "Sosyal görgü hukuku (`غَيْرَ نَٰظِرِينَ إِنَىٰهُ` `33:53`): Ziyafet öncesinde vaktini beklemeden eve doluşmama nezaketi."
            return "Seyredenlerin gözünde hayranlık uyandıran görsel kanıtlar (`تَسُرُّ ٱلنَّٰظِرِينَ` `2:69`, `7:108`, `15:16`, `26:33`)."
        if lemma == 'munZaruwn':
            return "Mühlet sınırının dolması (`مُنظَرِينَ` `7:15`, `15:8,37`, `26:203`, `38:80`, `44:29`): İnsana tanınan vade bittiğinde ek erteleme kalmayışı."
        if lemma == 'muntaZiruwn':
            return "Bekleme yarışının çift kutuplu vurgusu (`مُنتَظِرُونَ` `6:158`, `7:71`, `10:20,102`, `11:122`, `32:30`): Hak ve gerçeği örtme çizgilerinin sonu beklemesi."
        if lemma == 'yantaZiru':
            if (s, a) == (33, 23):
                return "Verdiği söze sadakatle nöbet sırasını bekleyenler (`وَمِنْهُم مَّن يَنتَظِرُ` `33:23`): Kararlı sebat bekleyişi."
            return "Uyarıya rağmen son ana kadar sonuç bekleyenlere verilen karşılık (`فَٱنتَظِرُوٓا۟` `6:158`, `7:71`, `10:20,102`, `11:122`, `32:30`)."
        if lemma == 'yunZaru':
            if (s, a) in ((7, 14), (15, 36), (38, 79)):
                return "Kibirli isyancı odağın 'diriliş gününe dek bana süre ver (`أَنظِرْنِىٓ`)' talebi: IV. babın 'mühlet/erteleme verme' anlamı."
            if (s, a) in ((7, 195), (10, 71), (11, 55)):
                return "Sahte odaklara karşı meydan okuma (`فَلَا تُنظِرُونِ`): 'Topluca tuzak kurun ve bana göz açtıracak bir an bile mühlet vermeyin!'"
            return "Yapılan hataların sonucu geldiğinde hiç kimseye ek erteleme ve mühlet tanınmayacağı yasası (`لَا يُنظَرُونَ` `2:162`, `3:88`, `6:8`, `16:85`, `21:40`, `32:29`)."
        if lemma == 'n~aZara':
            if (s, a) in ((2, 210), (6, 158), (7, 53), (16, 33), (35, 43), (36, 49), (38, 15), (43, 66), (47, 18), (57, 13)):
                return "I. bab `نَظَرَ`nın 'gözünü dikip beklemek' anlamında kullanımı (`هَلْ / مَا يَنظُرُونَ` `2:210`, `36:49`, `38:15`): Belirti geldiğinde bekleme vaktinin bitmesi."
            if (s, a) in ((2, 104), (4, 46)):
                return "Alaycı çift anlamlı `رَٰعِنَا` sözü yerine açık saygılı `ٱنظُرْنَا` ('bizi gözet / durumumuza bak') demenin emredilişi (`2:104`, `4:46`)."
            if (s, a) == (3, 77):
                return "Sözleşmesini ucuz çıkara satanlara hesap günü şefkat ve ilgiyle bakılmaması (`وَلَا يَنظُرُ إِلَيْهِمْ` `3:77`)."
            if (s, a) == (7, 143):
                return "Duyusal sınır dersi (`أَنظُرْ إِلَيْكَ` vs `ٱنظُرْ إِلَى ٱلْجَبَلِ` `7:143`): Mûsâ'nın bakma isteğine karşı fiziki dağa bakarak güç sınırını kavraması."
            if (s, a) in ((2, 259), (6, 99), (7, 185), (50, 6), (80, 24), (86, 5), (88, 17)):
                return "Bilimsel ve biyolojik gözlem çağrısı: yemek-kemik dirilişi (`2:259`), bitki meyvesi (`6:99`), gıdası (`80:24`), yaratılış maddesi (`86:5`) ve devenin/göğün yapısı (`88:17`, `50:6`)."
            if (s, a) in ((59, 18), (78, 40)):
                return "Öz-hesap ve sorumluluk bakışı: 'Her benlik yarın için ne hazırladığına baksın (`وَلْتَنظُرْ نَفْسٌ` `59:18`)' ve elinin öne sürdüğüne bakış (`78:40`)."
            return "Tarihî enkazları gezerek sonuçları gözlemleme (`فَٱنظُرُوا۟ كَيْفَ كَانَ عَٰقِبَةُ` `6:11`, `12:109`, `30:9,42`) ve görgü tanıklığı (`2:50,55`, `3:143`, `51:44`, `83:23,35`)."

    if root_ar == 'س-أ-ل':
        if lemma == 'su&aAl':
            return "Mevcut imkânla yetinmeyip başkasının tek varlığını da kendi payına katma talebinin haksızlığı (`بِسُؤَالِ نَعْجَتِكَ إِلَىٰ نِعَاجِهِۦ` `38:24`)."
        if lemma == 'su&ol':
            return "Mûsâ'nın bütün samimi istek ve ihtiyaçlarının karşılanması (`قَدْ أُوتِيتَ سُؤْلَكَ` `20:36`)."
        if lemma == 'maso_#uwl':
            if (s, a) in ((17, 34), (17, 36)):
                return "Etik sorumluluk ilkesi (`17:34` verilen söz `عَهْد`, `17:36` işitme-görme-kavrama duyuları `مَسْـُٔولًا`): Sahip olunan her yetkinin hesabı sorulur."
            return "Sözleşme sorumluluğu (`33:15`), durdurulup sorgulanma (`37:24`) ve yerine getirilecek kesin söz (`وَعْدًا مَّسْـُٔولًا` `25:16`)."
        if lemma == 'saA^}il':
            if (s, a) in ((12, 7), (70, 1)):
                return "Araştırıp bilmek isteyenler için ibret (`لِّلسَّآئِلِينَ` `12:7`) ve alayla azap isteyen sorucu (`سَآئِلٌۢ` `70:1`)."
            if (s, a) == (93, 10):
                return "Hem maddi ihtiyaç sahibini hem bilgi soranı kırıp azarlamama ilkesi (`وَأَمَّا ٱلسَّآئِلَ فَلَا تَنْهَرْ` `93:10`)."
            return "Toplumsal paylaşım hakkı: tüm rızık arayanlar için dengeli ölçü (`سَوَآءً لِّلسَّآئِلِينَ` `41:10`) ve muhtaçların maldaki sabit hakkı (`2:177`, `51:19`, `70:25`)."
        if lemma == "yatasaA^'alu":
            if (s, a) == (4, 1):
                return "Sosyal dayanışma hukuku (`تَسَآءَلُونَ بِهِۦ وَٱلْأَرْحَامَ` `4:1`): İnsanların birbirinden hak ve iyilik isterken sığındıkları Yüce Ad ve akrabalık bağları."
            return "Karşılıklı soruşup sorgulama (`يَتَسَآءَلُونَ` `18:19`, `23:101`, `28:66`, `37:27,50`, `52:25`, `74:40`, `78:1`)."
        if lemma == 'sa>ala':
            if (s, a) == (21, 23):
                return "Mutlak Egemen ile sorumlu varlık sınırı (`لَا يُسْـَٔلُ عَمَّا يَفْعَلُ وَهُمْ يُسْـَٔلُونَ` `21:23`): Aynı ayette fiilin tekili Yaratıcı'yı, çoğulu ise tüm kulları sorgu kapsamına alır."
            if (s, a) in ((2, 134), (2, 141), (34, 25)):
                return "Bireysel ve kuşaksal sorumluluk devredilemezliği (`لَا تُسْـَٔلُونَ عَمَّا كَانُوا۟ يَعْمَلُونَ` / `وَلَا نُسْـَٔلُ عَمَّا تَعْمَلُونَ`): Kimse başkasının eyleminden sorgulanmaz."
            if (s, a) == (81, 8):
                return "Diri diri gömülen kız çocuğunun tanıklığı (`وَإِذَا ٱلْمَوْءُۥدَةُ سُئِلَتْ` `81:8`): Mazluma hangi suçtan öldürüldüğünün sorulması."
            if (s, a) == (102, 8):
                return "Verilmiş olan her türlü nimetten hesap sorulması (`لَتُسْـَٔلُنَّ يَوْمَئِذٍ عَنِ ٱلنَّعِيمِ` `102:8`)."
            if (s, a) in ((16, 43), (21, 7)):
                return "Bilgi hiyerarşisinde bilmeyenlerin uzman ve vahiy bilgisi sahiplerine danışma emri (`فَسْـَٔلُوٓا۟ أَهْلَ ٱلذِّكْرِ`)."
            if (s, a) == (5, 101):
                return "Yıkıcı merak veya gereksiz ayrıntı dayatma uyarısı (`لَا تَسْـَٔلُوا۟ عَنْ أَشْيَآءَ` `5:101`)."
            if 'PASS' in features:
                return "Uydurmalar ve verilen emanetler hakkında kaçınılmaz hesap sorgusu (`لَتُسْـَٔلُنَّ` `16:56,93`, `29:13`, `43:19,44`, `55:39`, `2:119`)."
            if (s, a) == (2, 186):
                return "Kulların seni benden sorduğunda (`سَأَلَكَ عِبَادِى عَنِّى` `2:186`): Aracısız doğrudan yakınlık yanıtı."
            return "Elçinin karşılık talep etmeyişi (`لَآ أَسْـَٔلُكُمْ أَجْرًا`), toplumsal sorular (`يَسْـَٔلُونَكَ`), tarihî bilgiyi araştırma emri (`سَلْ / فَسْـَٔلْ`) veya adil mehir iadesi (`60:10`)."

    if root_ar == 'ط-و-ع':
        if lemma == 'm~uTaAE':
            return "Vahyi ulaştıran güçlü ve güvenilir elçinin yüce konumu (`مُّطَاعٍ ثَمَّ أَمِينٍ` `81:21`): Zorbalıkla değil saygı ve güvenle kendisine uyulan otorite."
        if lemma == 'TaA^}iEiyn':
            return "Göklerin ve yerin kozmik çağrıya cevabı (`أَتَيْنَا طَآئِعِينَ` `41:11`): Evrensel yasaların zorla değil tam bir iç uyumla işleyişi."
        if lemma == 'muT~aw~iEiyn':
            return "Toplumsal dayanışmaya gönlünden koparak bağışta bulunanları (`ٱلْمُطَّوِّعِينَ` `9:79`) küçümseyenlerin alaycı tutumunun teşhiri."
        if lemma == 'Taw~aEato':
            return "İlk cinayet psikolojisi (`فَطَوَّعَتْ لَهُۥ نَفْسُهُۥ قَتْلَ أَخِيهِ` `5:30`): Kişinin kendi bencil benliğinin suçu kolay ve makul gösterip iç onayını teslim alması."
        if lemma == 'yuTaAEu':
            return "Elçinin misyonu (`وَمَآ أَرْسَلْنَا مِن رَّسُولٍ إِلَّا لِيُطَاعَ بِإِذْنِ ٱللَّهِ` `4:64`) ve hesap gününde sözü geçen bir kayırıcının bulunmayışı (`40:18`)."
        if lemma == 'taTaw~aEa':
            return "Zorunluluk sınırının ötesinde kendi hür iradesiyle fazladan iyilik üretme (`فَمَن تَطَوَّعَ خَيْرًا فَهُوَ خَيْرٌ لَّهُۥ` `2:158`, `2:184`): Gönüllü erdem faziletidir."
        if lemma == 'TaAEap':
            return "Sadece dil ucuyla söylenen yalancı uyum iddiası (`طَاعَةٌ` `4:81`, `24:53`, `47:21`): Somut sorumluluk saati gelince gizli niyetlerin ortaya çıkışı."
        if lemma == 'TawoE':
            return "Evrensel özgür irade vs zorunluluk ekseni (`طَوْعًا وَكَرْهًا` `3:83`, `9:53`, `13:15`, `41:11`): Gönüllü uyum (`طَوْعًا`) zoraki mecburiyetin (`كَرْهًا`) tam zıddıdır."
        if lemma == '{sotaTaAEa':
            if (s, a) == (18, 97):
                return "Aynı ayette fonetik ve anlam ikizliği (`فَمَا ٱسْطَٰعُوٓا۟ ... وَمَا ٱسْتَطَٰعُوا۟` `18:97`): Tırmanma aczi için kısa `ٱسْطَٰعُوٓا۟`, zırhlı setti delme imkânsızlığı için ağır tam `ٱسْتَطَٰعُوا۟` kullanımı!"
            if (s, a) in ((18, 78), (18, 82)):
                return "Kehf kıssasında Mûsâ'nın dayanma sınırı: hikmetler açılmadan önce ağır `تَسْتَطِع` (`18:78`), olaylar çözüldükten sonra hafiflemiş `تَسْطِع` (`18:82`) formu."
            if (s, a) == (64, 16):
                return "İnsanın sorumluluk sınırı (`فَٱتَّقُوا۟ ٱللَّهَ مَا ٱسْتَطَعْتُمْ وَٱسْمَعُوا۟ وَأَطِيعُوا۟` `64:16`): Güç ve imkân ölçüsü (`ٱسْتِطَاعَة`), gönüllü uyumun ön şartıdır."
            return "Güç, imkân, mali yeterlilik veya içsel direnç kapasitesi (`ٱسْتَطَاعَ`: `3:97`, `8:60`, `9:42`, `11:88` `إِنِ ٱسْتَطَعْتُ` gayreti)."
        if lemma == '>aTaAEa':
            if (s, a) == (4, 80):
                return "Elçiye gönüllü uyum ile Yaratıcı yasasına uyum arasındaki doğrudan bağ (`مَّن يُطِعِ ٱلرَّسُولَ فَقَدْ أَطَاعَ ٱللَّهَ` `4:80`)."
            if (s, a) in ((3, 50), (26, 108), (26, 110), (26, 126), (26, 131), (26, 144), (26, 150), (26, 163), (26, 179), (43, 63), (71, 3)):
                return "Elçilerin tarih boyu değişmeyen ortak çağrısı (`وَأَطِيعُونِ`): Kişisel hükümranlığa değil adalet ve koruyucu bilince gönüllü uyum (`-î` yâsı yazıda düşmüş form)."
            if (s, a) in ((33, 66), (33, 67)):
                return "Sürü psikolojisiyle kibirli önderlere körü körüne uymanın yıkıcı pişmanlığı (`يَٰلَيْتَنَآ أَطَعْنَا ٱللَّهَ وَأَطَعْنَا ٱلرَّسُولَا۠`)."
            if (s, a) == (24, 54):
                return "Elçiye düşen tek sorumluluğun açık duyuru olması ve hidayetin kör baskıda değil gönüllü uyumda (`وَإِن تُطِيعُوهُ تَهْتَدُوا۟` `24:54`) yatması."
            return "Bilinçli, gönüllü ve sorumlu uyum veya körce yanlış odağa boyun eğiş uyarısı (`4:59`, `5:92`, `6:121`, `31:15`, `47:33`, `49:14`, `64:12`)."

    if root_ar == 'ع-ظ-م':
        if lemma == 'yuEoZimo':
            return "IV. bab `وَيُعْظِمْ` (`65:5`): Kişinin sorumluluk bilinciyle hareket etmesine karşılık ödül miktarının büyütülüp genişletilmesi."
        if lemma == 'yuEaZ~imo':
            return "II. bab `يُعَظِّمْ` (`22:30`, `22:32`): Dokunulmaz sınırları ve ortak sembolleri saygıyla yüceltmenin kalplerdeki duyarlılık (`تَقْوَى ٱلْقُلُوبِ`) göstergesi oluşu."
        if lemma == 'EaZom':
            if (s, a) == (19, 4):
                return "Biyolojik yaşlanma gözlemi (`وَهَنَ ٱلْعَظْمُ مِنِّى` `19:4`): Kökün fizikî temeli olan kemiğin zayıflamasıyla beden gücünün çekilmesi."
            return "Gıda hukuku ayrımı (`أَوْ مَا ٱخْتَلَطَ بِعَظْمٍ` `6:146`): Kemiğe yapışık yağ dokusu üzerinden eski yasakların sınır tarifi."
        if lemma == '>aEoZam':
            return "Öncelik ve emek karşılığının derece üstünlüğü (`أَعْظَمُ دَرَجَةً` `9:20`, `57:10`; `أَعْظَمَ أَجْرًا` `73:20`): Zamanında yapılan fedakârlığın kıyas üstünlüğü."
        if lemma == 'EaZiym':
            if 'MP' in features:
                if (s, a) == (23, 14):
                    return "Embriyolojik kemik-et inşa basamağı (`فَخَلَقْنَا ٱلْمُضْغَةَ عِظَٰمًا فَكَسَوْنَا ٱلْعِظَٰمَ لَحْمًا` `23:14`): Aynı ayette çiğnemlik dokudan kemik (`عِظَٰمًا`) inşası ve üzerine et giydirilmesi!"
                return "Dağılmış/çürümüş kemiklerin yeniden inşası (`2:259`, `36:78`, `75:3`, `79:11`, `17:49`, `56:47`): Somut iskelet üzerinden diriliş kanıtlaması."
            if (s, a) in ((2, 255), (56, 74), (56, 96), (69, 33), (69, 52)):
                return "Sarsılmaz ve sınırsız yüceliğin adı (`ٱلْعَظِيمُ`): Kürsüsü bütün evreni kuşatan mutlak otorite."
            if (s, a) == (68, 4):
                return "Evrensel karakter standardı (`وَإِنَّكَ لَعَلَىٰ خُلُقٍ عَظِيمٍ` `68:4`): Çökmeyen kemik sağlamlığı gibi sarsılmaz ahlâkî omurga."
            if (s, a) in ((15, 87), (24, 11), (24, 15), (24, 16), (38, 67), (56, 76), (78, 2)):
                return "Önemli haber, ahlâkî iftira ağırlığı (`24:15,16`), vahiy bütünü (`15:87`) veya büyük tanıklık andı (`56:76`) için yapısal ağırlık ölçüsü."
            return "Büyük lütuf (`فَضْل عَظِيم`), ağır bedel (`عَذَاب عَظِيم`) veya büyük başarı (`فَوْز عَظِيم`): kökün sarsılmaz büyüklük ekseni (`2:7,105`, `4:113`, `9:72`)."

    if root_ar == 'خ-ل-ف':
        if lemma == 'm~usotaxolafiyn':
            return "Mülkiyet felsefesi (`أَنفِقُوا۟ مِمَّا جَعَلَكُم مُّسْتَخْلَفِينَ فِيهِ` `57:7`): İnsanın elindeki servetin mutlak maliki değil, önceki ve sonraki kuşaklar arasındaki geçici emanetçisi oluşu."
        if lemma == 'xilofap':
            return "Gece ile gündüzün birbirini izleyerek nöbetleşmesi (`خِلْفَةً` `25:62`): Biri geçince arkasından diğerinin gelip yerini doldurmasıyla oluşan hatırlatma ve değer bilme düzeni."
        if lemma == 'muxolif':
            return "Allah'ın elçilerine verdiği sözün arkasında duracağı mutlak güvencesi (`غَيْرَ مُخْلِفِ وَعْدِهِۦ` `14:47`)."
        if lemma in ('yataxal~afu', 'xul~ifu', 'xa`lifiyn', 'xawaAlif', 'muxal~afuwn'):
            return "Ortak sorumluluk ve sefer çağrısı karşısında mazeretsizce arkada kalıp kaytaranların (`9:81,83,87,93`, `48:11-16`) veya karar beklerken geride tutulanların (`9:118`) psikolojisi."
        if lemma == 'yuxaAlifu':
            if (s, a) == (11, 88):
                return "Söz-eylem tutarlılığı (`وَمَآ أُرِيدُ أَنْ أُخَالِفَكُمْ` `11:88`): Şuayb'ın toplumu uyardığı yasağın arkasına gizlenip bizzat kendisinin çiğnemeyeceğini bildirmesi."
            return "Ortak düzene ve uyarıya açıkça ters düşenlerin başlarına gelecek sarsıntı uyarısı (`24:63`)."
        if lemma == 'xalafa':
            if (s, a) in ((7, 142), (7, 150)):
                return "Vekâlet ve emanet sınavı (`ٱخْلُفْنِى` `7:142` vs `خَلَفْتُمُونِى` `7:150`): İnsanın bir başkasının ardından bıraktığı yeri ıslahla veya ihanetle doldurması."
            return "Öncekilerin ardından emaneti zayi eden yozlaşmış kuşağın gelişi (`7:169`, `19:59`) ve yeryüzünde yer değiştirme kudreti (`43:60`)."
        if lemma == '{sotaxolafa':
            return "Tarih ve toplum yasası (`ٱسْتَخْلَفَ` `6:133`, `7:129`, `11:57`, `24:55` x2): Sorumluluğu yitirenlerin ardından başkalarını yeryüzü temsilcisi kılma."
        if lemma == 'xila`f':
            if (s, a) in ((5, 33), (7, 124), (20, 71), (26, 49)):
                return "Anatomik çaprazlık (`مِنْ خِلَٰفٍ`): Sağ el ile sol ayağın ya da sol el ile sağ ayağın ters yönlerden kesilmesi."
            return "Sorumluluktan kaçıp arkada oturma (`خِلَٰفَ رَسُولِ ٱللَّهِ` `9:81`) ve senin ardından hemen oradan sürülme (`17:76`)."
        if lemma == '{xotila`f':
            if (s, a) == (4, 82):
                return "Bilimsel tutarlılık ve doğrulama ölçütü (`لَوَجَدُوا۟ فِيهِ ٱخْتِلَٰفًا كَثِيرًا` `4:82`): Vahiy metninin iç çelişkilerden arınmış bütünlüğü."
            if (s, a) == (30, 22):
                return "Dillerin ve ten renklerinin çeşitliliği (`وَٱخْتِلَٰفُ أَلْسِنَتِكُمْ وَأَلْوَٰنِكُمْ` `30:22`): Ayrımcılık sebebi değil yaratılış zenginliği kanıtı."
            return "Gece-gündüz döngüsünün ve kozmik mevsimlerin birbirini izleyerek değişmesi (`2:164`, `3:190`, `10:6`, `23:80`, `45:5`)."
        if lemma == 'xaliyfap':
            return "Yeryüzünde sorumluluk ve adalet emanetini kuşaktan kuşağa devralan temsilcilik (`2:30`, `38:26` Âdem ve Dâvûd; `6:165`, `7:69,74`, `10:14,73`, `27:62`, `35:39` insan toplulukları)."
        if lemma == 'm~uxotalif':
            if (s, a) in ((11, 118), (51, 8), (78, 3)):
                return "İradî tercih özgürlüğü yüzünden insanların görüşlerde ayrışması (`مُخْتَلِفِينَ` `11:118`, `51:8`, `78:3`)."
            return "Meyvelerin, bitkilerin, şifalı balın, dağ yollarının, insan ve hayvan renklerinin göz alıcı çeşitliliği (`6:141`, `16:13,69`, `35:27,28`, `39:21`)."
        if lemma == '>axolafu':
            if (s, a) == (34, 39):
                return "IV. babın tek olumlu telafi kullanımı (`وَمَآ أَنفَقْتُم مِّن شَىْءٍ فَهُوَ يُخْلِفُهُۥ` `34:39`): Paylaşılan değerin ardından yerine yenisini koyup telafi etmesi."
            return "Söz ve vaat güvencesi (`إِنَّ ٱللَّهَ لَا يُخْلِفُ ٱلْمِيعَادَ` `3:9`, `13:31`, `39:20`) ile insanın verdiği sözden dönme zaafı (`9:77`, `14:22`, `20:86-87`)."
        if lemma == 'xalof':
            if (s, a) in ((7, 169), (19, 59)):
                return "Cezimli `خَلْفٌ` (`7:169` geçici dünyalık alan, `19:59` sorumluluk ve destek bağını yitiren bozuk arka kuşak): fethalı hayırlı halefin zıddı."
            return "İnsanın önü ve arkasındaki görünmez zaman-mekân kuşağı (`2:255`, `7:17`, `13:11`, `36:9`, `41:42`) veya ardında bıraktığı nesil ve ibret (`2:66`, `4:9`, `10:92`)."
        if lemma == '{xotalafa':
            if (s, a) in ((2, 213), (10, 19), (10, 93), (16, 124), (45, 17)):
                return "Aynı ayette bilgi sonrası hizipleşme dinamiği (`ٱخْتَلَفُوا۟ ... يَخْتَلِفُونَ`): Ayrılık bilgisizlikten değil, bilgi geldikten sonraki çıkar ve kıskançlıktan doğar."
            return "Tarih boyu kitap ve hakikat konusunda düşülen ayrılıkların gerçek yargı gününde kesin çözüme bağlanması (`3:55`, `11:110`, `32:25`, `39:46`, `41:45`)."

    if root_ar == 'أ-ه-ل':
        if (s, a) in ((11, 45), (11, 46)):
            return "Mensubiyet ilkesi (`11:45-46`): 'Oğlum benim ailemdendir (`مِنْ أَهْلِى`)' iddiasına karşı 'O senin ehlinden değildir (`لَيْسَ مِنْ أَهْلِكَ`), çünkü dürüst olmayan bir eylemdir' ölçütü!"
        if (s, a) in ((4, 58), (48, 26), (74, 56)):
            return "Ehliyet ve liyakat yasası (`4:58` emanetleri ehil olana teslim etme, `48:26` sözüne en lâyık ve ehil olanlar, `74:56` korunup saygı duyulmaya ve bağışlamaya ehil Tek Otorite)."
        if (s, a) in ((16, 43), (21, 7)):
            return "Uzmanlık ve bilgi ehliyeti (`فَسْـَٔلُوٓا۟ أَهْلَ ٱلذِّكْرِ`): Bilinmeyen konuda konunun tanığı ve bilgi ehline danışma çağrısı."
        if (s, a) in ((4, 35), (24, 27), (66, 6)):
            return "Aile içi adalet ve saygı hukuku (`4:35` her iki aileden hakem, `24:27` hane halkına selam ve izinle girme, `66:6` kendini ve yakın çevreni yakıcı sonuca karşı koruma)."
        if (s, a) in ((11, 73), (33, 33)):
            return "Evin ve ocağın yakın mensupları (`أَهْلَ ٱلْبَيْتِ` `11:73`, `33:33`): Arınma, rahmet ve sorumluluk odağı olan hane halkı."
        if (s, a) in ((11, 117), (28, 59)):
            return "Toplumsal çöküş yasası (`11:117`, `28:59`): Bir kentin halkı (`أَهْلُهَا`) birbirini ıslah edip düzeltirken ve uyarı ulaşmadan o kent asla yıkılmaz."
        if (s, a) in ((20, 10), (27, 7), (28, 29)):
            return "Çöl yolculuğu ve çadır ocağı (`بِأَهْلِهِۦ ... لِأَهْلِهِ`): Kökün en eski Semitik 'otağ ve aile' tabakasını yaşatan Mûsâ anlatımı."
        if (s, a) in ((3, 64), (3, 65), (5, 47), (29, 46), (57, 29)):
            return "Önceki vahiy mirasını paylaşan kitap mensuplarıyla ortak hak sözü (`كَلِمَةٍ سَوَآءٍ` `3:64`) ve güzel usulle diyalog (`29:46`) çağrısı."
        return "Aile sorumluluğu (`أَهْلِيكُمْ` `5:89`, `48:11`), yerleşim sakinleri (`أَهْلُ ٱلْقُرَىٰ` `7:96-98`, `18:77`) veya eyleminin sonucuyla yüzleşen gruplar (`2:126`, `29:31`, `39:15`, `42:45`)."

    if root_ar == 'د-خ-ل':
        if lemma == 'mud~axal':
            return "İftial (VIII.) babında `t→d` idğamıyla (`مُدَّخَلًا` `9:57`): Korkudan dolayı içine sokulup saklanılacak dar kovuk, sığınak ve kaçış deliğinin fiziksel somutluğu."
        if lemma == 'daxal':
            return "Fethalı `دَخَلًۢا` (`16:92`, `16:94`): Bağlayıcı antları ve toplumsal sözleşmeleri çıkar uğruna içeriden bozan gizli fesat ve aldatma unsuru."
        if lemma == 'm~udoxal':
            if (s, a) == (17, 80):
                return "Aynı ayette hem `أَدْخِلْنِى` hem `مُدْخَلَ صِدْقٍ ↔ مُخْرَجَ صِدْقٍ` Mesânî çifti (`17:80`): Bütüncül doğruluk kapısından giriş ve çıkış duası."
            return "IV. bab mimli masdar/mekân (`مُّدْخَلًا كَرِيمًا` `4:31`, `مُّدْخَلًا يَرْضَوْنَهُۥ` `22:59`): İyileştirici tutumun sonunda ulaşılan onurlu ve razı olunan yerleşim makamı."
        if (s, a) in ((2, 208), (110, 2)):
            return "Kavramsal geçiş (`2:208` tam barış ve esenlik dairesine girme `ٱدْخُلُوا۟ فِى ٱلسِّلْمِ`, `110:2` Allah'ın yaşam düzenine dalga dalga katılma)."
        if (s, a) == (4, 23):
            return "Evlilik ve mahremiyet hukuku (`دَخَلْتُم بِهِنَّ` `4:23` x2): Eşlerle fiilî evlilik birlikteliğine girip girmemenin doğurduğu akrabalık sınırı."
        if (s, a) in ((24, 27), (24, 28), (24, 29), (33, 53)):
            return "Özel hayatın dokunulmazlığı ve hane adabı (`24:27-29` başkalarının evine izin ve selamsız girmeme, `33:53` elçinin evlerine zamansız girmeme ilkesi)."
        if (s, a) in ((12, 67), (12, 99), (27, 12), (27, 18), (27, 44)):
            return "Tarihsel ve fiziksel giriş sahneleri (`12:67` tek kapıdan değil ayrı kapılardan girme tedbiri, `12:99` Mısır'a güvenle giriş, `27:12` eli koyna sokma, `27:18` karınca yuvalarına giriş, `27:44` billur köşke giriş)."
        if (s, a) in ((5, 21), (5, 22), (5, 23), (5, 24)):
            return "Tarihî cesaret sınavı (`5:21-24`): Zorbaların bulunduğu beldeye girme çağrısı karşısında korkup çekinenlerin `لَن نَّدْخُلَهَا حَتَّىٰ يَخْرُجُوا۟ مِنْهَا` (`5:22`) itirazı."
        if (s, a) in ((7, 38), (33, 14), (66, 10)):
            return "Tarihsel veya hesapsal karşıt girişler (`7:38` kuşakların ateş yurduna art arda girişi, `33:14` şehre her yandan baskın girilmesi, `66:10` sorumluluğu reddeden iki eşe verilen ortak karar)."
        if lemma == '>udoxila':
            return "IV. bab geçişli/edilgen girdi (`أَدْخِلْ / نُدْخِلُ / أُدْخِلَ`): Eylemlerin sonucu olarak esenlik bahçelerine (`4:57`, `4:122`, `48:5`), rahmete (`7:151`, `21:75`, `76:31`) veya yakıcı ateş yurduna (`3:192`, `40:46`, `71:25`) alınma yasası."
        return "Bilinçli tercih sonucu esenlik yurtlarına, şehir kapılarına veya kendi seçiminin yakıcı karşılığına giriş (`2:58`, `13:23`, `15:46`, `16:29`, `39:72-73`, `89:29-30`)."

    if root_ar == 'خ-و-ف':
        if lemma == 'taxaw~uf':
            return "V. bab hapax `تَخَوُّفٍ` (`16:47`): Tarihte toplumların gücünü kenarlardan azar azar kırpıp eksilterek (`tenakkus`) veya korku kıskacıyla yakalama yasası."
        if lemma == 'taxowiyf':
            return "II. bab masdar hapax `تَخْوِيفًا` (`17:59`): Olağanüstü belgelerin ve uyarıların sırf gösteri için değil caydırıcı uyarı amacıyla gönderilmesi."
        if lemma == 'yuxaw~ifu':
            if (s, a) == (3, 175):
                return "Üçlü Furûk (`3:175`): Ayartıcı güç kendi yandaşlarıyla gözdağı verir (`يُخَوِّفُ`); siz ise onlardan korkmayın (`فَلَا تَخَافُوهُمْ`), yalnızca Benden çekinin (`وَخَافُونِ`)."
            return "İkinci bab korkutma (`17:60`, `39:16`, `39:36`): Hem ilâhî azap uyarısıyla sarsma (`39:16`) hem karşıtların sahte ortaklarla elçiye gözdağı vermeye çalışması (`39:36`)."
        if lemma == 'xiyfap':
            if (s, a) in ((11, 70), (20, 67), (51, 28)):
                return "Derin iç ürperti (`أَوْجَسَ ... خِيفَةً` `11:70`, `20:67`, `51:28`): Elçilerin insanî olarak hissettiği iç çekince ve hemen ardından gelen `لَا تَخَفْ` (`korkma`) tesellisi."
            return "İç sarsıntı ve ürperti (`7:205` sessiz iç yalvarış, `13:13` gök gürültüsünün ürperti vermesi, `30:28` kendi eşlerinizden/yetkilerinizden duyduğunuz çekince kıyaslaması)."
        if lemma == 'xaA^}if':
            return "I. bab ism-i fâil (`2:114` anma evlerine saygı ve çekince duymadan girememek gerekenler, `28:18,21` Mûsâ'nın kentte tehlikeyi kollayarak ürküntüyle yürümesi)."
        if (s, a) in ((2, 38), (2, 62), (2, 112), (2, 262), (2, 274), (2, 277), (3, 170), (5, 69), (6, 48), (7, 35), (7, 49), (10, 62), (43, 68), (46, 13)):
            return "Mesânî güven formülü (`لَا خَوْفٌ عَلَيْهِمْ وَلَا هُمْ يَحْزَنُونَ`): Geleceğe dönük tehlike kaygısı (`خَوْف`) ile geçmişe dönük üzüntünün (`حَزَن`) eşzamanlı sıfırlanması."
        if (s, a) in ((7, 56), (13, 12), (30, 24), (32, 16)):
            return "Duygu dengesi (`خَوْفًا وَطَمَعًا` `7:56`, `13:12`, `30:24`, `32:16`): Şimşeği görüp hem zarardan korkmak hem yağmur umuduyla dolmak arasındaki dengeli bilinç."
        if (s, a) in ((16, 112), (24, 55), (106, 4)):
            return "Toplumsal güvenlik ve açlık-korku sınaması (`24:55` ve `106:4` korkudan sonra güvene çıkarma; `16:112` nankörlüğün ardından açlık ve korku elbisesi giydirilmesi)."
        if (s, a) in ((2, 229), (4, 3), (4, 34), (4, 35), (4, 128)):
            return "Aile ve yetim hukukunda öngörülü tedbir (`خِفْتُمْ / تَخَافُونَ`): Evlilikte sınırların korunamamasından, yetim hakkının çiğnenmesinden veya aile geçimsizliğinden duyulan ihtiyatlı kaygı."
        if (s, a) in ((6, 80), (6, 81), (20, 68), (20, 77), (26, 21), (27, 10), (28, 7), (33, 19)):
            return "Cesaret ve emanet sınavı (`6:81` sahte ortakları korkulacak sanma yanılgısı, `20:77` `لَّا تَخَٰفُ دَرَكًا وَلَا تَخْشَىٰ` mutlak güven, `28:7` anneye `korkma` güveni, `33:19` savaş korkusu gelip gidince tavır değiştirenler)."
        return "Tehlike beklentisine karşı ahlâkî duyarlılık, elçilerin sorumluluk kaygısı (`إِنِّىٓ أَخَافُ عَلَيْكُمْ عَذَابَ يَوْمٍ عَظِيمٍ`) ve yersiz insan korkusunun aşılması."

    if root_ar == 'ر-ز-ق':
        if lemma == 'r~az~aAq':
            return "Tekil mübalağa unvanı (`إِنَّ ٱللَّهَ هُوَ ٱلرَّزَّاقُ` `51:58` hapax): Yaratan'ın kuldan hiçbir tayın istemeden (`51:57`) her varlığı kesintisiz besleyen Mutlak Kaynak oluşu."
        if lemma == 'r~a`ziqiyn':
            if (s, a) == (15, 20):
                return "Görev sınırı (`وَمَآ أَنتُمْ لَهُۥ بِرَٰزِقِينَ` `15:20`): İnsanların geçim kapılarına asıl rızkı var edenin kendileri değil Yaratıcı olduğu uyarısı."
            return "Üstünlük vurgusu (`خَيْرُ ٱلرَّٰزِقِينَ` `5:114`, `22:58`, `23:72`, `34:39`, `62:11`): Geçim dağıtan tüm aracılar içinde en kusursuz ve tükenmez kaynak."
        if (s, a) in ((2, 233), (4, 5), (4, 8)):
            return "İnsanî hukuk ve paylaşım sorumluluğu (`2:233` annelerin geçim hakkı `رِزْقُهُنَّ`, `4:5` reşit olmayanlara ve `4:8` miras anındaki muhtaçlara rızıktan pay ayırma `وَٱرْزُقُوهُمْ`)."
        if (s, a) in ((11, 6), (29, 60)):
            return "Ekolojik güvence yasası (`11:6` her canlının rızkının Allah katında belirlenmesi, `29:60` kendi rızkını sırtında taşıyamayan sayısız canlının beslenmesi)."
        if (s, a) in ((16, 71), (16, 75), (34, 36), (34, 39)):
            return "Ekonomik paylaşım ve genişlik-kısıtlılık sınavı (`16:71,75` rızıkta yetki alanların paylaşma sorumluluğu, `34:36,39` `يَبْسُطُ ٱلرِّزْقَ ... وَيَقْدِرُ` rızkı açma ve ölçülü tutma dengesi)."
        if (s, a) == (56, 82):
            return "Nimet-teşekkür tersinmesi (`وَتَجْعَلُونَ رِزْقَكُمْ أَنَّكُمْ تُكَذِّبُونَ` `56:82`): Size verilen payın/yaşam bağışının karşılığını şükür yerine yalanlama hâline getirmeniz."
        if (s, a) in ((2, 25), (3, 37), (3, 169), (12, 37), (20, 131), (20, 132), (24, 38), (65, 11)):
            return "Hesapsız ve kalıcı rızık (`بِغَيْرِ حِسَابٍ` `2:212`, `3:37`, `24:38`; `20:131` Rabbinin rızkı daha hayırlı ve kalıcıdır; `20:132` senden rızık istemiyoruz, seni Biz besliyoruz; `3:169` ölenlerin diriler olarak rızıklandırılması)."
        if (s, a) in ((2, 3), (2, 57), (2, 172), (5, 88), (16, 112), (28, 57), (29, 17), (67, 21)):
            return "Rızkı yalnızca gerçek kaynaktan isteme (`29:17`, `67:21`), temiz ve helal olanından yiyip (`2:172`, `5:88`) başkalarıyla paylaşma (`مِمَّا رَزَقْنَٰهُمْ يُنفِقُونَ` `2:3`) döngüsü."
        return "İnsanın yaşama, bilgiye ve meyveye kavuştuğu geçim payının Yaratıcı tarafından tahsis edilmesi ve bu payın iyilikle harcanması çağrısı."

    if root_ar == 'ب-ش-ر':
        if lemma == 'ba`$iru':
            return "Fiziksel kök doğrudanlığı (`بَٰشِرُوهُنَّ ... وَلَا تُبَٰشِرُوهُنَّ` `2:187` III. bab): Evlilikte iki tenin birbirine dokunması (`el-beşere`), itikaf süresince ise sınıra saygı duyulması."
        if lemma in ('bu$or', 'muba$~ira`t') or (s, a) == (30, 48):
            return "Doğadaki müjde sinyali (`7:57`, `25:48`, `27:63`, `30:46`, `30:48`): Yağmurdan önce yeryüzünü ve yüzleri dirilten rahmet öncesi müjde rüzgârları."
        if lemma == 'ba$ar':
            if (s, a) in ((74, 25), (74, 29), (74, 36)):
                return "Üçlü Müddessir vurgusu (`74:25,29,36`): Karşıtların 'bu yalnızca ölümlü insan (`ٱلْبَشَرِ`) sözü' küçümsemesine karşılık, hakikat ateşinin insan derisini (`لِلْبَشَرِ`) kavuran bir uyarıcı oluşu."
            if (s, a) in ((18, 110), (21, 3), (23, 47)):
                return "Elçilerin insanî kimliği (`إِنَّمَآ أَنَا۠ بَشَرٌ مِّثْلُكُمْ` `18:110`, `41:6`): Karşıtların elçiyi 'sıradan ten sahibi bir insan' diye reddetmesine karşılık vahyin 'evet, ama vahyolunan bir insanım' cevabı."
            if (s, a) in ((19, 17), (30, 20)):
                return "İnsanın topraktan derili-canlı varlık olarak ortaya çıkışı (`30:20` `ثُمَّ إِذَآ أَنتُم بَشَرٌ تَنتَشِرُونَ`) ve vahiy elçisinin düzgün insan suretinde görünmesi (`19:17` `بَشَرًا سَوِيًّا`)."
            return "Et ve dış deri taşıyan ölümlü insan doğası (`15:28,33`, `38:71` çamurdan yaratılan beşer, `3:47`, `19:20` Meryem'e hiçbir insanın dokunmamış olması)."
        if (s, a) in ((16, 58), (16, 59), (43, 17)):
            return "Dış deri tepkisi (`بُشِّرَ بِٱلْأُنثَىٰ` `16:58-59`, `43:17`): Normalde yüzü parlatan haber anlamına gelen kökün, cahiliye önyargısında kız çocuğu haberiyle yüz derisini karartan ironik sınanması."
        if (s, a) in ((3, 21), (4, 138), (9, 3), (9, 34), (31, 7), (45, 8), (84, 24)):
            return "Edebî tersinme (`فَبَشِّرْهُمْ بِعَذَابٍ أَلِيمٍ`): Gerçeğe sırt dönenlere yüzlerini parlatacak müjde yerine acı sonun müjdelenmesiyle sarsıcı ironik uyarı."
        if lemma in ('ba$iyr', 'muba$~ir'):
            if (s, a) == (12, 96):
                return "Kıssadaki müjdeci (`فَلَمَّآ أَن جَآءَ ٱلْبَشِيرُ` `12:96`): Yûsuf'un gömleğini getirip babası Yakub'un gözünü açan somut sevinç habercisi."
            return "Elçilik çift dengesi (`بَشِيرًا وَنَذِيرًا` / `مُبَشِّرًا وَنَذِيرًا`): İyilik yolundakilere müjde (`ب-ش-ر`), tehlike yolundakilere uyarı (`ن-ذ-ر`) taşıyan dengeli elçilik görevi."
        if lemma in ('yasotabo$iru', 'm~usotabo$irap', '>abo$iru') or (s, a) == (39, 45):
            if (s, a) == (39, 45):
                return "Kalpsel ayrım testi (`39:45`): Tek olan Allah anılınca gerilenlerin, sahte aracılar anılınca yüzlerinin birden müjdeyle açılması (`إِذَا هُمْ يَسْتَبْشِرُونَ`)."
            return "İçten taşan aydınlık sevinç (`3:170-171`, `9:111`, `41:30`, `80:39` `ضَاحِكَةٌ مُّسْتَبْشِرَةٌ`): Doğruluk ve emek karşılığında yüz derisinde parlayan kalıcı esenlik."
        return "Yüzü aydınlatan sevindirici haber, vahyin kalbe verdiği ferahlık (`بُشْرَىٰ` `2:97`, `16:89,102`, `27:2`, `46:12`) ve İbrâhim/Sâre (`11:71`, `15:54`) veya Yûsuf (`12:19`) kıssalarındaki umut doğuşu."

    if root_ar == 'ي-د-ي':
        if (s, a) in ((5, 64), (17, 29)):
            return "Cimrilik-cömertlik mecazı (`يَدُ ٱللَّهِ مَغْلُولَةٌ ... يَدَاهُ مَبْسُوطَتَانِ` `5:64` ve `17:29`): Boyna bağlanmış el cimriliği, sonuna dek açılmış iki el ise ölçüsüz vericilik ile savurganlık arasındaki dengeyi simgeler."
        if (s, a) in ((38, 75), (48, 10), (57, 29), (67, 1)):
            return "Mutlak tasarruf ve özen mecazı (`38:75` bizzat özenle yaratma `بِيَدَىَّ`, `48:10` sözleşme üstü ilâhî el, `57:29` lütuf ve `67:1` egemenliğin O'nun tasarrufunda olması)."
        if (s, a) in ((2, 237), (3, 73), (5, 38), (9, 29), (48, 24), (59, 2), (111, 1)):
            return "Hukukî yetki ve fiilî güç kullanımı (`2:237` evlilik bağı yetkisi, `5:38` hırsızlık yaptırımı, `9:29` `عَن يَدٍ` elden ve boyun eğerek ödeme, `48:24` çatışan ellerin geri tutulması, `59:2` kendi elleriyle yıkım, `111:1` iki elin boşa çıkması)."
        if (s, a) in ((5, 6), (7, 108), (28, 32)):
            return "Doğrudan fiziksel el organı (`5:6` temizlikte ellerin dirseklere dek yıkanması/meshedilmesi, `7:108` ve `28:32` Mûsâ'nın koynundan bembeyaz çıkan eli)."
        if (s, a) in ((2, 79), (2, 95), (5, 11), (5, 28), (38, 45), (60, 12)):
            return "Eylemin öznesi ve sorumluluğu (`2:79` kendi elleriyle vahiy tahrifi, `2:95` kendi ellerinin önceden gönderdiği işler, `5:28` kötülüğe el uzatmama, `38:45` irade ve güç sahipleri `أُو۟لِى ٱلْأَيْدِى`)."
        if (s, a) in ((5, 46), (36, 45), (58, 13)):
            return "Ön-uzam ve zaman mecazı (`بَيْنَ يَدَىْ`): Kişinin iki elinin arasındaki görünür alan (`36:45` önünüzdeki gelecek ve arkanızdaki geçmiş; `5:46` önceki Tevrat; `58:13` özel görüşme öncesi sadaka)."
        return "İnsanın kendi eliyle kazandığı sorumluluk (`قَدَّمَتْ / كَسَبَتْ أَيْدِيهِمْ`), önündeki süreç (`بَيْنَ يَدَيْهِ`) veya tasarruf/yetki alanı (`بِيَدِهِ`)."

    if root_ar == 'أ-م-م':
        if lemma == 'A^m~iyn':
            return "Tek I. bab ism-i fâil (`ءَآمِّينَ ٱلْبَيْتَ ٱلْحَرَامَ` `5:2`): Kutsal Ev'i kastedip oraya yönelen kimselerin dokunulmazlığı (`أَمَّ - يَؤُمُّ` = yönelmek)."
        if lemma == '>amaAm':
            return "Zaman-mekân zarfı hapax (`أَمَامَهُۥ` `75:5`): İnsanın kendi önünü ve geleceğini bile hiçe sayarak sınırsız taşkınlık yapmak istemesi."
        if lemma == '>um~iY~':
            if (s, a) in ((7, 157), (7, 158)):
                return "Vahiy elçisinin sıfatı (`ٱلرَّسُولَ ٱلنَّبِىَّ ٱلْأُمِّىَّ`): Önceki yazılı kitap geleneklerinin dışından yetişmiş fıtrî elçi."
            return "Kitap bilgisi veya yazılı vahiy geleneği dışı topluluklar (`2:78` kitabı bilmeyip kuruntuya dalanlar, `3:20,75`, `62:2` kendilerine içlerinden elçi gönderilen halk)."
        if lemma == '<imaAm':
            if (s, a) in ((15, 79), (36, 12)):
                return "Ana yol ve ana sicil (`15:79` hâlâ göz önündeki işlek ana yol üzerinde; `36:12` her izin ve eserin yazıldığı apaçık ana kütük)."
            if (s, a) in ((9, 12), (28, 41)):
                return "Olumsuz öncülük (`9:12` gerçeği örtme öncüleri, `28:41` yakıcı ateşe çağıran liderler): `أَئِمَّة` kelimesinin hem iyilik hem kötülük önderliğinde kullanılabildiği."
            return "Doğruluk önderliği ve rehber kitap (`2:124` İbrâhim'in insanlara önder kılınması, `11:17`, `46:12` Mûsâ'nın kitabı, `17:71` herkesin kendi önderi/kütüğüyle çağrılması, `21:73`, `25:74`, `28:5`, `32:24`)."
        if (s, a) in ((11, 8), (12, 45), (16, 120), (6, 38)):
            if (s, a) == (6, 38):
                return "Ekolojik evrensellik (`أُمَمٌ أَمْثَالُكُم` `6:38`): Yerde yürüyen ve kanatlarıyla uçan her canlının insan gibi birer ümmet/topluluk oluşu."
            if (s, a) == (16, 120):
                return "Tek kişilik model (`إِنَّ إِبْرَٰهِيمَ كَانَ أُمَّةً` `16:120`): Bir değer sistemini tek başına temsil eden kimsenin başlı başına bir ümmet oluşu."
            return "Zaman birimi olarak `أُمَّة` (`11:8` sayılı bir süreye ertelenmesi, `12:45` uzun bir zaman dilimi sonra hatırlaması)."
        if (s, a) in ((3, 7), (6, 92), (13, 39), (42, 7), (43, 4), (101, 9)):
            return "Ana merkez ve kaynak mecazı (`3:7`, `13:39`, `43:4` hükümlerin dayandığı `أُمُّ ٱلْكِتَٰبِ`, `6:92`, `42:7` kentlerin anası `أُمَّ ٱلْقُرَىٰ`, `101:9` sarıp kuşatan derin uçurum)."
        if (s, a) in ((4, 11), (4, 23), (58, 2)):
            return "Aile hukuku (`4:11` annenin miras hakkı, `4:23` biyolojik anne ile sütannenin evlilik sınırı, `58:2` eşlerin zıharla anne kılınamayacağı gerçeği)."
        return "Ortak bir yöneliş ve ilke çevresinde bütünleşen topluluk (`2:143` dengeli tanık topluluk, `3:110`, `21:92`, `23:52` tek ümmet ilkesi) veya anne sevgisi/sorumluluğu."

    if root_ar == 'ع-ز-ز':
        if lemma == 'Eaz~a':
            return "I. bab muzâaf tek fiil (`وَعَزَّنِى فِى ٱلْخِطَابِ` `38:23`): Söz ve tartışma gücünde karşısındakini bastırıp galip gelme."
        if lemma == 'Eaz~azo':
            return "II. bab tek fiil (`فَعَزَّزْنَا بِثَالِثٍ` `36:14`): Elçilik desteğini üçüncü bir tanıkla sağlamlaştırıp pekiştirme."
        if lemma == 'tuEiz~u':
            return "IV. bab tek fiil (`وَتُعِزُّ مَن تَشَآءُ وَتُذِلُّ مَن تَشَآءُ` `3:26`): Onur vermenin (`ع-ز-ز`) ve alçaltmanın (`ذ-ل-ل`) tek merkezde toplanması."
        if (s, a) in ((12, 30), (12, 51), (12, 78), (12, 88)):
            return "Siyasal makam unvanı (`ٱلْعَزِيزُ` Yûsuf kıssası): Mısır devlet mekanizmasının dokunulmaz yöneticisi."
        if (s, a) in ((2, 206), (11, 91), (11, 92), (18, 34), (19, 81), (26, 44), (38, 2), (63, 8)):
            return "Sahte izzet yanılgısı (`2:206` suçlu kibrine kapılma, `11:91-92` aşireti Allah'tan üstün/saygın sanma, `18:34` kalabalığıyla övünme, `26:44` Firavun gücüne sığınma, `63:8` kibirle üstünlük iddiası)."
        if (s, a) in ((4, 139), (5, 54), (10, 65), (27, 34), (35, 10)):
            return "İzzet-zillet yasası (`4:139`, `10:65`, `35:10` bütün onurun kaynağının Allah olması; `5:54` ve `27:34` hakikat çizgisinde onur ile zilletin yer değiştirmesi)."
        if (s, a) in ((9, 128), (14, 20), (35, 17), (41, 41)):
            return "Ağırlık, güçlük ve eşsizlik anlamları (`9:128` sıkıntının ağırlığı, `14:20` ve `35:17` Allah'a imkânsız/zor olmama, `41:41` sarsılmaz eşsiz kitap)."
        return "Yaratıcı Kudret'in yenilmezliğini, sarsılmaz hükmünü ve hikmet-merhametle birleşen aşılmaz gücünü (`ٱلْعَزِيزُ`) bildiren ana unvan."

    if root_ar == 'ج-ز-ي':
        if lemma == 'nuja`ziY^':
            return "III. bab hapax (`جَزَيْنَٰهُم ... وَهَلْ نُجَٰزِىٓ إِلَّا ٱلْكَفُورَ` `34:17`): İyilikte sınırı aşmayan I. bab karşılığına karşı, azgın nankörlükte aşırı gidenlere uygulanan birebir mufâale karşılığı."
        if lemma == 'jizoyap':
            return "Hukukî-mali hapax (`ٱلْجِزْيَةَ` `9:29`): Toplumsal güvenlik ve barış sözleşmesinin yükümlülüğünü karşılayan, kendi eliyle ödenen bedel."
        if (s, a) in ((2, 48), (2, 123), (31, 33)):
            return "Kökün en eski kefalet anlamı (`لَا تَجْزِى نَفْسٌ عَن نَفْسٍ` `2:48,123` ve `لَا يَجْزِى وَالِدٌ ... وَلَا مَوْلُودٌ هُوَ جَازٍ` `31:33`): Hesap gününde hiç kimsenin bir başkasının yerine geçip bedel ödeyememesi."
        if (s, a) in ((6, 160), (40, 40), (53, 31), (53, 41), (55, 60)):
            return "Kozmik adalet dengesi (`6:160` kötülüğe yalnızca dengi `مِثْلَهَا`, iyiliğe on katı; `40:40`; `53:31,41` en eksiksiz karşılık; `55:60` iyiliğin karşılığı yalnızca iyilik midir?)."
        if (s, a) in ((12, 74), (12, 75), (5, 38)):
            return "Yeryüzü hukuku ve Yûsuf kıssası (`12:74-75` 'kimin yükünden çıkarsa onun kendisi tam karşılığıdır' kuralı, `5:38` suçun caydırıcı karşılığı)."
        if (s, a) in ((14, 51), (20, 15), (40, 17), (45, 22)):
            return "Yaratılış gayesi ve bireysel hesap (`لِتُجْزَىٰ كُلُّ نَفْسٍۭ بِمَا كَسَبَتْ / تَسْعَىٰ` `14:51`, `20:15`, `40:17`, `45:22`): Her canlı kendi emeğinin karşılığını eksiksiz alır ve kimseye haksızlık edilmez."
        return "Yapılan her bilinçli eylemin (`بِمَا كَسَبُوا۟ / بِمَا عَمِلُوا۟ / بِمَا صَبَرُوا۟`) iyilik veya yıkım cinsinden adil karşılığının ödenmesi."

    if root_ar == 'أ-ب-و':
        if (s, a) == (4, 11):
            return "Aile miras hukuku (`وَلِأَبَوَيْهِ / أَبَوَاهُ / ءَابَآؤُكُمْ` `4:11`): Anne-babanın eşit miras payı ve kuşaklar arası mülkiyet dengesi."
        if (s, a) in ((4, 22), (24, 31), (33, 5), (33, 40)):
            return "Soy, evlat edinme ve mahremiyet hukuku (`4:22` baba eşleriyle evlenme yasağı, `24:31` aile mahremiyeti, `33:5` çocukları gerçek babalarına nispet etme ilkesi, `33:40` elçilik bağı vs biyolojik babalık ayrımı)."
        if (s, a) in ((2, 133), (2, 170), (5, 104), (43, 22)):
            return "Atalar mirası ikiliği (`2:133` bilinçli tevhit atalarına bağlılık vs `2:170`, `5:104`, `43:22` akletmeyen ataları körü körüne taklit eleştirisi)."
        if (s, a) in ((9, 23), (58, 22)):
            return "İlke-akrabalık önceliği (`9:23`, `58:22`): Biyolojik babalar bile hakikatle savaşıyorsa haksız desteklemenin reddi."
        if (s, a) in ((12, 4), (12, 8), (12, 68), (12, 99), (12, 100), (19, 42), (28, 26), (37, 102)):
            return "Baba-evlat şefkat diyaloğu (`يَٰٓأَبَتِ` `12:4,100`, `19:42`, `28:26`, `37:102` ve Yûsuf kıssasındaki `أَبَوَيْهِ` anne-baba kavuşması)."
        return "Bireysel baba sorumluluğu, kuşaklar arası manevî veya tarihsel bağ ile akıl dışı atalar taklidinin sorgulanması."

    if root_ar == 'ن-ه-ر':
        if lemma == 'tanoharo':
            return "İnsanî nezaket ve akışkan merhamet kuralı (`17:23` yaşlı anne-babayı, `93:10` el açanı/isteyeni sertçe azarlayıp geri püskürtme yasağı)."
        if (s, a) == (47, 15):
            return "Dörtlü esenlik bahçesi tasviri (`47:15`): Bozulmayan su, tadı değişmeyen süt, içimi lezzetli içecek ve süzme baldan oluşan dört ayrı ırmak (`أَنْهَٰرٌ`) türü."
        if (s, a) in ((2, 249), (18, 33), (43, 51), (54, 54)):
            return "Tekil `نَهَر` ve su egemenliği (`2:249` Tâlût'un ordusuna ırmak sınavı, `18:33` iki bağ ortasından fışkıran nehir, `43:51` Firavun'un ırmaklarla övünmesi, `54:54` esenlik bahçeleri ve aydınlık/ırmaklar)."
        if (s, a) in ((13, 3), (14, 32), (16, 15), (27, 61), (71, 12)):
            return "Yeryüzü hidrolojisi (`13:3`, `14:32`, `16:15`, `27:61`, `71:12`): Dağlarla dengelenmiş yeryüzünde yaşam ve ulaşım için akıtılıp hizmete verilen nehirler."
        if (s, a) in ((3, 27), (17, 12), (22, 61), (25, 47), (31, 29), (35, 13), (36, 37), (39, 5), (57, 6), (78, 11), (91, 3), (92, 2)):
            return "Gece-gündüz kozmolojisi (`لَيْل ↔ نَهَار`): Birbirinin içine geçirilip (`يُولِجُ`), sıyrılıp (`نَسْلَخُ`), açılıp diriliş ve geçim zamanı (`مَعَاشًا / نُشُورًا`) kılınan aydınlık gündüz döngüsü."
        if lemma == 'nahar':
            return "Esenlik bahçelerinin temel yaşam bileşeni (`جَنَّٰتٍ تَجْرِى مِن تَحْتِهَا ٱلْأَنْهَٰرُ`): Tabanından kesintisiz akan diriltici ırmaklar."
        return "Karanlıktan aydınlığa açılan gündüz zamanı ve iyilik çabasının kesintisiz gece-gündüz sürekliliği (`لَيْلًا وَنَهَارًا`)."

    if root_ar == 'أ-ك-ل':
        if lemma == 'm~a>okuwl':
            return "Fiziksel aşındırma hapaxı (`كَعَصْفٍ مَّأْكُولٍۭ` `105:5`): İçi kemirilip boşaltılmış, yenilip posası kalmış ekin yaprağı/saman haline dönüştürülme."
        if lemma == '>ak~a`luwn':
            return "Mübalağa sıfatı hapax (`أَكَّٰلُونَ لِلسُّحْتِ` `5:42`): Haram kazancı ve rüşveti tek seferlik değil, alışkanlık halinde oburca yutup sömürenler."
        if lemma == "'aAkiluwn":
            if (s, a) == (23, 20):
                return "Zeytin ağacının besin değeri (`صِبْغٍ لِّلْءَاكِلِينَ` `23:20`): Yiyenler için yağ ve ekmeğe batırılan katık üretmesi."
            return "Yakıcı yıkım yurdu beslenmesi (`37:66`, `56:52`): Karın dolduran ama beslemeyen zakkum ağacından zorunlu olarak yiyecek olanlar (`لَءَاكِلُونَ`)."
        if lemma == '>akol':
            if (s, a) == (89, 19):
                return "Mef'ûl-i mutlak pekiştirmesi (`وَتَأْكُلُونَ ٱلتُّرَاثَ أَكْلًا لَّمًّا` `89:19`): Zayıfların miras payını kendi payına katıp toptan süpürürcesine tüketme."
            return "Masdar halinde ekonomik gasp (`4:161`, `5:62`, `5:63`): Asılsız yoldan başkalarının malını (`أَمْوَٰلَ ٱلنَّاسِ بِٱلْبَٰطِلِ`) veya haram kazancı (`ٱلسُّحْتَ`) yiyip eritme."
        if lemma == '>ukul':
            if (s, a) == (13, 4):
                return "Doğal çeşitlilik kanıtı (`13:4`): Aynı suyla sulanan bitkilerin yenilebilir tat ve ürün veriminde (`فِى ٱلْأُكُلِ`) birbirinden farklı kılınması."
            if (s, a) == (34, 16):
                return "Ekolojik dönüşüm (`جَنَّتَيْنِ ذَوَاتَىْ أُكُلٍ خَمْطٍ` `34:16`): Şükürden yüz çevirme sonrası verimli bahçelerin buruk ve acı yemişli bitkilere dönüşmesi."
            return "Ağaç ve bahçenin olgun verimi (`أُكُل` `2:265`, `6:141`, `13:35`, `14:25`, `18:33`): Emek veya rahmet sonucu eksiksiz ortaya çıkan yenilebilir ürün."
        if (s, a) in ((3, 183), (34, 14)):
            if (s, a) == (3, 183):
                return "Ateşin tüketmesi (`قُرْبَانٍ تَأْكُلُهُ ٱلنَّارُ` `3:183`): Ateşin, sunulan nesneyi yakıp kül ederek maddesini eksiltip yok etmesi."
            return "Kurdun kemirmesi (`دَآبَّةُ ٱلْأَرْضِ تَأْكُلُ مِنسَأَتَهُۥ` `34:14`): Yer kurdunun Süleyman'ın ahşap asasını içten içe aşındırıp tüketerek devirmesini sağlaması."
        if (s, a) in ((2, 174), (4, 10)):
            return "Karın içi ateş mecazı (`يَأْكُلُونَ فِى بُطُونِهِمْ نَارًا` `2:174`, `4:10`): Vahyi gizleme veya yetim malı yeme karşılığında kişinin kendi içine yakıcı yıkım ateşini doldurması."
        if (s, a) in ((2, 188), (2, 275), (3, 130), (4, 2), (4, 6), (4, 29), (9, 34)):
            if (s, a) == (4, 2):
                return "Tazmîn sanatıyla mal birleştirme yasağı (`وَلَا تَأْكُلُوٓا۟ أَمْوَٰلَهُمْ إِلَىٰٓ أَمْوَٰلِكُمْ` `4:2`): Yetimlerin mallarını kendi mallarınıza katıp eriterek tüketmeyin."
            if (s, a) == (4, 6):
                return "Yetim malı sınır dengesi (`4:6`): Acele ve savurganlıkla (`إِسْرَافًا وَبِدَارًا`) tüketme yasağına karşılık, muhtaç vasinin örfe uygun (`بِٱلْمَعْرُوفِ`) ölçülü pay alması."
            return "Haksız ekonomik tüketim yasağı (`2:188`, `2:275`, `3:130`, `4:29`, `9:34`): Karşılıklı rıza ve üretim olmadan faizle veya asılsız yöntemlerle (`بِٱلْبَٰطِلِ`) başkalarının emeğini eksiltip sömürme."
        if (s, a) == (49, 12):
            return "Sosyal onuru kemirme benzetmesi (`أَن يَأْكُلَ لَحْمَ أَخِيهِ مَيْتًا` `49:12`): Arkadan çekiştirme/gıybetin, savunmasız ölü kardeşin etini parça parça koparıp kemirmek gibi tiksindirici bir tüketme olması."
        if (s, a) in ((12, 13), (12, 14), (12, 17), (12, 36), (12, 41), (12, 43), (12, 46), (12, 47), (12, 48)):
            if (s, a) in ((12, 43), (12, 46), (12, 47), (12, 48)):
                return "Kıtlık ekonomisi ve stok erimesi (`12:43-48`): Cılız ineklerin semizleri yemesi rüyası üzerinden yedi kurak yılın, önceki birikimi (`يَأْكُلْنَ مَا قَدَّمْتُمْ`) tüketip bitirmesi."
            return "Yûsuf kıssasında yırtıcı/kuş tüketimi (`12:13,14,17,36,41`): Kurdun veya kuşların canlıyı ya da ekmeği parçalayıp yemesi."
        if (s, a) in ((2, 35), (7, 19), (20, 121)):
            return "İlk insan çiftinin sınavı (`2:35`, `7:19`, `20:121`): Geniş nimet alanından serbestçe yeme izni karşısında yasak ağaca yaklaşma sınırının aşılması (`فَأَكَلَا مِنْهَا`)."
        if (s, a) in ((5, 75), (21, 8), (23, 33), (25, 7), (25, 20), (37, 91)):
            if (s, a) == (37, 91):
                return "Sahte sığınakların acizliği (`أَلَا تَأْكُلُونَ` `37:91`): İbrâhim'in, önlerine konan yiyeceği bile tüketip eksiltemeyen cansız putlara yönelttiği mantık sorgusu."
            return "Elçilerin biyolojik insanlığı (`يَأْكُلُ ٱلطَّعَامَ` `5:75`, `21:8`, `23:33`, `25:7,20`): Bütün elçilerin besin alıp tüketen ölümlü insanlar olduğunun ilanı."
        if (s, a) in ((2, 187), (22, 28), (22, 36), (24, 61)):
            if (s, a) == (2, 187):
                return "Öz denetim öncesi serbestlik sınırı (`وَكُلُوا۟ وَٱشْرَبُوا۟` `2:187`): Fecir çizgisi ayrılana dek yiyip içme ve ardından geceye kadar tüketimden kendini tutma (`صِيَام`)."
            if (s, a) == (24, 61):
                return "Toplumsal güven ve sofra hukuku (`24:61`): Yakın akraba ve dost evlerinde veya topluca/ayrı ayrı yemek yemenin sorumluluk darlığından çıkarılması."
            return "Paylaşımlı rızık dengesi (`فَكُلُوا۟ مِنْهَا وَأَطْعِمُوا۟` `22:28,36`): Kendi payından yerken çaresiz yoksulu ve isteyeni de doyurma ilkesi."
        if (s, a) in ((7, 73), (11, 64), (16, 69)):
            if (s, a) == (16, 69):
                return "Bal arısının doğa görevi (`ثُمَّ كُلِى مِن كُلِّ ٱلثَّمَرَٰتِ` `16:69`): Arının her tür meyve/çiçek özünden beslenerek şifalı bala dönüştürmesi."
            return "Sâlih'in devesinin yaşama hakkı (`فَذَرُوهَا تَأْكُلْ فِىٓ أَرْضِ ٱللَّهِ` `7:73`, `11:64`): İşaret niteliğindeki canlının Allah'ın toprağında serbestçe otlama hakkı."
        if (s, a) in ((5, 3), (6, 118), (6, 119), (6, 121), (6, 141), (7, 31)):
            if (s, a) == (6, 141):
                return "Hasat hukuku ve israf sınırı (`6:141`): Meyveden yiyip aynı gün hakkını vermeyi emreden ve ölçüsüz tüketimi (`وَلَا تُسْرِفُوٓا۟`) yasaklayan ilke."
            if (s, a) == (7, 31):
                return "Ölçülü yaşam kuralı (`وَكُلُوا۟ وَٱشْرَبُوا۟ وَلَا تُسْرِفُوٓا۟` `7:31`): Beslenme özgürlüğünü israf yasağıyla dengeleyen evrensel ölçü."
            return "Helal-haram beslenme bilinci (`5:3`, `6:118,119,121`): Yalnızca temiz ve Allah'ın adı anılarak meşrulaştırılan gıdaların tüketilmesi, darda kalma istisnası."
        if (s, a) in ((15, 3), (47, 12), (69, 37), (77, 46)):
            if (s, a) == (69, 37):
                return "Sorumsuzluğun acı sonucu (`لَّا يَأْكُلُهُۥٓ إِلَّا ٱلْخَٰطِـُٔونَ` `69:37`): Ağır sapmaya düşenlerin besini olan yakıcı yıkım artığı."
            return "Hesapsız dünya tüketimi uyarısı (`15:3`, `47:12`, `77:46`): Gerçeği örtenlerin amaçsızca hayvanlar gibi yiyip geçici haz sürmesinin geçiciliği."
        if (s, a) in ((52, 19), (69, 24), (77, 43), (43, 73)):
            return "Esenlik yurdunda emek karşılığı sofra (`كُلُوا۟ وَٱشْرَبُوا۟ هَنِيٓـًٔۢا` `43:73`, `52:19`, `69:24`, `77:43`): Geçmişte işlenen yararlı eylemlere karşılık afiyet ve bollukla beslenme."
        return "Yeryüzü, deniz, tarım ve hayvan nimetlerinden temiz ve helal olanı (`حَلَٰلًا طَيِّبًا`) şükür ve ölçüyle tüketip beslenme (`2:57,58,60,168,172`, `5:4,66,88,113`, `6:142`, `8:69`, `10:24`, `16:5,14,114`, `19:26`, `20:54,81`, `23:19,21,33,51`, `32:27`, `34:15`, `35:12`, `36:33,35,72`, `40:79`, `51:27`, `67:15`)."

    if root_ar == 'ح-س-ب':
        if lemma == 'HusobaAn':
            if (s, a) == (18, 40):
                return "Ölçülü gök darbesi (`حُسْبَانًا مِّنَ ٱلسَّمَآءِ` `18:40`): Kibirli bağ sahibinin bahçesini kaygan düzlüğe çeviren, gökten indirilmiş hesaplı darbe/afet."
            return "Kozmik hesap düzeni (`6:96`, `55:5`): Güneş ve ayın şaşmaz bir matematiksel ölçü ve döngü hesabı (`حُسْبَانًا / بِحُسْبَانٍ`) ile seyretmesi."
        if lemma == 'Ha`sibiyn':
            return "En hızlı ve şaşmaz hesap görücü (`6:62`, `21:47`): Hardal tanesi ağırlığındaki en küçük eylemi dahi adalet terazilerine getirip hesap görmede Allah'ın mutlak yetkinliği."
        if lemma == 'Hasiyb':
            if (s, a) == (17, 14):
                return "Öz-muhasebe (`كَفَىٰ بِنَفْسِكَ ٱلْيَوْمَ عَلَيْكَ حَسِيبًا` `17:14`): İnsanın kendi kayıt kitabını okuyarak kendine karşı bizzat hesap görücü olarak yetmesi."
            return "Kayıt ve denetim otoritesi (`4:6`, `4:86`, `33:39`): Yetim malı tesliminden en küçük selam karşılığına kadar her şeyi eksiksiz kayda alıp hesabını soran."
        if lemma == 'Hasob':
            if (s, a) in ((2, 206), (5, 104), (9, 68), (58, 8)):
                return "Yıkıcı veya yanlış yeterlilik (`2:206`, `5:104`, `9:68`, `58:8`): Gerçeği örtme ve kibre karşılık yakıcı yıkım yurdunun yetmesi veya 'atalarımızın yolu bize yeter' diyerek hakikate kapanma."
            return "Tek gerçek dayanak ve tam yeterlilik (`حَسْبُنَا / حَسْبُكَ / حَسْبِىَ / فَهُوَ حَسْبُهُۥٓ` `3:173`, `8:62,64`, `9:59,129`, `39:38`, `65:3`): Allah'a dayanan için başka destek aramaya gerek kalmaması."
        if lemma == 'HaAsabo':
            return "III. bab karşılıklı muhasebe (`2:284`, `65:8`, `84:8`): İnsanın açık-gizli tüm yaptıklarıyla yüzleştirilmesi, azgın kentlerin çetin (`حِسَابًا شَدِيدًا`) veya sağdan verilenin kolay (`حِسَابًا يَسِيرًا`) muhasebeden geçmesi."
        if lemma == 'yaHotasibu':
            return "VIII. bab öngörü dışı tecelli (`مِنْ حَيْثُ لَا يَحْتَسِبُ / لَمْ يَحْتَسِبُوا۟` `39:47`, `59:2`, `65:3`): İnsanların kendi zihin defterlerine ve beklentilerine hiç katmadıkları yerden rızık veya sarsıcı gerçeğin gelmesi."
        if lemma == 'HisaAb':
            if (s, a) == (78, 36):
                return "Sıfat anlamıyla tam yeterlilik (`عَطَآءً حِسَابًا` `78:36`): Rabbin katından hak edilmiş emeği eksiksiz karşılayıp doyuran yeterli ve cömert bağış."
            if (s, a) in ((10, 5), (17, 12)):
                return "Matematiksel zaman bilgisi (`عَدَدَ ٱلسِّنِينَ وَٱلْحِسَابَ` `10:5`, `17:12`): Ayın evreleri ve gece-gündüz dönüşüyle yılların sayımının ve vakit hesabının öğrenilmesi."
            if (s, a) in ((2, 212), (3, 27), (3, 37), (24, 38), (38, 39), (40, 40)):
                return "Sınırsız ve hesapsız akış (`بِغَيْرِ حِسَابٍ`): Yaratıcı Kudret'in dilediğine ve yararlı eylem sahiplerine daraltma ve sayı sınırı olmaksızın rızık ve karşılık vermesi."
            if (s, a) in ((6, 52), (6, 69), (13, 40), (23, 117), (26, 113), (88, 26)):
                return "Sorumluluk sınırlarının ayrımı (`6:52,69`, `13:40`, `23:117`, `26:113`, `88:26`): Hiç kimsenin başkasının hesabından sorumlu olmaması ve elçinin görevinin yalnızca bildiri olup hesabın Allah'a aitliği."
            if (s, a) in ((69, 20), (69, 26)):
                return "Bireysel kayıtla yüzleşme (`حِسَابِيَهْ` `69:20,26`): Kitabı sağdan alanın hesabıyla buluşmayı bilmesi ile soldan alanın 'keşke hesabımı hiç bilmeseydim' pişmanlığı."
            return "Hızlı ve adil eylem muhasebesi (`سَرِيعُ ٱلْحِسَابِ`, `يَوْمُ ٱلْحِسَابِ`, `سُوٓءُ ٱلْحِسَابِ`, `فَوَفَّىٰهُ حِسَابَهُۥ`): Herkesin kendi ürettiğinin eksiksiz dökümüyle yüzleşmesi (`2:202`, `3:19,199`, `5:4`, `13:18,21,41`, `14:41,51`, `21:1`, `24:39`, `38:16,26,53`, `40:17,27`, `65:8`, `78:27`, `84:8`)."
        if (s, a) in ((3, 169), (3, 178), (3, 180), (3, 188), (8, 59), (14, 42), (14, 47), (24, 11), (24, 57)):
            return "Yanılgı uyarısı (`لَا تَحْسَبَنَّ / لَا يَحْسَبَنَّ` `3:169,178,180,188`, `8:59`, `14:42,47`, `24:11,57`): Tek taraflı yüzeysel hesaba kapılıp gerçeğin tersini sanmama konusunda kesin uyarı."
        if (s, a) in ((18, 18), (24, 39), (27, 44), (27, 88), (76, 19)):
            return "Dış görünüş yanılgısı (`18:18`, `24:39`, `27:44,88`, `76:19`): Uyuyanları uyanık, serabı su, cam zemini derin su, yürüyen dağları sabit veya hizmetçileri saçılmış inci sanma gibi duyusal hesap yanılması."
        return "Zihinde tek yönlü hesabını çıkarıp sanmak (`حَسِبَ` `2:214,273`, `3:78,142`, `5:71`, `7:30`, `9:16`, `18:9,102,104`, `23:55,115`, `24:15`, `25:44`, `29:2,4`, `33:20`, `43:37,80`, `45:21`, `47:29`, `58:18`, `59:14`, `63:4`, `75:3,36`, `90:5,7`, `104:3`): karşı ihtimali dışarıda bırakarak yanlış varsayımda bulunma."

    if root_ar == 'ف-ع-ل':
        if lemma == 'fiEol':
            return "Masdar hapaxı (`فِعْلَ ٱلْخَيْرَٰتِ` `21:73`): Hayırları yalnızca niyet ya da söz olarak bırakmayıp dış dünyada fiilen icra etme sorumluluğu."
        if lemma == 'faEolat':
            return "Binâ-yı merre hapaxı (`وَفَعَلْتَ فَعْلَتَكَ ٱلَّتِى فَعَلْتَ` `26:19`): Tek ayette üç kez kökü tekrarlayarak Mûsâ'nın geçmişteki tekil somut olayını vurgulaması."
        if lemma == 'faE~aAl':
            return "Mutlak İrade'nin eylem sıfatı (`فَعَّالٌ لِّمَا يُرِيدُ` `11:107`, `85:16`): İstediği şeyi arada hiçbir engel olmadan kesintisiz olguya dönüştüren."
        if lemma == 'mafoEuwl':
            return "Kesin gerçekleşme sıfatı (`مَفْعُولًا` `4:47`, `8:42,44`, `17:5,108`, `33:37`, `73:18`): Verilmiş kararın veya sözün mutlaka fiilî gerçekliğe dönüşmesi."
        if lemma == 'faAEil':
            if (s, a) in ((21, 79), (21, 104)):
                return "Kozmik ve tarihsel icra beyanı (`وَكُنَّا فَٰعِلِينَ / إِنَّا كُنَّا فَٰعِلِينَ` `21:79,104`): Yaratıcı Kudret'in dağları-kuşları buyruk altına almayı ve ilk yaratılışı geri çevirmeyi bizzat gerçekleştirmesi."
            if (s, a) == (18, 23):
                return "Gelecek eylem iddiası sınırı (`إِنِّى فَاعِلٌ ذَٰلِكَ غَدًا` `18:23`): İnsanın Allah'ın dilemesine bağlamadan 'yarın kesin yapacağım' dememesi."
            if (s, a) == (23, 4):
                return "Paylaşımı eyleme geçirme (`لِلزَّكَوٰةِ فَٰعِلُونَ` `23:4`): Arınma ve gelişme payını sözde bırakmayıp fiilen yerine getirenler."
            return "Bir eylemi fiilen gerçekleştirmeye yönelme (`فَٰعِلِينَ` `12:10,61`, `15:71`, `21:17,68`): Kararlılık veya niyet sınaması."
        if 'PASS' in features:
            return "Edilgen eylem ve sonuç (`34:54`, `46:9`, `75:25`): Geçmiş benzerlerine yapılan müdahale (`فُعِلَ`), gelecekte başa gelecek belirsiz durum (`مَا يُفْعَلُ بِى`) veya belkemiğini kıran yıkım olgusu (`يُفْعَلَ`)."
        if (s, a) in ((61, 2), (61, 3), (26, 226)):
            return "Söz-eylem tutarlılığı turnusolü (`61:2-3`, `26:226`): Dille söylenen (`قَوْل`) ile dış dünyada fiilen gerçekleştirilen (`فِعْل`) arasındaki çelişkinin reddi."
        if (s, a) in ((2, 85), (2, 234), (22, 14), (27, 88), (39, 70), (58, 13)):
            return "Furûk eşleşmesi (`2:85,234`, `22:14`, `27:88`, `39:70`, `58:13`): Aynı ayette `فِعْل` (tekil somut vaka/etki) ile `عَمَل` (sürekli sorumluluk işi) veya `صُنْع` (kusursuz ustalık) ayrımının görülmesi."
        if (s, a) in ((2, 24), (2, 279), (5, 67), (8, 73)):
            return "Acizlik veya yükümlülük koşulu (`2:24,279`, `5:67`, `8:73`): İstenen eylemi yapamama (`فَإِن لَّمْ تَفْعَلُوا۟ وَلَن تَفْعَلُوا۟`) veya yapmama halinde doğacak sistemik sonuçlar."
        if (s, a) in ((2, 68), (16, 50), (22, 77), (37, 102), (66, 6)):
            return "Buyruğu fiilen uygulama (`فَٱفْعَلُوا۟ مَا تُؤْمَرُونَ / ٱفْعَلْ مَا تُؤْمَرُ / وَٱفْعَلُوا۟ ٱلْخَيْرَ`): Talimatı tartışıp ertelemeden doğrudan eyleme dökme."
        if (s, a) in ((2, 253), (3, 40), (4, 147), (14, 27), (21, 23), (22, 18), (30, 40), (89, 6), (105, 1)):
            return "Yaratıcı Kudret'in fiilî tasarrufu (`يَفْعَلُ مَا يَشَآءُ / يُرِيدُ`, `لَا يُسْـَٔلُ عَمَّا يَفْعَلُ`, `كَيْفَ فَعَلَ رَبُّكَ`): İradesini engelsiz gerçekleştirme ve tarihsel müdahaleler."
        return "İnsanın bireysel, hukukî, ahlakî veya toplumsal alanda yaptığı somut eylem ve davranış (`فَعَلَ - يَفْعَلُ`), sonuçta her yaptığının tam kayda alınıp bilinmesi."

    if root_ar == 'أ-ج-ر':
        if lemma in ('ta>ojura', '{sota_#ojaro'):
            return "İş sözleşmesi kökü (`28:26-27`): Şuayb'ın kızının 'onu bedelle istihdam et (`ٱسْتَـْٔجِرْهُ`)' önerisi ve babanın sekiz yıllık emek anlaşması (`عَلَىٰٓ أَن تَأْجُرَنِى`)."
        if (s, a) in ((4, 24), (4, 25), (5, 5), (33, 50), (60, 10)):
            return "Evlilik hukuku bedeli (`أُجُورَهُنَّ` `4:24,25`, `5:5`, `33:50`, `60:10`): Nikâh akdiyle kadınlara ödenmesi farz kılınan maddî hak ve güvence bedeli."
        if (s, a) in ((18, 77), (28, 25), (65, 6)):
            return "Somut hizmet ücreti (`18:77`, `28:25`, `65:6`): Duvar onarımı, suvarma işçiliği veya boşanma sonrası çocuğunu emzirme emeği karşılığı ödenen ücret (`أَجْرَ / أُجُورَهُنَّ`)."
        if (s, a) in ((7, 113), (26, 41)):
            return "Çıkar beklentisi (`إِنَّ لَنَا لَأَجْرًا` `7:113`, `26:41`): Firavun'un sihirbazlarının galibiyet karşılığında peşin ücret talep etmesi."
        if (s, a) in ((6, 90), (10, 72), (11, 29), (11, 51), (12, 104), (25, 57), (26, 109), (26, 127), (26, 145), (26, 164), (26, 180), (34, 47), (36, 21), (38, 86), (42, 23), (52, 40), (68, 46)):
            return "Elçilerin ücret reddi (`لَآ أَسْـَٔلُكُمْ عَلَيْهِ أَجْرًا` / `إِنْ أَجْرِىَ إِلَّا عَلَى ٱللَّهِ`): Hakikat çağrısının hiçbir maddî borç ve bedel karşılığı yapılmaması, emeğin karşılığının yalnızca Allah'a aitliği."
        if (s, a) in ((3, 171), (7, 170), (9, 120), (11, 115), (12, 56), (12, 90), (18, 30)):
            return "Zayi olmayan hak ediş (`لَا يُضِيعُ أَجْرَ ٱلْمُحْسِنِينَ / ٱلْمُؤْمِنِينَ / ٱلْمُصْلِحِينَ`): Emek, sebat ve iyilik çabasının asla boşa çıkarılmaması."
        if (s, a) in ((41, 8), (68, 3), (84, 25), (95, 6)):
            return "Kesintisiz karşılık (`أَجْرٌ غَيْرُ مَمْنُونٍ` `41:8`, `68:3`, `84:25`, `95:6`): Kesintiye uğratılmayan, başa kakılmayan kalıcı hak ediş."
        if (s, a) in ((3, 57), (3, 185), (4, 173), (35, 30), (39, 10)):
            return "Tam ödeme ve artı lütuf (`يُوَفِّيهِمْ أُجُورَهُمْ` `3:57,185`, `4:173`, `35:30`, `39:10`): Emeğin denk bedelinin eksiksiz verilip ayrıca Allah'ın lütfuyla (`فَضْل`) artırılması."
        return "Güvene ermenin, yararlı işlerin, hicretin, affedip düzeltmenin (`42:40`) veya sebatın (`28:54`, `33:31`) Allah katındaki onarıcı ve hak edilmiş karşılığı (`أَجْر`)."

    if root_ar == 'و-ج-د':
        if lemma == 'wujod':
            return "İsim hapaxı (`مِن وُجْدِكُمْ` `65:6`): Boşanmış kadının barındırılmasında dayanak olan eldeki maddî imkân, güç ve varlık genişliği."
        if 'PASS' in features:
            return "Edilgen fiil hapaxı (`وُجِدَ فِى رَحْلِهِۦ` `12:75`): Yükler açılıp arandığında suç delilinin somut olarak birinin eşyası içinde bulunması."
        if (s, a) == (24, 39):
            return "Sanı vs gerçeklik çarpışması (`24:39`): Susayanın uzaktan su sandığı (`يَحْسَبُهُ`) serabın yanına varınca hiçbir şey bulamaması (`لَمْ يَجِدْهُ شَيْـًٔا`) ve hemen yanı başında hesabını eksiksiz ödeyen Allah'ı bulması (`وَوَجَدَ`)."
        if (s, a) in ((17, 77), (33, 62), (35, 43), (48, 23)):
            return "Değişmez ilâhî yasa (`لَن تَجِدَ لِسُنَّةِ ٱللَّهِ تَبْدِيلًا / تَحْوِيلًا`): Tarih boyunca işleyen yasalarda keyfî değişme veya sapma bulunamaması."
        if (s, a) in ((5, 104), (7, 28), (10, 78), (21, 53), (26, 74), (31, 21), (43, 22), (43, 23), (43, 24)):
            return "Kör gelenek argümanı (`وَجَدْنَا عَلَيْهِ ءَابَآءَنَا`): Hakikat yerine ataları hangi yaşam biçimi üzerinde bulduklarını tek ölçü sayma yanılgısı."
        if (s, a) in ((2, 110), (3, 30), (18, 49), (73, 20)):
            return "Eylemin hazır bulunması (`تَجِدُوهُ عِندَ ٱللَّهِ`, `مُحْضَرًا / حَاضِرًا`): Yapılan her iyi ya da kötü işin sonuç anında insanın önünde somutlaşmış olarak bulunması."
        if (s, a) in ((93, 6), (93, 7), (93, 8)):
            return "Duhâ onarım üçlüsü (`93:6-8`): Seni yetim, yolunu arar (`ضَآلًّا`) ve darlık içinde bulup (`وَوَجَدَكَ`) barındırması, yön vermesi ve zengin kılması."
        if (s, a) in ((18, 69), (28, 27), (37, 102), (38, 44)):
            return "Karakter ve sebat tespiti (`سَتَجِدُنِىٓ` / `إِنَّا وَجَدْنَٰهُ صَابِرًا`): Sınama ve sorumluluk anında kişinin sebatkâr, dirençli ve güvenilir olduğunun fiilen tespit edilmesi."
        if (s, a) in ((2, 196), (2, 283), (4, 43), (4, 92), (5, 6), (5, 89), (9, 91), (9, 92), (24, 33), (58, 4), (58, 12), (65, 6)):
            return "İmkân veya nesne yokluğunda çözüm (`فَلَمْ تَجِدُوا۟ / فَمَن لَّمْ يَجِدْ / لَا يَجِدُونَ`): Su, binek, özgürleştirilecek köle veya infak imkânı bulunamadığında hukukî ve ahlakî alternatifin devreye girmesi."
        if (s, a) in ((12, 65), (12, 79), (12, 94), (18, 65), (18, 77), (18, 86), (18, 90), (18, 93), (20, 10), (27, 23), (27, 24), (28, 15), (28, 23), (72, 8), (72, 9)):
            return "Yolculuk ve duyusal karşılaşma (`فَوَجَدَ / فَوَجَدَا / لَأَجِدُ رِيحَ يُوسُفَ`): Yolda bir topluluk, duvar, ateş üstünde yol gösterici, gökte koruma veya uzaktan koku gibi doğrudan olguyu/duyuyu bulmak."
        return "Gözlem, arayış, sınama veya hesap anında bir niteliği (`4:82`, `5:82`, `59:9`), bir çıkış yolunu veya yardımcı/sığınağı (`4:88,145`, `17:97`, `18:17`, `72:22`) hazır halde bulmak ya da bulamamak."

    if root_ar == 'ع-د-و':
        if lemma == 'Eudowap':
            return "Fizikî mekân çapası (`بِٱلْعُدْوَةِ ٱلدُّنْيَا / ٱلْقُصْوَى` `8:42`): Bedir vadisinin iki karşıt kenarında/yamacında konumlanma — kökün somut mekân ve karşı saf anlamını doğrulayan coğrafî kök kullanım."
        if lemma == 'Ea`diya`t':
            return "Fizikî koşu hapaxı (`وَٱلْعَٰدِيَٰتِ ضَبْحًا` `100:1`): Soluk soluğa ileri atılıp sınırı yararak koşanlar."
        if lemma == 'yaEodu':
            if (s, a) == (18, 28):
                return "Bakış sınırı uyarısı (`وَلَا تَعْدُ عَيْنَاكَ عَنْهُمْ` `18:28`): Dünya süsüne yönelerek gözlerini mütevazı odak halkasından öteye taşırmaman uyarısı."
            return "Cumartesi sınırı ihlali (`4:154`, `7:163`): Sebt günü koyulan yasağı I. bab fiille aşmak (`لَا تَعْدُوا۟ / إِذْ يَعْدُونَ`)."
        if lemma == 'EaAdayo':
            return "Tersinir dönüşüm hapaxı (`عَسَى ٱللَّهُ أَن يَجْعَلَ بَيْنَكُمْ وَبَيْنَ ٱلَّذِينَ عَادَيْتُم مِّنْهُم مَّوَدَّةً` `60:7`): III. bab tek geçişinde önceden karşı safta düşmanlaşılan kimselerle bile sevgi bağı kurulabilmesi."
        if lemma == 'yataEad~a':
            return "Sınır taşımı yasası (`وَمَن يَتَعَدَّ حُدُودَ ٱللَّهِ` `2:229`, `4:14`, `65:1`): V. babın üç ayetinin tamamında aile ve hukuk sınırlarını (`حُدُودَ ٱللَّهِ`) aşan kişinin doğrudan kendi benliğine yazık edeceği uyarısı."
        if (s, a) in ((2, 190), (2, 193), (2, 194)):
            return "Çatışmada ölçülülük yasası (`2:190,193,194`): Sınırı aşmayın (`وَلَا تَعْتَدُوٓا۟`), zalimler dışına düşmanlık (`عُدْوَٰنَ`) yoktur ve saldırıya ancak kendi saldırı ölçüsü kadar (`بِمِثْلِ مَا ٱعْتَدَىٰ`) karşılık verilir."
        if (s, a) in ((2, 173), (6, 145), (16, 115), (23, 7), (70, 31)):
            return "Furûk ölçütü (`غَيْرَ بَاغٍ وَلَا عَادٍ` / `هُمُ ٱلْعَادُونَ`): Darda kalındığında taşkın arzu (`ب-غ-ي`) taşımadan ve zorunlu yaşam sınırını (`ع-د-و`) aşmadan hareket etmek; meşru eş sınırını aşanlarınsa `عَادُونَ` olması."
        if lemma in ('Eudowa`n', 'muEotadiyn', 'muEotad') or lemma == '{EotadaY`':
            return "Haddi çiğneme ve taşkınlık (`ٱعْتَدَىٰ / عُدْوَٰن / مُعْتَدٍ`): İçsel çöküşle (`إِثْم`) birlikte toplumsal düzeni, hukuku, boşanma ve ahit ilkelerini veya yeme ve temiz nimet ölçüsünü aşmak (`2:85,231`, `5:2,87`, `50:25`, `58:8-9`, `68:12`)."
        if (s, a) in ((3, 103), (5, 14), (5, 64), (5, 82), (5, 91), (41, 34), (60, 4)):
            return "Karşıtlaşma veya onarılan düşmanlık (`عَدَاوَة / أَعْدَآء`): Ayrılık, söz unutma veya kışkırtma sonucu ortaya çıkan düşmanlık (`5:14,64,91`, `60:4`) ile iyilik ve uzlaştırmanın o düşmanlığı sıcak dostluk ve kardeşliğe dönüştürmesi (`3:103`, `41:34`)."
        return "Karşı safa geçen açık düşman (`عَدُوّ / أَعْدَآء`): İnsanı yoldan çıkaran saptırıcı güç (`2:168`, `12:5`, `35:6`, `36:60`), Allah ve elçilerinin düşmanları (`2:98`, `9:114`, `25:31`, `41:19`), iki yüzlü iç tehdit (`63:4`) veya insanı haktan alıkoyabilen yakın çevre imtihanı (`64:14`)."

    if root_ar == 'ر-ج-ع':
        if lemma == 'yataraAjaEa':
            return "Aile hukuku hapaxı (`أَن يَتَرَاجَعَآ` `2:230`): İki boşama ve yeni evlilik sürecinden sonra, Allah'ın sınırlarını koruyacaklarını öngörmeleri koşuluyla eşlerin karşılıklı rızayla yeniden birbirine dönmesi."
        if lemma == 'r~ujoEaY`^':
            return "Nihaî dönüş hapaxı (`إِنَّ إِلَىٰ رَبِّكَ ٱلرُّجْعَىٰٓ` `96:8`): Kendi kendine yettiğini sanan azgın insana karşı bütün varoluşun mutlak dönüşünün Rabbine ait olduğu gerçeği."
        if lemma == 'rajoE':
            return "Döngüsel ve biyolojik geri getirme (`رَجْع` `50:3`, `86:8,11`): Göğün buharı yağmurla geri döndürmesi (`86:11`) gibi, insanın da öldükten sonra çıktığı özden tekrar geri döndürülmesi (`86:8`), ancak kör bakanların bunu uzak sayması (`50:3`)."
        if (s, a) in ((67, 3), (67, 4), (56, 87), (60, 10)):
            return "Geçişli fiil olarak geri çevirme (`فَٱرْجِعِ ٱلْبَصَرَ`, `تَرْجِعُونَهَآ`, `لَا تَرْجِعُوهُنَّ`): Gözün göğü tekrar taraması (`67:3-4`), canı geri çevirmeye güç yetirilememesi (`56:87`) veya muhacir kadınların gerçeğin üzerini örtenlere iade edilmemesi (`60:10`)."
        if (s, a) in ((20, 89), (27, 28), (27, 35), (34, 31)):
            return "Söz ve yanıt iadesi (`يَرْجِعُ قَوْلًا`, `بِمَ يَرْجِعُ`, `يَرْجِعُ بَعْضُهُمْ إِلَىٰ بَعْضٍ ٱلْقَوْلَ`): Heykelin tek söz bile döndürememesi (`20:89`), elçilerin nasıl bir yanıtla döneceği (`27:35`) veya suçluların huzurda suçu birbirine paslayıp söz çevirmesi (`34:31`)."
        if (s, a) in ((21, 64), (89, 28), (2, 46), (2, 156), (23, 60)):
            return "Bilinçli ve gönüllü yöneliş (`فَرَجَعُوٓا۟ إِلَىٰٓ أَنفُسِهِمْ` `21:64`, `رَاضِيَةً مَّرْضِيَّةً` `89:28`, `إِنَّا لِلَّهِ وَإِنَّآ إِلَيْهِ رَٰجِعُونَ`): İnsanın iç muhasebesine dönmesi ve Rabbe gönül huzuruyla dönenlerin bilinci."
        if (s, a) in ((23, 99), (32, 12), (36, 31), (36, 50), (36, 67), (21, 95), (2, 18)):
            return "Kapanan geri dönüş eşiği (`لَا يَرْجِعُونَ` vs `رَبِّ ٱرْجِعُونِ / فَٱرْجِعْنَا`): Dünyada sağır ve kör kalıp dönmeyenlerin (`2:18`) ölüm ve yıkım sonrası (`21:95`, `23:99`, `32:12`, `36:31,50,67`) dünyaya geri dönüş kapısının kapanması."
        if (s, a) in ((3, 72), (7, 168), (7, 174), (12, 62), (21, 58), (30, 41), (32, 21), (43, 28), (43, 48), (46, 27)):
            return "Umut kapısı kalıbı (`لَعَلَّهُمْ يَرْجِعُونَ`): Sıkıntı, uyarı, âyet açıklaması veya ikram vesilesiyle insanların düşünüp doğru çizgiye geri dönmeleri fırsatı."
        if 'PASS' in features or lemma == 'marojiE':
            return "Zorunlu nihaî iade ve hesap mercii (`تُرْجَعُونَ / يُرْجَعُونَ / مَرْجِعُكُمْ`): Bütün canlıların ve bütün işlerin (`ٱلْأُمُورُ`) insan tercihinden bağımsız olarak kaynak ve hüküm sahibine geri döndürülmesi (`2:28,210,281`, `3:55`, `10:4`, `39:7`, `41:50`)."
        return "Yolculuktan, görevden veya ziyaretten başlangıç noktasına fizikî dönüş (`رَجَعَ / رَجَعْتُمْ / ٱرْجِعُوا۟`: `2:196`, `7:150`, `9:83,94,122`, `12:46,50,63,81`, `20:40,86,91`, `21:13`, `24:28`, `27:37`, `33:13`, `57:13`, `63:8`)."

    if root_ar == 'ف-ض-ل':
        if lemma == 'yatafaD~ala':
            return "V. bab hapaxı (`يَتَفَضَّلَ عَلَيْكُمْ` `23:24`): Elçiyi 'kendi toplumunun içinde fazladan ayrıcalık ve statü elde etmeye çalışmakla' suçlayan kodamanların bakışı."
        if (s, a) == (13, 4):
            return "Doğal farklılaştırma (`وَنُفَضِّلُ بَعْضَهَا عَلَىٰ بَعْضٍ فِى ٱلْأُكُلِ` `13:4`): Aynı suyla beslenen komşu topraklarda ürün ve tat çeşitliliği — kökün tek muzâri fiil geçişi."
        if (s, a) == (2, 237):
            return "Hukukun üstünde gönüllü iyilik (`وَلَا تَنسَوُا۟ ٱلْفَضْلَ بَيْنَكُمْ` `2:237`): Ayrılıkta kesinleşmiş yarım borcun ötesine geçerek karşılıklı feragat ve ihsanı korumak."
        if (s, a) in ((2, 198), (5, 2), (16, 14), (17, 12), (17, 66), (28, 73), (30, 23), (30, 46), (35, 12), (45, 12), (62, 10), (73, 20)):
            return "Üretim ve ticaret artısı (`يَبْتَغُونَ فَضْلًا / مِن فَضْلِ ٱللَّهِ`): Gündüz emeği, deniz taşımacılığı, ticaret ve yolculukla elde edilen helâl geçim ve artı değer arayışı."
        if (s, a) in ((3, 171), (3, 174), (4, 95), (4, 173), (35, 30), (35, 32), (48, 29)):
            return "Bedel (`أَجْر`) veya orta ölçü (`مُّقْتَصِد`) üstü artış (`وَيَزِيدُهُم مِّن فَضْلِهِۦ`): Hak edilen tam karşılığın üstüne katılan artı bolluk ve katkı."
        if (s, a) in ((2, 64), (4, 83), (4, 113), (24, 10), (24, 14), (24, 20), (24, 21)):
            return "Koruyucu çatı (`لَوْلَا فَضْلُ ٱللَّهِ عَلَيْكُمْ وَرَحْمَتُهُۥ`): Hüsran, ağır azap ve kirlenmeden insanı ayakta tutup arındıran koruyucu açılım."
        if (s, a) in ((2, 47), (2, 122), (2, 253), (4, 32), (4, 34), (6, 86), (7, 140), (16, 71), (17, 21), (17, 55), (17, 70), (27, 15), (45, 16)):
            return "İşlev ve sorumluluk ayrışması (`فَضَّلَ ... عَلَى` / `فُضِّلُوا۟` / `تَفْضِيلًا`): Elçiler, toplumlar, rızık sahaları ve insanoğluna verilen donanım ve sorumluluk farklılıkları."
        if (s, a) in ((2, 268), (3, 180), (4, 37), (4, 54), (9, 28), (9, 75), (9, 76), (24, 22), (24, 32), (24, 33)):
            return "Yoksulluk korkusu, cimrilik ve kıskançlığa karşı cömertlik (`ٱلْفَقْر / ٱلْبُخْل` vs `فَضْل`): Eldeki imkân fazlalığını gizleyip biriktirmeyip ihtiyaç sahipleriyle paylaşmak."
        return "Hesapsız ve kuşatıcı açılım (`ذُو ٱلْفَضْلِ ٱلْعَظِيمِ` / `فَضْلُ ٱللَّهِ`): Kimseden izin veya tekel almadan Allah'ın dilediğine ulaştırdığı büyük nimet ve destek (`2:105`, `3:73-74`, `8:29`, `10:58,60,107`, `11:3`, `57:21,29`, `62:4`)."

    if root_ar == 'ص-ب-ر':
        if (s, a) == (18, 28):
            return "Fiziksel tutma çapası (`وَٱصْبِرْ نَفْسَكَ مَعَ ٱلَّذِينَ يَدْعُونَ رَبَّهُم` `18:28`): Geçişli emirle 'benliğini onların yanında sımsıkı tut, gözlerin öteye taşmasın (`وَلَا تَعْدُ عَيْنَاكَ`)' uyarısı."
        if lemma == '{SoTabiro':
            return "VIII. bab `ت -> ط` kalbi (`وَٱصْطَبِرْ` `19:65`, `20:132`, `54:27`): Yöneliş bağı ve gözetim sorumluluğunda ekstra irade ve çaba yüklenerek sebatla kenetlenmek."
        if (s, a) == (3, 200):
            return "Üçlü direnç mimarisi (`ٱصْبِرُوا۟ وَصَابِرُوا۟ وَرَابِطُوا۟` `3:200`): İçsel kenetlenme (I. bab), rakibe karşı dayanıklılık yarışı (III. bab hapaxı) ve sınır nöbeti (`رِبَاط`)."
        if lemma == 'Sab~aAr':
            return "Çift kutuplu denge sıfatı (`لِكُلِّ صَبَّارٍ شَكُورٍ` `14:5`, `31:31`, `34:19`, `42:33`): Darlıkta sarsılmayıp çok dirençli kalan ve genişlikte nimetin değerini çok açığa vuran kimse."
        if (s, a) in ((2, 175), (14, 21), (25, 42), (38, 6), (41, 24), (52, 16)):
            return "Nötr mekanik veya geç kalmış direnç (`2:175`, `14:21`, `25:42`, `38:6`, `41:24`, `52:16`): Ateş yolundaki pervasız cüret (`أَصْبَرَهُمْ عَلَى ٱلنَّارِ`), bâtılda ayak direme veya yıkım anında sızlanmakla farksızlaşan direniş."
        if (s, a) in ((18, 67), (18, 68), (18, 69), (18, 72), (18, 75), (18, 78), (18, 82)):
            return "Bilgi olgunlaşana dek iradeyi tutma (`18:67-82`): Bilgice kuşatılmamış olayların içyüzü açıklanana kadar acele tepkiyi kontrol altında tutabilme sınaması."
        if (s, a) in ((2, 249), (2, 250), (3, 120), (3, 125), (3, 146), (8, 46), (8, 65), (8, 66)):
            return "Çatışma ve cephe direnci (`أَفْرِغْ عَلَيْنَا صَبْرًا وَثَبِّتْ أَقْدَامَنَا`, `وَلَا تَنَٰزَعُوا۟`, `وَٱللَّهُ مَعَ ٱلصَّٰبِرِينَ`): Gevşeyip dağılmadan, korku ve sayı azlığı karşısında ayakları sabit tutma."
        if (s, a) in ((16, 126), (16, 127), (42, 43), (46, 35), (70, 5), (73, 10)):
            return "Ahlakî üstünlük ve ölçülü irade (`صَبْرًا جَمِيلًا`, `وَلَمَن صَبَرَ وَغَفَرَ`, `فَٱصْبِرْ كَمَا صَبَرَ أُو۟لُوا۟ ٱلْعَزْمِ`): Kışkırtma ve öç alma baskısı karşısında güzellikle direnip bağışlayabilmek."
        if (s, a) in ((2, 45), (2, 153), (90, 17), (103, 3)):
            return "Toplumsal ve ruhsal direnç desteği (`بِٱلصَّبْرِ وَٱلصَّلَوٰةِ` / `تَوَاصَوْا۟ بِٱلصَّبْرِ`): Zorluklarda dayanışma ve sebat bilincini karşılıklı ayakta tutmak."
        return "Zorluk, eksiklik, eziyet ve sınamalar karşısında dağılmayıp hedef ve hakikat üzerinde tutunmak, sonucunda sınırsız hak edişe (`39:10`) kavuşmak."

    if root_ar == 'أ-ذ-ن':
        if (s, a) in ((84, 2), (84, 5)):
            return "Fiziksel kulak-onay köprüsü (`وَأَذِنَتْ لِرَبِّهَا` `84:2,5`): Gök ve yerin Rabbine kulak kesilip işiterek uyum ve onay vermesi."
        if (s, a) == (9, 61):
            return "Organın şahsiyet mecazı (`هُوَ أُذُنٌ قُلْ أُذُنُ خَيْرٍ` `9:61`): 'Her duyduğuna kulak asıyor' suçlamasına karşı onun hayra ve güvene açık bir kulak olması."
        if (s, a) == (69, 12):
            return "Kavrayıcı kulak çapası (`أُذُنٌ وَٰعِيَةٌ` `69:12`): İşittiği tarihi ve uyarıyı tutup koruyan bilinçli alıcı organ."
        if (s, a) in ((2, 19), (4, 119), (5, 45), (6, 25), (7, 179), (7, 195), (17, 46), (18, 11), (18, 57), (22, 46), (31, 7), (41, 5), (41, 44), (71, 7)):
            return "Kulak organı ve duyum engeli (`ءَاذَانِهِمْ وَقْرًا`, `أَصَٰبِعَهُمْ فِىٓ ءَاذَانِهِم`, `فَضَرَبْنَا عَلَىٰٓ ءَاذَانِهِمْ`): Sağlıklı işitme aracına rağmen kulağı tıkama veya dış sese kapatma olgusu."
        if lemma in ('mu&a*~in', '>a*~ana', '>a*a`n', "'aA*an", 'ta>a*~ana') or (s, a) == (2, 279):
            return "Sesli duyuru ve ilân (`أَذَان / أَذَّنَ / ءَاذَنَ / تَأَذَّنَ / فَأْذَنُوا۟`): Açıkça ilân etme, büyük toplanma çağrısı (`22:27`), savaş bildirimi (`2:279`) veya Allah'ın kesin kararı (`14:7`)."
        if lemma == '{sota_#o*ana' or (s, a) in ((9, 43), (9, 49), (9, 90), (24, 28), (33, 53)):
            return "Toplumsal izin disiplini (`ٱسْتَأْذَنَ / يُؤْذَنَ`): Ev mahremiyetine girişte izin bekleme (`24:28,58-59`, `33:53`), ortak toplumsal işten izinsiz ayrılmama (`24:62`) ve seferden kaçış bahanesiyle izin isteme (`9:44-93`, `33:13`)."
        if (s, a) in ((2, 255), (10, 3), (20, 109), (34, 23), (53, 26), (78, 38)):
            return "Şefaat ve söz alma yetkisi (`إِلَّا بِإِذْنِهِۦ` / `مَنْ أَذِنَ لَهُ`): Hesap ve şefaat sahnesinde yalnızca Allah'ın onay verdiği kişinin konuşabilmesi."
        if (s, a) in ((10, 59), (42, 21)):
            return "Yetki ve kural koyma ölçütü (`ءَآللَّهُ أَذِنَ لَكُمْ` / `مَا لَمْ يَأْذَنۢ بِهِ ٱللَّهُ`): Allah'ın onay vermediği yasakları veya yaşam kurallarını uydurmanın reddi."
        return "Varoluşsal onay kanalı (`بِإِذْنِ ٱللَّهِ` / `أَذِنَ`): Vahyin inişi (`2:97`), Îsâ'nın göstergeleri (`3:49`, `5:110`), savunma hakkı (`22:39`), rızık/toprak verimi (`7:58`) ve olayların yalnızca ilâhî onay sınırında gerçekleşmesi."

    if root_ar == 'ش-د-د':
        if lemma == '{$otad~ato':
            return "VIII. bab hapaxı (`ٱشْتَدَّتْ بِهِ ٱلرِّيحُ` `14:18`): Fırtınalı günde rüzgârın baskısını yoğunlaştırıp külü savurması gibi temelsiz eylemlerin dağılması."
        if lemma == '$adado':
            return "Fizikî sıkılaştırma ve pekiştirme (`شَدَّ` `10:88`, `20:31`, `28:35`, `38:20`, `47:4`, `76:28`): Bağı düğümleme, eklemleri kurma, pazuyu/sırtı ve yönetimi sağlamlaştırma veya kalbi kilitleme."
        if lemma == '>a$ud~':
            return "Biyolojik-zihinsel olgunluk çağı (`بَلَغَ أَشُدَّهُۥ` `6:152`, `12:22`, `17:34`, `18:82`, `22:5`, `28:14`, `40:67`, `46:15`): İnsan bedeninin ve akıl bağlarının tam sağlamlık noktasına erişmesi."
        if (s, a) in ((48, 29), (59, 14), (100, 8), (73, 6), (78, 12), (57, 25), (12, 48), (11, 80)):
            return "Yapısal sıkılık ve karakter duruşu (`سَبْعًا شِدَادًا`, `أَشِدَّآءُ`, `لِحُبِّ ٱلْخَيْرِ لَشَدِيدٌ`, `أَشَدُّ وَطْـًٔا`): Gök katmanları, demir, gece yoğunluğu, mala sımsıkı sarılma veya dışa karşı tavizsiz duruş."
        if (s, a) in ((2, 74), (2, 165), (2, 191), (2, 200), (4, 66), (4, 77), (5, 82), (9, 69), (9, 81), (9, 97), (19, 69), (28, 78), (30, 9), (35, 44), (37, 11), (40, 21), (40, 82), (41, 15), (43, 8), (47, 13), (50, 36), (59, 13), (79, 27)):
            return "Derecelendirme ölçütü (`أَشَدُّ قُوَّةً / حُبًّا / خَلْقًا / قَسْوَةً`): Kuvvet, sevgi, yaratılış güçlüğü, kalp sertliği veya sapmada yoğunluk kıyası."
        return "Tavizsiz sonuç ve karşılık yoğunluğu (`شَدِيدُ ٱلْعِقَابِ`, `عَذَابٌ شَدِيدٌ`, `شَدِيدُ ٱلْمِحَالِ`): Kurulan düzeni bozanlara, sözü değiştirenlere ve zulümde diretenlere uygulanacak çetin hesap ve sonuç (`2:196`, `13:6,13`, `40:3`, `85:12`)."

    elif root_ar == 'و-ل-د':
        if (s, a) == (2, 233):
            return "Doğuran anne ve sorumlu baba dengesi (`2:233`): Kök bu ayette `8` kez geçerek iki yıl emziren annenin (`ٱلْوَٰلِدَٰتُ / وَٰلِدَةٌۢ`) geçim-giyim hakkını ve çocuğun kendisine doğurulduğu babanın (`ٱلْمَوْلُودِ لَهُۥ`) bakım sorumluluğunu zarar vermeme ilkesiyle kurar."
        if (s, a) == (31, 33):
            return "Bireysel hesap eşiği (`31:33` x4): Hiçbir doğuranın (`وَالِدٌ`) çocuğunun (`وَلَدِهِۦ`), hiçbir doğan çocuğun da (`مَوْلُودٌ`) doğuranının (`وَالِدِهِۦ`) yerine yüklenemeyeceği sarsılmaz sorumluluk ilkesi."
        if (s, a) == (58, 2):
            return "Biyolojik doğum gerçekliği (`58:2`): Eşlere örfî benzetmeyle 'annem' denmesini reddeder; gerçek anneliğin yalnızca bizzat doğurmuş olmaya (`إِنْ أُمَّهَٰتُهُمْ إِلَّا ٱلَّٰٓـِٔى وَلَدْنَهُمْ`) dayandığını bildirir."
        if (s, a) in ((112, 3), (37, 152)):
            return "Aşkın tek varlığın doğurmadan ve doğurulmadan bağımsızlığı (`37:152`, `112:3`): Yüce Yaratıcının biyolojik bölünme, çoğalma ve başlangıca sahip olma niteliklerinden tümüyle arınmış olması (`لَمْ يَلِدْ وَلَمْ يُولَدْ`)."
        if (s, a) == (11, 72):
            return "İleri yaşta olağanüstü doğum şaşkınlığı (`11:72`): Biyolojik doğurganlık sınırının ötesinde verilen müjde karşısındaki insanî hayret (`ءَأَلِدُ وَأَنَا۠ عَجُوزٌ`)."
        if (s, a) in ((19, 15), (19, 33)):
            return "Doğum eşiğine esenlik (`19:15`, `19:33`): Dünyaya gözlerini açtığı gün (`يَوْمَ وُلِدَ` / `وُلِدتُّ`) insana bahşedilen ilâhî koruma ve esenlik."
        if (s, a) == (71, 27):
            return "Bozulmuş nesil aktarımı uyarısı (`71:27`): Nûh'un uzun davetten sonra saptırıcı düzenden doğacak kuşakların da aynı yıkımı sürdüreceğine dair tespiti (`وَلَا يَلِدُوٓا۟`)."
        if (s, a) == (90, 3):
            return "Nesil zincirine tanıklık (`90:3`): Doğuran kuşağa ve doğurulan yeni nesle (`وَوَالِدٍ وَمَا وَلَدَ`) dikkat çekilerek insanın varoluş mücadelesi çerçevelenir."
        if (s, a) in ((12, 21), (28, 9)):
            return "Sosyal evlatlık edinme niyeti (`12:21`, `28:9`): Biyolojik doğum bağı olmaksızın Yûsuf veya Mûsâ'yı evlat konumuna alma kararı (`أَن نَّتَّخِذَهُۥ وَلَدًا`)."
        if (s, a) in ((2, 116), (3, 47), (4, 171), (6, 101), (10, 68), (17, 111), (18, 4), (19, 35), (19, 88), (19, 91), (19, 92), (21, 26), (23, 91), (25, 2), (39, 4), (43, 81), (72, 3)):
            if (s, a) == (3, 47):
                return "Biyolojik baba olmaksızın doğum hayreti (`3:47`): Meryem'in insanî sebep çerçevesinden sorduğu 'bana bir beşer dokunmamışken nasıl çocuğum (`وَلَدٌ`) olur?' sorusunun yaratma iradesiyle cevabı."
            return "Yüce Yaratıcıya çocuk/soy yakıştırmasının reddi (`ٱتَّخَذَ ٱللَّهُ وَلَدًا` / `سُبْحَٰنَهُۥ`): Gökleri ve yeri eşi olmadan yaratan Mutlak Kudretin doğurma veya evlat edinmeye hiçbir ihtiyacı olmadığı ilan edilir (`2:116`, `6:101`, `19:35,88-92`)."
        if lemma == 'waliyd':
            if s == 26:
                return "Yeni doğmuşluk hatırlatması (`26:18`): Firavun'un Mûsâ'ya henüz bebeklik/çocukluk çağından itibaren sarayda büyütüldüğünü (`وَلِيدًا`) hatırlatması."
            if s in (56, 76):
                return "Esenlik bahçesinin solmayan gençleri (`56:17`, `76:19`): Yaşlanmayan, daima taze genç hizmetliler (`وِلْدَٰنٌ مُّخَلَّدُونَ`)."
            if s == 73:
                return "Büyük sarsıntının dehşet ölçüsü (`73:17`): Küçücük çocukları dahi dehşetten ak saçlı ihtiyara çeviren hesap günü (`يَجْعَلُ ٱلْوِلْدَٰنَ شِيبًا`)."
            return "Ezilen ve savunmasız çocuklar (`4:75,98,127`): Baskı altında çaresiz kalmış erkek-kadın ve küçük çocuklar (`ٱلْوِلْدَٰنِ`) için hak ve kurtuluş sorumluluğu."
        if (s, a) in ((6, 140), (6, 151), (17, 31), (60, 12)) and lemma == 'walad':
            return "Doğmuş çocukları öldürme yasağı (`6:140,151`, `17:31`, `60:12`): Geçim veya yoksulluk korkusuyla kendi çocuklarının (`أَوْلَٰدَكُمْ`) canına kıyılmasının ağır bir sapma ve kayıp olduğu vurgulanır."
        if (s, a) in ((4, 7), (4, 11), (4, 12), (4, 33), (4, 176)):
            return "Doğum ve nesep merkezli miras hukuku (`4:7,11,12,33,176`): Ebeveynler (`ٱلْوَٰلِدَانِ`) ve çocuklar (`وَلَد / أَوْلَٰد`) arasındaki hakça pay dağıtım ölçüleri."
        if lemma in ('waAlid', 'wa`liday', 'wa`lidap'):
            return "Anne-babaya somut iyilik, vefa ve adalet (`2:83`, `4:36,135`, `6:151`, `17:23`, `31:14`, `46:15`): Hamilelik, doğum ve yetiştirme emeğine karşılık özellikle yaşlılıklarında ebeveyne hürmet, öf bile dememe, iyi davranış ve dua borcu."
        return "Mal ve çocukların sınav ve ölçü boyutu (`3:10,116`, `8:28`, `9:55`, `18:39`, `57:20`, `63:9`, `64:14-15`): Soy ve çocuk sevgisinin insanı sorumlu davranıştan saptırmaması veya kalıcı güven yerine geçmeyeceği uyarısı."

    elif root_ar == 'د-ي-ن':
        if (s, a) == (2, 282):
            return "Karşılıklı vadeli borç akdinin belgelenmesi (`2:282`): İki taraf arasında belirli vadeye bağlanan malî yükümlülüğün (`تَدَايَنتُم بِدَيْنٍ`) adaletle yazıya geçirilmesi ve şahitlendirilmesi ilkesi."
        if (s, a) in ((4, 11), (4, 12)):
            return "Miras paylaşımından önce borç tasfiyesi (`4:11`, `4:12` x3): Ölüm sonrası tereke dağıtımının ancak bırakılan vasiyet veya üstlenilmiş borçların (`أَوْ دَيْنٍ`) ödenmesinden sonra yapılabileceği hükmü."
        if (s, a) in ((37, 53), (56, 86)):
            return "Hesaba çekilip borç ödeyen sorumlu varlık (`مَدِينِينَ` `37:53`, `56:86`): İnsanın öldükten sonra başıboş kalmayacağı, yaşadığı hayatın hesabını ödemeye tabi (`مَدِين`) kılındığı vurgusu."
        if (s, a) == (12, 76):
            return "Hükümdarın yargı ve yasa düzeni (`فِى دِينِ ٱلْمَلِكِ` `12:76`): Mısır kralının hukuk sistemine göre kardeşin alıkonulamayacağı bağlamında kökün doğrudan 'yürürlükteki devlet yasası ve adlî yargı sistemi' anlamı."
        if (s, a) == (24, 2):
            return "Yaratıcının belirlediği yargı ve ceza ölçüsü (`فِى دِينِ ٱللَّهِ` `24:2`): Hukukî yaptırım uygulanırken duygusal acımanın adalet ve ilâhî yasa ölçüsünü esnetmemesi ilkesi."
        if (s, a) == (9, 29):
            return "Hak yasaya fiilen boyun eğme (`يَدِينُونَ دِينَ ٱلْحَقِّ` `9:29`): Kökün Kur'an'daki tek I. bab fiiliyle somut biçimde 'konulan hak sisteme uyup gereğini yerine getirme' eylemini belgeler."
        if (s, a) in ((1, 4), (15, 35), (24, 25), (26, 82), (37, 20), (38, 78), (51, 6), (51, 12), (56, 56), (70, 26), (74, 46), (82, 9), (82, 15), (82, 17), (82, 18), (83, 11), (95, 7), (107, 1)):
            if (s, a) == (1, 4):
                return "Hesap ve denk karşılık gününün tek mutlak yöneticisi (`مَٰلِكِ يَوْمِ ٱلدِّينِ` `1:4`): Her eylemin kayıtlı borç gibi terazide eksiksiz karşılığını bulduğu büyük yargı günü."
            if (s, a) == (24, 25):
                return "Gerçek ve eksiksiz hak karşılığı (`دِينَهُمُ ٱلْحَقَّ` `24:25`): İftira atanlara yaptıklarının şaşmaz ve tam karşılığının ödetilmesi."
            return "Hesap ve denk karşılık günü (`يَوْمُ ٱلدِّينِ / بِٱلدِّينِ` `51:6,12`, `70:26`, `82:9-18`, `95:7`, `107:1`): Eylemlerin borç-karşılık dengesiyle ödeneceği yargı günü; erdemliler onu doğrular, nankörler yalanlar."
        if (s, a) == (2, 256):
            return "İnanç ve yaşam sistemine girişte zorlamanın yasaklanması (`لَآ إِكْرَاهَ فِى ٱلدِّينِ` `2:256`): Doğru ile eğrinin apaçık ayrıldığı bilinç alanında baskıya yer olmadığı ilkesi."
        if (s, a) == (109, 6):
            return "Karşılıklı yol ve sorumluluk ayrımı (`لَكُمْ دِينُكُمْ وَلِىَ دِينِ` `109:6`): Her tarafın kendi seçtiği itaat, yaşam ve hesap sisteminin sonucunu bizzat üstleneceği beyanı."
        if (s, a) == (9, 36):
            return "Kozmik takvim ve evrensel denge yasası (`9:36`): On iki aylık gök döngüsü ve dört dokunulmaz ay düzeninin 'ayakta duran dosdoğru sistem (`ٱلدِّينُ ٱلْقَيِّمُ`)' diye nitelenmesi."
        if (s, a) in ((6, 161), (12, 40), (30, 30), (30, 43)) or ((s, a) == (98, 5) and 'NOM' in features):
            return "Fıtratla örtüşen şaşmaz yaşam sistemi (`ٱلدِّينُ ٱلْقَيِّمُ` / `فِطْرَتَ ٱللَّهِ` `30:30,43`, `12:40`, `6:161`, `98:5`): İnsanın yaratılış programıyla tam uyumlu, aracıları reddeden ayakta duran sistem."
        if (s, a) in ((2, 193), (4, 146), (7, 29), (8, 39), (10, 22), (16, 52), (29, 65), (31, 32), (39, 2), (39, 3), (39, 11), (39, 14), (40, 14), (40, 65), (98, 5)):
            return "Yönelişi ve itaat bağını yalnız Tek Kudrete arındırmak (`مُخْلِصِينَ لَهُ ٱلدِّينَ` / `وَلَهُ ٱلدِّينُ وَاصِبًا` `16:52`, `39:2-14`, `40:14,65`): Zorlukta veya kesintisiz biçimde tüm bağlılığı yalnız Yaratıcıya tahsis etme ilkesi."
        if (s, a) in ((6, 159), (30, 32), (42, 13)):
            return "Ortak yaşam sistemini parçalama yasağı (`أَقِيمُوا۟ ... وَلَا تَتَفَرَّقُوا۟` `42:13`; `فَرَّقُوا۟ دِينَهُمْ` `6:159`, `30:32`): Tek merkezli sistemi hiziplere bölerek ayrışma uyarısı."
        if (s, a) in ((2, 132), (3, 19), (3, 83), (3, 85), (4, 125), (5, 3), (9, 33), (10, 104), (10, 105), (22, 78), (24, 55), (48, 28), (61, 9), (110, 2)):
            return "Evrenin boyun eğdiği bütüncül teslimiyet ve kolaylık sistemi (`3:19,83`, `5:3`, `9:33`, `22:78`, `110:2`): Kemale erdirilen, güçlük barındırmayan ve diğer tüm beşerî düzenlere üstün kılınan hak yaşam yasası."
        if (s, a) in ((8, 72), (9, 11), (9, 122), (33, 5), (60, 8), (60, 9)):
            return "Toplumsal dayanışma, ilke kardeşliği ve adalet hukuku (`8:72`, `9:11,122`, `33:5`, `60:8-9`): Yaşam düzeninde derinleşme, kan bağı bilinmeyenlerle kardeşleşme ve saldırgan olmayanlarla barışçıl adalet ilişkisi."
        return "Yaşam ve itaat düzenini çarpıtma, küçümseme veya yetkisiz yasa uydurma (`4:46,171`, `5:57,77`, `6:70,137`, `7:51`, `40:26`, `42:21`, `49:16`): Sorumluluk sistemini oyun-eğlenceye çevirme, aşırılığa sapma veya eski düzeni koruma kaygısı."

    elif root_ar == 'ص-ح-ب':
        if (s, a) == (4, 36):
            return "Yanı başındaki fizikî arkadaş (`وَٱلصَّاحِبِ بِٱلْجَنۢبِ` `4:36`): Uzak komşudan ayrı olarak insanın bizzat omuz omuza yürüdüğü, oturduğu veya yolculuk ettiği yakın eşlikçisine iyi davranma görevi."
        if (s, a) == (18, 76):
            return "Yol arkadaşlığı sınırı (`فَلَا تُصَاحِبْنِى` `18:76` III. bab): Mûsâ'nın bilge yol arkadaşına üçüncü sorudan sonra yol arkadaşlığını bitirme koşulu koyması."
        if (s, a) == (31, 15):
            return "İlke ayrımına rağmen güzelce arkadaşlık (`وَصَاحِبْهُمَا فِى ٱلدُّنْيَا مَعْرُوفًا` `31:15` III. bab): İnançta baskı yapsalar bile anne ve babaya yanlışta uymayıp dünya ilişkisinde onurlu arkadaşlığı sürdürme dengesi."
        if (s, a) == (21, 43):
            return "Himaye ve korumadan yoksunluk (`وَلَا هُم مِّنَّا يُصْحَبُونَ` `21:43` I. bab meçhul): Sözde koruyucu odakların kendi taraftarlarını ilâhî yaptırımdan sahiplenip kurtaramayacağı uyarısı."
        if (s, a) in ((12, 39), (12, 41)):
            return "Zindan arkadaşlarına ortak mesaj (`يَٰصَىٰحِبَىِ ٱلسِّجْنِ` `12:39,41`): Yûsuf'un aynı dar mekânı paylaştığı iki tutukluya tek ve her şeye gücü yeten Yaratıcıyı anlatması."
        if (s, a) in ((6, 101), (72, 3)):
            return "Ömür eşinden münezzeh Mutlak Birlik (`وَلَمْ تَكُن لَّهُۥ صَٰحِبَةٌ` `6:101`, `72:3`): Biyolojik doğumun dişi eş (`صَٰحِبَة`) koşuluna bağlı olduğu gösterilerek Yaratıcının eş ve çocuktan arınmışlığı ilan edilir."
        if (s, a) in ((70, 12), (80, 36)):
            return "Büyük hesap anında eşten bile kaçış (`وَصَٰحِبَتِهِۦ` `70:12`, `80:36`): Korku anında insanın en yakın ömür yoldaşından bile uzaklaşıp kendi derdine düşeceği vurgusu."
        if (s, a) in ((7, 184), (34, 46), (53, 2), (81, 22)):
            return "İçlerinden yetişmiş güvenilir tanıdık arkadaş (`صَاحِبُكُمْ / بِصَاحِبِهِم` `7:184`, `34:46`, `53:2`, `81:22`): Elçiyi karalayanların gerçekte ömrü yanlarında geçmiş, akıl tutulmasından uzak yakın arkadaşlarını iyi tanıdıkları hatırlatılır."
        if (s, a) == (9, 40):
            return "Mağaradaki kritik yol arkadaşlığı (`لِصَٰحِبِهِۦ لَا تَحْزَنْ` `9:40`): Kuşatma anında iki kişiden birinin diğerini teskin ettiği ve iç huzurla desteklenen omuz omuza yoldaşlık."
        if (s, a) in ((18, 34), (18, 37)):
            return "İki bağ arkadaşının imtihanı (`لِصَٰحِبِهِۦ / صَاحِبُهُۥ` `18:34,37`): Mal ve çevre çokluğuyla övünen kişiye yol arkadaşının insanın topraktan yaratılışını hatırlatması."
        if (s, a) == (54, 29):
            return "Bozgunculuk için öne sürülen adam (`فَنَادَوْا۟ صَاحِبَهُمْ` `54:29`): Semûd toplumunun suikast için kendi içlerinden çağırıp görevlendirdiği yoldaşları."
        if (s, a) == (68, 48):
            return "Balığın karnında sıkışıp kalan Yûnus (`كَصَاحِبِ ٱلْحُوتِ` `68:48`): Bunalıp aceleci davranarak balıkla aynı yerde sıkışan arkadaş örneği üzerinden direnç öğüdü."
        if (s, a) == (6, 71):
            return "Çıkış yoluna çağıran gerçek dostlar (`لَهُۥٓ أَصْحَٰبٌ يَدْعُونَهُۥ` `6:71`): Şaşkın kalmış yolcuyu güvenilir yöne davet eden sağduyulu yol arkadaşları."
        if (s, a) == (74, 31):
            return "Ateş alanının görevli sorumluları (`أَصْحَٰبَ ٱلنَّارِ` `74:31`): Yakıcı düzenin yönetiminden sorumlu kozmik görevliler topluluğu."
        if (s, a) == (68, 17):
            return "Dünya bahçesi sahipleri kıssası (`أَصْحَٰبَ ٱلْجَنَّةِ` `68:17`): Yoksulları mahrum bırakma kararı alıp bahçelerini kaybeden mülk sahipleri örneği."
        if (s, a) in ((56, 8), (56, 9), (56, 27), (56, 38), (56, 41), (56, 90), (56, 91), (74, 39), (90, 18), (90, 19)):
            return "Sağ/uğur ehli ile sol/yıkım ehli saflaşması (`أَصْحَٰبُ ٱلْمَيْمَنَةِ / ٱلْيَمِينِ` vs `ٱلْمَشْـَٔمَةِ / ٱلشِّمَالِ` `56:8-91`, `74:39`, `90:18-19`): Eylem yönüne göre ayrılan iki zıt kader topluluğu."
        if (s, a) in ((7, 44), (7, 48), (7, 50), (59, 20)):
            return "Karşıt sonuç ehlinin yüzleşmesi (`أَصْحَٰبُ ٱلْجَنَّةِ` ve `أَصْحَٰبُ ٱلنَّارِ / ٱلْأَعْرَافِ` `7:44-50`, `59:20`): Esenlik yurdu ehli ile ateş ehlinin hiçbir biçimde denk olamayacağı ilkesi."
        if (s, a) in ((2, 82), (7, 42), (7, 46), (10, 26), (11, 23), (20, 135), (25, 24), (36, 55), (46, 14), (46, 16)):
            return "Esenlik bahçesi veya dosdoğru güzergâh ehli (`أَصْحَٰبُ ٱلْجَنَّةِ / ٱلصِّرَٰطِ ٱلسَّوِىِّ` `2:82`, `7:42`, `20:135`, `36:55`, `46:14`): Güven ve erdemli eylemleriyle kalıcı esenlik alanının sürekli sakinleri."
        if (s, a) in ((4, 47), (9, 70), (15, 78), (15, 80), (18, 9), (22, 44), (25, 38), (26, 61), (26, 176), (29, 15), (36, 13), (38, 13), (50, 12), (50, 14), (51, 59), (60, 13), (85, 4), (105, 1)):
            return "Tarihî olay ve mekân zümreleri (`أَصْحَٰبُ ٱلْكَهْفِ` `18:9`, `ٱلسَّفِينَةِ` `29:15`, `مُوسَىٰ` `26:61`, `ٱلْحِجْرِ / ٱلْأَيْكَةِ / ٱلْأُخْدُودِ / ٱلْفِيلِ` `15:78-80`, `85:4`, `105:1`): Ortak süreci, mekânı ve tarihsel kaderi paylaşan topluluklar."
        return "Kendi seçtiği yıkıcı sonucun sürekli ehli (`أَصْحَٰبُ ٱلنَّارِ / ٱلْجَحِيمِ / ٱلسَّعِيرِ` `2:39,81`, `7:36`, `67:10-11`): Gerçeği örterek ve zulümde direnerek yakıcı ateş alanının ayrılmaz sakinine dönüşen topluluk."

    elif root_ar == 'أ-ن-س':
        if (s, a) == (4, 6):
            return "Olgunluk belirtisinin açıkça sezilmesi (`فَإِنْ ءَانَسْتُم مِّنْهُمْ رُشْدًا` `4:6` IV. bab): Yetimlerde mal yönetimi ve sağduyu olgunluğunun somutça görülüp fark edilmesi halinde mallarının kendilerine teslim edilmesi."
        if (s, a) in ((20, 10), (27, 7), (28, 29)):
            return "Karanlıkta uzaktan ateş seçip sıcaklık ummak (`ءَانَسْتُ نَارًا` / `ءَانَسَ ... نَارًا` `20:10`, `27:7`, `28:29`): Mûsâ'nın gece yolculuğunda karanlığı ve yabancılığı yaran belirgin bir ateş görüp ailesine ışık ve yol bilgisi getirme hamlesi."
        if (s, a) == (24, 27):
            return "Eve girmeden seslenip ünsiyet kurmak (`حَتَّىٰ تَسْتَأْنِسُوا۟ وَتُسَلِّمُوا۟` `24:27` X. bab): Başkasının hanesine habersiz baskın yapıp ürkütmemek için önce seslenerek tanışıklık, kabul ve izin isteme ölçüsü."
        if (s, a) == (33, 53):
            return "Sözlü sohbete dalıp ortamı uzatmama adabı (`وَلَا مُسْتَـْٔنِسِينَ لِحَدِيثٍ` `33:53` X. bab ism-i fâil): Davet yemeği bittikten sonra ev sahibini yoracak biçimde lafa dalıp ünsiyet aramama inceliği."
        if (s, a) == (19, 26):
            return "Sosyal insanla sözlü temastan çekilme (`فَلَنْ أُكَلِّمَ ٱلْيَوْمَ إِنسِيًّا` `19:26`): Aynı ayetteki dış bedeni belirten `بَشَر` yanında `إِنسِيًّا` kelimesiyle 'kendisiyle konuşulup ünsiyet kurulacak kimse' ayrımı vurgulanır."
        if (s, a) in ((2, 60), (7, 82), (7, 160), (17, 71), (25, 49), (27, 56)):
            return "Ünsiyet kuran topluluklar ve halk kesimleri (`أُنَاس` & `أَنَاسِىَّ` `2:60`, `7:82,160`, `17:71`, `25:49`, `27:56`): On iki pınardan su içme yerini bilen topluluklar, önderiyle çağrılacak gruplar ve yağmurla sulanan kalabalıklar."
        if lemma == '<ins':
            return "Görünür insan zümresinin gizli/örtülü varlıklarla (`ٱلْجِنّ / جَآنّ`) simetrisi (`6:112-130`, `17:88`, `51:56`, `55:33,39`, `72:5-6`): `إِنس` sözcüğünün Kur'an'daki `18` geçişinin tamamında gözden örtülü şuurlu varlıklarla yan yana gelerek yaratılış amacı ve ortak sorumlulukta buluşması."
        if (s, a) in ((4, 28), (15, 26), (16, 4), (23, 12), (32, 7), (36, 77), (50, 16), (55, 3), (55, 14), (75, 3), (76, 1), (76, 2), (80, 24), (82, 6), (86, 5), (90, 4), (95, 4), (96, 2), (96, 5)):
            return "İnsanın biyolojik kökeni, en güzel kıvamı ve bilgi donanımı (`15:26`, `23:12`, `76:2`, `95:4`, `96:2-5`): Balçık ve karma sudan yaratılıp zayıflığına rağmen duyma-görme ve bilmediğini öğrenme yeteneğiyle şereflendirilen `ٱلْإِنسَٰن`."
        if (s, a) in ((12, 5), (17, 13), (17, 53), (25, 29), (29, 8), (31, 14), (33, 72), (46, 15), (53, 24), (53, 39), (59, 16), (75, 5), (75, 10), (75, 13), (75, 14), (75, 36), (79, 35), (84, 6), (89, 23), (99, 3)):
            return "İnsanın emaneti, çabası ve öz tanıklığı (`33:72`, `53:39`, `75:14`, `84:6`, `31:14`): Göklerin ve dağların çekindiği emaneti sırtlanan, anne-babaya vefayla sorumlu tutulan ve yalnızca kendi emeğinin karşılığını görecek olan bilinçli insan."
        return "Darlık-bolluk salınımında insanın aceleci ve nankör eğilimi uyarısı (`10:12`, `11:9`, `14:34`, `17:11,67,83`, `21:37`, `39:8,49`, `70:19`, `80:17`, `96:6`, `100:6`, `103:2`): Sıkıntıda yalvarıp ferahlıkta yüz çevirme ve nankörlüğe kayma zaaflarının teşhisi."

    elif root_ar == 'ق-ر-ب':
        if (s, a) == (51, 27):
            return "Fizikî sunum ve önüne yaklaştırma (`فَقَرَّبَهُۥٓ إِلَيْهِمْ` `51:27` II. bab): İbrâhîm'in kızartılmış yemeği bizzat misafirlerin önüne yaklaştırıp ikrama çağırması — kökün somut mekân yaklaştırması."
        if (s, a) in ((5, 27), (3, 183), (46, 28)):
            return "Yakınlık sağlamak için takdim edilen sunu (`قَرَّبَا قُرْبَانًا` `5:27`, `3:183`, `46:28`): Yaratıcıya veya yüce makama yaklaşmak amacıyla öne getirilen takdimin yalnız sorumluluk bilinciyle kabul görmesi."
        if (s, a) in ((34, 37), (39, 3)):
            return "Gerçek yakınlaşma vesilesi ile sahte aracılık ayrımı (`تُقَرِّبُكُمْ / لِيُقَرِّبُونَآ ... زُلْفَىٰ` `34:37`, `39:3`): Malın, evladın ve sözde yardımcıların değil yalnız güven ve erdemli eylemin insana gerçek yakınlık sağladığı bildirilir."
        if (s, a) == (9, 99):
            return "Harcamaların yakınlaşma adımlarına dönüşmesi (`قُرُبَٰتٍ ... أَلَآ إِنَّهَا قُرْبَةٌ` `9:99`): Maddi paylaşımın samimi niyetle gerçek bir yakınlık bağına (`قُرْبَة`) dönüşmesi."
        if (s, a) == (19, 52):
            return "Seçkin elçiyi yakın konuşmaya çekme (`وَقَرَّبْنَٰهُ نَجِيًّا` `19:52` II. bab): Tûr'un sağ yanından seslenilen Mûsâ'nın özel sırdaş yakınlığına alınması."
        if (s, a) == (96, 19):
            return "Bilinçle boyun eğerek yaklaşma çağrısı (`وَٱسْجُدْ وَٱقْتَرِب` `96:19` VIII. bab emir): Baskıcı zorbalara uymayıp alçalarak ve içtenlikle Yaratıcıya yaklaşma emri."
        if (s, a) in ((2, 35), (2, 187), (2, 222), (4, 43), (6, 151), (6, 152), (7, 19), (9, 28), (12, 60), (17, 32), (17, 34)) and lemma == 'yaqorabu':
            if (s, a) == (12, 60):
                return "Koşullu mesafe uyarısı (`وَلَا تَقْرَبُونِ` `12:60`): Yûsuf'un küçük kardeş getirilmedikçe erzak ve görüşme yakınlığı tanımayacağını bildirmesi."
            return "Sınır çevresi koruma yasağı (`لَا تَقْرَبُوا۟` `2:35,187,222`, `4:43`, `6:151-152`, `17:32,34`, `9:28`): Kur'an'daki tüm `11` I. bab fiilinin olumsuz emir gelmesiyle çirkinliklere, yetim malına ve sınırlara daha başlangıç adımında yaklaşma bile denmesi."
        if (s, a) in ((3, 45), (4, 172), (7, 114), (26, 42), (56, 11), (56, 88), (83, 21), (83, 28)):
            return "En yakına alınmış seçkinler (`ٱلْمُقَرَّبُونَ` `3:45`, `4:172`, `56:11,88`, `83:21,28` & dünyevî saray yakınlığı `7:114`, `26:42`): İleri yarışanların ve kozmik görevlilerin yüksek yakınlık makamı."
        if (s, a) in ((2, 186), (7, 56), (11, 61), (34, 50), (50, 16), (56, 85)):
            return "Yaratıcının insana kuşatıcı yakınlığı (`فَإِنِّى قَرِيبٌ` `2:186`, `قَرِيبٌ مِّنَ ٱلْمُحْسِنِينَ` `7:56`, `أَقْرَبُ إِلَيْهِ مِنْ حَبْلِ ٱلْوَرِيدِ` `50:16`, `56:85`): Çağrıya anında karşılık veren ve şah damarından daha yakın olan ilâhî yakınlık."
        if (s, a) in ((4, 77), (7, 185), (9, 42), (11, 81), (13, 31), (14, 44), (16, 77), (17, 51), (21, 1), (21, 97), (21, 109), (33, 63), (34, 51), (42, 17), (48, 18), (48, 27), (50, 41), (54, 1), (59, 15), (61, 13), (63, 10), (70, 7), (72, 25), (78, 40)):
            return "Zaman ve mekân yakınlığı (`ٱقْتَرَبَ حِسَابُهُمْ` `21:1`, `54:1`, `فَتْحًا قَرِيبًا` `48:18,27`, `61:13`, `أَقَرِيبٌ أَم بَعِيدٌ` `21:109`, `أَجَلٍ قَرِيبٍ` `4:77`, `63:10`): Hesabın, yardımın veya açılımın uzak sanılsa da kapıya dayanmışlığı."
        if (s, a) in ((2, 237), (3, 167), (5, 8), (5, 82), (18, 24), (18, 81), (22, 13)):
            return "Nitelik ve tutumda daha yakın olma ölçüsü (`أَقْرَبُ لِلتَّقْوَىٰ` `2:237`, `5:8`, `لِأَقْرَبَ مِنْ هَٰذَا رَشَدًا` `18:24`, `أَقْرَبَهُم مَّوَدَّةً` `5:82`): Bağışlamanın ve adaletin sorumluluk bilincine yakınlığı ile eğilim karşılaştırmaları."
        return "Kan bağı, soy ve toplumsal hısımlık yakınlığı (`ذِى ٱلْقُرْبَىٰ` `2:83,177`, `4:8,36`, `16:90`, `42:23`, `ٱلْأَقْرَبُونَ` `4:7,33`, `ذَا مَقْرَبَةٍ` `90:15`): Akraba komşular, miras önceliği, yetim koruması ve soy yakınlığında adalet sorumluluğu (`4:135`, `6:152`, `35:18`)."

    elif root_ar == 'ب-غ-ي':
        if (s, a) == (28, 77):
            if lemma == '{botagaY`':
                return "Gelecek kalıcı yurdu emekle arama çağrısı (`وَٱبْتَغِ` `28:77` VIII. bab emir): İmkânları gelecek yurt iyiliği için değerlendirme ve dünyevî payı ihmal etmeme dengesi."
            return "Yeryüzünde taşkın bozgunculuk çıkarma yasağı (`وَلَا تَبْغِ ٱلْفَسَادَ` `28:77` I. bab nehiy): Aynı ayette yapıcı arama (`وَٱبْتَغِ`) karşısında sınır aşan bozgunculuğun (`تَبْغِ`) kesin reddi."
        if (s, a) == (55, 20):
            return "Doğal denge sınırını ihlal etmeme yasası (`بَيْنَهُمَا بَرْزَخٌ لَّا يَبْغِيَانِ` `55:20`): İki farklı su kütlesinin aralarındaki görünmez engelle birbirinin sınırına taşmadan akışı."
        if (s, a) in ((19, 92), (25, 18), (26, 211), (36, 40), (36, 69), (38, 35)):
            return "Kozmik ve yapısal uygunsuzluk ölçüsü (`مَا / لَا يَنۢبَغِى` `19:92`, `25:18`, `26:211`, `36:40,69`, `38:35`): Güneşin aya yetişemeyeceği gibi çocuk edinmenin Rahmân'a, şiirin ise vahye asla yaraşıp uymadığı ilkesi."
        if (s, a) == (24, 33):
            if lemma == "bigaA^'":
                return "İffet dışı kazanca zorlama yasağı (`عَلَى ٱلْبِغَآءِ` `24:33`): Namuslu kalmak isteyen genç kızların dünyevî çıkar uğruna iffet sınırını aşmaya zorlanmasının kesin yasağı."
            return "Özgürlük akdi veya geçici dünya metaı arayışı (`يَبْتَغُونَ ٱلْكِتَٰبَ` / `لِّتَبْتَغُوا۟ عَرَضَ` `24:33`): Özgürleşmek isteyenlere kapı açılması ile sömürü arayışının karşılaştırılması."
        if (s, a) in ((19, 20), (19, 28)):
            return "İffet sınırının korunması (`وَلَمْ أَكُ بَغِيًّا` `19:20,28`): Meryem'in babası ve annesi gibi kendisinin de asla namus ölçüsünü çiğneyen biri olmadığını beyanı."
        if (s, a) in ((2, 173), (6, 145), (16, 115)):
            return "Zorunluluk anında keyfî taşkınlık gütmeme şartı (`غَيْرَ بَاغٍ وَلَا عَادٍ` `2:173`, `6:145`, `16:115`): Hayatta kalma zaruretinde içsel azgın arzuyla (`بَاغٍ`) ve miktar sınırını aşarak (`عَادٍ`) yeme yasağı."
        if (s, a) == (18, 108):
            return "Esenlik yurdundan ayrılmak istememek (`لَا يَبْغُونَ عَنْهَا حِوَلًا` `18:108`): Kalıcı huzur ortamında bulunanların başka bir yere değişim aramayacakları vurgusu."
        if (s, a) in ((12, 65), (18, 64)):
            return "Yalın arayış ve hedef tespiti (`مَا نَبْغِى` `12:65`; `ذَٰلِكَ مَا كُنَّا نَبْغِ` `18:64`): I. bab fiilin taşkınlık olmaksızın 'tam arayıp beklediğimiz işaret' anlamında sade kullanımı."
        if (s, a) in ((2, 207), (2, 265), (2, 272), (4, 114), (5, 2), (13, 22), (17, 28), (17, 57), (29, 17), (48, 29), (57, 27), (59, 8), (60, 1), (92, 20)):
            return "Arı niyetle hoşnutluk ve rıza arayışı (`ٱبْتِغَآءَ مَرْضَاتِ / وَجْهِ رَبِّهِ` `2:207,265,272`, `13:22`, `48:29`, `92:20`): Çıkar hesaplarından arınarak yalnız Yaratıcının rızasını ve rahmetini hedefleme."
        if (s, a) in ((2, 198), (13, 17), (16, 14), (17, 12), (17, 66), (28, 73), (30, 23), (30, 46), (35, 12), (45, 12), (62, 10), (73, 20)):
            return "Doğal nimetlerden meşru geçim ve lütuf arayışı (`يَبْتَغُونَ فَضْلًا مِّنَ ٱللَّهِ` `2:198`, `16:14`, `28:73`, `30:23`, `62:10`, `73:20`): Gündüz ışığı, denizler ve yolculuklar içinde emek verip rızık arama serbestliği."
        if (s, a) in ((2, 187), (4, 24), (4, 104), (5, 35), (6, 35), (6, 114), (17, 110), (28, 55), (33, 51)):
            return "Meşru sınırlar içinde yol, vesile ve denge arayışı (`وَٱبْتَغُوٓا۟ إِلَيْهِ ٱلْوَسِيلَةَ` `5:35`, `17:110`, `4:24`, `28:55`): Aşırılıklar arasında orta ses tonunu, hukukî nikâhı veya doğru hükmü arama."
        if (s, a) in ((3, 7), (3, 83), (3, 85), (4, 94), (4, 139), (5, 50), (6, 164), (7, 140), (9, 47), (9, 48), (17, 42), (23, 7), (66, 1), (70, 31)):
            return "Hedefi şaşan veya hakkın dışında merci/sınır ötesi arzulayan tutumlar (`3:7,83,85`, `5:50`, `6:164`, `7:140`, `23:7`, `70:31`): Kargaşa veya keyfî yorum peşinde koşma, Yaratıcı dışında rab-hüküm arama yahut helal sınırının ötesini isteme."
        if (s, a) in ((3, 99), (7, 45), (7, 86), (11, 19), (14, 3)):
            return "Dosdoğru yolda eğrilik ve çarpıklık arama (`وَيَبْغُونَهَا عِوَجًا` `3:99`, `7:45,86`, `11:19`, `14:3`): İnsanları hak güzergâhından alıkoyup yolu yamultmaya çalışma."
        if (s, a) in ((2, 90), (2, 213), (3, 19), (6, 146), (10, 90), (42, 14), (45, 17)):
            return "Açık bilgi geldikten sonra kıskançlık ve taşkınlıkla ayrışma (`بَغْيًۢا بَيْنَهُمْ` `2:213`, `3:19`, `42:14`, `45:17`; `2:90`, `10:90`): Bilgisizlikten değil sırf üstünlük ve çekememezlik taşkınlığıyla hakkı reddetme."
        return "Hakkı çiğneyen saldırgan taşkınlık, haksız yol arama ve adalet dengesi (`4:34`, `9:47`, `10:23`, `16:90`, `22:60`, `28:76`, `38:22,24`, `42:27,39,42`, `49:9`, `6:164`, `7:140`): Başkasının hakkına tecavüz etme, aile içi haksız bahane arama (`4:34`), nimet bolluğunda azgınlaşma (`42:27`) ve saldırıya karşı meşru adalet dengesi (`49:9`)."

    elif root_ar == 'أ-خ-و':
        if (s, a) == (49, 10):
            return "Sarsılmaz toplumsal kardeşlik ve arabuluculuk (`إِنَّمَا ٱلْمُؤْمِنُونَ إِخْوَةٌ فَأَصْلِحُوا۟ بَيْنَ أَخَوَيْكُمْ` `49:10`): Biyolojik çekirdek kardeşlik kelimesi `إِخْوَة` ile ortak bilince sahip toplum bireylerinin onarımcı dayanışması vurgulanır."
        if (s, a) in ((3, 103), (6, 87), (15, 47), (49, 12), (59, 10)):
            return "Gönül birliği, seçilmiş soy halkası ve kardeş onuru (`3:103`, `6:87`, `15:47`, `49:12`, `59:10`): Düşmanlıktan kalp birliğiyle `إِخْوَٰنًا` konumuna geçme, seçkin hidayet halkası ve gıybetten kardeş etine dokunur gibi sakınma."
        if (s, a) in ((7, 38), (17, 27), (43, 48)):
            return "Karakter, topluluk ve işaretlerde eşdeğer kardeşlik (`أُخْتَهَا` `7:38`, `43:48`; `إِخْوَٰنَ ٱلشَّيَٰطِينِ` `17:27`): Aynı huyu, gidişatı veya işlevi paylaşan benzer varlıkların kardeş sayılması."
        if (s, a) in ((4, 11), (4, 12), (4, 23), (4, 176), (24, 31), (24, 61), (33, 55)):
            return "Miras, nikâh sınırı ve ev mahremiyeti hukuku (`4:11-23,176`, `24:31,61`, `33:55`): Öz, süt ve baba/anne bir kardeşlerin tereke payları, evlilik yasağı ve rahat ziyaret sınırları."
        if (s, a) in ((5, 25), (7, 111), (7, 142), (7, 150), (7, 151), (10, 87), (19, 53), (20, 30), (20, 40), (20, 42), (23, 45), (25, 35), (26, 36), (28, 11), (28, 34), (28, 35)):
            return "Mûsâ, Hârûn ve ablası arasındaki omuzdaşlık (`28:34-35`, `19:53`, `20:30,40`, `7:111`): Pazunun kardeşle sımsıkı güçlendirilmesi ve zorlu görevde aile dayanışması."
        if (s, a) in ((7, 65), (7, 73), (7, 85), (11, 50), (11, 61), (11, 84), (26, 106), (26, 124), (26, 142), (26, 161), (27, 45), (29, 36), (46, 21), (50, 13)):
            return "Toplumun içinden yetişmiş soydaş elçi (`أَخَاهُمْ / أَخُوهُمْ`): Âd, Semûd, Medyen ve Lût halklarına yabancı değil, kendi içlerinden dili ve derdi ortak bir kardeşlerinin gönderilmesi."
        if (s, a) in ((12, 5), (12, 7), (12, 8), (12, 58), (12, 59), (12, 63), (12, 64), (12, 65), (12, 69), (12, 70), (12, 76), (12, 77), (12, 87), (12, 89), (12, 90), (12, 100), (5, 30), (5, 31)):
            return "Kardeşler arası kıskançlık sınavı ve bağışlama dönüşümü (`5:30-31`, `12:5-100`): İlk kardeş cinayeti pişmanlığından Yûsuf'un hasetçi kardeşleriyle (`إِخْوَة`) kucaklaşmasına uzanan imtihan çizgisi."
        if (s, a) in ((2, 178), (2, 220), (9, 11), (33, 5), (38, 23)):
            return "Toplumsal hukuk, yetim koruma ve ilke kardeşliği (`2:178,220`, `9:11`, `33:5`, `38:23`): Kısasta insanî kardeşlik bağıyla af kapısı, babası bilinmeyenlerle ilke kardeşliği ve adalet ölçüsü."
        if (s, a) in ((9, 23), (9, 24), (58, 22), (70, 12), (80, 34)):
            return "Kardeşlik bağının hakikat ve hesap karşısındaki sınırı (`9:23-24`, `58:22`, `70:12`, `80:34`): Değerler çiğnendiğinde ilkenin öz kardeşlikten üstün tutulması ve hesap günündeki kaçış."
        return "Yanıltıcı/bozguncu dayanışma uyarısı veya soy bağı hitabı (`3:156,168`, `7:202`, `19:28`, `33:18`, `59:11`): Kardeşçe görünüp geri çekilmeye çağıranlar, sapmada destekleşenler veya Meryem'e soy bağıyla seslenilmesi (`19:28`)."

    elif root_ar == 'ح-ب-ب':
        if lemma in ('Hab~', 'Hab~ap'):
            return "Tohum, tahıl tanesi ve kozmik hassasiyet ölçüsü (`2:261`, `6:59,95,99`, `21:47`, `31:16`, `36:33`, `50:9`, `55:12`, `78:15`, `80:27`): Yedi yüz kat filiz veren tohumdan toprağın karanlığındaki hardal tanesine uzanan somut hayat çekirdeği."
        if (s, a) in ((9, 23), (14, 3), (16, 107), (41, 17)) and lemma == '{sotaHab~u':
            return "Tercih ve değer sıralaması (`ٱسْتَحَبُّوا۟` `9:23`, `14:3`, `16:107`, `41:17` X. bab): Hakikat ve gelecek kalıcı yurt yerine dünya çıkarını veya körlüğü daha sevgili seçip üstün tutma uyarısı."
        if (s, a) == (20, 39):
            return "Kalplere bırakılan ilâhî yakınlık çekimi (`مَحَبَّةً مِّنِّى` `20:39`): Bebek Mûsâ'ya bakan gönüllerde sevgi uyandırılması."
        if (s, a) == (49, 7):
            return "Gönle yerleştirilen sevgi ve tiksinti kutuplaşması (`حَبَّبَ ... وَكَرَّهَ` `49:7` II. bab hapaxı): Kalbe güveni sevdirip süslerken gerçeği örtmeyi ve sapmayı itici kılma mekanizması."
        if (s, a) == (5, 18):
            return "İmtiyaz ve sevgili dostluk iddiasının reddi (`وَأَحِبَّٰٓؤُهُۥ` `5:18`): Yaptıklarının hesabını veren beşer varlığın ayrıcalıklı sevgi iddiasında bulunamayacağı uyarısı."
        if (s, a) == (2, 165):
            return "Sevgi yoğunluğu ve yöneliş sınırı (`2:165` x3): Aracı figürlere duyulan sevgi ile güvene erenlerin yalnız Tek Yaratıcıya beslediği çok daha güçlü sevgi (`أَشَدُّ حُبًّا`) farkı."
        if (s, a) in ((3, 31), (5, 54), (24, 22), (28, 56)):
            return "Eylemle test edilen sevgi ve karşılıklı gönül bağı (`3:31`, `5:54`, `24:22`, `28:56`): Sevgi iddiasının elçiye somut uyumla (`فَٱتَّبِعُونِى يُحْبِبْكُمُ ٱللَّهُ` `3:31`) doğrulanması."
        if (s, a) in ((2, 177), (3, 92), (59, 9), (76, 8)):
            return "Sevileni paylaşarak sınanma (`3:92`, `2:177`, `59:9`, `76:8`): Kendi özünün sevdiği malı ve yemeği muhtaçlarla bölüşme erdemi."
        if (s, a) in ((3, 14), (9, 24), (12, 8), (12, 30), (12, 33), (38, 32), (75, 20), (76, 27), (89, 20), (100, 8)):
            return "İnsanî tutkuların yönü ve öncelik testi (`3:14`, `9:24`, `12:8-33`, `38:32`, `89:20`, `100:8`): Mal, at ve dünya sevgisinin (`حُبُّ ٱلشَّهَوَٰتِ`) sorumluluğu gölgelememesi ve Yûsuf'un zindanı zevke üstün tutması."
        if (s, a) in ((2, 195), (2, 222), (3, 76), (3, 134), (3, 146), (3, 148), (3, 159), (5, 13), (5, 42), (5, 93), (9, 4), (9, 7), (9, 108), (49, 9), (60, 8), (61, 4)):
            return "İlâhî onay ve sevgi yöneltilen somut erdemler (`يُحِبُّ`): İyilik üretenler (`ٱلْمُحْسِنِينَ`), adaletle hükmedenler (`ٱلْمُقْسِطِينَ`), sorumluluk bilincindekiler, arınanlar, direnenler ve kenetlenmiş safta duranlar."
        if (s, a) in ((2, 190), (2, 205), (2, 276), (3, 32), (3, 57), (3, 140), (4, 36), (4, 107), (4, 148), (5, 64), (5, 87), (6, 76), (6, 141), (7, 31), (7, 55), (8, 58), (16, 23), (22, 38), (28, 76), (28, 77), (30, 45), (31, 18), (42, 40), (57, 23)):
            return "İlâhî onayın dışında kalan kırmızı çizgiler (`لَا يُحِبُّ`): Saldırganlar, bozguncular, nankörler, hainler, israfçılar, kibirlenip böbürlenenler ve batan geçici yıldızlar (`6:76`)."
        return "Toplumsal sevgi yanılgıları ve insanî tercihler (`2:216`, `3:119`, `3:152`, `3:188`, `7:79`, `24:19`, `49:12`, `61:13`): İnsanın bazen zararına olanı sevmesi, çirkinliği yayma arzusu veya öğüt vereni sevmemesi (`7:79`)."

    elif root_ar == 'س-ب-ح':
        if (s, a) in {(21, 33), (36, 40)}:
            return "Kozmik yörünge yüzüşü (`21:33`, `36:40`): Güneş, ay ve gök cisimlerinin kendi yörüngelerinde (`felek`) akıp süzülmesi (`يَسْبَحُونَ`); kökün sudaki sürtünmesiz ve kesintisiz akış çekirdeğini kozmik ölçekte görünür kılar."
        if (s, a) in {(73, 7), (79, 3)}:
            return "Engin akış ve hızla süzülüş (`73:7`, `79:3`): Gündüzün uzun meşguliyet akışı (`سَبْحًا طَوِيلًا`, `73:7`) ve kozmik görevlilerin emir doğrultusunda süratle yüzüp süzülüşü (`وَٱلسَّٰبِحَٰتِ سَبْحًا`, `79:3`)."
        if (s, a) in {(17, 1), (57, 1), (59, 1), (61, 1), (62, 1), (64, 1), (87, 1)}:
            return "Müsebbihât sûre açılışları (`17:1`, `57:1`, `59:1`, `61:1`, `62:1`, `64:1`, `87:1`): Dört farklı dilbilgisel kipte (`سُبْحَٰنَ` mastar `17:1`; `سَبَّحَ` mâzî `57:1`, `59:1`, `61:1`; `يُسَبِّحُ` muzârî `62:1`, `64:1`; `سَبِّحِ` emir `87:1`) tüm göklerin ve yerin Allah'ı eksiklikten uzak tuttuğu vurgulanır."
        if (s, a) in {(17, 44), (24, 41)}:
            return "Yedi gök, yer ve canlıların kendilerine özgü tesbîhi (`17:44`, `24:41`): Her varlık ve saf saf uçan kuşlar kendi işleyiş yasası içinde Allah'ı aşkınlığıyla anar; insan ise onların bu `تَسْبِيح` dilini kavrayamaz."
        if (s, a) == (17, 93):
            return "İnsanın olağanüstü beklentilerine karşı aşkınlık ilanı (`17:93`): Meydan okuma taleplerine karşı elçinin sadece insan bir haberci olduğunu bildiren `قُلْ سُبْحَانَ رَبِّى` yanıtı; 41 `suboHa`n` geçişi içinde tam elifle (`سبحان`) yazılan tek ayettir."
        if (s, a) == (34, 41):
            return "Sahte tapınma odaklarından arınma (`34:41`): Sorgulanan yüksek görevlilerin, kendilerini değil görünmez varlıkları merkeze alan insanlardan bütünüyle uzak durup Allah'ın aşkınlığını (`سُبْحَٰنَكَ`) ilan etmesi."
        if (s, a) in {(2, 30), (7, 206), (21, 20), (37, 166), (39, 75), (40, 7), (41, 38), (42, 5)}:
            return "Kozmik görevlilerin gece gündüz kesintisiz yönelişi (`2:30`, `7:206`, `21:20`, `37:166`, `39:75`, `40:7`, `41:38`, `42:5`): Kibir ve bıkkınlık taşımadan, varoluş düzeni içinde Allah'ı her eksiklikten uzak tutmaları."
        if (s, a) in {(13, 13), (21, 79), (38, 18)}:
            return "Doğa unsurlarının tesbîh eşliği (`13:13`, `21:79`, `38:18`): Gök gürültüsünün hamd ile yönelişi (`13:13`) ve dağlar ile kuşların Davud'a uyumla eşlik etmesi (`21:79`, `38:18`)."
        if (s, a) in {(21, 87), (37, 143)}:
            return "Zorluk daralmasından tesbîh ile çıkış (`21:87`, `37:143`): Yunus'un karanlıklar içinden `سُبْحَٰنَكَ` nidasıyla kendi hatasını kabullenip aşkınlığı ilan etmesi ve `ٱلْمُسَبِّحِينَ` arasında yer alması."
        if (s, a) in {(3, 41), (19, 11), (20, 33), (68, 28), (68, 29)}:
            return "Bireysel ve toplumsal özeleştiri/yöneliş (`3:41`, `19:11`, `20:33`, `68:28-29`): Zekeriyya'ya sabah akşam tesbîh işareti (`3:41`, `19:11`), Musa ve Harun'un çokça anma talebi (`20:33`), bahçe sahiplerinin hatalarını fark edince Rabb'i aşkın ilan etmesi (`68:28-29`)."
        if (s, a) in {(15, 98), (20, 130), (24, 36), (25, 58), (32, 15), (33, 42), (40, 55), (48, 9), (50, 39), (50, 40), (52, 48), (52, 49), (56, 74), (56, 96), (59, 24), (69, 52), (76, 26), (110, 3)}:
            return "Elçiye ve inananlara gün döngüsünde sebat ve hamd ile arındırma buyrukları (`15:98`, `20:130`, `25:58`, `40:55`, `50:39-40`, `52:48-49`, `56:74`, `56:96`, `69:52`, `76:26`, `110:3`): Güneşin doğuşundan batışına ve uzun gece boyunca kesintisiz direnç ve şükür yönelişi."
        if lemma == 'suboHa`n':
            return "Yakıştırılan eksiklik, ortak veya beşerî zaaf isnatlarından mutlak uzaklaştırma ilanı (`سُبْحَٰنَ`): Evrenin bütünlüğünü bozan her türlü yanlış tasavvuru reddedip Yaratıcıyı aşkın konumunda tutar."
        return "Allah'ı her türlü eksiklik, sınır veya keyfî isnattan uzak tutarak hamd ve bilinçli yönelişle anma (`سَبَّحَ / يُسَبِّحُ / سَبِّحْ`): Zamanın akışı içinde kararlı bir yörünge bilincini ifade eder."

    elif root_ar == 'ل-ي-ل':
        if (s, a) in {(2, 164), (3, 190), (10, 6), (23, 80), (25, 62), (45, 5)}:
            return "Gece ve gündüzün ardışık dönüşümü (`2:164`, `3:190`, `10:6`, `23:80`, `25:62`, `45:5`): Evrendeki düzenli devir (`ٱخْتِلَٰف` / `خِلْفَة`), akleden ve nimetin değerini bilmek isteyenler için başlı başına kozmik kanıttır."
        if (s, a) in {(3, 27), (7, 54), (13, 3), (22, 61), (24, 44), (31, 29), (35, 13), (39, 5), (57, 6)}:
            return "Gecenin gündüze katılıp sarılması (`3:27`, `7:54`, `13:3`, `22:61`, `24:44`, `31:29`, `35:13`, `39:5`, `57:6`): Mevsimsel ve küresel geçişlerle gecenin gündüz içine geçirilmesi (`يُولِجُ`), bürünmesi (`يُغْشِى`) ve küre üzerine sarık gibi dolanması (`يُكَوِّرُ` `39:5`)."
        if (s, a) in {(6, 96), (10, 67), (25, 47), (27, 86), (28, 71), (28, 72), (28, 73), (40, 61), (78, 10)}:
            return "Rahmet, dinlenme ve sükûnet örtüsü (`6:96`, `10:67`, `25:47`, `27:86`, `28:71-73`, `40:61`, `78:10`): Gecenin koruyucu bir elbise (`لِبَاسًا`) ve dinginlik yuvası (`سَكَنًا`) kılınması; kesintisiz gece veya kesintisiz gündüz halinde dengenin nasıl çökeceğinin `28:71-72` sorusuyla kanıtlanması."
        if (s, a) in {(6, 76), (14, 33), (16, 12), (17, 12), (21, 33), (36, 37), (36, 40), (41, 37), (79, 29)}:
            return "Yörüngesel sınır, gök cisimleri ve gece işaretinin silinmesi (`6:76`, `14:33`, `16:12`, `17:12`, `21:33`, `36:37,40`, `41:37`, `79:29`): Gecenin gündüzü geçememesi (`36:40`), güneş ve aya secde edilmeyip yalnız Yaratana yönelinmesi (`41:37`), İbrâhîm'in karanlıkta batan yıldızı sorgulaması (`6:76`)."
        if (s, a) in {(2, 51), (7, 142), (44, 3), (97, 1), (97, 2), (97, 3)}:
            return "Belirleyici vahiy ve sözleşme geceleri (`2:51`, `7:142`, `44:3`, `97:1-3`): Mûsâ'ya otuz artı on eşittir kırk gece vade (`لَيْلَةً`) verilmesi ile Kur'an'ın bereketli ve ölçü değeri taşıyan (`لَيْلَةِ ٱلْقَدْرِ`) gecede indirilmesi."
        if (s, a) in {(11, 81), (15, 65), (17, 1), (44, 23)}:
            return "Geceleyin kurtuluş ve tarihî yürüyüş (`11:81`, `15:65`, `17:1`, `44:23`): Lût ailesinin (`بِقِطْعٍ مِّنَ ٱلَّيْلِ`) ve Mûsâ önderliğindeki kulların (`لَيْلًا`) gece yola çıkarılması ile elçinin Mescid-i Harâm'dan Mescid-i Aksâ'ya gece yürütülmesi (`17:1`)."
        if (s, a) in {(19, 10), (34, 18), (69, 7), (89, 2)}:
            return "Sayılı gece dizileri ve kırık çoğul (`19:10`, `34:18`, `69:7`, `89:2`): Zekeriyyâ'nın üç gece konuşamama işareti (`19:10`), Sebe' ülkesinde güvenli gece yolculukları (`34:18`), Âd kavmine esen yedi gecelik kasırga (`69:7`) ve Fecr sûresindeki on gece (`89:2`)."
        if (s, a) in {(2, 187), (2, 274), (3, 113), (11, 114), (17, 78), (17, 79), (20, 130), (21, 20), (39, 9), (41, 38), (50, 40), (51, 17), (52, 49), (71, 5), (73, 2), (73, 6), (73, 20), (76, 26)}:
            return "Gece disiplini, öz denetim ve içsel uyanıklık (`2:187`, `2:274`, `3:113`, `11:114`, `17:78-79`, `20:130`, `39:9`, `50:40`, `51:17`, `52:49`, `73:2,6,20`, `76:26`): Gece kalkışının kalp-dil bütünlüğüne en sağlam zemin oluşturması (`73:6`), infak (`2:274`), geceye kadar süren öz denetim (`2:187`), Nûh'un gece gündüz çağrısı (`71:5`) ve yüksek görevlilerin kesintisiz tesbihi (`21:20`, `41:38`)."
        if (s, a) in {(6, 13), (6, 60), (10, 24), (10, 27), (13, 10), (21, 42), (30, 23), (34, 33), (37, 138)}:
            return "Gece-gündüz bütününde ilâhî kuşatma ve insan sorumluluğu (`6:13,60`, `10:24,27`, `13:10`, `21:42`, `30:23`, `34:33`, `37:138`): Gecede uyuyup sığınan ile gündüz ortaya çıkanın bilgisinin eşit olması (`13:10`), gece-gündüz kurulan tuzaklar (`34:33`), geçilen helak yurtları (`37:138`) ve yüzleri kaplayan karanlık gece parçası tasviri (`10:27`)."
        if (s, a) in {(74, 33), (81, 17), (84, 17), (89, 4), (91, 4), (92, 1), (93, 2)}:
            return "Mekkî sûrelerde gecenin fiziksel evreleri üzerine kozmik antlar (`74:33`, `81:17`, `84:17`, `89:4`, `91:4`, `92:1`, `93:2`): Sırtını dönen (`أَدْبَرَ`), kararıp çekilen (`عَسْعَسَ`), varlığı toplayan (`وَمَا وَسَقَ`), yürüyüp giden (`يَسْرِ`), bürüyen (`يَغْشَى`) ve durulan (`سَجَىٰ`) gece evreleriyle yapılan tanıklıklar."
        return "Gündüzün karşıtı olarak dünyayı saran karanlık, dinginlik ve odaklanma kuşağı (`ٱلَّيْل` / `لَيْلَة`)."

    elif root_ar == 'ل-ي-س':
        if (s, a) in {(42, 11), (53, 39), (3, 182), (8, 51), (22, 10), (53, 58), (56, 2), (69, 35), (70, 2), (88, 6)}:
            return "Tevhîd, adalet ve kesin gerçeklik hükmü (`42:11`, `53:39`, `3:182`, `8:51`, `22:10`, `53:58`, `56:2`, `69:35`, `70:2`, `88:6`): Yaratıcıya benzer hiçbir şey bulunmaması (`42:11`), kullara asla zulmedilmemesi (`3:182`), insana yalnız kendi emeğinin kalması (`53:39`) ve hesap saatinde aracı-kurtarıcı olmaması."
        if (s, a) in {(6, 30), (6, 53), (7, 172), (11, 78), (11, 81), (29, 10), (29, 68), (36, 81), (39, 32), (39, 36), (39, 37), (39, 60), (43, 51), (46, 34), (75, 40), (95, 8)}:
            return "Olumsuz soruyla kesin `بَلَىٰ` itirafı doğuran akıl ve hesap sınamaları (`6:30,53`, `7:172`, `11:78,81`, `29:10,68`, `36:81`, `39:32,36,37,60`, `43:51`, `46:34`, `75:40`, `95:8`): Fıtrî sözleşmede 'Ben Rabbiniz değil miyim?' sorusuna verilen `بَلَىٰ` yanıtı, yaratılış kudretinin kanıtı (`36:81`, `75:40`) ve Firavun'un sahte mülk iddiasının teşhiri (`43:51`)."
        if (s, a) in {(2, 113), (2, 177), (2, 189), (3, 113), (4, 18), (4, 123), (5, 68), (6, 89), (6, 122), (7, 61), (7, 67)}:
            return "Şeklî tanımı yıkıp hakikat ölçüsünü kurma (`2:113`, `2:177`, `2:189`, `3:113`, `4:18,123`, `5:68`, `6:89,122`, `7:61,67`): Rakip grupların birbirini 'temelsizlikle' suçlaması (`2:113`), hepsinin aynı olmadığını bildiren `لَيْسُوا۟ سَوَآءً` uyarısı (`3:113`), iyiliğin yüzleri yöneltmekten ibaret sayılmaması (`2:177`) ve son nefes tövbesinin geçersizliği (`4:18`)."
        if (s, a) in {(3, 66), (3, 167), (11, 46), (11, 47), (17, 36), (22, 71), (24, 15), (29, 8), (31, 15), (40, 42), (48, 11)}:
            return "Bilgi dayanağı olmayan iddia ve kalp-dil tutarsızlığının reddi (`3:66,167`, `11:46-47`, `17:36`, `22:71`, `24:15`, `29:8`, `31:15`, `40:42`, `48:11`): Bilmediği şeyin ardına düşmeme ilkesi (`17:36`), kalpte bulunmayanı dille söyleme (`3:167`, `48:11`) ve anne-babanın bile bilgisiz ortak koşma baskısına uyulmaması (`29:8`, `31:15`)."
        if (s, a) in {(2, 198), (2, 249), (2, 267), (2, 282), (3, 28), (3, 36), (3, 75), (4, 101), (4, 176), (5, 93), (9, 91), (15, 20), (24, 29), (24, 58), (24, 60), (24, 61), (33, 5), (33, 32), (48, 17)}:
            return "Muafiyet, hukukî paylaşım ve davranış sınırları (`2:198,282`, `4:101,176`, `9:91`, `24:29,58,60,61`, `33:5,32`, `48:17`): Zayıf, hasta, yolcu ve mazeret sahiplerinden gereksiz sorumluluğun kaldırılması (`9:91`, `24:61`, `48:17`), peşin ticarette yazım kolaylığı (`2:282`), yanılmalarda vebal olmayışı (`33:5`) ve kelâle mirası (`4:176`)."
        if (s, a) in {(2, 272), (3, 128), (4, 94), (5, 116), (6, 51), (6, 66), (6, 70), (6, 159), (11, 16), (13, 43), (15, 42), (16, 99), (17, 65), (40, 43), (46, 32), (58, 10), (88, 22)}:
            return "Elçilik sınırı, aracıların yokluğu ve yıkıcı gücün yetkisizliği (`2:272`, `3:128`, `4:94`, `5:116`, `6:51,66,70,159`, `13:43`, `15:42`, `16:99`, `17:65`, `40:43`, `46:32`, `58:10`, `88:22`): Elçinin vekil veya zorlayıcı olmadığı (`6:66`, `88:22`), barış sunana güvensizlik yakıştırılamayacağı (`4:94`) ve arınmış kullar üzerinde saptırıcı gücün nüfuzu bulunmadığı (`15:42`, `16:99`, `17:65`)."
        return "İsim cümlesinde varlık, geçerlilik veya yükümlülük bağını sıfırlayan câmid olumsuz kopula (`لَيْسَ`)."

    elif root_ar == 'ش-ط-ن':
        if (s, a) in {(2, 36), (7, 20), (7, 22), (7, 27), (20, 120)}:
            return "İlk ayartma, örtünün sıyrılması ve koruma uyarısı (`2:36`, `7:20,22,27`, `20:120`): Saptırıcı yıkıcı gücün fısıldamasıyla insanın ayağının kaydırılması, gizlenen kusurların açığa çıkması ve Ademoğullarına yöneltilen tarihî uyarı."
        if (s, a) in {(2, 14), (2, 102), (4, 38), (4, 60), (4, 76), (4, 83), (4, 117), (4, 119), (4, 120), (6, 112), (6, 121), (19, 68), (19, 83), (22, 3), (43, 36), (47, 25), (58, 10), (58, 19), (59, 16)}:
            return "İnsanî elebaşılar, yoldaşlık ve zayıf tuzakların teşhiri (`2:14,102`, `4:38,60,76,117-120`, `6:112,121`, `19:68,83`, `22:3`, `43:36`, `47:25`, `58:10,19`, `59:16`): İkiyüzlülerin elebaşıları (`2:14`), insan ve görünmez türlerin yaldızlı söz fısıldaması (`6:112`), tuzağının zayıflığı (`4:76`), unutkanlıkla hizipleşme (`58:19`) ve sonunda insanı yüzüstü bırakma (`59:16`)."
        if (s, a) in {(2, 168), (2, 208), (2, 268), (2, 275), (5, 90), (5, 91), (6, 142), (17, 27), (24, 21), (35, 6), (36, 60), (43, 62)}:
            return "Toplumsal, ekonomik ve ahlakî saptırma mekanizmaları (`2:168,208,268,275`, `5:90-91`, `6:142`, `17:27`, `24:21`, `35:6`, `36:60`, `43:62`): Adımlarına uymama yasağı, kıtlık korkusu aşılama (`2:268`), faiz (`2:275`), içki-kumar-dikili taşlar (`5:90-91`), savurganlık kardeşliği (`17:27`) ve açık düşman ilanı."
        if (s, a) in {(3, 36), (7, 200), (7, 201), (16, 98), (23, 97), (41, 36)}:
            return "İlâhî sığınak ve bilinçli uyanış kalkanı (`3:36`, `7:200-201`, `16:98`, `23:97`, `41:36`): Kur'an okurken ve dürtme geldiğinde Allah'a sığınma buyruğu ile sakınanların bir vesvese dokunduğunda hemen hatırlayıp gerçeği görmesi (`7:201`)."
        if (s, a) in {(3, 155), (3, 175), (6, 43), (6, 68), (6, 71), (7, 30), (7, 175), (8, 11), (8, 48), (12, 5), (12, 42), (12, 100), (14, 22), (16, 63), (17, 53), (17, 64), (18, 63), (19, 44), (19, 45), (22, 52), (22, 53), (25, 29), (27, 24), (28, 15), (29, 38), (31, 21), (38, 41)}:
            return "Aldatma yöntemleri, aile-toplum içi fitne ve yetkisizlik itirafı (`3:155,175`, `6:43,68`, `8:11,48`, `12:5,42,100`, `14:22`, `16:63`, `17:53,64`, `18:63`, `19:44-45`, `22:52-53`, `25:29`, `27:24`, `28:15`, `29:38`, `31:21`, `38:41`): Çirkini süsleme, unutkanlık, ara bozma, Mûsâ ve Eyyûb'un tespiti ile hesap gününde 'üzerinizde zorlayıcı yetkim yoktu' itirafı (`14:22`)."
        if (s, a) in {(15, 17), (21, 82), (26, 210), (26, 221), (37, 7), (37, 65), (38, 37), (67, 5), (81, 25)}:
            return "Göksel koruma, Süleymân'ın mühendis-dalgıçları ve vahyin berî oluşu (`15:17`, `21:82`, `26:210,221`, `37:7,65`, `38:37`, `67:5`, `81:25`): Taşlanmış yıkıcı odakların gökten ve vahiyden tamamen uzak tutulması ile Süleymân'ın emrindeki bina-dalgıçlık işlerinin yönetimi."
        return "Haktan uzaklaşıp korku, kuruntu ve bozgun üreten taşkın saptırıcı güç (`ٱلشَّيْطَٰن / ٱلشَّيَٰطِين`)."

    elif root_ar == 'ق-ر-أ':
        if (s, a) in {(16, 98), (17, 45), (17, 106), (20, 114), (73, 4), (73, 20), (75, 17), (75, 18), (87, 6), (96, 1), (96, 3)}:
            return "İlk okuma emri, toplama (`جَمْع`) ve hafıza güvencesi (`16:98`, `17:45,106`, `20:114`, `73:4,20`, `75:17-18`, `87:6`, `96:1,3`): Kur'an'ı ağır ağır ve anlayarak okumak (`73:4`, `17:106`), okuyup anlamaya başlarken sığınmak (`16:98`), acele etmemek (`20:114`) ve vahyî derleme-okuma sürecinin ilâhî garanti altında oluşu (`75:17-18`, `87:6`)."
        if (s, a) in {(2, 228), (10, 94), (17, 14), (17, 71), (17, 93), (69, 19)}:
            return "Döngüsel birikim (`قُرُوٓءٍ` `2:228`) ve bireysel eylem kitabını okuma (`10:94`, `17:14,71,93`, `69:19`): Boşanma sonrası üç döngüsel evre beklemek (`2:228`) ve hesap gününde kişinin kendi sicil kitabını eline alıp okuması (`17:14`, `17:71`, `69:19`)."
        if (s, a) in {(2, 185), (5, 101), (6, 19), (12, 2), (12, 3), (17, 78), (20, 2), (20, 113), (25, 32), (26, 199), (39, 28), (41, 3), (41, 44), (42, 7), (43, 3), (76, 23)}:
            return "Kur'an'ın indiriliş amacı, dili ve aşamalı inşası (`2:185`, `5:101`, `6:19`, `12:2-3`, `17:78`, `20:2,113`, `25:32`, `26:199`, `39:28`, `41:3,44`, `42:7`, `43:3`, `76:23`): Eğriliği olmayan Arapça okunuş (`12:2`, `39:28`, `43:3`), kalbe sağlam yerleşsin diye aşamalı iniş (`25:32`) ve yabancı dil iddiasının reddi (`41:44`)."
        if (s, a) in {(4, 82), (9, 111), (10, 37), (10, 61), (15, 1), (15, 87), (17, 9), (17, 41), (17, 82), (17, 89), (18, 54), (27, 1), (27, 6), (27, 76), (27, 92), (28, 85), (30, 58), (39, 27), (47, 24), (54, 17), (54, 22), (54, 32), (54, 40), (55, 2), (59, 21)}:
            return "Çelişkisiz tutarlılık, tefekkür (`تَدَبُّر`), şifa ve öğüt (`4:82`, `9:111`, `10:37,61`, `15:87`, `17:9,41,82,89`, `18:54`, `27:76`, `30:58`, `39:27`, `47:24`, `54:17-40`, `55:2`, `59:21`): Her örneği bünyesinde toplayan çelişkisiz metin üzerinde derin düşünme, kalplere şifa ve öğüt için kolaylaştırılmış dil."
        if (s, a) in {(7, 204), (10, 15), (13, 31), (15, 91), (17, 46), (17, 60), (17, 88), (25, 30), (34, 31), (36, 2), (36, 69), (38, 1), (41, 26), (43, 31), (46, 29), (50, 1), (50, 45), (56, 77), (72, 1), (84, 21), (85, 21)}:
            return "Vahyin benzersizliği, antlar, dinleme edebi ve direnç (`7:204`, `10:15`, `13:31`, `15:91`, `17:46,60,88`, `25:30`, `34:31`, `36:2,69`, `38:1`, `41:26`, `43:31`, `46:29`, `50:1,45`, `56:77`, `72:1`, `84:21`, `85:21`): Okunduğunda gürültü çıkarıp sabote edenler (`41:26`) ve terk edenlere (`25:30`) karşı görünmeyen varlıkların susup dinlemesi (`46:29`, `72:1`) ve kimsenin benzerini üretememesi (`17:88`)."
        return "Dağınık öğeleri ve ayetleri bir bütünlük içinde toplayıp seslendiren okuma eylemi (`قَرَأَ / قُرْءَان`)."

    elif root_ar == 'خ-ل-د':
        if (s, a) in {(7, 20), (7, 176), (20, 120), (21, 8), (21, 34), (26, 129), (104, 3)}:
            return "Dünyevî kalıcılık yanılgısı ve yere yapışma teşhiri (`7:20,176`, `20:120`, `21:8,34`, `26:129`, `104:3`): Âdem'e uzatılan sahte `شَجَرَةِ ٱلْخُلْدِ` aldatmacası, ayetlere rağmen toprağa yapışıp alçalanın (`أَخْلَدَ`) durumu, Âd'ın kalelerle ölümsüzlük hayali (`26:129`), malıyla ölümsüzleştiğini sanan servet tutkunu (`104:3`) ve dünyada hiçbir beşere kalıcılık verilmediği yasası (`21:34`)."
        if (s, a) in {(6, 128), (11, 107), (11, 108), (25, 69), (59, 17)}:
            return "Kozmik süre ölçüsü, ilâhî dileme şartı ve ikili hesap (`6:128`, `11:107-108`, `25:69`, `59:17`): Gökler ve yer durdukça Rabb'in dilemesi dışında kalıcılık ilkesi (`11:107-108`, `6:128`), alçaltılmış kalış (`25:69`) ve azdıranla aldananın ateşte ikili kalışı (`خَٰلِدَيْنِ` `59:17`)."
        if (s, a) in {(4, 57), (4, 122), (4, 169), (5, 119), (9, 22), (9, 100), (33, 65), (64, 9), (65, 11), (72, 23), (98, 8)}:
            return "Sonsuzluk pekiştirmeli (`خَٰلِدِينَ فِيهَآ أَبَدًا`) kesin yurt hükümleri (`4:57,122,169`, `5:119`, `9:22,100`, `33:65`, `64:9`, `65:11`, `72:23`, `98:8`): Hem esenlik bahçelerinde hem ağır sorumluluk yurdunda sürekliliğin bitimsiz `أَبَدًا` zarfıyla kilitlenmesi."
        if (s, a) in {(2, 25), (2, 82), (3, 15), (3, 107), (3, 136), (3, 198), (4, 13), (5, 85), (7, 42), (9, 72), (9, 89), (10, 26), (11, 23), (14, 23), (18, 108), (20, 76), (21, 102), (23, 11), (25, 15), (25, 16), (25, 76), (29, 58), (31, 9), (39, 73), (43, 71), (46, 14), (47, 15), (48, 5), (50, 34), (56, 17), (57, 12), (58, 22), (76, 19)}:
            return "Esenlik bahçelerinde bozulmaz ve hoşnut kalıcılık (`2:25,82`, `3:15,107,136,198`, `18:108`, `25:15-16`, `47:15`, `50:34`, `56:17`, `76:19`): Güvenen ve erdemli işler yapanların altından ırmaklar akan esenlik bahçelerinde, başka yere taşınmak istemeksizin (`18:108`) solmaz gençlik (`56:17`, `76:19`) ve selamla karşılandığı kalıcılık günü (`يَوْمُ ٱلْخُلُودِ` `50:34`)."
        return "Haktan uzaklaşma, büyüklük taslama, faiz ve kasıtlı haksızlık sonucunda yakıcı azap yurdunda kalıcılık (`2:39,81,162,217,257,275`, `4:14,93`, `10:52`, `32:14`, `41:28`, `43:74`, `64:10`, `98:6`): Hafifletme ve erteleme olmaksızın (`2:162`, `3:88`) yapılanların denk karşılığı olarak azapta yerleşik kalış."

    elif root_ar == 'ت-و-ب':
        if (s, a) in {(2, 37), (2, 128), (2, 187), (3, 128), (4, 17), (4, 26), (4, 27), (4, 64), (5, 71), (9, 15), (9, 27), (9, 102), (9, 104), (9, 106), (9, 117), (9, 118), (20, 122), (24, 10), (33, 24), (33, 73), (42, 25), (58, 13), (73, 20), (110, 3)}:
            return "İlâhî rahmet dönüşü, kabul ve kolaylaştırma (`تَابَ عَلَى`: `2:37,128,187`, `4:17,26-27`, `9:104,117-118`, `20:122`, `42:25`, `58:13`, `73:20`, `110:3`): Âdem ve toplulukların dönüşüne karşılık verilmesi, `9:118`de önce ilâhî dönmenin insanın dönmesine yol açması (`تَابَ عَلَيْهِمْ لِيَتُوبُوٓا۟`) ve gece-infak-eş ilişkisinde yükün hafifletilmesi (`2:187`, `58:13`, `73:20`)."
        if (s, a) in {(2, 160), (3, 89), (4, 16), (4, 146), (5, 34), (5, 39), (6, 54), (7, 153), (11, 112), (16, 119), (19, 60), (20, 82), (24, 5), (25, 70), (25, 71), (28, 67)}:
            return "Dönüş ve onarım bütünlüğü (`تَابَ وَأَصْلَحَ` / `عَمِلَ صَٰلِحًا`: `2:160`, `3:89`, `4:16,146`, `5:39`, `6:54`, `16:119`, `19:60`, `20:82`, `24:5`, `25:70-71`, `28:67`): Sözlü pişmanlıkla yetinmeyip bozulanı düzeltme, gizleneni açıklama (`2:160`) ve kötülüklerin iyiliğe dönüştürülmesi (`25:70`) şartları."
        if (s, a) in {(2, 54), (2, 222), (2, 279), (4, 92), (5, 74), (7, 143), (9, 3), (9, 5), (9, 11), (9, 112), (11, 3), (11, 52), (11, 61), (11, 90), (13, 30), (24, 31), (40, 3), (40, 7), (46, 15), (49, 12), (66, 4), (66, 5), (66, 8)}:
            return "Elçilerin çağrısı, katışıksız yöneliş ve arınma (`تُوبُوٓا۟ إِلَى ٱللَّهِ`: `2:54,222,279`, `7:143`, `9:112`, `11:3,52,61,90`, `13:30`, `24:31`, `40:3,7`, `46:15`, `66:4-8`): Bağışlanma dileğinin ardından Yaratıcıya dönmek, sürekli dönenlerin sevilmesi (`2:222`), `تَوْبَةً نَّصُوحًا` (`66:8`) ve `وَقَابِلِ ٱلتَّوْبِ` (`40:3`)."
        return "Dönüşün reddi, geç kalmış pişmanlık ve dönmemenin sonucu (`3:90`, `4:18`, `9:74,126`, `49:11`, `85:10`): Ölüm kapıyı çalınca yapılan sözde dönüşün geçersizliği (`4:18`), sapmada inat (`3:90`), sınanmalardan ders almama (`9:126`) ve dönmeyenlerin zulümde kalması (`49:11`, `85:10`)."

    if root_ar == 'م-و-ل':
        if (s, a) in {(2, 155), (3, 186), (4, 95), (8, 72), (9, 20), (9, 41), (9, 44), (9, 81), (9, 88), (9, 111), (47, 36), (48, 11), (49, 15), (59, 8), (61, 11)}:
            return "Can ve mal bütünlüğünde sınanma ve mücadele (`2:155`, `3:186`, `4:95`, `8:72`, `9:20,41,44,81,88,111`, `47:36`, `48:11`, `49:15`, `59:8`, `61:11`): Yaratıcı insanları mallardan ve canlardan eksiltmeyle sınar (`2:155`, `3:186`), mallarının tamamını talep etmez (`47:36`), yurtlarından ve mallarından çıkarılmış muhacirleri (`59:8`) ve canlarıyla mallarını Allah yolunda seferber edenleri (`4:95`, `9:20,111`, `49:15`, `61:11`) bahane üretip geri duranlardan (`9:44,81,88`, `48:11`) ayırır."
        if (s, a) in {(4, 2), (4, 5), (4, 6), (4, 10), (6, 152), (17, 34)}:
            return "Yetimlerin ve korumasızların mallarını muhafaza hukuku (`4:2,5,6,10`, `6:152`, `17:34`): Yetimin temiz malını kendi değersiz malıyla değiştirmeme (`4:2`), yönetemeyecek akıl olgunluğu öncesinde koruyup (`4:5`) rüşde ulaşınca şahitlerle eksiksiz teslim etme (`4:6`), yetim malını zulümle yiyenlerin kendi karınlarına ateş doldurduğu (`4:10`) ve yalnız en güzel koruma amacıyla yaklaşma buyruğu (`6:152`, `17:34`)."
        if (s, a) in {(2, 188), (2, 279), (4, 29), (4, 161), (9, 34), (30, 39)}:
            return "Bâtıl sömürü ve ribâ yasağı, meşru rıza ticareti (`2:188,279`, `4:29,161`, `9:34`, `30:39`): Malları haksız yollarla ve yargı rüşvetiyle yememe (`2:188`), karşılıklı rızaya dayalı ticareti esas alma (`4:29`), ribâyı terk halinde ana sermayeyi (`رُءُوسُ أَمْوَٰلِكُمْ`) güvenceye alma (`2:279`), halkın mallarını sömürenleri kınama (`4:161`, `9:34`) ve çıkar amaçlı artışın Allah katında bereketlenmeyeceğini bildirme (`30:39`)."
        if (s, a) in {(2, 177), (2, 261), (2, 262), (2, 264), (2, 265), (2, 274), (4, 24), (4, 34), (4, 38), (9, 103), (24, 33), (51, 19), (70, 24), (92, 18)}:
            return "Emanet bilinciyle paylaşım, aile sorumluluğu ve arındırma (`2:177,261-265,274`, `4:24,34,38`, `9:103`, `24:33`, `51:19`, `70:24`, `92:18`): Sevilen malı yoksullara verme (`2:177`), başa kakmadan ve gösterişsiz karşılıksız paylaşma (`2:261-265,274`, `4:38`), arındırıcı pay alma (`9:103`, `92:18`), eşleşme ve aile geçim sorumluluğu (`4:24,34`), Allah'ın verdiği kendi malından özgürlük sözleşmesine destek (`24:33`) ve muhtaçla yoksulun maldaki yerleşik hakkı (`51:19`, `70:24`)."
        if (s, a) in {(2, 247), (8, 28), (9, 24), (9, 55), (9, 69), (9, 85), (10, 88), (11, 29), (11, 87), (17, 6), (17, 64), (18, 34), (18, 39), (18, 46), (23, 55), (27, 36), (33, 27), (34, 35), (34, 37), (57, 20), (63, 9), (64, 15), (71, 12)}:
            return "Dünya süsü olarak mal ve soyun sınama boyutu (`2:247`, `8:28`, `9:24,55,69,85`, `10:88`, `11:29,87`, `17:6,64`, `18:34,39,46`, `23:55`, `27:36`, `33:27`, `34:35,37`, `57:20`, `63:9`, `64:15`, `71:12`): Mal çokluğunu üstünlük veya yakınlık ölçüsü sanma (`2:247`, `18:34,39,46`, `34:35,37`, `57:20`), elçilerin mal karşılığı istememesi ve Süleyman'ın mal teklifini reddi (`11:29`, `27:36`), mal ve çocukların yalnız bir sınav/ziynet oluşu (`8:28`, `9:24,55,69,85`, `10:88`, `63:9`, `64:15`) ve saptırıcı gücün ortaklık aradığı bir alan (`17:64`) olması yanında şükür ve yöneliş karşılığında maddî destek verilmesi (`17:6`, `33:27`, `71:12`, `23:55`)."
        return "Tutkulu yığma, hak yoldan alıkoyma ve hesap gününde malın işlevsizliği (`3:10,116`, `8:36`, `19:77`, `26:88`, `58:17`, `68:14`, `69:28`, `71:21`, `74:12`, `89:20`, `90:6`, `92:11`, `104:2,3`, `111:2`): Malı aşırı sevip yığınla övünme (`68:14`, `74:12`, `89:20`, `90:6`, `104:2`), ölümsüzlük sanısı (`104:3`), hak yoldan engellemeye harcama (`8:36`) ve son durakta 'malım bana fayda vermedi (`69:28 مَالِيَهْ`)' çığlığıyla malın tam çaresizliği (`3:10,116`, `26:88`, `58:17`, `71:21`, `92:11`, `111:2`)."

    if root_ar == 'أ-ح-د':
        if (s, a) in {(2, 102), (18, 26), (18, 38), (18, 42), (18, 110), (35, 41), (69, 47), (72, 2), (72, 7), (72, 18), (72, 20), (72, 22), (72, 26), (89, 25), (89, 26), (112, 1), (112, 4)}:
            return "Mutlak ilâhî birlik, ortaksız egemenlik ve eşsiz kudret (`2:102`, `18:26,38,42,110`, `35:41`, `69:47`, `72:2,7,18,20,22,26`, `89:25,26`, `112:1,4`): Yaratıcı kendi özünde bölünmez ve benzersiz Tek'tir (`112:1`), dengi yoktur (`112:4`), hükmüne, duasına ve kulluğuna hiç kimse ortak katılmaz (`18:26,38,42,110`, `72:2,18,20`), izni olmaksızın kimse kimseye zarar veremez (`2:102`), O'ndan başka gökleri-yeri tutacak, gayba ulaştıracak, koruyacak veya O'nun gibi azap edip bağlayacak hiçbir varlık yoktur (`35:41`, `69:47`, `72:7,22,26`, `89:25,26`)."
        if (s, a) in {(2, 136), (2, 282), (2, 285), (3, 73), (3, 84), (4, 152), (9, 4), (9, 6), (9, 84), (24, 6), (33, 32), (33, 39), (33, 40), (49, 9), (59, 11)}:
            return "Elçiler arası eşit güven, şahitlik hukuku ve ahit ahlakı (`2:136,282,285`, `3:73,84`, `4:152`, `9:4,6,84`, `24:6`, `33:32,39,40`, `49:9`, `59:11`): Elçilerin hiçbiri arasında ayrım gözetmeme (`2:136,285`, `3:84`, `4:152`), yazışmalı borç hukukunda iki şahitten biri unuttuğunda diğerinin hatırlatması (`2:282`), dörtlü şahitlik beyanı (`24:6`), bozulmayan anlaşmaya bağlılık ve sığınan her bireye güvence verme (`9:4,6`), gerçeği örten ölünün ardında durmama (`9:84`), elçinin konumu ve yalnız Allah'tan çekinme (`33:32,39,40`), çatışan iki gruptan birinin taşkınlığına adaletle müdahale (`49:9`) ile sahte dostluk ve seçilmişlik iddialarının aşılması (`3:73`, `59:11`)."
        if (s, a) in {(2, 180), (4, 18), (4, 20), (4, 43), (5, 6), (5, 106), (6, 61), (12, 4), (12, 36), (12, 41), (12, 78), (16, 58), (17, 23), (23, 99), (28, 25), (28, 26), (28, 27), (43, 17), (63, 10)}:
            return "Ecel anı sorumluluğu, aile hukuku ve ikili örneklerde tekil kişi (`2:180`, `4:18,20,43`, `5:6,106`, `6:61`, `12:4,36,41,78`, `16:58`, `17:23`, `23:99`, `28:25-27`, `43:17`, `63:10`): Her bir ferde ölüm yaklaştığında vasiyet ve şahitlik (`2:180`, `5:106`, `6:61`) yahut son dakika pişmanlığının fayda vermemesi (`4:18`, `23:99`, `63:10`), ihtiyaç halinde su yerine temiz toprakla arınma (`4:43`, `5:6`), eşe verilen mehri geri almama (`4:20`), anne-babadan biri yaşlandığında hürmet (`17:23`), kız çocuğu haberiyle öfkelenen cahiliye tavrı (`16:58`, `43:17`), Medyenli iki kızdan biri (`28:25-27`) ve Yûsuf kıssasında on bir yıldız ile zindan ve kardeş olayları (`12:4,36,41,78`)."
        if (s, a) in {(2, 96), (2, 266), (3, 91), (5, 27), (5, 115), (7, 80), (16, 76), (18, 32), (18, 47), (18, 49), (19, 98), (24, 21), (29, 28), (35, 42), (74, 35), (90, 5), (90, 7), (92, 19)}:
            return "Hesap eksiksizliği, uyarı ölçüleri ve hiçbir bireyin dışta kalmayışı (`2:96,266`, `3:91`, `5:27,115`, `7:80`, `16:76`, `18:32,47,49`, `19:98`, `24:21`, `29:28`, `35:42`, `74:35`, `90:5,7`, `92:19`): Bin yıl yaşama tutkusu ve bahçesi yanan ihtiyarın durumu (`2:96,266`), fidyeyle kurtulmanın imkânsızlığı (`3:91`), Âdem'in iki oğlundan birinin sunusu (`5:27`), emsalsiz sapma ve ceza uyarıları (`5:115`, `7:80`, `29:28`, `74:35`), sicil defterinde kimsenin dışlanmayıp haksızlık edilmemesi (`18:47,49`), geçmiş nesillerin tamamen silinmesi (`19:98`), bağlayıcı sözden dönüş (`35:42`), Allah'ın lütfu olmadan kimsenin arınamayacağı (`24:21`), kimsenin gücünün yetmeyeceğini/görmediğini sanma (`90:5,7`) ve kimseden karşılık beklemeden paylaşma (`92:19`)."
        return "Toplum adabı, ihtiyatlı gizlilik ve sınav sahnelerinde tekil fert (`3:153`, `5:20`, `8:7`, `9:52,127`, `11:81`, `15:65`, `18:19,22`, `19:26`, `24:28`, `38:35`, `49:12`): Çatışmadan kaçarken kimseye dönüp bakmama ve kaypakların bakışması (`3:153`, `9:127`), iki grup veya iki güzellikten biri (`8:7`, `9:52`), Mûsâ kavmine ve Süleyman'a başka kimseye verilmeyen lütuf (`5:20`, `38:35`), Lût ailesine geriye dönüp bakmama emri (`11:81`, `15:65`), Ashâb-ı Kehf'in içlerinden birini gönderip kimseye sezdirmemesi ve kimseden fetva sormama (`18:19,22`), Meryem'in kimseyle konuşmama adayı (`19:26`), izinsiz eve girmeme (`24:28`) ve gıybet yasağı (`49:12`)."

    if root_ar == 'ن-ج-و':
        if (s, a) in {(2, 49), (2, 50), (7, 141), (10, 86), (10, 92), (14, 6), (20, 40), (20, 80), (28, 21), (28, 25), (44, 30), (66, 11)}:
            return "Firavun zorbalığından, denizden ve zalim toplumdan kurtuluş (`2:49-50`, `7:141`, `10:86,92`, `14:6`, `20:40,80`, `28:21,25`, `44:30`, `66:11`): İsrâiloğullarının ağır esaretten ve denizin yarılmasıyla boğulmaktan çekilip çıkarılması (`2:49-50`, `7:141`, `14:6`, `20:80`, `44:30`), Firavun'un bedeninin ibret için karaya çıkarılması (`10:92`), Mûsâ'nın kederden ve zalimlerden kurtuluşu (`20:40`, `28:21,25`) ile zalim toplumdan ve Firavun'dan kurtuluş yakarışları (`10:86`, `66:11`)."
        if (s, a) in {(7, 64), (7, 72), (7, 83), (7, 89), (10, 73), (11, 58), (11, 66), (11, 94), (11, 116), (15, 59), (21, 9), (21, 71), (21, 74), (21, 76), (21, 88), (23, 28), (26, 65), (26, 118), (26, 119), (26, 169), (26, 170), (27, 53), (27, 57), (29, 15), (29, 24), (29, 32), (29, 33), (37, 76), (37, 115), (37, 134), (41, 18), (54, 34)}:
            return "Toplu helak ortasında elçilerin ve güvenenlerin seçilerek kurtarılması (`7:64,72,83,89`, `10:73`, `11:58,66,94,116`, `15:59`, `21:9,71,74,76,88`, `23:28`, `26:65,118-119,169-170`, `27:53,57`, `29:15,24,32-33`, `37:76,115,134`, `41:18`, `54:34`): Nûh'un gemiyle tufandan (`7:64`, `10:73`, `21:76`, `23:28`, `26:118-119`, `29:15`, `37:76`), Hûd, Sâlih ve Şuayb'ın rahmetle helakten (`7:72,89`, `11:58,66,94`, `27:53`, `41:18`), Lût'un ve ailesinin seher vakti kirli şehirden (`7:83`, `15:59`, `21:71,74`, `26:169-170`, `27:57`, `29:32-33`, `37:134`, `54:34`), İbrâhîm'in ateşten (`29:24`), Yûnus'un karanlık darlıktan (`21:88`) ve Mûsâ ile Hârûn'un büyük sıkıntıdan (`26:65`, `37:115`) çekip alınması; bozgunculuğa karşı çıkan azınlığın kurtuluşu (`11:116`, `21:9`)."
        if (s, a) in {(6, 63), (6, 64), (7, 165), (10, 22), (10, 23), (10, 103), (12, 42), (12, 45), (12, 110), (17, 67), (19, 72), (29, 65), (31, 32), (39, 61), (40, 41), (61, 10), (70, 14)}:
            return "Kurtuluş yasası, deniz fırtınası sınavı ve gerçek kurtuluşa çağrı (`6:63-64`, `7:165`, `10:22-23,103`, `12:42,45,110`, `17:67`, `19:72`, `29:65`, `31:32`, `39:61`, `40:41`, `61:10`, `70:14`): Karanlıklarda ve dalgalarda içtenlikle yakarıp karaya çıkarılınca yeniden ortak koşma veya azgınlaşma döngüsü (`6:63-64`, `10:22-23`, `17:67`, `29:65`, `31:32`), kötülükten men edenlerin ve sakınanların kurtarılması yasası (`7:165`, `10:103`, `12:110`, `19:72`, `39:61`), zindandan kurtulan arkadaş (`12:42,45`), ateşe karşı kurtuluşa çağrı (`40:41`), can yakıcı azaptan kurtaran kazançlı yol (`61:10`) ve hesap gününde herkesi feda edip kurtulmak isteyen suçlu (`70:14`)."
        return "Tenhaya çekilip gizlice konuşma etiği ve ilâhî şahitlik (`4:114`, `9:78`, `12:80`, `17:47`, `19:52`, `20:62`, `21:3`, `43:80`, `58:7-10,12-13`): Paylaşım, iyilik ve barış dışındaki gizli konuşmalarda hayır olmaması (`4:114`), sırların ve fısıltıların bilinmesi (`9:78`, `43:80`, `58:7`), kardeşlerin ve büyücülerin kenara çekilip gizlice danışması (`12:80`, `20:62`), elçiye karşı gizli kumpas fısıltıları (`17:47`, `21:3`, `58:8,10`), Mûsâ'nın özel konuşma için yaklaştırılması (`19:52`), iyilik ve sakınma üzerine fısıldaşma emri (`58:9`) ve elçiyle baş başa görüşme öncesi paylaşım ölçüsü (`58:12-13`)."

    if root_ar == 'س-و-ي':
        if (s, a) in {(2, 29), (7, 54), (10, 3), (13, 2), (20, 5), (25, 59), (32, 4), (41, 11), (57, 4)}:
            return "Göklerin düzenlenmesi ve evrensel egemenlik makamına kurulma (`2:29`, `7:54`, `10:3`, `13:2`, `20:5`, `25:59`, `32:4`, `41:11`, `57:4`): Henüz duman halindeki göğe sapmadan düz hatla yönelme (`2:29`, `41:11`), yedi göğü pürüzsüz uyumla düzenleme ve evrensel yönetim makamına (`ٱلْعَرْش`) sarsıntısız, tam bir denge, kontrol ve istikrarla kurulma."
        if (s, a) in {(4, 95), (5, 100), (6, 50), (9, 19), (11, 24), (13, 16), (16, 75), (16, 76), (32, 18), (35, 12), (35, 19), (35, 22), (39, 9), (39, 29), (40, 58), (41, 34), (57, 10), (59, 20)}:
            return "Nitelik, emek ve bilinç eşitsizliğinin ilânı (`4:95`, `5:100`, `6:50`, `9:19`, `11:24`, `13:16`, `16:75-76`, `32:18`, `35:12,19,22`, `39:9,29`, `40:58`, `41:34`, `57:10`, `59:20`): Kör ile görenin, aydınlık ile karanlığın, temiz ile pisin, bilen ile bilmeyenin, emek veren ile oturanın asla aynı basamakta ve terazi kefesinde denk olmayacağı (`لَا يَسْتَوِى / هَلْ يَسْتَوِى`)."
        if (s, a) in {(2, 6), (7, 193), (13, 10), (14, 21), (16, 71), (26, 98), (26, 136), (30, 28), (36, 10), (52, 16), (63, 6)}:
            return "İki karşıt seçeneğin farksızlığı ve sahte denklik kurma yanılgısı (`2:6`, `7:193`, `13:10`, `14:21`, `16:71`, `26:98,136`, `30:28`, `36:10`, `52:16`, `63:6`): Gerçeğin üzerini kasten örten şartlanmış bilinçte uyarı ile uyarısızlığın aynı kapıya çıkması (`2:6`, `36:10`, `63:6`), direnç gösterme ile feryat etmenin azap karşısında eşit sonuç vermesi (`14:21`, `52:16`), rızıkta kulların kendi ortaklarıyla eşitlenmeyi kabullenmeyişi (`16:71`, `30:28`) ve sahte mercileri evrenin Rabbine denk tutma itirafı (`26:98`)."
        if (s, a) in {(2, 108), (3, 64), (3, 113), (4, 89), (5, 12), (5, 60), (5, 77), (8, 58), (20, 58), (21, 109), (22, 25), (28, 22), (37, 55), (38, 22), (41, 10), (44, 47), (45, 21), (60, 1)}:
            return "Ortak adil hiza, şeffaf eşitlik zemini ve dosdoğru orta yol (`2:108`, `3:64,113`, `4:89`, `5:12,60,77`, `8:58`, `20:58`, `21:109`, `22:25`, `28:22`, `37:55`, `38:22`, `41:10`, `44:47`, `45:21`, `60:1`): Ortak ve adil ilkeye çağrı (`3:64`), antlaşma feshinde tarafları eşit bilgi zeminine koyma (`8:58`), arayan her canlıya yeryüzü imkanlarının eşit sunulması (`41:10`), Mûsâ ile sihirbazların eşit mesafedeki açık meydanda buluşması (`20:58`), ateşin tam orta merkezi (`37:55`, `44:47`) ve ana rotadan sapma (`سَوَآءَ ٱلسَّبِيلِ`)."
        return "Fiziksel, biyolojik ve mekânsal düzleme, denge ve donanım (`4:42`, `11:44`, `15:29`, `18:37,96`, `19:10,17,43`, `20:135`, `23:28`, `28:14`, `32:9`, `38:72`, `43:13`, `48:29`, `53:6`, `67:22`, `75:4,38`, `79:28`, `82:7`, `87:2`, `91:7,14`): Dağlar arasına demir doldurup aynı seviyeye getirme (`18:96`), geminin Cûdî ve bineklerin sırtında dengeli duruşu (`11:44`, `23:28`, `43:13`), ekinin sapında dimdik doğrulması (`48:29`), Mûsâ'nın olgunluk çağına ermesi (`28:14`), parmak uçlarının ve benliğin kusursuz oranlanması (`75:4`, `91:7`), sağlıklı organ dengesi (`19:10`), yüzüstü kapaklanmadan dik yürüme (`67:22`) ve Semûd yurdunun yerle bir düzlenmesi (`91:14`, `4:42`)."

    if root_ar == 'ك-ي-ف':
        if (s, a) in {(3, 6), (5, 64), (30, 48)}:
            return "Soru anlamı taşımayan hâl ve tasarım tarzı belirleyicisi (`3:6`, `5:64`, `30:48`): Ana rahimlerinde insanları (`3:6`), rızık/kaynak akışını (`5:64`) ve gökteki bulut yayılımını (`30:48`) dilediği biçim, desen ve dağıtım düzeniyle (`كَيْفَ يَشَآءُ`) şekillendirme işleyişi."
        if (s, a) in {(2, 259), (2, 260), (5, 31), (25, 45), (29, 19), (29, 20), (30, 50), (50, 6), (71, 15), (88, 17), (88, 18), (88, 19), (88, 20)}:
            return "Doğrudan gözleme dayalı fiziksel, biyolojik, kozmolojik ve pratik süreç incelemesi (`2:259-260`, `5:31`, `25:45`, `29:19-20`, `30:50`, `50:6`, `71:15`, `88:17-20`): Karganın toprağı eşeleyip gömme yöntemini göstermesi (`5:31`), kemiklerin kaldırılıp et giydirilmesi ve diriltme mekanizması (`2:259-260`), gölge fiziği (`25:45`), yaratılışın başlangıcı ve toprağın canlanması (`29:19-20`, `30:50`), göklerin tabakalı yapısı ile devenin, dağların ve yeryüzünün somut tasarım düzeni (`50:6`, `71:15`, `88:17-20`)."
        if (s, a) in {(3, 137), (6, 11), (7, 84), (7, 86), (7, 103), (10, 39), (10, 73), (12, 109), (14, 45), (16, 36), (27, 14), (27, 51), (27, 69), (28, 40), (30, 9), (30, 42), (35, 44), (37, 73), (40, 21), (40, 82), (43, 25), (47, 10), (89, 6), (105, 1)}:
            return "Tarihsel ve arkeolojik sonuç gözlemi (`3:137`, `6:11`, `7:84,86,103`, `10:39,73`, `12:109`, `14:45`, `16:36`, `27:14,51,69`, `28:40`, `30:9,42`, `35:44`, `37:73`, `40:21,82`, `43:25`, `47:10`, `89:6`, `105:1`): Yeryüzünde gezip önceki toplumların, yalanlayıcıların, bozguncuların, Âd ve Fil ordusunun akıbetinin hangi somut yasalar ve süreçlerle gerçekleştiğini yerinde inceleme çağrısı."
        if (s, a) in {(3, 25), (4, 41), (4, 62), (7, 93), (13, 32), (22, 44), (34, 45), (35, 26), (40, 5), (47, 27), (54, 16), (54, 18), (54, 21), (54, 30), (67, 18), (73, 17)}:
            return "Sonuç bağlacıyla (`فَكَيْفَ`) çarpıcı yüzleştirme ve kaçınılmaz netice sorgusu (`3:25`, `4:41,62`, `7:93`, `13:32`, `22:44`, `34:45`, `35:26`, `40:5`, `47:27`, `54:16,18,21,30`, `67:18`, `73:17`): Büyük hesap anı, tanıklık yüzleşmesi veya kural ihlalinin doğurduğu ağır karşılık (`عِقَابِ / نَكِيرِ / عَذَابِى`) karşısında insanın içine düşeceği çarpıcı hâlin muhatabın vicdanına bırakılması."
        if (s, a) in {(2, 28), (3, 86), (3, 101), (4, 21), (5, 43), (6, 81), (9, 7), (9, 8), (10, 35), (18, 68), (19, 29), (37, 154), (68, 36), (74, 19), (74, 20)}:
            return "Açık olgu ve ölçüt karşısında mantıksal çelişki yüzleştirmesi (`2:28`, `3:86,101`, `4:21`, `5:43`, `6:81`, `9:7-8`, `10:35`, `18:68`, `19:29`, `37:154`, `68:36`, `74:19-20`): Diriltilmiş olma, sağlam ahit, elde metin bulunması veya bilgi sınırı gibi somut gerçekler ortadayken tutarsız davranışın, çarpık hüküm ölçütünün (`مَا لَكُمْ كَيْفَ تَحْكُمُونَ`) ve kurgusal çarpıtmanın (`كَيْفَ قَدَّرَ`) mantıksal zeminsizliğini açığa çıkarma."
        return "İletişim, kanıt tasrifi ve eylem niteliği incelemesi (`4:50`, `5:75`, `6:24,46,65`, `7:129`, `10:14`, `14:24`, `17:21,48`, `25:9`, `67:17`): Kanıtların farklı açılardan açıklanma biçimi (`كَيْفَ نُصَرِّفُ / نُبَيِّنُ`), örnek kurma yöntemleri (`كَيْفَ ضَرَبَ / ضَرَبُوا۟`), yalan uydurma biçimleri (`4:50`, `6:24`) ve toplumlara emanet edilen sorumlulukta nasıl iş ortaya koyduklarının sahada gözlemlenmesi (`7:129`, `10:14`)."

    if root_ar in DYNAMIC_ROOT_SPECS:
        spec = DYNAMIC_ROOT_SPECS[root_ar]
        for cluster in spec.get('context_clusters', []):
            if _rule_matches(cluster, lemma, pos, features, s, a, word_rasm):
                return cluster['text']
        if spec.get('context_default'):
            return spec['context_default']

    raise ValueError(f"Açıklama üretilemedi: root={root_ar}, lemma={lemma}, ref={s}:{a}")


def build_root(ar_root, corpus=None, locked_roots_data=None, purified_turkish=None):
    """Tek bir kilitli kök için `data/kavramlar/<slug>.json` dosyasını üretir."""
    cfg = ROOT_CONFIG[ar_root]
    bw_root = cfg['buckwalter']

    if corpus is None:
        corpus = QuranCorpus()
    if locked_roots_data is None:
        with open(os.path.join(DATA_DIR, 'locked_roots.json'), 'r', encoding='utf-8') as f:
            locked_roots_data = json.load(f)
    if purified_turkish is None:
        raw_tr = load_verses(os.path.join(DATA_DIR, 'quran-turkish.txt'))
        purified_turkish = {ref: purify_tabula_rasa(txt) for ref, txt in raw_tr.items()}

    locked_data = locked_roots_data['locked_roots'][ar_root]
    word_groups = corpus.get_root_word_groups(bw_root)

    ayah_occurrences = []
    for (s, a, w), segs in word_groups:
        surah_name = SURAH_NAMES.get(s, f"Sûre {s}")
        ayah_text_ar = corpus.ayahs_uthmani.get((s, a), '')
        ayah_text_tr = purified_turkish.get((s, a), '')

        words_in_ayah = extract_ayah_words(ayah_text_ar, s, a)
        if not (0 <= (w - 1) < len(words_in_ayah)):
            raise IndexError(f"Kelime indeksi taşması: {ar_root} {s}:{a} w={w} len={len(words_in_ayah)}")

        target_word_uthmani = words_in_ayah[w - 1]
        target_word_rasm = strip_tashkeel(target_word_uthmani)

        stem_seg = next((sg for sg in segs if 'STEM' in sg['features']), segs[0])
        pos = stem_seg['tag']
        features = stem_seg['features']
        lemma = stem_seg['lem']

        literal_irab = determine_literal_irab(ar_root, lemma, pos, features, s, a)
        explanation = generate_contextual_explanation(
            ar_root, target_word_uthmani, target_word_rasm, lemma, pos, features, s, a, surah_name
        )

        start_idx = max(0, w - 4)
        end_idx = min(len(words_in_ayah), w + 3)
        context_snippet_ar = " ".join(words_in_ayah[start_idx:end_idx])
        context_snippet_tr = extract_turkish_snippet(ayah_text_tr, ar_root)

        ayah_occurrences.append({
            'surah': s,
            'ayah': a,
            'surah_name': surah_name,
            'ayah_ref': f"{s}:{a}",
            'word_position': w,
            'target_word_uthmani': target_word_uthmani,
            'target_word_rasm': target_word_rasm,
            'target_word_literal_irab': literal_irab,
            'context_snippet_arabic': context_snippet_ar,
            'context_snippet_turkish_tabula_rasa': context_snippet_tr,
            'morphology': {
                'lemma': lemma,
                'pos': pos,
                'features': features,
            },
            'ayah_text_arabic_full': ayah_text_ar,
            'ayah_text_turkish_tabula_rasa_full': ayah_text_tr,
            'contextual_meaning': explanation,
        })

    unique_ayahs = len(set((o['surah'], o['ayah']) for o in ayah_occurrences))
    concept_file_data = {
        'root': ar_root,
        'root_latin': locked_data['root_latin'],
        'concept_name': cfg['concept_name'],
        'rank': locked_data.get('rank'),
        'total_occurrences': len(ayah_occurrences),
        'unique_ayahs_count': unique_ayahs,
        'unified_core_mechanism': locked_data['unified_core_mechanism'],
        'physical_core': locked_data['physical_core'],
        'dictionary_arbitration': locked_data['dictionary_arbitration'],
        'semitic_cognates': locked_data['semitic_cognates'],
        'mesani_opposite': locked_data['mesani_opposite'],
        'same_ayah_furuk': locked_data['same_ayah_furuk'],
        'anchor_ayahs': locked_data['anchor_ayahs'],
        'grammar_and_branch_rules': locked_data['grammar_and_branch_rules'],
        'derivatives': locked_data['derivatives'],
        'ayah_occurrences': ayah_occurrences,
    }

    kavramlar_dir = os.path.join(DATA_DIR, 'kavramlar')
    os.makedirs(kavramlar_dir, exist_ok=True)
    output_filename = os.path.join(kavramlar_dir, f"{cfg['slug']}.json")
    with open(output_filename, 'w', encoding='utf-8') as out_f:
        json.dump(concept_file_data, out_f, ensure_ascii=False, indent=2)

    print(f"Kavram dosyası üretildi: {cfg['slug']}.json ({len(ayah_occurrences)} geçiş, {unique_ayahs} ayet)")
    return output_filename


def build_all():
    corpus = QuranCorpus()
    with open(os.path.join(DATA_DIR, 'locked_roots.json'), 'r', encoding='utf-8') as f:
        locked_roots_data = json.load(f)
    raw_tr = load_verses(os.path.join(DATA_DIR, 'quran-turkish.txt'))
    purified_turkish = {ref: purify_tabula_rasa(txt) for ref, txt in raw_tr.items()}

    for ar_root in ROOT_CONFIG:
        if ar_root in locked_roots_data['locked_roots']:
            build_root(ar_root, corpus=corpus, locked_roots_data=locked_roots_data, purified_turkish=purified_turkish)


if __name__ == '__main__':
    build_all()
