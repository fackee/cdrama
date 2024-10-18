from paddleocr import PaddleOCR
import cv2
import time
import queue
import threading
import concurrent

lock = threading.Lock()

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
        print(f"识别结果-{timestamp}: {text}")
        return text,contains_chinese
    return None, False

def read_frames(video_path,frame_queue,frame_per_second = 16,crop_area = (),stop_signal = 16):
    """
    从视频捕获对象中读取帧并放入队列中
    :param frame_queue: 存储帧的队列
    :param crop_area: 裁剪区域
    """
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
        frame_queue.put((timestamp, frame))
    for _ in range(stop_signal):  # 向队列中放入结束信号
        frame_queue.put(None)
        # 释放视频捕获对象并关闭所有窗口
    cap.release()
    cv2.destroyAllWindows()

def process_frames(orc,frame_queue, results):
    """
    从队列中读取帧并进行 OCR 处理
    :param frame_queue: 存储帧的队列
    :param results: 存储结果的列表
    """
    while True:
        item = frame_queue.get()
        if item is None:
            frame_queue.task_done()
            break
        timestamp, frame = item
        ocr_text, contains_chinese = ocr_frame(orc,frame,timestamp)
        with lock:
            results.append((timestamp, ocr_text, contains_chinese))
        frame_queue.task_done()



def detect_subtitle_by_ocr(video_path,frame_per_second = 10,corp_area = (0, 0.61, 1, 0.14),concurrents = 16,queue_size = 2048):
    # 示例使用
    crop_area = corp_area
    frame_queue = queue.Queue(maxsize=queue_size)
    results = []
    start_time = int(time.time())
    # 启动帧读取线程
    reader_thread = threading.Thread(target=read_frames, args=(video_path,frame_queue,frame_per_second,crop_area,concurrents))
    reader_thread.start()

    # 启动帧处理线程池
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrents) as executor:
        ocr_instances = [PaddleOCR(use_angle_cls=True, lang='ch', show_log=False) for _ in range(concurrents)]
        futures = [executor.submit(process_frames, ocr_instances[i], frame_queue, results) for i in range(concurrents)]

    reader_thread.join()
    frame_queue.join()
    # 等待所有处理线程完成
    concurrent.futures.wait(futures)
    print(f'ocr cost: {int(time.time()) - start_time}')
    return results