-- Ejecutar una sola vez en SQL Editor de Supabase, sobre una instalación existente.
-- Permite alta de sedes exclusivamente al administrador autenticado.
-- El control se aplica en PostgreSQL (RLS), no únicamente en la interfaz.
grant insert on public.sucursales to authenticated;
drop policy if exists sucursales_admin_crear on public.sucursales;
create policy sucursales_admin_crear on public.sucursales
for insert to authenticated
with check (public.es_administrador() and activo = true);
-- Se mantienen las políticas existentes de lectura y los seis registros actuales.
