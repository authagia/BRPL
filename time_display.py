import math

from textual.widget import Widget


class Time_display(Widget):
    def __init__(self, name=None, current=0, duration=0) -> None:
        super().__init__(name)
        self.current = current
        self.duration = duration

    def render(self):
        disp = (
            str(int(self.current//60)) +":"+ str(int(self.current%60)).zfill(2) 
            + "/" 
            + str(int(self.duration//60)) +":"+ str(int(self.duration%60)).zfill(2)
            )

        padding_width = self.size.width - len(disp)
        padding_left = " " * math.floor(padding_width/2)
        padding_heght = self.size.height - 1
        return (
            "\n" * padding_heght
            + padding_left + disp
            )
