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
    该图片是影视剧的视频帧，识别出图片底部的字幕,特别注意，只需要识别底部的字幕，画面中其他部分出现的文字不需要。输出格式严格按照下面的json格式输出
    <format>
    {'hasSubtitle': $HASSUBTITLE # true or false,'subTitle': $SUBTITLE}
    </format>
    注意，如果你遇到模棱两可的翻译选择，结合上下文选择你认为最合适的输出就可以，不要让我选择。
    '''
    EN_TRANSLATE_PROMPT = '''
    You are a highly skilled translator with expertise in many languages. 
    Your task is to translate movie subtitle from Chinese to English base on gave movie summary.
    Translate must be preserving the meaning, tone, and nuance of the original text. Please maintain proper grammar, spelling, and punctuation in the translated version.
    Note that, You're just need output the translated text. If input is empty, just output blank character. If input contains Chinese name, just translate as Chinese Pinyin.
    '''
    # TRANSLATE_PROMPT = '''
    # 你现在是一个专业的字幕翻译师, 你需要根据影视剧信息，将剧中的字幕由中文翻译成英文。 特别注意，你只需要输出翻译后的内容，不要输出与原文翻译无关的内容，如果输入不包含中文导致无法含义，直接输出空白就可以。
    # '''
 

    def translate_prompt(movie_info):
        if movie_info:
            prompt = f'''
            {Config.EN_TRANSLATE_PROMPT}
            <movie_summary>
            {movie_info}
            </movie_summary>
            '''
            return prompt
        return Config.EN_TRANSLATE_PROMPT
