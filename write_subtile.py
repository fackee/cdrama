import moviepy.editor as mp
import ffmpeg

def add_subtitles(video_path, subtitle_path, output_path):
    # 加载视频文件
    video = mp.VideoFileClip(video_path)
    
    # 创建一个临时无字幕的视频文件
    temp_video_path = "temp_video.mp4"
    video.write_videofile(temp_video_path, codec="libx264")
    
    # 使用ffmpeg将SRT字幕嵌入到视频中
    (
        ffmpeg
        .input(temp_video_path)
        .output(output_path, vf="subtitles=" + subtitle_path)
        .run(overwrite_output=True)
    )
    
    # 删除临时视频文件
    import os
    os.remove(temp_video_path)

# 示例使用
video_path = "./asserts/short_drama.mp4"
subtitle_path = "./asserts/subtitle.srt"
output_path = "./asserts/video_with_subtitles.mp4"

add_subtitles(video_path, subtitle_path, output_path)
