from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
import cv2

ocr_recognize = pipeline(Tasks.ocr_recognition, model='damo/ofa_ocr-recognition_web_base_zh', model_revision='v1.0.1')

### 使用图像文件
### 请准备好名为'ocr_recognition.jpg'的图像文件
img_path = './asserts/samples/48880.0.jpg'
img = cv2.imread(img_path)
result = ocr_recognize(img)
print(result)