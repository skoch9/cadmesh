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
from tqdm.auto import tqdm
from pathlib import Path
import multiprocessing
import functools
import gc
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from ..core.step_processor import StepProcessor

@contextlib.contextmanager
# def tqdm_joblib(tqdm_object):
#     """Context manager to patch joblib to report into tqdm progress bar given as argument"""
#     class TqdmBatchCompletionCallback(joblib.parallel.BatchCompletionCallBack):
#         def __init__(self, *args, **kwargs):
#             super().__init__(*args, **kwargs)
#
#         def __call__(self, *args, **kwargs):
#             tqdm_object.update(n=self.batch_size)
#             return super().__call__(*args, **kwargs)
#
#     old_batch_callback = joblib.parallel.BatchCompletionCallBack
#     joblib.parallel.BatchCompletionCallBack = TqdmBatchCompletionCallback
#     try:
#         yield tqdm_object
#     finally:
#         joblib.parallel.BatchCompletionCallBack = old_batch_callback
#         tqdm_object.close()




# def with_timeout(timeout):
#     def decorator(decorated):
#         @functools.wraps(decorated)
#         def inner(*args, **kwargs):
#             pool = multiprocessing.pool.ThreadPool(1)
#             async_result = pool.apply_async(decorated, args, kwargs)
#             try:
#                 return async_result.get(timeout)
#             except multiprocessing.TimeoutError:
#                 return False
#         return inner
#     return decorator
#
#
# @with_timeout(120.0)
# def process_single_step(sf, output_dir, log_dir, produce_meshes=True):
#     if produce_meshes:
#         sp = StepProcessor(sf, Path(output_dir), Path(log_dir))
#     else:
#         sp = StepProcessor(sf, Path(output_dir), Path(log_dir), mesh_builder=None)
#     sp.load_step_file()
#     sp.process_parts()
#     return True
#
#
# def process_step_folder(data_path="data/simple", output_path="data/results_simple", log_path="data/log_simple", file_pattern="*/*.step", file_range=[0, -1]):
#     data_dir = Path(data_path)
#     output_dir = Path(output_path)
#     log_dir = Path(log_path)
#
#     step_files = sorted(data_dir.glob(file_pattern))
#     print(step_files)
#     if file_range[1] == -1:
#         step_files = step_files[file_range[0]:]
#     else:
#         step_files = step_files[file_range[0]:file_range[1]]
#
#     with tqdm_joblib(tqdm(desc="Processing step files", total=len(step_files))) as progress_bar:
#         results = Parallel(n_jobs=4)(delayed(process_single_step)(sf, output_dir, log_dir) for sf in step_files)
#
#     return results

# def with_timeout(timeout):
#     def decorator(decorated):
#         @functools.wraps(decorated)
#         def inner(*args, **kwargs):
#             pool = multiprocessing.pool.ThreadPool(1)
#             async_result = pool.apply_async(decorated, args, kwargs)
#             try:
#                 return async_result.get(timeout)
#             except multiprocessing.TimeoutError:
#                 return False
#
#         return inner
#
#     return decorator
#
#
# @with_timeout(120.0)
# def process_single_file(sf, output_dir, log_dir, produce_meshes=True):
#     if produce_meshes:
#         sp = StepProcessor(sf, Path(output_dir), Path(log_dir))
#     else:
#         sp = StepProcessor(sf, Path(output_dir), Path(log_dir), mesh_builder=None)
#     sp.load_step_file()
#     sp.process_parts()
#     return True
#
#
# def process_batch(batch_files, output_dir, log_dir):
#     batch_results = []
#     failed_files = []
#     for sf in batch_files:
#         try:
#             result = process_single_file(sf, output_dir, log_dir)
#             batch_results.append(result)
#         except Exception as e:
#             failed_files.append(str(sf))
#             print(f"Error processing file: {sf}")
#             print(f"Error message: {str(e)}")
#
#     return batch_results, failed_files
#
#
# def process_step_folder(data_path="new_format", output_path="converted", log_path="data/log_new_format",
#                         file_pattern="*.step", file_range=[0, -1], batch_size=1000):
#     data_dir = Path(data_path)
#     output_dir = Path(output_path)
#     log_dir = Path(log_path)
#
#     step_files = sorted(data_dir.glob(file_pattern))
#     if file_range[1] == -1:
#         step_files = step_files[file_range[0]:]
#     else:
#         step_files = step_files[file_range[0]:file_range[1]]
#
#     num_files = len(step_files)
#
#     with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
#         progress_bar = tqdm(total=num_files, desc="Processing step files")
#
#         futures = []
#         for i in range(0, num_files, batch_size):
#             batch_files = step_files[i:i + batch_size]
#             future = executor.submit(process_batch, batch_files, output_dir, log_dir)
#             futures.append(future)
#
#         failed_files = []
#         for future in futures:
#             batch_results, batch_failed_files = future.result()
#             progress_bar.update(len(batch_results))
#             failed_files.extend(batch_failed_files)
#
#         progress_bar.close()
#
#     return num_files, failed_files
# def with_timeout(timeout):
#     def decorator(decorated):
#         @functools.wraps(decorated)
#         def inner(*args, **kwargs):
#             return joblib.timeouts.time_limit(timeout)(decorated)(*args, **kwargs)
#
#         return inner
#
#     return decorator
#
#
# @with_timeout(120.0)
# def process_single_file(sf, output_dir, log_dir, produce_meshes=True):
#     try:
#         if produce_meshes:
#             sp = StepProcessor(sf, Path(output_dir), Path(log_dir))
#         else:
#             sp = StepProcessor(sf, Path(output_dir), Path(log_dir), mesh_builder=None)
#         sp.load_step_file()
#         sp.process_parts()
#         return True
#     except Exception as e:
#         print(f"Error processing file {sf}: {e}")
#         return False
#
#
# def process_step_folder(data_path="new_format", output_path="converted", log_path="data/log_new_format",
#                         file_pattern="*.step", file_range=[0, -1], batch_size=1000):
#     data_dir = Path(data_path)
#     output_dir = Path(output_path)
#     log_dir = Path(log_path)
#
#     step_files = sorted(data_dir.glob(file_pattern))
#     if file_range[1] == -1:
#         step_files = step_files[file_range[0]:]
#     else:
#         step_files = step_files[file_range[0]:file_range[1]]
#
#     num_files = len(step_files)
#     num_batches = (num_files + batch_size - 1) // batch_size
#
#     failed_files = []
#
#     with tqdm(total=num_files, desc="Processing step files") as progress_bar:
#         for i in range(0, num_files, batch_size):
#             batch_files = step_files[i:i + batch_size]
#             results = joblib.Parallel(n_jobs=-1, backend="threading")(
#                 joblib.delayed(process_single_file)(sf, output_dir, log_dir) for sf in batch_files)
#             for sf, result in zip(batch_files, results):
#                 if result:
#                     progress_bar.update(1)
#                 else:
#                     failed_files.append(sf)
#
#     print(f"Number of failed files: {len(failed_files)}")
#
#     return num_files, failed_files


# def process_single_step(sf, output_dir, log_dir, produce_meshes=True):
#     if produce_meshes:
#         sp = StepProcessor(sf, Path(output_dir), Path(log_dir))
#     else:
#         sp = StepProcessor(sf, Path(output_dir), Path(log_dir), mesh_builder=None)
#     sp.load_step_file()
#     sp.process_parts()
#     return True
#
# def process_step_file(sf_path, output_dir, log_dir):
#     try:
#         return process_single_step(str(sf_path), str(output_dir), str(log_dir))
#     except Exception as e:
#         print(f"Error processing {sf_path}: {e}")
#         return False
#
# def process_step_folder(data_path="data/simple", output_path="data/results_simple", log_path="data/log_simple", file_pattern="*/*.step", file_range=[0, -1]):
#     data_dir = Path(data_path)
#     output_dir = Path(output_path)
#     log_dir = Path(log_path)
#
#     step_files = sorted(data_dir.glob(file_pattern))
#     print(step_files)
#     if file_range[1] == -1:
#         step_files = step_files[file_range[0]:]
#     else:
#         step_files = step_files[file_range[0]:file_range[1]]
#
#     num_processes = multiprocessing.cpu_count()
#     progress_bar = tqdm(total=len(step_files), desc="Processing step files")
#
#     with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
#         results = list(executor.map(partial(process_step_file, output_dir=output_dir, log_dir=log_dir), step_files))
#         progress_bar.update(len(step_files))
#
#     progress_bar.close()
#     return results

#New
# def tqdm_joblib(tqdm_object):
#     """Context manager to patch joblib to report into tqdm progress bar given as argument"""
#     class TqdmBatchCompletionCallback(parallel_backend.BatchCompletionCallBack):
#         def __init__(self, *args, **kwargs):
#             super().__init__(*args, **kwargs)
#
#         def __call__(self, *args, **kwargs):
#             tqdm_object.update(n=self.batch_size)
#             return super().__call__(*args, **kwargs)
#
#     old_batch_callback = parallel_backend.BatchCompletionCallBack
#     parallel_backend.BatchCompletionCallBack = TqdmBatchCompletionCallback
#     try:
#         yield tqdm_object
#     finally:
#         parallel_backend.BatchCompletionCallBack = old_batch_callback
#         tqdm_object.close()
#
# def with_timeout(timeout):
#     def decorator(decorated):
#         @functools.wraps(decorated)
#         def inner(*args, **kwargs):
#             pool = multiprocessing.pool.ThreadPool(1)
#             async_result = pool.apply_async(decorated, args, kwargs)
#             try:
#                 return async_result.get(timeout)
#             except multiprocessing.TimeoutError:
#                 return False
#         return inner
#     return decorator
#
# @with_timeout(120.0)
# def process_single_step(sf, output_dir, log_dir, produce_meshes=True):
#     if produce_meshes:
#         sp = StepProcessor(sf, Path(output_dir), Path(log_dir))
#     else:
#         sp = StepProcessor(sf, Path(output_dir), Path(log_dir), mesh_builder=None)
#     sp.load_step_file()
#     sp.process_parts()
#     return True
#
# def process_step_folder(data_path="data/simple", output_path="data/results_simple", log_path="data/log_simple", file_pattern="*/*.step", file_range=[0, -1], batch_size=50):
#     data_dir = Path(data_path)
#     output_dir = Path(output_path)
#     log_dir = Path(log_path)
#
#     step_files = sorted(data_dir.glob(file_pattern))
#     print(step_files)
#     if file_range[1] == -1:
#         step_files = step_files[file_range[0]:]
#     else:
#         step_files = step_files[file_range[0]:file_range[1]]
#
#     num_files = len(step_files)
#     num_batches = (num_files + batch_size - 1) // batch_size
#
#     with tqdm_joblib(tqdm(desc="Processing step files", total=num_files)) as progress_bar:
#         with parallel_backend("multiprocessing"):  # Specify multiprocessing backend
#             results = []
#             for batch_idx in range(num_batches):
#                 start_idx = batch_idx * batch_size
#                 end_idx = min(start_idx + batch_size, num_files)
#                 batch_files = step_files[start_idx:end_idx]
#
#                 batch_results = Parallel(n_jobs=4)(delayed(process_single_step)(sf, output_dir, log_dir) for sf in batch_files)
#                 results.extend(batch_results)
#                 progress_bar.update(n=len(batch_files))
#
#     return results


#New 1
# def tqdm_joblib(tqdm_object):
#     """Context manager to patch joblib to report into tqdm progress bar given as argument"""
#     class TqdmBatchCompletionCallback(parallel_backend.BatchCompletionCallBack):
#         def __init__(self, *args, **kwargs):
#             super().__init__(*args, **kwargs)
#
#         def __call__(self, *args, **kwargs):
#             tqdm_object.update(n=self.batch_size)
#             return super().__call__(*args, **kwargs)
#
#     old_batch_callback = parallel_backend.BatchCompletionCallBack
#     parallel_backend.BatchCompletionCallBack = TqdmBatchCompletionCallback
#     try:
#         yield tqdm_object
#     finally:
#         parallel_backend.BatchCompletionCallBack = old_batch_callback
#         tqdm_object.close()
#
# def with_timeout(timeout):
#     def decorator(decorated):
#         @functools.wraps(decorated)
#         def inner(*args, **kwargs):
#             pool = multiprocessing.pool.ThreadPool(1)
#             async_result = pool.apply_async(decorated, args, kwargs)
#             try:
#                 return async_result.get(timeout)
#             except multiprocessing.TimeoutError:
#                 return False
#         return inner
#     return decorator
#
# @with_timeout(120.0)
# def process_single_step(sf, output_dir, log_dir, produce_meshes=True):
#     if produce_meshes:
#         sp = StepProcessor(sf, Path(output_dir), Path(log_dir))
#     else:
#         sp = StepProcessor(sf, Path(output_dir), Path(log_dir), mesh_builder=None)
#     sp.load_step_file()
#     sp.process_parts()
#     return True
#
# def process_step_folder(data_path="data/simple", output_path="data/results_simple", log_path="data/log_simple", file_pattern="*/*.step", file_range=[0, -1], batch_size=50):
#     data_dir = Path(data_path)
#     output_dir = Path(output_path)
#     log_dir = Path(log_path)
#
#     step_files = sorted(data_dir.glob(file_pattern))
#     print(step_files)
#     if file_range[1] == -1:
#         step_files = step_files[file_range[0]:]
#     else:
#         step_files = step_files[file_range[0]:file_range[1]]
#
#     num_files = len(step_files)
#     num_batches = (num_files + batch_size - 1) // batch_size
#
#     with tqdm_joblib(tqdm(desc="Processing step files", total=num_files)) as progress_bar:
#         with parallel_backend("multiprocessing"):  # Specify multiprocessing backend
#             results = []
#             for batch_idx in range(num_batches):
#                 start_idx = batch_idx * batch_size
#                 end_idx = min(start_idx + batch_size, num_files)
#                 batch_files = step_files[start_idx:end_idx]
#
#                 batch_results = Parallel(n_jobs=4)(delayed(process_single_step)(sf, output_dir, log_dir) for sf in batch_files)
#                 results.extend(batch_results)
#                 progress_bar.update(n=len(batch_files))
#
#     return results

def tqdm_joblib(tqdm_object):
    """Context manager to patch joblib to report into tqdm progress bar given as argument"""
    class TqdmBatchCompletionCallback(multiprocessing.pool.BatchCompletionCallBack):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def __call__(self, *args, **kwargs):
            tqdm_object.update(n=self.batch_size)
            return super().__call__(*args, **kwargs)

    old_batch_callback = multiprocessing.pool.BatchCompletionCallBack
    multiprocessing.pool.BatchCompletionCallBack = TqdmBatchCompletionCallback
    try:
        yield tqdm_object
    finally:
        multiprocessing.pool.BatchCompletionCallBack = old_batch_callback
        tqdm_object.close()

def with_timeout(timeout):
    def decorator(decorated):
        @functools.wraps(decorated)
        def inner(*args, **kwargs):
            pool = multiprocessing.pool.ThreadPool(1)
            async_result = pool.apply_async(decorated, args, kwargs)
            try:
                return async_result.get(timeout)
            except multiprocessing.TimeoutError:
                return False
        return inner
    return decorator

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
        # Log the error and return False
        print(f"Exception occurred while processing {sf}: {str(e)}")
        traceback.print_exc()  # print the full traceback
        return False


from concurrent.futures import ThreadPoolExecutor

def process_step_folder(data_path="data/simple", output_path="data/results_simple",
                        log_path="data/log_simple", file_pattern="*/*.step", file_range=[0, -1],
                        batch_size=50, debug=True, num_workers=4):  # Added num_workers parameter

    data_dir = Path(data_path)
    output_dir = Path(output_path)
    log_dir = Path(log_path)

    step_files = sorted(data_dir.glob(file_pattern))
    if debug:
        print(step_files)
    if file_range[1] == -1:
        step_files = step_files[file_range[0]:]
    else:
        step_files = step_files[file_range[0]:file_range[1]]

    num_files = len(step_files)

    progress_bar = tqdm(total=num_files, desc="Processing step files")

    results = []
    failed_files = []  # list to store failed file paths

    # Use ThreadPoolExecutor to execute function in parallel
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_sf = {executor.submit(process_single_step, sf, output_dir, log_dir): sf for sf in step_files}
        for future in concurrent.futures.as_completed(future_to_sf):
            sf = future_to_sf[future]
            try:
                success = future.result()
                results.append(success)
                if not success:
                    failed_files.append(sf)  # add failed file to the list
            except Exception as exc:
                print('%r generated an exception: %s' % (sf, exc))
            finally:
                progress_bar.update()
                gc.collect()  # Manually trigger garbage collection

    progress_bar.close()
    return results, failed_files  # return failed files along with results

