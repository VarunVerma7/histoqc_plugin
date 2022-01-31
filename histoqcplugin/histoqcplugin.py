from ctk_cli import CLIArgumentParser
import girder_client
import os
import tempfile
import subprocess
import numpy as np
import imageio
from datetime import datetime
import logging
import sys


def descend_folder(gc, folder_id, verbose=True):
    # Recursively descend into folders, finding slides and other folders

    # recursively call on subfolders
    for folder in gc.listFolder(
        parentId=folder_id, parentFolderType="folder", limit=None
    ):
        descend_folder(gc, folder["_id"], verbose=True)

    # get list of slides in current folder
    for slide in gc.listItem(folderId=folder_id, limit=None):
        query_slide(gc, slide["_id"], verbose)

    return


def query_slide(gc, slide_id, parentId, verbose=True):

    # Download folder or download item?

    supported_extensions = [".svs", ".tif", ".tiff" ".svslide", ".scn", ".vmu"]

    with tempfile.TemporaryDirectory() as tmpdir:
        gc.downloadItem(slide_id, tmpdir)

        logging.debug("LISTING directory after download ", os.listdir(tmpdir))

        logging.debug("ABSOLUTE PATH AFTER DOWNLOAD ", os.path.abspath(tmpdir))

        item = gc.getItem(slide_id)
        item_name = item.get("name", "None")
        gc.downloadItem(slide_id, tmpdir)

        # path is histoqc/tmpdir/itemname

        _, extension = os.path.splitext(item_name)

        logging.debug(f"EXTENSION IS {extension} ITEM NAME IS {item_name}")

        if extension in supported_extensions:
            logging.debug("Extension found in supported extensions")
            os.chdir("../HistoQC")

            logging.debug(f"THIS IS THE TMP DIR {tmpdir}")
            input_directory = f"{tmpdir}/{item_name}"

            logging.debug(f"{input_directory}")

            subprocess.run(
                f"python3 -m histoqc {input_directory} -o {tmpdir}/outputs --force",
                shell=True,
            )
            metadata_response_dict = process_image(tmpdir, item_name)

            logging.debug(f"Meta Data response dictionary {metadata_response_dict}")

            gc.addMetadataToItem(slide_id, metadata_response_dict)
            gc.upload(f"{tmpdir}/{slide_id}", parentId)

            logging.debug("Uploading completed!")

        else:
            logging.debug(f"File type not supported with item name of {item_name}")

    return


def process_image(tmp_directory, item_name):
    try:
        final_mask = imageio.imread(
            f"{tmp_directory}/outputs/{item_name}/{item_name}_mask_use.png"
        )

        logging.debug("Successfully read in final_mask")

        final_mask_np_flattened = np.array(final_mask).flatten()

        good_count = np.sum(final_mask_np_flattened > 0)
        bad_count = np.sum(final_mask_np_flattened == 0)

        threshold_num = 1 if bool(good_count / (good_count + bad_count) >= 0.5) else 0

        final_response = {
            "histoqc_metadata": {
                "thresholded": threshold_num,
                "percentage": good_count / (good_count + bad_count),
                "fileprocessed": item_name,
                "timeprocessed": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "config": "default",
            }
        }
    except Exception as Ex:
        logging.debug("Exception in processing", Ex)
        return {"histoqc_metadata": {"process": "failed"}}

    return final_response


def parse_dir_input(directory):
    # Parses girder ID out of directory argument passed to CLI

    return directory.split(os.sep)[4]


def configureLogger():
    root = logging.getLogger()

    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


def main(args):
    """We expect to receive a girder ID of a folder (directory), a Girder API url (girderApiUrl),
    and a Girder token (girderToken). We use the Girder API to walk the folders recursively,
    acquiring info from each item/slide, and writing metadata back to the items.
    """

    # create girder client from token and url
    # gc.setToken(args.girderToken)

    # #descend recursively into folders and analyze each slide within
    # descend_folder(gc, parse_dir_input(args.directory))

    configureLogger()

    logging.debug("START OF MAIN")

    logging.debug("ALL ARGS ", args)
    gc = girder_client.GirderClient(apiUrl=args.girderApiUrl)
    folder_id = "61dd35ab5ef164ec2f932d36"

    # use API key instead
    gc.authenticate(apiKey=args.girderApiKey)
    logging.debug("WE AUTHENTICATED")

    descend_folder(gc, parse_dir_input(args.directory))


if __name__ == "__main__":
    main(CLIArgumentParser().parse_args())
