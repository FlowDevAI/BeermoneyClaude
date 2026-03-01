# 🤖 BeermoneyClaude — MASTERPLAN

> **Proyecto:** BeermoneyClaude
> **Org:** FlowDevAI (https://github.com/FlowDevAI/BeermoneyClaude)
> **Autor:** Alex — FLOW DEV AI
> **Fecha:** Marzo 2026
> **Estado:** Pre-desarrollo

---

## 📋 ÍNDICE

1. [Visión del Producto](#1-visión-del-producto)
2. [Principios de Diseño](#2-principios-de-diseño)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Stack Tecnológico](#4-stack-tecnológico)
5. [Estructura del Repositorio](#5-estructura-del-repositorio)
6. [Base de Datos (Supabase)](#6-base-de-datos-supabase)
7. [Motor Python — Diseño Detallado](#7-motor-python--diseño-detallado)
8. [Dashboard Web — Diseño Detallado](#8-dashboard-web--diseño-detallado)
9. [Catálogo de Plataformas](#9-catálogo-de-plataformas)
10. [Fichas de Plataforma (Deep Research)](#10-fichas-de-plataforma-deep-research)
11. [Sprints de Ejecución](#11-sprints-de-ejecución)
12. [Variables de Entorno](#12-variables-de-entorno)
13. [Seguridad y Anti-Detección](#13-seguridad-y-anti-detección)
14. [Riesgos y Mitigaciones](#14-riesgos-y-mitigaciones)

---

## 1. Visión del Producto

### ¿Qué es?

Un agente autónomo que trabaja en plataformas de "beermoney" (user testing, encuestas, microtareas) de forma automática o semi-automática. Se ejecuta por la noche o en segundo plano, completa lo que puede solo, y te deja una cola organizada con lo que necesita intervención humana.

### ¿Qué NO es?

- No es un bot que fabrica respuestas falsas
- No es un sistema que miente en screeners
- No es un scraper agresivo que viola rate limits
- No es una herramienta para hacer trampas

### Filosofía

```
AUTOMÁTICO cuando es seguro:
  → Login, navegar, detectar tareas, aceptar slots,
    rellenar datos demográficos, reservar plazas

HUMANO cuando es necesario:
  → Tests de usabilidad con voz/webcam
  → Encuestas de opinión real
  → CAPTCHAs no resolubles
  → Cualquier cosa donde mentir = baneo

INTELIGENTE siempre:
  → Priorizar por ratio €/h real
  → Aprender de tus datos
  → Optimizar tu tiempo
```

### Resultado esperado

- **Sin el sistema:** Abres 15 webs cada día, revisas manualmente, pierdes oportunidades que se llenan en minutos, no sabes cuánto ganas realmente por hora en cada plataforma.
- **Con el sistema:** Te levantas, miras Telegram, ves "anoche reservé 3 plazas en Prolific y completé 2 screeners. Tienes 4 tareas en cola." Haces las tareas humanas en 1h, ganas 25€. El sistema trackea todo y te dice "deja ySense, no te renta."

---

## 2. Principios de Diseño

### 2.1 Profundidad antes que amplitud

Cada plataforma se desarrolla en su propio sprint con:
1. **Research**: navegar la web real, documentar flujos, capturar selectores
2. **Ficha**: documento detallado con todos los flujos, URLs, selectores, edge cases
3. **Código**: plugin completo con tests
4. **Test real**: ejecutar contra la plataforma real (modo visible, no headless)
5. **Ajuste**: corregir selectores que fallen, añadir edge cases
6. **Merge**: integrar al sistema principal

### 2.2 Conservador por defecto

Si hay duda → cola humana. Si detecta anti-bot → parar y alertar. NUNCA fabricar respuestas. NUNCA mentir en perfiles.

### 2.3 Recuperable

Si un plugin falla → los demás siguen. Si el browser crashea → restart automático. Si Supabase está caído → guardar local y sincronizar después.

### 2.4 Observable

Cada acción → log + screenshot. Cada decisión → razón documentada. Cada error → alerta + contexto. Dashboard → visión completa en tiempo real.

---

## 3. Arquitectura del Sistema

```
┌───────────────────────────────────────────────────────────────────┐
│                           TÚ (Alex)                               │
│                                                                    │
│   📱 Telegram Bot          🖥️ Dashboard (Vercel)     💻 Terminal  │
│   ├─ Alertas urgentes      ├─ Cola humana             ├─ run.py   │
│   ├─ /queue /stats /done   ├─ Earnings tracker        ├─ debug    │
│   └─ Morning report        ├─ Platform analytics      └─ manual   │
│                            └─ Agent control                       │
└──────────┬─────────────────────────┬──────────────────┬──────────┘
           │                         │                  │
           ▼                         ▼                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                         SUPABASE                                  │
│  platforms │ opportunities │ human_queue │ earnings │ agent_logs  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼─────────┐         ┌────────▼─────────┐
     │  PYTHON ENGINE    │         │  EMAIL MONITOR   │
     │  (Agente nocturno)│         │  (24/7 daemon)   │
     │  Playwright       │         │  Gmail IMAP      │
     │  Plugins x26      │         │  Parse + Notify  │
     │  Profiler         │         └──────────────────┘
     │  CAPTCHA Solver   │
     │  Scorer           │
     └──────────────────┘
```

### Flujo nocturno

```
23:00 → Agente arranca
  ├─→ Login en todas las plataformas (sesiones persistentes)
  ├─→ LOOP (hasta 07:00):
  │     ├── Cada 15 min: Scan Tier 1 (Prolific, Respondent, UserTesting)
  │     ├── Cada 30 min: Scan Tier 2
  │     └── Cada 60 min: Scan Tier 3-4
  │     Para cada tarea:
  │       ├── Score > 80 → AUTO-ACCEPT
  │       │     ├── Auto-completable → COMPLETAR → €€€
  │       │     └── Necesita humano → RESERVAR + COLA
  │       ├── Score 40-80 → ACCEPT + COLA
  │       └── Score < 40 → SKIP
  └─→ 07:00: Morning Report → Telegram
```

---

## 4. Stack Tecnológico

### Motor (Python)

| Componente | Librería | Para qué |
|-----------|----------|----------|
| Browser automation | playwright 1.49+ | Control de Chromium |
| Config | python-dotenv | Variables de entorno |
| CLI output | rich | Tablas, progress bars, colores |
| Logging | loguru | Logs estructurados |
| Telegram | python-telegram-bot 21+ | Bot de notificaciones |
| Scheduling | apscheduler | Cron jobs |
| Database | supabase-py | Conexión a Supabase |
| Encryption | cryptography | Fernet para credenciales |
| HTTP | httpx | Requests async |
| Data | pydantic 2+ | Validación de datos |
| Screenshots | Pillow | Procesamiento de imágenes |

### Dashboard (Next.js)

| Componente | Librería | Para qué |
|-----------|----------|----------|
| Framework | Next.js 15 (App Router) | Frontend |
| Styling | Tailwind CSS | Diseño |
| Components | shadcn/ui | UI components |
| Charts | Recharts | Gráficos |
| Database | @supabase/supabase-js | Cliente Supabase |
| Deploy | Vercel | Hosting |

---

## 5. Estructura del Repositorio

```
BeermoneyClaude/
├── README.md
├── .gitignore
├── .env.example
├── CLAUDE.md
│
├── engine/                            # Motor Python
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── run.py                         # Entry point
│   ├── setup_wizard.py
│   ├── core/
│   │   ├── config.py, browser.py, session.py
│   │   ├── scheduler.py, queue.py, db.py, logger.py
│   ├── plugins/
│   │   ├── base.py                    # Abstract plugin
│   │   ├── prolific.py, clickworker.py, usertesting.py...
│   ├── profiler/
│   │   ├── profile_data.py, form_filler.py, screener_bot.py
│   ├── notifier/
│   │   ├── telegram_bot.py, email_monitor.py, alerts.py
│   ├── scorer/
│   │   ├── opportunity.py, optimizer.py
│   ├── data/
│   │   ├── platforms.json, sessions/, screenshots/
│   ├── tests/
│   └── docs/PLATFORM_FICHAS/
│
├── dashboard/                         # Next.js
│   ├── src/app/ (home, queue, earnings, platforms, analytics, agent)
│   ├── src/components/
│   ├── src/lib/supabase/
│   └── src/hooks/
│
└── docs/
    ├── MASTERPLAN.md
    └── MEGA_PROMPT.md
```

---

## 6. Base de Datos (Supabase)

### 6.1 Tabla: platforms

```sql
CREATE TABLE platforms (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    login_url TEXT,
    dashboard_url TEXT,
    category TEXT NOT NULL,
    tier INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 4),
    avg_pay_min DECIMAL(8,2),
    avg_pay_max DECIMAL(8,2),
    currency TEXT DEFAULT 'EUR',
    payment_methods TEXT[],
    frequency TEXT,
    spain_available BOOLEAN DEFAULT true,
    plugin_status TEXT DEFAULT 'planned',
    active BOOLEAN DEFAULT false,
    check_interval_seconds INTEGER DEFAULT 1800,
    last_scanned_at TIMESTAMPTZ,
    last_task_found_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    login_status TEXT DEFAULT 'unknown',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.2 Tabla: opportunities

```sql
CREATE TABLE opportunities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    platform_id UUID REFERENCES platforms(id),
    source TEXT NOT NULL,
    external_id TEXT,
    title TEXT,
    description TEXT,
    estimated_pay DECIMAL(8,2),
    currency TEXT DEFAULT 'EUR',
    estimated_minutes INTEGER,
    effective_hourly_rate DECIMAL(8,2),
    url TEXT,
    priority TEXT DEFAULT 'medium',
    score INTEGER CHECK (score BETWEEN 0 AND 100),
    score_breakdown JSONB,
    difficulty TEXT DEFAULT 'human',
    status TEXT DEFAULT 'detected',
    agent_action TEXT,
    needs_human BOOLEAN DEFAULT true,
    human_reason TEXT,
    human_instructions TEXT,
    deadline TIMESTAMPTZ,
    screenshot_path TEXT,
    email_subject TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_platform ON opportunities(platform_id);
```

### 6.3 Tabla: human_queue

```sql
CREATE TABLE human_queue (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    opportunity_id UUID REFERENCES opportunities(id),
    platform_slug TEXT NOT NULL,
    task_title TEXT NOT NULL,
    estimated_pay DECIMAL(8,2),
    currency TEXT DEFAULT 'EUR',
    url TEXT,
    reason TEXT NOT NULL,
    instructions TEXT,
    deadline TIMESTAMPTZ,
    urgency TEXT DEFAULT 'medium',
    screenshot_path TEXT,
    status TEXT DEFAULT 'pending',
    actual_earnings DECIMAL(8,2),
    actual_minutes INTEGER,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.4 Tabla: earnings

```sql
CREATE TABLE earnings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    platform_id UUID REFERENCES platforms(id),
    opportunity_id UUID REFERENCES opportunities(id),
    amount DECIMAL(8,2) NOT NULL,
    currency TEXT DEFAULT 'EUR',
    amount_eur DECIMAL(8,2),
    task_type TEXT,
    task_description TEXT,
    time_spent_minutes INTEGER,
    effective_hourly_rate DECIMAL(8,2),
    completed_by TEXT DEFAULT 'human',
    payment_status TEXT DEFAULT 'pending',
    payment_date DATE,
    notes TEXT,
    completed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.5 Tabla: agent_logs

```sql
CREATE TABLE agent_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT,
    event_type TEXT NOT NULL,
    platform_slug TEXT,
    level TEXT DEFAULT 'info',
    message TEXT,
    details JSONB,
    screenshot_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.6 Tabla: daily_stats

```sql
CREATE TABLE daily_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    total_earned_eur DECIMAL(8,2) DEFAULT 0,
    total_time_minutes INTEGER DEFAULT 0,
    effective_hourly_rate DECIMAL(8,2),
    tasks_completed INTEGER DEFAULT 0,
    tasks_by_agent INTEGER DEFAULT 0,
    tasks_by_human INTEGER DEFAULT 0,
    opportunities_detected INTEGER DEFAULT 0,
    platforms_scanned INTEGER DEFAULT 0,
    best_platform TEXT,
    best_hourly_rate DECIMAL(8,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 7. Motor Python — Diseño Detallado

Ver MEGA_PROMPT.md para implementación completa de:
- BrowserManager (Playwright con comportamiento humano)
- SessionManager (login + persistencia de cookies)
- PlatformPlugin (clase abstracta base)
- NightAgent (loop principal)
- HumanQueue (cola de tareas)

---

## 8. Dashboard Web — Diseño Detallado

### Páginas

| Página | Contenido |
|--------|-----------|
| / (Home) | Stats cards, timeline agente, sparkline 7 días, deadlines |
| /queue | Cola humana con cards, botones acción, filtros urgencia |
| /earnings | Tabla ingresos, formulario manual, gráficos por plataforma |
| /platforms | Grid cards con toggle on/off, stats por plataforma |
| /analytics | Ranking €/h real, distribución, recomendaciones |
| /agent | Logs, control start/stop, config, screenshots |

### Diseño Visual

- Background: zinc-950 (dark mode default)
- Tier 1: emerald-500, Tier 2: blue-500, Tier 3: amber-500, Tier 4: zinc-500
- Critical: red-500 (pulse), High: orange-500, Medium: yellow-500

---

## 9. Catálogo de Plataformas

| # | Plataforma | €/h | Categoría | Tier | Sprint |
|---|-----------|-----|-----------|------|--------|
| 1 | Prolific | 9-17 | research | 1 | 3 |
| 2 | Respondent | 75-200 | research | 1 | 4 |
| 3 | UserTesting | 30-45 | ux_testing | 1 | 5 |
| 4 | User Interviews | 40-175 | research | 1 | 5 |
| 5 | TestingTime | 30-60 | ux_testing | 1 | 6 |
| 6 | IntelliZoom | 24-45 | ux_testing | 2 | 6 |
| 7 | Testbirds | 30-40 | ux_testing | 2 | 6 |
| 8 | Checkealos | 32 | ux_testing | 2 | 7 |
| 9 | Userlytics | 20-50 | ux_testing | 2 | 7 |
| 10 | uTest | 15-25 | microtasks | 2 | 7 |
| 11 | PlaytestCloud | 36 | beta | 2 | 7 |
| 12 | Clickworker | 5-15 | microtasks | 3 | 8 |
| 13 | Appen | 5-20 | search_eval | 3 | 8 |
| 14 | OneForma | 5-10 | microtasks | 3 | 8 |
| 15 | TELUS Digital | 12-15 | search_eval | 3 | 9 |
| 16 | BetaTesting | 15-30 | beta | 3 | 9 |
| 17 | Teemwork.ai | 14-15 | search_eval | 3 | 9 |
| 18 | LifePoints | 2-6 | surveys | 4 | 10 |
| 19 | Toluna | 3-6 | surveys | 4 | 10 |
| 20 | ySense | 2-6 | surveys | 4 | 10 |
| 21 | Swagbucks | 2-5 | surveys | 4 | 10 |
| 22 | TGM Panel | 5-10 | surveys | 4 | 10 |
| 23 | Panel Opinea | 3-9 | surveys | 4 | 10 |
| 24 | Ferpection | 10-30 | ux_testing | 4 | 10 |
| 25 | Surveyeah | 2-5 | surveys | 4 | 10 |
| 26 | Betabound | Variable | beta | 4 | 10 |

---

## 10. Fichas de Plataforma (Deep Research)

### Template de Ficha (crear una por plataforma ANTES de codificar)

```markdown
# FICHA: [Nombre Plataforma]

## Info General
- URL, Login URL, Dashboard URL, Tier, Categoría, Ratio €/h, Método pago

## Flujo de Login
- Selectores reales de email, password, submit
- ¿2FA? ¿CAPTCHA? Verificación de logged in

## Dashboard de Tareas
- Selectores del container, título, pago, duración, botón aceptar
- Estado "sin tareas"

## Flujo de Aceptación
- ¿Screener previo? Tipo de preguntas. ¿Redirige a web externa?

## Anti-Bot / Seguridad
- ¿Detecta Playwright? ¿Rate limiting? ¿Fingerprinting?

## Clasificación de Tareas
- Auto-completables, semi-auto, human-only

## Edge Cases
- Penalizaciones, expiración, límites simultáneos
```

---

## 11. Sprints de Ejecución

| Sprint | Objetivo | Duración |
|--------|----------|----------|
| 0 | Setup repo + estructura | 0.5 día |
| 1 | Core engine (browser, sessions, plugin base, CLI) | 1 día |
| 2 | Profiler + Telegram + Email monitor | 1 día |
| 3 | Plugin: Prolific ⭐ | 1-2 días |
| 4 | Plugin: Clickworker + Night agent loop | 1-2 días |
| 5 | Plugins: UserTesting + Respondent + User Interviews | 2 días |
| 6 | Dashboard: Setup + Home + Queue | 2 días |
| 7 | Dashboard: Earnings + Platforms + Analytics | 2 días |
| 8 | Plugins Tier 2 (6 plataformas) | 2-3 días |
| 9 | Plugins Tier 3 (6 plataformas) | 2 días |
| 10 | Plugins Tier 4 + Scoring | 2 días |
| 11 | Redesign visual + Polish | 1-2 días |

---

## 12. Variables de Entorno

```bash
# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Gmail
GMAIL_ADDRESS=
GMAIL_APP_PASSWORD=

# Supabase
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Captcha (opcional)
TWOCAPTCHA_API_KEY=

# Encriptación
ENCRYPTION_KEY=

# Agente
AGENT_MODE=night
NIGHT_START_HOUR=23
NIGHT_END_HOUR=7
HEADLESS=true
CHECK_INTERVAL_TIER1=900
CHECK_INTERVAL_TIER2=1800
CHECK_INTERVAL_TIER3=3600
CHECK_INTERVAL_TIER4=3600
MIN_SCORE_THRESHOLD=30
SCREENSHOT_RETENTION_DAYS=7

# Dashboard
NEXT_PUBLIC_APP_URL=
```

---

## 13. Seguridad y Anti-Detección

### Credenciales
- Encriptadas con Fernet, .env en .gitignore, data/sessions/ en .gitignore

### Comportamiento Humano
- Delays: clicks 0.8-2.5s, páginas 2-5s, typing 50-200ms/char
- Mouse gradual, typos ocasionales, scroll gradual
- Entre plataformas: 10-30s

### Fingerprinting
- User agents reales rotativos, viewports realistas
- Timezone Europe/Madrid, locale es-ES
- NO stealth plugins, NO modificar WebGL/Canvas

### Reglas del Agente
1. NUNCA fabricar respuestas de opinión
2. NUNCA mentir en screeners
3. Si detecta anti-bot → PARAR + alertar
4. Si CAPTCHA irresolvible → cola humana
5. Si login falla 3x → desactivar + alertar

---

## 14. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Baneo por bot | Media | Comportamiento humano, conservador |
| Web cambia estructura | Alta | Fichas documentadas, alertas de fallo |
| CAPTCHA irresolvible | Media | Cola humana como fallback |
| Login 2FA nuevo | Baja | Alertar humano, re-auth manual |
| Supabase caído | Baja | JSON local + sync posterior |
| Rate limiting | Media | Intervals conservadores, backoff |
