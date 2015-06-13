import csv
import logging
import logging.handlers
import threading
import time
import traceback
import requests


formatter = logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s')

logger = logging.getLogger('cso_parser')
logger.setLevel(logging.INFO)
logger.propagate = 0

file_handler = logging.handlers.RotatingFileHandler('cso_log.log', maxBytes=10 * 1024 * 1024, backupCount=2)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


class CsoParser:
    """
    This class runs a thread that gathers Combined Sewer Overflow (CSO) data periodically. It gathers the data from
    http://your.kingcounty.gov/dnrp/library/wastewater/cso/img/cso.csv, then parses the CSV, and returns a formatted
    version of the data.
    """

    csv_url = 'http://your.kingcounty.gov/dnrp/library/wastewater/cso/img/cso.csv'

    def __init__(self, frequency=30 * 60):
        self.frequency = frequency
        self.is_running = False
        self.now_count = 0
        self.recent_count = 0
        self.not_count = 0
        self.not_real_time_count = 0
        self.thread = None
        self.status = 1

    def _get_csv(self):
        logger.info('Retrieving CSV file.')

        # Stream the CSV so we don't eat a bunch of RAM.
        r = requests.get(self.csv_url, stream=True)
        with open('cso.csv', 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()

    def _parse_csv(self):
        """
        CSV Format: [cso identifier],[status code]

        The City CSOs are labeled with their NPDES number while the County CSOs are labeled by name.

        The status code indicates:
        1 = CSO discharging now
        2 = CSO discharged in last 48 hrs
        3 = CSO not discharging
        4 = Real time data not available
        """
        logger.info('Parsing CSV file')
        reader = csv.reader(open('cso.csv', 'r'))
        first_line = True
        now_count = 0
        recent_count = 0
        not_count = 0
        not_real_time_count = 0
        row_count = 0

        for row in reader:
            if not first_line:
                row_count += 1
                cso, status = row

                if status == '1':
                    now_count += 1
                elif status == '2':
                    recent_count += 1
                elif status == '3':
                    not_count += 1
                elif status == '4':
                    not_real_time_count += 1
            else:
                first_line = False

        self.now_count = now_count
        self.recent_count = recent_count
        self.not_count = not_count
        self.not_real_time_count = not_real_time_count

        log_msg = 'Rows: {}, Now Count: {}, Recent Count: {}, No Count: {}, Not Real Time: {}'
        logger.info(log_msg.format(row_count, now_count, recent_count, not_count, not_real_time_count))

    def _run_loop(self):
        while self.is_running:
            try:
                self.status = 1
                self._get_csv()
            except Exception:
                self.status = 0
                logger.exception('Error retrieving CSV!')
                traceback.print_exc()
            else:
                # Only parse the csv if we successfully retrieve it.
                try:
                    self.status = 1
                    self._parse_csv()
                except Exception:
                    self.status = 0
                    logger.exception('Error parsing CSV!')
                    traceback.print_exc()

            time.sleep(self.frequency)

    def start(self):
        logger.info('Starting CsoParser')
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        logger.info('Stopping CsoParser')
        self.is_running = False
        self.thread.join()
        self.thread = None


if __name__ == '__main__':
    c = CsoParser()
    c.csv_url = 'http://localhost:8080/'
    c.start()
    time.sleep(2)
    print(c.now_count, c.recent_count, c.not_count, c.not_real_time_count)
    c.stop()
