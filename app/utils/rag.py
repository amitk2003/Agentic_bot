import faiss
import numpy as np

# Lazy load to avoid slowing down startup if RAG is never called
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        # all-MiniLM-L6-v2 is extremely fast, lightweight, and standard for RAG
        _embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedder

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Splits text into overlapping chunks to preserve context boundaries."""
    chunks = []
    start = 0
    text_len = len(text)
    
    # Very short texts don't need chunking
    if text_len <= chunk_size:
        return [text]
        
    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= text_len:
            break
        start += (chunk_size - overlap)
    return chunks

class RAGSearcher:
    def __init__(self, context: str):
        self.chunks = chunk_text(context)
        self.embedder = get_embedder()
        self.index = None
        self._build_index()

    def _build_index(self):
        if not self.chunks:
            return
            
        # Create embeddings for all chunks
        embeddings = self.embedder.encode(self.chunks, convert_to_numpy=True)
        
        # Initialize FAISS index for L2 distance (Euclidean)
        d = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(d)
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 4) -> str:
        """
        Searches the FAISS index for the chunks most semantically similar to the query.
        Returns the top_k chunks joined as a single context string.
        """
        if not self.chunks or not self.index:
            return ""
            
        # If there are fewer chunks than top_k, just return everything
        if len(self.chunks) <= top_k:
            return "\n\n...\n\n".join(self.chunks)
            
        # Encode the query
        q_emb = self.embedder.encode([query], convert_to_numpy=True)
        
        # Search the index
        distances, indices = self.index.search(q_emb, top_k)
        
        # Retrieve the relevant chunks, sorted by original order to preserve reading flow
        retrieved_indices = sorted([idx for idx in indices[0] if 0 <= idx < len(self.chunks)])
        
        results = []
        for idx in retrieved_indices:
            results.append(self.chunks[idx])
                
        return "\n\n...[gap]...\n\n".join(results)
