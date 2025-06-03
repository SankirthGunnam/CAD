import gradio as gr


def greet(name, intensity):
    # return "Hello, " + name + "!" * int(intensity)
    return "Hello, I don't care about the intensity, ha ha ha !!!"


demo = gr.Interface(
    fn=greet,
    inputs=["text", "slider"],
    outputs=["text"],
)

demo.launch()
