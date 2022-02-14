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
import json
import imageio


def query_slide(gc, inputImageFile, outputAnnotationFile, outputStainImageFile_1):

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
            metadata_response_dict = process_image(
                tmpdir, (name + extension), outputStainImageFile_1
            )

            print(f"Meta Data response dictionary {metadata_response_dict}")
            annotation = [
                {
                    "name": "Final Mask",
                    "description": "Binary Mask",
                    "elements": [
                        {
                            "type": "image",
                            "girderId": "outputStainImageFile_1",
                            "transform": {
                                "xoffset": 0,
                                "yoffset": 0,
                            },
                        }
                    ],
                }
            ]

            with open(outputAnnotationFile, "w") as annotation_file:
                json.dump(annotation, annotation_file, indent=2, sort_keys=False)

            # gc.addMetadataToItem(slide_id, metadata_response_dict)
            # gc.upload(f"{tmpdir}/{slide_id}", parentId)

            print("Uploading completed!")

        else:
            print(f"File type not supported with item name of {inputImageFile}")

    return


def process_image(tmp_directory, item_name, outputStainImageFile_1):
    try:
        final_mask = imageio.imread(
            f"{tmp_directory}/outputs/{item_name}/{item_name}_mask_use.png"
        )

        print(f"FINAL MASK SHAPE {final_mask.shape}")

        imageio.imsave(f"{outputStainImageFile_1}.svs", final_mask[:, :, 0])

        print(os.listdir())
        print("SUCCESSFULLY SAVED")

        final_response = {
            "histoqc_metadata": {
                "fileprocessed": item_name,
                "timeprocessed": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "config": "default",
            }
        }
        return final_response
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
    print("OUTPUT ANNOTATION FILE ", args.outputAnnotationFile)
    print("OUTPUT STAIN IMAGE FILE 1 ", args.outputStainImageFile_1)
    gc = girder_client.GirderClient(apiUrl=args.girderApiUrl)
    gc.authenticate(apiKey=args.girderApiKey)
    print("WE AUTHENTICATED")
    query_slide(
        gc, args.inputImageFile, args.outputAnnotationFile, args.outputStainImageFile_1
    )


if __name__ == "__main__":
    main(CLIArgumentParser().parse_args())
