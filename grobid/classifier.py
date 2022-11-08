from grobid.cmd_utils import wapiti_infer

wapiti_model_map = {
    "segment": "/Users/hyy/mytask/b_paper/playground/Wapiti/data/seg_model.wapiti",
    "fulltext": "/Users/hyy/mytask/b_paper/playground/Wapiti/data/fulltext_model.wapiti",
}

def classifier(model_type, feature_path):
    if model_type not in wapiti_model_map:
        return []

    results =  wapiti_infer(wapiti_model_map[model_type], feature_path)
    return results