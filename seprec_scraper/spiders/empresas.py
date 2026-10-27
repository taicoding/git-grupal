from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import scrapy
from scrapy import signals

from seprec_scraper.items import EmpresaItem
from seprec_scraper.storage import RequestCollector
from seprec_scraper.utils import load_company_names


class EmpresasSpider(scrapy.Spider):
    name = "empresas"
    allowed_domains = ["servicios.seprec.gob.bo"]

    base_url = "https://servicios.seprec.gob.bo/api/empresas/buscarEmpresas"
    filter_type = "nombre"
    results_per_page = 10
    daily_request_limit = 200
    retryable_statuses = {408, 425, 429, 500, 502, 503, 504, 522, 524}

    custom_settings = {
        "HTTPERROR_ALLOW_ALL": True,
        "JOBDIR": "jobs/empresas",
    }

    @classmethod
    def from_crawler(cls, crawler: scrapy.Crawler, *args: Any, **kwargs: Any):
        spider = super().from_crawler(crawler, *args, **kwargs)
        state_path = crawler.settings.get(
            "SEPREC_STATE",
            os.getenv("SEPREC_STATE", "seprec_state.sqlite3"),
        )
        spider.collector = RequestCollector(Path(state_path), spider.daily_request_limit)
        crawler.signals.connect(spider.close_collector, signal=signals.spider_closed)
        return spider

    def __init__(self, input: str | None = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.input_path = Path(input or os.getenv("SEPREC_INPUT", "empresas.csv"))
        self.cookie = os.getenv("SEPREC_COOKIE", "").strip()
        self.collector: RequestCollector

    async def start(self):
        for item in self.start_requests():
            yield item

    def start_requests(self):
        if not self.input_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {self.input_path}")

        companies = load_company_names(self.input_path)
        remaining = self.collector.remaining_today()
        pending = [
            company for company in companies if not self.collector.processed(company)
        ][:remaining]

        self.logger.info(
            "Empresas cargadas: %d; pendientes: %d; solicitudes restantes hoy: %d",
            len(companies),
            len(pending),
            remaining,
        )
        for row in self.collector.results():
            yield self.result_item(
                row["empresa"],
                row["status"],
                row["http_status"],
                data=json.loads(row["data"]) if row["data"] else None,
                error=row["error"] or "",
                queried_at=row["queried_at"],
            )
        for company in pending:
            if not self.collector.reserve():
                break
            request = scrapy.Request(
                f"{self.base_url}?{urlencode({
                    'filtro': company,
                    'tipoFiltro': self.filter_type,
                    'limite': self.results_per_page,
                    'pagina': 1,
                })}",
                headers=self.request_headers(),
                cookies={"cf_clearance": self.cookie} if self.cookie else None,
                callback=self.parse,
                errback=self.on_error,
                cb_kwargs={"company": company},
            )
            yield request

    def request_headers(self) -> dict[str, str]:
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-BO,en;q=0.9,es-BO;q=0.8,es;q=0.7",
            "origin": "https://miempresa.seprec.gob.bo",
            "referer": "https://miempresa.seprec.gob.bo/",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/156.0.0.0 Safari/537.36"
            ),
        }

    def parse(self, response: scrapy.http.Response, company: str):
        if response.status == 403:
            error = "Acceso rechazado; se detiene el lote."
            self.collector.save(
                company, "forbidden", http_status=403, error=error,
            )
            self.crawler.engine.close_spider(
                self, reason="SEPREC rechazó la solicitud (403)"
            )
            return self.result_item(
                company, "forbidden", 403, error=error
            )

        if response.status in self.retryable_statuses:
            self.collector.save(
                company, "http_error", http_status=response.status,
                error=response.text[:500],
            )
            return self.result_item(
                company, "http_error", response.status, error=response.text[:500]
            )

        try:
            data = response.json()
        except ValueError as exc:
            error = f"Respuesta JSON inválida: {exc}"
            self.collector.save(
                company, "invalid_response", http_status=response.status,
                error=error,
            )
            return self.result_item(
                company, "invalid_response", response.status, error=error
            )

        self.collector.save(company, "ok", http_status=response.status, data=data)
        return self.result_item(company, "ok", response.status, data=data)

    def on_error(self, failure):
        company = failure.request.cb_kwargs["company"]
        error = failure.getErrorMessage()
        self.collector.save(company, "network_error", error=error)
        return self.result_item(company, "network_error", error=error)

    def result_item(
        self,
        company: str,
        status: str,
        http_status: int | None = None,
        *,
        data: Any = None,
        error: str = "",
        queried_at: str | None = None,
    ) -> EmpresaItem:
        return EmpresaItem(
            empresa=company,
            status=status,
            http_status=http_status,
            queried_at=queried_at or datetime.now(timezone.utc).isoformat(),
            data=data,
            error=error,
        )

    def close_collector(self, reason: str) -> None:
        self.collector.close()
