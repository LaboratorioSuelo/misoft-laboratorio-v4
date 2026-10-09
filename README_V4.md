# MISOFT V4 - Hojas técnicas e informes

Se añade **Hojas técnicas e informes** al menú V3, usando las mismas tablas existentes `fichas_suelo` y `probetas_concreto`; no se requiere migración SQL nueva.

Suelos: nueve fichas con tabla dinámica editable, cálculos algebraicos donde proceden, gráficos cuando existen pares medidos, Excel, Word y PDF. Concreto: informe sobre probetas guardadas, con cálculo básico de resistencia por carga y área.

**Alcance:** todas las salidas indican BORRADOR. Los módulos de excavación, clasificación, capacidad portante y sales no generan interpretación geotécnica definitiva. Granulometría normaliza masa retenida (verificar balance con masa inicial); límites aproxima LL a 25 golpes por ajuste logarítmico; Proctor informa máximo observado, no determina MDS normativa; corte directo ajusta pico a recta, sin corrección de área. Se requieren validación de métodos, equipos calibrados y firma profesional. No existe expediente normativo completamente automatizado.

Ejecute `pip install -r requirements.txt` para instalar librerías nuevas. Para base nueva ejecute SQL en este orden: `schema.sql`, `02_configurar_sedes.sql`, `03_habilitar_alta_sedes.sql`, `04_modulos_suelos_concreto.sql`. Para V3 existente, no repita esos scripts: respalde primero y despliegue el código V4; la base V3 ya incluye las tablas requeridas.

**Importante:** no se guardan los gráficos como archivo binario en la base; se regeneran a partir de mediciones. PDF/Word se generan al solicitar descarga. Informe sin firma digital; no constituye certificado acreditado.
