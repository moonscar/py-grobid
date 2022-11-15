import os
from bs4 import BeautifulSoup

label_map = {
    "<section>": ("<head>", "</head>"),
    "<paragraph>": ("<p>", "</p>"),
    "<citation_marker>": ('<ref type="bibr">', "</ref>"),
    "<equation>": ("<formula>", "</formula>")
}

def compose_tag(tag_words):
    fulltext = " ".join(tag_words)
    fulltext = fulltext.replace(" TOK_CONJ ", "").replace(" - ", "")
    return fulltext

def build_tei_body(fulltext_result_path):
    output_words = []

    cur_state = ""

    with open(fulltext_result_path) as f:
        fulltext_result = f.readlines()

    for l in fulltext_result:
        cols = l.strip().split("\t")
        if len(cols) != 2:
            print(cols)
            continue

        feature, label = cols
        feature_cols = feature.split(" ")
        token = feature_cols[0]
        conj_pos = feature_cols[11]
        
        # label 标准化，如果label 不在规定范围内，就不输出
        if label.startswith("I-"):
            label = label.lstrip("I-")
            label_start = True
            if not cur_state:
                cur_state = label
        else:
            label_start = False

        if label in {"<figure>", "<figure_marker>", "<table>", "<table_marker>"}:
            continue

        if cur_state != label:
            output_words.append(label_map[cur_state][1])
            if label == "<section>":
                output_words.append("</div>")

            cur_state = label
            
        if label_start:
            if label == "<section>":
                output_words.append("<div>")

            output_words.append(label_map[label][0])

        if token == "-" and conj_pos == "LINEEND":
            token = "TOK_CONJ"
        output_words.append(token)

    tei_content = compose_tag(output_words)

    return tei_content
