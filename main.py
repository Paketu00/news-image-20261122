"""Sunday, 22 November 2026: the world on a single page.

A standard-library-only Python program.  It renders a broadsheet
front page that sums up the world news reported on Sunday
22 November 2026, pixel by pixel, and saves the result as a PNG
named entry.png.

The picture is painted into an in-memory RGB buffer using a compact
5x7 bitmap typeface defined below.  The buffer is then encoded as a
PNG with zlib.  The program reads no clock, uses no randomness and
touches no network, so two runs always emit identical bytes.

Output goes only to MAKEFUN_OUTPUT_DIR when that variable is set,
otherwise to /output, otherwise to the working directory.  Each
candidate folder is tried in turn inside a guard, so an unwritable
or read-only location never aborts the run.
"""

import os
import struct
import zlib

PAGE_W = 1024
PAGE_H = 1024

PAPER = (246, 240, 226)
BLACK = (24, 22, 20)
SOFT = (88, 82, 72)
CRIMSON = (158, 24, 18)
NAVY = (18, 40, 88)
GREEN = (14, 88, 76)
OCHRE = (186, 128, 26)
TINT = (233, 224, 198)
TINT_BLUE = (222, 231, 240)
MIDNIGHT = (13, 20, 40)
OFFWHITE = (248, 246, 238)
PALE = (198, 206, 218)

LETTERS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10101", "10011", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}

SIGNS = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10001", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
}

ALL_GLYPHS = dict(LETTERS)
ALL_GLYPHS.update(SIGNS)


class Canvas:
    """A flat RGB pixel buffer with rectangle drawing only."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(bytes(colour) * (width * height))

    def fill_rect(self, x, y, w, h, colour):
        left = max(0, x)
        top = max(0, y)
        right = min(self.width, x + w)
        bottom = min(self.height, y + h)
        if right <= left or bottom <= top:
            return
        segment = bytes(colour) * (right - left)
        for row_y in range(top, bottom):
            start = (row_y * self.width + left) * 3
            self.pixels[start:start + len(segment)] = segment

    def frame(self, x, y, w, h, colour, thick=2):
        self.fill_rect(x, y, w, thick, colour)
        self.fill_rect(x, y + h - thick, w, thick, colour)
        self.fill_rect(x, y, thick, h, colour)
        self.fill_rect(x + w - thick, y, thick, h, colour)

    def rule(self, x, y, w, colour, thick=2):
        self.fill_rect(x, y, w, thick, colour)


def measure(text, scale):
    return len(text) * 6 * scale - scale if text else 0


def put_text(canvas, x, y, text, scale, colour):
    pen = x
    for ch in text.upper():
        glyph = ALL_GLYPHS.get(ch)
        if glyph is not None:
            for r, row in enumerate(glyph):
                for c, bit in enumerate(row):
                    if bit == "1":
                        canvas.fill_rect(pen + c * scale, y + r * scale,
                                         scale, scale, colour)
        pen += 6 * scale
    return pen


def put_centred(canvas, y, text, scale, colour, centre=512):
    put_text(canvas, centre - measure(text, scale) // 2, y, text, scale, colour)


def split_lines(text, limit):
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if len(trial) <= limit:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def put_paragraph(canvas, x, y, text, scale, colour, limit, gap=5):
    for line in split_lines(text, limit):
        put_text(canvas, x, y, line, scale, colour)
        y += 8 * scale + gap
    return y


def article(canvas, x, y, w, kicker, headline, body, accent):
    canvas.fill_rect(x, y, w, 6, accent)
    put_text(canvas, x, y + 14, kicker, 2, accent)
    cursor = y + 38
    for line in split_lines(headline, max(10, w // 18)):
        put_text(canvas, x, cursor, line, 3, BLACK)
        cursor += 26
    cursor += 4
    put_paragraph(canvas, x, cursor, body, 2, SOFT, max(16, w // 12), gap=5)


def build_front_page():
    page = Canvas(PAGE_W, PAGE_H, PAPER)
    page.frame(10, 10, PAGE_W - 20, PAGE_H - 20, BLACK, 3)
    page.frame(18, 18, PAGE_W - 36, PAGE_H - 36, BLACK, 1)

    # Masthead block
    put_centred(page, 34, "THE WORLD IN ONE PAGE", 6, BLACK)
    page.rule(48, 86, PAGE_W - 96, BLACK, 3)
    put_centred(page, 98, "SUNDAY  22 NOVEMBER 2026", 3, CRIMSON)
    put_centred(page, 128, "ONE DAY - ONE FRONT PAGE - EVERY CONTINENT", 2, SOFT)
    page.rule(48, 152, PAGE_W - 96, BLACK, 2)

    # Lead: COP31 in Antalya nears a deal on Sunday
    page.fill_rect(32, 164, PAGE_W - 64, 150, MIDNIGHT)
    put_text(page, 52, 178, "CLIMATE SUMMIT - ANTALYA, TURKIYE", 2, OCHRE)
    put_text(page, 52, 202, "COP31 NEARS FINAL DEAL", 5, OFFWHITE)
    put_text(page, 52, 244, "AS NEW PACKAGE LANDS SUNDAY", 4, OFFWHITE)
    put_paragraph(page, 52, 280,
                  "NEARLY 200 NATIONS, SECOND DAY OF OVERTIME. DRAFT OMITS FOSSIL FUELS, SETS 35% ELECTRIC POWER BY 2035.",
                  2, PALE, 78, gap=2)

    # Gulf escalation, two columns
    article(page, 36, 330, 452, "MANAMA - BAHRAIN + HORMUZ",
            "IRAN HITS BAHRAIN SITE, TANKERS STRUCK NEAR HORMUZ",
            "BAHRAIN SAID AN IRANIAN STRIKE SET A CIVILIAN INDUSTRIAL SITE ABLAZE, NO ONE HURT. TWO OIL TANKERS WERE HIT NEAR THE STRAIT OF HORMUZ.", CRIMSON)
    article(page, 536, 330, 452, "RIYADH - SAUDI ARABIA",
            "SAUDI DOWNS 3 HOUTHI MISSILES OVER RIYADH",
            "AIR DEFENCES INTERCEPTED THREE BALLISTIC MISSILES AT THE CAPITAL AND ANOTHER TOWARD THE WEST, AS THE COALITION STRUCK HODEIDAH PORT IN YEMEN.", NAVY)

    page.rule(48, 548, PAGE_W - 96, BLACK, 2)

    # War in the north, disaster in Java
    article(page, 36, 562, 452, "GULF OF FINLAND - BALTIC",
            "RUSSIAN CARGO SHIP ABLAZE AFTER DRONE STRIKE",
            "THE SANCTIONED SPARTA II CAUGHT FIRE OFF FINLAND, ITS CREW RESCUED. IN KRYVYI RIH A RUSSIAN DOUBLE-TAP KILLED 2 AND WOUNDED 60.", NAVY)
    article(page, 536, 562, 452, "SERANG, BANTEN - INDONESIA",
            "FACTORY FIRE: 3 DEAD, 36 WORKERS MISSING",
            "RESCUERS SEARCHED THE RUINS OF A CANDY FACTORY NEAR JAKARTA ON SUNDAY. THE BLAZE BROKE OUT SATURDAY WITH ABOUT 60 PEOPLE INSIDE.", GREEN)

    # Geneva and Shenzhen strip
    page.fill_rect(32, 756, 468, 62, TINT)
    page.frame(32, 756, 468, 62, BLACK, 1)
    put_text(page, 48, 766, "GENEVA - UNITED NATIONS", 3, NAVY)
    put_paragraph(page, 48, 794, "KILLER-ROBOT TALKS EXTENDED TO 2028", 2, BLACK, 36, gap=2)
    page.fill_rect(524, 756, 468, 62, TINT_BLUE)
    page.frame(524, 756, 468, 62, BLACK, 1)
    put_text(page, 540, 766, "SHENZHEN - CHINA", 3, GREEN)
    put_paragraph(page, 540, 794, "151 ROBOTS DANCE TO A WORLD RECORD", 2, BLACK, 36, gap=2)

    # Bottom briefs: Africa, America, Asia
    put_text(page, 36, 834, "BAYELSA - NIGERIA", 2, CRIMSON)
    put_text(page, 36, 856, "BOAT TOLL RISES TO 24", 2, BLACK)
    put_paragraph(page, 36, 880, "CROWDED BOAT TO A FUNERAL CAPSIZED. 24 DEAD, 24 SURVIVORS RESCUED.", 2, SOFT, 24, gap=4)
    put_text(page, 356, 834, "FLORIDA - USA", 2, CRIMSON)
    put_text(page, 356, 856, "RIVER BREAKS 73-YR RECORD", 2, BLACK)
    put_paragraph(page, 356, 880, "ST JOHNS RIVER HIT 18.8 FEET NEAR COCOA, ABOVE ITS 1953 RECORD. 150+ RESCUED.", 2, SOFT, 24, gap=4)
    put_text(page, 676, 834, "MANIPUR - INDIA", 2, GREEN)
    put_text(page, 676, 856, "TOXIC ALCOHOL KILLS 11", 2, BLACK)
    put_paragraph(page, 676, 880, "ADULTERATED LIQUOR KILLED 11 AND PUT 180+ IN HOSPITAL. INQUIRY ORDERED.", 2, SOFT, 25, gap=4)

    # Closing ticker
    page.fill_rect(32, 962, PAGE_W - 64, 34, BLACK)
    put_text(page, 44, 972, "ALSO: BANDA SEA QUAKE M6.8  +  IRAQ POWER-STATION FIRE KILLS 4", 2, OFFWHITE)
    return page


def encode_png(canvas):
    rows = bytearray()
    stride = canvas.width * 3
    for yy in range(canvas.height):
        rows.append(0)
        start = yy * stride
        rows.extend(canvas.pixels[start:start + stride])
    payload = zlib.compress(bytes(rows), 9)

    def make_chunk(kind, data):
        block = struct.pack(">I", len(data)) + kind + data
        return block + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += make_chunk(b"IHDR", ihdr)
    png += make_chunk(b"IDAT", payload)
    png += make_chunk(b"IEND", b"")
    return png


def main():
    image_bytes = encode_png(build_front_page())
    folders = []
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env_dir:
        folders.append(env_dir)
    folders.append("/output")
    folders.append(os.getcwd())
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            target = os.path.join(folder, "entry.png")
            with open(target, "wb") as handle:
                handle.write(image_bytes)
            print("wrote", target, len(image_bytes), "bytes")
            return
        except Exception:
            continue


if __name__ == "__main__":
    main()
