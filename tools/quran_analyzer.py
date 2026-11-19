# -*- coding: utf-8 -*-
"""
Kur'an Kök, Rasm-ı Osmânî ve Morfoloji Analiz Motoru
Tabula Rasa Mesânî Çözümleme Sistemi (v3.0)
"""

import re
import os
from collections import defaultdict, Counter

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

SURAH_NAMES = {
    1: "Fâtiha", 2: "Bakara", 3: "Âl-i İmrân", 4: "Nisâ", 5: "Mâide",
    6: "En'âm", 7: "A'râf", 8: "Enfâl", 9: "Tevbe", 10: "Yûnus",
    11: "Hûd", 12: "Yûsuf", 13: "Ra'd", 14: "İbrâhîm", 15: "Hicr",
    16: "Nahl", 17: "İsrâ", 18: "Kehf", 19: "Meryem", 20: "Tâhâ",
    21: "Enbiyâ", 22: "Hac", 23: "Mü'minûn", 24: "Nûr", 25: "Furkān",
    26: "Şuarâ", 27: "Neml", 28: "Kasas", 29: "Ankebût", 30: "Rûm",
    31: "Lokmân", 32: "Secde", 33: "Ahzâb", 34: "Sebe'", 35: "Fâtır",
    36: "Yâsîn", 37: "Sâffât", 38: "Sâd", 39: "Zümer", 40: "Mü'min (Gāfir)",
    41: "Fussilet", 42: "Şûrâ", 43: "Zuhruf", 44: "Duhân", 45: "Câsiye",
    46: "Ahkāf", 47: "Muhammed", 48: "Fetih", 49: "Hucurât", 50: "Kāf",
    51: "Zâriyât", 52: "Tûr", 53: "Necm", 54: "Kamer", 55: "Rahmân",
    56: "Vâkıa", 57: "Hadîd", 58: "Mücâdele", 59: "Haşr", 60: "Mümtehine",
    61: "Saff", 62: "Cuma", 63: "Münâfikūn", 64: "Tegābün", 65: "Talâk",
    66: "Tahrîm", 67: "Mülk", 68: "Kalem", 69: "Hâkka", 70: "Meâric",
    71: "Nûh", 72: "Cin", 73: "Müzzemmil", 74: "Müddessir", 75: "Kıyâme",
    76: "İnsân", 77: "Mürselât", 78: "Nebe'", 79: "Nâziât", 80: "Abese",
    81: "Tekvîr", 82: "İnfitâr", 83: "Mutaffifîn", 84: "İnşikāk", 85: "Bürûc",
    86: "Târık", 87: "A'lâ", 88: "Gāşiye", 89: "Fecr", 90: "Beled",
    91: "Şems", 92: "Leyl", 93: "Duhâ", 94: "İnşirâh", 95: "Tîn",
    96: "Alak", 97: "Kadir", 98: "Beyyine", 99: "Zilzâl", 100: "Âdiyât",
    101: "Kāria", 102: "Tekâsür", 103: "Asr", 104: "Hümeze", 105: "Fîl",
    106: "Kureyş", 107: "Mâûn", 108: "Kevser", 109: "Kâfirûn", 110: "Nasr",
    111: "Mesed", 112: "İhlâs", 113: "Felak", 114: "Nâs"
}

BW_TO_AR = {
    'A': 'أ', 'b': 'ب', 't': 'ت', 'v': 'ث', 'j': 'ج', 'H': 'ح', 'x': 'خ',
    'd': 'د', '*': 'ذ', 'r': 'ر', 'z': 'ز', 's': 'س', '$': 'ش', 'S': 'ص',
    'D': 'ض', 'T': 'ط', 'Z': 'ظ', 'E': 'ع', 'g': 'غ', 'f': 'ف', 'q': 'ق',
    'k': 'ك', 'l': 'ل', 'm': 'م', 'n': 'ن', 'h': 'ه', 'w': 'و', 'y': 'ي',
    'Y': 'ى', 'p': 'ة', '\'': 'ء', '>': 'أ', '<': 'إ', '&': 'ؤ', '}': 'ئ'
}

BW_TO_LATIN = {
    'A': 'E', 'b': 'B', 't': 'T', 'v': 'S', 'j': 'C', 'H': 'H', 'x': 'H',
    'd': 'D', '*': 'Z', 'r': 'R', 'z': 'Z', 's': 'S', '$': 'S', 'S': 'S',
    'D': 'D', 'T': 'T', 'Z': 'Z', 'E': 'A', 'g': 'G', 'f': 'F', 'q': 'K',
    'k': 'K', 'l': 'L', 'm': 'M', 'n': 'N', 'h': 'H', 'w': 'W', 'y': 'Y',
    'Y': 'Y', 'p': 'T', '\'': 'A', '>': 'E', '<': 'I', '&': 'U', '}': 'I'
}

_TASHKEEL_RE = re.compile(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06dc\u06df-\u06e8\u06ea-\u06ed]')
_BASMALA_RASM = ['بسم', 'ٱلله', 'ٱلرحمن', 'ٱلرحيم']


def to_arabic_root(bw):
    """Buckwalter kök kodunu tireli Arapça kök dizisine dönüştürür."""
    return '-'.join(BW_TO_AR.get(c, c) for c in bw)


def to_latin_root(bw):
    """Buckwalter kök kodunu tireli Latin kök dizisine dönüştürür."""
    return '-'.join(BW_TO_LATIN.get(c, c) for c in bw)


def strip_tashkeel(text):
    """Tüm hareke ve okuma işaretlerini soyar, saf Rasm-ı Osmânî iskeletini çıkarır."""
    return _TASHKEEL_RE.sub('', text)


def load_verses(filepath):
    """`sure|ayet|metin` biçimindeki metin dosyasını {(sure, ayet): metin} sözlüğüne yükler."""
    verses = {}
    if not os.path.exists(filepath):
        return verses
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|', 2)
            if len(parts) >= 3:
                verses[(int(parts[0]), int(parts[1]))] = parts[2]
    return verses


def extract_ayah_words(uthmani_text, surah, ayah):
    """
    Uthmani ayet metnini Quranic Corpus kelime indekslemesiyle (1 tabanlı `w`) birebir hizalar.
    Tanzil Uthmani dosyasındaki 112 adet Sûre-1 başı Besmelesini ve 37:130 (`إِلْ يَاسِينَ`)
    ayrımını korpus kelime sınırlarına uyarlar.
    """
    if not uthmani_text:
        return []
    words = uthmani_text.split()
    if (
        surah not in (1, 9)
        and ayah == 1
        and len(words) >= 4
        and [strip_tashkeel(w) for w in words[:4]] == _BASMALA_RASM
    ):
        words = words[4:]
    if (surah, ayah) == (37, 130) and len(words) == 4:
        words = [words[0], words[1], f"{words[2]} {words[3]}"]
    return words


class QuranCorpus:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        self.morphology_file = os.path.join(data_dir, 'quranic-corpus-morphology-0.4.txt')
        self.uthmani_file = os.path.join(data_dir, 'quran-uthmani.txt')
        self.simple_file = os.path.join(data_dir, 'quran-simple.txt')

        self.ayahs_uthmani = load_verses(self.uthmani_file)
        self.ayahs_simple = load_verses(self.simple_file)
        self.roots_map = defaultdict(list)
        self._load_morphology()

    def _load_morphology(self):
        if not os.path.exists(self.morphology_file):
            return
        with open(self.morphology_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('LOCATION'):
                    continue
                parts = line.split('\t')
                if len(parts) < 4:
                    continue
                loc, form, tag, features = parts[0], parts[1], parts[2], parts[3]
                root_match = re.search(r'ROOT:([^|]+)', features)
                if not root_match:
                    continue
                root = root_match.group(1)
                m = re.match(r'\((\d+):(\d+):(\d+):(\d+)\)', loc)
                if not m:
                    continue
                s, a, w, segment = map(int, m.groups())
                lemma_match = re.search(r'LEM:([^|]+)', features)
                pos_match = re.search(r'POS:([^|]+)', features)
                self.roots_map[root].append({
                    's': s,
                    'a': a,
                    'w': w,
                    'seg': segment,
                    'form': form,
                    'tag': tag,
                    'pos': pos_match.group(1) if pos_match else tag,
                    'lem': lemma_match.group(1) if lemma_match else '',
                    'features': features
                })

    def get_root_word_groups(self, root):
        """Kökün geçişlerini `(sure, ayet, kelime)` bazında gruplayarak sıralı döndürür."""
        word_groups = defaultdict(list)
        for entry in self.roots_map.get(root, []):
            word_groups[(entry['s'], entry['a'], entry['w'])].append(entry)
        return sorted(word_groups.items())

    def get_root_stats(self, root):
        """Kök istatistikleri, fiil babları ve örnek ayet dökümü."""
        word_groups = self.get_root_word_groups(root)
        total = len(word_groups)
        unique_ayahs = sorted(set((s, a) for (s, a, _), _ in word_groups))

        pos_counts = Counter()
        lemmas = Counter()
        verb_forms = Counter()

        for (_, _, _), segs in word_groups:
            stem = next((sg for sg in segs if 'STEM' in sg['features']), segs[0])
            pos_counts[stem['pos']] += 1
            if stem['lem']:
                lemmas[stem['lem']] += 1
            if 'POS:V' in stem['features']:
                vf_match = re.search(r'\(([IVX]+)\)', stem['features'])
                verb_forms[vf_match.group(1) if vf_match else 'I'] += 1

        return {
            'root': root,
            'total_occurrences': total,
            'unique_ayahs_count': len(unique_ayahs),
            'pos_breakdown': dict(pos_counts),
            'verb_forms': dict(verb_forms),
            'top_lemmas': dict(lemmas.most_common(10)),
            'sample_ayahs': unique_ayahs[:10]
        }

    def get_ayah_text(self, s, a):
        uthmani = self.ayahs_uthmani.get((s, a), '')
        simple = self.ayahs_simple.get((s, a), '')
        return {
            'surah': s,
            'ayah': a,
            'uthmani': uthmani,
            'simple': simple,
            'rasm': strip_tashkeel(uthmani)
        }


if __name__ == '__main__':
    qc = QuranCorpus()
    print("Corpus loaded.")
    for r in ['Alh', 'qwl', 'kfr', '$kr', 'Amn', 'nfq']:
        stats = qc.get_root_stats(r)
        print(f"Root: {r} -> Total: {stats['total_occurrences']} in {stats['unique_ayahs_count']} ayahs. Forms: {stats['verb_forms']}")
