import os

# 配置文件
class Config:
    
    QWEN_CLOUD_BASE_URL = os.getenv('QW_B_U', 'https://dashscope.aliyuncs.com/compatible-mode/v1')


    
    API_URL = 'https://api.openai.com/v1/chat/completions'
    PROXIES = {
        "http://": "http://127.0.0.1:8118",
        "https://": "http://127.0.0.1:8118"
    }
    EXTRACT_SUBTITLE_PROMPT = '''
    该图片是影视剧的视频帧，识别出图片中的字幕。输出格式严格按照下面的json格式输出。
    <format>
    {'hasSubtitle': $HASSUBTITLE # true or false,'subTitle': $SUBTITLE}
    </format>
    注意，如果你遇到模棱两可的翻译选择，结合上下文选择你认为最合适的输出就可以，不要让我选择。
    '''
    TRANSLATE_PROMPT = '''
    你现在是一个专业的字幕翻译师, 你需要根据影视剧信息，将剧中的字幕由中文翻译成英文。 特别注意，你只需要输出翻译后的内容，不要输出与原文翻译无关的内容。
    '''
    API_URL_QWEN = "http://117.50.193.126/generate"
    

    def translate_prompt(movie_info):
        if movie_info:
            prompt = f'''
            {Config.TRANSLATE_PROMPT}
            <movie_info>
            {movie_info}
            </movie_info>
            '''
            return prompt
        return Config.TRANSLATE_PROMPT
