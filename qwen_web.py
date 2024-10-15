from flask import Flask, request, jsonify
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# 初始化Flask应用
app = Flask(__name__)

# 设定API密钥
API_KEY = "Zjx7532554!"

# 初始化Qwen2VL工具类
class Qwen2VLTool:
    def __init__(self, model_path, processor_path, torch_dtype="auto", device_map="auto", attn_implementation=None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # 加载模型
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_path, 
            torch_dtype=torch_dtype, 
            device_map=device_map,
            attn_implementation=attn_implementation
        )
        
        # 加载处理器
        self.processor = AutoProcessor.from_pretrained(processor_path)
    
    def process_messages(self, messages):
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        return inputs.to(self.device)
    
    def generate_output(self, inputs, max_new_tokens=128):
        generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        print("qwen response: " + str(output_text))
        return output_text

# 初始化模型和处理器
model_path = "/path/to/your/local/model"
processor_path = "/path/to/your/local/processor"
qwen_tool = Qwen2VLTool(model_path, processor_path)

# 鉴权装饰器
def require_api_key(func):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if api_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

# 定义HTTP接口
@app.route('/generate', methods=['POST'])
@require_api_key
def generate():
    data = request.json
    if not data or 'messages' not in data:
        return jsonify({"error": "Invalid input"}), 400
    
    messages = data['messages']
    try:
        inputs = qwen_tool.process_messages(messages)
        output = qwen_tool.generate_output(inputs)
        return jsonify({"output": output})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 运行Flask应用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
