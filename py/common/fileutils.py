import os
from common import config

# TODO check for path existence in all filepath functions

# not temporary
def getimagepath(imagename, *subdirs):
    imagedir = os.path.join(config.PROJECT_ROOT, "images")
    if len(subdirs):
        dirlist = [imagedir] + list(subdirs)
        imagedir = os.path.join(*dirlist)
        if not os.path.exists(imagedir):
            os.mkdir(imagedir)
    return os.path.join(imagedir, imagename)

def getdatadir(*subdirs):
    if not len(subdirs):
        directory = config.DATA_DIR
    else:
        dirlist = [config.DATA_DIR] + list(subdirs)
        directory = os.path.join(*dirlist)
    return directory

def getdatapath(*args):
    filename = args[0]
    directory = getdatadir(*args[1:])
    path = os.path.join(directory, filename)
    return path

def getcachedir(*subdirs):
    if not len(subdirs):
        directory = config.DATA_CACHE_DIR
    else:
        dirlist = [config.DATA_CACHE_DIR] + list(subdirs)
        directory = os.path.join(*dirlist)
        if not os.path.exists(directory):
            os.mkdir(directory)

    return directory

def getcache(*args):
    filename = args[0]
    directory = getcachedir(*args[1:])
    path = os.path.join(directory, filename)
    return path

def getcachecontents(*subdirs):
    directory = getcachedir(*subdirs)
    contents = os.listdir(directory)
    return contents

