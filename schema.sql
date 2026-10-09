-- Ejecutar en SQL Editor de Supabase (proyecto dedicado a UN laboratorio).
-- RLS: usuarios autenticados comparten registros dentro de este proyecto.
create extension if not exists pgcrypto;
create table if not exists public.sucursales (
 id uuid primary key default gen_random_uuid(),
 codigo text not null unique, nombre text not null, activo boolean not null default true,
 creado_en timestamptz not null default now()
);
create table if not exists public.perfiles (
 usuario_id uuid primary key references auth.users(id) on delete cascade,
 rol text not null check (rol in ('administrador','sede')),
 sucursal_id uuid references public.sucursales(id),
 activo boolean not null default true,
 constraint perfil_sede check ((rol='administrador') or (rol='sede' and sucursal_id is not null))
);
create table if not exists public.muestras (
 sucursal_id uuid not null references public.sucursales(id),
 id uuid primary key default gen_random_uuid(),
 codigo text not null unique check (length(trim(codigo)) > 0),
 fecha_recepcion date not null default current_date,
 hora_recepcion time,
 proyecto text not null,
 cliente text,
 ubicacion text,
 calicata text,
 prof_inicio numeric(10,3) check (prof_inicio is null or prof_inicio >= 0),
 prof_fin numeric(10,3) check (prof_fin is null or prof_fin >= 0),
 tipo text not null default 'Alterada',
 cantidad_kg numeric(12,3) check (cantidad_kg is null or cantidad_kg > 0),
 embalaje text,
 condicion text not null default 'Buena',
 fecha_muestreo date,
 responsable_campo text,
 recibido_por text,
 ensayos_solicitados text,
 estado text not null default 'Recibida',
 almacenamiento text,
 observaciones text,
 custodia text,
 creado_por uuid not null default auth.uid(),
 creado_en timestamptz not null default now(),
 actualizado_en timestamptz not null default now(),
 constraint profundidad_valida check (prof_inicio is null or prof_fin is null or prof_fin >= prof_inicio)
);
create table if not exists public.ensayos (
 id uuid primary key default gen_random_uuid(),
 muestra_id uuid not null references public.muestras(id) on delete restrict,
 ensayo text not null,
 norma text,
 fecha_asignacion date,
 tecnico text,
 fecha_inicio date,
 fecha_fin date,
 resultado text,
 estado text not null default 'Pendiente',
 observaciones text,
 creado_por uuid not null default auth.uid(),
 creado_en timestamptz not null default now(),
 actualizado_en timestamptz not null default now(),
 constraint fechas_ensayo_validas check (fecha_inicio is null or fecha_fin is null or fecha_fin >= fecha_inicio)
);
create table if not exists public.bitacora (
 sucursal_id uuid references public.sucursales(id),
 id bigint generated always as identity primary key,
 tabla text not null,
 registro_id uuid not null,
 accion text not null,
 actor uuid default auth.uid(),
 fecha timestamptz not null default now(),
 antes jsonb,
 despues jsonb
);
create or replace function public.registrar_cambio() returns trigger language plpgsql security definer set search_path=public as $$
begin
  if TG_OP = 'UPDATE' then
    new.actualizado_en = now();
    insert into public.bitacora(tabla, registro_id, accion, actor, antes, despues, sucursal_id)
      values (TG_TABLE_NAME, new.id, 'ACTUALIZAR', auth.uid(), to_jsonb(old), to_jsonb(new), case when TG_TABLE_NAME='muestras' then new.sucursal_id else (select sucursal_id from public.muestras where id=new.muestra_id) end);
    return new;
  elsif TG_OP = 'INSERT' then
    insert into public.bitacora(tabla, registro_id, accion, actor, antes, despues, sucursal_id)
      values (TG_TABLE_NAME, new.id, 'CREAR', auth.uid(), null, to_jsonb(new), case when TG_TABLE_NAME='muestras' then new.sucursal_id else (select sucursal_id from public.muestras where id=new.muestra_id) end);
    return new;
  end if;
  return null;
end $$;
drop trigger if exists audit_muestras on public.muestras;
create trigger audit_muestras before insert or update on public.muestras for each row execute function public.registrar_cambio();
drop trigger if exists audit_ensayos on public.ensayos;
create trigger audit_ensayos before insert or update on public.ensayos for each row execute function public.registrar_cambio();
create index if not exists idx_muestras_sucursal on public.muestras(sucursal_id);
create index if not exists idx_muestras_fecha on public.muestras (fecha_recepcion desc);
create index if not exists idx_ensayos_muestra on public.ensayos (muestra_id);
create index if not exists idx_bitacora_fecha on public.bitacora (fecha desc);
-- Autorizar por membresía de sucursal, siempre desde la base de datos (no solo filtros UI).
create or replace function public.es_administrador() returns boolean
language sql stable security definer set search_path=public as $$
 select exists(select 1 from public.perfiles where usuario_id=auth.uid() and rol='administrador' and activo);
$$;
create or replace function public.puede_acceder_sucursal(sid uuid) returns boolean
language sql stable security definer set search_path=public as $$
 select exists(select 1 from public.perfiles where usuario_id=auth.uid() and activo
   and (rol='administrador' or (rol='sede' and sucursal_id=sid)));
$$;
revoke all on function public.es_administrador() from public;
revoke all on function public.puede_acceder_sucursal(uuid) from public;
grant execute on function public.es_administrador() to authenticated;
grant execute on function public.puede_acceder_sucursal(uuid) to authenticated;

alter table public.sucursales enable row level security;
alter table public.perfiles enable row level security;
alter table public.muestras enable row level security;
alter table public.ensayos enable row level security;
alter table public.bitacora enable row level security;

create policy sucursales_lectura on public.sucursales for select to authenticated
 using (public.puede_acceder_sucursal(id));
create policy perfiles_lectura on public.perfiles for select to authenticated
 using (usuario_id=auth.uid() or public.es_administrador());
create policy muestras_lectura on public.muestras for select to authenticated
 using (public.puede_acceder_sucursal(sucursal_id));
create policy muestras_crear on public.muestras for insert to authenticated
 with check (public.puede_acceder_sucursal(sucursal_id) and creado_por=auth.uid());
create policy muestras_modificar on public.muestras for update to authenticated
 using (public.puede_acceder_sucursal(sucursal_id))
 with check (public.puede_acceder_sucursal(sucursal_id));
create policy ensayos_lectura on public.ensayos for select to authenticated
 using (exists(select 1 from public.muestras m where m.id=muestra_id and public.puede_acceder_sucursal(m.sucursal_id)));
create policy ensayos_crear on public.ensayos for insert to authenticated
 with check (creado_por=auth.uid() and exists(select 1 from public.muestras m where m.id=muestra_id and public.puede_acceder_sucursal(m.sucursal_id)));
create policy ensayos_modificar on public.ensayos for update to authenticated
 using (exists(select 1 from public.muestras m where m.id=muestra_id and public.puede_acceder_sucursal(m.sucursal_id)))
 with check (exists(select 1 from public.muestras m where m.id=muestra_id and public.puede_acceder_sucursal(m.sucursal_id)));
create policy bitacora_lectura on public.bitacora for select to authenticated
 using (public.puede_acceder_sucursal(sucursal_id));

grant usage on schema public to authenticated;
grant select on public.sucursales,public.perfiles to authenticated;
grant select,insert,update on public.muestras,public.ensayos to authenticated;
grant select on public.bitacora to authenticated;
-- El administrador da de alta nuevas sedes y asigna roles desde el SQL Editor,
-- usando un rol administrativo de Supabase y no una clave en el frontend.
-- Ejemplos de provisión:
-- insert into public.sucursales(codigo,nombre) values ('CENTRAL','Sede Central'),('CUTERVO','Sucursal Cutervo');
-- insert into public.perfiles(usuario_id,rol) values ('UUID-USUARIO-ADMIN','administrador');
-- insert into public.perfiles(usuario_id,rol,sucursal_id)
-- select 'UUID-USUARIO-OPERADOR','sede',id from public.sucursales where codigo='CUTERVO';
