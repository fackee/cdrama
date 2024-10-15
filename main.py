import os
import cv2
import pysrt
from utils import list_video_files, extract_text_from_frame_by_qwen, translate_text_by_openai, frame_to_base64,get_movie_info
from config import Config
import json

def extract_subtitles_from_video(video_path,douban_id, frame_rate=2, src_lang='中文', dest_lang='英文'):
    file_dir, file_name = os.path.split(video_path)
    base_name, _ = os.path.splitext(file_name)
    output_subtitle_file_path = os.path.join(file_dir, base_name + '.srt')
    if douban_id:
        movie_info = get_movie_info(subject_id=douban_id)
    translate_system_prompt = Config.translate_prompt(movie_info=movie_info)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps / frame_rate)
    frame_count = 0
    messages = [{"role": "system", "content": translate_system_prompt % (src_lang, dest_lang)}]
    subs = pysrt.SubRipFile()

    index = 0
    last_subtitle = ""
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            base64_frame = frame_to_base64(frame)
            try:
                text = extract_text_from_frame_by_qwen(base64_image=base64_frame)
                if text:
                    subtitle = json.loads(text.strip('```json').strip('```').strip())
                    if subtitle['hasSubtitle']:
                        subtitle_text = subtitle['subTitle']
                        if last_subtitle == subtitle_text:
                            end_time = pysrt.SubRipTime.from_ordinal(int((frame_count + frame_interval) * 1000 / fps))
                            subs[-1].end = end_time
                        else:
                            translated_text = translate_text_by_openai(subtitle_text, messages)
                            print(f'{index}: {subtitle_text} ---- {translated_text}')
                            last_subtitle = subtitle_text
                            if translated_text:
                                start_time = pysrt.SubRipTime.from_ordinal(int(frame_count * 1000 / fps))
                                end_time = pysrt.SubRipTime.from_ordinal(int((frame_count + frame_interval) * 1000 / fps))
                                sub = pysrt.SubRipItem(index + 1, start=start_time, end=end_time, text=translated_text)
                                subs.append(sub)
                                index += 1
            except Exception as e:
                print(e)
        frame_count += 1

    cap.release()
    subs.save(output_subtitle_file_path, encoding='utf-8')
    print(f"字幕已保存到 {output_subtitle_file_path}")

def generate_subtitle_from_dir(directory):
    video_files = list_video_files(directory)
    for video_path in video_files:
        extract_subtitles_from_video(video_path=video_path)

if __name__ == "__main__":
    directory = '/Users/zhujianxin04/mini_drama/wk/merged_video_1.mp4'
    extract_subtitles_from_video(directory)
