import math
import sys
import threading

import miniaudio as ma
import numpy as np
from brstm import Brstm


class Bplayer:
    paused = True
    stopping = False
    gain = 0.60
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

        device = ma.PlaybackDevice(
            output_format=ma.SampleFormat.SIGNED16,
            nchannels=self.brstm.HEAD_chunk_1["number_of_channel"],
            sample_rate=self.brstm.HEAD_chunk_1["sample_rate"],
            )
        
        self.event = threading.Event()
        self.loop_thread = threading.Thread(target=self.play_thread,args=[device, self.brstm, self.event])
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
        #print("start stopping",self.brstm.path,file=sys.stderr,flush=True)
        self.stopping = True
        self.event.set()
        self.loop_thread.join(1)
        #print("stopped.",file=sys.stderr,flush=True)
    
    def play_thread(self, dev:ma.PlaybackDevice, b:Brstm, evt: threading.Event):#create 1-loop list
        number_of_block = b.HEAD_chunk_1["whole_number_of_block"]
        samples_per_block = b.HEAD_chunk_1["samples_per_block"]
        lp_sample = b.HEAD_chunk_1["loop_start_point"]
        lp_block = math.floor(lp_sample/samples_per_block)
        lp_sample_at_block = lp_sample - samples_per_block * lp_block
        sr = self.brstm.HEAD_chunk_1["sample_rate"]
        n_ch = self.brstm.HEAD_chunk_1["number_of_channel"]

        def check_app_state():
            if self.paused:
                evt.wait()
                evt.clear()
            if self.stopping:
                return True
            return False

        def get_next_block():
            block_index = 0
            while True:
                dat = b.read(block_index).T
                yield dat, block_index
                block_index = lp_block if (block_index == number_of_block-1) else block_index +1

        def pcm_generator():
            next_size = yield b''
            buffer = np.zeros((1, n_ch)).astype(np.int16)
            for blk, b_index in get_next_block():
                if check_app_state():break

                if b_index == lp_block:
                    blk = blk[lp_sample_at_block:]
                blk_size = len(blk)
                buffer = np.concatenate([buffer, blk])

                while next_size <= len(buffer):
                    if check_app_state():break

                    tmp = yield (buffer[0:next_size] * self.gain).astype(np.int16)
                    buffer = buffer[next_size:]
                    next_size = tmp
                else:
                    left_size = len(buffer)
                    if self.on_block_played != None:
                        self.on_block_played(
                            sr,
                            b_index*samples_per_block + (blk_size - left_size),
                        )
                    continue
                break

        stream = pcm_generator()
        next(stream)  # start the generator
        evt.clear()
        dev.start(stream)
        while True:
            evt.wait()
            if self.stopping:
                dev.stop()
                dev.close()
                self.stopping = False
                break
