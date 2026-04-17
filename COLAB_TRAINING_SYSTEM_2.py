"""
SYSTEM 2 - Train on Assigned Dataset Splits
Copy this entire code into a single Colab cell
"""

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================
!pip install -q transformers datasets accelerate huggingface_hub torch

# ============================================================================
# IMPORTS
# ============================================================================
import os
import torch
import pandas as pd
from datasets import Dataset, DatasetDict, concatenate_datasets
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from huggingface_hub import login, HfApi
from sklearn.model_selection import train_test_split
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================
HF_TOKEN = "your-hf-token"
HF_USERNAME = "Bharat2004"
MODEL_NAME = "microsoft/deberta-v3-base"
OUTPUT_MODEL_NAME = "fake-news-mega-split-2"
SPLIT_NUMBER = 2  # System id
TOTAL_SPLITS = 3

# Login to HuggingFace
login(token=HF_TOKEN)

print(f"🚀 Training System {SPLIT_NUMBER}/{TOTAL_SPLITS}")
print(f"📦 Base Model: {MODEL_NAME}")
print(f"💾 Output: {HF_USERNAME}/{OUTPUT_MODEL_NAME}")
print(f"🔥 GPU Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"   Device: {torch.cuda.get_device_name(0)}")

# ============================================================================
# LOAD DATA FROM HUGGINGFACE
# ============================================================================
print("\n📊 Loading dataset from HuggingFace...")

from datasets import load_dataset

dataset = load_dataset("Bharat2004/factchecker-deberta", split="train")

# Convert to pandas for splitting
df = dataset.to_pandas()
print(f"Total samples: {len(df)}")

# ============================================================================
# SPLIT DATA INTO 3 PARTS - USE SPLIT 2
# ============================================================================
total_samples = len(df)
split_size = total_samples // TOTAL_SPLITS

# Calculate indices for this split
start_idx = (SPLIT_NUMBER - 1) * split_size
if SPLIT_NUMBER == TOTAL_SPLITS:
    end_idx = total_samples  # Last split gets remaining samples
else:
    end_idx = SPLIT_NUMBER * split_size

# Get this split's data
df_split = df.iloc[start_idx:end_idx].copy()
print(f"\n✂️ Split {SPLIT_NUMBER}: Samples {start_idx} to {end_idx}")
print(f"   Training on {len(df_split)} samples")

# Split into train/val
train_df, val_df = train_test_split(
    df_split,
    test_size=0.1,
    random_state=42,
    stratify=df_split['label'] if 'label' in df_split.columns else None
)

print(f"   Train: {len(train_df)} samples")
print(f"   Val: {len(val_df)} samples")

# ============================================================================
# CREATE DATASETS
# ============================================================================
train_dataset = Dataset.from_pandas(train_df)
val_dataset = Dataset.from_pandas(val_df)

# ============================================================================
# TOKENIZATION
# ============================================================================
print("\n🔤 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=512
    )

print("🔤 Tokenizing datasets...")
train_dataset = train_dataset.map(tokenize_function, batched=True)
val_dataset = val_dataset.map(tokenize_function, batched=True)

# Set format for PyTorch
train_dataset.set_format("torch", columns=["input_ids", "attention_mask", "label"])
val_dataset.set_format("torch", columns=["input_ids", "attention_mask", "label"])

# ============================================================================
# LOAD MODEL
# ============================================================================
print("\n🤖 Loading model...")
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=2,  # binary classification (fake/real)
    problem_type="single_label_classification"
)

# Move to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# ============================================================================
# TRAINING ARGUMENTS
# ============================================================================
training_args = TrainingArguments(
    output_dir=f"./results_split{SPLIT_NUMBER}",
    eval_strategy="steps",
    eval_steps=500,
    save_strategy="steps",
    save_steps=500,
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=2,
    weight_decay=0.01,
    warmup_ratio=0.1,
    logging_dir=f"./logs_split{SPLIT_NUMBER}",
    logging_steps=100,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    fp16=True,  # Use mixed precision for faster training
    save_total_limit=2,
    report_to="none",
    push_to_hub=False,  # We'll push manually
)

# ============================================================================
# METRICS
# ============================================================================
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    accuracy = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='binary'
    )
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

# ============================================================================
# TRAINER
# ============================================================================
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# ============================================================================
# TRAIN
# ============================================================================
print(f"\n🏋️ Starting training on Split {SPLIT_NUMBER}...")
print(f"⏱️ Estimated time: ~30-45 minutes on T4 GPU")

trainer.train()

# ============================================================================
# EVALUATE
# ============================================================================
print("\n📊 Evaluating model...")
eval_results = trainer.evaluate()

print("\n✅ Training Complete!")
print(f"📈 Final Results (Split {SPLIT_NUMBER}):")
for key, value in eval_results.items():
    print(f"   {key}: {value:.4f}")

# ============================================================================
# SAVE AND UPLOAD TO HUGGINGFACE
# ============================================================================
print(f"\n💾 Saving model to HuggingFace: {HF_USERNAME}/{OUTPUT_MODEL_NAME}")

# Save model locally first
model.save_pretrained(f"./model_split{SPLIT_NUMBER}")
tokenizer.save_pretrained(f"./model_split{SPLIT_NUMBER}")

# Create model card
model_card = (
    '---\n'
    'language: en\n'
    'license: apache-2.0\n'
    'tags:\n'
    '- text-classification\n'
    '- fake-news-detection\n'
    '- fact-checking\n'
    'datasets:\n'
    '- {HF_USERNAME}/factchecker-deberta\n'
    'metrics:\n'
    '- accuracy\n'
    '- f1\n'
    'model-index:\n'
    '- name: {OUTPUT_MODEL_NAME}\n'
    '  results:\n'
    '  - task:\n'
    '      type: text-classification\n'
    '      name: Fake News Detection\n'
    '    metrics:\n'
    '    - type: accuracy\n'
    '      value: {eval_accuracy:.4f}\n'
    '    - type: f1\n'
    '      value: {eval_f1:.4f}\n'
    '---\n'
    '\n'
    '# FactChecker DeBERTa - Split {SPLIT_NUMBER}\n'
    '\n'
    'This model is part of a distributed training setup (Split {SPLIT_NUMBER}/{TOTAL_SPLITS}).\n'
    '\n'
    '## Model Details\n'
    '- **Base Model:** {MODEL_NAME}\n'
    '- **Training Split:** {SPLIT_NUMBER} of {TOTAL_SPLITS}\n'
    '- **Training Samples:** {train_samples}\n'
    '- **Validation Samples:** {val_samples}\n'
    '\n'
    '## Performance\n'
    '- **Accuracy:** {eval_accuracy:.4f}\n'
    '- **F1 Score:** {eval_f1:.4f}\n'
    '- **Precision:** {eval_precision:.4f}\n'
    '- **Recall:** {eval_recall:.4f}\n'
    '\n'
    '## Usage\n'
    '```python\n'
    'from transformers import AutoTokenizer, AutoModelForSequenceClassification\n'
    '\n'
    'tokenizer = AutoTokenizer.from_pretrained("{HF_USERNAME}/{OUTPUT_MODEL_NAME}")\n'
    'model = AutoModelForSequenceClassification.from_pretrained("{HF_USERNAME}/{OUTPUT_MODEL_NAME}")\n'
    '\n'
    'text = "Your claim to fact-check"\n'
    'inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)\n'
    'outputs = model(**inputs)\n'
    'prediction = outputs.logits.argmax(-1).item()\n'
    '# 0 = Real, 1 = Fake\n'
    '```\n'
    '\n'
    '## Training Details\n'
    '- Epochs: 2\n'
    '- Batch Size: 8\n'
    '- Learning Rate: 2e-5\n'
    '- Mixed Precision: FP16\n'
    '- GPU: T4 (Free Colab)\n'
    '\n'
    '## Note\n'
    'This is one of {TOTAL_SPLITS} models trained in parallel. For best results, ensemble all splits or use the final merged model.\n'
).format(
    HF_USERNAME=HF_USERNAME,
    OUTPUT_MODEL_NAME=OUTPUT_MODEL_NAME,
    SPLIT_NUMBER=SPLIT_NUMBER,
    TOTAL_SPLITS=TOTAL_SPLITS,
    MODEL_NAME=MODEL_NAME,
    train_samples=len(train_df),
    val_samples=len(val_df),
    eval_accuracy=eval_results['eval_accuracy'],
    eval_f1=eval_results['eval_f1'],
    eval_precision=eval_results['eval_precision'],
    eval_recall=eval_results['eval_recall']
)

# Save model card
with open(f"./model_split{SPLIT_NUMBER}/README.md", "w") as f:
    f.write(model_card)

# Push to HuggingFace Hub
print("📤 Uploading to HuggingFace Hub...")
trainer.push_to_hub(
    repo_id=f"{HF_USERNAME}/{OUTPUT_MODEL_NAME}",
    commit_message=f"Upload split {SPLIT_NUMBER} model",
    token=HF_TOKEN
)

print(f"\n🎉 SUCCESS! Model uploaded to: https://huggingface.co/{HF_USERNAME}/{OUTPUT_MODEL_NAME}")
print(f"\n✅ System {SPLIT_NUMBER} Complete!")
print("\n📋 Next Steps:")
print(f"   1. Check System 1 status")
print(f"   2. Run System 3 on a third computer")
print(f"   3. Ensemble all 3 models for best results")
