#! /usr/bin/env python3

# import zoomrlib

# with zoomrlib.open("PRJDATA.ZDT", "r") as file:
#     prjdata = zoomrlib.project.load(file)

# print(prjdata.name)
# for track in prjdata.tracks:
#     print(track.file)
# print(prjdata.master.file)

# with zoomrlib.open("EFXDATA.ZDT", "r") as file:
#     efxdata = zoomrlib.effect.load(file)

# print(efxdata.send_reverb_patch_name)
# print(efxdata.send_chorus_patch_num)

import os
import json

DATADIR = os.path.expanduser("~/devel/zoom/data/PRJ000")
# FILENAME = "PRJDATA.ZDT"
FILENAME = "SMPLSEQ.ZDT"

if os.path.isdir(DATADIR):
    os.chdir(DATADIR)
else:
    exit(1)

if not os.path.isfile(FILENAME):
    exit(1)

# fp = open(FILENAME, "rb")
fp = open(FILENAME, "a+b")

# 47 character long ASCII string
header = fp.read(48).decode(encoding="ascii")

# one byte, only in projects
if FILENAME == "PRJDATA.ZDT":
    is_protected = bool(int(fp.read(1).hex()))

ZERO = b"\00"
EOD = b"\xff\xff\xff\xff"


def bytes2int(b):
    assert type(b) is bytes
    return int("0x" + b.hex(), 0)


# Read Until the first non zero byte
def read_until_next_non_zero(fp, rewind=True):
    cursor = ZERO
    while cursor == ZERO:
        cursor = fp.read(1)

    position = fp.tell()
    print(position - 1, cursor)

    if rewind:
        fp.seek(position - 1)
    return cursor


def read_until_next_zero(fp):
    start = fp.tell()
    found = ""
    while (char := fp.read(1)) != ZERO:
        found += char.decode(encoding="ascii")

    length = fp.tell() - start
    print(start, length, found)

    return found


def read_until_next_zero_block(fp, block_size=8):
    count = 0
    while count <= block_size:
        nr = bytes2int(fp.read(1))
        if nr == 0:
            count += 1
        else:
            count = 0
            print(fp.tell() - 1, nr)


def read_field(fp, position=0, offset=4):
    if position > 0:
        fp.seek(position)
    nr1 = bytes2int(fp.read(1))
    nr2 = bytes2int(fp.read(1))
    assert fp.read(1) == ZERO
    assert fp.read(1) == ZERO
    return nr1, nr2


def read_track_data(fp, length=12):
    data = []
    i = 0
    while i < length:
        data.append(read_field(fp)[0])
        i += 1
    return data


def read_string(fp, length=256):
    start = fp.tell()
    text = read_until_next_zero(fp)
    fp.seek(start + length)
    return text


def read_seq_line(fp, length=4):
    line = []
    for i in range(length):
        line.append(bytes2int(fp.read(1)))
    return line


def get_all(fp):
    data = {
        "header": header,
        "is_protected": is_protected,
    }

    # tracks
    data["track_params"] = []
    fp.seek(64)
    data["track_params"].append(read_track_data(fp)[:8])
    fp.seek(96)
    data["track_params"].append(read_track_data(fp)[:8])
    fp.seek(128)
    data["track_params"].append(read_track_data(fp)[:8])

    data["track_data"] = []
    for i in range(8):
        data["track_data"].append(read_track_data(fp))

    # filenames
    data["filenames"] = []
    fp.seek(648)
    for i in range(9):
        data["filenames"].append(read_string(fp))

    data["unknown"] = []
    while True:
        b = read_until_next_non_zero(fp)
        if b == b"":
            break

        data["unknown"].append(
            {
                "position": fp.tell(),
                "data": read_field(fp),
            }
        )

    return data


def dump_all(data, filename="project.dump"):
    with open(os.path.join(DATADIR, filename), "w") as f:
        f.write(json.dumps(data, indent=2))
