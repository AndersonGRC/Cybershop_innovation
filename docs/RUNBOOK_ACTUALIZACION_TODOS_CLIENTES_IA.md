# Traspaso operativo: actualización de IA para todos los clientes

Fecha de elaboración: 24/09/2026. Destinatario: otra IA u operador con acceso
autorizado a PostgreSQL, Git, systemd y al panel maestro
admin.cybershopcol.com. Este archivo es una **instrucción de trabajo, no un
registro de despliegue completado**. Revalidar todo el estado antes de actuar.

## Mandato y límites del propietario

- Actualizar cada cliente preservando su base, dominio, marca, configuración y
  datos; jamás consultar una base a partir de un slug inferido ni copiar datos
  de un cliente a la base, chat, reporte o respaldo de otro.
- **No cambiar credenciales de nada**: no rotar contraseñas, llaves, tokens,
  claves API, roles/usuarios PostgreSQL, usuarios de sistema, archivos de
  secretos ni EnvironmentFiles. No incluir secretos en este archivo, comandos,
  logs, capturas ni respuestas. Usar el acceso autorizado que ya exista.
- No activar acciones operativas de IA, chat público ni respaldo de pago de
  Anthropic durante el despliegue. No hacer llamadas de pago. Mantener
  ai_actions y ai_public apagados; presupuesto Anthropic en US$0 si ya está
  así. No alterar el presupuesto sin instrucción expresa.
- No usar git reset --hard, force-push, DROP, TRUNCATE, restauraciones sobre una
  BD viva, borrado de respaldos ni reinicio de clientes suspendidos.
- **Límite de seguridad:** en la inspección del 24/09 las siete bases figuraban
  con el mismo db_user PostgreSQL (postgres) y una instancia activa corría como
  root. Bases distintas no equivalen a aislamiento de privilegios. Dado que
  el propietario prohíbe cambiar credenciales/usuarios, este trabajo **no puede
  certificar aislamiento estricto entre clientes**. Si esa certificación es
  condición para el rollout, detenerse y pedir una decisión explícita; no
  presentar una actualización funcional como solución de ese riesgo.

## Estado observado, no supuesto actual

En el VPS el 24/09/2026 había 7 clientes (3 activos, 4 suspendidos). El
repositorio web instalado estaba en 33831a8, con modificaciones locales en
app/static/installers/version.json y app/templates/descargar.html, más un
archivo sin seguimiento que **no debe tocarse sin investigar su dueño**. El
maestro instalado estaba en 5701f6b; el master remoto del maestro estaba en
4afe0dd y el del web en 33831a8. El maestro instalado tenía migraciones
0001–0009, **no 0015**. Los cambios nuevos de IA en este workspace, incluida
0015_ia_acciones_pendientes.sql, estaban sin commit/publicación. El clic previo
del propietario en la tienda principal no pudo instalar ese lote nuevo; la
última migración registrada en su BD era 0009, aplicada en agosto.

El 24/09 se instaló una corrección del cron de respaldos desde
deploy/cybershop-backup.sh: incluye todas las BD registradas, incluso una de
nombre heredado que el script anterior omitía. Se generaron respaldos nuevos
de las 7 BD y del plano de control, y se verificó su compresión. **No se probó
una restauración.** El script anterior quedó en
/usr/local/bin/cybershop-backup.sh.pre-20260924. La fuente nueva local sigue
sin commit: incorporarla cuidadosamente al release. Revalidar instalación,
cron, inventario y respaldos antes del rollout.

La tienda principal usa el servicio cybershop.service y, en la observación,
su BD asignada era cybershop; cyber_t001 pertenecía a **otro** cliente. Nunca
derivar la BD del número o nombre del cliente.

## Puertas obligatorias antes de publicar

1. Registrar una ventana de mantenimiento, responsable, versión objetivo y
   criterio de abortar. Obtener aceptación explícita del riesgo residual de
   privilegios compartidos si se pretende continuar sin cambiar credenciales.
   Si no existe, **parar aquí**.
2. Revisar por separado los diffs completos de CyberShopAdmin y CyberShop.
   Conservar todos los cambios locales del VPS y del workspace; no hacer
   stash/reset ni incluir archivos ajenos por accidente. Comprobar que ambos
   releases estén versionados, revisados, probados con PostgreSQL real y
   publicados en sus respectivos master. Registrar los SHA exactos. No usar
   el botón como sustituto de commit/push: solo trae código web ya publicado.
3. Probar 0015 y todas las migraciones pendientes en una copia **aislada** con
   esquema representativo; verificar que cada SQL sea aditivo/idempotente.
   Probar permisos y flujos de confirmar/cancelar sin datos reales. Probar
   compatibilidad del código nuevo con clientes aún no migrados: el primer
   clic cambia archivos web compartidos para todos.
4. Inventariar todos los clientes desde saas_control_plane, no desde nombres
   de BD adivinados. Comprobar que cada tenant_id apunte a una BD existente y
   única. Comparar el DB_NAME **efectivo del proceso** con esa asignación
   leyendo solo ese campo del entorno/unidad, sin mostrar archivos completos
   que contengan secretos; para el primario revisar .cybershop.conf. Una fila
   sin BD, duplicada, proceso apuntando a otra BD o estado inesperado detiene
   el trabajo.
5. Verificar respaldos recientes **por BD** y del plano de control. Comparar
   la salida de /usr/local/bin/cybershop-backup.sh --list con el inventario;
   ejecutar --no-prune antes de cambios, comprobar cantidad, tamaño y gzip -t
   de todos los archivos. Hacer al menos una prueba de restauración en una BD
   temporal aislada, nunca en la BD de otro cliente ni en producción viva.
   No copiar dumps al repositorio ni mostrarlos al modelo.
6. Confirmar en el VPS el helper /usr/local/bin/cybershop-deploy-code.sh,
   reglas sudo y ExecReload de cybershop.service y cybershop@.service. El
   helper y el sudoers no están versionados en estos repos. Revisar también
   timeout del proxy; un 504 no demuestra que la operación se revirtió.

### Consultas de inventario (solo lectura)

Ejecutar con una sesión PostgreSQL autorizada. No seleccionar
db_password_enc ni datos de negocio. Sustituir los valores de ejemplo solo
después de cotejarlos con el resultado del plano de control.

~~~sql
SELECT t.id, t.slug, t.estado, td.db_name, td.db_user,
       r.port, r.subdomain, r.instance_status
FROM tenants t
LEFT JOIN tenant_databases td ON td.tenant_id = t.id
LEFT JOIN tenant_runtime r ON r.tenant_id = t.id
ORDER BY t.id;

SELECT db_name, COUNT(*)
FROM tenant_databases
GROUP BY db_name
HAVING COUNT(*) <> 1;

SELECT tenant_id, COUNT(*)
FROM tenant_databases
GROUP BY tenant_id
HAVING COUNT(*) <> 1;

SELECT t.id
FROM tenants t
LEFT JOIN tenant_databases td ON td.tenant_id = t.id
WHERE t.estado IN ('activo', 'suspendido')
  AND (td.db_name IS NULL OR td.db_name = '');

SELECT t.id, t.estado, td.db_name
FROM tenants t
JOIN tenant_databases td ON td.tenant_id = t.id
LEFT JOIN pg_database p ON p.datname = td.db_name
WHERE t.estado IN ('activo', 'suspendido')
  AND p.oid IS NULL;
~~~

Las cuatro consultas de anomalías deben devolver cero filas. Si el inventario real
incluye clientes cancelados, una BD ausente puede ser intencional tras un
destroy: clasificarlos aparte con el propietario; no omitirlos ni reactivarlos
en silencio.

En **cada BD asignada y verificada**, consultar primero:

~~~sql
SELECT current_database() AS base_real;

SELECT to_regclass('public.tenant_schema_migrations') AS seguimiento,
       to_regclass('public.ia_acciones_pendientes') AS tabla_0015;
~~~

base_real solo confirma que la sesión de auditoría se conectó a la BD
prevista; además hay que comprobar el DB_NAME efectivo de la instancia.
El health HTTP solo hace SELECT 1: db=ok indica conectividad, **no** que la
instancia use la BD correcta.

Si existe seguimiento, consultar:

~~~sql
SELECT filename, applied_at
FROM tenant_schema_migrations
ORDER BY filename;
~~~

No usar tenant_databases.schema_version como prueba de estas migraciones:
el migrador real registra cada archivo en tenant_schema_migrations. El
script tools/migrate_tenants.py --dry-run no reemplaza estas consultas:
puede ejecutar CREATE TABLE IF NOT EXISTS dentro de una transacción y su
código de salida no certifica éxito por cliente.

## Publicación controlada

1. **Maestro primero.** Publicar el release aprobado de CyberShopAdmin por su
   procedimiento propio, verificar SHA, reiniciar solo cybershop-admin.service
   y confirmar que el archivo 0015 existe en
   /var/www/CyberShopAdmin/migrations/tenant/. Esto no lo hace el botón del
   cliente. Confirmar que el panel conserva el inventario, módulo y salud.
2. **Web después.** Publicar el release aprobado de CyberShop en origin/master
   solo tras resolver los cambios locales del VPS sin perderlos. Revisar el
   diff que traerá el helper. No forzar Git ni usar «Deploy completo» para
   saltar el gate de rutas públicas.
3. **Canario.** El propietario eligió Cyber Shop Colombia (principal) como
   primer cliente. Volver a respaldar su BD real y comprobar que el servicio
   cybershop.service, su ExecReload, el sitio y /api/v1/health están sanos.
   En admin.cybershopcol.com → ese cliente → Técnico, usar «Actualizar app
   (después del login)» una sola vez. Capturar hora y mensaje íntegro.
   Verificar SHA web instalado, fila de 0015 y tabla
   ia_acciones_pendientes **en la BD asignada al primario**, servicio activo,
   panel IA de solo lectura, datos/identidad/branding y flags apagados. El
   campo version del health puede ser genérico: usar SHA Git como evidencia.
   La instancia principal lee .cybershop.conf, no el env de Integraciones del
   maestro; no inferir de esa pantalla que Anthropic esté configurado o activo.
4. **Activos restantes, uno por vez.** Para cada id/slug obtenido del
   inventario: registrar BD y puerto/servicio; respaldo reciente; estado y
   conteos no sensibles de tablas críticas; pulsar su «Actualizar app»; luego
   verificar **todos los SQL esperados del release** (incluida 0015), tabla,
   servicio cybershop@slug activo, health con status/db=ok, acceso propio,
   marca/dominio y conteos esperados. No
   ejecutar en paralelo. Un éxito verde del panel no sustituye estas pruebas.
5. **Suspendidos.** Mantenerlos suspendidos y sus procesos apagados. No usar
   una acción que los arranque o recargue. Tras respaldo, aplicar únicamente
   «Solo migrar BD» a la BD exacta de cada uno, de forma secuencial, y
   verificar todas las migraciones esperadas, tabla 0015 y que servicio y
   estado sigan detenidos.
   El código compartido se cargará cuando el propietario reactive cada
   instancia en su flujo habitual; no afirmar smoke de aplicación activa.
6. Registrar por cliente: id/slug, BD verificada, estado inicial/final, SHA
   web/maestro, respaldo y prueba de lectura, migraciones antes/después,
   salud y marca, hora, operador y resultado. Sin secretos ni datos personales.
   La tarea termina solo cuando el inventario completo tiene evidencia;
   «primer clic exitoso» no equivale a «todos actualizados».

## Parada y recuperación

- Ante error, 504, migración incompleta, diferencia de datos/marca, servicio
  caído, presupuesto/flag inesperado o consulta que muestre otra BD: detener
  todos los siguientes clientes. No reintentar a ciegas.
- El botón hace: código web global → migración solo de esa BD → sincronización
  de aviso de cobro → recarga solo de esa instancia. Puede dejar código global
  actualizado aunque falle la migración o recarga; las migraciones anteriores
  a la fallida quedan confirmadas. No hay rollback automático.
- Diagnosticar Git, tenant_schema_migrations, logs del servicio, salud y
  respaldos de **ese** cliente antes de decidir recuperación. No usar un dump
  de A en B. Cualquier restauración exige plan propio y autorización humana.
- No habilitar ai_actions, ai_public ni Anthropic como parte de esta tarea.
  El chat público y su índice no quedan operativos solo por actualizar.

Referencias: ../DEPLOY.md, ../migrations/tenant/README.md,
../../CyberShop/app/docs/IA_ACTUALIZACION_CLIENTES.md y
../../CyberShop/app/docs/AUDITORIA_IA_MULTITENANT_2026-09.md.
