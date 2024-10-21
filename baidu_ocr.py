from paddleocr import PaddleOCR
import cv2
import time
from PIL import Image,ImageEnhance
import multiprocessing
import numpy as np
import os

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

def orc_image(image_path):
    paddleocr = PaddleOCR(use_angle_cls=False,lang='ch', show_log=False,det_model_dir='./models/ch_PP-OCRv4_det_server_infer',rec_model_dir='./models/ch_PP-OCRv4_rec_server_infer')
    #sr_image = super_resolution(image_path)
    img = cv2.imread(image_path)
    result = paddleocr.ocr(img)
    if result and result[0]:
        # 拼接识别的文字
        text = ""
        for line in result[0]:
            t = line[1][0]
            #left_top_y = line[0][0][1]
            right_top_y = line[0][1][1]
           # left_bottom_y = line[0][2][1]
            right_bottom_y = line[0][3][1]
            if right_bottom_y - right_top_y > 40:
                text += t
        text = text.strip()
        text = text.replace('\n', '')
        print(text)

def ocr_frame(ocr,frame,timestamp):
    """
    使用 OCR 识别视频帧中的文字，并判断是否包含中文
    :param frame: 视频帧（numpy 数组）
    :return: 识别的文字和是否包含中文的布尔值
    """
    output_path =f"asserts/samples/{timestamp}.jpg"
        
     # 保存帧为图片
    cv2.imwrite(output_path, frame)
    # 使用 PaddleOCR 进行 OCR 识别
    result = ocr.ocr(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if result and result[0]:
        # 拼接识别的文字
        text = ""
        for line in result[0]:
            t = line[1][0]
            #left_top_y = line[0][0][1]
            right_top_y = line[0][1][1]
           # left_bottom_y = line[0][2][1]
            right_bottom_y = line[0][3][1]
            if right_bottom_y - right_top_y > 40:
                text += t
        # 判断文字是否包含中文
        contains_chinese = is_chinese(text)
        text = text.strip()
        text = text.replace('\n', '')
        return text,contains_chinese
    return None, False

def read_frames(video_path,frame_per_second = 16,crop_area = ()):
    """
    从视频捕获对象中读取帧并放入队列中
    :param frame_queue: 存储帧的队列
    :param crop_area: 裁剪区域
    """
    frames = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps / frame_per_second)
    frame_number = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_number += 1
        if frame_number % frame_interval != 0:
            continue
        if crop_area:
            h, w, _ = frame.shape
            x = int(w * crop_area[0])
            y = int(h * crop_area[1])
            width = int(w * crop_area[2])
            height = int(h * crop_area[3])
            frame = frame[y:y+height, x:x+width]
        timestamp = frame_number*1000 / fps
        frames.append((timestamp, frame))
    # 释放视频捕获对象并关闭所有窗口
    cap.release()
    return frames

def process_frames(frames, result_list):
    """
    从队列中读取帧并进行 OCR 处理
    :param frame_queue: 存储帧的队列
    :param result_queue: 存储结果的列表
    """
    paddleocr = PaddleOCR(use_angle_cls=True,lang='ch', show_log=False,det_model_dir='./modes/ch_ppocr_server_v2.0_det_infer',rec_model_dir='./modes/ch_ppocr_server_v2.0_rec_infer')
    for timestamp,frame in frames:
        ocr_text, contains_chinese = ocr_frame(paddleocr,frame,timestamp)
        result_list.append((timestamp, ocr_text, contains_chinese))
    print("process_frames finished")

def detect_subtitle_by_ocr(video_path,frame_per_second = 10,corp_area = (0, 0.61, 1, 0.14),concurrents = multiprocessing.cpu_count()):
    # 示例使用
    start_time = int(time.time())

    # 启动帧读取
    frames = read_frames(video_path=video_path,frame_per_second=frame_per_second,crop_area=corp_area)

    # 启动帧处理进程池
    manager = multiprocessing.Manager()
    result_list = manager.list()
    processes = []
    k, m = divmod(len(frames), concurrents)
    frame_slice = [frames[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(concurrents)]
    print(f'total frame: {len(frames)}')
    tf = 0
    for sub_frame in frame_slice:
        tf += len(sub_frame)
        p = multiprocessing.Process(target=process_frames, args=(sub_frame, result_list))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    # 收集结果
    results = list(result_list)
    results.sort(key=lambda x: x[0])  # 根据 timestamp 排序

    print(f'ocr cost: {int(time.time()) - start_time}')
    return results

# paddleocr = PaddleOCR(lang='ch', show_log=False,
#                       det_model_dir='.paddleocr\\whl\\det\\ch\\ch_PP-OCRv4_det_infer',
#                       rec_model_dir='.paddleocr\\whl\\rec\\ch\\ch_PP-OCRv4_rec_infer')
# img = cv2.imread('117120.0.jpg')  # 打开需要识别的图片
# result = paddleocr.ocr(img)
# for line in result[0]:
#     t = line[1][0]
#     print(t)
#     left_top_y = line[0][0][1]
#     right_top_y = line[0][1][1]
#     left_bottom_y = line[0][2][1]
#     right_bottom_y = line[0][3][1]
#     print(left_top_y,right_top_y,left_bottom_y,right_bottom_y)


# for i in range(2):
#     orc_image('asserts/samples/sr.jpg')