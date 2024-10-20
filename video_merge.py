import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import re

class VideoMerger:
    def __init__(self,directory,title):
        self.clips = []
        self.title = title
        self.directory = directory

    # 定义一个函数来提取文件名中的数字
    def extract_number(self,file_path):
        base_name = os.path.basename(file_path)
        match = re.search(r'(\d+)', base_name)
        if match:
            return int(match.group(1))
        return 0  # 如果没有找到数字，默认返回0

    def add_videos_from_directory(self,extensions=['.mp4', '.avi', '.mkv', '.mov', '.flv']):
        """
        从目录中读取所有视频文件，并按文件名排序后添加到合并列表中。

        :param directory_path: 视频文件所在目录路径
        """
        video_files = []
        for root, _, files in os.walk(self.directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    video_path = os.path.join(root, file)
                    _, file_name = os.path.split(video_path)
                    base_name, _ = os.path.splitext(file_name)
                    if not base_name.endswith('_st'):
                        continue
                    video_files.append(os.path.join(root, file))
        video_files.sort(key=self.extract_number)
        for video_path in video_files:
            self.add_video(video_path)

    def add_video(self, video_path):
        """
        添加视频片段到合并列表中。

        :param video_path: 视频片段文件路径
        """
        clip = VideoFileClip(video_path)
        self.clips.append(clip)


    def split_array_equally(self,arr, n):
        # 计算每个子数组的基本长度和需要额外添加一个元素的子数组数量
        base_size = len(arr) // n
        extra = len(arr) % n
        
        # 初始化结果列表
        result = []
        
        # 当前处理的位置索引
        start_index = 0
        
        for i in range(n):
            # 计算当前子数组的结束位置
            if i < extra:
                end_index = start_index + base_size + 1
            else:
                end_index = start_index + base_size
            
            # 添加子数组到结果列表
            result.append(arr[start_index:end_index])
            
            # 更新开始索引为下一个子数组的起始位置
            start_index = end_index
        
        return result

    def merge_videos(self,merge_count = 5):
        """
        将所有添加的视频片段合并成一个视频。

        :param output_path: 合成视频的输出路径
        """
        if not self.clips:
            print("没有视频片段可供合并")
            return
        
        split_clips = self.split_array_equally(self.clips,merge_count)
        index = 0
        for clips in split_clips:
            output_path = f'{directory_path}/{self.title}_{index}.mp4'
            index += 1
            final_clip = concatenate_videoclips(clips)
            final_clip.write_videofile(
                output_path, 
                codec='h264_nvenc',  # 使用 NVIDIA 的 H.264 编码器
                preset='fast',       # 设置编码速度/质量平衡
                ffmpeg_params=[
                    '-b:v', '5M'                 # 设置比特率
                ]
            )

    def clear_clips(self):
        """
        清空视频片段列表
        """
        self.clips = []

# 使用示例
if __name__ == "__main__":

    # 从目录中添加视频片段
    directory_path = "../../BaiduNetdiskDownload/woman_king"
        # 创建VideoMerger实例
    merger = VideoMerger(directory=directory_path,title='woman_king')
    merger.add_videos_from_directory()
    merger.merge_videos(merge_count=5)
