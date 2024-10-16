import os
import cv2
import pysrt
from utils import list_video_files, extract_text_from_frame_by_qwen, translate_text_by_openai, frame_to_base64
import concurrent
import threading
import json
import time

lock = threading.Lock()


def extract_subtitle_task(frame_count,frame_base64,subtitle_array):
    try:
        text = extract_text_from_frame_by_qwen(base64_image=frame_base64)
        clean_text = text.strip('```json').strip('```').strip()
        obj = json.loads(clean_text)
        if obj['hasSubtitle'] == True and obj['subTitle'] and len(obj['subTitle']) > 0:
            text = obj['subTitle'].strip()
            print(f'{frame_count}-extract: {text}')
        else:
            text = ""
    except Exception as e:
        print(e)
        text = ""
    with lock:
        if 0 <= frame_count < len(subtitle_array):  # 确保索引在有效范围内
            subtitle_array[frame_count] = text



def extract_subtitles_from_video(video_path,extract_subtitle_concurrent = 4,frame_rate=10):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = fps / frame_rate
    # 获取视频的总帧数
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    subtitle_array = [None] * total_frames
    frame_count = 0
    futures = []
    start_time = int(time.time())
    last_base64 = ""
    with concurrent.futures.ThreadPoolExecutor(max_workers=extract_subtitle_concurrent) as executor:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            print(f'handled: {frame_count} , left: {total_frames - frame_count}')
            # if frame_count % 1 == 0: 
            base64_frame = frame_to_base64(frame,compress_rate=50)
            if last_base64 == base64_frame:
                print("duplicate")
            else:
                last_base64 = base64_frame
            # 创建线程池处理视频帧
            futures.append(executor.submit(extract_subtitle_task,frame_count,base64_frame,subtitle_array))
            frame_count += 1
    concurrent.futures.wait(futures)
    current_time = int(time.time())
    print(f'extract {total_frames} frames cost {current_time - start_time}')
    cap.release()
    return fps,total_frames,subtitle_array


def translate_subtitles(subtitle_array,total_frame):
    translate_subtitle_array = [None] * total_frame
    last_subtitle = ""
    start_time = int(time.time())

    for frame_count,subtitle in enumerate(subtitle_array):
        if subtitle and len(subtitle) > 0:
            if last_subtitle != subtitle:
                text = translate_text_by_openai(text=subtitle)
                translate_subtitle_array[frame_count] = text
                last_subtitle = subtitle
            else:
                translate_subtitle_array[frame_count] = subtitle
    current_time = int(time.time())
    print(f'translate {total_frame} frames cost {current_time - start_time}')
    return translate_subtitle_array


def write_subtitle(video_path,fps,translate_subtitle_array):
    file_dir, file_name = os.path.split(video_path)
    base_name, _ = os.path.splitext(file_name)
    output_subtitle_file_path = os.path.join(file_dir, base_name + '.srt')
    subs = pysrt.SubRipFile()
    start = None
    last_non_empty = None
    index = 1
    for i in range(len(translate_subtitle_array)):
        translated_subtitle = translate_subtitle_array[i]
        if not translated_subtitle or len(translated_subtitle) <= 0:
            continue
        if start is None:
            start = i
        elif translated_subtitle != translate_subtitle_array[start]:
            if i - start > 1:
                start_frame = start
                end_frame = i - 1
                start_time = pysrt.SubRipTime.from_ordinal(int(start_frame * 1000 / fps))
                end_time = pysrt.SubRipTime.from_ordinal(int(end_frame * 1000 / fps))
                sub = pysrt.SubRipItem(index, start=start_time, end=end_time, text=translated_subtitle)
                subs.append(sub)
            else:
                start_frame = start
                end_frame = start
                start_time = pysrt.SubRipTime.from_ordinal(int(start_frame * 1000 / fps))
                end_time = pysrt.SubRipTime.from_ordinal(int(end_frame * 1000 / fps))
                sub = pysrt.SubRipItem(index, start=start_time, end=end_time, text=translated_subtitle)
                subs.append(sub)
            index += 1
            start = i
        last_non_empty = i
     # 检查最后一组连续重复元素
    if start is not None and last_non_empty is not None:
        if len(translate_subtitle_array) - start > 1:
            start_frame = start
            end_frame = len(translate_subtitle_array) - 1
            start_time = pysrt.SubRipTime.from_ordinal(int(start_frame * 1000 / fps))
            end_time = pysrt.SubRipTime.from_ordinal(int(end_frame * 1000 / fps))
            sub = pysrt.SubRipItem(index + 1, start=start_time, end=end_time, text=translate_subtitle_array[start])
            subs.append(sub)
        else:
            start_frame = start
            end_frame = start
            start_time = pysrt.SubRipTime.from_ordinal(int(start_frame * 1000 / fps))
            end_time = pysrt.SubRipTime.from_ordinal(int(end_frame * 1000 / fps))
            sub = pysrt.SubRipItem(index + 1, start=start_time, end=end_time, text=translate_subtitle_array[start])
            subs.append(sub)
    subs.save(output_subtitle_file_path, encoding='utf-8')
    print(f"字幕已保存到 {output_subtitle_file_path}")


def hanle_video(path,extract_subtitle_concurrent=2):
    fps,total_frames,subtitle_array = extract_subtitles_from_video(video_path=path,extract_subtitle_concurrent=extract_subtitle_concurrent)
    translate_subtitle_array = translate_subtitles(subtitle_array=subtitle_array,total_frame=total_frames)
    write_subtitle(video_path=path,fps=fps,translate_subtitle_array=translate_subtitle_array)

def generate_subtitle_from_dir(directory):
    video_files = list_video_files(directory)
    for video_path in video_files:
        hanle_video(video_path=video_path)

if __name__ == "__main__":
    directory = './asserts/short_drama.mp4'
    hanle_video(directory,extract_subtitle_concurrent=2)
