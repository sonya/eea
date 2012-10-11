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

