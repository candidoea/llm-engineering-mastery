# Semana 6 — De ML Tradicional a DL a Fine-tuning de Fronteira

**Duração do curso:** 4h 47min  
**Intensidade matemática:** Muito alta — requer todo o módulo de fundamentos.

## Objetivos

- Entender transfer learning geometricamente (por que representações pré-treinadas generalizam)
- Implementar full fine-tuning e identificar catastrophic forgetting
- Derivar LoRA matematicamente antes de usar a biblioteca
- Executar QLoRA em modelo open-source

## A Matemática do LoRA

LoRA (Low-Rank Adaptation) congela os pesos originais $W_0$ e aprende uma atualização de baixo rank:

$$W = W_0 + \Delta W = W_0 + BA$$

onde $B \in \mathbb{R}^{d \times r}$, $A \in \mathbb{R}^{r \times k}$, e $r \ll \min(d, k)$.

O número de parâmetros treináveis cai de $d \times k$ para $r(d + k)$. Para $d=k=4096$ e $r=16$: de 16.7M para 131K parâmetros — redução de 99.2%.

**Notebook obrigatório:** `01_lora_from_scratch.ipynb` — implementação manual de LoRA antes de usar a biblioteca PEFT.

## Estrutura

```
notebooks/
  01_lora_from_scratch.ipynb       # Derivação e implementação manual
  02_qlora_setup.ipynb             # Quantização 4-bit + LoRA
  03_sft_training_loop.ipynb       # Loop de fine-tuning com trl
  04_evaluation_post_finetune.ipynb # Comparação antes/depois
  05_catastrophic_forgetting.ipynb  # Experimento: o que o modelo esquece
src/
  lora_layer.py     # Implementação LoRA from scratch
  trainer.py        # Wrapper de treinamento
  evaluator.py      # Métricas de avaliação
tests/
  test_lora_layer.py
```
