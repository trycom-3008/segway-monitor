"""One asyncio thread for all radio work; Tk is updated only on its thread."""

import asyncio
import threading

from .backend import BluetoothService


class AsyncWorker:
    def __init__(self, emit):
        self.emit = emit
        self.loop = asyncio.new_event_loop()
        self.service = BluetoothService(emit)
        self.task = None
        self.closing = False
        self.thread = threading.Thread(target=self._run, name="Segway-Bluetooth", daemon=True)
        self.thread.start()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        finally:
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            if pending:
                self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    def submit(self, operation):
        if self.closing:
            return

        async def execute():
            self.task = asyncio.current_task()
            try:
                return await self.service.guarded(operation(self.service))
            finally:
                self.task = None
                self.emit("done", None)

        asyncio.run_coroutine_threadsafe(execute(), self.loop)

    def cancel(self):
        def do_cancel():
            if self.task is not None:
                self.task.cancel()
        self.loop.call_soon_threadsafe(do_cancel)

    def shutdown(self):
        if self.closing:
            return
        self.closing = True

        async def close():
            task = self.task
            if task is not None:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            self.loop.call_soon(self.loop.stop)

        asyncio.run_coroutine_threadsafe(close(), self.loop)
