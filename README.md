# APLICATIVO PERSONALIZADO - LABORATORIO DE SUELOS & CONCRETO MISOFT E.I.R.L.

**Razón social / nombre mostrado:** Laboratorio de Suelos & Concreto Misoft E.I.R.L.
**Sede principal:** Lima.
**Sucursales iniciales:** Cajamarca, Jaén, Chachapoyas, La Merced y Pasco.
**Total inicial:** 6 sedes. Se pueden agregar más sin modificar el modelo de datos.

## Primera instalación
1. Crear proyecto nuevo en Supabase.
2. Ejecutar `schema.sql` en SQL Editor.
3. Ejecutar `02_configurar_sedes.sql` para crear las seis sedes.
4. Crear los usuarios en Supabase Authentication y asignar roles/perfiles con los comandos de ejemplo del archivo SQL. Los UUID son marcadores de ejemplo: **no ejecutar sin reemplazarlos**.
5. Desplegar `app.py` en Streamlit Community Cloud y configurar los secretos según `.streamlit/secrets.toml.example`.
6. Comprobar la segregación por sede, la vista general de administración, la exportación y el historial con usuarios de prueba.

## Identificación sugerida de muestras
`LIM-2026-C01-M001`, `CAJ-2026-C01-M001`, `JAE-2026-C01-M001`, `CHA-2026-C01-M001`, `MER-2026-C01-M001`, `PAS-2026-C01-M001`. El código lo registra el técnico y debe ser único globalmente; **no existe aún numeración automática ni bloqueo de prefijo según sede**.

## Identidad de laboratorio
El nombre «Laboratorio de Suelos & Concreto Misoft E.I.R.L.» está configurado en `NOMBRE_LABORATORIO` de `app.py` y se muestra en acceso, navegación y panel principal.

## Consideraciones
- Esta entrega es código preparado para instalación; no está publicada en internet, ni tiene usuarios reales creados ni registros cargados.
- Sin migración automática desde el Excel inicial.
- El administrador central puede consultar todas las sedes; los perfiles de sucursal quedan delimitados por controles en base de datos.
- Agregar futuras sedes desde Supabase SQL Editor.
- Antes de producción realizar pruebas de permisos, respaldos, auditoría y seguridad; el sistema no emite certificados o informes técnicos firmados.

---

# Laboratorio de suelos — Aplicativo web en la nube

Aplicación Streamlit con base de datos PostgreSQL alojada en Supabase, diseñada a partir del libro «Registro_Muestras_Laboratorio_Suelos.xlsx».

## Funciones
- Autenticación por correo y contraseña (Supabase Auth).
- Registro, edición y consulta de muestras con código único, calicata, profundidad, cadena de custodia, recepción y almacenamiento.
- Registro y seguimiento de múltiples ensayos por muestra.
- Panel con conteos y gráficos; filtros y exportación a Excel.
- Bitácora de creación y cambios almacenada por disparadores en PostgreSQL.
- Seguridad RLS, sin permitir borrado de registros.

## Despliegue en la nube (Streamlit Community Cloud + Supabase)
1. Crear una cuenta/proyecto en **https://supabase.com** para un laboratorio (no mezclar laboratorios independientes en el mismo proyecto).
2. En **SQL Editor**, pegar el contenido de `schema.sql` y ejecutarlo. Verificar que aparecen `muestras`, `ensayos` y `bitacora`.
3. Ejecutar `02_configurar_sedes.sql` en SQL Editor para cargar Lima, Cajamarca, Jaén, Chachapoyas, La Merced y Pasco. En **Authentication → Users**, invitar/crear usuarios para el personal, con contraseña individual. Revisar si el proyecto exige confirmación de correo.
4. En **Project Settings → API** (o **Connect**, según interfaz), obtener la URL del proyecto y la clave **anon/publishable**. No usar una clave `service_role` ni una clave secreta en esta aplicación.
5. Subir `app.py`, `schema.sql`, `requirements.txt` y carpeta `.streamlit` a un repositorio privado GitHub.
6. En **https://share.streamlit.io**, desplegar una aplicación apuntando a `app.py` del repositorio.
7. En los **Secrets** de Streamlit Cloud colocar:
   ```toml
   SUPABASE_URL = "https://SU-PROYECTO.supabase.co"
   SUPABASE_ANON_KEY = "SU-CLAVE-PUBLICABLE"
   ```
8. Abrir la URL de Streamlit, iniciar sesión y registrar una muestra de prueba. Comprobar que los registros persisten al cerrar sesión y entrar desde otro dispositivo.

## Ejecución local
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Editar .streamlit/secrets.toml con credenciales válidas
streamlit run app.py
```

## Seguridad y alcance
- **Los datos solo quedan en la nube luego del despliegue y conexión a Supabase.** El ZIP por sí solo no constituye un servicio publicado.
- La RLS limita el acceso por sucursal; únicamente el administrador central puede consultar todas las sedes. Se recomienda verificar los permisos con usuarios reales antes del uso en producción.
- Compartir únicamente la clave anon/publishable, nunca la service_role/secret; no subir `.streamlit/secrets.toml` real al repositorio.
- Se admiten hasta 5000 registros por tabla en las vistas en su configuración actual; agregar paginación para mayor volumen.
- El campo resultado/referencia de archivo es texto: esta versión no carga PDF ni adjuntos a almacenamiento remoto.
- La interfaz no borra datos. Para producción, configurar copias de seguridad automáticas, retención documental y controles de acceso; supervisar capacidad y costos de los proveedores.
- **No se han migrado automáticamente los datos preexistentes del Excel.** Se pueden registrar manualmente o desarrollar una importación validada.
- Antes de emitir informes oficiales, verificar versión de normas técnicas, métodos de ensayo, calibraciones y responsabilidades profesionales.

## Nueva versión: un laboratorio con varias sucursales
- Instalación **nueva**: utilice el `schema.sql` incluido en este paquete (reemplaza el esquema mono-sede anterior).
- La base de datos contiene `sucursales`, `perfiles`, `muestras`, `ensayos` y `bitacora`.
- El **administrador central** tiene permiso para consultar y editar muestras/ensayos de todas las sucursales; puede filtrar el panel por sede.
- El **usuario de sucursal** solo ve y edita muestras/ensayos asignados a su sucursal, mediante políticas de seguridad RLS reales en PostgreSQL.
- Se asocian a una sucursal las muestras, sus ensayos y sus entradas en bitácora.
- Los **códigos de muestra deben ser únicos en todo el laboratorio**. Se recomienda prefijo de sede: `CUT-2026-C01-M001`.

### Configuración inicial obligatoria
1. Crear proyecto Supabase nuevo, ejecutar `schema.sql` en SQL Editor.
2. Crear las cuentas en Authentication > Users (con invitación/confirmación según configuración).
3. Ejecutar en SQL Editor las tres instrucciones de ejemplo comentadas al final de `schema.sql`, sustituyendo UUID de usuario y nombre/código de cada sede.
4. El primer usuario administrador **debe asignarse manualmente** desde SQL Editor con permisos administrativos.
5. Desplegar `app.py` en Streamlit Cloud con URL y clave pública del proyecto en Secrets.
6. Comprobar con dos usuarios de distintas sedes que uno no visualiza registros de la otra, y que el administrador sí.

**Importante:** El nuevo `schema.sql` está destinado a instalaciones nuevas y no actualiza automáticamente una base anterior que ya tiene muestras. Para migrar una base existente es necesario respaldarla, asignar `sucursal_id` a registros históricos y aplicar una migración supervisada. La administración de sucursales/usuarios se hace inicialmente desde Supabase (SQL Editor/Auth), no desde el panel web. La tabla bitácora debe mantenerse accesible solo para lectura; los triggers registran cambios por usuario.


## Agregar nuevas sedes desde el aplicativo

1. Si la base ya existe, ejecute `03_habilitar_alta_sedes.sql` en Supabase SQL Editor. Si instala desde cero, ejecute `schema.sql`, `02_configurar_sedes.sql` y luego `03_habilitar_alta_sedes.sql`.
2. Ingrese con un usuario cuyo perfil tenga `rol='administrador'` y `activo=true`.
3. Abra el menú **Administrar sedes → Agregar nueva sede**. Ingrese un código alfanumérico único (2 a 12 caracteres) y un nombre de sede; seleccione **Guardar sede**.
4. Actualice los datos. La sede se incorpora a los filtros, recepción de muestras y reportes.
5. Cree en Supabase Authentication las cuentas de usuarios de esa sede y asócielas mediante `public.perfiles` usando el identificador UUID de la sucursal. La creación de usuarios no forma parte del formulario de sedes.

**Seguridad:** el formulario solo se presenta a administradores; PostgreSQL RLS valida además cada inserción. Ninguna clave `service_role` debe colocarse en Streamlit. No se habilita eliminación automática de sedes para conservar la trazabilidad histórica.
