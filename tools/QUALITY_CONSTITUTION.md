# TABULA RASA MESÂNÎ ÇÖZÜMLEME SİSTEMİ
## KÖK VE AYET ANALİZLERİ ZORUNLU KALİTE ANAYASASI (v3.0)

Bu kurallar, sistemdeki tüm kök analizlerinde (Faz 1) ve ayet blokları çözümlemelerinde (Faz 2) tavizsiz olarak uygulanacak mutlak doğrulama filtreleridir:

1. **Gereksiz Alt-Sayım Yasağı ve Morfoloji Sadakati:**
   - Kökün toplam geçiş sayısını tutturmak için tahmini alt-isim/mastar kovaları üretilmez.
   - İstatistikte yalnızca genel ölçek (toplam geçiş / ayet) ve anlamı doğrudan belirleyen **fiil babları (Form I, II, IV, X vb.)** ile **harf-i cer kalıpları** (`آمن بـ` vs `آمن لـ`, `صلى على` vs `صلى لـ`) esas alınır.

2. **İbn Fâris Birebir İktibas & Çoklu Asıl Kuralı:**
   - `ibn_faris_asl` alanına başka sözlüklerden (*Lisânü'l-Arab*, *es-Sıhâh* vb.) cümle karıştırılamaz ve yapay zeka şerhi eklenemez.
   - İbn Fâris kökte *"أصلان / أصول متباينة"* (birden fazla bağımsız asıl) sayıyorsa, bunlar tek asılmış gibi birleştirilemez; ayrı ayrı belirtilir. Metin içi atlamalar kesinlikle `...` ile gösterilir.

3. **Sami Dilleri Ses Yasası ve Dil Ayrımı Kuralı:**
   - Tezi desteklemek için Sami dilleri kelimelerine sözlüklerde olmayan veya zıt anlamlar yüklenemez.
   - Strong/BDB içindeki İbranice maddeler ile Kitâb-ı Mukaddes Aramicesi maddeleri birbirine karıştırılamaz.
   - Islıklı ünsüz (Proto-Sami sibilant) ses yasasına sadık kalınır:
     * Proto-Sami `*s₂` -> Arapça `ش` (š) = İbranice `שׂ` (ś) = Sebece `s₂` = Aramice `ס/שׂ`.
     * Proto-Sami `*s₁` -> Arapça `س` (s) = İbranice `שׁ` (š) = Sebece `s₁`.

4. **Kaynak ve Referans Disiplini:**
   - Canlı web aramasında birebir doğrulanmamış hiçbir CAD, BDB veya Mekâyîs cilt/sayfa numarası tahmini yazılamaz. Yalnızca eser adı ve doğrudan madde başlığı verilir.

5. **"Eşkökenlisi Yok / Semantik Ayrışma Var" Dürüstlüğü:**
   - Bir Sami dilinde paralel kelime yoksa veya kök farklı bir anlama kaymışsa boşluk zorlanamaz. Açıkça "doğrudan paralel tespit edilmedi" veya "sesçe eşkökenli ancak semantik ayrışma var" olarak kaydedilir.

6. **Tek Çekirdek ve Kök-Dal Zorunluluğu (`unified_core_mechanism`):**
   - 1 kavram birden fazla alakasız veya çelişen anlama gelemez. Kökün Kur'an'daki tüm geçişleri tek bir değişmez çekirdek mekanizma altında %100 sıfır çelişkiyle çalışmalıdır.
   - Bağlamdaki görünür farklar keyfî anlam değişimi değil; yalnızca fiil babı, harf-i cer ve özne/nesne ilişkisinden kaynaklanır.

7. **Çift Yönlü MesÂNî (Ters-Anlam) Stres Testi:**
   - Bir köke (A) verilen anlamın tam tersi alındığında, bu ters kavram Kur'an'ın kendi metin içi Mesânî zıttının (B) geçtiği diğer tüm ayetlerdeki kullanımlarıyla %100 örtüşmek zorundadır.
   - "B'nin tüm Kur'an kullanımlarının tam tersi, A tanımımı doğruluyor mu?" testi geçilmeden kök kilitlenemez.

8. **Aynı Ayet İçi Furûk Kuralı (Terâdüf / Eşanlamlılık Yasağı):**
   - Kur'an'da aynı ayette veya paralel yapılarda yan yana gelen yakın kavramların hiçbiri eşanlamlı değildir (`Şekk / Rayb`, `Halaka / Fatara`, `Adl / Kıst`, `Salât / Zekât`, `Afv / Mağfiret` vb.).
   - Aralarındaki mekanik fark açıkça ayrıştırılmalıdır.

9. **Rasm-ı Osmânî (Harekesiz İskelet) ve Alternatif Okuma Denetimi:**
   - Özgün metin noktasız ve harekesiz ünsüz iskeletidir. İskeletin izin verdiği alternatif okumalar (etken/edilgen, farklı vezinler) denetlenir; harekeleme Mesânî veya sentaksla çelişiyorsa iskeletin izin verdiği okuma kanıtlarıyla not edilir.

10. **Sözlükler Eleme ve Hakem Masası Kuralı (Sözlük Dogmatizmini Önleme):**
   - Hiçbir sözlük yazarının (İbn Fâris dahil) otoritesi dogmatize edilemez. *Mekâyîsü'l-Luğa*, *Kitâbü'l-Ayn*, *Lisânü'l-Arab*, *es-Sıhâh* ve *el-Müfredât* gibi klasik kaynakların iddiaları toplanır; Sami arkeolojisi, Çift Yönlü Mesânî, %100 Ayet Stres Testi ve harf-i cer vektör uyumu süzgecinden geçirilerek hakem masası kararı gerekçelendirilir.
