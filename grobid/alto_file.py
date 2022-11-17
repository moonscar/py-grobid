from bs4 import BeautifulSoup
from collections import Counter


def get_counter_max(counter):
    items = counter.items()
    return max(items, key=lambda x:x[1])


class AltoFile:
    def __init__(self, alto_path):
        self.alto_path = alto_path
        self.pdf_data = None
        self._page_sizes = []
        self._line_rects = {}

    def _get_raw_from_alto(self):
        self.line_ids = []

        with open(self.alto_path, "rb") as f:
            content = f.read()
            root = BeautifulSoup(content, "xml")

        all_pages = root.find_all("PrintSpace")
        self.pdf_data = []

        for i, page in enumerate(all_pages, start=1):
            # page_data = defaultdict(list)
            page_data = [('words', 'bbox', 'block_ids', 'line_ids', 'page_id', 'labels')]
            for token in root.find_all("String"):
                top_left = (float(token.attrs["HPOS"]), float(token.attrs["VPOS"]))
                height = float(token.attrs["HEIGHT"])
                width = float(token.attrs["WIDTH"])
                bottom_right = (top_left[0] + height, top_left[1] + width)

                words = token.attrs["CONTENT"]
                bbox = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                line_id = token.parent.attrs["ID"]
                block_id = token.parent.parent.attrs["ID"]
                page_id = i
                label = None

                page_data.append((words, bbox, block_id, line_id, page_id, label))

            self.pdf_data.append(page_data)
            self._page_sizes.append((float(page.parent.attrs["WIDTH"]), float(page.parent.attrs["HEIGHT"])))

        return True

    def json(self):
        if not self.pdf_data:
            self._get_raw_from_alto()

        json_data = []
        for page_data in self.pdf_data:
            keys = page_data[0]
            page_json = {k:[] for k in keys}
            for token in page_data[1:]:
                for k, v in zip(keys, token):
                    page_json[k].append(v)

            json_data.append(page_json)

        return json_data

    def page_sizes(self):
        return self._page_sizes

    def get_line_zones(self):
        with open(self.alto_path, "rb") as f:
            content = f.read()
            root = BeautifulSoup(content, "xml")

        for line in root.find_all("TextLine"):
            line_id = line.attrs["ID"]
            top_left = float(line.attrs["HPOS"]), float(line.attrs["VPOS"])
            bottom_right = top_left[0] + float(line.attrs["WIDTH"]), top_left[1] + float(line.attrs["HEIGHT"])

            self._line_rects[line_id] = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])

        return self._line_rects

    def calc_page_main_areas(self):
        with open(self.alto_path, "rb") as f:
            content = f.read()
            root = BeautifulSoup(content, "xml")

        blocks = root.find_all("TextBlock")

        left_even = set()
        right_even = set()
        left_odd = set()
        right_odd = set()
        top_set = set()
        bottom_set = set()

        for block in blocks:
            top = float(block.attrs["VPOS"])
            left = float(block.attrs["HPOS"])
            width = float(block.attrs["WIDTH"])
            height = float(block.attrs["HEIGHT"])

            # small blocks can indicate that it's page numbers, some journal header info, etc. No need in them
            if left == 0 or height < 20 or width < 20 or height * width < 3000:
                continue

            # 奇偶分开计数
            if int(block.parent.parent.attrs["PHYSICAL_IMG_NR"]) % 2 == 0:
                left_even.add(int(left))
                right_even.add(int(left + width))
            else:
                left_odd.add(int(left))
                right_odd.add(int(left + width))

            top_set.add(int(top))
            bottom_set.add(int(top + height))

        page_size = len(root.find_all("Page"))

        page_areas = []

        if left_even and left_odd:
            page_even_x = 0
            page_even_width = 0
            if page_size > 1:
                page_even_x = min(left_even)
                page_even_width = max(right_even) - page_even_x + 1

            page_odd_x = min(left_odd)
            page_odd_width = max(right_odd) - page_odd_x + 1

            page_y = min(top_set)
            page_height = max(bottom_set) - page_y + 1

            page_areas.append((page_odd_x, page_y, page_odd_width, page_height))
            page_areas.append((page_even_x, page_y, page_even_width, page_height))

        print(page_areas)
        page_rect = (page_areas[0][0], page_areas[0][1], \
            page_areas[0][0] + page_areas[0][2], page_areas[0][1] + page_areas[0][3])

        return page_rect

if __name__ == '__main__':
    alto_path = "/Users/hyy/mytask/b_paper/backend/stuff/2022.acl-long.148.2.xml"
    alto_file = AltoFile(alto_path)
    print(alto_file.calc_page_main_areas())