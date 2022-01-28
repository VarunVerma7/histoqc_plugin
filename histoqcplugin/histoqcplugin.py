from ctk_cli import CLIArgumentParser
import girder_client
import os
import tempfile
import subprocess
import imageio
import numpy as np


def process_image(tmp_directory, item_name):
    try:
        final_mask = imageio.imread(
            f"../histoqc{tmp_directory}/outputs//item_name}/{item_name}_mask_use.png"
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
            }
        }
    except Exception as Ex:
        print("Exception in processing", Ex)
        return {"histoqc_metadata": {"process": "failed"}}

    return final_response


def descend_folder(gc, folder_id, verbose=True):
    # Recursively descend into folders, finding slides and other folders

    # recursively call on subfolders
    for folder in gc.listFolder(
        parentId=folder_id, parentFolderType="folder", limit=None
    ):
        descend_folder(gc, folder["_id"], verbose=True)

    # get list of slides in current folder
    for slide in gc.listItem(folderId=folder_id, limit=None):
        query_slide(gc, slide["_id"], parentId=folder_id, verbose=True)

    return


def query_slide(gc, slide_id, parentId, verbose=True):

    # Download folder or download item?

    supported_extensions = [".svs", ".tif", ".tiff" ".svslide", ".scn", ".vmu"]

    with tempfile.TemporaryDirectory() as tmpdir:
        gc.downloadItem(slide_id, tmpdir)

        item = gc.getItem(slide_id)
        item_name = item.get("name", "None")
        gc.downloadItem(slide_id, tmpdir)

        # path is histoqc/tmpdir/itemname

        _, extension = os.path.splitext(item_name)

        print(f"EXTENSION IS {extension} ITEM NAME IS {item_name}")

        if extension in supported_extensions:
            print("Extension found in supported extensions")
            os.chdir("../HistoQC2")

            print(f"THIS IS THE TMP DIR {tmpdir}")
            input_directory = f"../histoqc{tmpdir}/{item_name}"

            print(f"{input_directory}")

            print(f"Listing input directory {os.listdir(input_directory)}")

            subprocess.call(
                f"python3 -m histoqc {input_directory} -o ../histoqc{tmpdir}/outputs --force",
                shell=True,
            )
            metadata_response_dict = process_image(tmpdir, item_name)

            print(f"Meta Data response dictionary {metadata_response_dict}")

            gc.addMetadataToItem(slide_id, metadata_response_dict)
            gc.upload(f"../histoqc{tmpdir}/{slide_id}", parentId)

            print("Uploading completed!")

        else:
            print(f"File type not supported with item name of {item_name}")

    return


def parse_dir_input(directory):
    # Parses girder ID out of directory argument passed to CLI

    return directory.split(os.sep)[4]


def main(args):
    """We expect to receive a girder ID of a folder (directory), a Girder API url (girderApiUrl),
    and a Girder token (girderToken). We use the Girder API to walk the folders recursively,
    acquiring info from each item/slide, and writing metadata back to the items.
    """

    # create girder client from token and url
    # gc.setToken(args.girderToken)

    # #descend recursively into folders and analyze each slide within
    # descend_folder(gc, parse_dir_input(args.directory))

    print("START OF MAIN")

    print("ALL ARGS ", args)
    gc = girder_client.GirderClient(apiUrl=args.girderApiUrl)
    folder_id = "61dd35ab5ef164ec2f932d36"

    # use API key instead
    gc.authenticate("admin", "password")
    print("WE AUTHENTICATED")
    gc.inheritAccessControlRecursive("61dd35ab5ef164ec2f932d36")

    print("MAIN METHOD ENDED")
    descend_folder(gc, parse_dir_input(args.directory))


if __name__ == "__main__":
    main(CLIArgumentParser().parse_args())

