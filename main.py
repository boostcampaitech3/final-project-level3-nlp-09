import streamlit as st
from streamlit_chat import message

from model.inference import load_model, run_mrc

model, tokenizer = load_model()


st.title("Streamlit MRC")
if "input" not in st.session_state:
    st.session_state["input"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []


with st.form(key="my_form", clear_on_submit=True):
    col1, col2 = st.columns([8, 1])

    with col1:
        st.text_input(
            "Ask me anything!",
            placeholder="도널드 트럼프는 어느 나라의 대통령인가?",
            key="input",
        )
    with col2:
        st.write("&#9660;&#9660;&#9660;")
        submit = st.form_submit_button(label="Ask")

if submit:
    msg = (st.session_state["input"], True)
    st.session_state.messages.append(msg)
    for msg in st.session_state.messages:
        message(msg[0], is_user=msg[1])
    with st.spinner("두뇌 풀가동!"):
        result = run_mrc(None, None, None, None, tokenizer, model, msg[0])

    msg = (result, False)
    st.session_state.messages.append(msg)
    message(msg[0], is_user=msg[1])
