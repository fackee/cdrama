import gradio as gr

# 定义一个简单的函数，返回包含iframe的HTML字符串
def show_iframe(url):
    iframe_html = f'<iframe src="https://www.kdocs.cn/l/cb9e87wfmFUV?R=L1MvMQ%3D%3D" width="100%" height="500px"></iframe>'
    return iframe_html

# 创建Gradio接口
iface = gr.Interface(
    fn=show_iframe, 
    inputs=gr.inputs.Textbox(label="Enter URL"), 
    outputs=gr.outputs.HTML(label="Iframe Output")
)

# 启动Gradio应用
iface.launch()