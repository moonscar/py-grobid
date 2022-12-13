import os
import re
from bs4 import BeautifulSoup
from collections import namedtuple

Tag = namedtuple('Tag', ['Head', "Priority",'Tail'])

label_map = {
    # label : Tag-Start, Prior, Tag-End
    "<part>": Tag("<div>", 20, "</div>"),
    "<section>": Tag("<head>", 8, "</head>"),
    "<paragraph>": Tag("<p>", 10, "</p>"),
    "<citation_marker>": Tag('<ref type="bibr">', 5, "</ref>"),
    "<equation>": Tag("<formula>", 5, "</formula>"),
    "<equation_marker>": Tag("<formula>", 5, "</formula>"),
    "<equation_label>": Tag("<formula>", 5, "</formula>"),
}

def compose_tag(tag_words):
    fulltext = " ".join(tag_words)
    fulltext = fulltext.replace(" TOK_CONJ ", "").replace(" - ", "")
    return fulltext


def fix_head_number(root):
    head_number = re.compile("\d+( \. \d+)?")

    for head in root.find_all("head"):
        matched = head_number.match(head.string.strip())

        if not matched:
            continue

        matched_content = matched.group(0)
        head.string = head.string.replace(matched_content, "")
        head.attrs["n"] = matched_content.replace(" ", "")

    return root


def build_tei_body(fulltext_result_path):
    output_words = ["<div>"]

    cur_state = ""
    stack = ["<part>"]

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
        label_start = False
        if label.startswith("I-"):
            label_start = True
            label = label.lstrip("I-")

        if label in {"<figure>", "<figure_marker>", "<table>", "<table_marker>"}:
            continue

        if token == "-" and conj_pos == "LINEEND":
            token = "TOK_CONJ"

        if len(stack) == 0:
            stack.append("<part>")
            output_words.append("<div>")
            # output_words.append(label_map[label][0])

            # stack.append(label)
        else:
            if stack[-1] == label:
                if label_start:
                    output_words.append(label_map[label].Tail)
                    output_words.append(label_map[label].Head)
                output_words.append(token)
            else:
                # 比较优先级
                prev_tag = label_map[stack[-1]]
                cur_tag = label_map[label]

                if cur_tag.Priority < prev_tag.Priority:
                    stack.append(label)

                    output_words.append(cur_tag.Head)
                    output_words.append(token)
                else:
                    while cur_tag.Priority > prev_tag.Priority:
                        stack.pop()
                        output_words.append(prev_tag.Tail)

                        if len(stack):
                            prev_tag = label_map[stack[-1]]
                        else:
                            break

                    if stack and stack[-1] != label:
                        stack.append(label)
                        output_words.append(cur_tag.Head)

                    output_words.append(token)

    tei_content = compose_tag(output_words)

    bs = BeautifulSoup(tei_content, 'xml')
    bs = fix_head_number(bs)
    pretty_xml = bs.prettify()

    return pretty_xml

if __name__ == '__main__':
    import sys
    result_path = sys.argv[1]
    xml_content = build_tei_body(result_path)

    with open("test.tei.xml", "w+") as w:
        w.write(xml_content)
