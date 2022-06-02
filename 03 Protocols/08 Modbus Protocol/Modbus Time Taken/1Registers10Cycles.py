#!/usr/bin/env python3
# pylint: disable=missing-type-doc
"""Pymodbus Performance Example.

The following is an quick performance check of the synchronous
modbus client.
"""
# --------------------------------------------------------------------------- #
# import the necessary modules
# --------------------------------------------------------------------------- #
import logging
import os
from threading import Lock, Thread as tWorker
from concurrent.futures import ThreadPoolExecutor as eWorker, as_completed
from time import time
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from struct import unpack

try:
    from multiprocessing import Process as mWorker, log_to_stderr
except ImportError:
    import logging

    logging.basicConfig()
    log_to_stderr = logging.getLogger

# --------------------------------------------------------------------------- #
# choose between threads or processes
# --------------------------------------------------------------------------- #

# from multiprocessing import Process as Worker
from threading import Thread as Worker

_thread_lock = Lock()
# --------------------------------------------------------------------------- #
# initialize the test
# --------------------------------------------------------------------------- #
# Modify the parameters below to control how we are testing the client:
#
# * workers - the number of workers to use at once
# * cycles  - the total number of requests to send
# * host    - the host to send the requests to
# --------------------------------------------------------------------------- #
workers = 1  # pylint: disable=invalid-name
cycles = 10  # pylint: disable=invalid-name
host = "192.168.0.104"  # pylint: disable=invalid-name


def validator(instance):
    if not instance.isError():
        '''.isError() implemented in pymodbus 1.4.0 and above.'''
        decoder = BinaryPayloadDecoder.fromRegisters(
            instance.registers,
            byteorder=Endian.Big, wordorder=Endian.Little
        )
        print(instance.registers)
        # return float('{0:.2f}'.format(decoder.decode_32bit_float()))
        return decoder

    else:
        # Error handling.
        print("The register does not exist, Try again.")
        return None


# --------------------------------------------------------------------------- #
# perform the test
# --------------------------------------------------------------------------- #
# This test is written such that it can be used by many threads of processes,
# although it should be noted that there are performance penalties
# associated with each strategy.
# --------------------------------------------------------------------------- #
def single_client_test(host, cycles):
    """Perform a single threaded test of a synchronous client against the specified host

    :param host: The host to connect to
    :param cycles: The number of iterations to perform
    """
    logger = log_to_stderr()
    logger.setLevel(logging.WARNING)
    logger.debug("starting worker: %d" % os.getpid())

    try:
        count = 0
        client = ModbusTcpClient(host, port=10502)
        fp = open("test_1k.txt", "w")
        while count < cycles:
            start = time()
            request = client.read_holding_registers(1, 1, unit=1)
            # request = client.read_holding_registers(126, 125, unit=1)
            # request = client.read_holding_registers(252, 125, unit=1)
            # request = client.read_holding_registers(378, 125, unit=1)
            # request = client.read_holding_registers(504, 125, unit=1)
            # request = client.read_holding_registers(630, 125, unit=1)
            # request = client.read_holding_registers(756, 125, unit=1)
            # request = client.read_holding_registers(882, 125, unit=1)

            data = validator(request)
            print(data)
            count += 1
            stop = time()
            fp.write(str(stop - start))
            fp.write("/n")
    except:
        logger.exception("failed to run test successfully")
    logger.debug("finished worker: %d" % os.getpid())


def multiprocessing_test(fn, args):
    """Multiprocessing test."""
    from multiprocessing import Process as Worker
    start = time()
    procs = [mWorker(target=fn, args=args)
             for _ in range(workers)]

    any(p.start() for p in procs)  # start the workers
    any(p.join() for p in procs)  # wait for the workers to finish
    return start


def thread_test(fn, args):
    """Thread test."""
    from threading import Thread as Worker
    start = time()
    procs = [tWorker(target=fn, args=args)
             for _ in range(workers)]

    any(p.start() for p in procs)  # start the workers
    any(p.join() for p in procs)  # wait for the workers to finish
    return start


def thread_pool_exe_test(fn, args):
    """Thread pool exe."""
    from concurrent.futures import ThreadPoolExecutor as Worker
    from concurrent.futures import as_completed
    start = time()
    with eWorker(max_workers=workers, thread_name_prefix="Perform") as exe:
        futures = {exe.submit(fn, args): job for job in range(workers)}
        for future in as_completed(futures):
            future.result()
    return start


# --------------------------------------------------------------------------- #
# run our test and check results
# --------------------------------------------------------------------------- #
# We shard the total number of requests to perform between the number of
# threads that was specified. We then start all the threads and block on
# them to finish. This may need to switch to another mechanism to signal
# finished as the process/thread start up/shut down may skew the test a bit.

# RTU 32 requests/second @9600
# TCP 31430 requests/second

# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    args = (host, int(cycles * 1.0 / workers))
    # with Worker(max_workers=workers, thread_name_prefix="Perform") as exe:
    #     futures = {exe.submit(single_client_test, *args): job for job in range(workers)}
    #     for future in as_completed(futures):
    #         data = future.result()
    # for _ in range(workers):
    #    futures.append(Worker.submit(single_client_test, args=args))
    # procs = [Worker(target=single_client_test, args=args)
    #          for _ in range(workers)]

    # any(p.start() for p in procs)   # start the workers
    # any(p.join() for p in procs)   # wait for the workers to finish
    # start = multiprocessing_test(single_client_test, args)
    # start = thread_pool_exe_test(single_client_test, args)
    for tester in (multiprocessing_test):
        print(tester.__name__)
        start = tester(single_client_test, args)
        stop = time()
        print("&d requests per second" % ((1.0 * cycles) / (stop - start)))
        print(
            "time taken to complete %s cycle by "
            "%s workers is %s seconds" % (cycles, workers, stop - start)
        )
        print()
