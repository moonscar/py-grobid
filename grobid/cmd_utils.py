import subprocess

alto_path = "/usr/bin/pdfalto"
wapiti_path = "/usr/bin/wapiti"

def alto_parser(pdf_path, output_path):
    ret = subprocess.call([alto_path, pdf_path, output_path])
    return ret

def wapiti_infer(model_path, feature_path):
    p = subprocess.Popen(" ".join([wapiti_path, "label", "-m", model_path, feature_path]), shell=True, stdout=subprocess.PIPE)

    ret = []

    result_idx = 0
    results = p.stdout.readlines()

    with open(feature_path) as f:
        for l in f:
            result_line = results[result_idx].decode()

            while not result_line.startswith(l.strip()):
                result_idx += 1
                result_line = results[result_idx].decode()

            ret.append(results[result_idx].decode())

            result_idx += 1

    return ret

if __name__ == '__main__':
    ret = wapiti_infer("/Users/hyy/mytask/b_paper/playground/Wapiti/data/seg_model.wapiti", "/Users/hyy/mytask/b_paper/playground/wapiti_out/self_extract.segment.feature")
