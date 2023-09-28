import os
import sys 
'''
##############################################################################
# Copyright 2023 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

Created on Sep 22, 2023

@author: HWASSMAN
'''

import time
from bridgeLogger import getBridgeLogger
from messages import MSG


class ConfigWatcher(object):
    running = False
    refresh_delay_secs = 1

    # Constructor
    def __init__(self, watch_paths, call_func_on_change=None, *args, **kwargs):
        self._cached_stamp = {}
        self.logger = getBridgeLogger()
        self.paths = watch_paths
        self.filenames = set()
        self.call_func_on_change = call_func_on_change
        self.args = args
        self.kwargs = kwargs


    def update_files_list(self):
        oldfiles = self.filenames.copy()
        for path in self.paths:
            if os.path.isfile(path):
                self.filenames.add(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.endswith(".cfg"):
                            self.filenames.add(os.path.join(root, file))
            else:
                self.logger.trace(MSG['PathNoCfgFiles'].format(path))
        for file in self.filenames.difference(oldfiles):
            self.logger.debug(MSG['FileAddedToWatch'].format(file))


    # Look for changes
    def look(self):
        for filename in self.filenames:
            stamp = os.stat(filename).st_mtime
            if filename not in self._cached_stamp:
                self._cached_stamp[filename] = stamp
            elif stamp != self._cached_stamp[filename]:
                self._cached_stamp[filename] = stamp
                # File has changed, so do something...
                self.logger.info(MSG['FileChanged'].format(filename))
                if self.call_func_on_change is not None:
                    self.call_func_on_change(*self.args, **self.kwargs)

    # Keep watching in a loop        
    def watch(self):
        self.running = True
        self.logger.debug(MSG['StartWatchingFiles'].format(self.paths))
        while self.running: 
            try: 
                # Look for changes
                time.sleep(self.refresh_delay_secs)
                self.update_files_list() 
                self.look() 
            except KeyboardInterrupt: 
                self.logger.details(MSG['StopWatchingFiles'].format(self.paths))
                break 
            except FileNotFoundError as e:
                # Action on file not found
                self.logger.warning(MSG['FileNotFound'].format(e.filename))
                pass
            except Exception as e: 
                self.logger.warning(MSG['StopWatchingFiles'].format(self.paths))
                self.logger.details(MSG['UnhandledError'].format(type(e).__name__))
                break


    # break watching         
    def stop_watch(self):
        self.running = False

