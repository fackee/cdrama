import cv2
import numpy as np
import Quartz.CoreGraphics as CG
from Vision import VNImageRequestHandler, VNRecognizeTextRequest, VNRequest
import ctypes

def is_chinese(text):
    """
    判断一个字符串是否包含中文字符
    :param text: 输入字符串
    :return: 如果包含中文字符返回 True，否则返回 False
    """
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def numpy_to_cgimage(numpy_array):
    """
    将 numpy 数组转换为 CGImage
    :param numpy_array: 输入的 numpy 数组
    :return: 转换后的 CGImage 对象
    """
    height, width, channels = numpy_array.shape
    assert channels == 3, "Input image must have 3 color channels (RGB)."
    print(height,width,channels)
    # Create a Quartz color space
    color_space = CG.CGColorSpaceCreateDeviceRGB()

    # Ensure the numpy array is contiguous in memory
    numpy_array = np.ascontiguousarray(numpy_array, dtype=np.uint8)

    # Create a Quartz bitmap context
    bitmap_info = CG.kCGImageAlphaNoneSkipLast
    bytes_per_row = channels * width

    context = CG.CGBitmapContextCreate(numpy_array.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)), width, height, 8, bytes_per_row, color_space, bitmap_info)

    # Check if context creation was successful
    if context is None:
        raise ValueError("Failed to create CGBitmapContext")

    # Create a Quartz image from the context
    cg_image = CG.CGBitmapContextCreateImage(context)
    
    # Check if image creation was successful
    if cg_image is None:
        raise ValueError("Failed to create CGImage")
    
    return cg_image

def ocr_frame(frame, index):
    """
    使用 Apple 的 Vision 框架识别视频帧中的文字，并判断是否包含中文
    :param frame: 视频帧（numpy 数组）
    :param index: 当前帧的索引
    :return: 识别的文字和是否包含中文的布尔值
    """
    # 将视频帧从 BGR 转换为 RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # 将 numpy 数组转换为 CGImage
    cg_image = numpy_to_cgimage(frame_rgb)
    
    # 创建文本识别请求
    # 创建文本识别请求
    request = VNRecognizeTextRequest.alloc().initWithCompletionHandler_(None)
    
    # 设置识别级别为准确
    request.setRecognitionLevel_(1)
    
    # 创建图像请求处理器
    handler = VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
    
    # 执行文本识别请求
    success, error = handler.performRequests_error_([request], None)
    if not success:
        print(f"Text recognition failed: {error}")
        return "", False
    
    # 提取识别的文字
    text = "\n".join([observation.string() for observation in request.results()])
    
    # 打印识别的文字
    print("识别的文字：")
    print(text)
    
    # 判断文字是否包含中文
    contains_chinese = is_chinese(text)
    print(f"是否包含中文：{contains_chinese}")
    
    return text, contains_chinese


# 示例使用
# 打开视频文件
cap = cv2.VideoCapture('/Users/zhujianxin04/mini_drama/shcz/2.mp4')
fps = cap.get(cv2.CAP_PROP_FPS)
crop_area=(0, 0.61, 1, 0.14)
index = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    index += 1
    if index % fps != 0:
        continue
    if crop_area:
        h, w, _ = frame.shape
        x = int(w * crop_area[0])
        y = int(h * crop_area[1])
        width = int(w * crop_area[2])
        height = int(h * crop_area[3])
        frame = frame[y:y+height, x:x+width]
    # 对当前帧进行 OCR 识别
    ocr_text, contains_chinese = ocr_frame(frame,index)
    # 在窗口中显示当前帧

# 释放视频捕获对象并关闭所有窗口
cap.release()
cv2.destroyAllWindows()
