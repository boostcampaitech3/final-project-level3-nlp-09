import time
import streamlit as st
from streamlit_chat import message
import streamlit_modal as modal

from model.elastic_setting import *
from model.inference import load_model, run_mrc, run_reader
from collections import defaultdict

model, tokenizer = load_model()

st.title("뭐든 내게 물어봐!(MNM)")
if "input" not in st.session_state:
    st.session_state["input"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "doc_files" not in st.session_state:
    st.session_state["doc_files"] = []
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "uploaded_files_names" not in st.session_state:
    st.session_state["uploaded_files_names"] = []
if "selected_minute" not in st.session_state:
    st.session_state["selected_minute"] = ""
if "result_text_and_ids" not in st.session_state:
    st.session_state["result_text_and_ids"] = None
if "result_context" not in st.session_state:
    st.session_state["result_context"] = defaultdict(str)
if "is_deleting" not in st.session_state:
    st.session_state["is_deleting"] = False
if "faster_deleting" not in st.session_state:
    st.session_state["faster_deleting"] = False
if "is_changed" not in st.session_state:
    st.session_state["is_changed"] = False
if "is_inserting" not in st.session_state:
    st.session_state["is_inserting"] = False
if "is_fixxed" not in st.session_state:
    st.session_state["is_fixxed"] = False
if "is_submitted" not in st.session_state:
    st.session_state["is_submitted"] = False
else: 
    st.session_state["is_submitted"] = True
if "faster_inserting" not in st.session_state:
    st.session_state["faster_inserting"] = False

def delete_message():
    st.session_state["messages"] = []

def is_changed():
    st.session_state["is_changed"] = True if st.session_state["is_deleting"] else False

def click_insert_button():
    # 업로드한 파일 사용자 id에 삽입, insert_data_st()에서 중복 제거됨
    if st.session_state['uploaded_files'] is not None:
        corpus, titles = read_uploadedfile(st.session_state['uploaded_files'])

    setting_path = "./model/setting.json"
    if existing_user:
        insert_data_st(es, user_index, corpus, titles)
    else:
        initial_index(es, user_index, setting_path=setting_path)
        insert_data_st(es, user_index, corpus, titles)
    print("Complete uploading documents into user index")
    time.sleep(1)

def click_delete_button():
    deleted_doc = delete_doc(es, user_index, doc_id=str(title))
    print("삭제한 회의록: {}".format(title))
    st.session_state["doc_files"].remove(title)
    st.session_state["is_deleting"] = False
    time.sleep(1)

def click_fix_button():
    st.session_state["is_fixxed"] = False if st.session_state["is_fixxed"] else True
    title = st.session_state['doc_files'][st.session_state["selected_minute"]]
    data = check_data(es, user_index, doc_id=title)
    st.session_state.result_context["회의 제목"] = str(title)
    st.session_state.result_context["내용"] = str(data)    

def press_requery():
    st.session_state["is_fixxed"] = False if st.session_state["is_fixxed"] else True


# 사이드바 설정
with st.sidebar:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
            width: 450px;
        }
        <style>        
        """, unsafe_allow_html=True)

    # 사용자 설정
    st.title('프로젝트 이름을 입력해주세요!')
    user = st.text_input("프로젝트 이름", placeholder="프로젝트 이름", key="user", disabled=False)

    if user != "":
        user_index = user
    else:
        st.warning("프로젝트 이름을 입력해주세요!")
        st.stop()

    # 기존 사용자인 경우 저장된 문서 불러오기
    es, user_index = es_setting(index_name=user_index)
    existing_user, indices = check_index(es, user_index)
    if existing_user:
        res = search_all(es, user_index)
        st.session_state["doc_files"] = [hit['_id'] for hit in res['hits']['hits']]
        print("사용자의 기존 문서: {}".format(st.session_state["doc_files"])) 
    else:
        st.session_state["doc_files"] = []

    
    # 회의록 설정
    st.title('회의록을 입력해주세요!')
    st.session_state['uploaded_files'] = st.file_uploader('정해진 형식의 회의록을 올려주세요! (txt)', accept_multiple_files=True, 
                                                        disabled=(False if not st.session_state['uploaded_files'] and user else True))

    # 기존 파일 + 업로드 파일
    st.session_state['uploaded_files_names'] = list(set([files.name.split(".")[0] for files in st.session_state['uploaded_files']])) # 중복 제거한 업로드한 파일명
    st.session_state['doc_files'] += st.session_state['uploaded_files_names']  # 모든 회의록 파일명

    # 중복 파일 제거
    file_names = []
    doc_files = []
    for file in st.session_state['doc_files']:
        if file not in file_names:
            file_names.append(file)
            doc_files.append(file)
    
    st.session_state['doc_files'] = doc_files  # 삽입할 문서 전체

    options = list(range(len(st.session_state['doc_files'])))
    # print("@@@@@ 회의록 전체 @@@@@", st.session_state['doc_files'])


    # 회의록 업로드 버튼
    col = st.columns([2, 1])
    with col[1]:
        st.session_state["is_inserting"] = st.button(label="회의록 업로드", on_click=click_insert_button,
                                                    disabled=(False if len(st.session_state['uploaded_files_names']) > 0 else True))
    # 회의록 업로드 버튼 경고
    if not st.session_state["is_inserting"] and st.session_state['uploaded_files_names']:
        st.warning("회의록 업로드 버튼을 눌러주세요~")
        st.stop()

    # 회의록 선택
    docs_num = len(st.session_state['doc_files'])
    st.session_state["selected_minute"] = st.selectbox(f'회의록 목록 ({docs_num} 개)', options,
                                                        on_change = is_changed,
                                                        format_func = lambda x: [file for file in st.session_state['doc_files']][x])

    # 선택한 회의록 제목, 내용 반환
    if existing_user and st.session_state['doc_files'] or st.session_state["is_inserting"] and st.session_state['doc_files']:
        title = st.session_state['doc_files'][st.session_state["selected_minute"]]
        data = check_data(es, user_index, doc_id=title)
        print("선택한 회의록:", title)

    col = st.columns([1, 1, 1])
    with col[0]:
        submit_minute = st.button(label="회의록 보기", on_click=modal.open, disabled=(False if user and docs_num > 0 else True))
    with col[1]:
        st.session_state["is_deleting"] = st.button(label="회의록 삭제", on_click=click_delete_button,
                                                    disabled=(False if user and docs_num > 0 else True))
    with col[2]:
        if not st.session_state["is_fixxed"]:
            st.button(label="회의록 고정", on_click=click_fix_button, disabled=(False if user and docs_num > 0 else True))
        else:
            st.button(label="회의록 해제", on_click=click_fix_button, disabled=(False if user and docs_num > 0 else True))

if modal.is_open() and submit_minute:
    with modal.container():
        print("Modal is open...")
        html_text = f'''
        <p>{data.replace(f"{title}", f'<h3><div style="text-align:center">{title}</div></h3>')}</p>
        '''
        st.title("회의록 보기")
        st.components.v1.html(html_text, width=None, height=400, scrolling=True)


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
            if result is None:
                st.warning(f"😅\"{msg[0]}\" 에 대한 키워드가 포함된 회의록이 없어 검색해온 값이 없습니다.. 오타가 없는 지 확인하고 다시 질문해 주시기 바랍니다")
                best_answer = None
                del st.session_state.messages[-1]
            else:   
                result.sort(key=lambda x: x[0]["start_logit"] + x[0]["end_logit"], reverse=True)
                st.session_state.result_text_and_ids = [{"포함되어 있던 회의록": res[2], "찾은 답" : res[0]["text"],} for res in result]
                st.session_state.result_context = {"회의 제목": result[0][2], "내용": result[0][1]}
                best_answer = st.session_state.result_text_and_ids[0]["찾은 답"]
    if best_answer:
        msg = (str(best_answer), False)
        st.session_state.messages.append(msg)

for i, msg in enumerate(st.session_state.messages):
    logo_style = "croodles-neutral" if msg[1] else "bottts"
    message(message=msg[0], is_user=msg[1], avatar_style=logo_style, seed=user_index, key = i)

if st.session_state["messages"]:
    col = st.columns([1, 3, 3, 5])
    with col[1]:
        open_minute_modal = st.button(label="본문 보기 📖", on_click=modal.open)
    with col[2]:
        open_other_ans_modal = st.button(label="다른 답 보기 ⭐️", on_click=modal.open)
    with col[3]:
        if not st.session_state["is_fixxed"]:
            st.button(label="여기서 더 질문하기 🔎", on_click=press_requery)
        else:
            st.button(label="새로운 회의록에서 질문하기 🔎", on_click=press_requery)

if st.session_state.is_fixxed:
    st.write(st.session_state.result_context["회의 제목"] + " 에서 답을 찾는 중이야!")

with st.form(key="input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([8, 1, 1])
    with col1:
        if len(st.session_state['doc_files']) != 0:
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
        st.write("👨💬")
        st.session_state.is_submitted = st.form_submit_button(label="Ask")
    with col3:
        st.write("🧑🧹")
        st.session_state.is_submitted = st.form_submit_button(label="clear", on_click = delete_message)


if modal.is_open() and st.session_state["messages"]:
    if open_other_ans_modal:
        with modal.container():
            st.title("다른 회의록에서 찾은 답")
            html_text = ""
            medals = ["🥇","🥈","🥉"]
            for i, ans_dict in enumerate(st.session_state.result_text_and_ids):
                html_text += f"<div style=\"text-align:center\"><h3>{medals[i]} {i + 1} 순위 답변 </h3></div>"
                for key, val in ans_dict.items():
                    html_text += f"<p>💡 {key}</p>"
                    html_text += f"<pre>    - {val}</pre>"
                html_text += "<hr>"
            st.components.v1.html(html_text, width=None, height=400, scrolling=True)
    elif open_minute_modal:
        with modal.container():
            title = st.session_state.result_context["회의 제목"]
            context = st.session_state.result_context["내용"]
            best_answer = st.session_state.result_text_and_ids[0]["찾은 답"]
            
            html_text = f'''
                <p>{context
                .replace(f"{title}", f'<h3><div style="text-align:center">{title}</div></h3>')
                .replace(f"{str(best_answer)}", f'<mark style="background-color : #ffff9e">{str(best_answer)}</mark>')
                }</p>
                '''
            if best_answer not in context:
                html_text = '<p style="color:red">여기서는 답을 찾지 못하였습니다</p>' + html_text
            st.title("본문 내용")
            st.components.v1.html(html_text, width=None, height=400, scrolling=True)
