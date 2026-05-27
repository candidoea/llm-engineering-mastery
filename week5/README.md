# Week 5 — RAG Avançado: Embeddings Vetoriais e Recuperação

**Seção do curso:** Seção 5 — 32 aulas, 5h 25min

## O que o curso cobre

- Embeddings: o que são, como são gerados, o que representam
- Vector databases: ChromaDB, FAISS, Pinecone, Qdrant
- Pipeline RAG completo: ingestão → chunking → indexação → recuperação → geração
- Chunking strategies: tamanho fixo, por sentença, semântico
- Re-ranking: melhorar a qualidade dos resultados recuperados
- Projeto: AI Knowledge Worker (Q&A sobre documentos da empresa)

## Arquivos do curso

Notebooks `day1.ipynb` a `day5.ipynb`.  
Esta semana tem o projeto mais robusto até aqui: um knowledge worker completo.

## Minhas anotações e extensões

### Observações da semana

### Experimentos próprios

### Dúvidas para investigar

## Links úteis para esta semana

- [ChromaDB](https://docs.trychroma.com/)
- [FAISS by Meta](https://faiss.ai/)
- [Sentence Transformers](https://www.sbert.net/)
- Paper: [Retrieval-Augmented Generation (Lewis et al., 2020)](https://arxiv.org/abs/2005.11401)
- Paper: [Dense Passage Retrieval (Karpukhin et al., 2020)](https://arxiv.org/abs/2004.04906)

## Aprofundamento — ver `00_deep_dive/math_linear_algebra/`

RAG depende de álgebra linear:
- **Cosine similarity** é o produto interno normalizado
- **HNSW** (o índice do FAISS) usa geometria de alta dimensão
- **Dimensionalidade maldita:** por que busca em alta dimensão é contraintuitiva

Se quiser entender por que cosine similarity funciona como medida de similaridade semântica, o notebook `00_deep_dive/math_linear_algebra/01_vectors_dot_product.ipynb` cobre isso from scratch.
