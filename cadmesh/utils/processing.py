from tqdm.auto import tqdm
import contextlib
import joblib
import logging
from pathlib import Path
import multiprocessing
import functools
import os
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
                return async_result.get(timeout), None
            except multiprocessing.TimeoutError:
                return None, "TimeoutError"
        return inner
    return decorator


@with_timeout(60.0)
def process_single_step(sf, output_dir, log_dir, produce_meshes=True):
    try:
        if produce_meshes:
            sp = StepProcessor(sf, Path(output_dir), Path(log_dir))
        else:
            sp = StepProcessor(sf, Path(output_dir), Path(log_dir), mesh_builder=None)
        sp.load_step_file()
        sp.process_parts()
        return sf, None
    except Exception as e:
        return sf, str(e)


def process_step_folder(input_dir, output_dir, log_dir, file_pattern="*.stp", file_range=[0, -1]):
    data_dir = Path(input_dir)
    output_dir = Path(output_dir)
    log_dir = Path(log_dir)

    if not data_dir.exists():
        return [], ['Input directory does not exist']

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    step_files = sorted(data_dir.glob(file_pattern))
    if file_range[1] == -1:
        step_files = step_files[file_range[0]:]
    else:
        step_files = step_files[file_range[0]:file_range[1]]

    success_files = []
    failed_files = []

    with tqdm_joblib(tqdm(desc="Processing step files", total=len(step_files))) as progress_bar:
        results = Parallel(n_jobs=4)(delayed(process_single_step)(sf, output_dir, log_dir) for sf in step_files)

    for sf, error_message in results:
        if error_message is None:
            success_files.append(sf)
        else:
            failed_files.append((sf, error_message))

    return success_files, failed_files


def process_step_files(input_file_list, output_dir, log_dir):
    output_dir = Path(output_dir)
    log_dir = Path(log_dir)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # Read input files from a list in a text file
    with open(input_file_list, 'r') as f:
        input_files = [Path(line.strip()) for line in f]

    success_files = []
    failed_files = []

    with tqdm_joblib(tqdm(desc="Processing step files", total=len(input_files))) as progress_bar:
        results = Parallel(n_jobs=4)(delayed(process_single_step)(sf, output_dir, log_dir) for sf in input_files)

    model_names = []  # this will hold just the model names

    for sf, error_message in results:
        if error_message is None:
            success_files.append(sf)
            model_names.append(sf[0].name)  # append only the name of the file
        else:
            failed_files.append((sf, error_message))

    return success_files, failed_files
