import os
import time

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EMBED_MODEL = "gemini-embedding-001"
GEN_MODEL = "gemini-3.8-flash"


def embed_texts(texts):
    """Embed a list of texts (keep it under ~90 per call on the free tier)."""
    res = None
    for attempt in range(5):
        try:
            res = client.models.embed_content(
                model=EMBED_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY", output_dimensionality=768
                ),
            )
            break
        except errors.ClientError as e:
            if getattr(e, "code", None) == 429 and attempt < 4:
                print("  rate limited, waiting 55s...")
                time.sleep(55)
            else:
                raise
    vecs = np.vstack([np.array(e.values, dtype=np.float32) for e in res.embeddings])
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs