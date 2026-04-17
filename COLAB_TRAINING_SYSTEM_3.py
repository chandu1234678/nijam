"""
SYSTEM 3 - Train on Assigned Dataset Splits
Copy this entire code into a single Colab cell
"""

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================
!pip install -q transformers datasets accelerate huggingface_hub torch scikit-learn==1.3.0

# ============================================================================
# IMPORTS
# ============================================================================
import os
import torch
import numpy as np
from datasets import ClassLabel
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from huggingface_hub import login
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# ============================================================================
# CONFIGURATION
# ============================================================================
HF_TOKEN = "your-hf-token"
HF_USERNAME = "Bharat2004"
MODEL_NAME = "microsoft/deberta-v3-base"
OUTPUT_MODEL_NAME = "fake-news-mega-split-3"
SPLIT_NUMBER = 3  # System id
TOTAL_SPLITS = 3

# Login to HuggingFace
login(token=HF_TOKEN, add_to_git_credential=False)

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

# Assign multiple dataset splits across 3 systems
SYSTEM_DATASET_MAP = {
    1: [1, 4],
    2: [2, 5],
    3: [3],
}

assigned_splits = SYSTEM_DATASET_MAP[SPLIT_NUMBER]
dataset_repos = [f"{HF_USERNAME}/fake-news-mega-split-{i}" for i in assigned_splits]

loaded_datasets = []
for repo in dataset_repos:
    print(f"   Loading: {repo}")
    loaded_datasets.append(load_dataset(repo, split="train", token=HF_TOKEN))

dataset = concatenate_datasets(loaded_datasets)

# Cast label to ClassLabel for stratification
if 'label' in dataset.column_names:
    dataset = dataset.cast_column('label', ClassLabel(num_classes=2))

print(f"\n✂️ Loaded splits: {assigned_splits}")
print(f"   Training on {len(dataset)} samples")

# Split into train/val using datasets
split_dataset = dataset.train_test_split(
    test_size=0.1, 
    seed=42,
    stratify_by_column='label'
)

train_dataset = split_dataset['train']
val_dataset = split_dataset['test']

print(f"   Train: {len(train_dataset)} samples")
print(f"   Val: {len(val_dataset)} samples")

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
    fp16=False,  # Disabled for DeBERTa v3 compatibility
    save_total_limit=2,
    report_to="none",
    push_to_hub=False,  # We'll push manually
)

# ============================================================================
# METRICS
# ============================================================================

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    accuracy = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average='binary', zero_division=0
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
model_card = f"""---
language: en
license: apache-2.0
tags:
- text-classification
- fake-news-detection
- fact-checking
datasets:
- {', '.join(dataset_repos)}
metrics:
- accuracy
- f1
model-index:
- name: {OUTPUT_MODEL_NAME}
  results:
  - task:
      type: text-classification
      name: Fake News Detection
    metrics:
    - type: accuracy
      value: {eval_results['eval_accuracy']:.4f}
    - type: f1
      value: {eval_results['eval_f1']:.4f}
---

# FactChecker DeBERTa - Split {SPLIT_NUMBER}

This model is part of a distributed training setup (Split {SPLIT_NUMBER}/{TOTAL_SPLITS}).

## Model Details
- **Base Model:** {MODEL_NAME}
- **Training Split:** {SPLIT_NUMBER} of {TOTAL_SPLITS}
- **Training Samples:** {len(train_dataset)}
- **Validation Samples:** {len(val_dataset)}

## Performance
- **Accuracy:** {eval_results['eval_accuracy']:.4f}
- **F1 Score:** {eval_results['eval_f1']:.4f}
- **Precision:** {eval_results['eval_precision']:.4f}
- **Recall:** {eval_results['eval_recall']:.4f}

## Usage
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("{HF_USERNAME}/{OUTPUT_MODEL_NAME}")
model = AutoModelForSequenceClassification.from_pretrained("{HF_USERNAME}/{OUTPUT_MODEL_NAME}")

text = "Your claim to fact-check"
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
outputs = model(**inputs)
prediction = outputs.logits.argmax(-1).item()
# 0 = Real, 1 = Fake
```

## Training Details
- Epochs: 2
- Batch Size: 8
- Learning Rate: 2e-5
- Mixed Precision: No (FP16 disabled for DeBERTa v3)
- GPU: T4 (Free Colab)

## Note
This is one of {TOTAL_SPLITS} models trained in parallel. For best results, ensemble all splits or use the final merged model.
"""

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
print("\n📋 All Systems Complete!")
print(f"   ✅ System 1: {HF_USERNAME}/fake-news-mega-split-1")
print(f"   ✅ System 2: {HF_USERNAME}/fake-news-mega-split-2")
print(f"   ✅ System 3: {HF_USERNAME}/fake-news-mega-split-3")
print("\n🎯 Next: Ensemble all 3 models for best results")
