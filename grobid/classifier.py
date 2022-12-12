import os
from grobid.cmd_utils import wapiti_infer

wapiti_model_map = {
    "segment": "seg_model.wapiti",
    "fulltext": "fulltext_model.wapiti",
}

def classifier(model_type, feature_path):
    if model_type not in wapiti_model_map:
        return []

    results =  wapiti_infer(wapiti_model_map[model_type], feature_path)
    return results

def set_model_path(model_path):
    for key in wapiti_model_map:
        model_name = wapiti_model_map[key]
        wapiti_model_map[key] = os.path.join(model_path, model_name)
        assert os.path.exists(wapiti_model_map[key])

    return True