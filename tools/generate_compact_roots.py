# -*- coding: utf-8 -*-
"""
Kilitli Kökler Kompakt Özet Üretici (AI Studio / Web LLM Optimize Edici)
Tabula Rasa Mesânî Çözümleme Sistemi (v3.0)

Master data/locked_roots.json dosyasını bozmadan, web tarayıcılarında (Google AI Studio vb.)
token kullanımını ~800.000 tokenden ~45.000 tokene (%94 tasarruf) indiren hafif
özet dosyaları (JSON ve Markdown) üretir.
"""

import os
import json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

def generate_compact_files():
    locked_path = os.path.join(DATA_DIR, 'locked_roots.json')
    with open(locked_path, 'r', encoding='utf-8') as f:
        locked_data = json.load(f)

    lr = locked_data.get('locked_roots', {})
    
    # 1. Kompakt JSON (Modelin en çok ihtiyaç duyduğu çekirdek alanlar)
    compact_dict = {}
    md_lines = [
        "# MÜHÜRLÜ KÖKLER KAVRAM VE MESÂNÎ ÖZETİ (TABULA RASA v3.0)",
        f"> **Toplam Mühürlü Kök:** {len(lr)} Kök | **Kullanım Amacı:** Web LLM / AI Studio Context Optimizasyonu\n",
        "| Kök (Arapça) | Kök (Latin) | Tek Çekirdek Mekanizması (Unified Core) | Mesânî Zıttı |",
        "| :--- | :--- | :--- | :--- |"
    ]

    for root, entry in lr.items():
        latin = entry.get('root_latin', '')
        core = entry.get('unified_core_mechanism', '').replace('\n', ' ').replace('|', '/')
        opps = entry.get('mesani_opposite', {}).get('roots', []) if isinstance(entry.get('mesani_opposite'), dict) else []
        opp_str = ', '.join(opps) if isinstance(opps, list) else str(opps)

        compact_dict[root] = {
            'latin': latin,
            'core': entry.get('unified_core_mechanism'),
            'physical': entry.get('physical_core'),
            'opposites': opps
        }

        md_lines.append(f"| `{root}` | `{latin}` | {core} | {opp_str} |")

    # JSON yaz
    json_out_path = os.path.join(DATA_DIR, 'locked_roots_compact.json')
    with open(json_out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'meta': {
                'total_locked': len(lr),
                'description': 'AI Studio ve Web LLM bağlamı için hafifletilmiş kilitli kökler özeti'
            },
            'locked_roots': compact_dict
        }, f, ensure_ascii=False, indent=2)

    # Markdown yaz
    md_out_path = os.path.join(DATA_DIR, 'LOCKED_ROOTS_SUMMARY.md')
    with open(md_out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"Kompakt JSON üretildi: {json_out_path} ({os.path.getsize(json_out_path):,} bytes)")
    print(f"Kompakt Markdown üretildi: {md_out_path} ({os.path.getsize(md_out_path):,} bytes)")

if __name__ == '__main__':
    generate_compact_files()
