# -*- coding: utf-8 -*-
import scrapy
from scrapy_splash import SplashRequest


# lua scripts -->
script = """

function main(splash, args)
    assert(splash:go(args.url))
    assert(splash:wait(2))
    splash:set_viewport_full()
    return {
        html = splash:html()
    }
end

"""


pagination_script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(2))  
  assert(splash:runjs('document.querySelector(".page-number div a:nth-child(' .. splash.args.value .. ')").click()'))
  assert(splash:wait(1))
  splash:set_viewport_full()
  return {
      html = splash:html()
  }
end
"""


class SpiderScriptSpider(scrapy.Spider):

    name = 'spider_script'
    allowed_domains = ['fdc.nal.usda.gov']

    def start_requests(self):
        url = 'https://fdc.nal.usda.gov/fdc-app.html#/food-search'

        # This is crawled about 9 pages max due to for loop
        for i in range(1, 10):
            yield SplashRequest(url=url, callback=self.parse,
                                endpoint='execute',
                                cache_args=['lua_source'],
                                args={'lua_source': pagination_script, 'value': i},
                                headers={'X-My-Header': 'value'},
                                dont_filter=True
                                )

    def parse(self, response):
        description_row = '//tr[@name="search-food-result-row"]'
        url_xpath = './/td[@headers="food-Search-result-description-header"]/a[@class="result-description"]/@href'

        for rows in response.xpath(description_row):

            published = rows.xpath(
                './/td[@headers="Food-Search-result-published-date-header"]/text()').extract_first()
            url = rows.xpath(url_xpath).extract_first()
            page_url = 'https://fdc.nal.usda.gov/fdc-app.html'+url

            yield SplashRequest(url=page_url, callback=self.parse_all_info,
                                meta={'published': published},
                                endpoint='execute',
                                cache_args=['lua_source'],
                                args={'lua_source': script},
                                headers={'X-My-Header': 'value'},
                                dont_filter=True
                                )

    def getActualData(self, list_data):
        if list_data:
            sent = ''
            for sentence in list_data:
                sent += sentence.strip()
            list_data = sent
        return list_data

    def parse_all_info(self, response):
        description_xpath = '//span[@id="foodDetailsDescription"]/h1/text()'

        data_type_xpath = '//span[@id="foodType"]/span/following-sibling::text()'

        fdc_id_xpath = '//span[@id="foodDetailsFdcId"]/span/following-sibling::text()'

        food_code_xpath = '//span[@id="surveyFoodCode"]/span/following-sibling::text()'

        food_category_xpath = '//span[contains(text(), "Food Category:")]/following-sibling::text()'

        description = response.xpath(description_xpath).extract_first()
        dataType = response.xpath(data_type_xpath).extract_first()
        fdcId = response.xpath(fdc_id_xpath).extract()
        foodCode = response.xpath(food_code_xpath).extract_first()
        foodCategory = response.xpath(food_category_xpath).extract_first()
        published = response.meta.get('published')

        fdcId = self.getActualData(fdcId)
        foodCode = self.getActualData(foodCode)
        foodCategory = self.getActualData(foodCategory)
        published = self.getActualData(published)

        yield {
            'Description': description,
            'Data-Type': dataType,
            'FDC-ID': fdcId,
            'Food-Code': foodCode,
            'Food-Category': foodCategory,
            'Published': published
        }
