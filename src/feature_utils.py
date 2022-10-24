import re

from collections import defaultdict
from english_words import english_words_set
from fitz import Rect

spliter = re.compile("[ \n\r\t]|([,:;?.!/\(\)\-\"“”‘’'`$])")

fullPunctuations = "(（[ •*,:;?.!/)）-−–‐«»„\"“”‘’'`$#@]*\u2666\u2665\u2663\u2660\u00A0";


def skip_feature(forbid_zone, layout_token):
    """如果token在forbid_zone中，那么跳过这个token"""
    x0 = float(string0.attrs["HPOS"])
    y0 = float(string0.attrs["VPOS"])
    x1 = x0 + float(string0.attrs["HEIGHT"])
    y1 = y0 + float(string0.attrs["WIDTH"])

#     forbid_zone = Rect()
    token_zone = Rect(x0, y0, x1, y1)
    
    return forbid_zone.intersects(token_zone)


def tokenize(text):
    return [t for t in spliter.split(text) if t]


def get_bucket_num(cur, total, bucket):
    """将特征离散化，并映射到特定区间"""
    return int(cur * bucket / total)


def capital(s):
    if s.isupper() or s in fullPunctuations:
        return "ALLCAP"
    elif s[0].isupper():
        return "INITCAP"
    else:
        return "NOCAPS"

def digital(s):
    digital_list = [c.isdigit() for c in s]
    if all(digital_list):
        return "ALLDIGIT"
    elif any(digital_list):
        return "CONTAINSDIGITS"
    else:
        return "NODIGIT"
    
def punct(s):
    if len(s) != 1:
        return "NOPUNCT"

    if s.isalpha() or s.isdigit():
        return "NOPUNCT"

    punct_map = defaultdict(lambda : "PUNCT")
    punct_map.update({
         "(": "OPENBRACKET",
         ")": "ENDBRACKET",
         ".": "DOT",
         ",": "COMMA",
         "-": "HYPHEN",
         "'": "QUOTE",
         '"': "QUOTE",
    })
    return punct_map[s]


def build_font_feature_map(style):
    font_map = {}
    for font in style:
        font_map[font.attrs["ID"]] = {
            "fontsize": int(float(font.attrs["FONTSIZE"])), # HIGHERFONT / LOWERFONT
            "bold": "1" if "bold" in font.get("FONTSTYLE", "") else "0",
            "italics": "1" if "italics" in font.get("FONTSTYLE", "") else "0",
            "superscript": "1" if "superscript" in font.get("FONTSTYLE", "") else "0",
        }
    return font_map


def vectorize(feature_order, feature_dict):
    vector = []
    for key in feature_order:
        if type(feature_dict[key]) == list:
            vector.extend([str(value) for value in feature_dict[key]])
        else:
            vector.append(str(feature_dict[key]))
    return vector
