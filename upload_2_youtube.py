import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import  MediaFileUpload
import re
import time

# 设置API密钥
API_KEY = 'AIzaSyB1w98bgA6LWS-UJ_eKRXBkz2ogT6OTlO0'
proxy_url = 'http://127.0.0.1:7078'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube',
          'https://www.googleapis.com/auth/youtube.channel-memberships.creator',
          'https://www.googleapis.com/auth/youtube.force-ssl',
          'https://www.googleapis.com/auth/youtube.readonly',
          'https://www.googleapis.com/auth/youtubepartner']
# 设置全局代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7078'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7078'
def get_credentials():
    """获取或刷新API凭据"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# 创建YouTube API客户端
def build_youtube_client():
    """构建YouTube客户端，支持代理"""
    # http = httplib2.Http(proxy_info=httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, '127.0.0.1',7078))
    creds = get_credentials()
    return build('youtube', 'v3', credentials=creds)

# 上传视频
def upload_video(youtube, video_file, description, tags, category_id, privacy_status):
    title = description + "-" + os.path.splitext(os.path.basename(video_file))[0]
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
        notifySubscribers = True,
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


def add_video_to_playlist(youtube, playlist_id, video_id):
    """将视频添加到播放列表"""
    request_body = {
        'snippet': {
            'playlistId': playlist_id,
            'resourceId': {
                'kind': 'youtube#video',
                'videoId': video_id
            }
        }
    }

    response = youtube.playlistItems().insert(
        part='snippet',
        body=request_body
    ).execute()

    return response

# 主函数
def upload_single_video(youtube,playlist_id,video_file,description,
                 tags = ['cdrama', 'chinese drama','short drama','idol drama'],
                 category_id = '24',privacy_status = 'public',language='en',caption_name='English Subtitles'):

    file_dir, file_name = os.path.split(video_file)
    base_name, _ = os.path.splitext(file_name)
    caption_file = os.path.join(file_dir, base_name + '_subtitle.srt')
    

    # 上传视频
    video_id = upload_video(youtube, video_file, description, tags, category_id, privacy_status)
    print(f'Video uploaded with ID: {video_id}')

    # 上传字幕
    caption_response = upload_caption(youtube, video_id, caption_file, language, caption_name)
    print(f'Caption uploaded: {caption_response}')
    # 将视频添加到播放列表

    add_video_to_playlist(youtube, playlist_id, video_id)
    print(f'Video added to playlist with ID: {playlist_id}')


# 定义一个函数来提取文件名中的数字
def extract_number(file_path):
    base_name = os.path.basename(file_path)
    match = re.search(r'(\d+)', base_name)
    if match:
        return int(match.group(1))
    return 0  # 如果没有找到数字，默认返回0

def upload_dir_videos(youtube,directory,playlist_id,description,video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.flv']):
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(root, file))
    video_files.sort(key=extract_number)
    for video_path in video_files:
        upload_single_video(youtube=youtube,playlist_id=playlist_id,video_file=video_path,description=description)
        print(f'uploaded video: {video_path}')
        time.sleep(5)



if __name__ == '__main__':
    youtube = build_youtube_client()
    description = "Only After Death Did I Realize I Was the Beloved of the Capital's Crown Prince"
    playlist_id = 'PLlnAQCbIdpjwmukGLPnB9qyd7rqRyO2Rc'
    upload_dir_videos(youtube=youtube,directory='../../BaiduNetdiskDownload/demo',playlist_id=playlist_id,description=description)
