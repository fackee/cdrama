import boto3
from botocore.exceptions import NoCredentialsError, ClientError

class S3Uploader:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name):
        """
        初始化S3客户端
        :param aws_access_key_id: AWS访问密钥ID
        :param aws_secret_access_key: AWS秘密访问密钥
        :param region_name: AWS区域名称
        """
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )

    def upload_file(self, file_name, bucket, object_name=None):
        """
        上传文件到S3
        :param file_name: 要上传的文件路径
        :param bucket: S3 bucket 名称
        :param object_name: S3中的对象名称。如果未指定，则使用file_name
        :return: True 如果文件上传成功，否则False
        """
        if object_name is None:
            object_name = file_name

        try:
            self.s3_client.upload_file(file_name, bucket, object_name)
            print(f"文件 {file_name} 成功上传到 {bucket}/{object_name}")
            return True
        except FileNotFoundError:
            print(f"文件 {file_name} 未找到")
            return False
        except NoCredentialsError:
            print("AWS 凭证未找到")
            return False
        except ClientError as e:
            print(f"上传失败: {e}")
            return False

    def list_files(self, bucket):
        """
        列出指定Bucket中的文件
        :param bucket: S3 bucket 名称
        :return: 文件列表
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket)
            if 'Contents' in response:
                files = [file['Key'] for file in response['Contents']]
                return files
            else:
                return []
        except ClientError as e:
            print(f"列出文件失败: {e}")
            return []

    def delete_file(self, bucket, object_name):
        """
        删除S3中指定文件
        :param bucket: S3 bucket 名称
        :param object_name: 要删除的文件名称
        :return: True 如果文件删除成功，否则False
        """
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=object_name)
            print(f"文件 {object_name} 成功从 {bucket} 删除")
            return True
        except ClientError as e:
            print(f"删除文件失败: {e}")
            return False

# 使用示例
if __name__ == "__main__":
    aws_access_key_id = 'YOUR_ACCESS_KEY_ID'
    aws_secret_access_key = 'YOUR_SECRET_ACCESS_KEY'
    region_name = 'YOUR_REGION'

    s3_uploader = S3Uploader(aws_access_key_id, aws_secret_access_key, region_name)

    file_name = "path/to/your/file.txt"
    bucket = "your-s3-bucket-name"
    object_name = "your/object/name.txt"

    # 上传文件
    s3_uploader.upload_file(file_name, bucket, object_name)

    # 列出文件
    files = s3_uploader.list_files(bucket)
    print("Bucket中的文件:", files)

    # 删除文件
    s3_uploader.delete_file(bucket, object_name)
