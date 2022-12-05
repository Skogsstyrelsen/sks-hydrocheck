from pathlib import Path, PurePath
from time import time
import logging
import types
import functools
import inspect
from shutil import rmtree

logger = logging.getLogger(__name__)

def timer(func):
    def wrapper(*args, **kwargs):
        start = time()
        res = func(*args, **kwargs)
        elapsed = time() - start
        logger.debug("Exec time for %s: %.2f s", func.__name__, elapsed)
        return res
    return wrapper

class Counter():
    """An instance of this class can be used to keep a shared count between multiple threads"""
    def __init__(self, start=0):
        self.count = start
    def add(self, n=1):
        self.count += n
        return self.count
    def sub(self, n=1):
        self.count -= n
        return self.count

class Output(object):
    def __init__(self, work_dir):
        self.work_dir = PurePath(work_dir)
    def add(self, name, filename):
        filepath = (self.work_dir / filename).as_posix() if filename is not None else None
        setattr(self, name, filepath)

class Cache():
    __defaults = {
        "cache_var":"output"
    }
    instances = []
    def __init__(self, cache_var=None):
        self.cache_var = cache_var if cache_var is not None else Cache.__get_root_arg('cache_var')
        Cache.instances.append(self)

    @staticmethod
    def __get_root_arg(arg_name):
        if Cache.instances:
            root = Cache.instances[0]
            return getattr(root, arg_name)
        else:
            return Cache.__defaults[arg_name]

    def cache_funcs(self, module):
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, types.MethodType):
                spec = inspect.getfullargspec(obj)
                if self.cache_var in spec.args:
                    setattr(module, name, self.cache_handler(obj))

    def cache_handler(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            file_path = Path(kwargs[self.cache_var])
            if file_path.is_file():
                logger.info("Found cached data: %s", file_path)
                return file_path.as_posix()
            return func(*args, **kwargs)
        return wrapper

class WBTProcessingError(Exception):
    """Raised when Whitebox Tools panics"""

def wbt_callback(value):
    if not "%" in value:
        logger.debug(value)
    if 'panicked' in value: # Work-around for tool methods not returning non-zero exit codes
        raise WBTProcessingError

def setup_work_dir(work_dir_path, clean=False):
    work_dir=Path(work_dir_path).resolve()
    if clean:
        for path in work_dir.rglob("*"):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                rmtree(path)
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir
