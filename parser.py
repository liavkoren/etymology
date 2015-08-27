from collections import namedtuple
from pprint import pprint as pp

from bs4 import BeautifulSoup as Soup
import requests


ETYMONLINE_URL = 'http://www.etymonline.com/index.php?l={letter}&p={page}'


def scrap_etymonline():
    url = ETYMONLINE_URL.format(letter='a', page=0)
    response = requests.get(url)
    return Soup(response.content, 'html.parser')


def load_etymonline_dump():
    with open('etymoline_excerpt.html', 'r') as file:
        return Soup(file, 'html.parser')


def get_description_list(soup):
    """ Give an soup instance attempts to return an iterator over the dd element, or an empty list. """
    try:
        return soup.dl.children
    except AttributeError:
        return []


Entry = namedtuple('Entry', ['term', 'roots', 'cross_references', 'source'])


class TagNames:
    """ Enumerates DescriptionList tag types. """
    TERM = 'dt'
    DEFINITION = 'dd'
    WHITESPACE = '\n'


class DescriptionListParser:
    def parse(self, description_list):
        """
        Given a BeautifulSoup iterator over a <dl> list, parses the list into Entry named tuples.

        Loosely based on da beez's recursive descent parser in the Python Cookbook.
        """
        self.description_list = description_list
        self.tag = None
        self.next_tag = None
        self.entries = []
        self._advance()

        # for tag in self.description_list:
        while self.next_tag:
            term = self.get_tag_text()
            spans = self.next_tag.find_all('span')
            roots = [tag.text for tag in spans if tag['class'] == ['foreign']]
            hyperlinks = self.next_tag.find_all('a')
            cross_refs = [tag.text for tag in hyperlinks if tag['class'] == ['crossreference']]
            self.entries.append(Entry(term, roots, cross_refs, 'etymonline'))
            self._accept()

        return self.entries

    def get_tag_text(self):
        try:
            return self.tag.text
        except AttributeError:
            return ''

    def _advance(self):
        """ Advance to the next set of dt/dd tags.  """
        dt_tag = self._next_tag()
        self.tag = dt_tag

        dd_tag = self._next_tag()
        self.next_tag = dd_tag

    def _next_tag(self):
        tag = next(self.description_list, None)
        while tag == TagNames.WHITESPACE:
            tag = next(self.description_list, None)
        return tag

    def _accept(self):
        if self.tag.name == TagNames.TERM and self.next_tag.name == TagNames.DEFINITION:
            self._advance()
        else:
            raise SyntaxError('Unexpected tag.')


parser = DescriptionListParser()
soup = load_etymonline_dump()
description_list = get_description_list(soup)
result = parser.parse(description_list)

pp(result)
print("Ding!")

