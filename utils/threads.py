import threading


class StoppableThread(threading.Thread):
    def __init__(self, fn):
        super().__init__()
        self.__shutdown = False
        self.__fn = fn

    def run(self) -> None:
        if self.__shutdown:
            raise Exception("This thread has been shut down")
        self.__fn(self)

    def stop(self) -> None:
        self.__shutdown = True

    def shutdown_requested(self):
        return self.__shutdown

    def join(self, timeout: float | None = None) -> None:
        return super().join(timeout)
