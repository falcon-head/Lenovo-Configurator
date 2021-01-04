"""
__foldername__ = leno
__filename__ = lenovo.py
__author__ = Shrikrishna Joisa
__date_created__ = 03/01/2021
__date_last_modified__ = 04/01/2021
__python_version__ = 3.7.4 64-bit

"""

import scrapy
from scrapy.http import Request
from scrapy.selector import Selector
from ..items import LenoItem
import datetime
import json
from urllib.parse import urlparse
import re
from lxml.html import fromstring
import itertools
from selenium import webdriver
import time
from w3lib.html import remove_tags
from scrapy import signals
from pydispatch import dispatcher
from scrapy.http import FormRequest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from w3lib.http import basic_auth_header
import random
from Leno import settings
import logging
from random import randint
from selenium.webdriver.common.keys import Keys


class LenovoSpider(scrapy.Spider):
    name = "l_ca"
    username = ''
    pwd = ''
    PROJECT_ROOT = settings.PROJECT_ROOT

    def start_requests(self):

        """
        Passing the request to the URL and sending the response to the parse function. Proxy is used by using the NT authentication

        """

        #! Test link url https://h22174.www2.hpe.com/ngc/Welcome [Use it when the https://h22174.www2.hpe.com/SimplifiedConfig/Welcome# URL is down]
        yield scrapy.Request("https://dcsc.lenovo.com/#/categories/STG%40Servers%40Rack%20and%20Tower%20Servers", callback=self.parse, meta={'proxy': 'http://proxy.ins.dell.com:80'}, headers={'Proxy-Authorization': basic_auth_header(self.username, self.pwd)})

    def __init__(self, username='', pwd='', **kwargs):
        """
        Intialization of the chrome driver with different flags are used. Dispatcher is used to notify when the crawler stopped crawling

        Keyword Arguments:
            username {str} -- [nt username] (default: {''})
            pwd {str} -- [nt password] (default: {''})

        """
        self.username = username
        self.pwd = pwd

        # Chrome options
        chrome_option = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_option.add_experimental_option("prefs", prefs)
        chrome_option.add_argument("--disable-gpu-sandbox")
        chrome_option.add_argument("--incognito")
        chrome_option.add_argument("--disable-infobars")
        chrome_option.add_argument("--start-maximized")
        self.Browse = webdriver.Chrome(chrome_options=chrome_option)
        self.Browse.set_script_timeout(4000000)
        self.Browse.set_page_load_timeout(180000)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def parse(self, response):

        """
        Crawl through lenovo server products

        """

        # Get the URL
        self.Browse.get(response.url)
        time.sleep(10)

        # Change the region to Canada
        region_change = self.Browse.find_element_by_xpath('//div[@class="header__topbar__utils__item"][1]//div[1]//a')
        region_change.click()
        time.sleep(8)

        # Select to get the dropdown
        get_dropdown = self.Browse.find_element_by_xpath('//div[@class="ant-modal-body"]//div[contains(@class, "preference-section")][1]//div[@class="ant-select-selection__rendered"]')
        get_dropdown.click()
        time.sleep(5)
        input_dropdown = get_dropdown.find_element_by_xpath('//div[@class="ant-select-search__field__wrap"][1]//input[@class="ant-select-search__field"]')
        input_dropdown.send_keys("canada")
        time.sleep(3)
        language_span = self.Browse.find_element_by_xpath('//h4[contains(span, "L")]')
        language_span.click()
        time.sleep(3)

        # save preference
        save = self.Browse.find_element_by_xpath('//div[@class="buttons"]//button[contains(@class, "save")]')
        self.Browse.execute_script("arguments[0].scrollIntoView();", save)
        save.click()
        time.sleep(15)

        # Click on the servers
        click_servers = self.Browse.find_element_by_xpath('//div[@class="navigation"]//div[contains(@class, "navigation__tab")][1]')
        click_servers.click()
        time.sleep(10)


        # Click on the rack servers
        click_rack = self.Browse.find_element_by_xpath('//div[@class="category-child-detail__title"]//a[contains(text(), "Rack")]')
        self.Browse.execute_script("arguments[0].scrollIntoView();", click_rack)
        click_rack.click()
        time.sleep(10)

        # Go through the products
        product_list = self.Browse.find_elements_by_xpath('//div[@class="category-children-detail"]//div[@class="category-child-detail__item"]//button')
        j = 0
        for i in range(0, len(product_list)):
            j = j+1
            if( j == 1 or j == 2 or j == 3 or j == 9 or j == 10 or j==11 or j==12 or j == 13 or j == 14 or j == 15):
                each_product = self.Browse.find_elements_by_xpath('//div[@class="category-children-detail"]//div[@class="category-child-detail__item"]//button')[i]
                self.Browse.execute_script("arguments[0].scrollIntoView();", each_product)
                time.sleep(5)
                each_product.click()
                time.sleep(15)

                # # Make sure to display 30 products in minimum
                # find_the_dropdown = self.Browse.find_element_by_xpath('//div[@class="ant-pagination-options"]//div[@class="ant-select-selection-selected-value"]')
                # self.Browse.execute_script("arguments[0].scrollIntoView();", find_the_dropdown)
                # find_the_dropdown.click()
                # time.sleep(5)

                # # Select the dropdown with quantity 30
                # increase_the_quantity = self.Browse.find_element_by_xpath('//div[@class="ant-pagination-options"]//ul//li[3]')
                # increase_the_quantity.click()
                # time.sleep(10)

                # Capture the data here through the method of navigation
                the_table_tr = self.Browse.find_elements_by_xpath('//div[@type="preconfigured-models"]//table//tbody[@class="ant-table-tbody"]//tr')
                for i in range(0, len(the_table_tr)):

                    the_tr = self.Browse.find_elements_by_xpath('//div[@type="preconfigured-models"]//table//tbody[@class="ant-table-tbody"]//tr')[i]
                    button_customize = the_tr.find_element_by_xpath('.//td[@class="actions"]//button[contains(span, "Customize")]')
                    mpn = the_tr.find_element_by_xpath('//td[@class="actions"]//a//div').text
                    unit_price = the_tr.find_element_by_xpath('//td[@class="UnitPrice"]').text
                    server_model = self.Browse.find_element_by_xpath('//div[@class="ant-breadcrumb"]//span[4]').text
                    server_model = server_model.replace("/", "")
                    self.Browse.execute_script("arguments[0].scrollIntoView();", button_customize)
                    button_customize.click()
                    time.sleep(40)


                    configuration_price = self.Browse.find_element_by_xpath('//div[@class="summary-side-price__value"]').text

                    # Capture the components along with the parts
                    click_unconfigured = self.Browse.find_element_by_xpath('//div[@class="slick-track"]//div[contains(text(), "Unconfigure")]')
                    click_unconfigured.click()
                    time.sleep(30)

                    hxs = Selector(text=self.Browse.page_source)

                    # Click on the all the components and capture the data
                    try:
                        for comp_pos in self.Browse.find_elements_by_xpath('//div[contains(@class, "__sub-tab")]//span[contains(text(), "Processors") or contains(text(), "Memory") or contains(text(), "Storage") or contains(text(), "PCI")]'):
                            random_sleep = random.randint(7,15)
                            random_flic  = random.randint(3,9)
                            self.Browse.execute_script("arguments[0].scrollIntoView();", comp_pos)
                            try:
                                time.sleep(random_sleep)
                                comp_pos.click()
                                time.sleep(random_sleep)
                                hxs = Selector(text=self.Browse.page_source)
                                for component in hxs.xpath('//div[@class="section-panels"]//div[@role="tablist"]'):
                                    comp = ''.join(component.xpath('.//div[@class="section-panel-header__items"]//div[contains(@class,"__title")]/text()').extract())
                                    i = 0
                                    for table in component.xpath('.//div[@role="tabpanel"]//table'):
                                        i = i + 1
                                        heading = hxs.xpath('(//div[@class="section-panels"]//div[@role="tablist"]//div[@class="section-panel-header__items"]//table//tr)['+str(i)+']//th').extract()
                                        for row in table.xpath('.//tr'):
                                            item = LenoItem()
                                            item["Component"] = comp
                                            item["MPN"] = mpn
                                            item["Unit Price"] = unit_price
                                            item["Server Model"] = server_model
                                            item["Configuration Price"] = configuration_price
                                            item["Mode"] = "BTO"
                                            item['DateTime'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
                                            for pos,head in enumerate(heading):
                                                val = remove_tags(''.join(row.xpath('./td[{}]'.format(pos+1)).extract())).strip()
                                                if len(val) > 0:
                                                    item[remove_tags(head).strip()] = val
                                            if len(item.keys()) > 2:
                                                yield item
                                    time.sleep(6)
                            except Exception as e:
                                time.sleep(random_flic)
                                print("Error", e)
                                time.sleep(random_sleep)
                    except Exception as e:
                        time.sleep(500)
                        pass

                    time.sleep(6)

                    go_back_to_configure = self.Browse.find_element_by_xpath('//div[@class="ant-breadcrumb"]//span[4]')
                    self.Browse.execute_script("arguments[0].scrollIntoView();", go_back_to_configure)
                    go_back_to_configure.click()
                    time.sleep(6)

                    lose_it = self.Browse.find_element_by_xpath('//div[@class="ant-confirm-btns"]//button[contains(span, "Lose it")]')
                    self.Browse.execute_script("arguments[0].scrollIntoView();", lose_it)
                    lose_it.click()
                    time.sleep(14)

                time.sleep(6)

                # CTO
                try:
                    # Go to CTO tab
                    cto_tab = self.Browse.find_element_by_xpath('//div[@role="tab"]//span[contains(text(), "Configure")]')
                    self.Browse.execute_script("arguments[0].scrollIntoView();", cto_tab)
                    cto_tab.click()
                    time.sleep(8)

                    # CTO code here
                    get_cto_card = self.Browse.find_elements_by_xpath('//div[@class="category-cto-section__list"]//div[@class="ant-row"]//div[contains(@class, "category-cto-section__card")]')
                    for i in range(0, len(get_cto_card)):
                        each_card = self.Browse.find_elements_by_xpath('//div[@class="category-cto-section__list"]//div[@class="ant-row"]//div[contains(@class, "category-cto-section__card")]')[i]
                        configure_button = each_card.find_element_by_xpath('//div[@class="category-cto-card__customize"]//button')
                        mpn = each_card.find_element_by_xpath('//span[@class="category-cto-card__code"]').text
                        mpn = mpn.replace("Withdrawn", "")
                        server_model = self.Browse.find_element_by_xpath('//div[@class="ant-breadcrumb"]//span[4]').text
                        server_model = server_model.replace("/", "")
                        self.Browse.execute_script("arguments[0].scrollIntoView();", configure_button)
                        configure_button.click()
                        time.sleep(40)

                        # Capture the required data here
                        configuration_price = self.Browse.find_element_by_xpath('//div[@class="summary-side-price__value"]').text

                        # Capture the components along with the parts
                        click_unconfigured = self.Browse.find_element_by_xpath('//div[@class="slick-track"]//div[contains(text(), "Unconfigure")]')
                        click_unconfigured.click()
                        time.sleep(30)

                        hxs = Selector(text=self.Browse.page_source)

                        # Click on the all the components and capture the data
                        try:
                            for comp_pos in self.Browse.find_elements_by_xpath('//div[contains(@class, "__sub-tab")]//span[contains(text(), "Processors") or contains(text(), "Memory") or contains(text(), "Storage") or contains(text(), "PCI")]'):
                                random_sleep = random.randint(7,15)
                                random_flic  = random.randint(3,9)
                                self.Browse.execute_script("arguments[0].scrollIntoView();", comp_pos)
                                try:
                                    time.sleep(random_sleep)
                                    comp_pos.click()
                                    time.sleep(random_sleep)
                                    hxs = Selector(text=self.Browse.page_source)
                                    for component in hxs.xpath('//div[@class="section-panels"]//div[@role="tablist"]'):
                                        comp = ''.join(component.xpath('.//div[@class="section-panel-header__items"]//div[contains(@class,"__title")]/text()').extract())
                                        i = 0
                                        for table in component.xpath('.//div[@role="tabpanel"]//table'):
                                            i = i + 1
                                            heading = hxs.xpath('(//div[@class="section-panels"]//div[@role="tablist"]//div[@class="section-panel-header__items"]//table//tr)['+str(i)+']//th').extract()
                                            for row in table.xpath('.//tr'):
                                                item = LenoItem()
                                                item["Component"] = comp
                                                item["MPN"] = mpn
                                                item["Unit Price"] = ""
                                                item["Server Model"] = server_model
                                                item["Configuration Price"] = configuration_price
                                                item["Mode"] ="CTO"
                                                item['DateTime'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
                                                for pos,head in enumerate(heading):
                                                    val = remove_tags(''.join(row.xpath('./td[{}]'.format(pos+1)).extract())).strip()
                                                    if len(val) > 0:
                                                        item[remove_tags(head).strip()] = val
                                                if len(item.keys()) > 2:
                                                    yield item
                                        time.sleep(6)
                                except Exception as e:
                                    time.sleep(random_flic)
                                    print("Error", e)
                                    time.sleep(random_sleep)
                        except Exception as e:
                            time.sleep(500)
                            pass

                        time.sleep(6)

                        go_back_to_configure = self.Browse.find_element_by_xpath('//div[@class="ant-breadcrumb"]//span[4]')
                        self.Browse.execute_script("arguments[0].scrollIntoView();", go_back_to_configure)
                        go_back_to_configure.click()
                        time.sleep(6)

                        lose_it = self.Browse.find_element_by_xpath('//div[@class="ant-confirm-btns"]//button[contains(span, "Lose it")]')
                        self.Browse.execute_script("arguments[0].scrollIntoView();", lose_it)
                        lose_it.click()
                        time.sleep(15)

                except Exception as e:
                    print("CTO cards cannot be found")

                go_back_to_server = self.Browse.find_element_by_xpath('//div[@class="ant-breadcrumb"]//span[3]')
                self.Browse.execute_script("arguments[0].scrollIntoView();", go_back_to_server)
                go_back_to_server.click()
                time.sleep(10)

            else :

                print("I am a unconfigured server")
                time.sleep(10)

                get_cto_card = self.Browse.find_elements_by_xpath('//div[@class="category-cto-section__list"]//div[@class="ant-row"]//div[contains(@class, "category-cto-section__card")]')
                for i in range(0, len(get_cto_card)):
                    each_card = self.Browse.find_elements_by_xpath('//div[@class="category-cto-section__list"]//div[@class="ant-row"]//div[contains(@class, "category-cto-section__card")]')[i]
                    configure_button = each_card.find_element_by_xpath('//div[@class="category-cto-card__customize"]//button')
                    mpn = each_card.find_element_by_xpath('//span[@class="category-cto-card__code"]').text
                    mpn = mpn.replace("Withdrawn", "")
                    server_model = self.Browse.find_element_by_xpath('//div[@class="ant-breadcrumb"]//span[4]').text
                    server_model = server_model.replace("/", "")
                    self.Browse.execute_script("arguments[0].scrollIntoView();", configure_button)
                    configure_button.click()
                    time.sleep(40)

                    # Capture the required data here
                    configuration_price = self.Browse.find_element_by_xpath('//div[@class="summary-side-price__value"]').text

                    # Capture the components along with the parts
                    click_unconfigured = self.Browse.find_element_by_xpath('//div[@class="slick-track"]//div[contains(text(), "Unconfigure")]')
                    click_unconfigured.click()
                    time.sleep(30)

                    hxs = Selector(text=self.Browse.page_source)

                    # Click on the all the components and capture the data
                    try:
                        for comp_pos in self.Browse.find_elements_by_xpath('//div[contains(@class, "__sub-tab")]//span[contains(text(), "Processors") or contains(text(), "Memory") or contains(text(), "Storage") or contains(text(), "PCI")]'):
                            random_sleep = random.randint(7,15)
                            random_flic  = random.randint(3,9)
                            self.Browse.execute_script("arguments[0].scrollIntoView();", comp_pos)
                            try:
                                time.sleep(random_sleep)
                                comp_pos.click()
                                time.sleep(random_sleep)
                                hxs = Selector(text=self.Browse.page_source)
                                for component in hxs.xpath('//div[@class="section-panels"]//div[@role="tablist"]'):
                                    comp = ''.join(component.xpath('.//div[@class="section-panel-header__items"]//div[contains(@class,"__title")]/text()').extract())
                                    i = 0
                                    for table in component.xpath('.//div[@role="tabpanel"]//table'):
                                        i = i + 1
                                        heading = hxs.xpath('(//div[@class="section-panels"]//div[@role="tablist"]//div[@class="section-panel-header__items"]//table//tr)['+str(i)+']//th').extract()
                                        for row in table.xpath('.//tr'):
                                            item = LenoItem()
                                            item["Component"] = comp
                                            item["MPN"] = mpn
                                            item["Unit Price"] = ""
                                            item["Server Model"] = server_model
                                            item["Configuration Price"] = configuration_price
                                            item["Mode"] ="CTO"
                                            item['DateTime'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
                                            for pos,head in enumerate(heading):
                                                val = remove_tags(''.join(row.xpath('./td[{}]'.format(pos+1)).extract())).strip()
                                                if len(val) > 0:
                                                    item[remove_tags(head).strip()] = val
                                            if len(item.keys()) > 2:
                                                yield item
                                    time.sleep(6)
                            except Exception as e:
                                time.sleep(random_flic)
                                print("Error", e)
                                time.sleep(random_sleep)
                    except Exception as e:
                        time.sleep(500)
                        pass

                    time.sleep(6)

                    go_back_to_configure = self.Browse.find_element_by_xpath('//div[@class="ant-breadcrumb"]//span[4]')
                    self.Browse.execute_script("arguments[0].scrollIntoView();", go_back_to_configure)
                    go_back_to_configure.click()
                    time.sleep(8)

                    lose_it = self.Browse.find_element_by_xpath('//div[@class="ant-confirm-btns"]//button[contains(span, "Lose it")]')
                    self.Browse.execute_script("arguments[0].scrollIntoView();", lose_it)
                    lose_it.click()
                    time.sleep(25)


                go_back_to_server = self.Browse.find_element_by_xpath('//div[@class="ant-breadcrumb"]//span[3]')
                self.Browse.execute_script("arguments[0].scrollIntoView();", go_back_to_server)
                go_back_to_server.click()
                time.sleep(6)

    def spider_closed(self, spider):
        self.Browse.quit()
