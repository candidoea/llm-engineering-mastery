# Semana 5 — RAG Avançado com Embeddings Vetoriais

**Duração do curso:** 5h 25min  
**Intensidade matemática:** Alta — requer `00_foundations/math_linear_algebra` concluído.

## Objetivos

- Implementar embedding de documentos from scratch (TF-IDF antes de dense embeddings)
- Construir pipeline de indexação e recuperação com FAISS
- Implementar chunking semântico (não apenas por tamanho fixo)
- Implementar re-ranking com cross-encoder
- Avaliar qualidade do RAG com métricas (MRR, Recall@k)

## Estrutura

```
notebooks/
  01_tfidf_retrieval_from_scratch.ipynb  # BM25/TF-IDF antes de dense
  02_dense_embeddings.ipynb              # sentence-transformers, geometria
  03_vector_index_faiss.ipynb            # HNSW, produto interno, cosine
  04_rag_pipeline.ipynb                  # Pipeline completo E2E
  05_rag_evaluation.ipynb                # Métricas de avaliação
src/
  chunker.py       # Estratégias de chunking
  retriever.py     # Abstração de retrieval (BM25 / dense / hybrid)
  reranker.py      # Re-ranking com cross-encoder
  rag_pipeline.py  # Orquestração completa
tests/
  test_chunker.py
  test_retriever.py
```

## Por que TF-IDF antes de embeddings densos?

Começar com TF-IDF explicita o problema que embeddings densos resolvem: similaridade lexical vs. semântica. "cão" e "cachorro" têm TF-IDF similarity zero e cosine similarity alta em modelos de embedding — esse contraste é o argumento mais claro para motivar o uso de dense retrieval.
