import os, threading
import redis
from multiprocessing import Lock
from seneca.engine.conflict_resolution import CRContext


class BookKeeper:
    _shared_state = {}
    _lock = Lock()

    @classmethod
    def _get_key(cls) -> str:
        """
        Returns a key unique to this particular thread/process combination.
        :return: The unique thead-process key (as a string)
        """
        key = "{}:{}".format(os.getpid(), threading.get_ident())
        return key

    @classmethod
    def set_info(cls, sbb_idx: int, contract_idx: int, data: CRContext, **kwargs) -> None:
        """
        Sets the info (subblock builder index and contract index) for the current thread.
        """
        key = cls._get_key()
        # print("\nSetting key {} with info sbb_idx: {} and contract_idx: {}".format(key, sbb_idx, contract_idx))  # TODO remove

        with cls._lock:
            cls._shared_state[key] = {'sbb_idx': sbb_idx, 'contract_idx': contract_idx, 'data': data, **kwargs}

    @classmethod
    def get_info(cls) -> dict:
        """
        Returns the info previously set for this specific thread by set_info.
        :return:
        """
        key = cls._get_key()

        with cls._lock:
            assert key in cls._shared_state, "Key {} not found in shared state. Did you call set_info first?"
            return cls._shared_state[key]

    @classmethod
    def has_info(cls) -> bool:
        """
        Checks if bookkeeping info exists for this current process/thread combination
        """
        key = cls._get_key()

        with cls._lock:
            return key in cls._shared_state

    @classmethod
    def del_info(cls) -> None:
        key = cls._get_key()

        with cls._lock:
            assert key in cls._shared_state, "Key {} not found in shared state. Did you call set_info first?"
            del cls._shared_state[key]

