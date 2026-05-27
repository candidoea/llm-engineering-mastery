# Week 6 — De ML Tradicional a DL: Fine-tuning de Modelo de Fronteira

**Seção do curso:** Seção 6 — 27 aulas, 4h 47min

## O que o curso cobre

- Revisão de ML tradicional: regressão, classificação, tree-based models
- Deep Learning: redes neurais, backpropagation, otimização
- Transfer learning: por que funciona e quando usar
- Fine-tuning de um modelo de fronteira (OpenAI fine-tuning API)
- Curadoria de dados de treinamento: qualidade sobre quantidade
- Avaliação: comparar modelo fine-tunado vs base

## Atenção: esta semana usa Google Colab com GPU

Alguns notebooks rodam no Colab. Os links estão dentro de cada `dayN.ipynb`.

## Arquivos do curso

Notebooks `day1.ipynb` a `day5.ipynb` + `redemption_run.ipynb`, `redemption_train.ipynb`, `results.ipynb` (notebooks adicionais do projeto pricer).

## Minhas anotações e extensões

### Observações da semana

### Experimentos próprios

### Dúvidas para investigar

## Links úteis para esta semana

- [OpenAI Fine-tuning Guide](https://platform.openai.com/docs/guides/fine-tuning)
- [Weights & Biases](https://wandb.ai/) — monitoramento de treinamento
- Paper: [InstructGPT (Ouyang et al., 2022)](https://arxiv.org/abs/2203.02155)

## Aprofundamento — ver `00_deep_dive/math_calculus/`

Fine-tuning é otimização por gradiente descente. Para entender o que acontece nos bastidores:
- `00_deep_dive/math_calculus/01_gradients.ipynb` — derivadas e gradientes
- `00_deep_dive/math_calculus/03_manual_backprop.ipynb` — backprop manual em uma rede simples

Estes notebooks não são pré-requisitos para o curso, mas explicam *por que* o fine-tuning funciona e o que acontece quando dá errado (overfitting, catastrophic forgetting).
