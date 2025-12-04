from .seq import Duration, Note, Sequence

# bayan
ghe = Note(length=Duration.QUARTER, channel=1)
ke = Note(length=Duration.QUARTER, channel=2)

# dayan
ta = Note(length=Duration.QUARTER, channel=4)
tin = Note(length=Duration.QUARTER, channel=5)
te = Note(length=Duration.QUARTER, channel=3)

# complex bols
GHE = [ghe, Note(length=Duration.QUARTER)]
KE = [ke, Note(length=Duration.QUARTER)]
TA = [ta, Note(length=Duration.QUARTER)]
TU = TA  # TODO
TIN = [tin, Note(length=Duration.QUARTER)]
TE = [te, Note(length=Duration.QUARTER)]
TETE = [
    Note(length=Duration.EIGHTH, channel=3),
    Note(length=Duration.EIGHTH),
    Note(length=Duration.EIGHTH, channel=3),
    Note(length=Duration.EIGHTH),
]
DHA = [ghe, ta, Note(length=Duration.QUARTER)]
DHIN = [ghe, tin, Note(length=Duration.QUARTER)]
THIN = [ke, tin, Note(length=Duration.QUARTER)]
DHAGE = [
    Note(length=Duration.EIGHTH, channel=1),  # ghe
    Note(length=Duration.EIGHTH, channel=4),  # ta
    Note(length=Duration.EIGHTH),
    Note(length=Duration.EIGHTH, channel=1),  # ghe
    Note(length=Duration.EIGHTH),
]
TEREKETE = [
    Note(length=Duration.SIXTEENTH, channel=3),
    Note(length=Duration.SIXTEENTH),
    Note(length=Duration.SIXTEENTH, channel=3),
    Note(length=Duration.SIXTEENTH),
    Note(length=Duration.SIXTEENTH, channel=2),
    Note(length=Duration.SIXTEENTH),
    Note(length=Duration.SIXTEENTH, channel=3),
    Note(length=Duration.SIXTEENTH),
]

# taals
TEENTAAL = Sequence()
TEENTAAL.notes = (
    (DHA + DHIN + DHIN + DHA)
    + (DHA + DHIN + DHIN + DHA)
    + (DHA + TIN + TIN + TA)
    + (TETE + DHIN + DHIN + DHA)
)

EKTAAL = Sequence()
EKTAAL.notes = (
    (DHIN + DHIN + DHAGE + TEREKETE)
    + (TU + TA + TE + TA)
    + (DHAGE + TEREKETE)
    + (DHIN + TA)
)
