from warcio import ArchiveIterator
import scraptools
import seedgen
import livecrawl


def extract_warc(warc: str, save_mode: str, use_outlinks=False, depth=0,
                 concurrency: (int, int) = None):
    savefn = scraptools.save_wet if save_mode == 'wet' else scraptools.save_txt
    with open(warc, 'rb') as stream:
        for record in ArchiveIterator(stream):
            if record.rec_type == 'response':
                soup = scraptools.soupify(record.content_stream().read())
                url = record.rec_headers.get_header('WARC-Target-URI')
                data = {
                    "url": url,
                    "warc": warc,
                    "body": soup.text,
                    "time": record.rec_headers.get_header('WARC-Date'),
                    "doc-id": record.rec_headers.get_header('WARC-Doc-ID')
                }
                savefn(data)
                if use_outlinks:
                    links = scraptools.soup_links(soup, ['http', 'https'])
                    links = seedgen.crawl_depth(links, depth)
                    livecrawl.run(links, warc, savefn, concurrency)
