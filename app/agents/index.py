"""
Multi-Agent System — Healthy AI

Arsitektur:
                    ┌─────────────────────────────────┐
    Request ──────► │       agent_supervisor           │
                    │  (LangGraph StateGraph)          │
                    │                                  │
                    │  State: nama, berat, tinggi,     │
                    │         bmi_analysis,            │
                    │         personal_message,        │
                    │         next_agent, iteration    │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │   Routing Decision (LLM)         │
                    └──────┬───────────────┬──────────┘
                           │               │
               ┌───────────▼──┐     ┌──────▼──────────┐
               │ agent_bmi_   │     │ agent_messaging  │
               │ calculator   │     │                  │
               │              │     │ - Pesan personal │
               │ Tools:       │     │ - Motivasi       │
               │ - calc_bmi   │     │ - Rekomendasi    │
               │ - health_risk│     │   actionable     │
               └──────┬───────┘     └──────┬───────────┘
                      │                    │
                      └────────┬───────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │       Final Response             │
                    │  bmi_analysis + personal_message │
                    └─────────────────────────────────┘

Exports:
- run_supervisor(nama, berat_badan, tinggi_badan) -> dict
"""

from app.agents.agent_supervisor import run_supervisor

__all__ = ["run_supervisor"]
