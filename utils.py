import base64
import json
import requests
from PIL import Image
import cv2
from openai import OpenAI
import httpx
from config import Config
import os
from bs4 import BeautifulSoup
import re


client = OpenAI(api_key=Config.API_KEY, http_client=httpx.Client(proxies=Config.PROXIES))

qw_cloud_client = OpenAI(api_key=Config.QWEN_CLOUD_API_KEY, base_url=Config.QWEN_CLOUD_BASE_URL)


def get_movie_info(subject_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(f'https://movie.douban.com/subject/{subject_id}/', headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('span', {'property': 'v:itemreviewed'}).text
        summary = soup.find('span', {'property': 'v:summary'}).text.strip()
        clean_summary = re.sub(r'\s+', ' ', summary).strip()
        return "标题：" + title + "\n" + clean_summary
    else:
        print(f"Failed to retrieve data from https://movie.douban.com/subject/{subject_id}/")
        return None


def truncate_array(arr, num_tail_items=99):
    if not arr:
        return []
    first_item = arr[:1]
    last_items = arr[-num_tail_items:]
    if len(arr) <= num_tail_items:
        return arr
    truncated_arr = first_item + last_items if first_item != last_items[:1] else last_items
    return truncated_arr
def translate_text_by_openai(text,messages):
    text = text.strip()
    text = text.replace('\n', ' ')
    messages.append({"role": "user", "content": text})
    completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=truncate_array(messages,30)
    )
    translation = completion.choices[0].message.content
    messages.append({"role": "assistant", "content": translation})
    return translation


def correct_subtitle_by_openai(movie_info,text):
    prompt = Config.correct_subtitle_prompt(movie_info,text)
    completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[ 
                {
                    "role": "user",
                    "content": prompt
                }
            ]
    )
    translation = completion.choices[0].message.content
    print(f"correct subtitle result: {translation}")
    return translation

def translate_text_by_openai_v2(movie_info,text):
    prompt = Config.new_translate_prompt(movie_info,text)
    completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[ 
                {
                    "role": "user",
                    "content": prompt
                }
            ]
    )
    translation = completion.choices[0].message.content
    print(f"translate v2 result: {translation}")
    return translation


def frame_to_base64(frame,compress_rate = 50):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), compress_rate]  # 90表示压缩质量
    result, encimg = cv2.imencode('.jpg', frame, encode_param)
    if not result:
        print("Error: Could not encode frame.")
        return None

    # 将JPEG数据转换为字节流
    jpeg_bytes = encimg.tobytes()

    # 将字节流转换为Base64编码
    base64_str = base64.b64encode(jpeg_bytes).decode('utf-8')
    return base64_str

# 28 * 28 = 1token
# 270 * 480 = 165 token
# 300token/frame
# 1min = 15000 token
# 1hour = 900000 token
# 1 drama = 1800000 token
# 0.000008y/token
# 1drama = 14.4
# QPM = 60
def extract_text_from_frame_by_qwen_cloud(base64_image):
    message = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": Config.EXTRACT_SUBTITLE_PROMPT},
                {"type": "image", "image": f'data:image;base64,{base64_image}'}
            ]
        }
    ]
    completion = qw_cloud_client.chat.completions.create(
    model="qwen-vl-plus", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=message
    )
    return json.loads(completion.choices[0].message.content.strip('```json').strip('```').strip())


def extract_text_from_frame_by_qwen(base64_frame):
    message = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": Config.EXTRACT_SUBTITLE_PROMPT},
                {"type": "image", "image": f'data:image;base64,{base64_frame}'}
            ]
        }
    ]
    request_body = {"messages": message}
    headers = {
        "Content-Type": "application/json",
        "x-api-key": Config.API_KEY_QWEN
    }
    response = requests.post(Config.API_URL_QWEN, headers=headers, data=json.dumps(request_body))
    if response.status_code == 200:
        outputs = response.json()
        return outputs["output"][0]
    else:
        print("Error:", response.status_code, response.text)
        return ""

def list_video_files(directory, extensions=['.mp4', '.avi', '.mkv', '.mov', '.flv']):
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                video_files.append(os.path.join(root, file))
    return video_files