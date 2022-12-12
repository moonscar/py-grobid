OUTPUT_PATH=$1

wget https://github.com/kermitt2/grobid/blob/0.7.1-fixes/grobid-home/models/segmentation/model.wapiti -P $OUTPUT_PATH/
mv $OUTPUT_PATH/model.wapiti $OUTPUT_PATH/seg_model.wapiti

wget https://github.com/kermitt2/grobid/blob/0.7.1-fixes/grobid-home/models/fulltext/model.wapiti -P $OUTPUT_PATH/
mv $OUTPUT_PATH/model.wapiti $OUTPUT_PATH/fulltext_model.wapiti