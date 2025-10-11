import json
import torch
import os
from transformers import AutoTokenizer
from train_nlu import JointIntentAndNerModel

BASE_MODEL_NAME = "distilbert-base-uncased"
FINAL_MODEL_DIR = os.path.join("nlu_model", "final_model")

# -------------------------------
# Load mappings
# -------------------------------
with open(os.path.join(FINAL_MODEL_DIR, "intent2id.json"), "r", encoding="utf-8") as f:
    intent2id = json.load(f)
id2intent = {v: k for k, v in intent2id.items()}

with open(os.path.join(FINAL_MODEL_DIR, "ner2id.json"), "r", encoding="utf-8") as f:
    ner2id = json.load(f)
id2ner = {v: k for k, v in ner2id.items()}

# -------------------------------
# Load tokenizer and model
# -------------------------------
nlu_tokenizer = AutoTokenizer.from_pretrained(FINAL_MODEL_DIR)

print("Loading NLU model...")
nlu_model = JointIntentAndNerModel(
    model_name=BASE_MODEL_NAME, 
    num_intent_labels=len(intent2id), 
    num_ner_labels=len(ner2id)
)

weights_path = os.path.join(FINAL_MODEL_DIR, "pytorch_model.bin")
if not os.path.exists(weights_path):
    weights_path = os.path.join(FINAL_MODEL_DIR, "model.safetensors")

if weights_path.endswith(".bin"):
    nlu_model.load_state_dict(torch.load(weights_path, map_location=torch.device('cpu')))
else:
    from safetensors.torch import load_file
    nlu_model.load_state_dict(load_file(weights_path, device="cpu"))

nlu_model.eval()
print("NLU model loaded successfully.")


# -------------------------------
# Prediction function
# -------------------------------
def predict_nlu(text: str) -> dict:
    print(f"\n[DEBUG] Input to NLU: '{text}'")

    inputs = nlu_tokenizer(
        text, 
        return_tensors="pt", 
        truncation=True, 
        padding=True, 
        max_length=128
    )

    with torch.no_grad():
        intent_logits, ner_logits = nlu_model(**inputs)

    # ---- Intent ----
    intent_id = torch.argmax(intent_logits, dim=-1).item()
    intent = id2intent.get(intent_id, "fallback")
    print(f"[DEBUG] Predicted intent: '{intent}' (id={intent_id})")

    # ---- NER ----
    ner_preds = torch.argmax(ner_logits, dim=-1).squeeze().tolist()
    if not isinstance(ner_preds, list):
        ner_preds = [ner_preds]

    tokens = nlu_tokenizer.convert_ids_to_tokens(inputs["input_ids"].squeeze())
    entities, current_tokens, current_label = [], [], None

    for token, label_id in zip(tokens, ner_preds):
        if token in [nlu_tokenizer.cls_token, nlu_tokenizer.sep_token, nlu_tokenizer.pad_token]:
            continue

        label = id2ner.get(label_id, "O")

        if label.startswith("B-"):
            if current_tokens:
                entity_text = nlu_tokenizer.convert_tokens_to_string(current_tokens)
                entities.append({"label": current_label, "text": entity_text})
                print(f"[DEBUG] Finalized entity: {current_label}='{entity_text}'")

            current_tokens, current_label = [token], label[2:]

        elif label.startswith("I-") and current_label == label[2:]:
            current_tokens.append(token)

        else:
            if current_tokens:
                entity_text = nlu_tokenizer.convert_tokens_to_string(current_tokens)
                entities.append({"label": current_label, "text": entity_text})
                print(f"[DEBUG] Finalized entity: {current_label}='{entity_text}'")

            current_tokens, current_label = [], None

    if current_tokens:
        entity_text = nlu_tokenizer.convert_tokens_to_string(current_tokens)
        entities.append({"label": current_label, "text": entity_text})
        print(f"[DEBUG] Finalized entity: {current_label}='{entity_text}'")

    print(f"[DEBUG] Extracted entities: {entities}")

    return {"intent": intent, "entities": entities}
