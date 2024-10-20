import ffmpeg
import os
import re

# 手动指定 ffmpeg 路径
os.environ['PATH'] += os.pathsep + r'C:\Users\75325\AppData\Local\Programs\FFmpeg\bin'

# 定义一个函数来提取文件名中的数字
def extract_number(file_path):
    base_name = os.path.basename(file_path)
    match = re.search(r'(\d+)', base_name)
    if match:
        return int(match.group(1))
    return 0  # 如果没有找到数字，默认返回0

def add_each_subtitle(directory,extensions=['.mp4', '.avi', '.mkv', '.mov', '.flv']):
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                    _, file_name = os.path.split(file)
                    base_name, _ = os.path.splitext(file_name)
                    if base_name.endswith('_st'):
                        continue
                    video_files.append(os.path.join(root, file))
    video_files.sort(key=extract_number)
    for video_path in video_files:
        add_subtitles(video_path=video_path)

def add_subtitles(video_path,font='Arial',font_size=16, font_color='FFFFFF'):
    file_dir, file_name = os.path.split(video_path)
    base_name, ext = os.path.splitext(file_name)
    subtitle_path = f'{file_dir}/{base_name}_subtitle.srt'

    subtitle_content = ""
    with open(subtitle_path, 'r', encoding='utf-8') as f:
        subtitles = f.read()
        subtitle_content = '\n'.join([f"{i}\n{line}" for i, line in enumerate(subtitles.split('\n'), start=1)])
    
    if not subtitle_content or len(subtitle_content) < 10:  # 确保字幕内容至少包含两个字幕行
        print(f'{subtitle_path} is empty or too short, skip')
        return

    output_path = os.path.join(file_dir, base_name + '_st' + ext)
    # 使用ffmpeg将SRT字幕嵌入到视频中
    (
        ffmpeg
        .input(video_path,hwaccel='cuda', vcodec='h264_cuvid')
        .output(
            output_path, 
            vf=f"subtitles={subtitle_path}:force_style='FontName={font},FontSize={font_size},PrimaryColour=&H{font_color}'",
            vcodec='h264_nvenc',
            preset='fast')
        .run(overwrite_output=True)
    )
    

# 示例使用

add_each_subtitle(directory='../../BaiduNetdiskDownload/woman_king')
