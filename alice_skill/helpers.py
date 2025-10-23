import re

def normalize_spoken_token(tokens: list[str]) -> str:
    """
    Normalizes a list of spoken tokens into a canonical three-word string.
    - Lowercases all tokens.
    - Removes punctuation and extra spaces.
    - Replaces 'ё' with 'е'.
    - Replaces common Latin lookalike characters with Cyrillic equivalents.
    """
    normalized_words = []
    for token in tokens:
        # Lowercase
        word = token.lower()
        # Replace 'ё' with 'е'
        word = word.replace('ё', 'е')
        # Replace Latin lookalikes (basic set)
        word = word.replace('a', 'а').replace('e', 'е').replace('o', 'о').replace('p', 'р').replace('c', 'с').replace('x', 'х').replace('y', 'у')
        # Remove all non-Cyrillic characters (including punctuation, numbers, etc.)
        word = re.sub(r'[^а-я]', '', word)
        if word:
            normalized_words.append(word)
    return " ".join(normalized_words).strip()

def build_alice_response_payload(text, request_data):
    session_data = request_data['session']
    return {
        "response": {
            "text": text,
            "end_session": False
        },
        "session": {
            "session_id": session_data['session_id'],
            "user_id": session_data['user_id'],
        },
        "version": request_data['version']
    }
