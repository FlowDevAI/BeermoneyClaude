# FICHA: Clickworker

## Info General
- URL: https://www.clickworker.com
- Workplace URL: https://workplace.clickworker.com
- Registration URL: https://workplace.clickworker.com/en/users/new/
- Login URL: https://workplace.clickworker.com/en/users/sign_in  # TODO: VERIFY URL (inferred from Rails/Devise pattern)
- Login Alt URL: https://www.clickworker.com/clickworker/?login=1  (marketing site, has Signup + Login buttons)
- Tier: 3
- Categoria: microtasks
- Ratio EUR/h: 5-15 EUR
- Moneda: EUR
- Pago: PayPal, SEPA (minimo 5 EUR)
- Frecuencia: Diaria

## Research (2026-03-03)

### Estado de la cuenta
- Cuenta NO registrada aun — landing en pagina de registro `/en/users/new/`
- Todas las paginas del workplace devuelven 404 sin cuenta activa
- Necesita registro completo antes de poder investigar workplace

### Login Page (marketing site)
- URL: `https://www.clickworker.com/clickworker/?login=1`
- Tiene botones "Signup" (azul) y "Login" (outline)
- NO se encontraron campos email/password directos (carga dinamica o redireccion)
- El boton Login redirige al workplace login

### Registration Form (`/en/users/new/`)
- Formulario en 3 pasos (Step 1, Step 2, Step 3)
- Campos Step 1:
  - Salutation (dropdown)
  - Legal First Name
  - Legal Middle Name
  - Legal Last Name
  - Username
  - E-mail address
  - Password + Confirm password
  - Continue button
- Link: "Already have an account? Sign in"

### Tecnologia
- Backend: Ruby on Rails (Devise authentication based on URL patterns)
- NO usa data-testid attributes
- Clases CSS clasicas (Bootstrap-like: `btn`, `btn-primary`, `btn-lg`)
- Body ID para errores: `id="http_404"`
- Sidebar navigation con clases: `side-navbar`, `sidebar-scroll`
- Icons: FontAwesome (`fas fa-chevron-right`)

### Sidebar Navigation (workplace)
- About us, About Clickworker, Team, Career
- Clickworker Job (dropdown `#dropdown-cw-jobs`)
  - The term Clickworker
  - Distribution of tasks
- Icon class: `cww-icons ico-jobs-briefcase-outline`

## Selectores Descubiertos

### Login
- Email: TODO: VERIFY SELECTOR (account needed)
- Password: TODO: VERIFY SELECTOR (account needed)
- Submit: TODO: VERIFY SELECTOR (account needed)
- Probable pattern (Rails/Devise):
  - `input[name="user[email]"]` or `input#user_email`
  - `input[name="user[password]"]` or `input#user_password`
  - `input[type="submit"]` or `button[type="submit"]`

### Verificacion logged in
- Selector: TODO: VERIFY SELECTOR (account needed)
- Probable: presencia de sidebar con items de navegacion de workplace

### Dashboard / Workplace
- Container de jobs: TODO: VERIFY SELECTOR (404 sin cuenta)
- Job card individual: TODO: VERIFY SELECTOR
- Titulo: TODO: VERIFY SELECTOR
- Pago: TODO: VERIFY SELECTOR
- Tipo: TODO: VERIFY SELECTOR
- Boton start: TODO: VERIFY SELECTOR
- Estado vacio: TODO: VERIFY SELECTOR

### UHRS
- Enlace a UHRS: TODO: VERIFY SELECTOR (no detectado, necesita cuenta activa)
- Como acceder: Probablemente seccion dentro del workplace

## Tipos de Tareas (esperados)
- Categorizacion de textos/imagenes -> AUTO posible
- Transcripcion simple -> SEMI_AUTO
- Evaluacion de busqueda (UHRS) -> SEMI_AUTO/HUMAN
- Encuestas -> HUMAN
- Escritura creativa -> HUMAN

## Edge Cases
- Cualificaciones necesarias para ciertas tareas
- Assessments previos (tests de prueba) requeridos
- UHRS tiene su propia interfaz dentro de Clickworker
- Tareas con deadline
- Limite de tareas por dia
- Account activation puede tomar tiempo despues del registro

## Screenshots
- `data/screenshots/clickworker_research/01_login_page.png` — Marketing site login
- `data/screenshots/clickworker_research/02_after_login.png` — Registration form (3-step)
- `data/screenshots/clickworker_research/03_jobs.png` — 404 (no account)
- `data/screenshots/clickworker_research/03_account.png` — 404 (no account)
- `data/screenshots/clickworker_research/jobs_page_structure.html` — 404 HTML
