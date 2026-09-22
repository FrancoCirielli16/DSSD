# RescueSync — backend

App web (FastAPI + Jinja2 + HTMX + Bootstrap). Esqueleto de la Entrega 2 (T-02).

## Correr

```bash
docker compose up -d db         # desde la raíz del repo: Postgres en :5432
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # ajustar valores si hace falta
alembic upgrade head            # crea las tablas
python -m app.seed              # datos de demo (4 perfiles, 2 ONGs, pass: demo1234)
uvicorn app.main:app --reload
```

Cambios de modelo: editar `app/models/entities.py` y correr
`alembic revision --autogenerate -m "descripcion"` + `alembic upgrade head`.

- App: http://localhost:8000/
- Swagger (automático): http://localhost:8000/docs

## Estructura

```
app/
  main.py          # crea la app, monta /static, registra routers
  core/            # config (variables de entorno) y templating
  routers/         # rutas HTTP (páginas y endpoints /api/...), una por dominio
  services/        # lógica de negocio; los routers solo la llaman
  models/          # modelos SQLAlchemy (T-03)
  schemas/         # esquemas Pydantic de entrada/salida
  integrations/    # clientes externos (Bonita)
  templates/       # Jinja2 (base.html + una plantilla por pantalla)
  static/          # css/js propios
```

Convención: router → service → models/integrations. Los routers no
tocan la BD ni Bonita directamente.

## Tests

```bash
pip install -r requirements-dev.txt
pytest                                   # unitarios: sin Postgres ni Bonita, ~25 s
RUN_BONITA_INTEGRATION=1 pytest -m integration   # opcional: contra Bonita Studio corriendo
```

Qué protegen:
- `test_models.py`: restricciones del esquema (únicos, CHECK de enums, cascadas, versiones de oferta).
- `test_migrations.py`: **las migraciones coinciden con los modelos**. Si falla, cambiaste
  `models/entities.py` sin correr `alembic revision --autogenerate`.
- `test_auth.py`: login, sesión y 401/403 por rol.
- `test_bonita_client.py`: cliente de Bonita con HTTP simulado.
- `test_bonita_contract.py`: el contrato de instanciación y las tareas del `.bos`
  (`entrega-2/RescueSync.bos`) coinciden con lo que manda la app. Si cambiás el contrato en
  Studio, exportá el `.bos` y actualizá `CONTRACT_INPUTS`.

Regla: cada pieza nueva (endpoint, pantalla, servicio) entra con sus tests.

## Login y roles (T-04)

Sesión por cookie firmada (`SESSION_SECRET`). Usuarios de demo (`python -m app.seed`,
pass `demo1234`): `operador.municipal`, `coordinador.regional`, `ong.cruzroja`, `ong.bomberos`,
`auditor`. Con `SHOW_DEMO_USERS=true` en `.env` el login los lista (solo desarrollo).

Proteger una ruta con el rol:

```python
from app.core.deps import require_role
from app.models import Rol

@router.get("/lotes")
def lotes(user: Usuario = Depends(require_role(Rol.COORDINADOR))): ...
```

Sin sesión: páginas → redirige a `/login`; `/api/*` → 401 JSON. Rol incorrecto: 403.
Para sumar una pantalla al menú de un perfil, poner su ruta en `MENU_POR_ROL`
(`app/routers/pages.py`). Las plantillas reciben `session_user` y `rol_label` solas.

## Bonita

`app/integrations/bonita.py` es el cliente REST (login con CSRF, instanciar,
listar tareas, setear variables). Está probado contra Studio 10.4.0.
Configuración en `.env` (`BONITA_*`).

Reglas: la app nunca completa la tarea `Cargar Ofertas de Ayuda`; guarda el
`caseId` de cada emergencia; avanza tareas logueándose como un usuario del
rol correspondiente.
