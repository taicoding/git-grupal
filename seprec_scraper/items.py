import scrapy


class EmpresaItem(scrapy.Item):
    empresa = scrapy.Field()
    status = scrapy.Field()
    http_status = scrapy.Field()
    queried_at = scrapy.Field()
    data = scrapy.Field()
    error = scrapy.Field()
