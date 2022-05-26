import json
import pandas as pd
from datasets import load_metric 
def main():
    with open("./tmp_trainer/predictions.json", "r") as f:
        predictions = json.load(f)
    
    predictions = [
        {"id": list(predictions.keys())[i], "prediction_text": list(predictions.values())[i]}
        for i in range(len(predictions))
    ]

    pd_test = pd.read_csv("../data/test.csv")

    references = []
    for ex in range(len(pd_test)):
        answers = eval(pd_test.iloc[ex]["answers"])
        answers["answer_start"] = [answers["answer_start"]]
        answers["text"] = [answers["text"]]
        references.append({"id": pd_test.iloc[ex]["id"], "answers": answers})

    metric = load_metric("squad")
    print(metric.compute(predictions=predictions, references=references))

if __name__ == "__main__":
    main()