# Arquitecture

┌────────────────────────────┐
│        API (FastAPI)       │  ← Entrada
├────────────────────────────┤
│     Application Layer      │  ← Orquestra casos de uso
├────────────────────────────┤
│        Domain Layer        │  ← Regras puras
├────────────────────────────┤
│    Infrastructure Layer    │  ← AWS, DB, LLM
└────────────────────────────┘
