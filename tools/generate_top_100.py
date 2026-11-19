# -*- coding: utf-8 -*-
"""
Kur'an'da En Çok Geçen 100 Kök ve Kavram Haritalayıcı
Tabula Rasa Mesânî Çözümleme Sistemi (v3.0)
"""

import os
import re
import sys
import json
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quran_analyzer import DATA_DIR, to_arabic_root, to_latin_root

# Accurate descriptive concept labels in Tabula Rasa perspective
CONCEPT_LABELS = {
    'Alh': 'İlâh / Allâh (Yegâne Mutlak Sığınak ve Otorite Mercii)',
    'qwl': 'Kavl (Söz, İfade, Dışa Vurum ve Beyan)',
    'kwn': 'Kevn / Kâne (Yerleşip Ortaya Çıkma, Oluş ve Sabit Gerçeklik)',
    'rbb': 'Rabb (Besleyip Büyüten, Onarıp Olgunlaştıran Sahip ve Otorite)',
    'Amn': 'İman / Güven (Şüphesiz İçsel Emniyet ve Güven Bağı)',
    'Elm': 'İlim / Alîm / Âlem (Ayırt Edici İz, İşaret ve Doğrudan Bilgi)',
    'qwm': 'Kıyâm / İkāmet (Ayağa Kalkış, Duruş, Ayakta Tutma)',
    'Aty': 'İtâ / İtyân (Engelsiz Akıp Gelmek, Yönelip Ulaşmak ve Teslim Etmek)',
    'kfr': 'Küfür (Gerçeğin Üzerini Örtme, Yok Sayma)',
    '$yA': 'Şey / Meşîet (İrade ile Seçip Oldurmak, Varlık Birimi)',
    'byn': 'Beyân / Beyn (Aralık Açma, Sınırını Ayırıp Belirginleştirme)',
    'rsl': 'İrsâl / Resûl (Salıp Göndermek, Akıtmak, Görevli Elçi)',
    'ArD': 'Arz (Alt Taban, Üzerinde Yaşanılan Zemin ve Coğrafya)',
    'ywm': 'Yevm (Zaman Birimi, Aydınlık Döngü, Tarihsel Dönem / Aşama)',
    'Ayy': 'Âyet (Açık İşaret, Doğal Kanıt, Bilgilendirici Metin Birimi)',
    'smw': 'Semâ / İsim (Üst Kozmik Katman, Tavan ve Tanımlayıcı Ad)',
    'E*b': 'Azap (Tatlılıktan Kesilme, Mahrumiyet ve Ağır Yaptırım / Acı)',
    'kll': 'Küll / Kelâle / Kell (Kapsayan Bütünlük, Yanal Akrabalık ve Ağır Yük)',
    'Eml': 'Amel (Bilinçli Eylem, İş, Emek ve Üretim)',
    'jEl': 'Ce\'l (Kılmak, Düzenlemek, İşlev ve Rol Atamak)',
    'rHm': 'Rahmet (Kuşatıcı Şefkat, Besleyici Koruma ve Rahim Bağı)',
    'rAy': 'Re\'y / Rüya (Görmek, Zihinsel İdrak, Göstermek ve Görüş)',
    'ktb': 'Kitap / Ketb (Yazmak, Sabitlemek, Bağlayıcı Yasa ve Kayıt)',
    'hdy': 'Hidayet / Hedy (Zarafetle Yol Göstermek, Doğrultu Vermek ve Armağan Sunmak)',
    'Zlm': 'Zulüm / Zulumât (Karanlık, Bir Şeyi Yerinden Etmek ve Haksızlık)',
    'nfs': 'Can / Benlik / Soluk (Kişilik, Öz, Hayat Nefesi ve Yarış)',
    'nzl': 'Nüzûl / Tenzîl (Ölçülü İndirme, Kademeli Ulaştırma ve Konaklama İkramı)',
    'qbl': 'Kabûl / Kıble / Kabile (Yüz Yüze Karşılama, Yönelim ve Öncelik)',
    '*kr': 'Zikir / Zekâr (Zihinde İz Tutma, Unutmama, Hatırlatma ve Eril Cinsiyet)',
    'Hqq': 'Hak (Örtüşen Sağlam Gerçek, Sabit Ölçü, Hak Edilen Pay ve Borç)',
    'k*b': 'Kizb / Tekzîb (Beklentiyi Boşa Çıkarma, Gerçeği Çarpıtma ve Kanıtı Yalanlama)',
    'jyA': 'Mecî\' (Ağırlıklı Varmak, Somut Sonuç Getirmek ve Geri Dönülmez Ortaya Çıkış)',
    'Ebd': 'Abd / Ubûdiyet (Düzlenmiş Yol Gibi Boyun Eğme, Emek Sunma ve Bilinçli Hizmet Bağlılığı)',
    'Ax*': 'Ahz / İttihâz (Kavramak, Somut Yakalayış ve Kalıcı Olarak Edinmek)',
    'xlq': 'Halk (Ölçüp Tasarlamak, Oranlı Biçim Vermek, Pay ve İç Karakter)',
    'wqy': 'Vikâye / İttikâ (Kalkan Tutma, Zarardan Korunma ve Sorumluluk Bilinci)',
    'Axr': 'Âhir / Âhar / Te’hîr (Sonraki Aşama, Öteki Birim ve Geriye Bırakma)',
    'Amr': 'Emr (Yönlendirici İşaret, Karar, İşletim Düzeni ve Süreç)',
    'nws': 'Nâs (Hareketli İnsanlık Toplumu ve Kamuoyu)',
    'gfr': 'Mağfiret / Gufrân (Miğfer Gibi Örtüp Zırhlama ve Kusurun Üstünü Kapatma)',
    'wly': 'Velâyet / Tevellî (Bitişik Yakınlık, Sahiplenip Üstlenme ve Sırt Çevirme)',
    'bEd': 'Bu\'d / Ba\'d (Araya Giren Mesafe, Uzaklık, Ardından Gelme ve Tarihten Silinme)',
    'dEw': 'Da\'vet / Duâ (Seslenerek Kendine Çekme, Çağrı, Adlandırma ve Talep)',
    'Hkm': 'Hüküm / Hikmet (Gem Vurup Frenleme, Sağlamlaştırma, Ölçülü Karar ve Bilgelik)',
    'mlk': 'Mülk / Melik / Kozmik Görev (Sağlam Tutup Hükümranlık Etme, Sahiplik ve Görevli Güçler)',
    'jnn': 'Cennât / Cânn / Cünûn (Örtüp Gizleme, Sık Esenlik Bahçesi, Görünmeyen Bilinç ve Zihin Örtülmesi)',
    'xyr': 'Hayr / İhtiyâr (Seçkin İyi, Faydalı Değer-Mal ve Bilinçli Seçim)',
    'End': 'İnd / Anîd (Bitişik Yan, Kaynak Katı, Huzur ve Hizadan Sapıp Direnme)',
    'nwr': 'Nûr / Nâr / Münîr (Berrak Aydınlık, Yakıcı Ateş ve Yol Açıcı Işık)',
    'Hsn': 'Hüsn / İhsân / Ahsen (Sağlam Uyum, Ölçülü Güzellik ve İşi Özenle Tam Yapma)',
    'Dll': 'Dalâlet / Tadlîl (Pusula Kaybı, İz Silinmesi ve Doğru Yoldan Şaşma)',
    'smE': 'Sem\' / İstima\' (Ses Yakalama, Dikkatle Kulak Verme ve Yanıtla İçselleştirme)',
    'bny': 'Binâ / İbn (Taş Taş Örüp Yapı Kurmak, Soy Ve Aidiyet İnşası)',
    'Hyy': 'Hayat / Hayy / İhyâ / İstihyâ (Canlılık, İşlevsel Dirilik, Sağ Bırakma ve Hassas Sakınma)',
    'xrj': 'Hurûc / İhrâc / İstihrâc (Kapalı Sınırı Yarıp Dışarı Çıkmak, Açığa Çıkarmak ve Sürgün)',
    'SlH': 'Salâh / İslâh / Sâlihât / Sulh (Bozulmayı Giderip İşlevsel Dengeye Getirmek, Onarmak ve Barışı Kurmak)',
    'sbl': 'Sebîl / Sübül (Engelsiz İşlek Akış, Geçiş Yolu, Yöntem ve Sorumluluk Kapısı)',
    'tbE': 'İttibâ\' / Teba\' / İtbâ\' (Adım Adım İz Sürmek, Peşinden Yetişip Takip Etmek ve Örnek Almak)',
    'Awl': 'Evvel / Âl / Ülî / Te\'vîl (Başlangıç Kaynağı, Dönüp Bağlanan Yakın Çevre, Nitelik Sahipleri ve Asıl Sonuç)',
    'qtl': 'Katl / Kıtâl / Taktîl / İktitâl (Can Bağını Kesip Etkisizleştirme, Karşılıklı Çarpışma ve İç Çatışma)',
    'mvl': 'Mesel / Misil / Timsâl / Temessül (Karşılıklı Denk Model, Eşdeğer Ölçü, Örnek Tablo ve Surete Bürünme)',
    'qlb': 'Kalp / Taklîb / İnkılâb (Merkez Öz, Bilişsel Dönüşüm Odası ve Tersine Çevrilip Dönüş)',
    '$rk': 'Şerîk / İştirâk / İştikâk (Paydaş Kılma, Yetki Bölüşümü ve Ortaklık Kurma)',
    'kvr': 'Kesret / Ekser / Tekâsür / Kevser (Sayısal Çokluk, Yığılma Yarışı ve Taşkın Hayır Kaynağı)',
    'swA': 'Sû\' / Seyyie / Sev\'e / İsâe (Çirkinlik, Keder Veren Bozukluk, Zarar ve Kusur)',
    'mwt': 'Mevt / Memât / Meyyit / İmâte (Güç ve İşlevin Çekilmesi, Durağanlaşma ve Evre Değişimi)',
    'kbr': 'Kibr / Kebîr / Ekber / İstikbâr (Büyüklük, İleri Yaş ve Haksız Büyüklenme)',
    '$hd': 'Şehâdet / Şâhid / Şehîd / Meşhûd (Yerinde Hazır Bulunuş, Açık Gözlem ve Sorumlu Tanıklık)',
    'nbA': 'Nebe\' / Nebî / Nübüvvet / İnbâ (Büyük Haber, Geçmişten Geleceğe Bilgi Aktarma ve Haber Elçiliği)',
    'bED': 'Ba\'z / Ba\'ûda (Bütünden Ayrılan Parça, Karşılıklı Bağlantı ve Sivrisinek)',
    'nSr': 'Nasr / Nasîr / Ensâr / İntisâr / Nasârâ (Hayır ve Güç Ulaştırma, Aktif Destek ve Haklı Savunma)',
    'Sdq': 'Sıdk / Sadâkat / Sadaka / Tasdik (Sağlamlık, Söz-Eylem Örtüşmesi, Doğrulama ve Özden Paylaşım)',
    'gyr': 'Gayr / Tağyîr / Muğîrât (Sınır Çizen Başkalık, Nitelik Değişimi ve Öz-Eksen Dönüşüm)',
    'wEd': 'Va\'d / Vaîd / Mevid / Mîâd (Geleceğe Bağlayıcı Söz-Hedef Kurma, Belirlenmiş Vade ve Yaptırım Uyarısı)',
    'bSr': 'Basar / Basîret / İbsâr (Seçik Görme, Ayırt Edici İçgörü ve Kanıtla Fark Etme)',
    'rwd': 'İrâde / Murâvede / Ruveyd (Hedefe Yönelme, Meyletme, Çekerek Döndürmeye Çalışma ve Yumuşak Mühlet)',
    'lqy': 'Likā / İlkā / Telakkî / İltikā (Karşılaşma-Yüzleşme ve Önüne Bırakıp Ulaştırma)',
    'dwn': 'Dûn (Üst Sınırın Berisinde ve Altında Kalan, İkincil veya Dışındaki Konum)',
    'nEm': 'Nimet / Naîm (Yumuşak Refah, Hoşluk ve İyilik Bahşı)',
    'slm': 'Selâm / Teslimiyet / Bütünlük (Kusurdan Arınma, Güvenlik, Barış ve İçten Adanma)',
    'dnw': 'Dünyâ / Dünuv (Yakınlaşan, Mesafece ve Zamanca En Yakın İlk Aşama)',
    'qdr': 'Kader / Kudret / Miktar (Ölçü Belirleme, Orantılı Planlama, Kapasite ve Güç)',
    'n*r': 'Nezr / İnzâr (Tehlikeyi Önceden Bildirerek Uyarma ve Bağlayıcı Adak Sorumluluğu)',
    'jmE': 'Cem\' / Cemî / İcmâ (Dağınık Parçaları Bir Araya Toplama, Birlik ve Kesin Bütünlük)',
    'nZr': 'Nazar / İntizâr (Dikkatle Bakıp İnceleme, Gözetleme ve Süre/Mühlet Tanıma)',
    'sAl': 'Suâl / Mes\'ûliyet (Bilgi Öğrenmek İçin Sormak, İhtiyaç Talep Etmek ve Hesap Sorumluluğu)',
    'TwE': 'Tav\' / Tâat / İstitâat (Zorlanmadan Gönüllü Uyum, İçten Adanma ve İmkan-Güç Yetişi)',
    'EZm': 'Azîm / Azm / Ta\'zîm (Kemik Gibi Sarsılmaz Yapısal Sağlamlık, Büyüklük ve Yüceltme)',
    'xlf': 'Hilâfet / İhtilâf / Halef (Arkasından Gelip Yerini Alma, Çeşitlenme ve Ters Düşme)',
    'Ahl': 'Ehl / Ehliyet (Aynı Otağ-Evi Paylaşan Aile, Yerleşim Halkı ve İlkeye Lâyık/Mensup Olanlar)',
    'dxl': 'Duhûl / Müdhal / Dehâl (İçeri Girme, Sığınak Kovuğu ve Gizli İç Çürüme)',
    'xwf': 'Havf / Hîfe / Tehavvüf (Tehlike Beklentisinden Doğan Ürküntü, İç Çekince ve Kenardan Azaltma)',
    'rzq': 'Rızık / Rezzâk (Zamanlı Tahsisat, Yaşam Payı ve Sürdürülebilir Geçim Kaynağı)',
    'b$r': 'Beşer / Bişâret / Mübâşeret (Dış Deri/Ten, Ölümlü İnsan ve Yüzü Parlatan Müjde)',
    'ydy': 'Yed / Eydî (Organ Olarak El, Yetki Tasarrufu ve Ön-Zaman Yönelimi)',
    'Amm': 'Ümm / Ümmet / İmâm (Yönelinen Ana Kaynak, Anne, Ortak Yönlü Topluluk ve Öncü)',
    'Ezz': 'İzzet / Azîz (Sarsılmaz Sağlamlık, Yenilmez Üstünlük ve Eşsiz Değerlilik)',
    'jzy': 'Cezâ / Mücâzât (Yerine Geçip Kefil Olma, Birebir Denklik ve Eylem Karşılığı)',
    'Abw': 'Eb / Ebevân / Âbâ (Baba, Anne-Baba Birliği, Atalar ve Taklit-Soy Hukuku)',
    'nhr': 'Nehir / Nehâr (Yatağı Yarıp Akma, Aydınlık Gündüz ve Taşkınca Azarlama)'
}

def generate_top_100():
    data_dir = DATA_DIR
    morph_file = os.path.join(data_dir, 'quranic-corpus-morphology-0.4.txt')
    locked_file = os.path.join(data_dir, 'locked_roots.json')

    with open(locked_file, 'r', encoding='utf-8') as f:
        locked_roots = set(json.load(f)['locked_roots'].keys())

    roots_count = Counter()
    roots_ayahs = defaultdict(set)
    roots_lemmas = defaultdict(Counter)
    roots_sample_loc = {}
    total_tokens = 0

    with open(morph_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('('):
                m_root = re.search(r'ROOT:([^|]+)', line)
                if m_root:
                    r = m_root.group(1)
                    roots_count[r] += 1
                    total_tokens += 1
                    m_loc = re.match(r'\((\d+):(\d+):(\d+):', line)
                    if m_loc:
                        s, a, w = int(m_loc.group(1)), int(m_loc.group(2)), int(m_loc.group(3))
                        roots_ayahs[r].add((s, a))
                        if r not in roots_sample_loc:
                            roots_sample_loc[r] = f"{s}:{a}"
                    m_lem = re.search(r'LEM:([^|]+)', line)
                    if m_lem:
                        roots_lemmas[r][m_lem.group(1)] += 1

    top_100_list = []
    top_100_tokens = 0

    for rank, (bw, count) in enumerate(roots_count.most_common(100), 1):
        top_100_tokens += count
        ar_root = to_arabic_root(bw)
        lat_root = to_latin_root(bw)
        ayah_count = len(roots_ayahs[bw])
        top_lemmas = [lem for lem, _ in roots_lemmas[bw].most_common(3)]
        
        is_locked = ar_root in locked_roots
        concept_desc = CONCEPT_LABELS.get(bw, f"{bw} kökü ({', '.join(top_lemmas)})")

        top_100_list.append({
            'rank': rank,
            'root_arabic': ar_root,
            'root_latin': lat_root,
            'buckwalter': bw,
            'frequency': count,
            'unique_ayahs': ayah_count,
            'concept_label': concept_desc,
            'is_locked': is_locked,
            'sample_ayah': roots_sample_loc.get(bw, ''),
            'top_lemmas': top_lemmas
        })

    coverage_pct = (top_100_tokens / total_tokens) * 100

    # 1. Save JSON
    json_output = {
        'total_unique_roots_in_quran': len(roots_count),
        'total_root_tokens_in_quran': total_tokens,
        'top_100_token_count': top_100_tokens,
        'top_100_coverage_percentage': round(coverage_pct, 2),
        'locked_in_top_100': sum(1 for item in top_100_list if item['is_locked']),
        'top_100_roots': top_100_list
    }

    json_path = os.path.join(data_dir, 'top_100_roots.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)

    # 2. Save Markdown
    md_lines = [
        "# KUR'AN'DA EN ÇOK GEÇEN 100 KÖK VE TEMEL KAVRAM HARİTASI",
        "## Tabula Rasa Mesânî Çözümleme Sistemi (v3.0 Master İndeksi)",
        "",
        "> [!IMPORTANT]",
        f"> **İSTATİSTİKSEL KAPSAM REKORU:** Kur'an genelinde toplam **1.652 farklı kök** ve **{total_tokens:,} kök kullanımı** bulunmaktadır. İlk 100 kök tek başına **{top_100_tokens:,} geçişi ({coverage_pct:.2f}%)** oluşturmaktadır. Bu 100 kök çözüldüğünde Kur'an kelime haznesinin %60'ından fazlası Tabula Rasa ile mühürlenmiş olur.",
        "",
        "### 📊 Genel Dağılım Özeti",
        f"- **Kur'an Toplam Kök Sayısı:** 1.652 Kök",
        f"- **Toplam Kök Geçişi:** {total_tokens:,} Kelime",
        f"- **İlk 100 Kökün Toplam Geçişi:** {top_100_tokens:,} Kelime (**%{coverage_pct:.2f}**)",
        f"- **Şu Ana Kadar Mühürlenen Kökler (Faz 1):** {len(locked_roots)} Kök (Top 100 içinde: {sum(1 for item in top_100_list if item['is_locked'])} Kök)",
        "",
        "---",
        "",
        "### 📋 En Çok Geçen 100 Kök Master Tablosu",
        "",
        "| Sıra | Kök (Arapça) | Kök (Latin) | Geçiş | Ayet Sayısı | Temel Kavram ve Semantik Alan | Durum |",
        "| :---: | :---: | :---: | :---: | :---: | :--- | :---: |"
    ]

    for item in top_100_list:
        status_badge = "✅ **MÜHÜRLÜ**" if item['is_locked'] else "⏳ *Bekliyor*"
        md_lines.append(
            f"| {item['rank']} | `{item['root_arabic']}` | `{item['root_latin']}` | **{item['frequency']}** | {item['unique_ayahs']} | {item['concept_label']} | {status_badge} |"
        )

    md_lines.extend([
        "",
        "---",
        "",
        "### 🎯 Sıradaki Faz 1 Paketleri İçin Stratejik Öncelikler",
        "Top 100 listesinde yer alan ve Kur'an'ın omurgasını kuran en kritik aday kökler şunlardır:",
        "",
        "1. **`ع-ب-د` (Ebd - 275 geçiş, 251 ayet, Sıra 33):** Ubudiyet / Kulluk / Boyun Eğme mekanizması.",
        "2. **`خ-ل-ق` (Hlk - 261 geçiş, 218 ayet, Sıra 35):** Halk / Yaratılış / Takdir etme ve biçim verme.",
        "3. **`و-ق-ي` (Wqy - 258 geçiş, 237 ayet, Sıra 36):** Takvâ / Korunma / Sorumluluk bilinci.",
        "4. **`غ-ف-ر` (Gfr - 234 geçiş, 202 ayet, Sıra 40):** Mağfiret / Zırh gibi örtüp koruma mekanizması.",
        "5. **`ح-ك-م` (Hkm - 210 geçiş, 189 ayet, Sıra 44):** Hüküm / Hikmet / Engelleme ve sağlamlaştırma.",
        "6. **`م-ل-ك` (Mlk - 206 geçiş, 191 ayet, Sıra 45):** Mülk / Melek / Melik yetki ve kudret omurgası.",
        "7. **`ش-ر-ك` (Srk - 168 geçiş, 143 ayet, Sıra 63):** Şirk / Ortak koşma ve otoriteyi bölüşme.",
        "8. **`س-ل-م` (Slm - 140 geçiş, 127 ayet, Sıra 80):** İslâm / Selâm / Esenlik ve teslimiyet.",
        ""
    ])

    md_path = os.path.join(data_dir, 'TOP_100_KAVRAM.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"Top 100 JSON üretildi: {json_path}")
    print(f"Top 100 Markdown üretildi: {md_path}")

if __name__ == '__main__':
    generate_top_100()
