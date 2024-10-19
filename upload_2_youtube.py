import os
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import requests

# 设置API密钥
API_KEY = 'YOUR_API_KEY'

# 创建YouTube API客户端
def get_youtube_client(api_key):
    return build('youtube', 'v3', developerKey=api_key)

# 上传视频
def upload_video(youtube, video_file, title, description, tags, category_id, privacy_status):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    response = request.execute()
    return response['id']

# 上传字幕
def upload_caption(youtube, video_id, caption_file, language, caption_name):
    body = {
        'snippet': {
            'videoId': video_id,
            'language': language,
            'name': caption_name,
            'isDraft': False
        }
    }

    media = MediaFileUpload(caption_file, mimetype='application/octet-stream', chunksize=-1, resumable=True)

    request = youtube.captions().insert(
        part='snippet',
        body=body,
        media_body=media
    )

    response = request.execute()
    return response

# 主函数
def main():
    youtube = get_youtube_client(API_KEY)

    video_file = 'path_to_your_video.mp4'
    caption_file = 'path_to_your_caption.srt'
    title = 'Your Video Title'
    description = 'Your Video Description'
    tags = ['tag1', 'tag2']
    category_id = '22'  # 22 corresponds to 'People & Blogs'
    privacy_status = 'public'
    language = 'en'
    caption_name = 'English Subtitles'

    # 上传视频
    video_id = upload_video(youtube, video_file, title, description, tags, category_id, privacy_status)
    print(f'Video uploaded with ID: {video_id}')

    # 上传字幕
    caption_response = upload_caption(youtube, video_id, caption_file, language, caption_name)
    print(f'Caption uploaded: {caption_response}')

if __name__ == '__main__':
    main()
