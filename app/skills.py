"""Reusable skills: slash commands that expand into a ready-made prompt."""

SKILLS = {
    "brief": (
        "Today's daily brief",
        "Make my daily brief: first check my pending deadlines with get_schedule, then give my top 3 "
        "tasks for today, a time-boxed revision plan and one motivational line. {arg}",
    ),
    "plan": (
        "Study plan: /plan <topic or exam>",
        "Create a day-by-day study plan for '{arg}'. First check my notes with search_notes and my "
        "deadlines with get_schedule. Include topics, time and revision slots.",
    ),
    "career": (
        "Career advice: /career <goal>",
        "Give me a career roadmap for my goal '{arg}': skill gaps, a 30/60/90-day plan, 3 project ideas, "
        "and current market trends via web_search. Keep my profile from memory in mind.",
    ),
    "quiz": (
        "Quiz: /quiz <topic>",
        "Using my notes (search_notes), create 5 MCQs on '{arg}'. Give only the questions first and put "
        "the answers in a separate section at the end.",
    ),
    "summarize": (
        "Notes summary: /summarize <topic>",
        "Find my notes on '{arg}' with search_notes and give a short bullet-point summary.",
    ),
}


def expand(message):
    msg = message.strip()
    if not msg.startswith("/"):
        return message
    parts = msg[1:].split(maxsplit=1)
    name = parts[0].lower() if parts else ""
    arg = parts[1] if len(parts) > 1 else ""
    if name in SKILLS:
        return SKILLS[name][1].format(arg=arg).strip()
    return message


def catalog():
    return {k: v[0] for k, v in SKILLS.items()}
