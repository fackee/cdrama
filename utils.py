import base64
import json
import requests
from PIL import Image
import io
import cv2
from openai import OpenAI
import httpx
from config import Config
import os
from bs4 import BeautifulSoup
import re

client = OpenAI(api_key=Config.API_KEY, http_client=httpx.Client(proxies=Config.PROXIES))


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

def translate_text_by_openai(text, messages):
    messages.append({"role": "user", "content": text})
    truncate_message = truncate_array(messages)
    completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=truncate_message
    )
    translation = completion.choices[0].message.content
    messages.append({"role": "assistant", "content": translation})
    return translation

def frame_to_base64(frame):
    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    buffered = io.BytesIO()
    pil_image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def extract_text_from_frame_by_qwen(base64_image):
    message = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": Config.EXTRACT_SUBTITLE_PROMPT},
                {"type": "image", "image": f'data:image;base64,{base64_image}'}
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
