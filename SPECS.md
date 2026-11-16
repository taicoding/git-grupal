# SPECS — Segmentación de clientes basada en comportamiento transaccional

## 1. Descripción del proyecto

Desarrollar un pipeline de análisis de datos y aprendizaje no supervisado (Unsupervised Machine Learning) para identificar patrones de comportamiento transaccional y segmentar clientes según las características de sus operaciones financieras.

El objetivo es descubrir grupos de clientes que presenten características diferenciadoras en su comportamiento transaccional, considerando la frecuencia, distribución, concentración, diversidad y composición de sus operaciones.

La segmentación debe permitir identificar comportamientos similares entre clientes y descubrir grupos con patrones particulares o atípicos.

El proyecto debe priorizar la interpretabilidad de los segmentos y no únicamente la optimización de métricas estadísticas de clustering.

## 2. Objetivo analítico

Identificar agrupaciones naturales de clientes mediante técnicas de aprendizaje no supervisado.

Se busca responder preguntas como:

- ¿Existen grupos de clientes con patrones transaccionales similares?
- ¿Qué tipos y subtipos de transacciones caracterizan a cada grupo?
- ¿Existen clientes que concentran sus operaciones en pocas categorías?
- ¿Qué diferencias existen entre clientes con alta y baja diversidad transaccional?
- ¿Existen grupos con montos o frecuencias significativamente diferentes?
- ¿Qué características permiten diferenciar un segmento del resto?
- ¿Existen comportamientos transaccionales atípicos que merecen un análisis independiente?

No se debe asumir anticipadamente la cantidad de clusters ni imponer categorías de comportamiento.

**Importante:** este es un problema de aprendizaje no supervisado. No existen segmentos, perfiles ni etiquetas de referencia previamente identificados.

## 3. Fuente de datos

### 3.1. Dataset sintético

Debido a restricciones de privacidad, los datos originales de producción no pueden compartirse ni utilizarse en este entorno de desarrollo.

Por este motivo, el proyecto utilizará exclusivamente un dataset sintético como fuente de datos durante esta fase experimental.

Los archivos se encuentran en la raíz del proyecto:

```text
project/
├── transacciones_sinteticas.csv
├── catalogo_tipos_subtipos.csv
├── catalogo_bancos.csv
└── README.md
```

Los archivos reales disponibles deben inspeccionarse antes de comenzar el desarrollo.

### 3.2. Características generales

| Característica | Descripción |
|---|---|
| Clientes | 10.000 clientes ficticios |
| Transacciones | 1.000.000 de registros |
| Tipos de transacción | 57 categorías |
| Período | Enero a junio de 2026 |
| Moneda | Bolivianos (BOB) |
| Movimientos | Débito (D) y crédito (C) |
| Formato | CSV |
| Fuente | Dataset sintético |

### 3.3. Estructura de transacciones

El archivo `transacciones_sinteticas.csv` contiene los siguientes campos:

| Campo | Descripción |
|---|---|
| codigo_cliente | Identificador único del cliente ficticio. |
| fecha_transaccion | Fecha y hora de la operación. |
| tipo_transaccion | Código numérico de la categoría de transacción. |
| subtipo_transaccion | Código numérico de la subcategoría. |
| monto | Importe de la transacción en bolivianos, conservando su signo. |
| tipo_movimiento | D para débito y C para crédito. |
| glosa | Descripción ficticia de la operación, cuando corresponde. |
| banco_destino | Nombre de la entidad financiera de destino, cuando corresponde. |

Los débitos están representados mediante montos negativos y los créditos mediante montos positivos.

La variable `tipo_movimiento` debe utilizarse para identificar explícitamente la naturaleza del movimiento. No se debe asumir que el signo del monto es suficiente para determinarla sin realizar validaciones.

### 3.4. Catálogos

El archivo `catalogo_tipos_subtipos.csv` contiene:

- Código de tipo de transacción.
- Descripción del tipo de transacción.
- Código de subtipo.
- Descripción del subtipo.

El archivo `catalogo_bancos.csv` contiene las entidades financieras ficticias utilizadas en las operaciones.

Los catálogos deben utilizarse para enriquecer la interpretación de los resultados.

No se deben interpretar los códigos numéricos como variables continuas u ordinales.

### 3.5. Características estadísticas del dataset

El dataset sintético incorpora:

- Diferencias en la cantidad de transacciones por cliente.
- Distribuciones heterogéneas de tipos de transacción.
- Variabilidad en la frecuencia de operaciones.
- Montos con distribuciones asimétricas.
- Colas largas y valores extremos.
- Diferencias en la concentración de operaciones por categoría.
- Diversidad en los tipos y subtipos utilizados.
- Operaciones de débito y crédito.
- Glosas y bancos destino ficticios.

Estas características permiten experimentar con técnicas de análisis exploratorio, ingeniería de características, detección de anomalías y clustering.

**No existen perfiles de clientes predefinidos ni etiquetas que deban utilizarse para entrenar o evaluar los modelos.**

La heterogeneidad de los datos no debe interpretarse como una clasificación conocida.

## 4. Alcance y restricciones de esta fase

Durante esta fase:

1. Utilizar exclusivamente el dataset sintético disponible en la raíz del proyecto.
2. No conectarse a SQL Server.
3. No utilizar `mssql_python`.
4. No solicitar ni utilizar datos reales de clientes.
5. No modificar los archivos originales del dataset.
6. No generar etiquetas artificiales de segmentos.
7. No utilizar identificadores de clientes como variables de entrada del clustering.
8. No imponer una cantidad de clusters.
9. No eliminar automáticamente clientes con comportamientos extremos.
10. Mantener una arquitectura que permita incorporar posteriormente una fuente SQL Server sin reescribir el pipeline analítico.

La integración con datos reales queda fuera del alcance de esta fase.

## 5. Tecnologías y herramientas

Utilizar las siguientes tecnologías:

| Tecnología | Responsabilidad |
|---|---|
| Python | Lenguaje principal del proyecto. |
| Jupyter Notebooks | Desarrollo y documentación de las etapas analíticas. |
| Polars | Lectura, agregación y transformación eficiente de datos. |
| Plotly | Visualizaciones interactivas. |
| Scikit-learn | Preprocesamiento, clustering y evaluación. |
| NumPy | Operaciones numéricas. |
| SciPy | Estadística y análisis de distribuciones. |
| HDBSCAN | Clustering basado en densidad, cuando corresponda. |

Se recomienda utilizar `polars.scan_csv()` para trabajar con el dataset mediante ejecución lazy cuando resulte conveniente.

Evitar cargar múltiples copias innecesarias del dataset en memoria.

## 6. Pipeline de análisis

Todo el desarrollo analítico debe realizarse mediante Jupyter Notebooks dentro de la carpeta `analysis/`.

Cada notebook debe representar una etapa independiente, documentando el objetivo, metodología, resultados y conclusiones.

### 6.1. Data validation and extraction

Objetivo: verificar la integridad y consistencia de los datos antes de comenzar el análisis.

Actividades:

- Lectura de los archivos CSV.
- Inspección de columnas y tipos de datos.
- Validación de registros.
- Validación de clientes únicos.
- Validación de los 57 tipos de transacción.
- Validación de los catálogos.
- Identificación de valores nulos.
- Identificación de registros duplicados.
- Validación de montos y signos.
- Validación de fechas.
- Validación de relaciones entre tipos y subtipos.

El resultado debe ser un dataset validado y documentado.

### 6.2. Exploratory Data Analysis (EDA)

Objetivo: comprender la estructura y distribución del comportamiento transaccional.

Analizar:

**Clientes**
- Cantidad de transacciones por cliente.
- Distribución de actividad transaccional.
- Clientes con actividad baja y alta.
- Distribución de montos por cliente.

**Tipos de transacción**
- Frecuencia de los 57 tipos.
- Distribución de subtipos.
- Participación global por tipo y subtipo.
- Distribución de montos por categoría.

**Movimientos**
- Proporción de débitos y créditos.
- Distribución de montos por movimiento.
- Relación entre débitos y créditos por cliente.

**Temporalidad**
- Evolución mensual de las transacciones.
- Frecuencia diaria y mensual.
- Distribución temporal de montos.

**Concentración**
- Distribución de operaciones por categoría.
- Concentración de montos.
- Diversidad transaccional por cliente.

**Calidad**
- Valores nulos.
- Valores extremos.
- Distribuciones asimétricas.
- Correlaciones entre variables.

Utilizar Plotly para construir visualizaciones interactivas.

### 6.3. Outlier analysis

Objetivo: identificar y analizar valores extremos que puedan afectar el clustering.

Se debe considerar que existen clientes con comportamientos legítimamente extremos.

Evaluar:

- Outliers en cantidad de transacciones.
- Outliers en montos totales.
- Outliers en montos promedio.
- Outliers en proporciones.
- Outliers en indicadores de concentración.
- Clientes con actividad transaccional extraordinaria.

Evaluar diferentes técnicas:

- Percentiles.
- IQR.
- Winsorización.
- Transformaciones logarítmicas.
- RobustScaler.
- Isolation Forest.
- Local Outlier Factor.

No eliminar automáticamente los clientes identificados como outliers.

Comparar los resultados de clustering bajo diferentes estrategias:

1. Datos originales.
2. Datos transformados.
3. Datos con tratamiento de valores extremos.
4. Análisis separado de anomalías, cuando corresponda.

Documentar el impacto de cada estrategia.

### 6.4. Feature engineering

Objetivo: construir indicadores que representen el comportamiento transaccional individual de cada cliente.

El dataset original contiene registros transaccionales, por lo que será necesario construir una matriz de características agregadas por cliente.

**A. Indicadores de frecuencia**

- Cantidad total de transacciones.
- Cantidad de transacciones por tipo.
- Cantidad de transacciones por subtipo.
- Proporción de transacciones por tipo.
- Proporción de transacciones por subtipo.
- Cantidad de categorías utilizadas.
- Cantidad de subcategorías utilizadas.

**B. Indicadores monetarios**

- Monto total debitado.
- Monto total acreditado.
- Monto neto.
- Monto promedio por transacción.
- Monto mediano.
- Desviación estándar.
- Percentiles de montos.
- Montos agregados por tipo.
- Montos agregados por subtipo.
- Proporción del monto por categoría respecto al total individual.

**C. Indicadores de comportamiento**

- Relación entre débitos y créditos.
- Frecuencia relativa de débitos y créditos.
- Diversidad transaccional.
- Distribución de operaciones por categoría.
- Concentración de operaciones en determinadas categorías.
- Variabilidad de los montos.
- Participación de transferencias.
- Diversidad de bancos destino.

**D. Indicadores de concentración y diversidad**

Implementar indicadores adicionales que permitan representar la concentración y diversidad del comportamiento transaccional.

Considerar:

**Herfindahl-Hirschman Index (HHI)**

Medir la concentración de operaciones por tipo y subtipo de transacción.

Calcular indicadores diferenciados para:

- Cantidad de transacciones.
- Montos debitados.
- Montos acreditados.
- Distribución por tipo.
- Distribución por subtipo.

Para cada cliente:

\[
HHI_i = \sum_{j=1}^{n} p_{ij}^{2}
\]

Donde \(p_{ij}\) representa la participación de la categoría \(j\) en el total del cliente \(i\).

**Entropía de Shannon**

Medir la diversidad de categorías utilizadas:

\[
H_i = -\sum_{j=1}^{n} p_{ij}\log(p_{ij})
\]

Evaluar también la entropía normalizada para facilitar comparaciones entre clientes.

Otros indicadores podrán incorporarse cuando aporten información adicional.

Evitar generar variables redundantes o altamente correlacionadas sin justificación.

### 6.5. Feature selection

Objetivo: seleccionar las características que mejor representan el comportamiento transaccional.

Considerar:

- Análisis de correlación.
- Multicolinealidad.
- Redundancia de variables.
- Variabilidad de características.
- Distribución de variables.
- Relevancia analítica.
- Reducción de dimensionalidad.

Evaluar diferentes conjuntos de características y documentar su impacto sobre los resultados del clustering.

### 6.6. Data preprocessing

Objetivo: preparar las características para los algoritmos de clustering.

Considerar:

- Tratamiento de valores nulos.
- Transformaciones de distribuciones asimétricas.
- Escalamiento.
- Estandarización.
- Normalización.
- Tratamiento de valores extremos.
- Eliminación de variables no informativas.
- Preparación de matrices de características.

Evaluar diferentes estrategias:

- StandardScaler.
- RobustScaler.
- MinMaxScaler.
- PowerTransformer.
- Transformaciones logarítmicas cuando sean apropiadas.

No aplicar transformaciones indiscriminadamente. Justificar su uso según las características de cada variable.

Los identificadores de clientes y las columnas descriptivas no deben formar parte de la matriz de entrada del clustering.

### 6.7. Clustering experiments

Objetivo: experimentar con diferentes algoritmos de clustering para descubrir grupos de clientes con comportamientos similares.

Evaluar inicialmente:

- K-Means.
- MiniBatch K-Means.
- Gaussian Mixture Models.
- Agglomerative Clustering.
- DBSCAN.
- HDBSCAN.

Experimentar con:

- Diferentes conjuntos de características.
- Diferentes técnicas de escalamiento.
- Diferentes transformaciones.
- Diferentes hiperparámetros.
- Diferentes cantidades de clusters cuando el algoritmo lo requiera.

No asumir que K-Means será necesariamente la solución definitiva.

Evaluar también técnicas de reducción de dimensionalidad:

- PCA.
- UMAP.

Utilizarlas para facilitar el análisis y visualización de la estructura de los datos.

No utilizar la reducción de dimensionalidad únicamente como herramienta visual sin evaluar previamente sus implicaciones si se utiliza como entrada del clustering.

### 6.8. Cluster evaluation

Objetivo: evaluar la calidad y utilidad de las agrupaciones encontradas.

Considerar las siguientes métricas:

- Silhouette Score.
- Davies-Bouldin Index.
- Calinski-Harabasz Index.
- Tamaño de cada cluster.
- Distribución de clientes por cluster.
- Proporción de clientes sin asignación, cuando corresponda.
- Estabilidad de los resultados.
- Separación entre grupos.
- Interpretabilidad de las características diferenciadoras.

Comparar los resultados obtenidos con diferentes algoritmos y configuraciones.

No seleccionar un modelo exclusivamente por su Silhouette Score.

La evaluación debe considerar tanto la calidad estadística como la utilidad analítica de los segmentos.

### 6.9. Cluster profiling

Objetivo: caracterizar los grupos encontrados e identificar sus principales diferencias.

Para cada cluster analizar:

- Cantidad de clientes.
- Porcentaje de clientes.
- Cantidad promedio de transacciones.
- Distribución de montos.
- Tipos de transacción predominantes.
- Subtipos predominantes.
- Participación de débitos y créditos.
- HHI.
- Entropía.
- Diversidad transaccional.
- Concentración de montos.
- Características que lo diferencian de otros clusters.

Utilizar visualizaciones interactivas para comparar los perfiles.

Las descripciones de los clusters deben surgir de los resultados observados y no de categorías impuestas previamente.

Los nombres de los segmentos deben asignarse después del análisis de sus características.

## 7. Estructura del proyecto

Se propone la siguiente organización:

```text
project/
│
├── SPECS.md
│
├── transacciones_sinteticas.csv
├── catalogo_tipos_subtipos.csv
├── catalogo_bancos.csv
├── README.md
│
├── analysis/
│   ├── 00_data_validation.ipynb
│   ├── 01_exploratory_data_analysis.ipynb
│   ├── 02_outlier_analysis.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_feature_selection.ipynb
│   ├── 05_preprocessing.ipynb
│   ├── 06_clustering_experiments.ipynb
│   ├── 07_cluster_evaluation.ipynb
│   └── 08_cluster_profiling.ipynb
│
├── data/
│   └── processed/
│
└── results/
    ├── metrics/
        ├── models/
            └── visualizations/
            ```

            Se pueden incorporar módulos auxiliares de Python cuando exista una justificación técnica, pero los pasos principales del análisis deben permanecer documentados y ejecutables mediante Jupyter Notebooks.

            ## 8. Reproducibilidad y documentación

            Cada notebook debe contener:

            1. Objetivo.
            2. Descripción de los datos.
            3. Metodología.
            4. Desarrollo del análisis.
            5. Visualizaciones.
            6. Resultados.
            7. Interpretación.
            8. Conclusiones.
            9. Decisiones para la siguiente etapa.

            Se deben registrar las configuraciones de los experimentos, incluyendo:

            - Variables utilizadas.
            - Transformaciones.
            - Método de escalamiento.
            - Algoritmo.
            - Hiperparámetros.
            - Métricas obtenidas.
            - Cantidad de clusters.
            - Cantidad de clientes por grupo.

            Utilizar semillas aleatorias cuando corresponda para favorecer la reproducibilidad.

            No sobrescribir resultados anteriores sin conservar la información necesaria para comparar experimentos.

            ## 9. Entregables

            El proyecto debe producir:

            1. Dataset transaccional validado.
            2. Análisis exploratorio documentado.
            3. Análisis de outliers.
            4. Dataset de características por cliente.
            5. Indicadores de concentración y diversidad.
            6. Comparación de estrategias de preprocesamiento.
            7. Comparación de algoritmos de clustering.
            8. Evaluación de modelos.
            9. Identificación de una configuración seleccionada, si los resultados lo justifican.
            10. Asignación de clusters a clientes.
            11. Caracterización de los segmentos.
            12. Visualizaciones interactivas.
            13. Conclusiones y recomendaciones analíticas.

            ## 10. Criterios de aceptación

            El proyecto se considerará correctamente desarrollado cuando:

            - El dataset sintético pueda procesarse de manera reproducible.
            - Se hayan validado los datos y catálogos.
            - Se haya realizado un EDA completo.
            - Se hayan analizado y documentado los outliers.
            - Se hayan construido características representativas del comportamiento transaccional.
            - Se hayan evaluado indicadores de concentración y diversidad.
            - Se hayan experimentado diferentes algoritmos de clustering.
            - Se hayan comparado los resultados mediante métricas apropiadas.
            - Se puedan interpretar las diferencias entre los grupos.
            - Se disponga de una asignación de cluster por cliente para la solución seleccionada.
            - Las conclusiones estén respaldadas por datos y visualizaciones.

            Si los experimentos no encuentran clusters suficientemente diferenciados o estables, se debe documentar este resultado en lugar de forzar una segmentación.

            ## 11. Consideraciones para futuras fases

            La arquitectura debe permitir incorporar posteriormente datos reales provenientes de SQL Server.

            Para ello, separar conceptualmente:

            - Lectura y extracción de datos.
            - Validación y adaptación del esquema.
            - Ingeniería de características.
            - Preprocesamiento.
            - Clustering.
            - Evaluación.
            - Interpretación.

            La incorporación futura de una fuente real no debe requerir reescribir las etapas analíticas.

            Sin embargo, los resultados obtenidos con datos sintéticos no deben considerarse automáticamente representativos del comportamiento de clientes reales.

            La validación con datos reales será una fase independiente, sujeta a los permisos y controles de privacidad correspondientes.

            ---

            ## Principio fundamental del proyecto

            **Descubrir grupos de clientes con características diferenciadoras a partir de su comportamiento transaccional, mediante técnicas de aprendizaje no supervisado.**

            No se busca reproducir perfiles conocidos, sino explorar los datos, descubrir estructuras, evaluar su estabilidad e interpretar los patrones encontrados.