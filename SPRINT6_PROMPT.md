# SPRINT 6 — DASHBOARD: SETUP + HOME + QUEUE

## CONTEXTO
Estás desarrollando BeermoneyClaude, un agente autónomo de beermoney.
Sprints 0-4 completos (core engine, profiler, telegram, email, prolific, clickworker, night loop).
Lee MASTERPLAN.md secciones 6 (Base de Datos) y 8 (Dashboard Web) para contexto completo.

## OBJETIVO
Crear el dashboard web con Next.js 15 desplegable en Vercel.
Este sprint cubre: setup del proyecto, layout, página Home, y página Queue (cola humana).

La página Queue es LA MÁS IMPORTANTE — es donde ves las tareas que el agente te dejó pendientes.

---

## TAREA 1: Crear proyecto Next.js

Dentro de la carpeta `dashboard/` del repo:

```bash
cd dashboard
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
```

Configuración:
- App Router (NO Pages Router)
- TypeScript
- Tailwind CSS
- src/ directory
- Import alias @/*

Después instala dependencias:

```bash
npx shadcn@latest init
# Estilo: New York
# Color base: Zinc
# CSS variables: yes

# Instalar componentes shadcn que vamos a usar:
npx shadcn@latest add button card badge table tabs dialog input label select separator sheet skeleton toast dropdown-menu avatar scroll-area progress

# Instalar dependencias adicionales:
npm install @supabase/supabase-js recharts date-fns lucide-react
```

## TAREA 2: Configuración Supabase

### 2a. Crear archivo de tipos

Crea `dashboard/src/lib/supabase/types.ts` con los tipos TypeScript que corresponden al schema SQL del MASTERPLAN sección 6:

```typescript
// Tipos basados en las tablas del MASTERPLAN

export type Platform = {
  id: string
  slug: string
  name: string
  url: string
  login_url: string | null
  dashboard_url: string | null
  category: 'research' | 'ux_testing' | 'microtasks' | 'surveys' | 'beta' | 'search_eval'
  tier: 1 | 2 | 3 | 4
  avg_pay_min: number | null
  avg_pay_max: number | null
  currency: string
  payment_methods: string[]
  frequency: string | null
  spain_available: boolean
  plugin_status: 'planned' | 'research' | 'dev' | 'testing' | 'active' | 'broken'
  active: boolean
  check_interval_seconds: number
  last_scanned_at: string | null
  last_task_found_at: string | null
  last_login_at: string | null
  login_status: 'ok' | 'failed' | 'captcha' | 'unknown'
  notes: string | null
  created_at: string
  updated_at: string
}

export type Opportunity = {
  id: string
  platform_id: string
  source: 'scan' | 'email' | 'manual'
  external_id: string | null
  title: string | null
  description: string | null
  estimated_pay: number | null
  currency: string
  estimated_minutes: number | null
  effective_hourly_rate: number | null
  url: string | null
  priority: 'critical' | 'high' | 'medium' | 'low'
  score: number | null
  score_breakdown: Record<string, number> | null
  difficulty: 'auto' | 'semi_auto' | 'human'
  status: 'detected' | 'accepted' | 'reserved' | 'in_progress' | 'completed' | 'expired' | 'skipped' | 'failed'
  agent_action: string | null
  needs_human: boolean
  human_reason: string | null
  human_instructions: string | null
  deadline: string | null
  screenshot_path: string | null
  detected_at: string
  accepted_at: string | null
  completed_at: string | null
  created_at: string
}

export type HumanQueueItem = {
  id: string
  opportunity_id: string | null
  platform_slug: string
  task_title: string
  estimated_pay: number | null
  currency: string
  url: string | null
  reason: 'captcha' | 'voice_test' | 'opinion_survey' | 'screener_complex' | 'manual_review'
  instructions: string | null
  deadline: string | null
  urgency: 'critical' | 'high' | 'medium' | 'low'
  screenshot_path: string | null
  status: 'pending' | 'in_progress' | 'done' | 'skipped' | 'expired'
  actual_earnings: number | null
  actual_minutes: number | null
  completed_at: string | null
  created_at: string
}

export type Earning = {
  id: string
  platform_id: string
  opportunity_id: string | null
  amount: number
  currency: string
  amount_eur: number | null
  task_type: 'survey' | 'ux_test' | 'microtask' | 'interview' | 'screener' | 'bug_report' | null
  task_description: string | null
  time_spent_minutes: number | null
  effective_hourly_rate: number | null
  completed_by: 'agent' | 'human' | 'mixed'
  payment_status: 'pending' | 'processing' | 'paid'
  payment_date: string | null
  notes: string | null
  completed_at: string
  created_at: string
}

export type AgentLog = {
  id: string
  session_id: string | null
  event_type: 'start' | 'login' | 'scan' | 'accept' | 'complete' | 'captcha' | 'error' | 'queue' | 'stop'
  platform_slug: string | null
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical'
  message: string | null
  details: Record<string, any> | null
  screenshot_path: string | null
  created_at: string
}

export type DailyStats = {
  id: string
  date: string
  total_earned_eur: number
  total_time_minutes: number
  effective_hourly_rate: number | null
  tasks_completed: number
  tasks_by_agent: number
  tasks_by_human: number
  opportunities_detected: number
  opportunities_accepted: number
  platforms_scanned: number
  best_platform: string | null
  best_hourly_rate: number | null
  created_at: string
}
```

### 2b. Cliente Supabase

Crea `dashboard/src/lib/supabase/client.ts`:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### 2c. Environment variables

Crea `dashboard/.env.local.example`:
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## TAREA 3: Layout Principal

### 3a. Sidebar + Header

El layout tiene sidebar colapsable a la izquierda y header arriba.

Crea `dashboard/src/components/layout/Sidebar.tsx`:
- Logo/nombre: "BeermoneyClaude" con icono 🤖
- Links de navegación con iconos de lucide-react:
  - 🏠 Home → /
  - 📋 Queue → /queue (con badge del número de items pending)
  - 💰 Earnings → /earnings
  - 🔌 Platforms → /platforms
  - 📊 Analytics → /analytics
  - 🤖 Agent → /agent
- Separador
- ⚙️ Settings → /settings
- Indicador de estado del agente (🟢 Running / 🔴 Stopped / 🌙 Night Mode)
- Colapsable en mobile (sheet/drawer)

Crea `dashboard/src/components/layout/Header.tsx`:
- Muestra: Agent status dot + "Today: X.XX€" + "Queue: N pending"
- En mobile: hamburger menu que abre sidebar

Crea `dashboard/src/app/layout.tsx`:
- Dark mode por defecto (class="dark" en html)
- Sidebar + Header + main content area
- Fuente: Inter o Geist (la que venga por defecto con Next.js)
- Background: zinc-950
- Metadata: title "BeermoneyClaude Dashboard"

### 3b. Colores y Tema

En `globals.css` o `tailwind.config.ts`, definir:

```
TIER COLORS (para badges y bordes):
- Tier 1: emerald-500
- Tier 2: blue-500
- Tier 3: amber-500
- Tier 4: zinc-500

URGENCY COLORS:
- Critical: red-500 (con animación pulse)
- High: orange-500
- Medium: yellow-500
- Low: zinc-500

STATUS COLORS:
- Active/OK: emerald-500
- Warning: amber-500
- Error/Failed: red-500
- Pending: blue-500
```

## TAREA 4: Página Home (/)

La home muestra el resumen del día de un vistazo.

### 4a. Stats Cards (fila de 4)

```
[💰 Ganado Hoy]  [⏱️ Tiempo Hoy]  [📊 Ratio €/h]  [📋 En Cola]
   12.50€            1.5h             8.33€/h          3 pending
```

Cada card muestra:
- Icono + label
- Valor grande
- Comparación con ayer: "+2.50€ vs yesterday" (verde si sube, rojo si baja)

Crea `dashboard/src/components/dashboard/StatsCards.tsx`

### 4b. Timeline de actividad reciente

Lista vertical de las últimas 10-15 acciones del agente:

```
🟢 01:23 | Prolific    | Scan completed — 0 studies found
🟡 01:20 | Clickworker | Login successful
🔴 01:15 | Prolific    | Login timeout — retrying...
🟢 00:55 | System      | Night agent started
```

Cada item: color por level, timestamp, platform badge, mensaje.

Crea `dashboard/src/components/dashboard/RecentActivity.tsx`

### 4c. Mini chart: ingresos últimos 7 días

Sparkline o bar chart pequeño con Recharts:
- Eje X: últimos 7 días
- Eje Y: € ganados ese día
- Tooltip con detalle

Crea `dashboard/src/components/dashboard/EarningsChart.tsx`

### 4d. Próximas deadlines

Lista de las 3-5 tareas en cola con deadline más cercano:
```
⏰ Prolific study — £9.00 — expires in 2h 15m
⏰ UserTesting screener — $10.00 — expires in 5h
```

Crea `dashboard/src/components/dashboard/UpcomingDeadlines.tsx`

### 4e. Componer página Home

`dashboard/src/app/page.tsx`:
- Grid responsivo
- StatsCards en fila arriba (grid 4 cols en desktop, 2 en mobile)
- RecentActivity y EarningsChart lado a lado (2 cols)
- UpcomingDeadlines abajo

## TAREA 5: Página Queue (/queue) — LA MÁS IMPORTANTE

Esta es la página que uso cada mañana para ver qué me dejó el agente.

### 5a. QueueCard

Crea `dashboard/src/components/queue/QueueCard.tsx`:

Cada card muestra:
- Borde izquierdo coloreado por urgencia (critical=red pulse, high=orange, etc.)
- Badge de plataforma (con color de tier)
- Título de la tarea (grande)
- Pago estimado (€) + moneda
- Razón por la que necesita humano (badge: "CAPTCHA", "Voice Test", "Opinion Survey", etc.)
- Instrucciones del agente (texto)
- Deadline con countdown ("expires in 2h 15m" o "⚠️ EXPIRED")
- Screenshot thumbnail (si disponible) — click para ver grande
- 3 botones de acción:
  - 🔗 "Abrir" → abre URL de la tarea en nueva pestaña
  - ✅ "Completada" → abre modal para registrar earnings
  - ⏭️ "Saltar" → marca como skipped

### 5b. Modal "Completar tarea"

Crea `dashboard/src/components/queue/CompleteTaskDialog.tsx`:

Dialog/modal con:
- Título: "Completar: {task_title}"
- Campo: "¿Cuánto ganaste?" (input number + selector moneda EUR/GBP/USD)
- Campo: "¿Cuánto tardaste?" (input number en minutos)
- Campo: "Notas" (textarea, opcional)
- Calcula y muestra: "Ratio efectivo: X.XX€/h"
- Botones: "Cancelar" | "Guardar"
- Al guardar: actualiza human_queue status=done + crea earning en Supabase

### 5c. QueueList

Crea `dashboard/src/components/queue/QueueList.tsx`:

- Lista de QueueCards ordenadas por: urgency (critical primero), luego deadline (más cercano primero)
- Filtros arriba: por plataforma (dropdown), por urgencia (badges clickeables), por estado
- Tabs: "Pending (3)" | "Done (12)" | "Skipped (2)" | "Expired (1)"
- Empty state cuando no hay tareas: "🎉 No pending tasks! Check back after the next agent run."
- Loading skeleton mientras carga

### 5d. Componer página Queue

`dashboard/src/app/queue/page.tsx`:
- Header: "Human Queue" + badge con total pending
- Filtros
- Tabs
- QueueList

## TAREA 6: Datos de ejemplo (seed)

Como todavía no tenemos Supabase configurado con tablas, crea datos mock para desarrollo.

Crea `dashboard/src/lib/mock-data.ts`:

```typescript
// Datos de ejemplo para desarrollo sin Supabase

export const mockPlatforms: Platform[] = [
  {
    id: "1",
    slug: "prolific",
    name: "Prolific",
    url: "https://www.prolific.com",
    category: "research",
    tier: 1,
    avg_pay_min: 9,
    avg_pay_max: 17,
    currency: "GBP",
    plugin_status: "testing",
    active: true,
    login_status: "ok",
    // ... resto de campos
  },
  {
    id: "2",
    slug: "clickworker",
    name: "Clickworker",
    // ...
  },
  // Añadir 4-5 plataformas más de ejemplo
]

export const mockQueueItems: HumanQueueItem[] = [
  {
    id: "q1",
    platform_slug: "prolific",
    task_title: "Research study: Consumer behavior in online shopping",
    estimated_pay: 9.00,
    currency: "GBP",
    url: "https://app.prolific.com/studies/abc123",
    reason: "opinion_survey",
    instructions: "Complete the Qualtrics survey. Estimated 15 minutes. The agent reserved your spot.",
    deadline: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(), // 3h from now
    urgency: "high",
    status: "pending",
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "q2",
    platform_slug: "clickworker",
    task_title: "UHRS: Search result relevance evaluation",
    estimated_pay: 5.00,
    currency: "EUR",
    reason: "manual_review",
    instructions: "Evaluate 50 search results. The agent couldn't auto-complete because the task requires subjective judgment.",
    urgency: "medium",
    status: "pending",
    created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "q3",
    platform_slug: "prolific",
    task_title: "UX Test: Mobile banking app prototype",
    estimated_pay: 15.00,
    currency: "GBP",
    url: "https://app.prolific.com/studies/xyz789",
    reason: "voice_test",
    instructions: "Think-aloud UX test requiring microphone. 20 minutes. RECORD YOUR SCREEN.",
    deadline: new Date(Date.now() + 1 * 60 * 60 * 1000).toISOString(), // 1h from now
    urgency: "critical",
    status: "pending",
    created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  },
  // Añadir 2-3 items con status "done" y "skipped" para las tabs
  {
    id: "q4",
    platform_slug: "clickworker",
    task_title: "Text categorization batch",
    estimated_pay: 3.50,
    currency: "EUR",
    reason: "manual_review",
    urgency: "low",
    status: "done",
    actual_earnings: 3.50,
    actual_minutes: 12,
    completed_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(),
  },
]

export const mockEarnings: Earning[] = [
  // 7 días de ejemplo
  // Variación: algunos días 5€, otros 15€, alguno 0€
]

export const mockAgentLogs: AgentLog[] = [
  {
    id: "l1",
    session_id: "night-2026-03-03",
    event_type: "start",
    level: "info",
    message: "Night agent started — scanning 2 platforms",
    created_at: new Date().toISOString(),
  },
  // ... 10-15 logs de ejemplo con variedad de tipos y levels
]

export const mockDailyStats: DailyStats[] = [
  // últimos 7 días con datos variados
]
```

## TAREA 7: Hooks de datos

Crea hooks que primero usan mock data, pero están preparados para Supabase:

`dashboard/src/hooks/useQueue.ts`:
```typescript
// Si Supabase está configurado → fetch real
// Si no → devolver mock data
// Incluir: getQueue, markDone, markSkipped, addManual
```

`dashboard/src/hooks/useEarnings.ts`:
```typescript
// getEarnings, addEarning, getStats
```

`dashboard/src/hooks/usePlatforms.ts`:
```typescript
// getPlatforms, toggleActive
```

`dashboard/src/hooks/useAgentLogs.ts`:
```typescript
// getLogs, getRecentActivity
```

## TAREA 8: Verificar build

```bash
cd dashboard
npm run build
```

DEBE compilar sin errores. Si hay errores de tipo, corregirlos.

## TAREA 9: Git commit

```bash
cd ..
git add .
git commit -m "Sprint 6: Dashboard - Next.js setup, Home page, Queue page with mock data"
git push
```

## VERIFICACIONES

1. `cd dashboard && npm run dev` → abre en localhost:3000
2. Home page muestra: 4 stat cards, timeline, chart, deadlines
3. Queue page muestra: cards con urgencia, filtros, tabs (pending/done/skipped)
4. Click "Completada" abre modal con campos
5. Sidebar funciona, navigation entre páginas
6. Dark mode correcto (zinc-950 background)
7. Responsive: funciona en mobile (sidebar collapsa)
8. `npm run build` → sin errores
9. Tier colors correctos: T1 green, T2 blue, T3 amber, T4 grey
10. Urgency colors: critical red pulse, high orange, medium yellow

## DISEÑO VISUAL

Referencia del MASTERPLAN:
```
Background: zinc-950
Cards: zinc-900
Borders: zinc-800
Text primary: zinc-50
Text secondary: zinc-400
Accent: emerald-500 (para CTAs y positivo)
```

El dashboard debe verse premium y profesional:
- Spacing generoso
- Bordes sutiles
- Sombras suaves en cards
- Transiciones en hover
- Loading skeletons (no spinners)
- Empty states con iconos y mensajes claros
- Badges con colores de tier/urgency
- Iconos de lucide-react en todo

NO usar gradientes llamativos ni colores neon.
Estilo limpio, tipo Vercel dashboard o Linear app.

## NOTAS

- Usa mock data por ahora — conectamos Supabase real en el Sprint 7
- El dashboard NO necesita auth todavía (es solo para ti)
- Prioriza que compile y se vea bien
- Si shadcn tiene problemas de versión, usa las últimas versiones estables
- El layout debe ser 100% funcional en mobile (sidebar como drawer)
