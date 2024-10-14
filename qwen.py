import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

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
        print("qwen reponse: " + str(output_text))
        return output_text
