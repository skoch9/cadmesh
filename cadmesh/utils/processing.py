from tqdm.auto import tqdm
import glob
from pathlib import Path
import os
import contextlib
import joblib
import time
import multiprocessing
import functools
from joblib import Parallel, delayed


from ..core.step_processor import StepProcessor



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


def with_timeout(timeout):
    def decorator(decorated):
        @functools.wraps(decorated)
        def inner(*args, **kwargs):
            pool = multiprocessing.pool.ThreadPool(1)
            async_result = pool.apply_async(decorated, args, kwargs)
            try:
                async_result.get(timeout)
            except multiprocessing.TimeoutError:
                logging.info(f'Task timed out for args: {args}, kwargs: {kwargs}')  # log the time out
                return

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
    except multiprocessing.TimeoutError:
        print("Timeout error")
        return False
    except Exception as e:
        print("Exception error")
        print(e)
        return False


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def process_step_folder(data_path="data/simple", output_path="data/results_simple", log_path="data/log_simple",
                        file_pattern="*/*.step", file_range=[0, -1], chunk_size=10):
    data_dir = Path(data_path)
    output_dir = Path(output_path)
    log_dir = Path(log_path)

    step_files = sorted(data_dir.glob(file_pattern))
    if file_range[1] == -1:
        step_files = step_files[file_range[0]:]
    else:
        step_files = step_files[file_range[0]:file_range[1]]

    step_file_chunks = list(chunks(step_files, chunk_size))

    for i, step_file_chunk in enumerate(step_file_chunks):
        # logging.info(f'Starting chunk {i + 1}/{len(step_file_chunks)}')
        with tqdm_joblib(tqdm(desc=f"Processing step files chunk {i + 1}/{len(step_file_chunks)}",
                              total=len(step_file_chunk))) as progress_bar:
            Parallel(n_jobs=4)(delayed(process_single_step)(sf, output_dir, log_dir) for sf in step_file_chunk)