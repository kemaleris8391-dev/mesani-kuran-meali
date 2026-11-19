# Sıfır Önyargılı Mesânî Kur'an Meali (Tabula Rasa v3.0)

Bu depo; Kur'an kavramlarını geleneksel terim ve ön kabullerden arındırılmış biçimde, canlı sözlük/Sami dilleri doğrulaması, Rasm-ı Osmânî iskelet metni, Çift Yönlü Mesânî ve Aynı Ayet İçi Furûk kurallarıyla çözümleyen **Tabula Rasa v3.0** projesinin tek gerçek kaynağıdır.

## 🧭 Yapay Zeka Ajanları İçin Başlangıç (PC ve Antigravity Web)

Yeni bir oturumda (yerel PC veya Google AI Studio **Antigravity Agent Preview** web ortamında) çalışmaya başlamadan önce aşağıdaki sırayı izle:

1. Ana sistem anayasasını oku: `PROMPT.md`
2. Kalite sigortalarını oku: `tools/QUALITY_CONSTITUTION.md`
3. Mevcut ilerleme durumunu kontrol et:
   - `data/second_100_roots.json` ve `data/SECOND_100_KAVRAM.md` (aktif Faz 1 - Etap 2 listesi)
   - `data/locked_roots.json` (kilitli ana kök sözlüğü)
   - `data/top_100_roots.json` (tamamlanan Etap 1 listesi)

## 📁 Depo Yapısı

- `PROMPT.md`: Tüm çalışma protokolü (10 Uzman Disiplin, Sözlükler Hakem Masası, JSON v3.0 şeması, devam motoru)
- `data/locked_roots.json`: Mühürlenmiş tüm köklerin tam v3.0 veritabanı
- `data/locked_roots_compact.json`: Hızlı okuma için sıkıştırılmış kök özeti
- `data/kavramlar/*.json`: Her mühürlü kavramın Kur'an'da geçtiği tüm ayet dökümleri
- `data/top_100_roots.json` & `data/TOP_100_KAVRAM.md`: İlk 100 kök indeksi (tamamlandı)
- `data/second_100_roots.json` & `data/SECOND_100_KAVRAM.md`: İkinci 100 yeni kök indeksi (aktif etap)
- `data/quran-*.txt` & `data/quranic-corpus-morphology-0.4.txt`: Yerel Kur'an metinleri ve morfoloji korpusu
- `tools/`: Saf Python standart kütüphanesiyle çalışan doğrulama ve üretim araçları (ek paket kurulumu gerektirmez)

## 🛠️ Doğrulama ve Güncelleme Komutları (Linux / macOS / Windows)

Tüm araçlar harici paket gerektirmeden Python 3 ile çalışır:

```bash
# Yeni mühürlenen kök sonrası kavram JSON dosyasını üret/güncelle
python3 tools/build_kavramlar.py

# İndeksleri ve özet dosyaları yenile
python3 tools/generate_top_100.py
python3 tools/generate_second_100.py
python3 tools/generate_compact_roots.py

# Zorunlu sıfır hata bütünlük doğrulaması (her kök sonrası şart)
python3 tools/verify_project.py
```

## 🌐 Web (Antigravity Agent Preview) Çalışma Ayarları

Google AI Studio üzerindeki **Antigravity Agent Preview** ortamında devam ederken:

1. **Tools:** `Code execution`, `Grounding with Google Search`, `URL context` ve `Filesystem tools` açık olmalıdır.
2. **Environment -> Sources:** Bu GitHub deposu kaynak olarak eklenir.
3. **System instructions:** `PROMPT.md` içeriği doğrudan yapıştırılabilir veya ajandan depo kökündeki `PROMPT.md` dosyasını okuyarak kaldığı yerden devam etmesi istenir.
4. **Senkronizasyon:** Yapılan değişikliklerin kalıcı olması için oturum sonunda güncellenen dosyalar depoya kaydedilir (`git commit` / `git push`) veya dışa aktarılıp PC kopyasına işlenir.
