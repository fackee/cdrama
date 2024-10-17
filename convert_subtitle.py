import re

def srt_to_vtt(srt_path, vtt_path):
    with open(srt_path, 'r', encoding='utf-8') as srt_file:
        srt_content = srt_file.read()

    # 替换时间格式
    vtt_content = re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})', r'\1.\2', srt_content)

    # 添加 WebVTT 文件头
    vtt_content = 'WEBVTT\n\n' + vtt_content

    # 写入 WebVTT 文件
    with open(vtt_path, 'w', encoding='utf-8') as vtt_file:
        vtt_file.write(vtt_content)

# 示例使用
srt_path = '/Users/zhujianxin04/mini_drama/wk/1_subtitle.srt'
vtt_path = '/Users/zhujianxin04/mini_drama/wk/1_subtitle.vtt'
srt_to_vtt(srt_path, vtt_path)
print(f'转换完成: {vtt_path}')
