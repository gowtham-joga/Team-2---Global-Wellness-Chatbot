# train_nlu.py
import yaml, re, json
import torch
import numpy as np
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModel, TrainingArguments, Trainer, DataCollatorWithPadding
from torch.nn import CrossEntropyLoss
from functools import partial
import seqeval.metrics
from sklearn.metrics import accuracy_score

# -------------------------
# Step 1: Parse Rasa-style nlu.yml
# -------------------------
def parse_nlu_data(file_path="nlul.yml"):
    """
    Parses the Rasa NLU YAML file to extract text, intent, and entities.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    processed = []
    for item in data.get("nlu", []):
        intent = item.get("intent")
        examples_block = item.get("examples", "")
        examples = [line.strip() for line in examples_block.splitlines() if line.strip()]
        
        for ex in examples:
            if ex.startswith("- "):
                ex = ex[2:].strip()
            
            clean = ""
            entities = []
            last_idx = 0
            for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', ex):
                s, e = m.span()
                ent_text = m.group(1)
                ent_label = m.group(2)
                clean += ex[last_idx:s]
                ent_start = len(clean)
                clean += ent_text
                ent_end = len(clean)
                entities.append({"text": ent_text, "label": ent_label, "start": ent_start, "end": ent_end})
                last_idx = e
            clean += ex[last_idx:]
            processed.append({"text": clean.strip(), "intent": intent, "entities": entities})
    return processed

# -------------------------
# Step 2: labels and tokenizer alignment
# -------------------------
def setup_labels(data):
    """Create mappings for intent and NER labels."""
    unique_intents = sorted(list({d["intent"] for d in data}))
    intent2id = {l: i for i, l in enumerate(unique_intents)}
    
    unique_ner = sorted(list({ent["label"] for d in data for ent in d["entities"]}))
    ner_bio = ["O"]
    for t in unique_ner:
        ner_bio.append(f"B-{t}")
        ner_bio.append(f"I-{t}")
    ner2id = {t: i for i, t in enumerate(ner_bio)}
    
    return intent2id, ner2id

def tokenize_and_align_labels(examples, tokenizer, intent2id, ner2id, max_length=128):
    """Tokenize text and align NER labels using the BIO scheme."""
    texts = examples["text"]
    tokenized = tokenizer(texts, truncation=True, padding="max_length", max_length=max_length, return_offsets_mapping=True)
    
    all_ner = []
    all_intent = []

    for i, offsets in enumerate(tokenized["offset_mapping"]):
        ner_labels = [ner2id["O"]] * len(offsets)
        ents = examples["entities"][i]
        
        for ent in ents:
            s_char = ent["start"]
            e_char = ent["end"]
            label = ent["label"]
            
            token_start = -1
            for idx, (off_s, off_e) in enumerate(offsets):
                if off_s == off_e == 0: continue # Skip padding/special tokens
                if off_s >= s_char:
                    token_start = idx
                    break

            token_end = -1
            for idx, (off_s, off_e) in reversed(list(enumerate(offsets))):
                 if off_s == off_e == 0: continue
                 if off_e <= e_char:
                     token_end = idx
                     break

            if token_start != -1 and token_end != -1 and token_start <= token_end:
                 ner_labels[token_start] = ner2id.get(f"B-{label}", ner2id["O"])
                 for t in range(token_start + 1, token_end + 1):
                     ner_labels[t] = ner2id.get(f"I-{label}", ner2id["O"])

        final_labels = []
        for (off_s, off_e), lab in zip(offsets, ner_labels):
            if off_s == off_e == 0:
                final_labels.append(-100)
            else:
                final_labels.append(lab)
        
        all_ner.append(final_labels)
        all_intent.append(intent2id[examples["intent"][i]])
        
    tokenized.pop("offset_mapping", None)
    tokenized["ner_labels"] = all_ner
    tokenized["intent_label"] = all_intent
    return tokenized

# -------------------------
# Step 3: Model
# -------------------------
class JointIntentAndNerModel(torch.nn.Module):
    def __init__(self, model_name, num_intent_labels, num_ner_labels, dropout_prob=0.1):
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        self.dropout = torch.nn.Dropout(dropout_prob)
        hidden = self.bert.config.hidden_size
        self.ner_classifier = torch.nn.Linear(hidden, num_ner_labels)
        self.intent_classifier = torch.nn.Linear(hidden, num_intent_labels)

    def forward(self, input_ids, attention_mask=None, **kwargs):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
        seq_out = outputs.last_hidden_state
        pooled = seq_out[:, 0, :]
        
        seq_out = self.dropout(seq_out)
        pooled = self.dropout(pooled)
        
        ner_logits = self.ner_classifier(seq_out)
        intent_logits = self.intent_classifier(pooled)
        return intent_logits, ner_logits

# -------------------------
# Step 4: Trainer
# -------------------------
class JointTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        intent_labels = inputs.pop("intent_label")
        ner_labels = inputs.pop("ner_labels")
        
        intent_logits, ner_logits = model(**inputs)
        
        loss_fct = CrossEntropyLoss()
        intent_loss = loss_fct(intent_logits.view(-1, intent_logits.shape[-1]), intent_labels.view(-1))
        
        ner_loss = 0
        active_loss = ner_labels.view(-1) != -100
        if active_loss.sum() > 0:
            active_logits = ner_logits.view(-1, ner_logits.shape[-1])[active_loss]
            active_labels = ner_labels.view(-1)[active_loss]
            ner_loss = loss_fct(active_logits, active_labels)
            
        total_loss = intent_loss + ner_loss
        
        return (total_loss, (intent_logits, ner_logits)) if return_outputs else total_loss

# -------------------------
# Step 5: Data Collator
# -------------------------
class JointDataCollator(DataCollatorWithPadding):
    def __call__(self, features):
        input_features = [{"input_ids": f["input_ids"], "attention_mask": f["attention_mask"]} for f in features]
        batch = self.tokenizer.pad(input_features, padding=self.padding, return_tensors="pt")
        
        max_len = batch["input_ids"].shape[1]
        
        ner_padded = []
        for f in features:
            nl = f.get("ner_labels", [])
            pad_len = max_len - len(nl)
            ner_padded.append(nl + [-100] * pad_len)

        batch["ner_labels"] = torch.tensor(ner_padded, dtype=torch.long)
        batch["intent_label"] = torch.tensor([f["intent_label"] for f in features], dtype=torch.long)
        
        return batch

# -------------------------
# Main execution
# -------------------------
if __name__ == "__main__":
    MODEL_NAME = "distilbert-base-uncased"
    OUTPUT_DIR = "nlu_model"

    print("Step 1: Parse NLU")
    raw = parse_nlu_data("nlul.yml") 
    intent2id, ner2id = setup_labels(raw)
    id2intent = {v:k for k,v in intent2id.items()}
    id2ner = {v:k for k,v in ner2id.items()}

    ds = Dataset.from_list(raw)
    split = ds.train_test_split(test_size=0.2, seed=42)
    ds_dict = DatasetDict({"train": split["train"], "test": split["test"]})
    print("Dataset sizes:", len(ds_dict["train"]), len(ds_dict["test"]))

    print("Step 2: Tokenize & align")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenize_fn = partial(tokenize_and_align_labels, tokenizer=tokenizer, intent2id=intent2id, ner2id=ner2id)
    tokenized = ds_dict.map(tokenize_fn, batched=True, batch_size=8, remove_columns=ds.column_names)
    print("Tokenized keys:", list(tokenized["train"].features.keys()))

    print("Step 3: Build model & trainer")
    model = JointIntentAndNerModel(model_name=MODEL_NAME, num_intent_labels=len(intent2id), num_ner_labels=len(ner2id))

    # --- CORRECTED & SIMPLIFIED TRAINING ARGUMENTS ---
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        logging_steps=100,
        # The 'save_strategy' argument tells the trainer when to save model checkpoints.
        # We set it to "epoch" to save at the end of each training cycle.
        save_strategy="epoch",
        weight_decay=0.01,
        logging_dir="./logs",
        fp16=False,
        remove_unused_columns=False,
        report_to=[]
    )
    
    trainer = JointTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"], 
        tokenizer=tokenizer,
        data_collator=JointDataCollator(tokenizer=tokenizer),
        # Removed the compute_metrics function as it's not used without evaluation
    )

    print("Step 4: Train")
    trainer.train()

    print("Step 5: Save model and maps")
    final_model_path = f"{OUTPUT_DIR}/final_model"
    trainer.save_model(final_model_path)
    with open(f"{final_model_path}/intent2id.json", "w", encoding="utf-8") as f:
        json.dump(intent2id, f, indent=2)
    with open(f"{final_model_path}/ner2id.json", "w", encoding="utf-8") as f:
        json.dump(ner2id, f, indent=2)

    print("Done. Model saved to", final_model_path)