# E:/WELLNESS/nlu_loader.py
import requests
import os
import json
import logging

logger = logging.getLogger(__name__)

# --- IMPORTANT: FILL THIS IN ---
HF_USERNAME = "Agoj" # <-- PUT YOUR USERNAME HERE
# --------------------------------
REPO_NAME = "global-wellness-chatbot-nlu"

API_URL = f"https://api-inference.huggingface.co/models/{HF_USERNAME}/{REPO_NAME}"
HF_TOKEN = os.environ.get("HF_TOKEN")
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def predict_nlu(text: str):
    payload = {"inputs": text}
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status() 
        predictions = response.json()

        intent = "fallback" 
        entities = []

        if predictions and isinstance(predictions, list):
            # This logic extracts entities and tries to infer a primary intent.
            # It may need to be adjusted based on your exact model's output.
            current_entities = {}
            for token in predictions:
                entity_group = token.get('entity_group')
                if entity_group != 'O':
                    word = token.get('word')
                    # Handle subwords starting with ##
                    if word.startswith('##'):
                        word = word[2:]

                    # Group subwords into a single entity
                    if entity_group in current_entities:
                        current_entities[entity_group] += word
                    else:
                        current_entities[entity_group] = word

            # Convert grouped entities to final format
            for entity, value in current_entities.items():
                entities.append({"entity": entity, "value": value})

            # Simple logic to guess intent from found entities
            if any(e['entity'] == 'DISEASE' for e in entities):
                intent = 'ask_disease_info'
            elif any(e['entity'] == 'SYMPTOM' for e in entities):
                intent = 'inform_symptom'
            elif any(e['entity'] in ['DIET', 'FOOD'] for e in entities):
                intent = 'ask_diet'
            elif any(e['entity'] == 'EXERCISE' for e in entities):
                intent = 'ask_exercise'

        logger.debug(f"HF Inference successful. Intent: {intent}, Entities: {entities}")
        return {"intent": intent, "entities": entities}

    except requests.exceptions.RequestException as e:
        logger.error(f"Hugging Face API request failed: {e}")
        logger.error(f"Response content: {response.content.decode() if response else 'No response'}")
        return {"intent": "fallback", "entities": []}
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from Hugging Face API. Response: {response.text}")
        return {"intent": "fallback", "entities": []}