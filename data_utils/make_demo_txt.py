import os
import re
import pandas as pd

def preprocess(text):
    """
    삽입할 데이터 전처리
    """
    text = re.sub(r"\n\n", " ", text)
    # text = re.sub(r"\\n", " ", text)
    text = re.sub(r"#", " ", text)
    text = re.sub(r"[^A-Za-z0-9가-힣.?!,()~‘’“”"":%&《》〈〉''㈜·\-\'+\s一-龥]", "", text)
    text = re.sub(r"\s+", " ", text).strip()  # 두 개 이상의 연속된 공백을 하나로 치환
    
    return text


path = "../data/test.csv"
save_folder = "../data/demo_data/" 

df = pd.read_csv(path)
context_df = pd.DataFrame()
context_df["raw"] = df["context"]
# context_df.head()


for i in range(len(context_df)):
    # 회의록 내용이랑 제목 분리
    data = context_df["raw"].iloc[i].split("@")
    title = preprocess(data[1])

    # 회의록 띄어쓰기 보정
    if title[-12:] == " 본 회 의 회 의 록" or title[-12:] == "본 회 의 회 의 록":
        title = title[:-12] + " 본희의회의록"
    content = preprocess(data[2])
    
    # 제목을 파일명으로 저장
    save_path = save_folder + title + ".txt"
    print(save_path)
    
    with open(save_path, "w") as f:
        f.write(content)
    f.close()
