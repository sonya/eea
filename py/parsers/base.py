BIG_ENDIAN = 0
LITTLE_ENDIAN = 1
DEFAULT_ENDIAN=BIG_ENDIAN
DEFAULT_WORDSIZE=2

def ieee64(arg):
    mts = 1.0
    sgn = 1
    if arg & 0x8000000000000000:
        sgn = -1

    exp = ((arg & 0x7ff0000000000000) >> 52) - (2 ** (11 - 1) - 1)
    mts_bits = (arg & 0x000fffffffffffff)
    pos = 0
    while pos < 52:
        bit = mts_bits & 1
        mts += 2 ** (pos - 52) * bit
        mts_bits = mts_bits >> 1
        pos += 1

    return sgn * (2 ** exp) * mts

class Parser:

    def __init__(self, filename, endian=None, wordsize=None):

        self.fd = open(filename, "rb")

        if endian:
            self.ENDIAN = endian
        else:
            self.ENDIAN = DEFAULT_ENDIAN

        if wordsize:
            self.WORDSIZE = wordsize
        else:
            self.WORDSIZE = DEFAULT_WORDSIZE

        self.position = 0
        self.cache = []
        self.buffer = []

    def read(self, length, ignore_exceptions=False):
        read_length = length - len(self.buffer)
        if read_length > 0:
            rawchars = self.fd.read(read_length)
            #chars = self.buffer + [c for c in self.fd.read(read_length)]
            chars = self.buffer + [c for c in rawchars]

            self.buffer = []
        else:
            chars = self.buffer[:length]
            self.buffer = self.buffer[length:]

        if len(chars) != length and not ignore_exceptions:
            raise Exception("not able to read %d characters" % length)

        self.position += length
        self.cache = chars + self.buffer
        return chars

    def unread(self):
        self.position -= len(self.cache)
        self.buffer = self.cache
        self.cache = []

    def read_char(self, ignore_exceptions=False):
        char = self.read(1, ignore_exceptions)
        if len(char) > 0:
            return chr(char[0])
        return None

    def read_string(self, length):
        return ''.join([chr(c) for c in self.read(length)])

    def read_word(self, length=None, endian=None):
        if length is None:
            length = self.WORDSIZE
        if endian is None:
            endian = self.ENDIAN

        chars = self.read(length)

        if endian == LITTLE_ENDIAN:
            chars.reverse()

        value = 0
        for c in chars:
            value = (value << 8) + c

        return value

    def read_double(self, endian=None):
        word = self.read_word(8, endian)
        return ieee64(word)

    def skip(self, bytes):
        self.cache = []
        self.buffer = []
        self.fd.read(bytes)
        self.position += bytes

    def skipto(self, position):
        self.skip(position - self.position)
