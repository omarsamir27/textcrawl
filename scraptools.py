import os

from bs4 import BeautifulSoup
import codecs
import datetime
from selectolax.parser import HTMLParser

class WetRecord:
    warc_version: str
    warc_type: str
    warc_date: str
    warc_target_uri: str
    warc_doc_id: str
    content_type: str
    content_length: int
    content: str

    def __init__(self, version='WARC/1.0', type='response', date=datetime.datetime.min.isoformat(), uri='',
                 doc_id='', content_type='application/http', content=''):
        self.warc_version = version
        self.warc_type = type
        self.warc_date = date
        self.warc_target_uri = uri
        self.warc_doc_id = doc_id
        self.content_type = content_type
        self.content = content
        self.content_length = len(content)

    def __str__(self):
        return self.warc_version + '\n' + 'WARC-Type: ' + self.warc_type + '\n' + 'WARC-Date: ' + self.warc_date + '\n' + \
               'WARC-Target-URI: ' + self.warc_target_uri + '\n' + 'WARD-Doc-ID: ' + self.warc_doc_id + '\n' + 'Content-Type: ' + \
               self.content_type + '\n' + 'Content-Length: ' + str(self.content_length) + '\n' + self.content


# def soupify(response_text) -> BeautifulSoup:
#     soup = BeautifulSoup(response_text, 'lxml')
#     if soup.original_encoding == 'windows-1256':
#         text = codecs.decode(obj=response_text, encoding='utf-8', errors='strict')
#         soup = BeautifulSoup(text, 'lxml')
#     return soup

def soupify(response_text) -> HTMLParser:
    return HTMLParser(response_text)

def extract_text(tree:HTMLParser):
    if tree.body is None:
        return None

    for tag in tree.css('script'):
        tag.decompose()
    for tag in tree.css('style'):
        tag.decompose()

    text = tree.body.text(separator='\n')
    return text

def extract_links(tree):
    outlinks = []
    for tag in tree.tags('a'):
        attrs = tag.attributes
        if 'href' in attrs:
            outlinks.append(attrs['href'])
    return outlinks


def soup_links(soup: BeautifulSoup, protocols: [str] = None) -> list[str]:
    if protocols is None:
        return [link.get('href') for link in soup.find_all('a')]
    outlinks = []
    for link in soup.find_all('a'):
        outlink: str = link.get('href')
        if outlink is None:
            return []
        protocol = outlink.split(':')[0]
        if protocol in protocols:
            outlinks.append(outlink)
    return outlinks


def save_wet(data: dict):
    warcname: str = data["warc"]
    warcname = warcname.rsplit('.', maxsplit=1)[0]
    record = WetRecord(
        date=data["time"],
        uri=data["url"],
        doc_id=warcname + '-' + str(data["doc-id"]),
        content=data["body"],
    )
    with open(f'{warcname}.wet', 'a') as wet:
        wet.write((str(record) + '\n--\n'))
        wet.flush()
        os.fsync(wet)


def write_file_recursive(fileURI: str, data: str):
    from pathlib import Path
    if fileURI[-1] == '/':
        fileURI = fileURI.rstrip(fileURI[-1])
    fileURI = fileURI + '.txt'
    output_file = Path(fileURI)
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    try:
        output_file.write_text(data)
    except:
        pass


def save_txt(data: dict):
    write_file_recursive(data["url"], data["body"])


def log_error(url: str):
    with open('../errors.txt', 'a+') as error_log:
        error_log.write(f'{url}\n')
