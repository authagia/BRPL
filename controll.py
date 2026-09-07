from rich.panel import Panel
from textual.reactive import Reactive
from textual.widget import Widget


class Controll(Widget):
    paused = Reactive(True)
    play_art = "⢸⣷⣦⡀     \n⢸⣿⣿⣿⣷⣄⡀  \n⢸⣿⣿⣿⣿⣿⣿⠶ \n⢸⣿⣿⣿⡿⠋⠁  \n⢸⡿⠟⠁     "
    
    pause_art = "⣿⣿⠀⠀⠀⣿⣿\n⣿⣿⠀⠀⠀⣿⣿\n⣿⣿⠀⠀⠀⣿⣿\n⣿⣿⠀⠀⠀⣿⣿\n⣿⣿⠀⠀⠀⣿⣿"
    def render(self):
        "奏" "停"
        return Panel(self.play_art if self.paused else self.pause_art)

    #async def on_click(self, event) -> None:
    #    self.playing = False if self.playing else True
    #    return await super().on_click(event)
