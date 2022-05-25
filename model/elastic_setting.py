import json
import pprint
import warnings
import re
import argparse
from tqdm import tqdm
from elasticsearch import Elasticsearch

warnings.filterwarnings('ignore')

"""
Elasticsearch를 사용하기 전 처음에 한 번 실행시켜주세요!!!
데이터 index 설정값을 바꾸거나 새로운 데이터를 삽입할 때는 index_name을 변경해서 실행시켜주세요!!!
"""

# elasticsearch 서버 세팅 
def es_setting(index_name="origin-wiki"):
    es = Elasticsearch('http://localhost:9200', timeout=30, max_retries=10, retry_on_timeout=True)
    print("Ping Elasticsearch :", es.ping())
    # print('Elastic search info:')
    # print(es.info())

    return es, index_name

# 인덱스 생성
def set_index(es, index_name, setting_path):
    # 이미 인덱스가 존재하는 경우 삭제
    if es.indices.exists(index=index_name):
        print("Index already exists. Creating a new one after deleting it...")
        es.indices.delete(index=index_name)

    with open(setting_path, "r") as f:
        setting = json.load(f)
    es.indices.create(index=index_name, body=setting)
    print("Index creation has been completed")

# 삽입할 데이터 전처리
def preprocess(text):
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"\\n", " ", text)
    text = re.sub(r"#", " ", text)
    text = re.sub(r"[^A-Za-z0-9가-힣.?!,()~‘’“”"":%&《》〈〉''㈜·\-\'+\s一-龥サマーン]", "", text)  # サマーン 는 predictions.json에 있었음
    text = re.sub(r"\s+", " ", text).strip()  # 두 개 이상의 연속된 공백을 하나로 치환
    # text = re.sub(r"[^A-Za-z0-9가-힣.?!,()~‘’“”"":%&《》〈〉''㈜·\-\'+\s一-龥]", "", text)
    
    return text

# 위키피디아 데이터 로드
def load_data(dataset_path):
    # dataset_path = "../data/wikipedia_documents.json"
    with open(dataset_path, "r") as f:
        wiki = json.load(f)

    wiki_texts = list(dict.fromkeys([v["text"] for v in wiki.values()]))
    wiki_texts = [preprocess(text) for text in wiki_texts]
    wiki_corpus = [
        {"document_text": wiki_texts[i]} for i in range(len(wiki_texts))
    ]
    return wiki_corpus

# 인덱스에 데이터 삽입
def insert_data(es, index_name, dataset_path):
    wiki_corpus = load_data(dataset_path)
    for i, text in enumerate(tqdm(wiki_corpus)):
        try:
            es.index(index=index_name, id=i, body=text)
        except:
            print(f"Unable to load document {i}.")

    n_records = es.count(index=index_name)["count"]
    print(f"Succesfully loaded {n_records} into {index_name}")
    print("@@@@@@@ 데이터 삽입 완료 @@@@@@@")

# 삽입한 데이터 확인
def check_data(es, index_name, doc_id=0):
    print('샘플 데이터:')
    doc = es.get(index=index_name, id=doc_id)
    pprint.pprint(doc)

def es_search(es, index_name, question, topk):
    # question = "대통령을 포함한 미국의 행정부 견제권을 갖는 국가 기관은?"
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"document_text": question}}
                ]
            }
        }
    }

    res = es.search(index=index_name, body=query, size=topk)
    return res

def main(args):
    es, index_name = es_setting(index_name=args.index_name)
    set_index(es, index_name, args.setting_path)  # 이미 인덱스가 존재하면 주석처리
    insert_data(es, index_name, args.dataset_path)  # 이미 인덱스 안에 데이터가 존재하면 주석처리
    check_data(es, index_name, doc_id=1)


    query = "대통령을 포함한 미국의 행정부 견제권을 갖는 국가 기관은?"
    res = es_search(es, index_name, query, 10)
    print("========== RETRIEVE RESULTS ==========")
    pprint.pprint(res)


    print('\n=========== RETRIEVE SCORES ==========\n')
    for hit in res['hits']['hits']:
        print("Doc ID: %3r  Score: %5.2f" % (hit['_id'], hit['_score']))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--setting_path", default="./setting.json", type=str, help="생성할 index의 setting.json 경로를 설정해주세요")
    parser.add_argument("--dataset_path", default="/opt/ml/input/final-project-level3-nlp-09/data_utils/meeting_collection.json", type=str, help="삽입할 데이터의 경로를 설정해주세요")
    parser.add_argument("--index_name", default="origin-meeting-wiki", type=str, help="테스트할 index name을 설정해주세요")

    args = parser.parse_args()
    main(args)