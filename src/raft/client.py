from pydoc import cli
import uuid
from socket import socket, AF_INET, SOCK_STREAM, timeout

from raft import config
from raft.messaging import (
    SetValue,
    send_message,
    Message,
    Command,
    recv_message,
    Result,
    NotTheLeader,
    NoOp,
    GetValue,
    DelValue,
    ClientDisconnected)


class NoConnectionError(Exception):
    pass

class DistDict:
    def __init__(self, server_config, mutex, timeout=config.CLIENT_TIMEOUT):
        self.mutex = mutex
        self.server_config = server_config
        self.client_id = uuid.uuid1()
        self.timeout = timeout
        self._cached_sock = None
        self._leader_no = None

    def _connect_server(self, server_no):
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(1)
        s.connect(self.server_config[server_no])
        s.settimeout(self.timeout)
        return s

    def _request_id(self):
        return uuid.uuid1()

    def _find_leader(self):
        for server_no in self.server_config:
            try:
                s = self._connect_server(server_no)
            except OSError:
                continue
            else:
                no_op_msg = Message(
                    sender=self.client_id,
                    recipient=server_no,
                    term=None,
                    content=Command(operation=NoOp(request_id=self._request_id())),
                )
                send_message(s, bytes(no_op_msg))
                response = Message.from_bytes(recv_message(s))

                if isinstance(response.content, Result):
                    return s, response.sender
                elif isinstance(response.content, NotTheLeader):
                    if response.content.leader_id is None:
                        raise NoConnectionError("server didn't know who the leader was")
                    return (
                        self._connect_server(response.content.leader_id),
                        response.content.leader_id,
                    )
        raise NoConnectionError("couldn't connect to any machine in the cluster")

    def send(self, content):
        self.mutex.acquire()
        if client != "": print(client + " lock mutex; sleep(3 sec)")
        time.sleep(3)
        if client != "": print(client + " sleep() finish")
        try:
            message = Message(
                sender=self.client_id,
                recipient=self._leader_no,
                term=None,
                content=content,
            )
            send_message(self._cached_sock, bytes(message))
            resp = Message.from_bytes(recv_message(self._cached_sock))

            print("got response", resp)
            if isinstance(resp.content, NotTheLeader):
                raise ConnectionRefusedError(f"tried to connect to server {self._leader_no} but it was not the leader")

        except (AttributeError, ConnectionRefusedError, ClientDisconnected, timeout):
            print(f"was either connected to a server that wasn't the leader, or got a timeout")
            self._cached_sock, self._leader_no = self._find_leader()
            if client != "": print(client + " unlock mutex")
            self.mutex.release()
            return self.send(content)
        else:
            if client != "": print(client + " unlock mutex")
            self.mutex.release()
            return resp.content.content

    def __setitem__(self, key, value):
        return self.send(
            Command(SetValue(request_id=self._request_id(), key=key, value=value))
        )

    def __getitem__(self, item):
        return self.send(Command(GetValue(request_id=self._request_id(), key=item)))

    def __delitem__(self, key):
        return self.send(Command(DelValue(request_id=self._request_id(), key=key)))

import threading
import time
shared_mutex = threading.Lock()
import asyncio
import random
client = ""
async def task_client1(client1):
    global client
    print("client1: started")
    
    sleep_rand = random.random()
    print("client1: sleep " + str(sleep_rand))
    await asyncio.sleep(sleep_rand)
    client = "client1"
    client1['test_1'] = 'value_1'
    print("client1: client1['test_1'] = 'value_1'")

    sleep_rand = random.random()
    print("client1: sleep " + str(sleep_rand))
    await asyncio.sleep(sleep_rand)
    client = "client1"
    client1['test_2'] = 'value_2'
    print("client1: client1['test_2'] = 'value_2'")

    sleep_rand = random.random()
    print("client1: sleep " + str(sleep_rand))
    await asyncio.sleep(sleep_rand)
    client = "client1"
    client1['test_2'] = client1['test_1']
    print("client1: client1['test_2'] = client1['test_1']")

    sleep_rand = random.random()
    print("client1: sleep " + str(sleep_rand))
    await asyncio.sleep(sleep_rand)
    print("client1: finish")

async def task_clinet2(client2):
    global client
    print("client2: started")

    sleep_rand = random.random()
    print("client2: sleep " + str(sleep_rand))
    await asyncio.sleep(sleep_rand)
    client = "client2"
    client2['test_1'] = 'value_1_1'
    print("client2: client2['test_1'] = 'value_1_1'")

    sleep_rand = random.random()
    print("client2: sleep " + str(sleep_rand))
    await asyncio.sleep(sleep_rand)
    client = "client2"
    client2['test_2_2'] = 'value_2'
    print("client2: client2['test_2_2'] = 'value_2'")

    sleep_rand = random.random()
    print("client2: sleep " + str(sleep_rand))
    await asyncio.sleep(sleep_rand)
    print("client2: finish")


async def main():
    client1 = DistDict(config.SERVERS, shared_mutex)
    client2 = DistDict(config.SERVERS, shared_mutex)
    task1_coroutine = task_client1(client1)
    task2_coroutine = task_clinet2(client2)

    await asyncio.gather(task1_coroutine, task2_coroutine)
    client = "cl"
    print("client1['test_2']")
    print(client1['test_2'])

asyncio.run(main())

