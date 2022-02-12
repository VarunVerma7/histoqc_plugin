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
import requests
import large_image


def query_slide(gc, inputImageFile=None):

    # Download folder or download item?

    supported_extensions = [".svs", ".tif", ".tiff" ".svslide", ".scn", ".vmu"]
    print(f"Input image file in query ", inputImageFile)
    name, extension = os.path.splitext(os.path.basename(inputImageFile))

    print(f"EXTENSION IS {extension} ITEM NAME IS {name}")

    with tempfile.TemporaryDirectory() as tmpdir:

        if extension in supported_extensions:
            print("Extension found in supported extensions")
            os.chdir("../HistoQC")

            subprocess.run(
                f"python3 -m histoqc {inputImageFile} -o {tmpdir}/outputs --force",
                shell=True,
            )
            metadata_response_dict = process_image(tmpdir, (name + extension))

            print(f"Meta Data response dictionary {metadata_response_dict}")

            # gc.addMetadataToItem(slide_id, metadata_response_dict)
            # gc.upload(f"{tmpdir}/{slide_id}", parentId)

            print("Uploading completed!")

        else:
            print(f"File type not supported with item name of {inputImageFile}")

    return


def process_image(tmp_directory, item_name):
    try:
        final_mask = imageio.imread(
            f"{tmp_directory}/outputs/{item_name}/{item_name}_mask_use.png"
        )

        print("Successfully read in final_mask")

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
        print("Exception in processing", Ex)
        return {"histoqc_metadata": {"process": "failed"}}

    return final_response


def main(args):
    """We expect to receive a girder ID of a folder (directory), a Girder API url (girderApiUrl),
    and a Girder token (girderToken). We use the Girder API to walk the folders recursively,
    acquiring info from each item/slide, and writing metadata back to the items.
    """

    # create girder client from token and url
    # gc.setToken(args.girderToken)

    # #descend recursively into folders and analyze each slide within
    # descend_folder(gc, parse_dir_input(args.directory))

    # configureLogger()
    print("ALL ARGS ", args)
    print("INPUT FILE ", args.inputImageFile)
    gc = girder_client.GirderClient(apiUrl=args.girderApiUrl)
    gc.authenticate(apiKey=args.girderApiKey)
    print("WE AUTHENTICATED")
    query_slide(gc, args.inputImageFile)


if __name__ == "__main__":
    main(CLIArgumentParser().parse_args())
