import argparse
import pathlib
import sys

from bplayer import Bplayer
from controll import Controll
from paged_view import Paged_view
from rich.panel import Panel
from textual.app import App
from textual.widgets import Header
from time_display import Time_display
from v_progress import V_progress


class Terminalapp(App):
    index = 0
    player = Bplayer()

    def __init__(self, file_list:list, screen: bool = True, driver_class = None, log: str = "", log_verbosity: int = 1, title: str = "Textual Application"):
        self.file_list = file_list
        super().__init__(screen, driver_class, log, log_verbosity, title)

    async def on_key(self,event):
        k = event.key
        if k == "down":
            self.list_disp.scroll_up()
        if k == "up":
            self.list_disp.scroll_down()
        if k == "right":
            self.list_disp.page_next()
        if k == "left":
            self.list_disp.page_prev()
        if k == " ":#pause/play
            self.player.play() if self.player.paused else self.player.pause()
            self.ctrl.paused = self.player.paused

        if k == "enter":#select
            self.change_track(self.list_disp.whole_index)
            self.ctrl.paused = False #?

        if k == ",":#previous
            self.change_track(self.index-1)
            
        if k == ".":#next
            self.change_track(self.index+1)

        if k == "0":#volume up
            gain = self.player.gain 
            gain += 0.01
            self.player.gain = min(gain, 1.00)

        if k == "9":#volume down
            gain = self.player.gain 
            gain -= 0.01
            self.player.gain = max(gain, 0.00)

        #if k == "r":#refresh view
        #    self.refresh()
            
        self.title = self.file_list[self.index].name + "   vol: " + str(int(100*self.player.gain)) + "%"

    async def on_load(self):#enter
        await self.bind("q", "quit")
        #await self.bind("r", "refresh")

    async def action_quit(self) -> None:
        self.player.pause()
        self.player.stop()
        return await super().action_quit()

    async def on_mount(self):
        self.time = Time_display(name="time_d",)
        self.prog = V_progress(name="v_prog", thickness=3)
        self.ctrl = Controll("c")
        self.list_disp = Paged_view([Panel(trk.name[0:-6]) for trk in self.file_list])#TODO color for more infomative

        await self.view.dock(Header(tall=False, clock=False))
        grid = await self.view.dock_grid(edge="left", size=12)
        grid.add_column("column")
        grid.add_row("time",size=3, max_size=5)
        grid.add_row("seekbar")
        grid.add_row("controll", size=7, max_size=10)
        grid.add_widget(self.time)
        grid.add_widget(self.prog)
        grid.add_widget(self.ctrl)

        await self.view.dock(self.list_disp, edge="left")
        self.title = self.file_list[self.index].name

        def p_onload(rate, num_sample):
            self.time.current = self.prog.current = 0
            self.time.duration = num_sample / rate
            self.prog.max = num_sample
            self.time.refresh()
            self.prog.refresh()
        self.player.on_load = p_onload

        def p_onblockplayed(rate, num_read_sample):
            self.time.current = num_read_sample /rate
            self.prog.current = num_read_sample
            self.time.refresh()
            self.prog.refresh()
        self.player.on_block_played = p_onblockplayed

        for i,file in enumerate(self.file_list):#search playable file
            try: 
                self.list_disp.children[self.index].style = "none"
                self.player.load(file)
                self.index = i
                self.list_disp.children[i].style = "blue"
                break
            except ValueError:
                self.list_disp.children[i].style = "red"
        else:
            print("there is no valid file")
        self.list_disp.refresh()

        self.refresh()
        
    def change_track(self, new_index):
            self.player.pause()
            self.player.stop()

            new_index = new_index % len(self.file_list)
            poned_list = self.file_list[new_index:] + self.file_list[0:new_index]
            for i,file in enumerate(poned_list):#search the next playable
                j = (i + new_index) % len(self.file_list)
                try:
                    self.list_disp.children[self.index].style = "none"
                    self.player.load(file)
                    self.index = j
                    self.list_disp.children[j].style = "blue"
                    break
                except ValueError:
                    self.list_disp.children[j].style = "red"
            else:
                print("there is no valid file",file=sys.stderr,flush=True)
            self.list_disp.refresh()
            self.player.play()


def get_file_list(path_str):
    ls = list(pathlib.Path(path_str).glob("*.brstm"))
    return ls

def main():
    parser = argparse.ArgumentParser(description='discription here')
    parser.add_argument('directory', type=str, help='directory contains BRSTM files')
    args = parser.parse_args()
    list = get_file_list(args.directory)
    Terminalapp.run(log="textual.log", file_list=list)

if __name__ == "__main__":#num : recursive
    main()
