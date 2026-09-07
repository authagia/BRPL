import copy
# import math
# from functools import reduce
# from multiprocessing.dummy import Array

from rich.console import Group
from textual.reactive import Reactive
from textual.widget import Widget


class Paged_view(Widget):
    whole_index = 0
    pages = []
    curr_page = 0
    cursor = Reactive(0)
    def __init__(self, children, name: str = None, ) -> None:
        super().__init__(name)
        self.children = children


    def pager(self):
        page_height = 0
        page = []
        pages = []
        for child in self.children:
            if (page_height + (child.height or 3)) > self.size.height:
                pages.append(page)
                page = []
                page_height = 0

            page.append(child)
            page_height += child.height or 3
        pages.append(page)
        self.pages = pages


    def render(self):
        self.pager()
        page = copy.deepcopy(self.pages[self.curr_page])
        for i, elm in enumerate(page):
            if i == self.cursor:
                elm.style = "green"
        return Group(* page)


    def scroll_up(self):
        self.whole_index += 1
        self.whole_index = self.whole_index % len(self.children)
        
        self.cursor += 1
        if len(self.pages[self.curr_page]) == self.cursor:
            self.cursor = 0
            self.curr_page += 1
            self.curr_page = self.curr_page % len(self.pages)

    def scroll_down(self):
        self.whole_index -= 1
        self.whole_index = self.whole_index % len(self.children)

        self.cursor += -1
        if self.cursor == -1:
            self.cursor = len(self.pages[self.curr_page-1]) -1
            self.curr_page -= 1
            self.curr_page = self.curr_page % len(self.pages)

    def ok(self):
        pass

    def page_next(self):
        self.curr_page += 1
        self.curr_page = self.curr_page % len(self.pages)
        self.whole_index  = sum([len(l) for l in self.pages[0:self.curr_page]])
        self.cursor = 0
        self.refresh()

    def page_prev(self):
        self.curr_page -= 1
        self.curr_page = self.curr_page % len(self.pages)
        self.whole_index  = sum([len(l) for l in self.pages[0:self.curr_page]])
        self.cursor = 0
        self.refresh()
