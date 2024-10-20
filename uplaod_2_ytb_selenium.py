from youtube_uploader_selenium import YouTubeUploader
import json
import os
import time
import re

os.environ['PATH'] += os.pathsep + r'D:\geckodriver'

def upload_single_video(description,playlist_title,video_path,
                 tags = ['cdrama', 'chinese drama','short drama','idol drama'],
                 category_id = '24',privacy_status = 'public',language='en',caption_name='English Subtitles'):
    
    file_dir, file_name = os.path.split(video_path)
    base_name, _ = os.path.splitext(file_name)
    if not base_name.endswith('_st'):
        return
    meta_json_file = os.path.join(file_dir, base_name + '_meta.json')
    with open(meta_json_file, 'w',encoding='utf-8') as file:
        meta_json = {
            'title': f'{description}_{base_name}',
            'description': description,
            'tags': tags,
            'category': category_id,
            'privacyStatus': privacy_status
        }
        json.dump(meta_json, file, ensure_ascii=False, indent=4)

    uploader = YouTubeUploader(video_path, meta_json_file,profile_path=r'C:\Users\75325\AppData\Roaming\Mozilla\Firefox\Profiles\y9jhi7n8.default-release')
    was_video_uploaded, video_id = uploader.upload()
    print(was_video_uploaded, video_id)


# 定义一个函数来提取文件名中的数字
def extract_number(file_path):
    base_name = os.path.basename(file_path)
    match = re.search(r'(\d+)', base_name)
    if match:
        return int(match.group(1))
    return 0  # 如果没有找到数字，默认返回0

def add_each_subtitle(directory,descrption,playlist_title, extensions=['.mp4', '.avi', '.mkv', '.mov', '.flv']):
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                video_files.append(os.path.join(root, file))
    video_files.sort(key=extract_number)
    for video_path in video_files:
        upload_single_video(description=descrption,playlist_title=playlist_title,video_path=video_path)
        time.sleep(10)



if __name__ == '__main__': 
    video_path = '../../BaiduNetdiskDownload/demo'
    descrption = "Only After Death Did I Realize I Was the Beloved of the Capital's Crown Prince"
    playlist_title = "Only After Death Did I Realize I Was the Beloved of the Capital's Crown Prince"
    add_each_subtitle(directory=video_path,descrption=descrption,playlist_title=playlist_title)