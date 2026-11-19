# -*- coding: utf-8 -*-
"""
Kur'an'da İkinci 100 Yeni Kök (Seçenek A: Mühürsüz 100 Kök) Haritalayıcı
Tabula Rasa Mesânî Çözümleme Sistemi (v3.0)

İlk 100 kök (100/100) ve önceden mühürlenmiş 5 çekirdek kök sonrasında,
mühürlenmemiş sonraki 100 kökü (Genel Sıra 102 `أ-ك-ل` -> 204 `ع-ق-ل`)
haritalayarak `data/second_100_roots.json` ve `data/SECOND_100_KAVRAM.md`
dosyalarını üretir.
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_kavramlar import ROOT_CONFIG
from quran_analyzer import DATA_DIR, to_arabic_root, to_latin_root

# Faz 1'in ilk etabında önceden mühürlenen Top 100 dışı 5 çekirdek kök.
# Seçenek A hedef penceresi sabit kalsın diye bunlar hedef listeden hariç tutulur.
PRELOCKED_CORE_OUTSIDE_TOP100 = {
    'ن-ف-ق',
    'ص-ل-و',
    'س-ج-د',
    'ش-ك-ر',
    'ر-ك-ع',
}


def _collect_corpus_root_frequencies(morph_file):
    """Morfoloji korpusundan satır sonlarını temizleyerek kök frekanslarını toplar."""
    roots_count = Counter()
    roots_ayahs = defaultdict(set)
    roots_lemmas = defaultdict(Counter)
    roots_sample_loc = {}
    total_tokens = 0

    with open(morph_file, 'r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line.startswith('('):
                continue
            m_root = re.search(r'ROOT:([^|]+)', line)
            if not m_root:
                continue
            bw = m_root.group(1)
            roots_count[bw] += 1
            total_tokens += 1

            m_loc = re.match(r'\((\d+):(\d+):(\d+):', line)
            if m_loc:
                s, a = int(m_loc.group(1)), int(m_loc.group(2))
                roots_ayahs[bw].add((s, a))
                if bw not in roots_sample_loc:
                    roots_sample_loc[bw] = f"{s}:{a}"

            m_lem = re.search(r'LEM:([^|]+)', line)
            if m_lem:
                roots_lemmas[bw][m_lem.group(1)] += 1

    return roots_count, roots_ayahs, roots_lemmas, roots_sample_loc, total_tokens


def generate_second_100():
    """Seçenek A için İkinci 100 JSON ve Markdown indeks dosyalarını üretir."""
    morph_file = os.path.join(DATA_DIR, 'quranic-corpus-morphology-0.4.txt')
    top100_file = os.path.join(DATA_DIR, 'top_100_roots.json')
    locked_file = os.path.join(DATA_DIR, 'locked_roots.json')

    with open(top100_file, 'r', encoding='utf-8') as f:
        top100_roots = {r['root_arabic'] for r in json.load(f)['top_100_roots']}

    with open(locked_file, 'r', encoding='utf-8') as f:
        locked_roots = set(json.load(f)['locked_roots'].keys())

    (
        roots_count,
        roots_ayahs,
        roots_lemmas,
        roots_sample_loc,
        total_tokens,
    ) = _collect_corpus_root_frequencies(morph_file)

    ranked = roots_count.most_common()
    baseline_roots = top100_roots | PRELOCKED_CORE_OUTSIDE_TOP100
    baseline_tokens = sum(cnt for bw, cnt in ranked if to_arabic_root(bw) in baseline_roots)

    second_100_list = []
    prelocked_skipped = []
    second_100_tokens = 0

    for global_rank, (bw, count) in enumerate(ranked, 1):
        ar_root = to_arabic_root(bw)
        if ar_root in top100_roots:
            continue

        if ar_root in PRELOCKED_CORE_OUTSIDE_TOP100:
            if len(second_100_list) < 100:
                prelocked_skipped.append({
                    'global_rank': global_rank,
                    'root_arabic': ar_root,
                    'root_latin': to_latin_root(bw),
                    'buckwalter': bw,
                    'frequency': count,
                    'unique_ayahs': len(roots_ayahs[bw]),
                })
            continue

        if len(second_100_list) >= 100:
            break

        second_rank = len(second_100_list) + 1
        second_100_tokens += count
        top_lemmas = [lem for lem, _ in roots_lemmas[bw].most_common(3)]
        is_locked = ar_root in locked_roots

        if is_locked and ar_root in ROOT_CONFIG:
            concept_desc = ROOT_CONFIG[ar_root]['concept_name']
        else:
            concept_desc = f"Analiz Bekliyor ({', '.join(top_lemmas)})"

        second_100_list.append({
            'second_100_rank': second_rank,
            'global_rank': global_rank,
            'root_arabic': ar_root,
            'root_latin': to_latin_root(bw),
            'buckwalter': bw,
            'frequency': count,
            'unique_ayahs': len(roots_ayahs[bw]),
            'concept_label': concept_desc,
            'is_locked': is_locked,
            'sample_ayah': roots_sample_loc.get(bw, ''),
            'top_lemmas': top_lemmas,
        })

    locked_in_second = sum(1 for item in second_100_list if item['is_locked'])
    baseline_pct = round((baseline_tokens / total_tokens) * 100, 2)
    second_pct = round((second_100_tokens / total_tokens) * 100, 2)
    projected_tokens = baseline_tokens + second_100_tokens
    projected_pct = round((projected_tokens / total_tokens) * 100, 2)

    json_output = {
        'package': 'Faz 1 - İkinci 100 (Seçenek A: Mühürsüz 100 Yeni Kök)',
        'total_unique_roots_in_quran': len(roots_count),
        'total_root_tokens_in_quran': total_tokens,
        'already_locked_baseline_roots': len(baseline_roots),
        'already_locked_baseline_tokens': baseline_tokens,
        'already_locked_baseline_percentage': baseline_pct,
        'second_100_target_count': len(second_100_list),
        'second_100_token_count': second_100_tokens,
        'second_100_coverage_percentage': second_pct,
        'projected_total_locked_roots': len(baseline_roots) + len(second_100_list),
        'projected_cumulative_tokens': projected_tokens,
        'projected_cumulative_percentage': projected_pct,
        'locked_in_second_100': locked_in_second,
        'prelocked_skipped_in_range': prelocked_skipped,
        'second_100_roots': second_100_list,
    }

    json_path = os.path.join(DATA_DIR, 'second_100_roots.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)

    skipped_desc = ', '.join(
        f"{p['global_rank']}. `{p['root_arabic']}` ({p['frequency']})"
        for p in prelocked_skipped
    )

    md_lines = [
        "# KUR'AN'DA İKİNCİ 100 YENİ KÖK VE KAVRAM HARİTASI (SEÇENEK A)",
        "## Tabula Rasa Mesânî Çözümleme Sistemi (v3.0 Faz 1 - Etap 2 İndeksi)",
        "",
        "> [!IMPORTANT]",
        f"> **HEDEF KAPSAM (SEÇENEK A):** İlk 100 kök (`100/100`) ve 5 çekirdek kök (`{len(baseline_roots)}` kök, **{baseline_tokens:,}** geçiş / **%{baseline_pct:.2f}**) mühürlendikten sonra, bu etapta Genel Sıra **102 (`أ-ك-ل`) - 204 (`ع-ق-ل`)** arasındaki **100 yeni kök** işlenir. Bu 100 kök tek başına **{second_100_tokens:,} geçiş (%{second_pct:.2f})** ekler; tamamlandığında toplam **{len(baseline_roots) + len(second_100_list)} kilitli kök** ile Kur'an köklü kelimelerinin **%{projected_pct:.2f}**'i mühürlenmiş olur.",
        "",
        "### 📊 Genel Dağılım Özeti",
        f"- **Temizlenmiş Kur'an Toplam Kök Sayısı:** {len(roots_count):,} Benzersiz Kök / {total_tokens:,} Geçiş",
        f"- **Mevcut Başlangıç Tabanı:** {len(baseline_roots)} Kilitli Kök ({baseline_tokens:,} geçiş, **%{baseline_pct:.2f}**)",
        f"- **İkinci 100 Hedefi (Yeni Kökler):** 100 Kök ({second_100_tokens:,} geçiş, **+%{second_pct:.2f}**)",
        f"- **Etap Sonu Kümülatif Kapsam:** {len(baseline_roots) + len(second_100_list)} Kök ({projected_tokens:,} geçiş, **%{projected_pct:.2f}**)",
        f"- **İkinci 100 İçinde Şu Ana Kadar Mühürlenen:** {locked_in_second} / 100 Kök (Toplam Mühürlü: {len(locked_roots)} Kök)",
        f"- **Bu Aralıkta Önceden Mühürlü Olduğu İçin Atlanan 4 Çekirdek Kök:** {skipped_desc}",
        "",
        "---",
        "",
        "### 📋 İkinci 100 Yeni Kök Master Tablosu (Genel Sıra 102 - 204)",
        "",
        "| Etap Sıra | Genel Sıra | Kök (Arapça) | Kök (Latin) | Geçiş | Ayet | Örnek Ayet | Kavram ve Lemma Durumu | Durum |",
        "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |",
    ]

    for item in second_100_list:
        status_badge = "✅ **MÜHÜRLÜ**" if item['is_locked'] else "⏳ *Bekliyor*"
        md_lines.append(
            f"| {item['second_100_rank']} | {item['global_rank']} | `{item['root_arabic']}` | "
            f"`{item['root_latin']}` | **{item['frequency']}** | {item['unique_ayahs']} | "
            f"{item['sample_ayah']} | {item['concept_label']} | {status_badge} |"
        )

    md_lines.append("")
    md_path = os.path.join(DATA_DIR, 'SECOND_100_KAVRAM.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"Second 100 JSON üretildi: {json_path}")
    print(f"Second 100 Markdown üretildi: {md_path}")


if __name__ == '__main__':
    generate_second_100()
