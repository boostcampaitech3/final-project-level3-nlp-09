"""
Open-Domain Question Answering 을 수행하는 inference 코드 입니다.

대부분의 로직은 train.py 와 비슷하나 retrieval, predict 부분이 추가되어 있습니다.
"""


import sys
import logging
sys.path.append("model")
from typing import Callable, Dict, List, NoReturn, Tuple
import numpy as np
import streamlit as st
from datasets import Dataset, DatasetDict, Features, Value, load_metric
from transformers import (
    AutoConfig,
    AutoModelForQuestionAnswering,
    AutoTokenizer,
    DataCollatorWithPadding,
    EvalPrediction,
    HfArgumentParser,
    TrainingArguments,
    set_seed
)
import pandas as pd
from arguments import DataTrainingArguments, ModelArguments
from retrieval import SparseRetrieval, ElasticRetrieval
from trainer_qa import QuestionAnsweringTrainer
from utils_qa import postprocess_qa_predictions


@st.cache(allow_output_mutation=True)
def load_model():
    parser = HfArgumentParser((ModelArguments, DataTrainingArguments))
    model_args, data_args = parser.parse_args_into_dataclasses()

    print("=" * 100)
    print(model_args)
    config = AutoConfig.from_pretrained(
        model_args.config_name
        if model_args.config_name
        else model_args.model_name_or_path,
    )
    print(config)
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.tokenizer_name
        if model_args.tokenizer_name
        else model_args.model_name_or_path,
        use_fast=True,
    )
    model = AutoModelForQuestionAnswering.from_pretrained(
        model_args.model_name_or_path,
        from_tf=bool(".ckpt" in model_args.model_name_or_path),
        config=config,
    )

    return model, tokenizer
def run_mrc(
    data_args: DataTrainingArguments,
    training_args: TrainingArguments,
    model_args: ModelArguments,
    datasets: DatasetDict,
    tokenizer,
    model,
    query,
) -> NoReturn:
    parser = HfArgumentParser((ModelArguments, DataTrainingArguments))
    model_args, data_args = parser.parse_args_into_dataclasses()
    if query != None:
        my_dict = {"question": [query], "id": ["answer"]}
    else:
        pd_test = pd.read_csv("../data/test.csv")
        my_dict = {"question":list(pd_test["question"]),"id":list(map(str,pd_test["id"]))}
    datasets = DatasetDict()
    datasets["validation"] = Dataset.from_dict(my_dict)
    datasets = run_sparse_retrieval(
        tokenizer.tokenize,
        datasets,
        None,
        data_args,
    )
    column_names = datasets["validation"].column_names
    question_column_name = (
        "question" if "question" in column_names else column_names[0]
    )
    context_column_name = (
        "context" if "context" in column_names else column_names[1]
    )
    answer_column_name = (
        "answers" if "answers" in column_names else column_names[2]
    )

    pad_on_right = tokenizer.padding_side == "right"

    # Validation preprocessing
    def prepare_validation_features(examples):
        tokenized_examples = tokenizer(
            examples[
                question_column_name if pad_on_right else context_column_name
            ],
            examples[
                context_column_name if pad_on_right else question_column_name
            ],
            truncation="only_second" if pad_on_right else "only_first",
            max_length=384,
            stride=data_args.doc_stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            return_token_type_ids=False, # roberta: False / bert:True
            padding="max_length" if data_args.pad_to_max_length else False,
        )

        sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")

        tokenized_examples["example_id"] = []

        for i in range(len(tokenized_examples["input_ids"])):
            # setting sequence id
            sequence_ids = tokenized_examples.sequence_ids(i)
            context_index = 1 if pad_on_right else 0

            sample_index = sample_mapping[i]
            tokenized_examples["example_id"].append(
                examples["id"][sample_index]
            )

            # context의 일부가 아닌 offset_mapping을 None으로 설정하여 토큰 위치가 컨텍스트의 일부인지 여부를 쉽게 판별할 수 있습니다.
            tokenized_examples["offset_mapping"][i] = [
                (o if sequence_ids[k] == context_index else None)
                for k, o in enumerate(tokenized_examples["offset_mapping"][i])
            ]
        return tokenized_examples

    eval_dataset = datasets["validation"]

    # Create Validation Feature
    eval_dataset = eval_dataset.map(
        prepare_validation_features,
        batched=True,
        num_proc=data_args.preprocessing_num_workers,
        remove_columns=column_names,
        load_from_cache_file=not data_args.overwrite_cache,
    )

    data_collator = DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8)

# Post-processing: start logits & end logits을 original context의 정답과 match
    def post_processing_function(
        examples,
        features,
        predictions: Tuple[np.ndarray, np.ndarray],
        training_args: TrainingArguments,
    ) -> EvalPrediction:
        predictions = postprocess_qa_predictions(
            examples=examples,
            features=features,
            predictions=predictions,
            max_answer_length=data_args.max_answer_length,
            output_dir=training_args.output_dir,
        )

        # Metric을 구할 수 있도록 Format 맞춤
        formatted_predictions = [
            {"id": k, "prediction_text": v} for k, v in predictions.items()
        ]

        return formatted_predictions

    metric = load_metric("squad")

    def compute_metrics(p: EvalPrediction) -> Dict:
        return metric.compute(predictions=p.predictions, references=p.label_ids)

    # Trainer init
    trainer = QuestionAnsweringTrainer(
        model=model,
        args=training_args,
        train_dataset=None,
        eval_dataset=eval_dataset,
        eval_examples=datasets["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        post_process_function=post_processing_function,
        compute_metrics=compute_metrics,
    )

    predictions = trainer.predict(
        test_dataset=eval_dataset, test_examples=datasets["validation"]
    )
    return predictions[0]["prediction_text"][0]

def run_retriever_reader(
    data_args: DataTrainingArguments,
    training_args: TrainingArguments,
    model_args: ModelArguments,
    datasets: DatasetDict,
    tokenizer,
    model,
    query,
):
    parser = HfArgumentParser((ModelArguments, DataTrainingArguments))
    model_args, data_args = parser.parse_args_into_dataclasses()
    retriever = ElasticRetrieval(data_args.index_name)
    my_dict = {"question": [query], "id": ["answer"]}
    datasets = DatasetDict()
    datasets["validation"] = Dataset.from_dict(my_dict)
    retrieved_dfs = retriever.retrieve_split(datasets["validation"], topk = data_args.top_k_retrieval)
    results = []
    for df in retrieved_dfs:
        results.append((run_reader(None, None, None, None, tokenizer, model, df.iloc[0]["context"], df.iloc[0]["context_id"], query)))
    return results

def run_reader(
    data_args: DataTrainingArguments,
    training_args: TrainingArguments,
    model_args: ModelArguments,
    datasets: DatasetDict,
    tokenizer,
    model,
    text,
    text_id,
    query,
) -> NoReturn:
    parser = HfArgumentParser((ModelArguments, DataTrainingArguments))
    model_args, data_args = parser.parse_args_into_dataclasses()
    if query != None:
        my_dict = {"question": [query], "id": ["answer"]}
    else:
        pd_test = pd.read_csv("../data/test.csv")
        my_dict = {"question":list(pd_test["question"]),"id":list(map(str,pd_test["id"]))}

    f = Features(
        {
            "context": Value(dtype="string", id=None),
            "id": Value(dtype="string", id=None),
            "question": Value(dtype="string", id=None),
        }
    )
    df = pd.DataFrame({
        "question": query,
        "id": ["answer"],
        "context_id": 0 if text_id == None else text_id,
        "context": text,
    })

    datasets = DatasetDict({"validation": Dataset.from_pandas(df, features=f)})
    column_names = datasets["validation"].column_names
    question_column_name = (
        "question" if "question" in column_names else column_names[0]
    )
    context_column_name = (
        "context" if "context" in column_names else column_names[1]
    )
    answer_column_name = (
        "answers" if "answers" in column_names else column_names[2]
    )

    pad_on_right = tokenizer.padding_side == "right"

    # Validation preprocessing
    def prepare_validation_features(examples):
        tokenized_examples = tokenizer(
            examples[
                question_column_name if pad_on_right else context_column_name
            ],
            examples[
                context_column_name if pad_on_right else question_column_name
            ],
            truncation="only_second" if pad_on_right else "only_first",
            max_length=384,
            stride=data_args.doc_stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            return_token_type_ids=False, # roberta: False / bert:True
            padding="max_length" if data_args.pad_to_max_length else False,
        )

        sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")

        tokenized_examples["example_id"] = []

        for i in range(len(tokenized_examples["input_ids"])):
            # setting sequence id
            sequence_ids = tokenized_examples.sequence_ids(i)
            context_index = 1 if pad_on_right else 0

            sample_index = sample_mapping[i]
            tokenized_examples["example_id"].append(
                examples["id"][sample_index]
            )

            # context의 일부가 아닌 offset_mapping을 None으로 설정하여 토큰 위치가 컨텍스트의 일부인지 여부를 쉽게 판별할 수 있습니다.
            tokenized_examples["offset_mapping"][i] = [
                (o if sequence_ids[k] == context_index else None)
                for k, o in enumerate(tokenized_examples["offset_mapping"][i])
            ]
        return tokenized_examples

    eval_dataset = datasets["validation"]

    # Create Validation Feature
    eval_dataset = eval_dataset.map(
        prepare_validation_features,
        batched=True,
        num_proc=data_args.preprocessing_num_workers,
        remove_columns=column_names,
        load_from_cache_file=not data_args.overwrite_cache,
    )

    data_collator = DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8)

# Post-processing: start logits & end logits을 original context의 정답과 match
    def post_processing_function(
        examples,
        features,
        predictions: Tuple[np.ndarray, np.ndarray],
        training_args: TrainingArguments,
    ) -> EvalPrediction:
        predictions = postprocess_qa_predictions(
            examples=examples,
            features=features,
            predictions=predictions,
            max_answer_length=data_args.max_answer_length,
            output_dir=training_args.output_dir,
        )

        # Metric을 구할 수 있도록 Format 맞춤
        formatted_predictions = [
            {"id": k, "prediction_text": v} for k, v in predictions.items()
        ]

        return formatted_predictions

    metric = load_metric("squad")

    def compute_metrics(p: EvalPrediction) -> Dict:
        return metric.compute(predictions=p.predictions, references=p.label_ids)

    # Trainer init
    trainer = QuestionAnsweringTrainer(
        model=model,
        args=training_args,
        train_dataset=None,
        eval_dataset=eval_dataset,
        eval_examples=datasets["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        post_process_function=post_processing_function,
        compute_metrics=compute_metrics,
    )

    predictions = trainer.predict(
        test_dataset=eval_dataset, test_examples=datasets["validation"]
    )
    return predictions[0]["prediction_text"][0], text ,text_id

def run_sparse_retrieval(
    tokenize_fn: Callable[[str], List[str]],
    datasets: DatasetDict,
    training_args: TrainingArguments,
    data_args: DataTrainingArguments,
    data_path: str = "../data/",
    context_path: str = "../data/wikipedia_documents.json",
) -> DatasetDict:

    # Query에 맞는 Passage들을 Retrieval 합니다.
    
    # Elasticsearch 사용하는 경우
    if data_args.elastic:
        retriever = ElasticRetrieval(data_args.index_name)
    else:
        retriever = SparseRetrieval(
            tokenize_fn=tokenize_fn, data_path=data_path, context_path=context_path
        )
        retriever.get_sparse_embedding()


    if data_args.use_faiss:
        retriever.build_faiss(num_clusters=data_args.num_clusters)
        df = retriever.retrieve_faiss(
            datasets["validation"], topk=data_args.top_k_retrieval
        )
    else:
        df = retriever.retrieve(
            datasets["validation"], topk=data_args.top_k_retrieval
        )

    f = Features(
        {
            "context": Value(dtype="string", id=None),
            "id": Value(dtype="string", id=None),
            "question": Value(dtype="string", id=None),
        }
    )

    datasets = DatasetDict({"validation": Dataset.from_pandas(df, features=f)})
    return datasets

logger = logging.getLogger(__name__)

def main():
    model, tokenizer = load_model()
    set_seed(42)
    run_mrc(None, None, None, None, tokenizer, model, None)


if __name__ == "__main__":
    main()