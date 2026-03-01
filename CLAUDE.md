# BeermoneyClaude

## Descripción
Agente autónomo que trabaja en plataformas de beermoney (user testing, encuestas, microtareas) mientras duermes. Se ejecuta por la noche, completa lo que puede solo, y te deja una cola organizada con lo que necesita intervención humana.

## Documentación
- **MASTERPLAN.md** — Visión completa: arquitectura, DB schema, diseño, sprints
- **MEGA_PROMPT.md** — Prompts de ejecución sprint por sprint

## Stack
- **Engine:** Python 3.11+ con Playwright, loguru, rich, pydantic
- **Dashboard:** Next.js 15 + Tailwind CSS + shadcn/ui + TypeScript
- **Database:** Supabase (PostgreSQL)
- **Notifications:** Telegram Bot
- **Deploy:** Vercel (dashboard)

## Estructura del proyecto
```
BeermoneyClaude/
├── engine/           # Motor Python (agente autónomo)
│   ├── core/         # Browser, sessions, scheduler, queue
│   ├── plugins/      # Un plugin por plataforma
│   ├── profiler/     # Auto-fill de formularios
│   ├── notifier/     # Telegram + email monitor
│   ├── scorer/       # Scoring inteligente
│   └── data/         # Plataformas, sesiones, screenshots
├── dashboard/        # Next.js web dashboard
└── docs/             # Documentación
```

## Convenciones
- Python: type hints siempre, async/await para browser, loguru para logs
- TypeScript: strict mode, functional components, absolute imports con @/
- Selectores CSS: documentar en PLATFORM_FICHAS/ antes de codificar
- Commits: descriptivos, uno por tarea completada

## Comandos útiles
- `cd engine && pip install -r requirements.txt` → Instalar dependencias
- `playwright install chromium` → Instalar browser
- `python run.py --test-browser` → Test del browser
- `python run.py --night` → Modo agente nocturno
- `python run.py` → Menú interactivo

## Evitar
- Selectores CSS inventados (marcar con # TODO: VERIFY SELECTOR)
- Passwords en texto plano (usar Fernet encryption)
- Requests paralelos a la misma plataforma
- Fabricar respuestas de opinión en encuestas
- Commits sin verificar que el código funciona

## Orden de ejecución
1. Sprint 0: Setup repo + estructura
2. Sprint 1: Core engine (browser, sessions, plugins base)
3. Sprint 2: Profiler + Telegram + Email monitor
4. Sprint 3: Plugin Prolific (primera plataforma real)
5. Sprint 4+: Más plataformas + dashboard + scoring
