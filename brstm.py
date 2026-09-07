import numpy as np


class Brstm:
    path = ""
    BRSTM_header = None
    HEAD_header = None
    HEAD_chunk_1 = None
    HEAD_chunk_2_header = None
    HEAD_chunk_3_header = None
    HEAD_chunk_3_offset_tables = None
    ADPCM_channel_infos = None
    ADPC_header = None
    ADPC_table_entry = None
    DATA_header = None

    Cached_PCM_Per_Block = None

    def __init__(self, path):
        self.path = path
        self.load()

    def decode_BRSTM_header(self):
        #REQ 
        if not self.BRSTM_header:
            header = self.raw[0:64]
            self.endian = "big" if(header[4:6]==b'\xfe\xff')else "little"
            self.BRSTM_header =  {
                "is_RSTM": "RSTM".encode("utf-8") == header[0:4],
                "byte_order": self.endian,
                ##"version": str(header[6])+"."+str(header[7]),
                ##"file_size": int.from_bytes(header[8:12], self.endian),
                "header_size": int.from_bytes(header[12:14], self.endian),
                ##"number_of_chunks": int.from_bytes(header[14:16], self.endian),
                "offset_to_HEAD": int.from_bytes(header[16:20], self.endian),
                "size_of_HEAD": int.from_bytes(header[20:24], self.endian),
                "offset_to_ADPC": int.from_bytes(header[24:28], self.endian),
                "size_of_ADPC": int.from_bytes(header[28:32], self.endian),
                "offset_to_DATA": int.from_bytes(header[32:36], self.endian),
                ##"size_of_DATA": int.from_bytes(header[36:40], self.endian),
                #"padding":header[40:64],
            }
        return self.BRSTM_header

    def decode_HEAD_header(self):
        #REQ BRSTM header 
        if not self.HEAD_header:
            index = self.BRSTM_header["offset_to_HEAD"]
            size = self.BRSTM_header["size_of_HEAD"]
            header = self.raw[index:index+size]
            self.HEAD_header = {
                "is_HEAD": "HEAD".encode("utf-8") == header[0:4],
                ##"length_of_entire_HEAD": int.from_bytes(header[4:8], self.endian),
                #"marker: header[8:12]",
                "offset_to_chunk_1": int.from_bytes(header[12:16], self.endian),
                #"marker: header[16:20]",
                ##"offset_to_chunk_2": int.from_bytes(header[20:24], self.endian),
                #"marker: header[24:28]",
                "offset_to_chunk_3": int.from_bytes(header[28:32], self.endian),
            }
        return self.HEAD_header

    def decode_HEAD_chunk_1(self):
        #REQ BRSTM header HEAD header
        if not self.HEAD_chunk_1:
            start_index = 8 + self.BRSTM_header["offset_to_HEAD"] + self.HEAD_header["offset_to_chunk_1"]
            size = 52
            chunk = self.raw[start_index:start_index+size]
            self.HEAD_chunk_1 = {
                "codec": "8-bit PCM" if(chunk[0]==0) else "16-bit PCM" if (chunk[0]==1) else "4bit-ADPCM" if (chunk[0]==2) else "?",
                "loop": chunk[1],
                "number_of_channel": chunk[2],
                #"padding: chunk[3]",
                "sample_rate": int.from_bytes(chunk[4:6], self.endian),
                #"padding: chunk[6:8]",
                "loop_start_point": int.from_bytes(chunk[8:12], self.endian),#in samples
                "whole_number_of_samples": int.from_bytes(chunk[12:16], self.endian),
                ##"absolute_offset_to_ADPCM": int.from_bytes(chunk[16:20], self.endian),
                "whole_number_of_block": int.from_bytes(chunk[20:24], self.endian),
                "block_size": int.from_bytes(chunk[24:28], self.endian),#in bytes
                "samples_per_block": int.from_bytes(chunk[28:32], self.endian),
                "size_of_final_block": int.from_bytes(chunk[32:36], self.endian),#in bytes, counted without padding
                "number_of_samples_in_final_block": int.from_bytes(chunk[36:40], self.endian),
                "size_of_final_block_with_padding": int.from_bytes(chunk[40:44], self.endian),#in bytes
                ##"number_of_samples_per_entry": int.from_bytes(chunk[44:48], self.endian),#in ADPC table
                ##"bytes_per_entry": int.from_bytes(chunk[48:52], self.endian),#in ADPC table
            }
        return self.HEAD_chunk_1

    def decode_HEAD_chunk_2_header(self):
        #REQ BRSTM header 
        if not self.HEAD_chunk_2_header:
            start_index = 8 + self.BRSTM_header["offset_to_HEAD"] + self.BRSTM_header["offset_to_chunk_2"]
            size = 4
            header = self.raw[start_index:start_index+size]
            self.HEAD_chunk_2_header = {
                ##"number_of_tracks": header[0],
                ##"track_description_type": header[1],
                #"padding: header[2:4]",
            }
        return self.HEAD_chunk_2_header

    def decode_HEAD_chunk_3_header(self):
        #REQ BRSTM header HEAD header
        if not self.HEAD_chunk_3_header:
            start_index = 8 + self.BRSTM_header["offset_to_HEAD"] + self.HEAD_header["offset_to_chunk_3"]
            size = 4
            header = self.raw[start_index:start_index+size]
            self.HEAD_chunk_3_header = {
                ##"number_of_channel": header[0], # not referenced
                #"padding: header[1:4]",
            }
        return self.HEAD_chunk_3_header

    def decode_HEAD_chunk_3_offset_table(self):
        #REQ BRSTM header HEAD header HEAD chunk 1 
        if not self.HEAD_chunk_3_offset_tables:
            self.HEAD_chunk_3_offset_tables = []

            start_index = 8 + self.BRSTM_header["offset_to_HEAD"] + self.HEAD_header["offset_to_chunk_3"] + 4
            for i in range(self.HEAD_chunk_1["number_of_channel"]):
                table_raw = self.raw[start_index+i*8:start_index+(i+1)*8]
                offset_table = {
                    #"marker": table_raw[0:4],
                    "offset_to_channel_info": int.from_bytes(table_raw[4:8], self.endian),
                }
                self.HEAD_chunk_3_offset_tables.append(offset_table)
        return self.HEAD_chunk_3_offset_tables

    def decode_ADPCM_channel_info(self):
        #REQ HEAD chunk 1, BRSTM header, HEAD chunk 3 offset tables
        if not self.ADPCM_channel_infos:
            self.ADPCM_channel_infos = []

            for i in range(self.HEAD_chunk_1["number_of_channel"]):
                start_index = 8 + self.BRSTM_header["header_size"] + self.HEAD_chunk_3_offset_tables[i]["offset_to_channel_info"]
                size = 56
                info_raw = self.raw[start_index:start_index+size]
                channel_info = {
                    #"marker": info[0:4],
                    ##"offset_to_channel_ADPCM_coefficients": int.from_bytes(info_raw[4:8], self.endian),
                    "int16_ADPCM_coefficients": [int.from_bytes(info_raw[8+j*2:8+(j+1)*2], self.endian, signed=True) for j in range(16)],
                    ##"gain": int.from_bytes(info_raw[40:42], self.endian, signed=True),
                    ##"initial_predictor/scale":int.from_bytes(info_raw[42:44], self.endian),
                    ##"history_sample_1":int.from_bytes(info_raw[44:46], self.endian, signed=True),
                    ##"history_sample_2": int.from_bytes(info_raw[46:48], self.endian, signed=True),
                    ##"loop_predictor/scale": int.from_bytes(info_raw[48:50], self.endian),
                    ##"loop_history_sample_1": int.from_bytes(info_raw[50:52], self.endian, signed=True),
                    ##"loop_history_sample_2":int.from_bytes(info_raw[52:54], self.endian, signed=True),
                    #"padding": info_raw[54:56]
                }
                self.ADPCM_channel_infos.append(channel_info)
        return self.ADPCM_channel_infos

    def decode_ADPC_header(self):
        #REQ BRSTM header
        if not self.ADPC_header:
            start_index = self.BRSTM_header["offset_to_ADPC"]
            size = 8
            header = self.raw[start_index:start_index+size]
            self.ADPC_header = {
                "is_ADPC": header[0:4].decode("utf_8") == "ADPC",
                "length_of_entire_ADPC_chunk": int.from_bytes(header[4:8], self.endian),
            }
        return self.ADPC_header

    def decode_ADPC_table_entry(self):
        #REQ BRSTM header, HEAD chunk 1
        if not self.ADPC_table_entry:
            self.ADPC_table_entry = []

            start_index = self.BRSTM_header["offset_to_ADPC"] + 8 # size of header
            c = self.HEAD_chunk_1["number_of_channel"]
            b = self.HEAD_chunk_1["whole_number_of_block"]
            
            # size = self.BRSTM_header["size_of_ADPC"] - 8 # padding is not cared
            size = c * b * 4
            table = self.raw[start_index:start_index+size]

            for i in range(b):
                entry = [
                    [
                        int.from_bytes(
                            table[8*i+4*j+2*k : 8*i+4*j+2*k +2],
                            self.endian,
                            signed=True
                        ) for k in range(2)
                    ] for j in range(c)
                ]
                self.ADPC_table_entry.append(entry)
                    
        return self.ADPC_table_entry

    def decode_DATA_header(self):
        #REQ BRSTM header
        if not self.DATA_header:
            start_index = self.BRSTM_header["offset_to_DATA"]
            size = 32
            header = self.raw[start_index:start_index+size]
            self.DATA_header = {
                ##"is_DATA": header[0:4].decode("utf_8") == "DATA",
                ##"length_of_entire_DATA_chunk": int.from_bytes(header[4:8], self.endian),
                "number_of_padding": int.from_bytes(header[8:12], self.endian) #Number of padding samples between header and ADPCM data? Always 0x18
                #"padding": header[12:32]
            }
        return self.DATA_header

    def getBlock(self, index):#returns blockdata array per channel
        #REQ HEAD chunk 1, BRSTM header, DATA header,
        c = self.HEAD_chunk_1["number_of_channel"]
        block_size = self.HEAD_chunk_1["block_size"]
        number_of_block = self.HEAD_chunk_1["whole_number_of_block"]
        offset = self.BRSTM_header["offset_to_DATA"] + 32 + block_size * c * index 
        if index + 1 == number_of_block: block_size = self.HEAD_chunk_1["size_of_final_block_with_padding"]
        return [self.raw[offset+ i * block_size : offset+ (i+1) * block_size] for i in range(c)]

    def read(self, index):
        c = self.HEAD_chunk_1["codec"]
        if c == "4bit-ADPCM":
            return self.read_ADPCM(index)
        elif c == "16-bit PCM":
            return self.read_16_PCM(index)
        elif c == "8-bit PCM":
            return self.read_8_PCM(index)
        elif c == "?":
            return

    def read_ADPCM(self, index): ## ぼパクリ from brstm; js lib
        #REQ HEAD chunk 1, ADPC table entry, BRSTM header, ADPCM channel info
        if self.HEAD_chunk_1["codec"] != "4bit-ADPCM":
            raise Exception("Not 4bit-ADPCM Codec")

        if not self.Cached_PCM_Per_Block:
            self.Cached_PCM_Per_Block = [[]] * self.HEAD_chunk_1["whole_number_of_block"]

        if len(self.Cached_PCM_Per_Block[index]) != 0:
            return self.Cached_PCM_Per_Block[index]

        ADPC_table_entry = self.ADPC_table_entry
        number_of_block = self.HEAD_chunk_1["whole_number_of_block"]
        block = self.getBlock(index)
        number_of_sample_in_block = self.HEAD_chunk_1["samples_per_block"] if index + 1 < number_of_block else self.HEAD_chunk_1["number_of_samples_in_final_block"]
        result = np.zeros((self.HEAD_chunk_1["number_of_channel"], number_of_sample_in_block), np.int16)
        for chan_num in range(self.HEAD_chunk_1["number_of_channel"]):

            coefficients = self.ADPCM_channel_infos[chan_num]["int16_ADPCM_coefficients"]

            channel_block = block[chan_num]
            sample_result = []

            ps = channel_block[0]
            yn1 = ADPC_table_entry[index][chan_num][0]
            yn2 = ADPC_table_entry[index][chan_num][1]
            data_index = 0

            sample_index = 0
            while sample_index < number_of_sample_in_block:
                out_sample = 0
                if sample_index % 14 == 0:
                    ps  = channel_block[data_index]
                    data_index += 1
                if (sample_index & 1) == 0 :
                    out_sample = channel_block[data_index] >> 4
                else:
                    out_sample = channel_block[data_index] & 0xf
                    data_index += 1
                if out_sample >= 8:
                    out_sample -= 16

                scale = 1 << (ps & 0xf)
                c_index = (ps >> 4) << 1
                out_sample = (
                    0x400
                    + ((scale * out_sample) << 11)
                    + coefficients[c_index if 0 <= c_index <= 15 else 0 if c_index < 0 else 15] * yn1 # clamp omitted
                    + coefficients[c_index+1 if 0 <= c_index+1 <= 15 else 0 if c_index+1 < 0 else 15] * yn2
                ) >> 11

                yn2 = yn1
                yn1 = out_sample if -0x8000 <= out_sample <= 0x7fff else -0x8000 if out_sample < -0x8000 else 0x7fff
                sample_result.append(yn1)
                sample_index += 1

            # if index < number_of_block -1 :
            #     self.ADPC_table_entry[index + 1][chan_num][0] = sample_result[-1]
            #     self.ADPC_table_entry[index + 1][chan_num][1] = sample_result[-2]
            
            result[chan_num] = np.array(sample_result, np.int16)
        self.Cached_PCM_Per_Block[index] = result
        return result

    def read_16_PCM(self, index):
        #REQ HEAD chunk 1
        if self.HEAD_chunk_1["codec"] != "16-bit PCM":
            raise Exception("Not 16-bit PCM Codec")

        if not self.Cached_PCM_Per_Block:
            self.Cached_PCM_Per_Block = [[]] * self.HEAD_chunk_1["whole_number_of_block"]

        number_of_block = self.HEAD_chunk_1["whole_number_of_block"]
        block = self.getBlock(index)
        number_of_sample_in_block = self.HEAD_chunk_1["samples_per_block"] if index + 1 < number_of_block else self.HEAD_chunk_1["number_of_samples_in_final_block"]
        result = np.zeros((self.HEAD_chunk_1["number_of_channel"], number_of_sample_in_block), np.int16)
        for chan_num in range(self.HEAD_chunk_1["number_of_channel"]) :
            sample_result = [int.from_bytes(block[2*j:2*j+2], self.endian, signed=True) for j in range(number_of_sample_in_block)]
            result[chan_num] = sample_result
        self.Cached_PCM_Per_Block[index] = result
        return result

    def read_8_PCM(self, index):
        #REQ HEAD chunk 1
        if self.HEAD_chunk_1["codec"] != "8-bit PCM":
            raise Exception("Not 8-bit PCM Codec")

        if not self.Cached_PCM_Per_Block:
            self.Cached_PCM_Per_Block = [[]] * self.HEAD_chunk_1["whole_number_of_block"]

        number_of_block = self.HEAD_chunk_1["whole_number_of_block"]
        block = self.getBlock(index)
        number_of_sample_in_block = self.HEAD_chunk_1["samples_per_block"] if index + 1 < number_of_block else self.HEAD_chunk_1["number_of_samples_in_final_block"]
        result = np.zeros((self.HEAD_chunk_1["number_of_channel"], number_of_sample_in_block), np.int8)
        for chan_num in range(self.HEAD_chunk_1["number_of_channel"]) :
            sample_result = [int.from_bytes(block[j:j+1], self.endian, signed=True) for j in range(number_of_sample_in_block)]
            #TODO === sapmle_result : 8bit -> 16bit
            #result[i] = sample_result
            result[chan_num] = np.ndarray(sample_result * 2, np.int16)
        self.Cached_PCM_Per_Block[index] = result
        return result

    def load(self):
        with open(self.path, "rb") as f:
            self.raw = f.read()

    def unload(self):
        del self.raw
