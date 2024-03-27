import math
import json
import random
import asyncio
import traceback
import unicodedata
from item import Item
from loguru import logger
from playwright.async_api import async_playwright


async def parse_metro(query: str, threads: int):
    semaphore = asyncio.Semaphore(threads)
    logger.info("Начинаю парсинг")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            await page.goto(f'https://online.metro-cc.ru/search?q={query}')
            items_quantity = await page.text_content('.heading-products-count.page-search__heading-count')
            pages_quantity = math.ceil(int(items_quantity.strip().split(' ')[0]) / 30)
            await page.close()
            item_links = await get_item_links(browser, query, pages_quantity, semaphore)
            logger.info(f"Найдено {len(item_links)} элементов подходящих условиям")
            await parsing(browser, item_links, semaphore)
    except Exception as e:
        logger.error(f"Ошибка {e} {traceback.format_exc()}")
    finally:
        await browser.close()


async def parsing(browser, items_link, semaphore):
    logger.info("Начинаю парсинг товаров")
    tasks = [asyncio.create_task(parsing_item(browser, link, semaphore)) for link in items_link]
    items = await asyncio.gather(*tasks)
    items_dict = [item.to_dict() for item in items]
    save_item(items_dict)
    logger.success(f"Парсинг прошел успешно. Сохранено {len(items)} элементов")


async def parsing_item(browser, item_link, semaphore):
    try:
        async with semaphore:
            sec = random.uniform(0, 1)
            await asyncio.sleep(sec)
            page = await browser.new_page()
            await page.goto(item_link)
            await page.wait_for_selector('.product-page-content__labels-and-short-attrs')

            id_text = await page.text_content('.product-page-content__article')
            item_id = id_text.split(':')[1].strip()

            item_element = await page.text_content('.product-page-content__product-name.catalog-heading.heading__h2')
            item_name = clean_text(item_element)

            brand_elements = await page.query_selector_all(
                '.product-attributes__list.style--product-page-short-list > *')
            for brand_element in brand_elements:
                brand_text = await brand_element.text_content()
                if 'Бренд' in brand_text:
                    item_brand = clean_text(brand_text.split('Бренд')[1])

            if await page.query_selector('.product-unit-prices__old-wrapper .product-price__sum-rubles'):
                regular_element = await page.query_selector(
                    '.product-unit-prices__old-wrapper .product-price__sum-rubles')
                regular_price = (await regular_element.text_content()).strip()
                promo_element = await page.query_selector(
                    '.product-unit-prices__actual-wrapper .product-price__sum-rubles')
                promo_price = (await promo_element.text_content()).strip()
                await page.close()
                return Item(item_id, item_name, item_link, item_brand, regular_price, promo_price)
            else:
                regular_element = await page.query_selector(
                    '.product-unit-prices__actual-wrapper .product-price__sum-rubles')
                regular_price = (await regular_element.text_content()).strip()
                await page.close()
                return Item(item_id, item_name, item_link, item_brand, regular_price)
    except Exception as e:
        logger.error(f"Ошибка {e} {traceback.format_exc()}")
        await page.close()


async def get_item_links(browser, query, pages_quantity, semaphore):
    logger.info("Собираю ссылки товаров")
    item_links = []
    tasks = []
    try:
        for count in range(1, pages_quantity + 1):
            tasks.append(asyncio.create_task(parse_item_links(browser, query, count, semaphore)))
        all_links = await asyncio.gather(*tasks)

        for list_links in all_links:
            item_links.extend(list_links)
    except Exception as e:
        logger.error(f"Ошибка {e} {traceback.format_exc()}")
    finally:
        return item_links


async def parse_item_links(browser, query, count, semaphore):
    async with semaphore:
        sec = random.uniform(0, 1)
        await asyncio.sleep(sec)
        item_links = []
        try:
            page = await browser.new_page()
            await page.goto(f"https://online.metro-cc.ru/search?q={query}&page={count}")
            await page.wait_for_selector('.page-search__products')
            items_on_page = await page.query_selector_all('.page-search__products > *')
            for item in items_on_page:
                if await item.query_selector_all('.catalog-2-level-product-card__title'):
                    continue
                else:
                    link = await item.query_selector('.product-card-photo__link')
                    item_links.append("https://online.metro-cc.ru" + await link.get_attribute('href'))
            await page.close()
        except Exception as e:
            logger.error(f"Ошибка {e} {traceback.format_exc()}")
        finally:
            return item_links


def save_item(items):
    with open('result.json', 'w', encoding='UTF-8') as file:
        file.write(json.dumps(items, ensure_ascii=False, indent=2))


def clean_text(text):
    text = unicodedata.normalize('NFKD', text)
    text = text.replace('\n', '').strip()
    return text
