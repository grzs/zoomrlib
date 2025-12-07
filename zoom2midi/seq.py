from enum import IntEnum


class Duration(IntEnum):
    WHOLE = 192
    WHOLE_T = 128
    HALF_DOT = 144
    HALF = 96
    HALF_T = 64
    QUARTER_DOT = 72
    QUARTER = 48
    QUARTER_T = 32
    EIGHTH_DOT = 36
    EIGHTH = 24
    EIGHTH_T = 16
    SIXTEENTH_DOT = 18
    SIXTEENTH = 12
    SIXTEENTH_T = 8
    THIRTYSECOND_DOT = 9
    THIRTYSECOND = 6
    THIRTYSECOND_T = 4
    SIXTYFOURTH = 3
    SIXTYFOURTH_T = 2


class Note:
    """Representation of a Zoom sequencer binary note"""

    __slots__ = ("start", "_length_whole", "_length_fraction", "_channel", "_prop_x")

    def __init__(
        self, values_bin=None, start=0, length=Duration.WHOLE * 4, channel=255
    ):
        assert type(start) is int
        self.start = start

        if values_bin is not None:
            self.from_binary(values_bin)
        else:
            self.length = length
            self._channel = channel
            self._prop_x = 0  # this is the unknown 3rd byte of the note

    def __repr__(self):
        return "{:s}(start={:d}, length={:d}, channel={:d})".format(
            self.__class__.__name__, self.start, self.length, self.channel
        )

    @property
    def length(self):
        return (self._length_whole) * Duration.WHOLE + self._length_fraction

    @length.setter
    def length(self, length):
        if length > Duration.WHOLE:
            length_fraction = length % Duration.WHOLE
            length_whole = int((length - length_fraction) / Duration.WHOLE) - 1
        else:
            length_fraction = length
            length_whole = 0

        self._length_whole = length_whole
        self._length_fraction = length_fraction

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        assert value >= 0 and value <= 8 or value == 255
        self._channel = value

    @property
    def end(self):
        return self.start + self.length

    @property
    def is_step(self):
        return self._length_fraction != 255 and self.channel == 255

    @property
    def is_term(self):
        return self.to_binary() == b"\xff\xff\xff\xff"

    @property
    def is_empty(self):
        return self.to_binary() == b"\x00\x00\x00\x00"

    def from_binary(self, values_bin):
        assert type(values_bin) is bytes
        assert len(values_bin) == 4

        values = [i for i in values_bin]
        self._length_fraction = values[0]
        self._length_whole = values[1]
        self._prop_x = values[2]
        self.channel = values[3]

    def to_tuple(self):
        return self._length_fraction, self._length_whole, self._prop_x, self.channel

    def to_binary(self):
        bin_value = b""
        for prop in self.to_tuple():
            bin_value += prop.to_bytes(1, "little")
        return bin_value


class Sequence:
    __slots__ = ("filename", "notes")
    _header = b"ZOOM R8    SAMPLER SEQ DATA VER0001            \x00"
    _default_filename = "SMPLSEQ.ZDT"
    max_notes = 64 * 1024  # 65536

    def __init__(self, filename=None):
        self.filename = filename
        self.notes = [Note()]

        if filename is not None:
            print("No file specified, sequence is empty.")
            try:
                self.read_file()
            except TypeError as e:
                print("Wrong filename format, ", e)

    def __repr__(self):
        return "{:s}([\n  {}])".format(
            self.__class__.__name__,
            ",\n  ".join([repr(note) for note in self.notes]),
        )

    def __len__(self):
        return len(self.notes)

    @classmethod
    def _get_total_size(cls):
        return len(cls._header) + 4 * cls.max_notes

    @property
    def total_size(self):
        return self._get_total_size()

    @property
    def total_length(self):
        return sum(
            map(
                lambda note: note.length,
                (filter(lambda note: note.channel == 255, self.notes)),
            )
        )

    def _trim(self):
        """Ensure that sequence is closed properly and doesn't contain extra notes."""
        for i, note in enumerate(self.notes):
            if note.is_term:
                i += 1
                break
            elif note.is_empty:
                break

        if len(self.notes) == 0:
            self.notes.append(Note())
        elif len(self.notes) > i:
            self.notes = self.notes[:i]

    def multiply_notes(self, times=None):
        self._trim()
        self.notes *= times or int(self.max_notes - 2 / len(self.notes))
        self._close()

    def trim_and_close(self):
        self._trim()
        return self._close()

    def _close(self):
        term = Note(b"\xff\xff\xff\xff")
        actual_max_notes = self.max_notes - 2  # because of 8 bytes eof
        if len(self.notes) == 0:
            self.notes.append(Note())
        elif len(self.notes) > actual_max_notes:
            print("More notes than available space, truncating sequence!")
            self.notes = self.notes[:actual_max_notes]
            self.notes[-1] = term
            return 0

        if not self.notes[-1].is_term:
            self.notes.append(term)

        return actual_max_notes - len(self.notes)

    def to_messages(self, note_offset=0):
        messages = []
        for note in self.notes:
            if note.is_step:
                continue

            messages += [
                {
                    "type": "note_on",
                    "note": note.channel + note_offset,
                    "position": note.start,
                },
                {
                    "type": "note_off",
                    "note": note.channel + note_offset,
                    "position": note.end,
                },
            ]

        messages.sort(key=lambda msg: msg["position"])
        return messages

    def write_file(self, filename=None):
        if self.filename is None:
            if filename is None:
                self.filename = self._default_filename
                raise UserWarning(
                    "No filename specified, set to {}".format(self._default_filename)
                )
            else:
                self.filename = filename
        notes_left = self.trim_and_close()
        with open(self.filename, "wb") as fp:
            fp.seek(0)
            fp.write(self._header)
            for note in self.notes:
                assert isinstance(note, Note)
                fp.write(note.to_binary())

            # fill with zeros and an empty bar and more zeros
            empty_note = b"\x00\x00\x00\x00"
            empty_bar = b"\x00\x03\x00\xff"  # == Note().to_binary()
            fp.write(notes_left * empty_note + empty_bar + empty_note)

    def read_file(self, filename=None, append=False):
        if not append:
            self.notes = []
        with open(self.filename or filename, "rb") as fp:
            fp.seek(0)
            header = fp.read(len(self._header))
            assert header == self._header

            position = 0
            while True:
                note = Note(fp.read(4), position)
                if note.is_step:
                    position += note.length
                self.notes.append(note)
                if note.is_term:
                    break
