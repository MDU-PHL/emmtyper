"""
Update and make a BLAST DB from a new DB FASTA file
"""

import subprocess
import logging
import datetime
import json
import pathlib
import os
import tempfile
import shutil
import urllib.request
import re

import click

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging


class DBMetadata:
    """
    Store and update the DB Metadata
    """

    def __init__(self, metadata_db):
        self.path = pathlib.Path(metadata_db)
        self.db_folder = self.path.parent
        if self.path.exists():
            with open(self.path) as metad:
                self.metad = json.load(metad)
        else:
            self.metad = {
                "updated_on": f"{datetime.datetime.today():%Y-%m-%d}",
                "host": "ftp.cdc.gov",
                "filename": "/pub/infectious_diseases/biotech/tsemm/alltrimmed.tfa",
                "uploaded_to_server_on": "1970-01-01",
            }
        self.update_on = datetime.datetime.strptime(
            self.metad["updated_on"], "%Y-%m-%d"
        )
        self.uploaded_to_server_on = datetime.datetime.strptime(
            self.metad["uploaded_to_server_on"], "%Y-%m-%d"
        )

    def needs_updating(self, new_date):
        LOGGER.debug(f"Date of new db: {new_date.date()}")
        LOGGER.debug(f"Date of current db: {self.uploaded_to_server_on.date()}")
        LOGGER.debug(
            f"{new_date:%Y-%m-%d} is later than {self.uploaded_to_server_on:%Y-%m-%d}: {new_date.date() > self.uploaded_to_server_on.date()}"
        )
        return new_date.date() > self.uploaded_to_server_on.date()

    def update_info(self, key, value):
        try:
            self.metad[key] = value
        except KeyError as error:
            print(error)
            pass

    def update_metadata_file(self):
        with open(self.path, "w") as metajson:
            json.dump(self.metad, metajson)


def make_db(fasta_file, date):
    '''
    Main function to generate a BLAST DB
    '''
    title = f'"EMM DB created on {date}"'
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        LOGGER.info("Making BLAST DB...")
        LOGGER.debug(f"Working in temp folder {tmpdir}...")
        LOGGER.debug(f"Original FASTA file: {str(fasta_file.absolute())}")
        fasta_name = fasta_file.name
        shutil.copy(str(fasta_file.absolute()), fasta_name)
        cmd = f'makeblastdb -in "{fasta_name}" -dbtype nucl -title {title}'
        LOGGER.info(f"Running command: {cmd}")
        try:
            run_cmd = subprocess.run(cmd, shell=True, check=True)
            dest = str(fasta_file.parent)
            for fn in os.listdir():
                LOGGER.debug(f"Copying {fn} to {dest}")
                shutil.copy(fn, dest)
        except subprocess.CalledProcessError as error:
            LOGGER.exception(error)
            raise

def get_upload_datetime(url):
    info = urllib.request.urlopen(url).info() 
    date_time = re.search("Last-Modified: (.+)", str(info))
    if datetime:
        return datetime.datetime.strptime(date_time.groups()[0], '%a, %d %b %Y %H:%M:%S %Z')

def download_cdc_db(
    db_folder, db_metadata="db_metadata.json"
):
    '''
    Download the CDC DB.
    '''
    db_path = pathlib.Path(db_folder)
    db_metadata = db_path / db_metadata
    db_fasta = db_path / "emm.fna"
    db = DBMetadata(db_metadata)
    
    url = "https://" + db.metad["host"] + db.metad["filename"]

    if url.split("/")[-1] == "trimmed.tfa":
        url = url.replace("trimmed.tfa", "alltrimmed.tfa")

    updated_on = f"{datetime.datetime.today():%Y-%m-%d}"
    modified_time = get_upload_datetime(url)

    urllib.request.urlretrieve(url, db_fasta)
    
    if db.needs_updating(modified_time):
        try:
            if db_fasta.exists():
                make_db(db_fasta, updated_on)
                db.update_info("updated_on", updated_on)
                db.update_info("uploaded_to_server_on", modified_time.strftime("%Y-%m-%d"))
                db.update_metadata_file()
            else:
                raise FileNotFoundError
        except FileNotFoundError as error:
            LOGGER.exception(error)

    else:
        LOGGER.info("EMM DB is up-to-date.")


def get_db_folder():
    """
    Check if EMM_DB is in the os.environ, else return the location of the DB in the package.

    If not writable, make another suggestion in the users /home folder
    """
    db_folder = os.environ.get(
        "EMM_DB", pathlib.Path(__file__).absolute().parent.parent / "db"
    )
    try:
        test_file = db_folder / "test.txt"
        with open(test_file, "w") as testf:
            testf.write("testing")
        test_file.unlink()
    except PermissionError:
        try:
            db_folder = pathlib.Path.home() / "emm_db"
            db_folder.mkdir()
        except FileExistsError as error:
            pass
        except Exception as error:
            LOGGER.exception(error)
    return db_folder


@click.command()
@click.option(
    "--db_folder",
    "-d",
    help="Where to update the DB",
    default=get_db_folder(),
    show_default=True,
)
def emmtyper_db( db_folder):
    """

    By default, db_folder will be taken from EMM_DB environmental folder.
    If can't find the folder, will default to where emmtyper
    is installed. If it cannot write to the installation folder,
    it will make a suggestion in your /home folder.

    """
    download_cdc_db(db_folder)


if __name__ == "__main__":
    emmtyper_db()
