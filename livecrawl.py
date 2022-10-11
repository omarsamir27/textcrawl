import asyncio
import concurrent.futures.process
import datetime
import functools
import random

from aiohttp import ClientSession
import scraptools


def process_page(response_entry, warcfile, savefn, visit_count):
    response = response_entry[0]
    response_text = response_entry[1]
    if response.status != 200:
        return []
    page_soup = scraptools.soupify(response_text)
    page_data = scraptools.extract_text(page_soup)
    data = {
        "url": str(response.url),
        "warc": warcfile,
        "body": page_data,
        "time": response_entry[3],
        "doc-id": visit_count

    }
    savefn(data)
    if response_entry[2] == 0:
        return []
    return scraptools.extract_links(page_soup)
    # return scraptools.soup_links(page_soup, ['http', 'https'])


visit_count = 0
lock = asyncio.Lock()


async def scrap_url(url_queue, visited: set, warcfile, savefn,pool):
    global visit_count
    loop = asyncio.get_event_loop()
    while True:
        url_entry: (str, int) = await url_queue.get()
        url = url_entry[0]
        print(visit_count)
        outlinks = []
        if url in visited:
            url_queue.task_done()
            continue
        async with ClientSession() as session:
            try:
                async with session.get(url, headers={'Accept-Encoding': 'identity',
                                                     'Content-Type': 'text/html; charset=utf-8',
                                                     'User-agent': 'Mozilla/5.0'}) as response:
                    page = await response.text()
                    # await asyncio.sleep(random.random())
                    outlinks = await loop.run_in_executor(None, functools.partial(
                        process_page,
                        response_entry=(response, page, (url_entry[1] - 1), datetime.datetime.now().isoformat()),
                        warcfile=warcfile, savefn=savefn, visit_count=visit_count))
            except Exception as e:
                print(e)
                scraptools.log_error(url_entry[0])
        visited.add(url_entry[0])
        # if len(outlinks) != 0:
        #     for link in outlinks:
        #         if link not in visited:
        #             await url_queue.put((link, url_entry[1]))
        async with lock:
            visit_count += 1
        url_queue.task_done()


async def run(initial_seeds: list[(str, int)], warcfile: str, savefn, concurrency: (int, int) = (5, 5)):
    pool = concurrent.futures.process.ProcessPoolExecutor(max_workers=5)
    visited = set()
    url_queue = asyncio.Queue()
    for entry in initial_seeds:
        await url_queue.put(entry)
    scrapers = []
    # concurrency[0]
    for _ in range(100):
        scraper = asyncio.create_task(scrap_url(url_queue, visited, warcfile, savefn,pool))
        scrapers.append(scraper)

    await scrap_url(url_queue, visited, warcfile, savefn,pool)
    await url_queue.join()
    for scraper in scrapers:
        scraper.cancel()
    await asyncio.gather(*scrapers, return_exceptions=True)
