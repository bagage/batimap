import time


def timeit(method):
    """
    Compute the time a given method takes to compute its result
    Add @timeit annotation on method to investigate, for instance:

    @timeit
    def my_function():
        ...

    :param method: function to benchmark
    :return: time method took to compute
    """

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if "log_time" in kw:
            name = kw.get("log_name", method.__name__.upper())
            kw["log_time"][name] = int((te - ts) * 1000)
        else:
            print("%r  %2.2f ms" % (method.__name__, (te - ts) * 1000))
        return result

    return timed
