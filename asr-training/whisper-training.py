import os
from datasets import load_dataset, Audio
from transformers import WhisperProcessor, WhisperForConditionalGeneration, WhisperTokenizer
from transformers import Seq2SeqTrainingArguments, Seq2SeqTrainer
import torch
from dataclasses import dataclass
from typing import Any, Dict, List, Union
import numpy as np
from huggingface_hub import login
import pyarrow as pa
import evaluate

# Login to Hugging Face Hub
login("HF-TOKEN")

import torch
import os 
os.environ["CUDA_VISIBLE_DEVICES"] = "4"

# Load dataset and processor
dataset = load_dataset("kavyamanohar/supreme-court-speech")
processor = WhisperProcessor.from_pretrained("openai/whisper-small", task="transcribe", language="english")
tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-small",  task="transcribe", language="english")

def is_valid_audio(audio):
    """Check if audio is valid and longer than 1 second"""
    try:
        if audio is None or audio["array"] is None:
            return False
        # Check if audio is longer than 1 second (16000 samples at 16kHz)
        return len(audio["array"]) >= 16000
    except:
        return False

def safe_get_value(row, col):
    """Safely extract value from row"""
    try:
        if isinstance(row[col], (pa.Array, pa.ChunkedArray)):
            return row[col].to_pylist()[0]
        return row[col]
    except:
        return None

def prepare_dataset(batch):
    """Prepare dataset with proper error handling"""
    try:
        # Safely get audio and text
        audio = batch["audio"]
        text = safe_get_value(batch, "transcript")
        
        # Skip if audio is invalid or too short
        if not is_valid_audio(audio) or not text:
            return {
                "input_features": None,
                "labels": None
            }
        
        # Process audio
        input_features = processor(
            audio["array"],
            sampling_rate=16000,
            return_tensors="pt"
        ).input_features[0]
        
        # Process text
        labels = processor(text=text).input_ids
        
        return {
            "input_features": input_features,
            "labels": labels
        }
    except Exception as e:
        print(f"Error processing batch: {e}")
        return {
            "input_features": None,
            "labels": None
        }

print("Processing dataset...")
processed_dataset = dataset.map(
    prepare_dataset,
    remove_columns=['audio', 'transcript', 'duration'],
    num_proc=16,
    batch_size=100  # Process in smaller batches
)

print("Filtering invalid samples...")
processed_dataset = processed_dataset.filter(
    lambda x: x["input_features"] is not None and x["labels"] is not None
)

print(processed_dataset)

@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: Any
    
    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        # Additional validation
        features = [f for f in features if f is not None and "input_features" in f and "labels" in f]
        if not features:
            raise ValueError("No valid features found in batch")
            
        input_features = [{"input_features": feature["input_features"]} for feature in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
        
        label_features = [{"input_ids": feature["labels"]} for feature in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
        
        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
        
        batch["labels"] = labels
        
        return batch

# Initialize model and data collator
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)

metric = evaluate.load("wer")
def compute_metrics(pred):
    pred_ids = pred.predictions
    label_ids = pred.label_ids

    # replace -100 with the pad_token_id
    label_ids[label_ids == -100] = tokenizer.pad_token_id

    pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = tokenizer.batch_decode(label_ids, skip_special_tokens=True)

    wer = 100 * metric.compute(predictions=pred_str, references=label_str)
    return {"wer": wer}


# Training arguments
training_args = Seq2SeqTrainingArguments(
    output_dir="kavyamanohar/whisper-supreme-court-asr",
    per_device_train_batch_size=16,
    gradient_accumulation_steps=2,
    learning_rate=1e-5,
    warmup_steps=500,
    max_steps=1000,
    gradient_checkpointing=True,
    fp16=True,
    evaluation_strategy="steps",
    eval_steps=200,
    save_steps=200,
    logging_steps=25,
    report_to=["tensorboard"],
    load_best_model_at_end=True,
    metric_for_best_model="wer",
    greater_is_better=False,
    push_to_hub=True,
    hub_model_id="kavyamanohar/whisper-supreme-court-asr",
)

# Initialize trainer
trainer = Seq2SeqTrainer(
    args=training_args,
    model=model,
    train_dataset=processed_dataset["train"],
    eval_dataset=processed_dataset["test"],
    data_collator=data_collator,
    compute_metrics=compute_metrics,
    tokenizer=processor,
)


# Start training
trainer.train()

kwargs = {
    "dataset_tags": "kavyamanohar/supreme-court-speech",
    "dataset": "Supreme Court Hearing Corpus - Subset",  # a 'pretty' name for the training dataset
    "dataset_args": "split: test",
    "language": "eng",
    "model_name": "kavyamanohar/whisper-supreme-court-asr",  # a 'pretty' name for your model
    "finetuned_from": "openai/whisper-small",
    "tasks": "automatic-speech-recognition",
}

# Push to hub
trainer.push_to_hub(**kwargs)
