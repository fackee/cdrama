import requests
from bs4 import BeautifulSoup
import re

def get_movie_info(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('span', {'property': 'v:itemreviewed'}).text
        summary = soup.find('span', {'property': 'v:summary'}).text.strip()
        clean_summary = re.sub(r'\s+', ' ', summary).strip()
        return "标题：" + title + "\n" + clean_summary
    else:
        print(f"Failed to retrieve data from {url}")
        return None

# 示例使用
movie_url = 'https://movie.douban.com/subject/37039038/'  # 替换为你想获取信息的电影URL
movie_info = get_movie_info(movie_url)
if movie_info:
    print(movie_info)
