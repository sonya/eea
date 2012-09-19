__all__ = ["is_num"]

import re

def is_num(string):
    return re.compile("[\d\.\-]+").match(string)
