from tqdm.auto import tqdm
import contextlib
import joblib
import logging
from pathlib import Path
import multiprocessing
import functools
from joblib import Parallel, delayed

from ..core.step_processor import StepProcessor
from mpi4py import MPI

@contextlib.contextmanager
def tqdm_joblib(tqdm_object):
    """Context manager to patch joblib to report into tqdm progress bar given as argument"""

    class TqdmBatchCompletionCallback(joblib.parallel.BatchCompletionCallBack):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def __call__(self, *args, **kwargs):
            tqdm_object.update(n=self.batch_size)
            return super().__call__(*args, **kwargs)

    old_batch_callback = joblib.parallel.BatchCompletionCallBack
    joblib.parallel.BatchCompletionCallBack = TqdmBatchCompletionCallback
    try:
        yield tqdm_object
    finally:
        joblib.parallel.BatchCompletionCallBack = old_batch_callback
        tqdm_object.close()

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Configure logging
logging.basicConfig(filename='step_conversion.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def with_timeout(timeout):
    def decorator(decorated):
        @functools.wraps(decorated)
        def inner(*args, **kwargs):
            pool = multiprocessing.Pool(1)
            async_result = pool.apply_async(decorated, args, kwargs)
            try:
                output = async_result.get(timeout)
                return output
            except multiprocessing.TimeoutError:
                logging.error(f'Timeout error for file: {args[0]}')  # Log the time out
                return None
        return inner
    return decorator


@with_timeout(120.0)
def process_single_step(sf, output_dir, log_dir, produce_meshes=True):
    try:
        if produce_meshes:
            sp = StepProcessor(sf, Path(output_dir), Path(log_dir))
        else:
            sp = StepProcessor(sf, Path(output_dir), Path(log_dir), mesh_builder=None)
        sp.load_step_file()
        sp.process_parts()
        return True
    except Exception as e:
        logging.error(f'Exception for file: {sf} Error: {e}')  # Log the exception
        return False


def process_step_folder(data_path="data/simple", output_path="data/results_simple",
                        log_path="data/log_simple", file_pattern="*/*.step",
                        file_range=[0, -1]):

    comm = MPI.COMM_WORLD
    size = comm.Get_size()  # Total number of processes
    rank = comm.Get_rank()  # Rank of this process

    data_dir = Path(data_path)
    output_dir = Path(output_path)
    log_dir = Path(log_path)

    step_files = sorted(data_dir.glob(file_pattern, recursive=True))
    if file_range[1] == -1:
        step_files = step_files[file_range[0]:]
    else:
        step_files = step_files[file_range[0]:file_range[1]]

    # Divide the files among the available ranks
    files_per_rank = len(step_files) // size
    my_files = step_files[rank * files_per_rank:(rank + 1) * files_per_rank]

    for sf in my_files:
        result = process_single_step(sf, output_dir, log_dir)
        if result:
            logging.info(f'Successfully converted file: {sf}')  # Log success
        else:
            logging.error(f'Failed to convert file: {sf}')  # Log failure
