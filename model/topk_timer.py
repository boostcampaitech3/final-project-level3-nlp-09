from inference import *
import pandas as pd
import json
from contextlib import contextmanager
import time
import numpy as np
model, tokenizer = load_model()
times = []
"""
top k 별 시간 측정을 위한 코드입니다
"""

@contextmanager
def timer(name):
    t0 = time.time()
    yield
    times.append(time.time() - t0)


def main():
    test_queries = list(pd.read_csv("/opt/ml/input/final-project-level3-nlp-09/data/test.csv")["question"])
    result = []
    for query in test_queries:
        with timer(None):
            result.append([res[0]["text"] for res in run_mrc(None, None, None, None, tokenizer, model, query)])
    with open('../data/result_top1.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)
    nptimes = np.array(times)
    print(np.mean(nptimes), np.std(nptimes))
if __name__ == "__main__":
    main()
