""" This script is used for downloading large numbers of books from the SACHA interface. It makes use of the multiprocessing
library to speed up the process. All cores but one are used to download in parallel.
"""

import csv
import json
import logging
import requests
import time
import pathlib
from multiprocessing import Pool, cpu_count

logging.basicConfig(handlers=[logging.FileHandler('sacha_multi.log'),
                              logging.StreamHandler()],
                    # level=logging.DEBUG,
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%d/%m/%Y %I:%M:%S %p')


def download(barcode):
    start_time = time.time()
    logging.info('%s - now requesting.' % barcode)
    r = requests.get('https://iiif.onb.ac.at/presentation/ABO/%s/manifest/' % barcode)

    if r.status_code != 200:
        logging.critical('%s - requesting produced a HTTP %s' % (barcode, r.status_code))
    elif r.status_code == 200:
        manifest = json.loads(r.text)

        # store the meta data
        with open('%s/metadata/%s.meta' % (target_dir, barcode[1:]), 'w', encoding='utf-8') as metadata:
            json.dump(manifest['metadata'], fp=metadata, sort_keys=True, indent=4)

        # store content
        with open('%s/books/%s.txt' % (target_dir, barcode[1:]), 'w', encoding='utf-8') as fulltext:
            # iterate the manifest
            pages = len(manifest['sequences'][0]['canvases'])
            # for canvas in tqdm(manifest['sequences'][0]['canvases']):
            for canvas in manifest['sequences'][0]['canvases']:
                content_txt = canvas['otherContent'][0]['resources'][0]['resource']['@id']
                if content_txt[-3:] == 'txt':
                    # canvas_text = requests.get(content)
                    # quick fix for ONB switch to https, as this is not changed in the manifests yet
                    canvas_text = requests.get('https' + content_txt[4:])
                    status = canvas_text.status_code
                    if status == 200:
                        pathlib.Path('%s/books/%s' % (target_dir, barcode[1:])).mkdir(exist_ok=True)
                        with open('%s/books/%s/%s' % (target_dir, barcode[1:], content_txt.split("/")[-1]), 'wb') as f:
                              f.write(canvas_text.content)
                        pass
                    else:
                        logging.critical('%s - requesting produced a HTTP %s' % (content_txt, status))
                    fulltext.write(canvas_text.text)
                    fulltext.write('\n')
                content2 = canvas['otherContent'][0]['resources'][1]['resource']['@id']
                if content2[-4:] == 'html':
                    canvas_text = requests.get('https' + content2[4:])
                    status = canvas_text.status_code
                    if status == 200:
                        pathlib.Path('%s/books/%s' % (target_dir, barcode[1:])).mkdir(exist_ok=True)
                        with open('%s/books/%s/%s' % (target_dir, barcode[1:], content2.split("/")[-1]), 'wb') as f:
                            f.write(canvas_text.content)
                        pass
                    else:
                        logging.critical('%s - requesting produced a HTTP %s' % (content2, status))
                # TODO: change according to the current system!
                # Aim for a maximum of 400 requests per second, depending on the number of cores available.
                time.sleep(0.01)

            duration = time.time() - start_time
            average = duration / pages
            logging.info('%s - successfully stored to disk. Time needed: %.2fs for %d pages (averaging %.2f seconds per page).'
                         % (barcode, duration, pages, average))
    time.sleep(0.01)


if __name__ == '__main__':

    def callback_error(result):
        logging.error(result)

    # target_dir = '../../tl-classification/data/travelogues-groundtruth/sacha_full/16th_full'
    # csv_file = '../../tl-classification/data/travelogues-groundtruth/sacha_full/15-16-SACHA.csv'

    # target_dir = '../../tl-classification/data/travelogues-groundtruth/sacha_full/17th_full'
    # csv_file = '../../tl-classification/data/travelogues-groundtruth/sacha_full/16-17-SACHA.csv'

    # target_dir = '../../tl-classification/data/travelogues-groundtruth/sacha_full/18th_full'
    # csv_file = '../../tl-classification/data/travelogues-groundtruth/sacha_full/17-18-SACHA.csv'

    # target_dir = '../../tl-classification/data/travelogues-groundtruth/sacha_full/19th_full'
    # csv_file = '../../tl-classification/data/travelogues-groundtruth/sacha_full/18-1877-SACHA.csv'

    target_dir = '.'

    pool = Pool(processes=cpu_count()-1)  # uses all available cores minus 1 (to prevent locking the system)

    # with open(csv_file) as csvfile:
    #     # read .csv content
    #     csv_reader = csv.DictReader(csvfile, delimiter=',')
    #
    #     for row in csv_reader:
    #         barcode = str(row['Strichcode'])
    #         pool.apply_async(download, args=(barcode,))

    with open('analyzed_min.csv') as f:
        barcode_list = f.read().splitlines()

    for barcode in barcode_list:
        pool.apply_async(download, args=(barcode,), error_callback=callback_error)

    pool.close()
    pool.join()
