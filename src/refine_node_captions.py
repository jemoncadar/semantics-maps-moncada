

import argparse
import json
import os
import time

from tqdm import trange

import slam
from llm.gemini_provider import GoogleGeminiProvider
from utils.file_utils import (create_directories_for_file, load_json,
                              save_as_json, save_as_pickle)

# Credentials
GOOGLE_GEMINI_CREDENTIALS_FILE_PATH = "./credentials/concept-graphs-moncada-a807e893ef12.json"
GOOGLE_GEMINI_PROJECT_ID = "concept-graphs-moncada"
GOOGLE_GEMINI_PROJECT_LOCATION = "us-central1"

# Constants
CAPTIONS_FILENAME = "cfslam_llava_captions.json"
REFINED_CAPTION_FILENAME = "cfslam_gpt-4_responses.pkl"


def main(args):

    # Create Gemini instance
    llm_service = GoogleGeminiProvider(credentials_file=GOOGLE_GEMINI_CREDENTIALS_FILE_PATH,
                                       project_id=GOOGLE_GEMINI_PROJECT_ID,
                                       project_location=GOOGLE_GEMINI_PROJECT_LOCATION,
                                       model_name=GoogleGeminiProvider.GEMINI_1_5_PRO)

    # Get captions generated by extract_node_captions
    captions_file_path = os.path.join(args.cache_dir_path,
                                      CAPTIONS_FILENAME)
    captions_list = load_json(file_path=captions_file_path)

    # List with all caption refinement responses
    caption_refinement_responses = list()

    for obj_idx in trange(len(captions_list),
                          desc="Iterating over objects..."):
        # Get object captions without "low confidences"
        object_with_captions = captions_list[obj_idx]
        object_with_captions = {
            k: v for k, v in object_with_captions.items() if k != "low_confidences"}
        object_with_captions_str = json.dumps(object_with_captions, indent=0)

        # Get refined caption file path
        refined_caption_output_file_path = os.path.join(args.scene_dir_path,
                                                        "llm_results",
                                                        "refine_node_captions",
                                                        f"object_{obj_idx}.json")

        if os.path.exists(refined_caption_output_file_path):  # File already exists
            print(
                f"File already exists {refined_caption_output_file_path}, skipping LLM call...")
            refined_caption = load_json(
                file_path=refined_caption_output_file_path)

        else:  # File doesn't exist
            # Perform LLM call
            refined_caption = llm_service.refine_captions(
                captions_dict_str=object_with_captions_str)
            # Sleep to avoid Gemini 1.5 max responses per minute error
            time.sleep(10)

            refined_caption = json.loads(refined_caption)

            # Save response
            create_directories_for_file(refined_caption_output_file_path)
            save_as_json(obj=refined_caption,
                         file_path=refined_caption_output_file_path)

        object_with_captions["response"] = refined_caption
        caption_refinement_responses.append(refined_caption)

    # Save result to a pickle file
    result_file_path = os.path.join(args.cache_dir_path,
                                    REFINED_CAPTION_FILENAME)
    create_directories_for_file(result_file_path)
    save_as_pickle(obj=caption_refinement_responses,
                   file_path=result_file_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="TODO: program description")

    parser.add_argument("--scene-dir-path",
                        "-s",
                        type=str,
                        required=True,
                        help="Path to the scene folder")

    parser.add_argument("--map-file-path",
                        "-m",
                        type=str,
                        required=True,
                        help="Path to the map file")

    # TODO: help
    parser.add_argument("--cache-dir-path",
                        "-c",
                        type=str,
                        required=True,
                        help="")

    args = parser.parse_args()

    main(args)
