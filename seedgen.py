import operator
import os

from warcio import ArchiveIterator
from functools import reduce


def list_from_file(file: str) -> list[str]:
    print(os.getcwd())
    with open(file, 'r') as filelist:
        listing = [line.rstrip() for line in filelist.readlines()]
    return listing


def extract_urls_from_warc(warc: str) -> list[str]:
    seeds = []
    with open(warc, 'rb') as stream:
        for record in ArchiveIterator(stream):
            if record.rec_type == 'response':  # Response is the record type for HTML/txt files
                url = record.rec_headers.get_header('WARC-Target-URI')
                seeds.append(url)
    return seeds


def seeds_from_warclist_flat(seeds: str) -> list[str]:
    listing = list_from_file(seeds)
    seeds = list(map(extract_urls_from_warc, listing))
    seeds = reduce(operator.concat, iter(seeds))
    with open('../warc_url_seeds.txt', 'w') as output:
        output.write('\n'.join(seeds))
    return seeds


def crawl_depth(seeds: list[str], depth: int = 0) -> list[(str, int)]:
    return [(url, depth) for url in seeds]
