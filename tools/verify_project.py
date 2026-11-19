# -*- coding: utf-8 -*-
"""
Tabula Rasa Mesânî Çözümleme Sistemi - Sıfır Hata Doğrulama Motoru
PROMPT.md §9.3 kapsamında tüm JSON şemalarını, morfoloji sayımlarını,
Rasm-ı Osmânî kelime hizalamalarını ve Tabula Rasa temizliğini doğrular.
"""

import os
import re
import sys
import json
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quran_analyzer import DATA_DIR, QuranCorpus, extract_ayah_words, strip_tashkeel, load_verses
from tabula_rasa import find_forbidden_terms, purify_tabula_rasa
from build_kavramlar import ROOT_CONFIG

REQUIRED_LOCKED_KEYS = [
    'root_latin',
    'arabic',
    'rank',
    'morphology_and_rasm',
    'physical_core',
    'ibn_faris_asl',
    'dictionary_arbitration',
    'semitic_cognates',
    'mesani_opposite',
    'same_ayah_furuk',
    'anchor_ayahs',
    'unified_core_mechanism',
    'grammar_and_branch_rules',
    'derivatives',
]

REQUIRED_KAVRAM_KEYS = [
    'root',
    'root_latin',
    'concept_name',
    'rank',
    'total_occurrences',
    'unique_ayahs_count',
    'unified_core_mechanism',
    'physical_core',
    'dictionary_arbitration',
    'semitic_cognates',
    'mesani_opposite',
    'same_ayah_furuk',
    'anchor_ayahs',
    'grammar_and_branch_rules',
    'derivatives',
    'ayah_occurrences',
]


def verify_all():
    errors = []
    corpus = QuranCorpus()

    # 1. Tüm 6.236 ayette kelime sayısı hizalamasını doğrula
    ayah_max_w = defaultdict(int)
    with open(corpus.morphology_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.startswith('('):
                continue
            tab = line.find('\t')
            m = re.match(r'\((\d+):(\d+):(\d+):', line[:tab])
            if m:
                s, a, w = map(int, m.groups())
                if w > ayah_max_w[(s, a)]:
                    ayah_max_w[(s, a)] = w

    for (s, a), txt in corpus.ayahs_uthmani.items():
        words = extract_ayah_words(txt, s, a)
        if len(words) != ayah_max_w[(s, a)]:
            errors.append(f"Kelime hizalama hatası {s}:{a}: uthmani={len(words)}, corpus={ayah_max_w[(s, a)]}")

    # 2. Tüm 6.236 Türkçe ayette Tabula Rasa arındırma kontrolü
    raw_tr = load_verses(os.path.join(DATA_DIR, 'quran-turkish.txt'))
    if len(raw_tr) != 6236:
        errors.append(f"Türkçe ayet sayısı 6236 değil: {len(raw_tr)}")
    for (s, a), txt in raw_tr.items():
        hits = find_forbidden_terms(purify_tabula_rasa(txt))
        if hits:
            errors.append(f"Tabula Rasa kalıntısı ({s}:{a}): {hits}")

    # 3. locked_roots.json v3.0 şema ve korpus tutarlılık kontrolü
    with open(os.path.join(DATA_DIR, 'locked_roots.json'), 'r', encoding='utf-8') as f:
        locked_json = json.load(f)
    locked_roots = locked_json.get('locked_roots', {})

    for ar_root, entry in locked_roots.items():
        for k in REQUIRED_LOCKED_KEYS:
            if k not in entry:
                errors.append(f"locked_roots[{ar_root}] eksik anahtar: {k}")

        cfg = ROOT_CONFIG.get(ar_root)
        if not cfg:
            errors.append(f"ROOT_CONFIG içinde eksik kök: {ar_root}")
            continue

        bw = cfg['buckwalter']
        stats = corpus.get_root_stats(bw)
        approx_freq = entry.get('morphology_and_rasm', {}).get('approx_frequency', '')
        expected_prefix = f"{stats['total_occurrences']} geçiş / {stats['unique_ayahs_count']} ayet"
        if not approx_freq.startswith(expected_prefix):
            errors.append(
                f"locked_roots[{ar_root}] frekans uyumsuzluğu: '{approx_freq}' != '{expected_prefix}...'"
            )

        # Fiil babı gerçeği kontrolü (ör. أ-ل-ه içinde fiil yoksa Form I yazılmamalı)
        vf_str = " ".join(entry.get('morphology_and_rasm', {}).get('verb_forms_used', []))
        if not stats['verb_forms'] and 'Form I' in vf_str:
            errors.append(f"locked_roots[{ar_root}] fiil formu hatası: korpusta fiil yok ama '{vf_str}' yazılmış")

        # 4. data/kavramlar/<slug>.json kontrolü
        kavram_path = os.path.join(DATA_DIR, 'kavramlar', f"{cfg['slug']}.json")
        if not os.path.exists(kavram_path):
            errors.append(f"Eksik kavram dosyası: {kavram_path}")
            continue

        with open(kavram_path, 'r', encoding='utf-8') as kf:
            kd = json.load(kf)

        for k in REQUIRED_KAVRAM_KEYS:
            if k not in kd:
                errors.append(f"{cfg['slug']}.json eksik anahtar: {k}")

        occs = kd.get('ayah_occurrences', [])
        if kd.get('total_occurrences') != stats['total_occurrences'] or len(occs) != stats['total_occurrences']:
            errors.append(
                f"{cfg['slug']}.json toplam geçiş uyumsuz: json={len(occs)} / {kd.get('total_occurrences')}, corpus={stats['total_occurrences']}"
            )
        if kd.get('unique_ayahs_count') != stats['unique_ayahs_count']:
            errors.append(
                f"{cfg['slug']}.json ayet sayısı uyumsuz: json={kd.get('unique_ayahs_count')}, corpus={stats['unique_ayahs_count']}"
            )

        for occ in occs:
            s, a, w = occ['surah'], occ['ayah'], occ['word_position']
            expected_words = extract_ayah_words(corpus.ayahs_uthmani.get((s, a), ''), s, a)
            expected_word = expected_words[w - 1]
            if occ['target_word_uthmani'] != expected_word:
                errors.append(f"{cfg['slug']}.json {s}:{a} w={w} kelime uyumsuz: {occ['target_word_uthmani']} != {expected_word}")
            if occ['target_word_rasm'] != strip_tashkeel(expected_word):
                errors.append(f"{cfg['slug']}.json {s}:{a} w={w} rasm uyumsuz")
            if occ['target_word_literal_irab'] == 'Kavramın sentaktik / irablı konumu':
                errors.append(f"{cfg['slug']}.json {s}:{a} w={w} genel irab şablonuna düştü")

            for field in [
                'context_snippet_turkish_tabula_rasa',
                'ayah_text_turkish_tabula_rasa_full',
                'target_word_literal_irab',
                'contextual_meaning',
            ]:
                hits = find_forbidden_terms(occ.get(field, ''))
                if hits:
                    errors.append(f"{cfg['slug']}.json {s}:{a} {field} yasaklı terim içeriyor: {hits}")

    # 5. top_100_roots.json ve TOP_100_KAVRAM.md tutarlılığı
    with open(os.path.join(DATA_DIR, 'top_100_roots.json'), 'r', encoding='utf-8') as f:
        top100 = json.load(f)
    top100_locked = [r for r in top100['top_100_roots'] if r['is_locked']]
    expected_top100_locked = [r for r in top100['top_100_roots'] if r['root_arabic'] in locked_roots]
    if len(top100_locked) != len(expected_top100_locked) or top100['locked_in_top_100'] != len(expected_top100_locked):
        errors.append("top_100_roots.json mühür sayısı locked_roots.json ile uyumsuz")

    with open(os.path.join(DATA_DIR, 'TOP_100_KAVRAM.md'), 'r', encoding='utf-8') as f:
        md_text = f.read()
    expected_badge_line = f"**Şu Ana Kadar Mühürlenen Kökler (Faz 1):** {len(locked_roots)} Kök (Top 100 içinde: {len(expected_top100_locked)} Kök)"
    if expected_badge_line not in md_text:
        errors.append(f"TOP_100_KAVRAM.md özet satırı güncel değil: '{expected_badge_line}' bekleniyordu")

    # 6. second_100_roots.json ve SECOND_100_KAVRAM.md tutarlılığı
    second100_path = os.path.join(DATA_DIR, 'second_100_roots.json')
    if os.path.exists(second100_path):
        with open(second100_path, 'r', encoding='utf-8') as f:
            second100 = json.load(f)
        s2_locked = [r for r in second100['second_100_roots'] if r['is_locked']]
        expected_s2_locked = [r for r in second100['second_100_roots'] if r['root_arabic'] in locked_roots]
        if len(s2_locked) != len(expected_s2_locked) or second100['locked_in_second_100'] != len(expected_s2_locked):
            errors.append("second_100_roots.json mühür sayısı locked_roots.json ile uyumsuz")

        s2_md_path = os.path.join(DATA_DIR, 'SECOND_100_KAVRAM.md')
        if not os.path.exists(s2_md_path):
            errors.append(f"Eksik indeks dosyası: {s2_md_path}")
        else:
            with open(s2_md_path, 'r', encoding='utf-8') as f:
                s2_md_text = f.read()
            expected_s2_line = (
                f"**İkinci 100 İçinde Şu Ana Kadar Mühürlenen:** "
                f"{len(expected_s2_locked)} / 100 Kök (Toplam Mühürlü: {len(locked_roots)} Kök)"
            )
            if expected_s2_line not in s2_md_text:
                errors.append(f"SECOND_100_KAVRAM.md özet satırı güncel değil: '{expected_s2_line}' bekleniyordu")

    if errors:
        print(f"DOĞRULAMA BAŞARISIZ! Toplam {len(errors)} hata bulundu:")
        for err in errors[:30]:
            print("  -", err)
        return 1

    print(
        f"SIFIR HATA DOĞRULANDI! 6236 ayet hizalaması, {len(locked_roots)} kilitli kök v3.0 şeması, "
        f"tüm kavram JSON dosyaları ve Top 100 indeksi %100 tutarlı ve Tabula Rasa arınmış."
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(verify_all())
