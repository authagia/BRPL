from brstm import Brstm as B
import numpy as np

b = B("./streams/STRM125.brstm")
b.decode_BRSTM_header()
b.decode_HEAD_header()
b.decode_HEAD_chunk_1()
b.decode_HEAD_chunk_3_offset_table()
b.decode_DATA_header()
b.decode_ADPC_table_entry()
b.decode_ADPCM_channel_info()

f = open("out.pcm", "wb")

whole = np.array([0], np.int16)

for i in range(b.HEAD_chunk_1["whole_number_of_block"]):
    PCM = b.read(i)
    whole = np.concatenate([whole, PCM[0]])
    buf = PCM[0].tobytes()
    f.write(buf)
f.close()
print("file closed.")

