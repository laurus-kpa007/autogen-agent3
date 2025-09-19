import gradio as gr
import time

def answer_with_steps(message, history):
    # 각 단계별 답변 생성과정을 순차적으로 추가
    steps = [
        "🔍 질의 해석 중...",
        "🕵️‍♂️ 관련 정보 검색 중...",
        "✍️ 답변 요약 작성 중..."
    ]
    history = []
    for step in steps:
        history.append(("assistant", step))
        yield history, gr.update(visible=False), ""  # 최종 답변 탭은 숨김

    final = "이것이 최종 답변입니다."
    history.append(("assistant", final))
    # 답변완료 시 '최종답변' 탭 활성화
    yield history, gr.update(visible=True), final

with gr.Blocks() as demo:
    with gr.Tabs() as tabs:
        with gr.TabItem("답변 생성 단계"):
            chatbot = gr.Chatbot()
            input_text = gr.Textbox(label="질문을 입력하세요")
            send = gr.Button("질문 보내기")
        with gr.TabItem("최종 답변", visible=False) as answer_tab:
            final_box = gr.Textbox(label="최종 답변", interactive=False)
            
    state = gr.State()
    # 질문 전송 시 단계별 진행상황 스트리밍 → 최종 답변 생성 → 탭 자동 전환
    send.click(
        answer_with_steps,
        inputs=[input_text, state],
        outputs=[chatbot, answer_tab, final_box],
        queue=True
    )

demo.launch()
