#
# Copyright 2012 Sonya Huang
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import parsers.base as base
from parsers.base import Parser

DBF_EXTENSION = "dbf"

class DbfParser(Parser):

    def __init__(self, filename):
        Parser.__init__(self, filename) # creates self.fd

        self.fields = []
        self.records = []
        self.headers_done = False
        self.records_done = False

        self.data_types = {
            'C': self.read_string_trim, # < 254 bytes
            'N': self.read_string_trim, # string repr of number, < 18 bytes
            #'L': self.read_logical, # 1 byte
            #'D': self.read_date, # YYYYMMDD
            #'M': self.read_memo, # 10 byte pointer
            'F': self.read_string_trim, # 20 bytes
            #'B': self.read_binary,
            #'G': self.read_ole,
            #'P': self.read_picture,
            #'Y': self.read_currency,
            #'T': self.read_datetime,
            'I': self.read_word, # 4 byte little endian
            #'V': self.read_varifield,
            #'X': self.read_variant,
            #'@': self.read_timestamp, # 8 bytes: 2 longs
            'O': self.read_double, # 8 bytes
            '+': self.read_word, # autoincrement value, 4 byte long
            }

    def update_read_status(self):
        char = self.read_char(ignore_exceptions=True)
        if char == '\x1a' or char is None:
            self.records_done = True
        else:
            self.unread()

    def read_string_trim(self, length):
        return self.read_string(length).strip('\x00 \r\n')

    ####################### header contents ########################
    # Byte     Length  Type  Endian  Description
    # 0        1       int           version number
    # 1        3       int           date of last update (YY, MM, DD)
    # 4        4       long  Little  number of records 
    # 8        2       int   Little  number of bytes in header
    # 10       2       int   Little  number of bytes in record
    # 12       2       int   Big     reserved, zero-filled
    # 14       1       int   Big     transaction flag 0x0 ended 0x1 started
    # 15       1       int   Big     encryption flag 0x0 no 0x1 yes
    # 16       4       int   Big     reserved
    # 20       8       int   Big     reserved
    # 28       1       int   Big     MDX flag
    # 29       1       int   Big     language driver ID
    # 30       2       int   Big     reserved, zero-filled
    # 32       32d     int   Big     field descriptor array
    # 32+32d   1       char          0x0D (Field Descriptor Terminator)
    ################################################################
    def read_header(self):
        if self.headers_done:
            return

        dbase_version_id = self.read_word(1)
        last_modified = (
            self.read_word(1) + 1900,
            self.read_word(1),
            self.read_word(1)
            )

        self.num_records = self.read_word(4, base.LITTLE_ENDIAN)
        self.header_length = self.read_word(2, base.LITTLE_ENDIAN)
        self.record_length = self.read_word(2, base.LITTLE_ENDIAN)
        self.skipto(32)
        while self.read_char() != '\x0d':
            self.unread()
            self.fields.append(self.read_field_desc())

        self.headers_done = True

        # in case the data contains no records
        self.update_read_status()

    ################# field descriptor contents ###################
    # Byte  Length  Type  Description
    # 0     11      char  field name (zero-filled)
    # 11    1       char  field type [BCDNLM@I+F0G]
    # 12    4       int   field data address (in memory for dbase)
    # 16    1       int   field length (max 255)
    # 17    1       int   decimal count (max 15)
    # 18    2       int   reserved
    # 20    1       int   work area ID
    # 21    2       int   reserved
    # 23    1       int   SET FIELDS flag
    # 24    7       int   reserved
    # 31    2       int   index field flag 0x0 no key 0x1 key exists
    ################################################################
    def read_field_desc(self):
        field = {
            "name": self.read_string(11).strip('\x00'),
            "type": self.read_char(),
            "address": self.read_word(4),
            "length": self.read_word(1),
            "decimcount": self.read_word(1),
            }
        self.skip(14)
        return field

    def read_all_records(self):
        while not self.records_done:
            self.records.append(self.read_record())

    # before each record there is a 1 byte record deletion flag 
    # 0x2a true 0x20 false
    def read_record(self):
        deleted = self.read_word(1)
        record = {}
        for field in self.fields:
            func = self.data_types[field["type"]]
            record[field["name"]] = func(field["length"])

        self.update_read_status()
        return record

    def __iter__(self):
        self.read_header()
        return self

    def next(self):
        if self.records_done:
            raise StopIteration
        return self.read_record()

