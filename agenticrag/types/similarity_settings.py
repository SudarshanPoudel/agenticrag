from dataclasses import dataclass, field
from typing import Literal, Optional, List, Callable, Dict, Any

DistanceMetric = Literal[
    "default", # If backend doesn't support multiple strategies per query

    # Vector-based
    "cosine",        # Cosine similarity
    "dot_product",   # Inner product
    "euclidean",     # L2 distance
    "manhattan",     # L1 distance

    # Lexical / keyword-based
    "keyword",       # Simple term match
    "bm25",          # Okapi BM25
    "tfidf",         # Term Frequency–Inverse Document Frequency
    "jaccard",       # Jaccard similarity (set/overlap)
    "ngram_overlap", # n-gram overlap / character-level

    # Edit / fuzzy matching
    "edit_distance", # Levenshtein distance
    "hamming",       # Hamming distance
]

@dataclass
class RetrievalStep:
    strategy: DistanceMetric = "default"
    top_k: int = 5                        
    min_score: Optional[float] = None  
    include_duplicates: bool = False   # allow chunks already seen in earlier steps
    reranker: Optional[Callable] = None  # rerank results *within this step*
    additional_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SimilaritySettings:
    steps: List[RetrievalStep]         
    global_reranker: Optional[Callable] = None  
    final_top_k: Optional[int] = None 
    global_sort_order: Literal["asc", "desc", "llm_preferred"] = "asc"
    additional_global_params: Dict[str, Any] = field(default_factory=dict)
