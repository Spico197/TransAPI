import time
import json
import urllib3
import traceback
from bdb import BdbQuit
from pathlib import Path

import click
from omegaconf import OmegaConf
from loguru import logger
from tqdm import tqdm

import transkit.utils
import transkit.translator


def backforth_translate(translator, instance, time_interval=0.5, max_retries=10):
    """
    backforth translation with error handling
    """
    sent = None
    for _ in range(max_retries):
        time.sleep(time_interval)
        try:
            sent = translator.backforth_translate(
                instance['sentence'], instance['head'], instance['tail'],
                tokens=instance['original_info']['token'],
                head_pos=instance['original_info']['head_pos'],
                tail_pos=instance['original_info']['tail_pos'],
            )
            if sent:
                sent = sent.lower()
                break
        except (OSError, json.JSONDecodeError, ConnectionError, KeyError, \
                urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError):
            err = traceback.format_exc().replace('\n', '\t')
            logger.error(f"{err}\n")
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except BdbQuit:
            raise BdbQuit
        except Exception:
            err = traceback.format_exc().replace('\n', '\t')
            logger.error(f"{err}\n")
            sent = None
            break
    return sent


@click.command()
@click.option('-c', '--config-filepath', required=True, type=click.Path(exists=True))
def main(config_filepath):
    config = OmegaConf.load(config_filepath)
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.add(config.log_path)
    logger.info(f"Config filepath: {config_filepath}")
    logger.info(config)

    data_utils = getattr(transkit.utils, config.data_utils)()
    translator = getattr(transkit.translator, config.translator)(
        config.trans_type,
        dict(config[config.trans_type]),
        time_interval=config.time_interval,
    )

    data_dir = Path(config.data_dir)
    for data_filepath in config.data_files:
        data_path = data_dir.joinpath(data_filepath)
        data = data_utils.load_data(data_path)

        err_path = output_dir.joinpath(data_filepath + '.err')
        err_fh = err_path.open('wt', encoding='utf-8')
        if config.start_from == 1:
            write_mode = 'wt'
        else:
            write_mode = 'a'
        translated_path = output_dir.joinpath(data_filepath + '.translated')
        output_fh = translated_path.open(write_mode, encoding='utf-8')

        pbar = tqdm(data, ascii=True, ncols=80)
        for idx, ins in enumerate(pbar, start=1):
            if idx < config.start_from:
                continue

            translated = backforth_translate(
                translator, ins,
                time_interval=config.time_interval,
                max_retries=config.max_retries
            )

            if translated is None:
                err_fh.write(f"{idx}, {ins}\n")
                err_fh.flush()
            else:
                ins.update({
                    "translated": {
                        f"{config.translator}.{config.trans_type}": translated
                    }
                })
                output_fh.write(f'{json.dumps(ins)}\n')
                output_fh.flush()

        err_fh.close()
        output_fh.close()


if __name__ == "__main__":
    main()
