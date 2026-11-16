# Dataset sintético de comportamiento transaccional

## Contenido
- `transacciones_sinteticas.csv`: 1.000.000 de transacciones de 10.000 clientes.
- `catalogo_tipos_subtipos.csv`: catálogo sintético de 57 tipos y sus subtipos.
- `catalogo_bancos.csv`: nombres ficticios de bancos/entidades.

## Cobertura temporal
Del 2026-01-01 al 2026-06-30 (seis meses).

## Esquema de transacciones
- `codigo_cliente`: identificador sintético (1 a 10.000).
- `fecha_transaccion`: fecha y hora de la operación.
- `tipo_transaccion`: código numérico de 1 a 57.
- `subtipo_transaccion`: código numérico local al tipo de transacción.
- `monto`: importe en bolivianos (BOB), con signo.
- `tipo_movimiento`: `D` débito o `C` crédito.
- `glosa`: descripción sintética; se deja vacía en operaciones donde no aplica.
- `banco_destino`: entidad ficticia; se deja vacía cuando no aplica.

## Convención del signo
Para este dataset sintético, los débitos (`D`) se representan con montos negativos y los créditos (`C`) con montos positivos. Esta es una convención de generación y debe validarse/adaptarse si el sistema real utiliza otra.

## Consideraciones metodológicas
- No existe una columna de segmento, perfil, clase ni `ground_truth_segment`.
- No se asignaron perfiles conocidos a los clientes. La heterogeneidad surge de distribuciones probabilísticas por cliente, categoría, frecuencia y monto.
- Se incorporaron distribuciones asimétricas, colas largas y transacciones de montos extremos para permitir estudiar outliers.
- Los patrones no están diseñados como clases discretas separables; el clustering debe descubrir estructura si existe.
- Los bancos y descripciones son ficticios.
- Los datos no corresponden a personas, cuentas ni operaciones reales.

## Reproducibilidad
Semilla aleatoria: `20261116`.

## Advertencia
El catálogo es ilustrativo y no representa el catálogo oficial de ninguna entidad financiera.
