import streamlit as st
from streamlit_chat import message
import streamlit_modal as modal

import streamlit.components.v1 as components

from model.inference import load_model, run_mrc, run_reader, run_retriever_reader

model, tokenizer = load_model()
sample_txt = '''
다음은 의사일정 제3항 본회의 휴회의 건을 상정합니다. 상임의원회 의정활동을 위하여 8월 27일부터 9월 3일까지 8일간 본회를 휴회 하고자 합니다. 의원여러분 이의 있으십니까? (『없습니다』하는 의원 있음) 이의가 없으므로 가결되었음을 선포합니다. 이상으로 제207회 완주군의회 임시회 제1차 본회의를 마치겠습니다. 다음 제2차 본회의는 9월 4일 오전 10시에 개의하겠습니다. 의원여러분 수고 많으셨습니다. 산회를 선포합니다.
'''

st.title("뭐든 내게 물어봐!(MNM)")

if "input" not in st.session_state:
    st.session_state["input"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "is_fixxed" not in st.session_state:
    st.session_state["is_fixxed"] = False
if "result_text_and_ids" not in st.session_state:
    st.session_state["result_text_and_ids"] = None
if "result_context" not in st.session_state:
    st.session_state["result_context"] = ""
if "is_submitted" not in st.session_state:
    st.session_state["is_submitted"] = False
else: 
    st.session_state["is_submitted"] = True
def press_requery():
    st.session_state["is_fixxed"] = False if st.session_state["is_fixxed"] else True

# 회의록 입력
with st.sidebar:
    st.title('회의록을 입력해주세요!')
    st.session_state['uploaded_files'] = st.file_uploader('정해진 형식의 회의록을 올려주세요!(json)',accept_multiple_files=True)
    minutes_list =[files.name.split(".")[0] for files in st.session_state['uploaded_files']]
    options = list(range(len(minutes_list)))
    selected_minutes = st.selectbox(f'회의록 목록(개수: {len(minutes_list)}): ', options, 
                                    format_func = lambda x: minutes_list[x])
    submit_minute = st.button(label="회의록 보기", disabled=(False if st.session_state['uploaded_files'] else True)) 
    if submit_minute:
        st.text_area(minutes_list[selected_minutes], st.json(st.session_state['uploaded_files'][selected_minutes]))

# 제출 시 모델 사용
if st.session_state["is_submitted"] and st.session_state["input"] != "":
    msg = (st.session_state["input"], True)
    st.session_state.messages.append(msg)
    with st.spinner("두뇌 풀가동!"):
        if st.session_state["is_fixxed"]:
            best_answer = run_reader(None, None, None, None, tokenizer, model, st.session_state.result_context["내용"],
            st.session_state.result_context["회의 제목"], msg[0])[0]['text']
            st.session_state.result_text_and_ids = [{"찾은 답" : best_answer, "포함되어 있던 회의록": st.session_state.result_context["회의 제목"]}] 
        else:
            result = run_retriever_reader(None, None, None, None, tokenizer, model, msg[0])
            result.sort(key=lambda x: x[0]["start_logit"] + x[0]["end_logit"], reverse=True)
            st.session_state.result_text_and_ids = [{"찾은 답" : res[0]["text"], "포함되어 있던 회의록": res[2]} for res in result]
            st.session_state.result_context = {"회의 제목": result[0][2], "내용": result[0][1]}
            best_answer = st.session_state.result_text_and_ids[0]["찾은 답"]
    msg = (str(best_answer), False)
    st.session_state.messages.append(msg)

for i,msg in enumerate(st.session_state.messages):
    message(msg[0], is_user=msg[1], key = i)

if st.session_state["is_submitted"]:
    col = st.columns([1,1,2,3])
    with col[0]:
        open_minute_modal = st.button(label="회의록 볼래?", on_click=modal.open)
    with col[1]:
        open_other_ans_modal = st.button(label="다른 답 볼래?", on_click=modal.open)
    with col[2]:
        if not st.session_state["is_fixxed"]:
            st.button(label="이번 회의록에서 다시 질문해볼래?", on_click=press_requery)
        else:
            st.button(label="지정한 회의록을 해제해볼래?", on_click=press_requery)

if st.session_state.is_fixxed:
    print(st.session_state['result_text_and_ids'])
    st.write(f"회의록이 {st.session_state['result_text_and_ids'][0]['포함되어 있던 회의록']}으로 고정되어 있어!")

with st.form(key="input_form", clear_on_submit=True):
    col1, col2 = st.columns([8, 1])
    with col1:
        if len(st.session_state['uploaded_files']) != 0:
            st.text_input(
                "궁금한 건 뭐든지 물어봐 (물론 회의록 내에서)",
                placeholder="2015년 2차 본회의는 언제야?",
                key="input", disabled=False,
            )
        else: 
            st.text_input(
                "궁금한 건 뭐든지 물어봐 (물론 회의록 내에서)",
                placeholder="회의록을 먼저 올려주세요!!!",
                key="input", disabled=False
            )
    with col2:
        st.write("&#9660;&#9660;&#9660;")
        st.session_state.is_submitted = st.form_submit_button(label="Ask")

if modal.is_open() and open_other_ans_modal:
    with modal.container():
        st.write(
            st.session_state.result_text_and_ids
        )

if modal.is_open() and open_minute_modal:
    with modal.container():
        st.write(
            st.session_state.result_context
        )
