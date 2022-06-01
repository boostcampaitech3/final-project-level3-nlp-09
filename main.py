import streamlit as st
from streamlit_chat import message
import streamlit_modal as modal

import streamlit.components.v1 as components

from model.inference import load_model, run_mrc

model, tokenizer = load_model()


st.title("뭐든 내게 물어봐!(MNM)")
st.image("https://t1.daumcdn.net/cfile/tistory/99D595365C348A850A")

if "input" not in st.session_state:
    st.session_state["input"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "is_fixxed" not in st.session_state:
    st.session_state["is_fixxed"] = False

# 회의록 입력
with st.sidebar:
    st.title('회의록을 입력해주세요!')
    st.session_state['uploaded_files'] = st.file_uploader('정해진 형식의 회의록을 올려주세요!(json)',accept_multiple_files=True)
    minutes_list =[files.name.split(".")[0] for files in st.session_state['uploaded_files']]
    options = list(range(len(minutes_list)))
    print(options, st.session_state['uploaded_files'])
    selected_minutes = st.selectbox(f'회의록 목록(개수: {len(minutes_list)}): ', options, 
                                    format_func = lambda x: minutes_list[x])
    print(selected_minutes)
    submit_minute = st.button(label="회의록 보기", disabled=(False if st.session_state['uploaded_files'] else True)) 
    if submit_minute:
        st.text_area(minutes_list[selected_minutes], st.json(st.session_state['uploaded_files'][selected_minutes]))

# 입력 


def press_requery():
    st.session_state["is_fixxed"] = False if st.session_state["is_fixxed"] else True
    print("고정됨" if st.session_state["is_fixxed"] else "풀림")


for i,msg in enumerate(st.session_state.messages):
    message(msg[0], is_user=msg[1], key = i)

if st.session_state.messages:
    col = st.columns([1,1,2,3])
    with col[0]:
        st.button(label="회의록 볼래?", on_click=modal.open)
    with col[1]:
        st.button(label="다른 답 볼래?", on_click=modal.open)
    with col[2]:
        if not st.session_state["is_fixxed"]:
            st.button(label="이번 회의록에서 다시 질문해볼래?", on_click=press_requery)
        else:
            st.button(label="지정한 회의록을 해제해볼래?", on_click=press_requery)



with st.form(key="my_form", clear_on_submit=True):
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
        submit = st.form_submit_button(label="Ask")

# 제출 시 모델 사용
if submit:
    msg = (st.session_state["input"], True)
    st.session_state.messages.append(msg)
    with st.spinner("두뇌 풀가동!"):
        result = run_mrc(None, None, None, None, tokenizer, model, msg[0])
    msg = (result, False)
    st.session_state.messages.append(msg)

if modal.is_open():
    with modal.container():
        st.write(
            '''
            [출결 주의사항]
            1. QR코드 파일은 어떠한 형태로든 절대 다운받아서 소지/사용하지 말고 “게시된 QR코드"를 앱으로 ‘스캔'하여 [체크인], [체크아웃]을 각각 진행해주세요. (KDT 가이드에 따름)
            2. 매일 체크인(10:00까지)과 체크아웃(19:00부터) 하루에 2번, QR 코드를 스캔해주세요. 스캔을 할 때에는 반드시 본인이 등록된 KDT 교육 회차에 맞는 QR 코드를 스캔해야 합니다~
            3. QR 출결을 하여도 변함없이 [부스트코스 학습시작, 학습종료]를 같이 눌러주셔야 합니다.
            4. 공결처리는 최소 3일전에 boostcamp_ai@connect.or.kr로 미리 운영진에게 말씀을 주시고, 갑자기 일이 생겨 조퇴나 결석이 필요할 경우 꼭 그 당일에 메일을 주셔야합니다. 그 이후에는 처리가 어렵습니다. 공결을 위한 문서는 +1일까지 보내주셔도 됩니다.
            '''
        )
        