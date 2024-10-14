import os
from PIL import Image
import pysrt
import base64
from openai import OpenAI
import json
import time
import cv2
import numpy as np
import io
from qwen import Qwen2VLTool

extract_subtile_prompt = '''
该图片是短剧的视频帧，识别出图片中的字幕。输出格式严格按照下面的json格式输出。
<format>
{'hasSubtitle': $HASSUBTITLE # true or false,'subTitle': $SUBTITLE}
</format>
注意，如果你遇到模棱两可的翻译选择，结合上下文选择你认为最合适的输出就可以，不要让我选择。
'''

translate_promot = '''你现在是一个专业的字幕翻译师, 你需要将这篇短剧的字幕由 %s 翻译成 %s. 特别注意，你只需要输出翻译后的内容，不要输出与原文翻译无关的内容。
'''


def translate_text_with_chatgpt(text, messages,qwen:Qwen2VLTool):
    # 添加用户输入到消息历史
    print(messages)
    messages.append({"role": "user", "content": text})
    
    # 调用qwen进行翻译
    inputs = tool.process_messages(messages)
    # 获取翻译结果
    translation = tool.generate_output(inputs)[0]
    messages.append({"role": "assistant", "content": translation})
    return translation

def frame_to_base64(frame):
    """
    将视频帧转换为Base64编码

    :param frame: 视频帧（图像）
    :return: Base64编码的字符串
    """
    # 将帧转换为PIL图像
    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # 将PIL图像转换为字节流
    buffered = io.BytesIO()
    pil_image.save(buffered, format="JPEG")
    
    # 将字节流编码为Base64
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return img_str

def extract_text_from_frame(base64_image,qwen:Qwen2VLTool):
    message = [
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": extract_subtile_prompt
            },
            {
                "type": "image_url",
                "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
            ]
        }
    ]
    input = qwen.process_messages(messages=message)
    return qwen.generate_output(inputs=input)[0]

def extract_subtitles_from_video(video_path, output_file,frame_rate=1,src_lang='中文', dest_lang='英文'):
    """
    从视频中提取字幕并保存到文件
    """
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps / frame_rate)
    frame_count = 0
    saved_frame_count = 0
    # 初始化消息历史
    messages = [
        {"role": "system", "content": translate_promot % (src_lang, dest_lang)}
    ]
    
    # 创建字幕文件对象
    subs = pysrt.SubRipFile()

    index = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 每隔一定帧数进行一次识别
        if frame_count % frame_interval == 0:
            # 转换为PIL图像
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            base64_frame = base64.b64encode(buffer).decode('utf-8')
            text = extract_text_from_frame(base64_image=base64_frame)
            if text:
                subtitle = json.loads(text.strip('```json').strip('```').strip())
                if subtitle['hasSubtitle'] == True:
                    subtitle_text = subtitle['subTitle']
                    translated_text = translate_text_with_chatgpt(subtitle_text, messages)
                    if translated_text:
                        print(str(index) + ": " + subtitle_text + " ---- " + translated_text)
                        # 创建字幕条目
                        start_time = pysrt.SubRipTime(0, 0, index)
                        end_time = pysrt.SubRipTime(0, 0, index + 1)
                        sub = pysrt.SubRipItem(index + 1, start=start_time, end=end_time, text=translated_text)
                        subs.append(sub)
                        index += 1
        frame_count += 1
        
    # 释放视频捕获对象
    cap.release()

    
    # 将翻译后的字幕保存到新的文件
    subs.save(output_file, encoding='utf-8')

    print(f"字幕已保存到 {output_file}")


# 替换为你的帧文件夹路径和输出字幕文件路径
video_path = './asserts/short_drama.mp4'
output_subtitle_file_path = './asserts/output_subtitle_file.srt'
model_path = "/data/models/Qwen2-VL-7B-Instruct/"
processor_path = "/data/models/Qwen2-VL-7B-Instruct/"
tool = Qwen2VLTool(model_path, processor_path, torch_dtype="auto", device_map="auto", attn_implementation="flash_attention_2")

extract_subtitles_from_video(video_path, output_subtitle_file_path)