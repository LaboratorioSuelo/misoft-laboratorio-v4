-- MIGRACIÓN V3 - Ejecutar DESPUÉS de schema.sql y 03_habilitar_alta_sedes.sql
-- Permitir editar/desactivar sede: no se eliminan datos históricos.
grant update on public.sucursales to authenticated;
drop policy if exists sucursales_admin_editar on public.sucursales;
create policy sucursales_admin_editar on public.sucursales for update to authenticated
 using (public.es_administrador()) with check (public.es_administrador());
-- Impedir que personal de sedes inactivas acceda a registros o inserte nuevos.
create or replace function public.puede_acceder_sucursal(sid uuid) returns boolean
language sql stable security definer set search_path=public as $$
 select exists(select 1 from public.perfiles p where p.usuario_id=auth.uid() and p.activo
   and (p.rol='administrador' or (p.rol='sede' and p.sucursal_id=sid
     and exists(select 1 from public.sucursales s where s.id=sid and s.activo))));
$$;
-- Validar también en BD que nadie desactive la sede principal.
create or replace function public.proteger_sede_central() returns trigger language plpgsql as $$
begin
 if old.codigo='LIM' and not new.activo then raise exception 'No se puede desactivar la sede LIM'; end if;
 if old.codigo<>new.codigo then raise exception 'El código de sede no se puede editar'; end if;
 return new;
end $$;
drop trigger if exists proteger_sede_central on public.sucursales;
create trigger proteger_sede_central before update on public.sucursales for each row execute function public.proteger_sede_central();

create table if not exists public.fichas_suelo (
 id uuid primary key default gen_random_uuid(),
 muestra_id uuid not null references public.muestras(id) on delete restrict,
 tipo text not null, datos jsonb not null default '{}'::jsonb,
 norma text, tecnico text, estado text not null default 'Borrador',
 observaciones text, creado_por uuid not null default auth.uid(),
 creado_en timestamptz not null default now(), actualizado_en timestamptz not null default now()
);
create index if not exists fichas_suelo_muestra_idx on public.fichas_suelo(muestra_id,tipo);
create table if not exists public.probetas_concreto (
 id uuid primary key default gen_random_uuid(), sucursal_id uuid not null references public.sucursales(id),
 codigo text not null unique, proyecto text not null, elemento text, geometria text not null,
 curado text, fecha_moldeo date, fecha_rotura date, edad_dias integer,
 fc_mpa numeric, diametro_mm numeric, altura_mm numeric, carga_kn numeric, resistencia_mpa numeric,
 norma text, tecnico text, estado text not null default 'Recibida', observaciones text,
 creado_por uuid not null default auth.uid(), creado_en timestamptz not null default now(),
 actualizado_en timestamptz not null default now()
);
create index if not exists probetas_concreto_sucursal_idx on public.probetas_concreto(sucursal_id);

create or replace function public.auditar_v3() returns trigger language plpgsql security definer set search_path=public as $$
declare sid uuid;
begin
 if tg_table_name='fichas_suelo' then
  select sucursal_id into sid from public.muestras where id=new.muestra_id;
 else sid:=new.sucursal_id; end if;
 if tg_op='UPDATE' then
  new.actualizado_en:=now();
  insert into public.bitacora(sucursal_id,tabla,registro_id,accion,actor,antes,despues)
   values (sid,tg_table_name,new.id,'ACTUALIZAR',auth.uid(),to_jsonb(old),to_jsonb(new));
 else
  insert into public.bitacora(sucursal_id,tabla,registro_id,accion,actor,antes,despues)
   values (sid,tg_table_name,new.id,'CREAR',auth.uid(),null,to_jsonb(new));
 end if;
 return new;
end $$;
drop trigger if exists audit_fichas_suelo on public.fichas_suelo;
create trigger audit_fichas_suelo before insert or update on public.fichas_suelo for each row execute function public.auditar_v3();
drop trigger if exists audit_probetas_concreto on public.probetas_concreto;
create trigger audit_probetas_concreto before insert or update on public.probetas_concreto for each row execute function public.auditar_v3();

alter table public.fichas_suelo enable row level security;
alter table public.probetas_concreto enable row level security;
drop policy if exists ficha_ver on public.fichas_suelo;
create policy ficha_ver on public.fichas_suelo for select to authenticated
using (exists(select 1 from public.muestras m where m.id=muestra_id and public.puede_acceder_sucursal(m.sucursal_id)));
drop policy if exists ficha_crear on public.fichas_suelo;
create policy ficha_crear on public.fichas_suelo for insert to authenticated
with check (creado_por=auth.uid() and exists(select 1 from public.muestras m where m.id=muestra_id and public.puede_acceder_sucursal(m.sucursal_id)));
drop policy if exists ficha_editar on public.fichas_suelo;
create policy ficha_editar on public.fichas_suelo for update to authenticated
using (exists(select 1 from public.muestras m where m.id=muestra_id and public.puede_acceder_sucursal(m.sucursal_id)))
with check (exists(select 1 from public.muestras m where m.id=muestra_id and public.puede_acceder_sucursal(m.sucursal_id)));
drop policy if exists probeta_ver on public.probetas_concreto;
create policy probeta_ver on public.probetas_concreto for select to authenticated
using (public.puede_acceder_sucursal(sucursal_id));
drop policy if exists probeta_crear on public.probetas_concreto;
create policy probeta_crear on public.probetas_concreto for insert to authenticated
with check (creado_por=auth.uid() and public.puede_acceder_sucursal(sucursal_id)
 and exists(select 1 from public.sucursales s where s.id=sucursal_id and s.activo));
drop policy if exists probeta_editar on public.probetas_concreto;
create policy probeta_editar on public.probetas_concreto for update to authenticated
using (public.puede_acceder_sucursal(sucursal_id))
with check (public.puede_acceder_sucursal(sucursal_id));
grant select,insert,update on public.fichas_suelo,public.probetas_concreto to authenticated;
