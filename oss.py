import oss2
import os
from config import Config

class OssUploader:
    def __init__(self):
        """
        初始化 OSS 客户端

        :param access_key_id: 阿里云 Access Key ID
        :param access_key_secret: 阿里云 Access Key Secret
        :param bucket_name: OSS Bucket 名称
        :param endpoint: OSS 的 endpoint
        """
        self.access_key_id = Config.access_key_id
        self.access_key_secret = Config.access_key_secret
        self.bucket_name = Config.bucket_name
        self.endpoint = Config.endpoint
        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)

    def upload_file(self, local_file_path, remote_file_name):
        """
        上传文件到 OSS

        :param local_file_path: 本地文件路径
        :param remote_file_name: 上传到 OSS 后的文件名
        :return: 文件的访问链接
        """
        try:
            # 上传文件
            result = self.bucket.put_object_from_file(remote_file_name, local_file_path)
            
            if result.status == 200:
                print(f"文件 {local_file_path} 已成功上传到 OSS")
                # 获取文件的访问链接
                file_url = f"https://{self.bucket_name}.{Config.endpoint_suffix}/{remote_file_name}"
                return file_url
            else:
                print(f"上传失败，状态码: {result.status}")
                return None
        except oss2.exceptions.OssError as e:
            print(f"OSS 错误: {e}")
            return None