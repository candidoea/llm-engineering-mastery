# 00 — Fundamentos Matemáticos

Esta pasta contém as implementações *from scratch* da matemática que sustenta toda arquitetura de LLMs. É a base epistêmica do repositório: nada nas fases seguintes faz sentido completo sem o que está aqui.

## Organização

### `math_linear_algebra/`
Álgebra linear do zero. Implementações manuais antes de qualquer NumPy.

Sequência de estudo:
1. `01_vectors_from_scratch.ipynb` — vetores, normas, produto interno sem NumPy
2. `02_matrix_operations.ipynb` — multiplicação, transposição, inversa
3. `03_svd_and_pca.ipynb` — decomposição SVD, aplicação em compressão de embeddings
4. `04_eigenvalues.ipynb` — autovalores, autovetores, aplicação em PCA
5. `05_linear_algebra_in_transformers.ipynb` — como cada conceito aparece na atenção

### `math_calculus/`
Cálculo multivariável com foco em backpropagation.

Sequência:
1. `01_derivatives_and_gradients.ipynb` — derivadas parciais, gradiente, Jacobiano
2. `02_chain_rule_computation_graph.ipynb` — regra da cadeia em grafos
3. `03_manual_backprop_mlp.ipynb` — backprop à mão em um MLP de 2 camadas
4. `04_autograd_from_scratch.ipynb` — implementando autograd (estilo micrograd)

### `math_probability/`
Probabilidade e estatística para modelos de linguagem.

Sequência:
1. `01_probability_distributions.ipynb` — distribuições discretas e contínuas
2. `02_mle_and_map.ipynb` — estimação de máxima verossimilhança
3. `03_bayesian_inference.ipynb` — inferência bayesiana aplicada a NLP
4. `04_sampling_strategies.ipynb` — greedy, top-k, top-p, temperature from scratch

### `math_information_theory/`
Teoria da informação: a linguagem da loss function.

Sequência:
1. `01_entropy_and_information.ipynb` — entropia de Shannon, bits de informação
2. `02_cross_entropy_loss.ipynb` — derivação da cross-entropy como loss de LLMs
3. `03_kl_divergence.ipynb` — KL-divergence, aplicação em RLHF
4. `04_perplexity.ipynb` — perplexidade, interpretação e relação com cross-entropy

## Princípio de implementação

Cada notebook segue esta estrutura:
1. **Motivação** — por que este conceito importa especificamente para LLMs
2. **Derivação matemática** — equações com explicação de cada passo
3. **Implementação Python puro** — sem bibliotecas, para forçar entendimento
4. **Implementação NumPy** — vetorizada, mais eficiente
5. **Verificação** — comparação com resultado esperado ou referência
6. **Conexão com LLMs** — onde exatamente este conceito aparece na arquitetura
