# Trilha de Aprendizado: LLM Engineering Mastery

> Versão 1.0 | Referência persistente de estudo

---

## Princípio de Ordenação

A trilha respeita dependência epistêmica estrita: nenhum tópico é abordado sem que seus pré-requisitos matemáticos estejam consolidados. O critério de consolidação é implementação funcional, não leitura.

---

## Fase 0 — Fundamentos Matemáticos (Paralela ao Curso)

Execute esta fase em paralelo com as semanas 1-3 do curso. Não é pré-requisito bloqueante para começar, mas é pré-requisito bloqueante para a semana 6 em diante.

### 0.1 Álgebra Linear

**Por que importa para LLMs:** toda operação em transformers — projeções de query/key/value, embeddings, camadas lineares — é álgebra linear. Sem isso, attention é caixa-preta.

| Conceito | Implementação from scratch | Referência |
|----------|---------------------------|------------|
| Vetores, normas, produto interno | `math_linear_algebra/01_vectors.py` | Gilbert Strang, cap. 1 |
| Multiplicação matricial | `math_linear_algebra/02_matrix_ops.py` | — |
| Decomposição SVD | `math_linear_algebra/03_svd.py` | — |
| Autovalores e autovetores | `math_linear_algebra/04_eigendecomp.py` | — |
| PCA from scratch | `math_linear_algebra/05_pca.py` | — |

**Recurso principal:** [3Blue1Brown — Essence of Linear Algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab)

### 0.2 Cálculo Multivariável

**Por que importa:** backpropagation é cálculo aplicado a grafos computacionais. Sem dominar derivadas parciais e regra da cadeia, você não entende como parâmetros são atualizados.

| Conceito | Implementação | Referência |
|----------|---------------|------------|
| Derivadas parciais e gradiente | `math_calculus/01_gradients.py` | — |
| Regra da cadeia em grafos | `math_calculus/02_chain_rule.py` | — |
| Backprop manual (rede 2 camadas) | `math_calculus/03_manual_backprop.py` | Andrej Karpathy: micrograd |
| Autograd from scratch | `math_calculus/04_autograd.py` | — |

**Recurso principal:** [Andrej Karpathy — Neural Networks: Zero to Hero](https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ)

### 0.3 Probabilidade e Estatística

**Por que importa:** tokens são distribuições de probabilidade. Sampling, temperatura, top-p — tudo é estatística aplicada. RLHF e alinhamento dependem de teoria bayesiana.

| Conceito | Implementação | Referência |
|----------|---------------|------------|
| Distribuições discretas e contínuas | `math_probability/01_distributions.py` | — |
| Maximum Likelihood Estimation | `math_probability/02_mle.py` | — |
| Bayes e inferência posterior | `math_probability/03_bayesian.py` | — |
| Sampling: greedy, top-k, top-p, temperature | `math_probability/04_sampling_strategies.py` | — |

### 0.4 Teoria da Informação

**Por que importa:** a loss function de um LLM é cross-entropy. KL-divergence aparece em VAEs, RLHF (PPO) e alinhamento. Perplexidade é a métrica padrão de avaliação.

| Conceito | Implementação | Referência |
|----------|---------------|------------|
| Entropia de Shannon | `math_information_theory/01_entropy.py` | — |
| Cross-entropy e log-likelihood | `math_information_theory/02_cross_entropy.py` | — |
| KL-divergence | `math_information_theory/03_kl_divergence.py` | — |
| Perplexidade de modelos de linguagem | `math_information_theory/04_perplexity.py` | — |

---

## Fase 1 — Arquitetura Transformer (Semanas 1-2 do curso + aprofundamento)

### Papers obrigatórios (nesta ordem)

1. **Attention Is All You Need** (Vaswani et al., 2017) — o paper fundador
2. **BERT** (Devlin et al., 2018) — encoder-only, pré-treinamento
3. **GPT-2** (Radford et al., 2019) — decoder-only, language modeling
4. **Scaling Laws** (Kaplan et al., 2020) — como tamanho afeta performance

### Implementações progressivas

```
Semana 1-2 do curso → implementar em paralelo:
  - Tokenization from scratch (BPE manual)
  - Softmax e attention score from scratch
  - Multi-head attention com NumPy
  - Transformer decoder miniatura (GPT-nano)
```

---

## Fase 2 — RAG e Sistemas de Recuperação (Semana 5)

### Conceitos-chave

- Embeddings semânticos: o que representam geometricamente
- Produto interno como similaridade: por que funciona
- HNSW e FAISS: estruturas de índice para busca aproximada
- Re-ranking: cross-encoders vs bi-encoders
- Chunking strategies: tamanho, sobreposição, semântico

### Papers recomendados

- **Dense Passage Retrieval** (Karpukhin et al., 2020)
- **Retrieval-Augmented Generation** (Lewis et al., 2020)

---

## Fase 3 — Fine-tuning e Adaptação (Semanas 6-7)

### Sequência de aprendizado

1. Transfer learning: por que funciona (representações pré-treinadas)
2. Full fine-tuning: custo, risco de catastrophic forgetting
3. LoRA: decomposição de baixo rank, por que é eficiente
4. QLoRA: quantização + LoRA, viabilidade em hardware limitado

### Papers obrigatórios

- **LoRA** (Hu et al., 2021)
- **QLoRA** (Dettmers et al., 2023)
- **InstructGPT** (Ouyang et al., 2022) — base do RLHF

---

## Fase 4 — Agentes e Sistemas Autônomos (Semana 8)

### Conceitos

- ReAct: reasoning + acting em loop
- Tool use: function calling e MCP
- Memória: in-context vs external (RAG) vs episódica
- Multi-agent: orquestração, comunicação, delegação

### Papers recomendados

- **ReAct** (Yao et al., 2022)
- **Toolformer** (Schick et al., 2023)

---

## Recursos de Referência

### Livros

- *Deep Learning* — Goodfellow, Bengio, Courville (gratuito online)
- *Mathematics for Machine Learning* — Deisenroth, Faisal, Ong (gratuito online)
- *Speech and Language Processing* — Jurafsky & Martin (cap. 7-10)

### Cursos complementares

- [fast.ai — Practical Deep Learning](https://course.fast.ai)
- [CS224N — NLP with Deep Learning (Stanford)](https://web.stanford.edu/class/cs224n/)
- [Andrej Karpathy — Neural Networks: Zero to Hero](https://karpathy.ai/zero-to-hero.html)

### Repositórios de referência

- [karpathy/nanoGPT](https://github.com/karpathy/nanoGPT) — GPT mínimo, bem documentado
- [karpathy/micrograd](https://github.com/karpathy/micrograd) — autograd from scratch
- [huggingface/transformers](https://github.com/huggingface/transformers) — implementação de referência

---

## Critérios de Avanço

Antes de avançar de uma fase, valide:

- [ ] Implementação from scratch funcionando com testes passando
- [ ] Consegue derivar as equações principais sem consultar referência
- [ ] Notebook com experimento que demonstra a mecânica (não apenas que funciona)
- [ ] Consegue explicar por escrito em 3 parágrafos sem jargão desnecessário

O último critério é o mais rigoroso: se não consegue explicar, não consolidou.
