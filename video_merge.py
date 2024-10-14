import os
from moviepy.editor import VideoFileClip, concatenate_videoclips

class VideoMerger:
    def __init__(self):
        self.clips = []

    def add_videos_from_directory(self, directory_path):
        """
        从目录中读取所有视频文件，并按文件名排序后添加到合并列表中。

        :param directory_path: 视频文件所在目录路径
        """
        video_files = sorted(
            [f for f in os.listdir(directory_path) if f.endswith(('.mp4', '.avi', '.mov', '.mkv','.ts'))]
        )
        for video_file in video_files:
            video_path = os.path.join(directory_path, video_file)
            self.add_video(video_path)

    def add_video(self, video_path):
        """
        添加视频片段到合并列表中。

        :param video_path: 视频片段文件路径
        """
        clip = VideoFileClip(video_path)
        self.clips.append(clip)

    def merge_videos(self, output_path):
        """
        将所有添加的视频片段合并成一个视频。

        :param output_path: 合成视频的输出路径
        """
        if not self.clips:
            print("没有视频片段可供合并")
            return

        final_clip = concatenate_videoclips(self.clips)
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=8)

    def clear_clips(self):
        """
        清空视频片段列表
        """
        self.clips = []

# 使用示例
if __name__ == "__main__":
    # 创建VideoMerger实例
    merger = VideoMerger()

    # 从目录中添加视频片段
    directory_path = "./KM6f7e979e6e37ae7f3cabc4472fac405c"
    merger.add_videos_from_directory(directory_path)

    # 合并视频片段并输出
    output_path = "./KM6f7e979e6e37ae7f3cabc4472fac405c/merged_video_2.mp4"
    merger.merge_videos(output_path)
