import json
import time
import ffmpeg
import os
from oss import OssUploader
from http import HTTPStatus
import dashscope


dashscope.api_key = 'sk-01541446af8a40c6833153cab7f06a2c'
api_key = "sk-01541446af8a40c6833153cab7f06a2c"  # 在此处替换为您的API密钥
language_hints = ["zh"]
uploader = OssUploader()
# 设置全局代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7078'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7078'

def extract_voice(video_path):
    # 使用 FFmpeg 提取音频
    file_dir, file_name = os.path.split(video_path)
    base_name, _ = os.path.splitext(file_name)
    output_path = os.path.join(file_dir, base_name + '.mp3')
    ffmpeg.input(video_path).output(output_path, format='mp3').run(overwrite_output=True)
    remote_file_name = f"{time.time()}_{base_name}.mp3"
    file_url = uploader.upload_file(output_path, remote_file_name)
    # 删除临时文件
    #os.remove(output_path)
    return file_url

# 提交文件转写任务，包含待转写文件url列表
def detect_subtitle_by_voice(file_url) -> str:

    # For prerequisites running the following sample, visit https://help.aliyun.com/document_detail/611472.html
    task_response = dashscope.audio.asr.Transcription.async_call(
        model='paraformer-v2',
        file_urls=[file_url],
        language_hints=['zh', 'en']  # “language_hints”只支持paraformer-v2和paraformer-realtime-v2模型
    )

    transcribe_response = dashscope.audio.asr.Transcription.wait(task=task_response.output.task_id)
    if transcribe_response.status_code == HTTPStatus.OK:
        print(json.dumps(transcribe_response.output, indent=4, ensure_ascii=False))
        print('transcription done!')


# file_url = extract_voice('../../BaiduNetdiskDownload/woman_king/1.mp4')
detect_subtitle_by_voice('https://cdrama-intelli.oss-cn-chengdu.aliyuncs.com/1729419778.246095_1.mp3')