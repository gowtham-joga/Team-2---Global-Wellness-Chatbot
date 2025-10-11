# app/routers/chat.py

import sqlite3
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from thefuzz import fuzz
from deep_translator import GoogleTranslator

from .. import models, schemas, database
from .users import get_current_user
from nlu_loader import predict_nlu

# ---------------------------------
# Router & DB Path
# ---------------------------------
router = APIRouter(prefix="/chat", tags=["Chat"])
DB_PATH = "main_database.db"

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# -------------------------------
# Helper: Fetch response from KB
# -------------------------------
def _normalize(text: str) -> str:
    return (text or "").lower().strip(" ?.!").replace('"', "").replace("'", "")


def _generate_ngrams(tokens: list[str], n_max: int = 3) -> list[str]:
    """Generate contiguous n-grams up to n_max for the tokens list."""
    ngrams = []
    L = len(tokens)
    for n in range(1, min(n_max, L) + 1):
        for i in range(L - n + 1):
            ngrams.append(" ".join(tokens[i : i + n]))
    return ngrams


def get_response_from_kb(intent: str, entities: list[dict] | None) -> dict:
    """
    Try to fetch best response from KB using intent + improved fuzzy entity matching.
    Falls back to intent-only if no good entity match is found.
    """
    static_replies = {
        "greet": "Hello! How can I help you with your wellness questions today? 😊",
        "goodbye": "Goodbye! Take care and stay healthy.",
        "chitchat": "I am a wellness assistant, ready to help with your questions."
    }
    if intent in static_replies:
        return {"response": static_replies[intent], "status": "ok"}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    context = ""

    # --- Entity-based fuzzy matching (improved for multi-word entities) ---
    if entities:
        # Build a list of candidate strings from the NLU entities:
        cleaned_entities = []
        for e in entities:
            text = (e.get("text") or e.get("value") or "")
            text_norm = _normalize(text)
            if not text_norm:
                continue
            cleaned_entities.append(text_norm)
            # tokens and ngrams to help match multi-word entities and partial phrases
            tokens = text_norm.split()
            cleaned_entities.extend(_generate_ngrams(tokens, n_max=3))

        # also deduplicate
        cleaned_entities = list(dict.fromkeys(cleaned_entities))
        logger.debug(f"[KB MATCH] Looking for entities (expanded): {cleaned_entities} in intent '{intent}'")

        cursor.execute("""
            SELECT entity_value, response_text
            FROM knowledge_base
            WHERE intent = ? AND entity_value IS NOT NULL AND TRIM(entity_value) <> ''
        """, (intent,))
        possible_matches = cursor.fetchall()

        best_match_score, best_match_response, best_entity = 0, "", None

        for row in possible_matches:
            db_entity = _normalize(row["entity_value"])
            if not db_entity:
                continue

            # Compare against all expanded user entity forms
            for ent in cleaned_entities:
                # primary: token_set_ratio (handles reordering & multi-word)
                score_ts = fuzz.token_set_ratio(ent, db_entity)
                # secondary: partial_ratio to capture partial overlaps
                score_partial = fuzz.partial_ratio(ent, db_entity)
                # choose the stronger of both scoring methods for robustness
                score = max(score_ts, score_partial)
                logger.debug(f"[KB MATCH] '{ent}' vs '{db_entity}' => token_set={score_ts} partial={score_partial} => use={score}")

                if score > best_match_score:
                    best_match_score = score
                    best_match_response = row["response_text"]
                    best_entity = db_entity

        # Keep previous threshold but allow slightly more flexibility for partial matches
        if best_match_score >= 72:
            logger.debug(f"[KB MATCH] ✅ Best match: '{best_entity}' with score {best_match_score}")
            context = best_match_response
        else:
            logger.debug(f"[KB MATCH] ❌ No entity passed threshold (best={best_match_score})")

    # --- Intent-only fallback ---
    if not context:
        cursor.execute("""
            SELECT response_text
            FROM knowledge_base
            WHERE intent = ? AND (entity_value IS NULL OR TRIM(entity_value) = '')
        """, (intent,))
        result = cursor.fetchone()
        if result:
            conn.close()
            return {"response": result["response_text"], "status": "ok_intent_only"}

    conn.close()
    if context:
        return {"response": context, "status": "ok"}

    return {"response": "Sorry, I don’t have information about that yet.", "status": "not_found"}


# -------------------------------
# Helper: Disclaimer text
# -------------------------------
# Unified general disclaimer (neutral) + urgent disclaimer
GENERAL_DISCLAIMER = (
    "\n\n---\n\n"
    "⚠ Disclaimer: This information is provided for general informational purposes only.\n\n"
    "It is not tailored advice. For personalized guidance or professional advice, "
    "please consult a qualified expert."
)

URGENT_DISCLAIMER = (
    "\n\n---\n\n"
    "⚠ URGENT: This is not a substitute for emergency or professional care.\n\n"
    "If you are experiencing a medical emergency or severe symptoms, contact your local "
    "emergency services or a healthcare professional immediately."
)


def get_disclaimer(intent: str) -> str:
    if intent in ["greet", "goodbye", "chitchat", "fallback"]:
        return ""
    if intent in ["emergency_help", "ask_first_aid", "inform_symptom"]:
        return URGENT_DISCLAIMER
    return GENERAL_DISCLAIMER


# -------------------------------
# Main Chat Endpoint
# -------------------------------
@router.post("/", response_model=schemas.ChatResponse)
def handle_chat_message(
    request: schemas.ChatRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Translate Hindi → English for NLU (preserve original behaviour)
    message_for_nlu = request.message
    if request.language == "hi":
        try:
            message_for_nlu = GoogleTranslator(source="hi", target="en").translate(request.message)
        except Exception as e:
            logger.exception("Translation (hi->en) failed; falling back to original text.")
            message_for_nlu = request.message

    logger.debug(f"[DEBUG] Input to NLU: '{message_for_nlu}'")

    # NLU prediction
    nlu_result = predict_nlu(message_for_nlu)
    intent, entities = nlu_result.get("intent"), nlu_result.get("entities")

    logger.debug(f"[DEBUG] NLU predicted intent: '{intent}', entities: {entities}")

    # Handle fallback intent
    if intent == "fallback":
        response_text = (
            "I'm sorry, I couldn't find information on that topic right now."
        )
        unanswered = models.UnansweredQuestion(
            user_id=current_user.id, question_text=request.message
        )
        db.add(unanswered)
        db.commit()
    else:
        kb_result = get_response_from_kb(intent, entities)
        response_text = kb_result["response"]

        if kb_result["status"] == "ok_intent_only":
            response_text = (
                f"I have information about topics related to '{intent.replace('_', ' ')}', "
                "but I couldn't find details on that specific one. Could you rephrase?"
            )

    if not response_text:
        response_text = "Sorry, I don’t have information about that yet."

    # Add disclaimers
    final_response_en = response_text + get_disclaimer(intent)

    # Translate back to Hindi if needed
    final_response = final_response_en
    if request.language == "hi":
        try:
            final_response = GoogleTranslator(source="en", target="hi").translate(final_response_en)
        except Exception:
            logger.exception("Translation (en->hi) failed; returning English text.")
            final_response = final_response_en

    # Save chat history
    history_entry = models.ChatHistory(
        user_id=current_user.id,
        user_message=request.message,
        bot_response=final_response,
        intent=intent
    )
    db.add(history_entry)
    db.commit()

    return {"response": final_response, "intent": intent, "entities": entities}
