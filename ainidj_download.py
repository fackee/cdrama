import requests
import os

class AinidjDownloader:

    def __init__(self,base_url,target_path):
        self.base_url = base_url
        self.target_path = target_path
        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)
    
    def download(self):
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://ainidj.com',
            'Pragma': 'no-cache',
            'Referer': 'https://ainidj.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'm-debug': 'true',
            'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'swimlane': 'zhujianxin04-fyvre'
        }
        index = 0

        while True:
            sufix_name = f'/{index:06d}.ts'
            url = self.base_url + sufix_name
            file_name = f'{self.target_path}{sufix_name}'
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                print(f"Download stopped. HTTP status code: {response.status_code}")
                break

            with open(file_name, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded: {file_name}")

            index += 1


# 使用示例
if __name__ == "__main__":
    # https://shls.mcloud.139.com/hls/KM6f7e979e6e37ae7f3cabc4472fac405c/single/video/0/720/ts/000000.ts
    # downlaoder = AinidjDownloader(base_url="https://shls.mcloud.139.com/hls/KM6f7e979e6e37ae7f3cabc4472fac405c/single/video/0/720/ts",target_path="KM6f7e979e6e37ae7f3cabc4472fac405c")
    # downlaoder.download()