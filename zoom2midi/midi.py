from mido import Message, MidiFile, MidiTrack
from .seq import Duration, Note, Sequence


class ZoomMidiFile(MidiFile):
    zoom_track_name = "ZOOM sequence"
    _default_filename = "zoom.mid"

    def __init__(
        self,
        *args,
        note_offset=0,
        zoom_track_nr=0,
        sequence=None,
        sequence_file=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if self.filename is None:
            self.filename = self._default_filename

        self.tick_duration_ratio = self.ticks_per_beat / Duration.QUARTER
        self.note_offset = note_offset

        self.zoom_track_nr = None

        # find or create zoom track
        if len(self.tracks) > zoom_track_nr and self._track_has_notes(zoom_track_nr):
            self.zoom_track_nr = zoom_track_nr
        else:
            for i, track in enumerate(self.tracks):
                if track.name == self.zoom_track_name:
                    self.zoom_track_nr = i
                    break
        if self.zoom_track_nr is None:
            self._create_zoom_track()

        if isinstance(sequence, Sequence):
            self.seq = sequence
            self.from_sequence()
        else:
            self.seq = Sequence(filename=sequence_file)
            self.to_sequence()

    def _track_has_notes(self, track_nr):
        return bool(
            len([msg for msg in self.tracks[track_nr] if msg.type.startswith("note_")])
        )

    def _create_zoom_track(self):
        self.tracks.append(MidiTrack())
        self.zoom_track_nr = len(self.tracks) - 1
        self.tracks[-1].name = self.zoom_track_name

    def duration2ticks(self, duration: int):
        return int(duration * self.tick_duration_ratio)

    def ticks2duration(self, ticks: int):
        return int(ticks / self.tick_duration_ratio)

    def from_sequence(self, seq=None):
        if not isinstance(seq, Sequence):
            seq = self.seq

        track = self.tracks[self.zoom_track_nr]
        position = 0
        for msg in seq.to_messages(note_offset=self.note_offset):
            msg["time"] = self.duration2ticks(msg["position"] - position)  # delta
            position = msg.pop("position")
            track.append(Message(**msg))

    def to_sequence(self, seq=None):
        if not isinstance(seq, Sequence):
            seq = self.seq

        track = self.tracks[self.zoom_track_nr]
        channels = [[], [], [], [], [], [], [], []]
        position = 0
        for msg in track:
            if msg.type.startswith("note_"):
                channel_nr = msg.note - self.note_offset
                channel = channels[channel_nr]

                # close previous note
                if len(channel) > 0:
                    prev_note = channel[-1]
                    if msg.type == "note_off" or prev_note.length == 1:
                        prev_note.length = position - channel[-1].start

                if msg.type == "note_on":
                    note = Note(channel=channel_nr, start=position, length=1)
                    channel.append(note)
                    seq.notes.append(note)

            delta = self.ticks2duration(msg.time)
            if delta > 0:
                seq.notes.append(Note(start=position, length=delta))
                position += delta

        return seq.trim_and_close()
