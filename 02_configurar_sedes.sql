-- Ejecutar DESPUÉS de schema.sql en el SQL Editor de Supabase.
-- Crea las 6 sedes iniciales; se pueden añadir más por SQL Editor.
-- Ejecutar con privilegios de administrador del proyecto.
insert into public.sucursales (codigo,nombre,activo) values
('LIM','Lima (Sede principal)',true),
('CAJ','Cajamarca',true),
('JAE','Jaén',true),
('CHA','Chachapoyas',true),
('MER','La Merced',true),
('PAS','Pasco',true)
on conflict (codigo) do nothing;

-- Para dar de alta a un administrador, crear primero su cuenta en Authentication.
-- Luego reemplazar el UUID siguiente y EJECUTAR esta instrucción por separado:
-- insert into public.perfiles(usuario_id,rol) values ('UUID-ADMIN-REAL','administrador');

-- Para asociar a un operador de Jaén, crear primero su cuenta y luego:
-- insert into public.perfiles(usuario_id,rol,sucursal_id)
-- select 'UUID-OPERADOR-REAL','sede',id from public.sucursales where codigo='JAE';

-- Para agregar sucursales futuras:
-- insert into public.sucursales(codigo,nombre) values ('NUE','Nueva sucursal');
