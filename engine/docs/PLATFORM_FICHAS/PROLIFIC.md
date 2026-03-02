# FICHA: Prolific

## Info General
- URL: https://www.prolific.com
- App URL: https://app.prolific.com
- Login URL: https://app.prolific.com/login (redirects to auth.prolific.com via Auth0)
- Dashboard URL: https://app.prolific.com/studies  # TODO: VERIFY after profile completion
- Tier: 1
- Categoria: research (academic studies)
- Ratio EUR/h: GBP 6-15 (minimo legal GBP 6/h, media GBP 9-12/h)
- Moneda: GBP
- Pago: PayPal, Circle

## Selectores Descubiertos

### Login (Auth0 hosted - auth.prolific.com)
Prolific usa Auth0 para autenticacion. El login form esta en un dominio externo.

- Email: `input[name="email"]` — NO encontrado en primera carga (flujo multi-paso: primero email, luego password)
- Password: `input[type="password"]` / `#password` / `input[name="password"]`
  - Attrs confirmados: `class="input c24dce660 cfba09985"`, `id="password"`, `autocomplete="current-password"`
- Submit: `button[type="submit"]` (text: "Continue")
  - Attrs: `data-action-button-primary="true"`, `name="action"`, `value="default"`
- Google login: `button[data-provider="google"]` / `button:has-text("Google")`
  - Dentro de un `<form data-provider="google" data-form-secondary="true">`
  - Text: "Continue with Google"

### Verificacion logged in
- Selector: TODO: VERIFY SELECTOR (cuenta en waitlist, no se pudo verificar dashboard)
- Candidatos: `[data-testid*="user"]`, `[data-testid*="avatar"]`, `[data-testid*="balance"]`
- URL check: si la URL NO contiene "/login" ni "auth0" ni "auth.prolific.com", probablemente logged in

### Registro / Profile completion
Despues del primer login, Prolific muestra formulario de perfil multi-paso:
- URL: `https://app.prolific.com/register/participant/join-waitlist/profile`
- Progress bar: `[data-testid="progress-bar"]`
- Steps: Profile -> Demographics -> Languages -> Education -> Work -> Other -> Confirmation
- First name: `input[data-testid="question-text-first-name"]`
- Last name: `input[data-testid="question-text-last-name"]`
- Email: `input[data-testid="question-email-email"]`
- DOB month: `input[name="age-month"]`
- DOB day: `input[name="age-day"]`
- DOB year: `input[name="age-year"]`
- Sex: `[data-testid="question-select-sex"]` (dropdown)
- Next button: `button.next[type="submit"]`

### Dashboard de Studies
- Container de studies: TODO: VERIFY SELECTOR
- Study card individual: TODO: VERIFY SELECTOR
- Titulo del study: TODO: VERIFY SELECTOR
- Reward/pago: TODO: VERIFY SELECTOR
- Tiempo estimado: TODO: VERIFY SELECTOR
- Plazas disponibles: TODO: VERIFY SELECTOR
- Boton Take Part: TODO: VERIFY SELECTOR
- Estado vacio (no studies): TODO: VERIFY SELECTOR

### Cookie consent
- Accept button: `button:has-text("Accept")` (class: orejime-Button orejime-Banner-saveButton)

## Flujo de Login
1. Navegar a https://app.prolific.com/login
2. Redirige a https://auth.prolific.com/u/login?state=...
3. Formulario multi-paso Auth0:
   a. Paso 1: Email field (necesita VERIFY - posiblemente `input[name="username"]`)
   b. Paso 2: Password field (`#password`)
   c. Click submit (`button[type="submit"]` text "Continue")
4. 2FA: Desconocido (no se pudo probar)
5. CAPTCHA: No observado en login basico, pero posible
6. Redirige a: https://app.prolific.com/studies (si perfil completo)
7. Si primer login: redirige a /register/participant/join-waitlist/profile

## Flujo de Aceptacion
1. Desde dashboard, cada study muestra: titulo, reward, tiempo, plazas
2. Click "Take part in this study" (o similar) — TODO: VERIFY
3. Redirige a URL externa (Qualtrics, Google Forms, etc.)
4. Deadline: varia por study (tipico 1-24h)
5. Se puede abandonar: Si, "Return submission"

## Clasificacion de Tareas
- AUTO: Ninguna (los studies son externos y requieren opinion/interaccion humana)
- SEMI_AUTO: Screeners demograficos antes del study
- HUMAN: Todos los studies en si (encuestas externas)

## Que puede hacer el agente
1. Login automatico (via Auth0)
2. Detectar studies disponibles
3. Extraer: titulo, pay, duracion, plazas
4. Reservar plaza (click "Take part") — VELOCIDAD CRITICA
5. Detectar screener previo y auto-rellenar demograficos
6. NO completar el study en si (es externo + opiniones)

## Lo que el agente DEBE hacer rapido
Prolific studies se llenan en 1-5 minutos.
El agente debe:
- Scan cada 5-15 minutos (tier 1)
- Al detectar study -> accept INMEDIATAMENTE (no calcular score primero)
- Notificar por Telegram con urgencia CRITICAL

## Edge Cases
- Studies que requieren webcam/microfono -> detectar y queue humana
- Studies con prescreening -> puede que no seas elegible
- Plazas se llenan -> manejar "study full" gracefully
- Prolific puede mostrar "About You" para completar perfil
- Rate limiting: no refrescar mas de 1 vez por minuto
- Cuenta en waitlist: detectar URL /join-waitlist y notificar

## Anti-Bot
- Prolific usa Auth0 con posible deteccion
- NO usar intervalos fijos (anadir random jitter)
- NO refrescar agresivamente
- Comportamiento realista: abrir, scrollear, esperar, actuar

## Notas Tecnicas
- Frontend: Vue.js (data-v-* attributes observados)
- Auth: Auth0 hosted login page
- Cookie consent: Orejime library
- Design system: Custom DS con data-testid pattern (ds-input-wrapper, label-wrapper, etc.)
