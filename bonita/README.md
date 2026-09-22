# Automatizacion de Bonita para RescueSync

> **Desactualizado en un punto:** la organización que realmente se usa hoy es
> `entrega-2/ACME.xml` (ACME editada de forma aditiva), no
> `organizations/RescueSyncOrg.xml` de más abajo. Los pasos de instalación
> completos y vigentes están en el `README.md` de la raíz del repo.

Este folder junta todo lo que se puede automatizar alrededor de Bonita
Studio/Engine para la Entrega 2. Resumen de la investigacion (ver fuentes
al final):

- **No hay forma de automatizar el diseno del proceso** (crear variables,
  mapear actores a lanes, configurar la expresion del timer) sin abrir
  Bonita Studio. La herramienta que sí lo permite en teoria
  (`BonitaStudioBuilder`, para generar `.bar` por linea de comandos) es
  una feature de las ediciones Subscription -- no esta disponible en
  Community, que es la que tenemos instalada.
- Editar a mano el `.proc` (el XML interno del `.bos`, formato XMI/EMF de
  Eclipse) es tecnicamente posible pero no tiene schema publico y no hay
  forma de validar que Studio lo siga abriendo bien sin GUI -- no vale la
  pena el riesgo para algo que en Studio son 5 minutos de trabajo con el
  mouse.
- Lo que SI es automatizable de punta a punta es todo lo que pasa
  **despues** de que el proceso esta desplegado: login, arrancar
  instancias, setear variables de un caso, consultar tareas -- eso es la
  REST API de Bonita Engine, disponible en Community.

## Lo que queda manual en Studio (una sola vez, ~15-20 min)

La checklist detallada y con orden de dependencia ya esta en
`entrega-1/contrato-instanciacion.md` (seccion 6) -- ese documento es la
fuente de verdad congelada del contrato (10 variables, 4 inputs, 4
operations, script del timer). No la duplico aca para que no queden dos
versiones pisandose; si algo de este README no coincide con ese `.md`,
gana el `.md`.

Un agregado a esa checklist: el mapeo de actores es por **grupo**, no por
rol (`organizations/RescueSyncOrg.xml` ya viene con la jerarquia
`/rescuesync/{municipio,coordinador,ong}` que pide el punto 6). La lane
"Entidad Nacional / Sistema RescueSync" no necesita actor mapping: son
todas `serviceTask`, las ejecuta el motor via conectores.

**Antes de importar la organizacion nueva**, anota el usuario
administrador/tecnico con el que Studio te deja entrar al Portal --
Bonita solo permite una organizacion activa a la vez, asi que
`RescueSyncOrg.xml` va a reemplazar a `ACME` por completo (sus usuarios
tambien). Si el admin tecnico de Bonita es independiente de la
organizacion (suele serlo), no deberia pasar nada, pero conviene
verificarlo antes de perder acceso.

## `organizations/RescueSyncOrg.xml`

Organizacion lista para importar: grupo raiz `rescuesync` con 3 subgrupos
(`municipio`, `coordinador`, `ong`) y 4 usuarios de prueba
(`operador.municipal`, `coordinador.regional`, `ong.cruzroja`,
`ong.bomberos`, todos con password `bpm`, rol generico `member` como en
ACME). Hay dos ONGs para poder probar en serio la tarea multi-instancia
"Confirmar Finalizacion de Actividades" (una instancia por ONG
adjudicada) -- el checklist del contrato pide 1 por grupo como minimo,
esta segunda es un agregado mio; borrala si no la queres. Estructura
verificada contra el `ACME.xml` real que ya viene en el `.bos` (mismo
schema `organization-xml-schema/1.1` y mismo patron `parentPath` para
grupos anidados), asi que el formato es correcto.

## `scripts/bonita_client.py`

Cliente Python (`pip install requests`) que hace login con manejo del
token CSRF (`X-Bonita-API-Token`), resuelve el `processDefinitionId`,
arranca una instancia mandando los 4 inputs del contrato (seccion 1 y 5
de `contrato-instanciacion.md`) y lista las tareas humanas abiertas.
Tambien trae `set_case_variable(s)` para pisar a mano una variable
interna durante una prueba (ej. forzar `coberturaCompleta=true` sin
esperar al ServiceTask real, para probar la rama del gateway). Es el
punto de partida para T-07/T-08/T-13.

**No fue probado contra un servidor real** porque no hay forma de correr
Bonita desde esta sesion -- esta armado siguiendo la documentacion oficial
de los endpoints, pero lo mas probable es que al correrlo contra tu
instancia local aparezcan ajustes puntuales (nombres de campos, algun
endpoint que cambio entre versiones). Eso es exactamente el trabajo de
"pulir e investigar" que quieren hacer este finde -- corranlo, vean el
error real, y lo ajustamos.

## Fuentes

- [REST API Overview](https://documentation.bonitasoft.com/bonita/2021.2/api/rest-api-overview)
- [Manage a process](https://documentation.bonitasoft.com/bonita/latest/api/manage-a-process)
- [Automating build of artifacts outside the Studio](https://documentation.bonitasoft.com/bonita/2021.1/automating-builds) (BonitaStudioBuilder, Subscription only)
- [CSRF security](https://documentation.bonitasoft.com/bonita/2022.2/security/csrf-security)
- [Getting the X-Bonita-API-Token (foro)](https://community.bonitasoft.com/questions-and-answers/getting-x-bonita-api-token)
- [Manage an organization](https://documentation.bonitasoft.com/bonita/latest/api/manage-an-organization)
- [Organization overview](https://documentation.bonitasoft.com/bonita/latest/identity/organization-overview)
