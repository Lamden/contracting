import asyncio
import zmq
import json


class AsyncInbox:
    def __init__(self, port: int, ctx: zmq.Context, linger=2000, poll_timeout=2000):
        self.port = port

        self.address = 'tcp://*:{}'.format(port)

        self.ctx = ctx

        self.socket = None

        self.linger = linger
        self.poll_timeout = poll_timeout

        self.running = False

    async def serve(self):
        self.setup_socket()

        self.running = True

        while self.running:
            try:
                event = await self.socket.poll(timeout=self.poll_timeout, flags=zmq.POLLIN)
                if event:
                    _id = await self.socket.recv()
                    msg = await self.socket.recv()
                    asyncio.ensure_future(self.handle_msg(_id, msg))

            except zmq.error.ZMQError:
                self.socket.close()
                self.setup_socket()

        self.socket.close()

    async def handle_msg(self, _id, msg):
        asyncio.ensure_future(self.return_msg(_id, msg))

    async def return_msg(self, _id, msg):
        sent = False
        while not sent:
            try:
                await self.socket.send_multipart([_id, msg])
                sent = True
            except zmq.error.ZMQError:
                self.socket.close()
                self.setup_socket()

    def setup_socket(self):
        self.socket = self.ctx.socket(zmq.ROUTER)
        self.socket.setsockopt(zmq.LINGER, self.linger)
        self.socket.bind(self.address)

    def stop(self):
        self.running = False
