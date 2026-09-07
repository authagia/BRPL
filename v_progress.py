import math
from textual.widget import Widget
from rich.panel import Panel

class V_progress(Widget):

    bars = ["", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

    def __init__(self, name=None, current=0, max=100, thickness=1):
        super().__init__(name)
        self.current = current
        self.max = max
        self.thickness = thickness

    #def render(self):
    #    length = math.floor(self.current/self.max * self.size.height*8) # number of "▁" 
    #    return (
    #        str(self.i ) +":"+ str(self.max) +":"+ str(length)
    #        + "\n" * (self.size.height - math.floor(length/8))
    #        + self.bars[length % 8] * self.thickness + "\n"
    #        + (self.bars[8] * self.thickness + "\n") * math.floor(length/8)
    #    )

    def render(self):
        padding_width = self.size.width - self.thickness
        padding_left = " " * math.floor(padding_width/2)
        bar_height = self.size.height - 2

        rate = self.current / self.max if self.current <= self.max else 1
        complete_part = math.floor(rate * bar_height)
        index_devided_part = math.ceil((rate * bar_height - complete_part)*8)

        return (
            padding_left + "━" * self.thickness + "\n"
            + "\n" * (bar_height - complete_part - 1)
            + (padding_left + (self.bars[index_devided_part] * self.thickness + "\n") if rate !=1 else "")
            + (padding_left + self.bars[8] * self.thickness + "\n") * complete_part
            + padding_left + "━" * self.thickness
        )

    def on_click(self):
        self.current += 64
        self.refresh()
