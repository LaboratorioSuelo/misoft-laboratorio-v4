"""Laboratorio de Suelos & Concreto Misoft E.I.R.L.: gestión multisucursal."""
import io
import os
import re
from datetime import date, datetime, time
import pandas as pd
import streamlit as st
from supabase import create_client

NOMBRE_LABORATORIO = "Laboratorio de Suelos & Concreto Misoft E.I.R.L."
SEDE_PRINCIPAL = "Lima"
SEDES_INICIALES = ["Lima", "Cajamarca", "Jaén", "Chachapoyas", "La Merced", "Pasco"]
st.set_page_config(page_title=NOMBRE_LABORATORIO, page_icon="🧪", layout="wide")
st.markdown("""<style>
.block-container {padding-top:1.7rem;max-width:1500px;}
[data-testid="stMetric"] {background:#f4f7fa;padding:12px 18px;border-radius:10px;border:1px solid #e3eaf1;}
</style>""", unsafe_allow_html=True)

TIPOS = ['Alterada', 'Inalterada', 'Remoldeada', 'Roca', 'Otro']
CONDICIONES = ['Buena', 'Húmeda', 'Embalaje deteriorado', 'Sin identificación', 'Contaminada', 'Rechazada']
ESTADOS_M = ['Recibida', 'En preparación', 'En ensayo', 'Ensayos concluidos', 'Informe entregado', 'Rechazada']
ESTADOS_E = ['Pendiente', 'Asignado', 'En proceso', 'Terminado', 'Informado', 'Anulado']
PRUEBAS = ['Contenido de humedad', 'Granulometría por tamizado', 'Granulometría por sedimentación',
          'Límites de Atterberg', 'Gravedad específica', 'Proctor estándar', 'Proctor modificado',
          'CBR', 'Corte directo', 'Compresión triaxial', 'Compresión inconfinada',
          'Consolidación', 'Densidad natural', 'Sales solubles', 'Otro']
COLUMNAS_M = {
 'sucursal_nombre':'Sucursal','codigo':'Código muestra','fecha_recepcion':'Fecha recepción','hora_recepcion':'Hora recepción',
 'proyecto':'Proyecto / obra','cliente':'Cliente / entidad','ubicacion':'Ubicación / sector',
 'calicata':'Calicata / sondeo','prof_inicio':'Prof. inicial (m)','prof_fin':'Prof. final (m)',
 'tipo':'Tipo muestra','cantidad_kg':'Cantidad (kg)','embalaje':'Embalaje',
 'condicion':'Condición recepción','fecha_muestreo':'Fecha muestreo',
 'responsable_campo':'Responsable campo','recibido_por':'Recibido por',
 'ensayos_solicitados':'Ensayos solicitados','estado':'Estado muestra',
 'almacenamiento':'Almacenamiento','observaciones':'Observaciones','custodia':'N° cadena custodia'
}
COLUMNAS_E = {'ensayo':'Ensayo','norma':'Norma / método','fecha_asignacion':'Fecha asignación',
 'tecnico':'Técnico responsable','fecha_inicio':'Fecha inicio','fecha_fin':'Fecha fin',
 'resultado':'Resultado / archivo','estado':'Estado ensayo','observaciones':'Observaciones'}

def secret(name):
    try: return st.secrets[name]
    except Exception: return os.getenv(name)

if not secret('SUPABASE_URL') or not secret('SUPABASE_ANON_KEY'):
    st.error('Faltan SUPABASE_URL y SUPABASE_ANON_KEY. Consulte README.md antes de usar el aplicativo.')
    st.stop()

if 'db' not in st.session_state:
    st.session_state.db = create_client(secret('SUPABASE_URL'), secret('SUPABASE_ANON_KEY'))

client = st.session_state.db

if not st.session_state.get('autenticado', False):
    st.title('🧪 ' + NOMBRE_LABORATORIO)
    st.caption('Sistema de gestión de muestras y ensayos · Sede central Lima · Acceso para personal autorizado')
    with st.form('acceso'):
        email = st.text_input('Correo electrónico')
        clave = st.text_input('Contraseña', type='password')
        entrar = st.form_submit_button('Ingresar', type='primary')
    if entrar:
        try:
            res = client.auth.sign_in_with_password({'email':email.strip(), 'password':clave})
            st.session_state.autenticado = bool(res.session)
            st.session_state.usuario = res.user.email
            st.rerun()
        except Exception:
            st.error('No se pudo iniciar sesión. Revise el usuario, contraseña o configuración.')
    st.stop()

# Las políticas RLS en PostgreSQL aplican separación real por sucursal.
try:
    uid=client.auth.get_user().user.id
    perfil_rows=client.table('perfiles').select('rol,sucursal_id,activo').eq('usuario_id',uid).execute().data
    if not perfil_rows or not perfil_rows[0]['activo']:
        st.error('Su usuario no tiene perfil activo. Solicite al administrador asignación de sede.');st.stop()
    perfil=perfil_rows[0]
    sucursales=client.table('sucursales').select('id,codigo,nombre,activo').eq('activo',True).order('nombre').execute().data or []
except Exception as ex:
    st.error(f'No se pudo verificar su perfil o las sucursales: {ex}');st.stop()

if perfil['rol']=='administrador':
    nombres={'Todas las sucursales':None}
    nombres.update({f"{x['codigo']} · {x['nombre']}":x['id'] for x in sucursales})
    with st.sidebar:
        sede_etiqueta=st.selectbox('Sucursal para consultar',list(nombres))
    sucursal_filtro=nombres[sede_etiqueta]
else:
    sucursal_filtro=perfil['sucursal_id']
    sede=next((x for x in sucursales if x['id']==sucursal_filtro),None)
    if not sede:
        st.error('Sucursal inactiva o no asignada. Contacte al administrador.');st.stop()
    with st.sidebar:st.caption(f"Sucursal: {sede['nombre']}")

@st.cache_data(ttl=15, show_spinner=False)
def lista_sucursales(_usuario, refresh):
    return client.table('sucursales').select('id,codigo,nombre').execute().data or []

@st.cache_data(ttl=15, show_spinner=False)
def lista_muestras(_usuario, refresh):
    return client.table('muestras').select('*,sucursales(nombre)').order('fecha_recepcion', desc=True).limit(5000).execute().data or []

@st.cache_data(ttl=15, show_spinner=False)
def lista_ensayos(_usuario, refresh):
    return client.table('ensayos').select('*').order('creado_en', desc=True).limit(5000).execute().data or []

def refrescar():
    st.session_state['revision'] = st.session_state.get('revision',0)+1
    st.cache_data.clear()

def fdate(value):
    if not value:return None
    try:return date.fromisoformat(str(value)[:10])
    except (ValueError,TypeError): return None

def texto(v):return '' if v is None else str(v)
def fecha_iso(v):return v.isoformat() if v is not None else None

def excel_bytes(df):
    buf=io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Registro')
        ws=writer.sheets['Registro']; ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
        for col in ws.columns:
            key=col[0].column_letter
            ws.column_dimensions[key].width=min(max(max(len(str(c.value or '')) for c in list(col)[:101])+2,14),45)
    return buf.getvalue()

with st.sidebar:
    st.header('🧪 ' + NOMBRE_LABORATORIO)
    st.caption(st.session_state.get('usuario',''))
    modulos=['Panel de control','Recepción de muestras','Seguimiento de ensayos','Ensayos de suelos','Ensayos de concreto','Hojas técnicas e informes','Trazabilidad y exportación']
    if perfil['rol']=='administrador':modulos.append('Administrar sedes')
    pagina=st.radio('Módulos',modulos)
    if st.button('🔄 Actualizar datos',use_container_width=True):refrescar();st.rerun()
    if st.button('Cerrar sesión',use_container_width=True):
        client.auth.sign_out()
        for k in ['autenticado','usuario','db']:st.session_state.pop(k,None)
        st.cache_data.clear();st.rerun()

try:
    rev=st.session_state.get('revision',0)
    muestras_todas=lista_muestras(st.session_state.usuario,rev)
    ensayos_todos=lista_ensayos(st.session_state.usuario,rev)
    muestras=[dict(m, sucursal_nombre=(m.get('sucursales') or {}).get('nombre','')) for m in muestras_todas if sucursal_filtro is None or m.get('sucursal_id')==sucursal_filtro]
    ids_visibles={m['id'] for m in muestras}
    ensayos=[e for e in ensayos_todos if e['muestra_id'] in ids_visibles]
except Exception as err:
    st.error(f'No se pueden leer los datos. Revise tablas, políticas RLS o conexión: {err}')
    st.stop()

mapa={m['id']:m for m in muestras}

def tabla_muestras(datos):
    if not datos:return pd.DataFrame(columns=['Código muestra','Proyecto / obra','Fecha recepción','Estado muestra'])
    return pd.DataFrame(datos).reindex(columns=list(COLUMNAS_M)).rename(columns=COLUMNAS_M)

def tabla_ensayos(datos):
    if not datos:return pd.DataFrame(columns=['Código muestra',*COLUMNAS_E.values()])
    df=pd.DataFrame(datos)
    df.insert(0,'Código muestra',df.muestra_id.map(lambda x:mapa.get(x,{}).get('codigo','SIN VINCULAR')))
    return df.reindex(columns=['Código muestra',*COLUMNAS_E]).rename(columns=COLUMNAS_E)

st.title(pagina)
st.caption(f'{NOMBRE_LABORATORIO} · Sede principal: {SEDE_PRINCIPAL} · {len(sucursales)} sedes activas')
if pagina=='Administrar sedes':
    if perfil['rol']!='administrador':
        st.error('Acceso exclusivo de administración central.');st.stop()
    st.info('Las sedes nuevas aparecen automáticamente en los formularios y filtros. La asignación de usuarios se efectúa por separado en Supabase Authentication y perfiles.')
    st.subheader('Sedes registradas')
    try:
        listado=client.table('sucursales').select('id,codigo,nombre,activo,creado_en').order('nombre').execute().data or []
        st.dataframe(pd.DataFrame([{'Código':x['codigo'],'Sede':x['nombre'],'Activa':x['activo'],'Creada':x.get('creado_en','')} for x in listado]),hide_index=True,use_container_width=True)
    except Exception as exc:
        st.error(f'No se pudieron consultar todas las sedes: {exc}')
        listado=sucursales
    st.subheader('Agregar nueva sede')
    with st.form('nueva_sede',clear_on_submit=True):
        nuevo_codigo=st.text_input('Código único de sede *',max_chars=12,placeholder='CUT')
        nuevo_nombre=st.text_input('Nombre o ciudad de la sede *',max_chars=120,placeholder='Cutervo')
        guardar_sede=st.form_submit_button('➕ Guardar sede',type='primary')
    if guardar_sede:
        cod=nuevo_codigo.strip().upper()
        nom=' '.join(nuevo_nombre.split())
        prev_cod={x['codigo'].upper() for x in listado}
        prev_nom={x['nombre'].strip().casefold() for x in listado}
        if not re.fullmatch(r'[A-Z0-9]{2,12}',cod):
            st.error('El código debe tener de 2 a 12 caracteres: letras A-Z y números, sin espacios.')
        elif len(nom)<2:
            st.error('Ingrese un nombre de sede válido (mínimo 2 caracteres).')
        elif cod in prev_cod or nom.casefold() in prev_nom:
            st.error('Ya existe una sede con ese código o nombre.')
        else:
            try:
                client.table('sucursales').insert({'codigo':cod,'nombre':nom,'activo':True}).execute()
                refrescar()
                st.success(f'Sede {nom} ({cod}) registrada correctamente. Actualice la página para verla en los filtros.')
            except Exception as exc:
                st.error(f'No fue posible registrar la sede. Verifique la migración SQL y los permisos: {exc}')
    st.subheader('Editar o desactivar sede')
    if listado:
        etiquetas={f"{x['codigo']} · {x['nombre']} · {'Activa' if x['activo'] else 'Inactiva'}":x for x in listado}
        escogida=etiquetas[st.selectbox('Seleccionar sede a gestionar',list(etiquetas))]
        with st.form('editar_sede'):
            nombre_editado=st.text_input('Nuevo nombre de sede',value=escogida['nombre'])
            activa=st.checkbox('Sede activa',value=bool(escogida['activo']))
            confirmar=st.checkbox('Confirmo la modificación del estado o nombre de esta sede')
            guardar_edicion=st.form_submit_button('Guardar cambios de sede')
        if guardar_edicion:
            nom=' '.join(nombre_editado.split())
            nombres_otros={x['nombre'].casefold() for x in listado if x['id']!=escogida['id']}
            if not confirmar:st.error('Debe confirmar la modificación.')
            elif len(nom)<2 or nom.casefold() in nombres_otros:st.error('Nombre inválido o duplicado.')
            elif escogida['codigo']=='LIM' and not activa:st.error('La sede central LIM no puede desactivarse desde esta pantalla.')
            else:
                try:
                    client.table('sucursales').update({'nombre':nom,'activo':activa}).eq('id',escogida['id']).execute()
                    refrescar();st.success('Sede actualizada. Se preservan sus muestras, ensayos e historial.');st.rerun()
                except Exception as exc:st.error(f'No se pudo modificar la sede: {exc}')
    st.caption('La desactivación impide nuevos registros operativos de usuarios de esa sede; nunca elimina los datos existentes.')

if pagina=='Panel de control':
    total=len(muestras); enp=sum(x.get('estado')=='En ensayo' for x in muestras)
    completos=sum(x.get('estado') in ['Ensayos concluidos','Informe entregado'] for x in muestras)
    pendientes=sum(x.get('estado') in ['Pendiente','Asignado'] for x in ensayos)
    a,b,c,d=st.columns(4)
    a.metric('Muestras recibidas',total)
    b.metric('En ensayo',enp)
    c.metric('Concluidas / entregadas',completos)
    d.metric('Ensayos pendientes',pendientes)
    if perfil['rol']=='administrador':
        st.subheader('Muestras registradas por sede')
        resumen=[]
        for sede_item in sucursales:
            registros=[m for m in muestras_todas if m.get('sucursal_id')==sede_item['id']]
            resumen.append({'Sucursal':sede_item['nombre'], 'Código':sede_item['codigo'],
                'Muestras':len(registros),
                'En ensayo':sum(m.get('estado')=='En ensayo' for m in registros),
                'Concluidas':sum(m.get('estado') in ('Ensayos concluidos','Informe entregado') for m in registros)})
        st.dataframe(pd.DataFrame(resumen),hide_index=True,use_container_width=True)
    st.subheader('Estado de muestras')
    if muestras:
        ch=pd.Series([m['estado'] for m in muestras]).value_counts()
        st.bar_chart(ch)
    else:st.info('No existen muestras registradas. Comience en Recepción de muestras.')
    st.subheader('Últimas muestras')
    st.dataframe(tabla_muestras(muestras[:20]),use_container_width=True,hide_index=True)

elif pagina=='Recepción de muestras':
    modo=st.radio('Operación',['Registrar muestra','Editar muestra','Consultar muestras'],horizontal=True)
    origen={}
    if modo=='Editar muestra':
        if not muestras:st.info('Todavía no hay muestras.');st.stop()
        opts={f"{m['codigo']} · {m.get('proyecto','')}":m for m in muestras}
        elegido=st.selectbox('Seleccione la muestra',list(opts))
        origen=opts[elegido]
    if modo in ['Registrar muestra','Editar muestra']:
        sedes_disponibles=[x for x in sucursales if perfil['rol']=='administrador' or x['id']==perfil['sucursal_id']]
        if not sedes_disponibles:st.error('No hay sucursales disponibles.');st.stop()
        opciones_sedes={f"{x['codigo']} · {x['nombre']}":x['id'] for x in sedes_disponibles}
        nombres_sedes=list(opciones_sedes)
        inicial=next((i for i,k in enumerate(nombres_sedes) if opciones_sedes[k]==origen.get('sucursal_id')),0)
        with st.form('form_muestra',clear_on_submit=modo=='Registrar muestra'):
            sede_elegida=st.selectbox('Sucursal responsable *',nombres_sedes,index=inicial,disabled=perfil['rol']!='administrador' or modo=='Editar muestra')
            c1,c2,c3=st.columns(3)
            codigo=c1.text_input('Código único de muestra *',value=texto(origen.get('codigo')),disabled=modo=='Editar muestra')
            proyecto=c2.text_input('Proyecto / obra *',value=texto(origen.get('proyecto')))
            cliente=c3.text_input('Cliente / entidad',value=texto(origen.get('cliente')))
            c1,c2,c3,c4=st.columns(4)
            fr=c1.date_input('Fecha de recepción',value=fdate(origen.get('fecha_recepcion')) or date.today())
            hr=c2.time_input('Hora de recepción',value=time.fromisoformat(origen['hora_recepcion'][:8]) if origen.get('hora_recepcion') else datetime.now().time().replace(second=0,microsecond=0))
            fm=c3.date_input('Fecha muestreo',value=fdate(origen.get('fecha_muestreo')) or date.today())
            cal=c4.text_input('Calicata / sondeo',value=texto(origen.get('calicata')))
            c1,c2,c3,c4=st.columns(4)
            p1=c1.number_input('Profundidad inicial (m)',min_value=0.0,step=0.1,value=float(origen.get('prof_inicio') or 0))
            p2=c2.number_input('Profundidad final (m)',min_value=0.0,step=0.1,value=float(origen.get('prof_fin') or 0))
            cantidad=c3.number_input('Cantidad (kg)',min_value=0.0,step=0.5,value=float(origen.get('cantidad_kg') or 0))
            ti=c4.selectbox('Tipo de muestra',TIPOS,index=TIPOS.index(origen.get('tipo')) if origen.get('tipo') in TIPOS else 0)
            c1,c2,c3=st.columns(3)
            condicion=c1.selectbox('Condición recepción',CONDICIONES,index=CONDICIONES.index(origen.get('condicion')) if origen.get('condicion') in CONDICIONES else 0)
            estado=c2.selectbox('Estado',ESTADOS_M,index=ESTADOS_M.index(origen.get('estado')) if origen.get('estado') in ESTADOS_M else 0)
            embalaje=c3.text_input('Envase / embalaje',value=texto(origen.get('embalaje')))
            c1,c2=st.columns(2)
            ubicacion=c1.text_input('Ubicación / sector',value=texto(origen.get('ubicacion')))
            almacen=c2.text_input('Lugar de almacenamiento',value=texto(origen.get('almacenamiento')))
            c1,c2,c3=st.columns(3)
            responsable=c1.text_input('Responsable en campo',value=texto(origen.get('responsable_campo')))
            receptor=c2.text_input('Recibido por',value=texto(origen.get('recibido_por')))
            custodia=c3.text_input('N° cadena de custodia',value=texto(origen.get('custodia')))
            req=st.text_area('Ensayos solicitados',value=texto(origen.get('ensayos_solicitados')),height=80)
            observ=st.text_area('Observaciones',value=texto(origen.get('observaciones')),height=80)
            enviar=st.form_submit_button('Guardar registro',type='primary')
        if enviar:
            if not codigo.strip() or not proyecto.strip():st.error('Código y proyecto son obligatorios.')
            elif p2<p1:st.error('La profundidad final no puede ser menor que la inicial.')
            elif cantidad<=0:st.error('La cantidad debe ser mayor que cero.')
            elif fm>fr:st.warning('Revise la fecha: el muestreo es posterior a la recepción.')
            else:
                payload=dict(sucursal_id=opciones_sedes[sede_elegida],codigo=codigo.strip(),proyecto=proyecto.strip(),cliente=cliente,ubicacion=ubicacion,
                    fecha_recepcion=fecha_iso(fr),hora_recepcion=hr.strftime('%H:%M:%S'),fecha_muestreo=fecha_iso(fm),
                    calicata=cal,prof_inicio=p1,prof_fin=p2,cantidad_kg=cantidad,tipo=ti,
                    condicion=condicion,estado=estado,embalaje=embalaje,almacenamiento=almacen,
                    responsable_campo=responsable,recibido_por=receptor,custodia=custodia,
                    ensayos_solicitados=req,observaciones=observ)
                try:
                    if origen:payload.pop('codigo',None);payload.pop('sucursal_id',None);client.table('muestras').update(payload).eq('id',origen['id']).execute()
                    else:client.table('muestras').insert(payload).execute()
                    refrescar();st.success('Muestra guardada correctamente.');st.rerun()
                except Exception as exc:st.error(f'No se guardó: {exc}')
    else:
        consulta=st.text_input('Buscar por código, proyecto, sector o calicata').casefold()
        seleccion=[m for m in muestras if consulta in ' '.join(texto(m.get(k)) for k in ('codigo','proyecto','ubicacion','calicata')).casefold()]
        filtro=st.multiselect('Filtrar por estado',ESTADOS_M)
        if filtro:seleccion=[m for m in seleccion if m.get('estado') in filtro]
        st.dataframe(tabla_muestras(seleccion),use_container_width=True,hide_index=True)
        st.download_button('Descargar selección en Excel',excel_bytes(tabla_muestras(seleccion)),file_name='muestras_filtradas.xlsx')

elif pagina=='Seguimiento de ensayos':
    if not muestras:st.info('Registre una muestra antes de asignar ensayos.');st.stop()
    modo=st.radio('Operación',['Asignar ensayo','Editar ensayo','Consultar ensayos'],horizontal=True)
    origen={}
    if modo=='Editar ensayo':
        if not ensayos:st.info('No hay ensayos registrados.');st.stop()
        opciones={f"{mapa.get(e['muestra_id'],{}).get('codigo','?')} · {e['ensayo']} · {e['id'][:8]}":e for e in ensayos}
        origen=opciones[st.selectbox('Seleccionar ensayo',list(opciones))]
    if modo != 'Consultar ensayos':
        codigos={f"{m['codigo']} — {m.get('proyecto','')}":m['id'] for m in muestras}
        labels=list(codigos)
        sel=next((i for i,k in enumerate(labels) if codigos[k]==origen.get('muestra_id')),0)
        with st.form('form_ensayo',clear_on_submit=modo=='Asignar ensayo'):
            codigo_sel=st.selectbox('Muestra *',labels,index=sel)
            ensayo=st.selectbox('Ensayo *',PRUEBAS,index=PRUEBAS.index(origen.get('ensayo')) if origen.get('ensayo') in PRUEBAS else 0)
            norma=st.text_input('Norma / método (verificar versión aplicable)',value=texto(origen.get('norma')))
            tec=st.text_input('Técnico responsable',value=texto(origen.get('tecnico')))
            c1,c2,c3=st.columns(3)
            fa=c1.date_input('Fecha asignación',value=fdate(origen.get('fecha_asignacion')) or date.today())
            fi=c2.date_input('Fecha inicio',value=fdate(origen.get('fecha_inicio')),format='DD/MM/YYYY')
            ff=c3.date_input('Fecha fin',value=fdate(origen.get('fecha_fin')),format='DD/MM/YYYY')
            estado=st.selectbox('Estado ensayo',ESTADOS_E,index=ESTADOS_E.index(origen.get('estado')) if origen.get('estado') in ESTADOS_E else 0)
            resultado=st.text_input('Resultado / referencia de archivo',value=texto(origen.get('resultado')))
            obs=st.text_area('Observaciones',value=texto(origen.get('observaciones')))
            guardar=st.form_submit_button('Guardar ensayo',type='primary')
        if guardar:
            if fi and ff and ff<fi:st.error('Fecha fin anterior a fecha inicio.')
            else:
                payload={'muestra_id':codigos[codigo_sel],'ensayo':ensayo,'norma':norma,'tecnico':tec,
                         'fecha_asignacion':fecha_iso(fa),'fecha_inicio':fecha_iso(fi),'fecha_fin':fecha_iso(ff),
                         'estado':estado,'resultado':resultado,'observaciones':obs}
                try:
                    if origen:client.table('ensayos').update(payload).eq('id',origen['id']).execute()
                    else:client.table('ensayos').insert(payload).execute()
                    refrescar();st.success('Ensayo registrado.');st.rerun()
                except Exception as exc:st.error(f'No se pudo guardar: {exc}')
    else:
        buscar=st.text_input('Filtrar por muestra, ensayo o técnico').casefold()
        datos=[e for e in ensayos if buscar in ' '.join([mapa.get(e['muestra_id'],{}).get('codigo',''),e.get('ensayo',''),e.get('tecnico') or '']).casefold()]
        st.dataframe(tabla_ensayos(datos),use_container_width=True,hide_index=True)
        st.download_button('Descargar ensayos',excel_bytes(tabla_ensayos(datos)),file_name='ensayos.xlsx')

elif pagina=='Trazabilidad y exportación':
    st.subheader('Exportar información')
    c1,c2=st.columns(2)
    c1.download_button('⬇️ Muestras (.xlsx)',excel_bytes(tabla_muestras(muestras)),file_name='registro_muestras.xlsx',use_container_width=True)
    c2.download_button('⬇️ Ensayos (.xlsx)',excel_bytes(tabla_ensayos(ensayos)),file_name='seguimiento_ensayos.xlsx',use_container_width=True)
    st.subheader('Historial de modificaciones')
    try:
        log=client.table('bitacora').select('fecha,tabla,accion,actor,registro_id,sucursal_id').order('fecha',desc=True).limit(500).execute().data
        if sucursal_filtro:log=[x for x in log if x.get('sucursal_id')==sucursal_filtro]
        st.dataframe(pd.DataFrame(log),hide_index=True,use_container_width=True)
        st.caption('Se registran las altas y modificaciones. Los datos no se pueden eliminar desde la aplicación.')
    except Exception as exc:st.error(f'No se pudo consultar la bitácora: {exc}')

st.caption('Una organización · varias sucursales · acceso segregado por sede · Registro operativo de laboratorio · Verifique datos, métodos de ensayo y cadena de custodia antes de emitir resultados oficiales.')


# ===== MÓDULOS TÉCNICOS V3 =====
# Los formularios son fichas de captura de datos. No sustituyen validación del responsable técnico.
FICHAS_SUELO={
 'Registro de excavación': [('calicata','Identificación de excavación','texto'),('profundidad_m','Profundidad total (m)','num'),('nivel_freatico_m','Nivel freático (m), si existe','num'),('estratos','Descripción de estratos y cotas','area'),('coordenadas','Coordenadas / referencia','texto'),('fecha_campo','Fecha de excavación','fecha')],
 'Clasificación de suelo': [('grava_pct','Grava (%)','num'),('arena_pct','Arena (%)','num'),('finos_pct','Finos (%)','num'),('ll_pct','Límite líquido (%)','num'),('lp_pct','Límite plástico (%)','num'),('simbolo_sucs','Símbolo SUCS (validado por profesional)','texto'),('simbolo_aashto','Grupo AASHTO (validado)','texto')],
 'Granulometría': [('masa_seca_g','Masa seca total (g)','num'),('tamices','Tamices y masas retenidas (anotar malla:masa, separadas por línea)','area'),('metodo','Método de ensayo / norma','texto'),('observaciones','Observaciones','area')],
 'Humedad': [('tara_g','Masa del recipiente (g)','num'),('humedo_tara_g','Masa húmeda + recipiente (g)','num'),('seco_tara_g','Masa seca + recipiente (g)','num')],
 'Límites': [('puntos_ll','Puntos LL: golpes,humedad (%) por línea','area'),('ll_pct','Límite líquido medido (%)','num'),('lp_pct','Límite plástico medido (%)','num'),('metodo','Método de determinación','texto')],
 'Proctor': [('tipo_proctor','Tipo de Proctor','texto'),('pares','Humedad (%),densidad seca (g/cm³), un punto por línea','area'),('humedad_optima_pct','Humedad óptima estimada / validada (%)','num'),('densidad_max_g_cm3','Densidad seca máxima validada (g/cm³)','num')],
 'Corte directo': [('normal_kpa','Esfuerzos normales (kPa), separados por comas','texto'),('corte_kpa','Esfuerzos cortantes máximos (kPa), separados por comas','texto'),('cohesion_kpa','Cohesión obtenida (kPa)','num'),('phi_grados','Ángulo de fricción (°)','num'),('condicion','Condición drenada / consolidación','texto')],
 'Capacidad portante': [('tipo_cimentacion','Tipo de cimentación','texto'),('ancho_m','Ancho B (m)','num'),('largo_m','Largo L (m)','num'),('desplante_m','Profundidad Df (m)','num'),('gamma_kn_m3','Peso unitario (kN/m³)','num'),('cohesion_kpa','Cohesión (kPa)','num'),('phi_grados','Fricción (°)','num'),('nivel_freatico','Nivel freático y efecto','texto'),('factor_seguridad','Factor de seguridad utilizado','num'),('asentamientos','Verificación de asentamientos / parámetros','area'),('qadm_kpa','Presión admisible validada (kPa)','num')],
 'Sales': [('tipo','Cloruros / sulfatos / sales solubles','texto'),('masa_muestra_g','Masa de muestra (g)','num'),('concentracion','Concentración medida','num'),('unidad','Unidad (%, mg/kg, ppm...)','texto'),('metodo','Norma de ensayo','texto')],
}

def campos_dinamicos(config, anterior):
    valores={}
    for nombre,etiqueta,tipo in config:
        v=anterior.get(nombre)
        if tipo=='num':valores[nombre]=st.number_input(etiqueta,value=float(v or 0),format='%.3f',key='v3_'+nombre)
        elif tipo=='area':valores[nombre]=st.text_area(etiqueta,value=str(v or ''),key='v3_'+nombre)
        elif tipo=='fecha':valores[nombre]=st.date_input(etiqueta,value=fdate(v) or date.today(),key='v3_'+nombre).isoformat()
        else:valores[nombre]=st.text_input(etiqueta,value=str(v or ''),key='v3_'+nombre)
    return valores

def calculos_preliminares(tipo, d):
    # Solo magnitudes que se obtienen directamente de las masas o índices ingresados.
    try:
        if tipo=='Humedad':
            agua=d['humedo_tara_g']-d['seco_tara_g']; solido=d['seco_tara_g']-d['tara_g']
            if solido>0 and agua>=0:return {'humedad_calculada_pct':round(100*agua/solido,3)}
        if tipo=='Límites' or tipo=='Clasificación de suelo':
            ll=d.get('ll_pct',0);lp=d.get('lp_pct',0)
            if ll>0 and lp>0 and ll>=lp:return {'indice_plasticidad_pct':round(ll-lp,3)}
        if tipo=='Granulometría':
            total=d['masa_seca_g']; lineas=[x.strip() for x in d.get('tamices','').splitlines() if x.strip()]
            if total>0 and lineas:
                retenido=sum(float(x.rsplit(':',1)[1].strip()) for x in lineas)
                if retenido<=total:return {'porcentaje_retenido_total':round(100*retenido/total,3),'diferencia_masas_g':round(total-retenido,3)}
    except (ValueError,IndexError,KeyError,TypeError):pass
    return {}

if pagina=='Ensayos de suelos':
    st.subheader('Fichas especializadas de ensayos y exploración geotécnica')
    st.warning('Resultados sujetos a revisión, métodos y normas aplicables. No se genera automáticamente una capacidad portante de diseño ni una clasificación SUCS/AASHTO definitiva.')
    if not muestras:st.info('Primero registre una muestra en Recepción de muestras.')
    else:
        tipo=st.selectbox('Módulo de suelos',list(FICHAS_SUELO))
        opciones={f"{x['codigo']} · {x['proyecto']}":x for x in muestras}
        selec=opciones[st.selectbox('Muestra asociada',list(opciones))]
        try:
            registros=client.table('fichas_suelo').select('*').eq('muestra_id',selec['id']).eq('tipo',tipo).order('creado_en',desc=True).execute().data or []
        except Exception as exc:
            st.error(f'La base de datos requiere ejecutar 04_modulos_suelos_concreto.sql: {exc}');registros=[]
        editar=st.selectbox('Ficha para trabajar',['Nueva ficha']+[f"{x['id'][:8]} · {x['estado']}" for x in registros])
        origen=next((x for x in registros if editar.startswith(x['id'][:8])),None)
        with st.form('ficha_suelo_'+tipo):
            datos=campos_dinamicos(FICHAS_SUELO[tipo],(origen or {}).get('datos') or {})
            norma=st.text_input('Norma/método aplicado (edición y revisión)',value=(origen or {}).get('norma') or '')
            tecnico=st.text_input('Técnico responsable',value=(origen or {}).get('tecnico') or '')
            estado=st.selectbox('Estado de ficha',['Borrador','En revisión','Validado'],index=['Borrador','En revisión','Validado'].index((origen or {}).get('estado','Borrador')))
            comentario=st.text_area('Observaciones y condiciones del ensayo',value=(origen or {}).get('observaciones') or '')
            guardar=st.form_submit_button('Guardar ficha de suelos',type='primary')
        prelim=calculos_preliminares(tipo,datos)
        if prelim:st.info(f'Cálculos automáticos orientativos: {prelim}')
        if guardar:
            if not tecnico.strip():st.error('Identifique al técnico responsable.')
            elif estado=='Validado' and not norma.strip():st.error('Para validar indique el método normativo aplicado.')
            else:
                payload={'muestra_id':selec['id'],'tipo':tipo,'datos':dict(datos,**prelim),'norma':norma,'tecnico':tecnico,'estado':estado,'observaciones':comentario}
                try:
                    if origen:client.table('fichas_suelo').update(payload).eq('id',origen['id']).execute()
                    else:client.table('fichas_suelo').insert(payload).execute()
                    refrescar();st.success('Ficha de suelos guardada.');st.rerun()
                except Exception as exc:st.error(f'Error al guardar: {exc}')
        if registros:
            st.subheader('Historial de fichas')
            st.dataframe(pd.DataFrame([{'Fecha':r['creado_en'],'Técnico':r['tecnico'],'Estado':r['estado'],'Norma':r['norma'],'Datos':str(r['datos'])} for r in registros]),hide_index=True,use_container_width=True)

if pagina=='Ensayos de concreto':
    st.subheader('Recepción y compresión de probetas de concreto')
    st.caption('Módulo de registro de probetas cilíndricas o cúbicas, curado, edad de rotura, carga y resistencia. Verifique método y geometría según la norma aplicable.')
    sedes_disponibles=[x for x in sucursales if perfil['rol']=='administrador' or x['id']==perfil['sucursal_id']]
    if not sedes_disponibles:st.error('No hay sedes activas disponibles.')
    else:
        try:
            items=client.table('probetas_concreto').select('*').order('creado_en',desc=True).limit(2000).execute().data or []
            if sucursal_filtro:items=[x for x in items if x['sucursal_id']==sucursal_filtro]
        except Exception as exc:
            st.error(f'La base de datos requiere ejecutar 04_modulos_suelos_concreto.sql: {exc}');items=[]
        modo=st.radio('Operación',['Nueva probeta','Editar probeta','Consultar probetas'],horizontal=True)
        original={}
        if modo=='Editar probeta':
            if not items:st.info('No existen probetas registradas.')
            else:
                opts={f"{x['codigo']} · {x['id'][:8]}":x for x in items}
                original=opts[st.selectbox('Seleccione probeta',list(opts))]
        if modo in ['Nueva probeta','Editar probeta'] and (modo=='Nueva probeta' or original):
            cod_sedes={f"{x['codigo']} · {x['nombre']}":x['id'] for x in sedes_disponibles}
            etiquetas=list(cod_sedes)
            idx=next((i for i,x in enumerate(etiquetas) if cod_sedes[x]==original.get('sucursal_id')),0)
            with st.form('form_concreto'):
                sel_sede=st.selectbox('Sede responsable',etiquetas,index=idx,disabled=bool(original))
                c1,c2=st.columns(2)
                codigo=c1.text_input('Código único de probeta *',value=original.get('codigo') or '',disabled=bool(original))
                proyecto=c2.text_input('Proyecto / obra *',value=original.get('proyecto') or '')
                c1,c2,c3=st.columns(3)
                elemento=c1.text_input('Elemento estructural / vaciado',value=original.get('elemento') or '')
                tipo=c2.selectbox('Geometría',['Cilindro','Cubo'],index=0 if original.get('geometria','Cilindro')=='Cilindro' else 1)
                curado=c3.text_input('Condiciones de curado',value=original.get('curado') or '')
                c1,c2,c3=st.columns(3)
                fmolde=c1.date_input('Fecha de moldeo',value=fdate(original.get('fecha_moldeo')) or date.today())
                frotura=c2.date_input('Fecha de rotura',value=fdate(original.get('fecha_rotura')) or date.today())
                fc=c3.number_input('f’c especificado (MPa)',min_value=0.,value=float(original.get('fc_mpa') or 0),format='%.2f')
                c1,c2,c3=st.columns(3)
                diam=c1.number_input('Diámetro (mm) / lado de cubo (mm)',min_value=0.,value=float(original.get('diametro_mm') or 0))
                alto=c2.number_input('Altura de probeta (mm)',min_value=0.,value=float(original.get('altura_mm') or 0))
                carga=c3.number_input('Carga máxima de rotura (kN)',min_value=0.,value=float(original.get('carga_kn') or 0),format='%.3f')
                norma=st.text_input('Norma y procedimiento de ensayo',value=original.get('norma') or '')
                tecnico=st.text_input('Técnico responsable',value=original.get('tecnico') or '')
                observ=st.text_area('Observaciones / forma de falla',value=original.get('observaciones') or '')
                estado=st.selectbox('Estado',['Recibida','En curado','Ensayada','Validada'],index=['Recibida','En curado','Ensayada','Validada'].index(original.get('estado','Recibida')))
                guardar=st.form_submit_button('Guardar probeta',type='primary')
            import math
            area=math.pi*diam*diam/4 if tipo=='Cilindro' else diam*diam
            resistencia=round(carga*1000/area,3) if area>0 and carga>0 else None
            if resistencia is not None:st.metric('Resistencia calculada (MPa)',resistencia)
            if guardar:
                if not codigo.strip() or not proyecto.strip():st.error('Código y proyecto obligatorios.')
                elif frotura<fmolde:st.error('La rotura no puede preceder al moldeo.')
                elif estado in ['Ensayada','Validada'] and (resistencia is None or not tecnico.strip() or not norma.strip()):st.error('Para ensayo finalizado son necesarios geometría, carga, técnico y norma.')
                else:
                    payload={'sucursal_id':cod_sedes[sel_sede],'codigo':codigo.strip(),'proyecto':proyecto.strip(),'elemento':elemento,'geometria':tipo,'curado':curado,'fecha_moldeo':fmolde.isoformat(),'fecha_rotura':frotura.isoformat(),'edad_dias':(frotura-fmolde).days,'fc_mpa':fc,'diametro_mm':diam,'altura_mm':alto,'carga_kn':carga,'resistencia_mpa':resistencia,'norma':norma,'tecnico':tecnico,'observaciones':observ,'estado':estado}
                    try:
                        if original:payload.pop('sucursal_id');payload.pop('codigo');client.table('probetas_concreto').update(payload).eq('id',original['id']).execute()
                        else:client.table('probetas_concreto').insert(payload).execute()
                        refrescar();st.success('Probeta registrada.');st.rerun()
                    except Exception as exc:st.error(f'No se pudo guardar: {exc}')
        elif modo=='Consultar probetas':
            st.dataframe(pd.DataFrame(items),hide_index=True,use_container_width=True)
            if items:st.download_button('Exportar probetas a Excel',excel_bytes(pd.DataFrame(items)),file_name='probetas_concreto.xlsx')


if pagina == "Hojas técnicas e informes":
    from hojas_tecnicas import mostrar_hojas
    mostrar_hojas(st, client, perfil, muestras, sucursales, sucursal_filtro)
