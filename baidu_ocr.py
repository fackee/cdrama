from paddleocr import PaddleOCR
import cv2
import time
import multiprocessing

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

def ocr_frame(ocr,frame, timestamp):
    """
    使用 OCR 识别视频帧中的文字，并判断是否包含中文
    :param frame: 视频帧（numpy 数组）
    :param timestamp: 当前帧的时间戳
    :return: 识别的文字和是否包含中文的布尔值
    """
    # 将视频帧转为灰度图像
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 使用 PaddleOCR 进行 OCR 识别
    result = ocr.ocr(gray, cls=True)
    if result and result[0]:
        # 拼接识别的文字
        text = '\n'.join([line[1][0] for line in result[0]])
        # 判断文字是否包含中文
        contains_chinese = is_chinese(text)
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
    orc = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
    for timestamp,frame in frames:
        ocr_text, contains_chinese = ocr_frame(orc,frame,timestamp)
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

    print(f'total sub frame: {tf}')

    for p in processes:
        p.join()

    # 收集结果
    results = list(result_list)
    results.sort(key=lambda x: x[0])  # 根据 timestamp 排序

    print(f'ocr cost: {int(time.time()) - start_time}')
    return results