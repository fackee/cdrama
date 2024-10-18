import cv2
import os
from PIL import Image
from io import BytesIO
import base64
from utils import extract_text_from_frame_by_qwen,translate_text_by_openai
from convert_subtitle import srt_to_vtt
import json
import time

# 设置Tesseract的路径（如果需要）
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def compress_and_encode_image(image):
    """
    按照比例压缩图片并返回Base64编码
    :param image: PIL Image对象
    :return: Base64编码的图片
    """
    
    # 将图片保存到字节流
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    
    # 获取字节流的Base64编码
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str

def extract_frames(video_path,frames_per_second=1,crop_area=(0, 0.61, 1, 0.16)):
    """
    提取关键帧和中间帧
    :param video_path: 视频路径
    :param frame_interval: 帧间隔
    :return: 帧列表和时间戳列表
    """
    start_time = int(time.time())
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_interval = int(fps / frames_per_second)

    frames = []
    timestamps = []

    frame_number = 0
    success, frame = cap.read()

    while success:
        if frame_number % frame_interval == 0:
            if crop_area:
                h, w, _ = frame.shape
                x = int(w * crop_area[0])
                y = int(h * crop_area[1])
                width = int(w * crop_area[2])
                height = int(h * crop_area[3])
                frame = frame[y:y+height, x:x+width]
            frames.append(frame)
            timestamps.append(frame_number*1000 / fps)
        frame_number += 1
        success, frame = cap.read()
    
    cap.release()
    print(f'extract frame from {video_path} cost: {int(time.time()) - start_time}')
    return frames, timestamps

def detect_subtitles(frames, timestamps):
    """
    检测字幕并记录出现和消失时间
    :param frames: 帧列表
    :param timestamps: 时间戳列表
    :return: 字幕列表
    """
    current_time = int(time.time())
    subtitles = []
    current_subtitle = None
    start_time = None

    for i, frame in enumerate(frames):
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        base64_image = compress_and_encode_image(image)
        
        etext = extract_text_from_frame_by_qwen(base64_image)
        clean_text = etext.strip('```json').strip('```').strip()
        obj = json.loads(clean_text)
        if obj['hasSubtitle'] == True and obj['subTitle'] and len(obj['subTitle']) > 0:
            text = obj['subTitle'].strip()
            text = text.replace('，',' ')
            print(f'{timestamps[i]}: {text}')
        else:
            text = None
        if text and text != current_subtitle:
            if current_subtitle is not None:
                end_time = timestamps[i-1]  # 上一帧的时间戳作为结束时间
                subtitles.append((start_time, end_time, current_subtitle))
            
            current_subtitle = text
            start_time = timestamps[i]

        elif not text and current_subtitle is not None:
            # 当前帧没有字幕，且之前有字幕
            end_time = timestamps[i-1]  # 上一帧的时间戳作为结束时间
            subtitles.append((start_time, end_time, current_subtitle))
            current_subtitle = None
            start_time = None

    # 添加最后一条字幕
    if current_subtitle is not None:
        end_time = timestamps[-1]
        subtitles.append((start_time, end_time, current_subtitle))

    print(f'detect subtile from cost: {int(time.time()) - current_time}')
    return subtitles

def translate_subtitles(subtitles):
    start_time = int(time.time())
    translate_subtitles = []
    for i, (start, end, subtitle) in enumerate(subtitles):
        translate_subtitle = translate_text_by_openai(text=subtitle)
        print(f'translate {start}-{end}: {subtitle} --- {translate_subtitle}')
        if translate_subtitle and len(translate_subtitle) > 0:
            translate_subtitles.append((start,end,translate_subtitle))

    print(f'translate subtitle from cost: {int(time.time()) - start_time}')
    return translate_subtitles

def format_time(milliseconds):
    """
    将毫秒转换为SRT格式的时间字符串
    :param milliseconds: 毫秒
    :return: 格式化的时间字符串
    """
    seconds = milliseconds // 1000
    ms = milliseconds % 1000
    minutes = seconds // 60
    hours = minutes // 60
    return f"{int(hours):02}:{int(minutes % 60):02}:{int(seconds % 60):02},{int(ms):03}"

def backup_subtitles(video_path,subtitles,translate = False):
    file_dir, file_name = os.path.split(video_path)
    base_name, _ = os.path.splitext(file_name)
    if translate:
        output_path = os.path.join(file_dir, base_name + '_translate.txt')
    else:
        output_path = os.path.join(file_dir, base_name + '_origin.txt')
    with open(output_path, 'w') as file:
        for i, (start, end, subtitle) in enumerate(subtitles):
            file.write(f"{start}-{end}: {subtitle}\n")

def write_subtitles(video_path,subtitles):
    file_dir, file_name = os.path.split(video_path)
    base_name, _ = os.path.splitext(file_name)
    output_path = os.path.join(file_dir, base_name + '_subtitle.srt')
    with open(output_path, 'w') as file:
        for i, (start, end, translated_text) in enumerate(subtitles):
            file.write(f"{i+1}\n")
            file.write(f"{format_time(start)} --> {format_time(end)}\n")
            file.write(f"{translated_text}\n\n")

def cvt_subtitle(video_path):
    file_dir, file_name = os.path.split(video_path)
    base_name, _ = os.path.splitext(file_name)
    srt_path = os.path.join(file_dir, base_name + '_subtitle.srt')
    vtt_path = os.path.join(file_dir, base_name + '_subtitle.vtt')
    srt_to_vtt(srt_path=srt_path,vtt_path=vtt_path)

def embed_subtitle(video_path):
    file_dir, file_name = os.path.split(video_path)
    base_name, _ = os.path.splitext(file_name)
    subtitle_path = os.path.join(file_dir, base_name + '_subtitle.srt')
    embed_video_path = os.path.join(file_dir, base_name + '_embed.mp4')
    os.system(f"ffmpeg -i {video_path} -vf subtitles={subtitle_path} {embed_video_path}")
    

def start_single(video_path):
    try:
        start_time = int(time.time())
        # 存在字母，跳过
        file_dir, file_name = os.path.split(video_path)
        base_name, _ = os.path.splitext(file_name)
        subtitle_file = os.path.join(file_dir, base_name + '_subtitle.srt')
        if os.path.exists(subtitle_file):
            print(f'{subtitle_file} exists, skip')
            return
        
        # 存在翻译，直接写字幕
        translate_file = os.path.join(file_dir, base_name + '_translate.txt')
        if os.path.exists(translate_file):
            translated_subtitles = []
            with open(translate_file, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.strip():
                        time_arr = line.split(':')[0]
                        start, end = time_arr.split('-')
                        text = line.split(':')[1]
                        translated_subtitles.append((float(start),float(end),text))
                        print(f'{start}-{end}: {text}')
            write_subtitles(video_path=video_path,subtitles=translated_subtitles)
            print(f'{translate_file} exists, skip')
            return
        
        # 提取帧，直接翻译
        origin_file = os.path.join(file_dir, base_name + '_origin.txt')
        if os.path.exists(origin_file):
            subtitle = []
            with open(origin_file, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.strip():
                        time_arr = line.split(':')[0]
                        start, end = time_arr.split('-')
                        text = line.split(':')[1]
                        subtitle.append((start,end,text))
                        print(f'{start}-{end}: {text}')
            translated_subtitles = translate_subtitles(subtitles=subtitle)
            backup_subtitles(video_path=video_path,subtitles=translated_subtitles,translate=True)
            write_subtitles(video_path=video_path,subtitles=translated_subtitles)
            print(f'{origin_file} exists, skip')
            return

        frames, timestamps = extract_frames(video_path, frames_per_second=8)
        subtitles = detect_subtitles(frames, timestamps)
        backup_subtitles(video_path=video_path,subtitles=subtitles,translate=False)
        translated_subtitles = translate_subtitles(subtitles=subtitles)
        backup_subtitles(video_path=video_path,subtitles=translated_subtitles,translate=True)
        write_subtitles(video_path=video_path,subtitles=translated_subtitles)
        #cvt_subtitle(video_path=video_path)
        print(f'handle {video_path} cost: {int(time.time()) - start_time}')
    except Exception as e:
        print(f'handle {video_path} error',e)

def start_batch(directory,extensions=['.mp4', '.avi', '.mkv', '.mov', '.flv']):
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                video_files.append(os.path.join(root, file))
    video_files.sort(key=lambda x: os.path.basename(x).lower())
    for video_path in video_files:
        start_single(video_path=video_path)

def start_all(directory):
    dir_all = []
    for root, _, files in os.walk(directory):
        for file in files:
            # 判断文件是否是文件夹
            if os.path.isdir(os.path.join(root, file)):
                dir_all.append(os.path.join(root, file))
    for dir in dir_all:
        start_batch(directory=dir)



# 示例使用
start_all('../../BaiduNetdiskDownload')
