import os

from collections import Counter, OrderedDict
from functools import partial 

from bs4 import BeautifulSoup
from src.feature_utils import *
from src.cmd_utils import wapiti_infer

PAGE_INFO = ["PAGESTART", "PAGEIN", "PAGEEND"]
BLOCK_INFO = ["BLOCKSTART", "BLOCKIN", "BLOCKEND"]
LINE_INFO = ["LINESTART", "LINEIN", "LINEEND"]

feature_cols = {
    "segment": ["token_text","2nd_token_text","lower_token","token_prefix","block_info","page_info","font_type","font_size_type","font_bold","font_italics","is_captal","is_digital","single_char","proper_name","common_name","first_name","year","mounth","email","http","relative_document_position","relative_page_position_characters","punct_profile","punct_profile_len","line_len","bitmap_around","vector_around","repetitive_pattern","first_repetitive_pattern", "in_main_area"], 
    "fulltext": ["token_text", "lower_token", "token_prefix", "token_suffix", "block_info", "line_info", "align_status", "font_type", "font_size_type", "font_bold", "font_italics", "is_captal", "is_digital", "single_char", "punct_info", "relative_document_position", "relative_page_position_characters", "bitmap_around", "calloutType", "calloutKnown", "superscript"]
    }

wapiti_model_map = {
    "segment": "/Users/hyy/mytask/b_paper/playground/Wapiti/data/seg_model.wapiti",
    "fulltext": "/Users/hyy/mytask/b_paper/playground/Wapiti/data/fulltext_model.wapiti",
}

class FeatureFactory():
    def __init__(self, alto_file):
        self.alto_path = alto_file
        self.feature_map = {}
        self.font_map = {}
        self.dump_map = {}

    def prepare(self):
        with open(self.alto_path) as f:
            self.alto_root = BeautifulSoup(f.read(), "xml")

        self.font_map = build_font_feature_map(self.alto_root.Styles)

    def _dump_feature(self, feature_type, output_path):
        feature_vectorise = partial(vectorize, feature_cols[feature_type])
        col_feature = map(feature_vectorise, self.feature_map[feature_type])

        with open(output_path, "w+") as w:
            for feature in col_feature:
                feature_line = " ".join(feature) + "\n"
                w.write(feature_line)

        self.dump_map[feature_type] = output_path

    def build_feature(self, output_path=""):
        # 直接读取原始的alto.xml，build
        self.feature_map["segment"] = self._extract_for_segment()

        segment_feature_path = "segment.feature"

        if output_path:
            segment_feature_path = os.path.join(output_path, segment_feature_path)

        self._dump_feature("segment", segment_feature_path)

        # 调用分类器，获取segment分类结果
        seg_results = wapiti_infer(wapiti_model_map["segment"], self.dump_map["segment"])

        with open(segment_feature_path + ".out", "w+") as w:
            for l in seg_results:
                w.write(l)

        # 根据segment分类结果，将文档分为不同部分
        self.block_map = self._build_block_map(seg_results)

        # 获取fulltext需要分类的部分，使用fulltext
        fulltext_feature = []
        for block in self.block_map["<body>"]:
            page_height = float(block.parent.parent.attrs["HEIGHT"])
            token_features = self._extract_for_fulltext(block, {"page_height": page_height})
            fulltext_feature.extend(token_features)

        self.feature_map["fulltext"] = fulltext_feature

        fulltext_feature_path = "fulltext.feature"

        if output_path:
            fulltext_feature_path = os.path.join(output_path, fulltext_feature_path)

        self._dump_feature("fulltext", fulltext_feature_path)

        # 调用分类器，获取fulltext分类结果
        fulltext_results = wapiti_infer(wapiti_model_map["fulltext"], self.dump_map["fulltext"])

        with open(fulltext_feature_path + ".out", "w+") as w:
            for l in fulltext_results:
                w.write(l)

        return True

    def _extract_for_segment(self):
        doc_layout = self.alto_root.Layout

        font = ""
        font_size = 0
        
        feature_list = []
        
        doc_token_len = len(doc_layout.find_all("String"))
        doc_level_pos = 0

        for page_zone in doc_layout:
            page_info = PAGE_INFO[0]
            page = page_zone.PrintSpace
            
            page_token_len = len(page.find_all("String"))
            page_level_pos = 0

            for text_block in page.children:
                block_info = BLOCK_INFO[0]
                max_line_len = 1
        
                for text_line in text_block.children:
                    first_token = text_line.next
                    feature_token = first_token
                    first_token_text = first_token.attrs["CONTENT"]
                    
                    # if skip_feature(feature_token):
                    #     continue

                    if first_token.next.name == "SP":
                        second_token_text = first_token.next.next.attrs["CONTENT"]
                    else:
                        second_token_text = first_token_text

                    # 获取字体信息
                    cur_font = first_token.attrs["STYLEREFS"]
                    if font != cur_font:
                        font_style = "NEWFONT"
                        font = cur_font
                    else:
                        font_style = "SAMEFONT"

                    # 获取字体信息
                    if font_size < self.font_map[cur_font]["fontsize"]:
                        font_size = self.font_map[cur_font]["fontsize"]
                        font_size_style = "HIGHERFONT"
                    elif self.font_map[cur_font]["fontsize"] == font_size:
                        font_size_style = "SAMEFONTSIZE"
                    elif self.font_map[cur_font]["fontsize"] < font_size:
                        font_size = self.font_map[cur_font]["fontsize"]
                        font_size_style = "LOWERFONT"

                    line_token = [c for c in text_line.children if c and c.name == "String"]
                    full_line = " ".join([t.attrs["CONTENT"] for t  in line_token])
                    line_len = len(full_line)
                    if max_line_len < line_len:
                        max_line_len = line_len
                    
                    punct_profile = "".join([c for c in full_line if c != " " and c in fullPunctuations])
                    if not punct_profile:
                        punct_profile = "no"
                        punct_profile_len = "0"
                    else:
                        punct_profile_len = len(punct_profile)

                    feature_list.append({
                        # features
                        "token_text": first_token_text,
                        "2nd_token_text": second_token_text,
                        "lower_token": first_token_text.lower(),
                        "token_prefix": [first_token_text[:i] for i in range(1, 5)],
                        "block_info": block_info,
                        "page_info": page_info, # 8.
                        "font_type": font_style,
                        "font_size_type": font_size_style, # 10.
                        "font_bold": self.font_map[cur_font]["bold"], # 字体加粗
                        "font_italics": self.font_map[cur_font]["italics"], # 字体变斜
                        "is_captal": capital(first_token_text), # 大写情况
                        "is_digital": digital(first_token_text), #
                        "single_char": "1" if len(first_token_text)==1 and first_token_text.isalpha() else "0",
                        "proper_name": "0", # properName
                        "common_name": "1" if first_token_text.lower() in english_words_set else "0", # 17. commonName
                        "first_name": "0", # firstName
                        "year": "0", # year
                        "mounth": "0", # 20. month
                        "email": "0", # email
                        "http": "0", # http
                        "relative_document_position": get_bucket_num(doc_level_pos, doc_token_len, 12), # relative document position
                        "relative_page_position_characters": get_bucket_num(page_level_pos, page_token_len, 12), # relative page position characters
                        "punct_profile": punct_profile, # 25. punctuation profile
                        "punct_profile_len": punct_profile_len, # punctuation profile
                        "line_len": line_len, # 27. round(10 * len(first_token_text) / max_len,  # lineLength
                        "bitmap_around": "0", # bitmapAround
                        "vector_around": "0", # vectorAround
                        "repetitive_pattern": "0", # repetitivePattern
                        "first_repetitive_pattern": "0", # firstRepetitivePattern
                        "in_main_area": "1", # inMainArea
                        # extra info for debug
                        "full_line": full_line,
                    })

                    if block_info == BLOCK_INFO[0]:
                        block_info = BLOCK_INFO[1]

                    if page_info == PAGE_INFO[0]:
                        page_info = PAGE_INFO[1]
                
                for i in range(1, len(text_block)+1):
                    line_len = feature_list[-i]["line_len"]
                    feature_list[-i]["line_len"] = get_bucket_num(line_len, max_line_len, 10)

                if 1 < len(text_block):
                    feature_list[-1]["block_info"] = BLOCK_INFO[-1] # fix block info
            
                block_token_len = len(text_block.find_all("String"))
                page_level_pos += block_token_len
                doc_level_pos += block_token_len

            feature_list[-1]["page_info"] = PAGE_INFO[-1] # fix page info

        return feature_list

    def _extract_for_fulltext(self, text_block, extern_feature={}):
        font = ""
        font_size = 0
        
        feature_list = []

        block_info = BLOCK_INFO[0]
        max_line_len = 1

        for text_line in text_block.children:
            line_info = LINE_INFO[0]

            line_tokens = text_line.find_all("String")

            for i, token in enumerate(line_tokens, start=1):
                feature_token = token
                full_token_text = token.attrs["CONTENT"]

                # 获取字体信息
                cur_font = feature_token.attrs["STYLEREFS"]
                if font != cur_font:
                    font_style = "NEWFONT"
                    font = cur_font
                else:
                    font_style = "SAMEFONT"

                # 获取字体信息
                if font_size < self.font_map[cur_font]["fontsize"]:
                    font_size = self.font_map[cur_font]["fontsize"]
                    font_size_style = "HIGHERFONT"
                elif self.font_map[cur_font]["fontsize"] == font_size:
                    font_size_style = "SAMEFONTSIZE"
                elif self.font_map[cur_font]["fontsize"] < font_size:
                    font_size = self.font_map[cur_font]["fontsize"]
                    font_size_style = "LOWERFONT"

                token_y_pos = float(feature_token.attrs["VPOS"])
                
                tokenized_text = tokenize(full_token_text)
                
                for token_text in tokenized_text:
                    a_feature = {
                        # features
                        "token_text": token_text,
                        "lower_token": token_text.lower(),
                        "token_prefix": [token_text[:i] for i in range(1, 5)],
                        "token_suffix": [token_text[i:] for i in range(-1, -5, -1)],
                        "block_info": block_info,
                        "line_info": line_info,
                        # "line_pos": get_bucket_num(i, len(line_tokens), 10),
                        "align_status": "ALIGNEDLEFT",
                        "font_type": font_style,
                        "font_size_type": font_size_style, # 10.
                        "font_bold": self.font_map[cur_font]["bold"], # 字体加粗
                        "font_italics": self.font_map[cur_font]["italics"], # 字体变斜
                        "is_captal": capital(token_text), # 大写情况
                        "is_digital": digital(token_text), #
                        "single_char": "1" if len(token_text)==1 else "0",
                        "punct_info": punct(token_text), # 25. punctuation type
                        "relative_document_position": 0,#get_bucket_num(doc_level_pos, doc_token_len, 12), # relative document position
                        "relative_page_position_characters": get_bucket_num(token_y_pos, extern_feature.get("page_height", 1.0), 12),#get_bucket_num(page_level_pos, page_token_len, 12), # relative page position characters
                        "bitmap_around": "0", # bitmapAround
                        "calloutType": "UNKNOWN",
                        "calloutKnown": 0,
                        "superscript": self.font_map[cur_font]["superscript"],
                    }

                    feature_list.append(a_feature)

                    if line_info == LINE_INFO[0]:
                        line_info = LINE_INFO[1]

                    if block_info == BLOCK_INFO[0]:
                        block_info = BLOCK_INFO[1]

            if 1 < len(text_line):
                feature_list[-1]["line_info"] = LINE_INFO[-1] # fix line info

        if 1 < len(text_block):
            feature_list[-1]["block_info"] = BLOCK_INFO[-1] # fix block info

        return feature_list

    def _build_block_map(self, features):
        doc_layout = self.alto_root.Layout

        feature_idx = 0
        block_map = OrderedDict()

        for page_zone in doc_layout:
            page = page_zone.PrintSpace

            for text_block in page.children:
                line_labels = set()

                # 归并相同label的特征行，经过验证，label相同的行一定属于同一个block
                for text_line in text_block.children:
                    label = features[feature_idx].split("\t")[1]
                    line_labels.add(label.strip().lstrip("I-"))
                    feature_idx += 1

                if len(line_labels) == 1:
                    seg_type = line_labels.pop()
                    if seg_type not in block_map:
                        block_map[seg_type] = []

                    line_feature = features[feature_idx].split("\t")[0].split()
                    rel_page_pos = line_feature[27] if len(line_feature) > 30 else "0"
                    
                    block_map[seg_type].append(text_block)

        return block_map

if __name__ == '__main__':
    ff = FeatureFactor("../tests/data/2020.emnlp-main.31.xml")
    ff.prepare()
    ff.build_feature()
