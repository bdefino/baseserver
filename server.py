# Copyright 2018 Bailey Defino
# <https://bdefino.github.io>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
__package__ = "baseserver"

import socket
import thread
import time

import eventhandler
import events
import straddress
import threaded

__doc__ = "server core implementation"

class BaseServer(socket.socket, threaded.Threaded):
    """base class for an interruptible server socket"""
    
    def __init__(self, event_class = events.DummyEvent,
            event_handler_class = eventhandler.DummyHandler,
            address = None, backlog = 100, buflen = 512, nthreads = -1,
            socket_event_function_name = None, timeout = 0.001,
            type = socket.SOCK_DGRAM):
        if not address: # determine the best default address
            address = ("", 1080)

            for addrinfo in socket.getaddrinfo(None, 1080):
                address = addrinfo[4]
                break
        af = socket.AF_INET # determine the address family

        if len(address) == 4:
            af = socket.AF_INET6
        elif not len(address) == 2:
            raise ValueError("unknown address family")
        socket.socket.__init__(self, af, type)
        threaded.Threaded.__init__(self, nthreads)
        self.address = address
        self.alive = threaded.Synchronized(True)
        self.backlog = backlog
        self.buflen = buflen
        self.conn_sleep = conn_sleep
        self.event_handler_class = event_handler_class
        self.sleep = 1.0 / self.backlog # optimal value
        self.bind(self.address)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.settimeout(timeout)
        self.socket_event_function_name = socket_event_function_name
        self.timeout = timeout

    def __call__(self):
        self.listen(self.backlog)
        
        try:
            for event in self:
                self.execute(self.event_handler_class(event).__call__)
        except KeyboardInterrupt:
            self.alive.set(False)
        finally:
            self.shutdown(socket.SHUT_RDWR)
            self.close()

    def next(self):
        """generate events"""
        while 1:
            if not self.alive.get() or not self.socket_event_function_name:
                raise StopIteration()
            
            try:
                return self.event_class(*getattr(self,
                    self.socket_event_function_name))
            except socket.error:
                pass
            time.sleep(self.sleep)

class BaseTCPServer(BaseServer):
    def __init__(self, event_class = events.ConnectionEvent,
            event_handler_class = eventhandler.ConnectionHandler,
            address = None, backlog = 100, buflen = 65536,
            conn_inactive = None, conn_sleep = 0.001, nthreads = -1,
            timeout = 0.001):
        BaseServer.__init__(self, event_class, event_handler_class, address,
            backlog, buflen, nthreads, "accept", timeout)
        self.conn_inactive = conn_inactive # inactivity period before cleanup
        self.conn_sleep = conn_sleep

class BaseUDPServer(BaseServer):
    def __init__(self, event_class = events.DatagramEvent,
            event_handler_class = eventhandler.DatagramHandler, address = None,
            backlog = 100, buflen = 512, nthreads = -1, timeout = 0.001):
        BaseServer.__init__(self, event_class, event_handler_class, address,
            backlog, buflen, nthreads, "recvfrom", timeout)
