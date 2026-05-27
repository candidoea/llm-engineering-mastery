# 00 — Deep Dive: Fundamentos Matemáticos

Esta pasta **não faz parte do curso do Ed Donner**. É uma extensão pessoal para dominar os fundamentos matemáticos que o curso usa mas não ensina.

O curso é focado em aplicação — e está certo nisso. Mas se o objetivo é se tornar um Engenheiro de LLMs que entende o que está fazendo (e não apenas como usar ferramentas), a matemática subjacente precisa ser consolidada separadamente.

---

## Organização

### `math_linear_algebra/`
**Relevância para LLMs:** embeddings são vetores; attention é produto interno matricial; PCA e SVD aparecem em interpretabilidade e compressão de modelos.

| Notebook | Conteúdo |
|----------|----------|
| `01_vectors_dot_product.ipynb` | Vetores, normas, produto interno — a geometria da similaridade |
| `02_matrix_multiplication.ipynb` | Multiplicação matricial como operação de atenção em paralelo |
| `03_svd_and_pca.ipynb` | SVD, PCA — compressão de representações |
| `04_eigenvalues.ipynb` | Autovalores e autovetores |

### `math_calculus/`
**Relevância para LLMs:** fine-tuning é otimização por gradiente; backpropagation é regra da cadeia em grafos computacionais.

| Notebook | Conteúdo |
|----------|----------|
| `01_derivatives_gradients.ipynb` | Derivadas parciais, gradiente, Jacobiano |
| `02_chain_rule_graph.ipynb` | Regra da cadeia em grafos computacionais |
| `03_manual_backprop.ipynb` | Backprop manual em MLP de 2 camadas |
| `04_autograd_scratch.ipynb` | Autograd from scratch (estilo micrograd) |

### `math_probability/`
**Relevância para LLMs:** tokens são distribuições de probabilidade; temperatura, top-p e top-k são operações sobre distribuições.

| Notebook | Conteúdo |
|----------|----------|
| `01_distributions.ipynb` | Distribuições discretas e contínuas |
| `02_mle.ipynb` | Maximum Likelihood Estimation |
| `03_sampling_strategies.ipynb` | Greedy, top-k, top-p, temperatura — from scratch |

### `math_information_theory/`
**Relevância para LLMs:** cross-entropy é a loss function de todo LLM; KL-divergence aparece em RLHF; perplexidade é a métrica padrão de avaliação.

| Notebook | Conteúdo |
|----------|----------|
| `01_entropy.ipynb` | Entropia de Shannon |
| `02_cross_entropy_loss.ipynb` | Cross-entropy como loss de LLMs — derivação |
| `03_kl_divergence.ipynb` | KL-divergence e sua aplicação em RLHF |
| `04_perplexity.ipynb` | Perplexidade — interpretação e cálculo |

### `architecture_transformers/`
**Relevância para LLMs:** implementar o mecanismo de atenção from scratch consolida tudo acima em um único objeto.

| Notebook | Conteúdo |
|----------|----------|
| `01_attention_from_scratch.ipynb` | Scaled dot-product attention sem bibliotecas |
| `02_multihead_attention.ipynb` | Multi-head attention com NumPy |
| `03_positional_encoding.ipynb` | RoPE e encodings absolutos |
| `04_gpt_nano.ipynb` | Decoder-only transformer mínimo treinável |
| `05_lora_from_scratch.ipynb` | LoRA implementado from scratch — conecta com week7 |

---

## Quando estudar isto

- **Paralelo ao curso:** `math_linear_algebra/` e `math_probability/` enquanto faz weeks 1-4
- **Antes de week 6:** `math_calculus/` e `math_information_theory/`
- **Antes ou depois de week 7:** `architecture_transformers/` — especialmente `05_lora_from_scratch.ipynb`

---

## Referências externas

- [3Blue1Brown — Essence of Linear Algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab)
- [Andrej Karpathy — Neural Networks: Zero to Hero](https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ)
- [karpathy/micrograd](https://github.com/karpathy/micrograd) — autograd from scratch em 100 linhas
- [karpathy/nanoGPT](https://github.com/karpathy/nanoGPT) — GPT mínimo bem documentado
