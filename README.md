# SEPREC Scrapy scraper

Proyecto Scrapy para consultar empresas de SEPREC de forma controlada. Lee un
CSV con una columna `EMPRESA`, elimina duplicados, limita el lote a 200
solicitudes por día y guarda el estado en SQLite para poder reanudar la
ejecución.

## Uso

```bash
python -m pip install -r requirements.txt
export SEPREC_COOKIE='valor-temporal-si-es-necesario'
scrapy crawl empresas
```

La cookie es opcional y nunca se escribe en el repositorio. También puede
seleccionarse otro archivo de entrada:

```bash
scrapy crawl empresas -a input=otra_lista.csv
```

La salida CSV y JSON se guarda por defecto en `results/` y se puede configurar
con `SEPREC_RESULTS_DIR`, `SEPREC_JSON_OUTPUT` o `SEPREC_CSV_OUTPUT`. El estado queda en
`seprec_state.sqlite3` y el directorio `jobs/empresas`; ambos permiten
reanudar la ejecución. Los resultados ya registrados no se vuelven a
consultar.

La configuración usa una solicitud concurrente por dominio, una espera mínima
de ocho segundos y AutoThrottle hasta 18 segundos. Los errores transitorios
se reintentan con el middleware estándar de Scrapy. Un `403` detiene el lote
para no insistir ante un rechazo de acceso. No se evaden controles de acceso,
Cloudflare ni límites del servicio.
