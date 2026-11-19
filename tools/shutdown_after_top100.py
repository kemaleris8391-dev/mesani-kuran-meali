# -*- coding: utf-8 -*-
"""
Top 100 Kök Tamamlanma Sonrası Güvenli PC Kapatma Betiği

Bu betik yalnızca şu iki koşulun ikisi de %100 sağlandığında Windows
kapatma komutunu (`shutdown /s /t 20`) tetikler:
1. `data/top_100_roots.json` içinde Top 100 kökün tamamı (`100 / 100`) mühürlüdür.
2. `tools/verify_project.py` (`verify_all()`) sıfır hata (`0`) ile geçer.
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quran_analyzer import DATA_DIR
from verify_project import verify_all


def main(dry_run=False):
    top100_path = os.path.join(DATA_DIR, "top_100_roots.json")
    with open(top100_path, "r", encoding="utf-8") as f:
        top100 = json.load(f)

    roots = top100.get("top_100_roots", [])
    locked_items = [r for r in roots if r.get("is_locked")]
    locked_count = len(locked_items)

    if len(roots) != 100 or locked_count != 100 or top100.get("locked_in_top_100") != 100:
        print(
            f"KAPATMA İPTAL EDİLDİ: Top 100 henüz tamamlanmadı "
            f"({locked_count}/100 mühürlü)."
        )
        return 1

    if verify_all() != 0:
        print("KAPATMA İPTAL EDİLDİ: verify_project.py sıfır hata ile geçmedi.")
        return 1

    cmd = [
        "shutdown",
        "/s",
        "/t",
        "20",
        "/c",
        "Tabula Rasa Top 100 kavramlar sifir hata ile tamamlandi. PC 20 sn sonra kapatilacak.",
    ]

    if dry_run:
        print("DRY-RUN BAŞARILI: Tüm 100 kavram mühürlü ve doğrulandı. Çalıştırılacak komut:")
        print(" ", " ".join(cmd))
        return 0

    print("100/100 kavram mühürlendi ve doğrulandı. PC 20 saniye içinde kapatılıyor...")
    subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv[1:]
    raise SystemExit(main(dry_run=is_dry))
