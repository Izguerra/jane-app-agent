import re

def split_into_sentence_chunks(text: str, limit: int = 1500) -> list[str]:
    """Splits a long message into sentence-aware chunks under the character limit."""
    # Split by common sentence endings (keep the ending characters)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= limit:
            current_chunk = (current_chunk + " " + sentence).strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If a single sentence is still larger than the limit, hard-split it
            if len(sentence) > limit:
                temp_sentence = sentence
                while len(temp_sentence) > limit:
                    chunks.append(temp_sentence[:limit])
                    temp_sentence = temp_sentence[limit:]
                current_chunk = temp_sentence
            else:
                current_chunk = sentence
                
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

# Test Cases
test_text = (
    "This is a short sentence. "
    "This is a medium sentence that contains some more information to fill up the space. "
    "This is a very long sentence " + ("that repeats " * 200) + "to test the hard-split logic."
)

print(f"Original length: {len(test_text)}")
chunks = split_into_sentence_chunks(test_text, limit=300)
for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} (Length: {len(chunk)}) ---")
    print(f"[{chunk}]")

# Verify that no chunk exceeds limit
for chunk in chunks:
    assert len(chunk) <= 300
    
print("\nSuccess: Chunker logic verified.")
