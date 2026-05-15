from dataclasses import dataclass
from collections import Counter

from services.config import AGENT_EVENT_LIMIT

MAX_HISTORY_MESSAGES = 8


@dataclass(frozen=True)
class AgentProfile:
    name: str
    role: str
    goal: str


AGENT_PROFILE = AgentProfile(
    name="Agente AgroVision",
    role="triagem operacional de eventos",
    goal="Analisar detecções recentes, explicar riscos e sugerir a próxima ação.",
)

_SYSTEM_PROMPT = (
    f"Você é o {AGENT_PROFILE.name}, um agente de {AGENT_PROFILE.role}. "
    f"Objetivo: {AGENT_PROFILE.goal} "
    "Trate os dados como monitoramento operacional autorizado de ambiente real. "
    "Responda em português do Brasil, de forma direta e útil. "
    "Use apenas os eventos fornecidos como fonte. "
    "Não invente dados que não aparecem no contexto. "
    "Não tente identificar pessoas; fale apenas sobre eventos, riscos e próximas ações. "
    "Quando fizer sentido, organize a resposta em: Leitura, Risco e Recomendação."
)


def build_event_context(events: list[dict]) -> str:
    if not events:
        return "Contexto operacional: nenhum evento registrado ainda."

    labels = [e["label"] for e in events]
    distribution = Counter(labels)
    avg_conf = sum(e["confidence"] for e in events) / len(events)

    lines = [
        "Contexto operacional para o agente:",
        f"- Eventos considerados: {len(events)}",
        f"- Evento mais recente: {events[0]['label']} em {events[0]['event_time']}",
        f"- Distribuição: {', '.join(f'{k}: {v}' for k, v in distribution.most_common())}",
        f"- Confiança média: {avg_conf:.2f}",
        "Eventos recentes:",
    ]
    for e in events[:8]:
        lines.append(f"  - {e['event_time']} | {e['label']} ({e['confidence']:.0%})")

    return "\n".join(lines)


def normalize_history(history: list) -> list[dict]:
    result = []
    for msg in history:
        if hasattr(msg, "role"):
            result.append({"role": msg.role, "content": msg.content})
        elif isinstance(msg, dict):
            result.append(msg)
    return result[-MAX_HISTORY_MESSAGES:]


def build_agent_messages(question: str, history: list, events: list[dict]) -> list[dict]:
    system_content = _SYSTEM_PROMPT + "\n\n" + build_event_context(events)
    return [
        {"role": "system", "content": system_content},
        *normalize_history(history),
        {"role": "user",   "content": question},
    ]


def agent_status(events: list[dict]) -> dict:
    return {
        "name":              AGENT_PROFILE.name,
        "role":              AGENT_PROFILE.role,
        "goal":              AGENT_PROFILE.goal,
        "events_in_context": len(events),
        "context_preview":   build_event_context(events),
    }
