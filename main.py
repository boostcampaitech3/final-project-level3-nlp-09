import time
from requests import session
import streamlit as st
from streamlit_chat import message
from model.elastic_setting import *
from model.inference import load_model, run_mrc, run_reader
import streamlit_authenticator as stauth
import streamlit_modal as modal


def streamlit_main():
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
        st.session_state["result_context"] = ""
    if "is_fixxed" not in st.session_state:
        st.session_state["is_fixxed"] = False
    if "is_deleting" not in st.session_state:
        st.session_state["is_deleting"] = False
    if "is_changed" not in st.session_state:
        st.session_state["is_changed"] = False
    if "is_inserting" not in st.session_state:
        st.session_state["is_inserting"] = False
    if "faster_inserting" not in st.session_state:
        st.session_state["faster_inserting"] = False
    if "is_submitted" not in st.session_state:
        st.session_state["is_submitted"] = False
    else: 
        st.session_state["is_submitted"] = True
    # if 'insert_file_cnt' not in st.session_state:
    #     st.session_state["insert_file_cnt"] = 0

    def uploader_callback():
        print('Uploaded file')

    def press_requery():
        st.session_state["is_fixxed"] = False if st.session_state["is_fixxed"] else True
        
    def delete_file():
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

    def click_insert_button():
        st.session_state["is_inserting"] = True if st.session_state["is_inserting"] else False
        # st.session_state["insert_file_cnt"] += 1
        # print("회의록 업로드 횟수:", st.session_state["insert_file_cnt"])

    # 사이드바 설정
    with st.sidebar:

        # 사용자 설정
        user = st.session_state['username']
        user_index = user # 수정
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
        st.session_state['uploaded_files'] = st.file_uploader('정해진 형식의 회의록을 올려주세요! (txt)', accept_multiple_files=True, 
                                                            on_change=click_insert_button,
                                                            disabled=(False if not st.session_state["is_inserting"] and user else True))


        # 기존 파일 + 업로드 파일
        st.session_state['uploaded_files_names'] = list(set([files.name.split(".")[0] for files in st.session_state['uploaded_files']])) # 중복 제거한 업로드한 파일명
        st.session_state['doc_files'] += st.session_state['uploaded_files_names']  # 모든 회의록 파일명
        print("@@@@@@ 업로드한 파일 @@@@@@:", st.session_state['uploaded_files_names'])

        # 중복 파일 제거
        file_names = []
        doc_files = []
        for file in st.session_state['doc_files']:
            if file not in file_names:
                file_names.append(file)
                doc_files.append(file)
        st.session_state['doc_files'] = doc_files  # 삽입할 문서 전체

        options = list(range(len(st.session_state['doc_files'])))
        print("회의록 전체:", st.session_state['doc_files'])


        # 회의록 업로드 버튼 1    
        col = st.columns([1, 1])
        with col[0]:
            st.session_state["is_inserting"] = st.button(label="회의록 업로드", on_click=click_insert_button,
                                                        disabled=(False if len(st.session_state['uploaded_files_names']) > 0 else True))

        # 회의록 업로드
        if st.session_state["is_inserting"]:
            # 업로드한 파일 사용자 id에 삽입, insert_data_st()에서 중복 제거됨
            if st.session_state['uploaded_files'] is not None:
                corpus, titles = read_uploadedfile(st.session_state['uploaded_files'])

            # 사용자 id에 회의록 삽입
            setting_path = "./model/setting.json"
            if existing_user:
                insert_data_st(es, user_index, corpus, titles)
            else:
                initial_index(es, user_index, setting_path=setting_path)
                insert_data_st(es, user_index, corpus, titles)
            print("Complete uploading documents into user index")

        # 회의록 업로드 버튼 2
        with col[1]:
            st.session_state["faster_inserting"] = st.button(label="빠르게 올라가랏!", on_click=click_insert_button,
                                                    disabled=False if st.session_state['is_inserting'] else True)
        # 회의록 업로드 버튼 경고
        if not st.session_state["is_inserting"] and st.session_state['uploaded_files_names']:
            st.warning("회의록 업로드 버튼을 눌러주세요~")
            st.stop()
        if st.session_state['uploaded_files_names'] and st.session_state["is_inserting"]:
            st.warning("빠르게 버튼을 눌러주세요~")
            st.stop() 
        
        # 회의록 선택
        docs_num = len(st.session_state['doc_files'])
        st.session_state["selected_minute"] = st.selectbox(f'회의록 목록 ({docs_num} 개)', options,
                                                            on_change = is_changed,
                                                            format_func = lambda x: [file for file in st.session_state['doc_files']][x])


        # 선택한 회의록 제목, 내용 반환
        # if st.session_state['doc_files']:
        if existing_user and st.session_state['doc_files'] or st.session_state["is_inserting"] and st.session_state['doc_files']:
            selected_minute = st.session_state["selected_minute"]
            title = st.session_state['doc_files'][selected_minute]
            data = check_data(es, user_index, doc_id=title)
            print("선택한 회의록:", title)
            # print("data in title:", data)


        col = st.columns([1, 1, 1])
        with col[0]:
            submit_minute = st.button(label="회의록 보기", on_click=modal.open, disabled=(False if user and docs_num > 0 else True))
        with col[1]:
            st.session_state["is_deleting"] = st.button(label="회의록 삭제", on_click=delete_file, disabled=(False if user and docs_num > 0 else True))
            # print("Is deleting", st.session_state["is_deleting"])
        with col[2]:
            fix_minute = st.button(label="회의록 고정", on_click=modal.open, disabled=(False if user and docs_num > 0 else True))  


    if modal.is_open() and submit_minute:
        with modal.container():
            # data = st.session_state['uploaded_files'][selected_minute].read().decode('utf-8')
            st.title(st.session_state['doc_files'][selected_minute])
            st.text_area(label="", value=data, height=500, disabled=False)


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

names = ['Changuk','Nayeon']
usernames = ['chan','yeon']
passwords = ['123','456']
hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(names,usernames,hashed_passwords,'cookie_name', 'signature_key',cookie_expiry_days=1)
name, authentication_status, username = authenticator.login('Login', 'main')

if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.write(f'사용자: {st.session_state["name"]}')
    streamlit_main()
elif st.session_state["authentication_status"] == False:
    st.error('Username/password를 확인하세요')
elif st.session_state["authentication_status"] == None:
    st.warning('username and password를 입력하세요')