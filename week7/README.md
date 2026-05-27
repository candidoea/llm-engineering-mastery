# Week 7 — Fine-tune Open-Source para Competir com Modelo de Fronteira

**Seção do curso:** Seção 7 — 24 aulas, 4h

## O que o curso cobre

- QLoRA: quantização 4-bit + LoRA — fine-tune em hardware limitado
- PEFT (Parameter-Efficient Fine-Tuning): família de técnicas
- SFT (Supervised Fine-Tuning) com a biblioteca `trl`
- Curadoria de dados de treinamento para open-source
- Merge de adaptadores LoRA com o modelo base
- Deploy do modelo fine-tunado no HuggingFace Hub
- Comparação de performance: open-source fine-tunado vs GPT-4

## Atenção: semana de maior custo computacional

Esta semana usa Google Colab com GPU (T4 ou A100).  
Ed Donner menciona gastar ~$10 no Colab Pro para resultados melhores, mas o plano gratuito funciona.

## Arquivos do curso

Notebooks `day1.ipynb` a `day5.ipynb`.

## Minhas anotações e extensões

### Observações da semana

### Experimentos próprios

### Dúvidas para investigar

## Links úteis para esta semana

- [PEFT Library](https://huggingface.co/docs/peft)
- [TRL Library](https://huggingface.co/docs/trl)
- [bitsandbytes](https://github.com/bitsandbytes-foundation/bitsandbytes)
- Paper: [LoRA (Hu et al., 2021)](https://arxiv.org/abs/2106.09685)
- Paper: [QLoRA (Dettmers et al., 2023)](https://arxiv.org/abs/2305.14314)

## A matemática do LoRA (resumo)

LoRA congela os pesos originais $W_0$ e aprende uma atualização de baixo rank:

$$W = W_0 + \Delta W = W_0 + B \cdot A$$

onde $B \in \mathbb{R}^{d \times r}$, $A \in \mathbb{R}^{r \times k}$, com $r \ll \min(d, k)$.

Para $d = k = 4096$ e $r = 16$: de 16.7M para 131K parâmetros treináveis — redução de 99.2%.

Para a derivação completa e implementação from scratch, ver `00_deep_dive/architecture_transformers/`.
