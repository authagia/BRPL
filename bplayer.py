import math
import threading

import numpy as np
import pyaudio

from brstm import Brstm


class Bplayer:
    paused = True
    stopping = False
    p = None
    gain = 0.15
    on_load = None
    on_block_played = None

    def load(self,path):
        self.brstm = Brstm(path)
        self.brstm.decode_BRSTM_header()
        if not self.brstm.BRSTM_header["is_RSTM"]:
            raise ValueError
        self.brstm.decode_HEAD_header()
        if not self.brstm.HEAD_header["is_HEAD"]:
            raise ValueError
        self.brstm.decode_HEAD_chunk_1()
        if self.brstm.HEAD_chunk_1["codec"] == "?":
            raise ValueError
        self.brstm.decode_HEAD_chunk_3_offset_table()
        self.brstm.decode_ADPCM_channel_info()
        self.brstm.decode_ADPC_table_entry()
        self.brstm.decode_DATA_header()

        self.p = pyaudio.PyAudio() if self.p == None else self.p
        stream = self.p.open(
            self.brstm.HEAD_chunk_1["sample_rate"],
            self.brstm.HEAD_chunk_1["number_of_channel"],
            pyaudio.paInt16,
            output=True,
        )
        self.event = threading.Event()
        self.loop_thread = threading.Thread(target=self.loop,args=[stream, self.brstm, self.event])
        self.loop_thread.start()
        if self.on_load != None:
            self.on_load(
                self.brstm.HEAD_chunk_1["sample_rate"],
                self.brstm.HEAD_chunk_1["whole_number_of_samples"]
            )

    def play(self):
        self.paused = False
        self.event.set()

    def pause(self):
        self.paused = True

    def stop(self):
        self.stopping = True
        self.event.set()
        self.loop_thread.join()

    def loop(self, s:pyaudio.Stream, b:Brstm, evt:threading.Event):#lp loop_point  b_index block_index
        number_of_block = b.HEAD_chunk_1["whole_number_of_block"]
        samples_per_block = b.HEAD_chunk_1["samples_per_block"]
        lp_sample = b.HEAD_chunk_1["loop_start_point"]
        lp_block = math.floor(lp_sample/samples_per_block)
        lp_sample_at_block = lp_sample - samples_per_block * lp_block

        b_index = 0

        for i in range(lp_block):
            if self.paused :
                evt.wait()
                evt.clear()
            if self.stopping:
                s.close()
                self.stopping = False
                return

            PCM = b.read(b_index).T

            PCM = (PCM * self.gain).astype(np.int16)
            s.write(PCM.tobytes())
            b_index +=1
            if self.on_block_played != None:
               self.on_block_played(
                    self.brstm.HEAD_chunk_1["sample_rate"],
                    b_index*samples_per_block + len(PCM)
                )
            del PCM

        while True:
            if self.paused :
                evt.wait()
                evt.clear()
            if self.stopping:
                s.close()
                self.stopping = False
                return

            flag_loop_initial = b_index == lp_block
            flag_last_block = b_index == number_of_block -1

            PCM = b.read(b_index)
            PCM = PCM[lp_sample_at_block if flag_loop_initial else 0:].T
            PCM = (PCM * self.gain).astype(np.int16)
            s.write(PCM.tobytes())
            b_index = lp_block if flag_last_block else b_index +1
            if self.on_block_played != None:
                self.on_block_played(
                    self.brstm.HEAD_chunk_1["sample_rate"],
                    b_index*samples_per_block + len(PCM)
                )
            del PCM
            
