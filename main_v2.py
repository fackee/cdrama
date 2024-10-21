import os
from utils import translate_text_by_openai,translate_text_by_openai_v2,correct_subtitle_by_openai
from convert_subtitle import srt_to_vtt
import time
from baidu_ocr import detect_subtitle_by_ocr
import traceback
import re
from config import Config

def detect_subtitles(video_path,corp_area = (0, 0.73, 1, 0.074),frame_per_second = 10,concurrents = 8):
    current_time = int(time.time())
    frame_subtitles = detect_subtitle_by_ocr(video_path=video_path,frame_per_second=frame_per_second,corp_area=corp_area)
    current_subtitle = None
    start_time = None
    last_timestamp = 0
    subtitles = []
    for timestamp,text,_ in frame_subtitles:
        if text and text != current_subtitle:
            if current_subtitle is not None:
                end_time = last_timestamp  # 上一帧的时间戳作为结束时间
                subtitles.append((start_time, end_time, current_subtitle))
            
            current_subtitle = text
            start_time = timestamp

        elif not text and current_subtitle is not None:
            # 当前帧没有字幕，且之前有字幕
            end_time = last_timestamp  # 上一帧的时间戳作为结束时间
            subtitles.append((start_time, end_time, current_subtitle))
            current_subtitle = None
            start_time = None
        last_timestamp = timestamp

    # 添加最后一条字幕
    if current_subtitle is not None:
        end_time = last_timestamp
        subtitles.append((start_time, end_time, current_subtitle))

    print(f'detect subtile from cost: {int(time.time()) - current_time}')
    return subtitles


def merge_subtitles(subtitles):
    """
    合并相邻 text 一致的字幕
    :param subtitles: 包含三元组 (start_time, end_time, text) 的列表
    :return: 合并后的字幕列表
    """
    if not subtitles:
        return []

    merged_subtitles = []
    current_start_time, current_end_time, current_text = subtitles[0]

    for i in range(1, len(subtitles)):
        start_time, end_time, text = subtitles[i]
        if text == current_text:
            # 如果相邻的 text 一致，更新 current_end_time
            current_end_time = end_time
        else:
            # 如果相邻的 text 不一致，添加当前字幕到 merged_subtitles
            merged_subtitles.append((current_start_time, current_end_time, current_text))
            # 更新 current_start_time, current_end_time 和 current_text
            current_start_time = start_time
            current_end_time = end_time
            current_text = text

    # 添加最后一个字幕
    merged_subtitles.append((current_start_time, current_end_time, current_text))

    return merged_subtitles

def translate_subtitles(subtitles,messages):
    subtitles = merge_subtitles(subtitles)
    start_time = int(time.time())
    translate_subtitles = []
    for start, end, subtitle in subtitles:
        translate_subtitle = translate_text_by_openai(text=subtitle,messages=messages)
        print(f'translate {start}-{end}: {subtitle} --- {translate_subtitle}')
        if translate_subtitle and len(translate_subtitle.strip()) > 0:
            translate_subtitles.append((start,end,translate_subtitle))

    print(f'translate subtitle from cost: {int(time.time()) - start_time}')
    return merge_subtitles(translate_subtitles)


def translate_subtitles_v2(movie_info,subtitles):
    subtitles = merge_subtitles(subtitles)
    start_time = int(time.time())
    translate_subtitles = []
    origin_subtitle_content = ""
    for start, end, subtitle in subtitles:
        origin_subtitle_content += f'{start}-{end}: {subtitle}\n'
    corrected_subtitle_content = correct_subtitle_by_openai(movie_info,origin_subtitle_content)
    corrected_subtitle_content = corrected_subtitle_content.replace('```','')
    translated_subtitle_content = translate_text_by_openai_v2(movie_info,corrected_subtitle_content)
    translated_subtitle_content = translated_subtitle_content.replace('```','')
    translated_subtitle_content_arr = translated_subtitle_content.split('\n')
    for ts in translated_subtitle_content_arr:
        ts_arr = ts.split(':')
        if len(ts_arr) != 2:
            continue
        time_content = ts_arr[0]
        time_arr = time_content.split('-')
        if len(time_arr) != 2:
            continue
        start = float(time_arr[0])
        end = float(time_arr[1])
        text = ts_arr[1]
        translate_subtitles.append((start,end,text))
    print(translate_subtitles)
    print(f'translate subtitle from cost: {int(time.time()) - start_time}')
    return merge_subtitles(translate_subtitles)


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
    with open(output_path, 'w', encoding='utf-8') as file:
        for i, (start, end, subtitle) in enumerate(subtitles):
            file.write(f"{start}-{end}: {subtitle}\n")

def write_subtitles(video_path,subtitles):
    file_dir, file_name = os.path.split(video_path)
    base_name, _ = os.path.splitext(file_name)
    output_path = os.path.join(file_dir, base_name + '_subtitle.srt')
    with open(output_path, 'w',encoding='utf-8') as file:
        for i, (start, end, translated_text) in enumerate(subtitles):
            print(f'{start}-{end}: {translated_text}')
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
    

def start_single(video_path,movie_info):
    try:
        print(f'starting process video {video_path}')
        translate_system_prompt = Config.translate_prompt(movie_info=movie_info)
        messages = [{"role": "system", "content": translate_system_prompt}]
        start_time = int(time.time())
        # 存在字幕，跳过
        file_dir, file_name = os.path.split(video_path)
        base_name, _ = os.path.splitext(file_name)
        subtitle_file = os.path.join(file_dir, base_name + '_subtitle.srt')
        if os.path.exists(subtitle_file):
            content = ""
            with open(subtitle_file, 'r',encoding='utf-8') as f:
                content = f.read()
            if len(content) > 10:
                print(f'{subtitle_file} exists, skip')
                return
        
        # 存在翻译，直接写字幕
        translate_file = os.path.join(file_dir, base_name + '_translate.txt')
        if os.path.exists(translate_file):
            translated_subtitles = []
            with open(translate_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.strip():
                        time_arr = line.split(':')[0]
                        start, end = time_arr.split('-')
                        text = line.split(':')[1]
                        translated_subtitles.append((float(start),float(end),text))
            write_subtitles(video_path=video_path,subtitles=translated_subtitles)
            print(f'{translate_file} exists, skip')
            return
        
        # 提取帧，直接翻译
        origin_file = os.path.join(file_dir, base_name + '_origin.txt')
        if os.path.exists(origin_file):
            subtitle = []
            with open(origin_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.strip():
                        time_arr = line.split(':')[0]
                        start, end = time_arr.split('-')
                        text = line.split(':')[1]
                        subtitle.append((start,end,text))
            translated_subtitles = translate_subtitles_v2(movie_info=movie_info,subtitles=subtitle)
            backup_subtitles(video_path=video_path,subtitles=translated_subtitles,translate=True)
            write_subtitles(video_path=video_path,subtitles=translated_subtitles)
            print(f'{origin_file} exists, skip')
            return

        subtitles = detect_subtitles(video_path)
        backup_subtitles(video_path=video_path,subtitles=subtitles,translate=False)
        # translated_subtitles = translate_subtitles(subtitles=subtitles,messages=messages)
        # backup_subtitles(video_path=video_path,subtitles=translated_subtitles,translate=True)
        # write_subtitles(video_path=video_path,subtitles=translated_subtitles)
        # cvt_subtitle(video_path=video_path)
        print(f'handle {video_path} cost: {int(time.time()) - start_time}')
    except Exception as e:
        print(f'handle error: {video_path}',e)
        traceback.print_exc()

# 定义一个函数来提取文件名中的数字
def extract_number(file_path):
    base_name = os.path.basename(file_path)
    match = re.search(r'(\d+)', base_name)
    if match:
        return int(match.group(1))
    return 0  # 如果没有找到数字，默认返回0

def start_batch(directory,video_info,extensions=['.mp4', '.avi', '.mkv', '.mov', '.flv']):
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                video_files.append(os.path.join(root, file))
    video_files.sort(key=extract_number)
    for video_path in video_files:
        start_single(video_path=video_path,movie_info=video_info)

def start_all(directory):
    dir_all = []
    for root, _, files in os.walk(directory):
        for file in files:
            # 判断文件是否是文件夹
            if os.path.isdir(os.path.join(root, file)):
                dir_all.append(os.path.join(root, file))
    for dir in dir_all:
        start_batch(directory=dir)


if __name__ == '__main__': 
    video_path = '/Users/zhujianxin04/mini_drama/wk/1.mp4'
    movie_info = '商业新秀许安生穿越到桃园县五年，把治下打造成世外桃源却拒不缴纳朝廷赋税，引来女帝微服私访、讨要税银。发现了许安生的能力，想要扶持桃源县却被反派安乐侯一路暗杀。'
    start_single(video_path=video_path,movie_info=movie_info)