# MISOFT – V3 / Suelos y concreto (multisucursal)

Incluye módulos Registro de excavación, Clasificación de suelo, Granulometría, Humedad, Límites, Proctor, Corte directo, Capacidad portante y Sales; probetas de concreto, compresión y resistencia; edición/desactivación de sedes.

## Instalación
1. Crear Supabase y ejecutar `schema.sql` si es instalación nueva.
2. Ejecutar `02_configurar_sedes.sql`, y luego `03_habilitar_alta_sedes.sql`.
3. **Ejecutar `04_modulos_suelos_concreto.sql`**, incluso en instalaciones existentes.
4. Crear usuarios y perfiles de acceso en Supabase; configurar `SUPABASE_URL` y `SUPABASE_ANON_KEY` en secretos de Streamlit.
5. Instalar `requirements.txt` y lanzar `streamlit run app.py`, o desplegar en Streamlit Cloud.

## Alcance técnico
- Los módulos de suelos son fichas estructuradas de registro con algunos cálculos directos ilustrativos (humedad, IP, balance de masas); NO son hojas de cálculo normativas completamente automatizadas. Capacidad portante y corte directo guardan parámetros/resultados validados por profesional.
- Compresión de concreto calcula f = carga (N) / área transversal (mm²) en MPa, según geometría seleccionada. No sustituye calibración, corrección geometría, refrentado, verificación de prensa ni requisitos de aceptación.
- Confirmar normas vigentes NTP / ASTM de cada ensayo antes de emitir reportes acreditables.
- Desactivar sede preserva sus registros. El administrador central mantiene consulta histórica.
- Esta entrega incluye código y migración, pero no está desplegada, ni probada contra un proyecto real de Supabase.
