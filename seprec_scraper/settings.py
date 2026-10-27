import os


RESULTS_DIR = os.getenv("SEPREC_RESULTS_DIR", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

BOT_NAME = "seprec_scraper"

SPIDER_MODULES = ["seprec_scraper.spiders"]
NEWSPIDER_MODULE = "seprec_scraper.spiders"

ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 8
DOWNLOAD_DELAY_JITTER = 0
CONCURRENT_REQUESTS_PER_DOMAIN = 1
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 8
AUTOTHROTTLE_MAX_DELAY = 18
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [408, 425, 429, 500, 502, 503, 504, 522, 524]

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_IGNORE_HTTP_CODES = [401, 403, 429, 500, 502, 503, 504]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

COOKIES_ENABLED = True
FEED_EXPORT_ENCODING = "utf-8"
FEEDS = {
    os.getenv("SEPREC_JSON_OUTPUT", f"{RESULTS_DIR}/seprec_resultados.json"): {
        "format": "json",
        "overwrite": True,
    },
    os.getenv("SEPREC_CSV_OUTPUT", f"{RESULTS_DIR}/seprec_resultados.csv"): {
        "format": "csv",
        "overwrite": True,
    },
}

LOG_LEVEL = os.getenv("SCRAPY_LOG_LEVEL", "INFO")
