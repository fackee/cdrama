import os
from utils import translate_text_by_openai
from convert_subtitle import srt_to_vtt
import time
from baidu_ocr import detect_subtitle_by_ocr
import traceback

def detect_subtitles(video_path,corp_area = (0, 0.61, 1, 0.14),frame_per_second = 1,concurrents = 8):
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

    print(subtitles)
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

def translate_subtitles(subtitles,movie_info):
    start_time = int(time.time())
    translate_subtitles = []
    for start, end, subtitle in subtitles:
        translate_subtitle = translate_text_by_openai(text=subtitle,movie_info=movie_info)
        print(f'translate {start}-{end}: {subtitle} --- {translate_subtitle}')
        if translate_subtitle and len(translate_subtitle) > 0:
            translate_subtitles.append((start,end,translate_subtitle))

    merged_subtitles = []
    print(f'translate subtitle from cost: {int(time.time()) - start_time}')
    return merged_subtitles

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
    

def start_single(video_path,movie_info):
    try:
        start_time = int(time.time())
        # 存在字幕，跳过
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
            translated_subtitles = translate_subtitles(subtitles=subtitle,movie_info=movie_info)
            backup_subtitles(video_path=video_path,subtitles=translated_subtitles,translate=True)
            write_subtitles(video_path=video_path,subtitles=translated_subtitles)
            print(f'{origin_file} exists, skip')
            return

        subtitles = detect_subtitles(video_path)
        backup_subtitles(video_path=video_path,subtitles=subtitles,translate=False)
        translated_subtitles = translate_subtitles(subtitles=subtitles,movie_info=movie_info)
        backup_subtitles(video_path=video_path,subtitles=translated_subtitles,translate=True)
        write_subtitles(video_path=video_path,subtitles=translated_subtitles)
        cvt_subtitle(video_path=video_path)
        print(f'handle {video_path} cost: {int(time.time()) - start_time}')
    except Exception as e:
        print(f'handle {video_path} error',e)
        traceback.print_exc()

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


if __name__ == '__main__': 
    video_path = '/Users/zhujianxin04/mini_drama/shcz/1.mp4'
    movie_info = '沈熹微死的那天，正好是裴云霄结婚的日子！裴云霄是沈家司机的儿子，沈熹微心疼他家境不好，让他和自己一起坐迈巴赫上学，给他刷自己的卡，送他昂贵的奢侈品，把父亲留下的公司给他。他花着她的钱，享受着她给的一切，却和别人谈着恋爱，把他的女朋友宠成公主，却把她当佣人使唤……她给他打电话，想让他给自己一点钱看病，他却残忍地道：“被你缠着的这些年，就是我的噩梦！沈熹微，你赶紧去死。”她死了！直到死的那一刻，才知道，那个曾经被自己拒绝的京圈太子爷，竟然一直在等着她……'
    # 示例使用
    start_single(video_path=video_path,movie_info=movie_info)