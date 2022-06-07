import json
import time
from collections import defaultdict
import streamlit as st
from streamlit_chat import message
import streamlit_modal as modal
import traitlets
import streamlit.components.v1 as components

from model.elastic_setting import *
from model.inference import load_model, run_mrc, run_reader

model, tokenizer = load_model()

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
if "doc_files" not in st.session_state:
    st.session_state["doc_files"] = []
if "is_deleting" not in st.session_state:
    st.session_state["is_deleting"] = False
if "is_changed" not in st.session_state:
    st.session_state["is_changed"] = False

def uploader_callback():
    print('Uploaded file')

def press_requery():
    st.session_state["is_fixxed"] = False if st.session_state["is_fixxed"] else True
    
def delete_file(user_index, title):
    if st.session_state["is_deleting"]:
        # 회의록 삭제
        print("회의록 삭제중")
        deleted_doc = delete_doc(es, user_index, doc_id=str(title))
        print("삭제한 회의록: {}".format(title))
        st.session_state["doc_files"].remove(title)
        print("삭제 후: ", st.session_state["doc_files"])
        st.session_state["is_deleting"] = False

def is_changed():
    st.session_state["is_changed"] = True if st.session_state["is_deleting"] else False


# 사이드바 설정
with st.sidebar:
    # 사용자 설정
    st.title('프로젝트 ID를 입력해주세요!')
    user = st.text_input("프로젝트 ID", placeholder="프로젝트 ID", key="user", disabled=False)

    if user != "":
        user_index = user
    else:
        st.warning("프로젝트 ID를 입력해주세요!")
        st.stop()

    # 기존 사용자인 경우 저장된 문서 불러오기
    es, user_index = es_setting(index_name=user_index)
    existing_user, indices = check_index(es, user_index)
    if existing_user:
        res = search_all(es, user_index)
        st.session_state["doc_files"] = [hit['_id'] for hit in res['hits']['hits']]
        print("{} 사용자의 기존 문서: {}".format(user_index, st.session_state["doc_files"])) 
    else:
        st.session_state["doc_files"] = []


    # 회의록 설정
    st.title('회의록을 입력해주세요!')
    st.session_state['uploaded_files'] = st.file_uploader('정해진 형식의 회의록을 올려주세요! (txt)', accept_multiple_files=True, disabled=(False if user else True))
    

    # 기존 파일 + 업로드 파일
    # uploaded_files_names = [files.name.split(".")[0] for files in uploaded_files] # 모든 회의록 파일명
    uploaded_files = [files.name.split(".")[0] for files in st.session_state['uploaded_files']] # 모든 회의록 파일명
    st.session_state['doc_files'] += uploaded_files


    # 중복 파일 제거
    file_names = []
    doc_files = []
    for file in st.session_state['doc_files']:
        if file not in file_names:
            file_names.append(file)
            doc_files.append(file)
    st.session_state['doc_files'] = doc_files

    print("회의록 전체:", st.session_state['doc_files'])
    print("uploaded_files:", uploaded_files)

    minutes_list = [file for file in st.session_state['doc_files']] # 모든 회의록 파일명
    options = list(range(len(minutes_list)))
    print("모든 회의록: {}".format(minutes_list)) 


    if st.session_state["uploaded_files"] is not None:
        corpus, titles = read_uploadedfile(st.session_state["uploaded_files"])

    # 사용자 id에 회의록 삽입
    setting_path = "./model/setting.json"
    if existing_user:
        insert_data_st(es, user_index, corpus, titles)
    else:
        initial_index(es, user_index, setting_path=setting_path)
        insert_data_st(es, user_index, corpus, titles)
    print("user setting done")

    
    # 회의록 선택
    # selected_minutes = st.selectbox(f'회의록 목록 ({len(minutes_list)} 개)', options, 
                                    # format_func = lambda x: minutes_list[x])
    selected_minutes = st.selectbox(f'회의록 목록 ({len(minutes_list)} 개)', options,
                                    on_change = is_changed,
                                    format_func = lambda x: [file for file in st.session_state['doc_files']][x])


    # 선택한 회의록 제목, 내용 반환
    # if st.session_state['doc_files'] and selected_minutes:
    if st.session_state['doc_files']:
        # print(len(st.session_state['doc_files']))
        # print(len(minutes_list))
        # print(len(st.session_state['uploaded_files']))

        # print("doc_files: ", type(st.session_state['doc_files']))
        # print("uploaded_files: ", type(st.session_state['uploaded_files']))

        title = st.session_state['doc_files'][selected_minutes]
        data = check_data(es, user_index, doc_id=title)
        print("선택한 회의록:", title)
        # print("data in title:", data)

    # print("변경된 회의록 목록:", [file for file in st.session_state['doc_files']])


    col = st.columns([1, 1, 1])
    with col[0]:
        submit_minute = st.button(label="회의록 보기", on_click=modal.open, disabled=(False if user and len(minutes_list) > 0 else True))
    with col[1]:
        # delete_minute = st.button(label="회의록 삭제", on_click=delete_file(user_index, title), disabled=(False if user and len(minutes_list) > 0 else True))
        st.session_state["is_deleting"] = st.button(label="회의록 삭제", on_click=delete_file(user_index, title), disabled=(False if user and len(minutes_list) > 0 else True))
        print("Is deleting", st.session_state["is_deleting"])
    with col[2]:
        fix_minute = st.button(label="회의록 고정", on_click=modal.open, disabled=(False if user and len(minutes_list) > 0 else True)) 
    # submit_minute = st.button(label="회의록 보기", on_click=modal.open, disabled=(False if st.session_state['uploaded_files'] else True)) 



if modal.is_open() and submit_minute:
    with modal.container():
        # st_json = json.dumps(st.session_state['uploaded_files'][selected_minutes].read().decode('utf-8')) # 파일 형식에 따라서 주기
        # data = st.session_state['uploaded_files'][selected_minutes].read().decode('utf-8')
            
        st.title(minutes_list[selected_minutes])
        st.text_area(label="", value=data, height=500, disabled=False)



# if modal.is_open() and delete_minute:
#     # 회의록 삭제
#     print("회의록 삭제중")
#     deleted_doc = delete_doc(es, user_index, doc_id=str(title))
#     print("삭제한 회의록: {}".format(title))
#     minutes_list.remove(title)
#     st.session_state["doc_files"].remove(title)

#     print("삭제 후: ", minutes_list)
#     print("삭제 후: ", st.session_state["doc_files"])

if modal.is_open() and fix_minute:
    # 회의록 고정
    print("회의록 고정중")



# 질문 시작
if st.session_state["is_submitted"] and st.session_state["input"] != "":
    time.sleep(2)
    msg = (st.session_state["input"], True)
    st.session_state.messages.append(msg)
    with st.spinner("두뇌 풀가동!"):
        if st.session_state["is_fixxed"]:
            best_answer = run_reader(None, None, None, None, tokenizer, model, st.session_state.result_context["내용"],
            st.session_state.result_context["회의 제목"], msg[0])[0]['text']
            st.session_state.result_text_and_ids = [{ "포함되어 있던 회의록": st.session_state.result_context["회의 제목"], "찾은 답" : best_answer}] 
        else:
            result = run_mrc(None, None, None, None, tokenizer, model, msg[0], user_index)
            print(result)
            result.sort(key=lambda x: x[0]["start_logit"] + x[0]["end_logit"], reverse=True)
            st.session_state.result_text_and_ids = [{"포함되어 있던 회의록": res[2], "찾은 답" : res[0]["text"],} for res in result]
            st.session_state.result_context = {"회의 제목": result[0][2], "내용": result[0][1]}
            best_answer = st.session_state.result_text_and_ids[0]["찾은 답"]
    msg = (str(best_answer), False)
    st.session_state.messages.append(msg)

for i,msg in enumerate(st.session_state.messages):
    message(msg[0], is_user=msg[1], key = i)

if st.session_state["messages"]:
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

if modal.is_open() and st.session_state["messages"]:
    if open_other_ans_modal:
        with modal.container():
            st.title("다른 회의록에서 찾은 답")
            st.write(
                st.session_state.result_text_and_ids
            )
    elif open_minute_modal:
        with modal.container():
            title = st.session_state.result_context["회의 제목"]
            context = st.session_state.result_context["내용"]
            st.title(f"{title}")
            st.text_area(label="", value=context, height=500, disabled=False)