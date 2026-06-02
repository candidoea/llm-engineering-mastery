"""
metrics.py — KPIs de execução do Scraper Doctor.

Coleta e exibe métricas de performance e qualidade a cada execução.
Referência arquitetural: DA-03 (dois modelos por fase).
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RunMetrics:
    """Métricas coletadas durante uma execução completa."""

    # Tempo
    started_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    total_time_s: float = 0.0
    crawl_time_s: float = 0.0
    llm_time_s: float = 0.0

    # LLM
    tokens_prompt: int = 0
    tokens_completion: int = 0
    llm_calls: int = 0
    model_diagnose: str = ""
    model_fix: str = ""

    # Seletores
    selectors_total: int = 0
    selectors_ok: int = 0
    selectors_broken: int = 0
    selectors_fixed: int = 0

    # Etapas
    stages_attempted: int = 0
    stages_completed: int = 0
    stages_failed: int = 0
    retries_total: int = 0

    @property
    def fix_rate_pct(self) -> float:
        """Proporção de seletores corrigidos com sucesso."""
        if self.selectors_broken == 0:
            return 100.0
        return round(self.selectors_fixed / self.selectors_broken * 100, 1)

    @property
    def tokens_total(self) -> int:
        return self.tokens_prompt + self.tokens_completion

    @property
    def llm_pct_of_total(self) -> float:
        """Proporção do tempo total gasto em inferência LLM."""
        if self.total_time_s == 0:
            return 0.0
        return round(self.llm_time_s / self.total_time_s * 100, 1)

    def report(self) -> str:
        """Gera relatório de KPIs formatado para o terminal."""

        lines = [
            "",
            "╔══════════════════════════════════════════════════╗",
            "║              SCRAPER DOCTOR — KPIs               ║",
            "╠══════════════════════════════════════════════════╣",
            f"║  Iniciado em:        {self.started_at:<27}║",
            "╠══════════════════════════════════════════════════╣",
            "║  TEMPO                                           ║",
            f"║  Total:              {self.total_time_s:>8.1f}s                     ║",
            f"║  Navegação (crawl):  {self.crawl_time_s:>8.1f}s                     ║",
            f"║  Inferência (LLM):   {self.llm_time_s:>8.1f}s  ({self.llm_pct_of_total:>5.1f}% do total)  ║",
            "╠══════════════════════════════════════════════════╣",
            "║  LLM                                             ║",
            f"║  Chamadas:           {self.llm_calls:>8d}                     ║",
            f"║  Tokens enviados:    {self.tokens_prompt:>8d}                     ║",
            f"║  Tokens gerados:     {self.tokens_completion:>8d}                     ║",
            f"║  Tokens total:       {self.tokens_total:>8d}                     ║",
            f"║  Modelo (diagnóstico): {self.model_diagnose:<25}║",
            f"║  Modelo (correção):    {self.model_fix:<25}║",
            "╠══════════════════════════════════════════════════╣",
            "║  SELETORES                                       ║",
            f"║  Total extraídos:    {self.selectors_total:>8d}                     ║",
            f"║  Válidos (estático): {self.selectors_ok:>8d}                     ║",
            f"║  Quebrados:          {self.selectors_broken:>8d}                     ║",
            f"║  Corrigidos (LLM):   {self.selectors_fixed:>8d}                     ║",
            f"║  Taxa de correção:   {self.fix_rate_pct:>7.1f}%                     ║",
            "╠══════════════════════════════════════════════════╣",
            "║  ETAPAS DO FLUXO                                 ║",
            f"║  Tentadas:           {self.stages_attempted:>8d}                     ║",
            f"║  Concluídas:         {self.stages_completed:>8d}                     ║",
            f"║  Falhas:             {self.stages_failed:>8d}                     ║",
            f"║  Retentativas:       {self.retries_total:>8d}                     ║",
            "╚══════════════════════════════════════════════════╝",
        ]

        return "\n".join(lines)

    def save(self, path: str) -> None:
        """Salva o relatório de KPIs em arquivo."""
        import json
        from pathlib import Path

        data = {
            "started_at": self.started_at,
            "time": {
                "total_s": self.total_time_s,
                "crawl_s": self.crawl_time_s,
                "llm_s": self.llm_time_s,
                "llm_pct": self.llm_pct_of_total,
            },
            "llm": {
                "calls": self.llm_calls,
                "tokens_prompt": self.tokens_prompt,
                "tokens_completion": self.tokens_completion,
                "tokens_total": self.tokens_total,
                "model_diagnose": self.model_diagnose,
                "model_fix": self.model_fix,
            },
            "selectors": {
                "total": self.selectors_total,
                "ok": self.selectors_ok,
                "broken": self.selectors_broken,
                "fixed": self.selectors_fixed,
                "fix_rate_pct": self.fix_rate_pct,
            },
            "stages": {
                "attempted": self.stages_attempted,
                "completed": self.stages_completed,
                "failed": self.stages_failed,
                "retries": self.retries_total,
            },
        }

        Path(path).write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
