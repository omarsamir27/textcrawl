import asyncio
import os
import pathlib
from pathlib import Path
import sys
import seedgen
import warcextract
import configparser
import datetime
import livecrawl
import scraptools
from multiprocessing import Process


def warc_dryrun(warcs: str, dest_home: str):
    dest = Path(dest_home + f'/{datetime.datetime.now().isoformat()}')
    dest.mkdir(parents=True, exist_ok=False)
    warc_list = seedgen.list_from_file(warcs)
    for warc in warc_list:
        seeds = seedgen.extract_urls_from_warc(warc)
        out = Path(f'{dest}/{warc}_urls')
        out.parent.mkdir(parents=True,exist_ok=True)
        out.touch()
        out.write_text('\n'.join(seeds))


def warc_offline(warcs: str, extract_home: str, save_mode: str, use_outlinks: bool, crawl_depth: int,
                 concurrency: (int, int) = None):
    now = f'/{datetime.datetime.now().isoformat()}'
    extract = Path(extract_home + now)
    extract.mkdir(parents=True, exist_ok=False)
    currdir = os.getcwd()
    warc_list = seedgen.list_from_file(warcs)
    warc_list = [f'{currdir}/{warc}' for warc in warc_list]
    os.chdir(extract)
    procs = []
    for warc in warc_list:
        procs.append(
            Process(target=warcextract.extract_warc, args=(
                warc,
                save_mode,
                use_outlinks,
                crawl_depth,
                concurrency
            ))
        )
    for proc in procs:
        proc.start()
    for proc in procs:
        proc.join()


def warc_live(warcs: str, extract_home: str, save_mode: str, crawl_depth: int,
              concurrency: (int, int) = None):
    now = f'/{datetime.datetime.now().isoformat()}'
    savefn = scraptools.save_wet if save_mode == 'wet' else scraptools.save_txt
    extract = Path(extract_home + now)
    extract.mkdir(parents=True, exist_ok=False)
    currdir = os.getcwd()
    warc_list = seedgen.list_from_file(warcs)
    warc_list = [f'{currdir}/{warc}' for warc in warc_list]
    os.chdir(extract)
    for warc in warc_list:
        seeds = seedgen.extract_urls_from_warc(warc)
        seeds = seedgen.crawl_depth(seeds, crawl_depth)
        name = warc.rsplit('/',maxsplit=1)
        name = name[-1]
        asyncio.run(livecrawl.run(seeds, name, savefn, concurrency))


if __name__ == '__main__':
    print(os.getcwd())
    try:
        config_file = sys.argv[1]
        if not pathlib.Path.is_file(Path(config_file)):
            raise FileNotFoundError
    except IndexError:
        print("Must specify configuration file")
        exit(0)
    except FileNotFoundError:
        print(f'{config_file} configuration file not found')
        exit(0)
    config = configparser.ConfigParser()
    config.read(config_file)
    match config['DEFAULT']['OPERATION_MODE']:
        case 'warc_dryrun':
            warc_dryrun(config['DEFAULT']['WARCS_SRC_FILE'], config['DEFAULT']['WARCS_LINKS_EXTRACT_DIR'])
        case 'warc_offline':
            save_home = config['DEFAULT']['WET_DIR'] if config['DEFAULT']['SAVE_MODE'] == 'wet' else config['DEFAULT'][
                'TXT_DIR']
            warc_offline(
                config['DEFAULT']['WARCS_SRC_FILE'],
                save_home,
                config['DEFAULT']['SAVE_MODE'],
                config['DEFAULT'].getboolean('USE_WARC_OUTLINKS'),
                config['DEFAULT'].getint('CRAWL_DEPTH'),
                (config['DEFAULT']['NUM_CRAWLERS'], config['DEFAULT']['NUM_PROCESSORS'])
            )
        case 'warc_live':
            save_home = config['DEFAULT']['WET_DIR'] if config['DEFAULT']['SAVE_MODE'] == 'wet' else config['DEFAULT'][
                'TXT_DIR']
            warc_live(config['DEFAULT']['WARCS_SRC_FILE'],
                      save_home,
                      config['DEFAULT']['SAVE_MODE'],
                      config['DEFAULT'].getint('CRAWL_DEPTH'),
                      (config['DEFAULT'].getint('NUM_CRAWLERS'), config['DEFAULT'].getint('NUM_PROCESSORS'))
                      )
