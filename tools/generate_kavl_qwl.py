# -*- coding: utf-8 -*-
"""
Kavl (ق-و-ل) Kavram Dosyası Üreticisi (Ortak Motora Yönlendirici)
Top 100 Sıra 2: 1.722 Geçiş / 1.383 Ayet
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_kavramlar import build_root


def main():
    build_root('ق-و-ل')


if __name__ == '__main__':
    main()
