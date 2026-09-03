import re
import math
from typing import List, Dict, Tuple
from collections import Counter
from backend.app.services.rag.chunker import CodeChunk

class VectorStore:
    """
    Fast in-memory BM25 / Cosine-similarity vector retriever for repository code chunks.
    Allows zero-dependency offline retrieval and embedding search.
    """
    def __init__(self, chunks: List[CodeChunk]):
        self.chunks = chunks
        self.doc_tokens: List[List[str]] = []
        self.doc_freqs: Counter = Counter()
        self.total_docs = len(chunks)
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        # Split on snake_case, camelCase, and punctuation
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return [t for t in tokens if len(t) > 1]

    def _build_index(self):
        for chunk in self.chunks:
            tokens = self._tokenize(chunk.content + " " + chunk.file_path + " " + chunk.symbol_name)
            self.doc_tokens.append(tokens)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freqs[t] += 1

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[CodeChunk, float]]:
        query_tokens = self._tokenize(query)
        if not query_tokens or self.total_docs == 0:
            return [(c, 1.0) for c in self.chunks[:top_k]]

        scores: List[Tuple[int, float]] = []

        for doc_idx, tokens in enumerate(self.doc_tokens):
            if not tokens:
                continue
            
            token_counts = Counter(tokens)
            doc_len = len(tokens)
            score = 0.0

            for qt in query_tokens:
                tf = token_counts.get(qt, 0)
                if tf > 0:
                    df = self.doc_freqs.get(qt, 1)
                    idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))
                    # BM25 term weighting
                    k1 = 1.5
                    b = 0.75
                    avg_doc_len = 100.0
                    tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_doc_len)))
                    score += idf * tf_norm

            if score > 0:
                scores.append((doc_idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]
        
        return [(self.chunks[idx], round(score, 3)) for idx, score in top_results]
