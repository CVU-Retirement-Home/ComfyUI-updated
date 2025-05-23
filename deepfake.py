import os
import random
import sys
from typing import Sequence, Mapping, Any, Union
import torch


def get_value_at_index(obj: Union[Sequence, Mapping], index: int) -> Any:
    """Returns the value at the given index of a sequence or mapping.

    If the object is a sequence (like list or string), returns the value at the given index.
    If the object is a mapping (like a dictionary), returns the value at the index-th key.

    Some return a dictionary, in these cases, we look for the "results" key

    Args:
        obj (Union[Sequence, Mapping]): The object to retrieve the value from.
        index (int): The index of the value to retrieve.

    Returns:
        Any: The value at the given index.

    Raises:
        IndexError: If the index is out of bounds for the object and the object is not a mapping.
    """
    try:
        return obj[index]
    except KeyError:
        return obj["result"][index]


def find_path(name: str, path: str = None) -> str:
    """
    Recursively looks at parent folders starting from the given path until it finds the given name.
    Returns the path as a Path object if found, or None otherwise.
    """
    # If no path is given, use the current working directory
    if path is None:
        path = os.getcwd()

    # Check if the current directory contains the name
    if name in os.listdir(path):
        path_name = os.path.join(path, name)
        print(f"{name} found: {path_name}")
        return path_name

    # Get the parent directory
    parent_directory = os.path.dirname(path)

    # If the parent directory is the same as the current directory, we've reached the root and stop the search
    if parent_directory == path:
        return None

    # Recursively call the function with the parent directory
    return find_path(name, parent_directory)


def add_comfyui_directory_to_sys_path() -> None:
    """
    Add 'ComfyUI' to the sys.path
    """
    comfyui_path = find_path("ComfyUI")
    if comfyui_path is not None and os.path.isdir(comfyui_path):
        sys.path.append(comfyui_path)
        print(f"'{comfyui_path}' added to sys.path")


def add_extra_model_paths() -> None:
    """
    Parse the optional extra_model_paths.yaml file and add the parsed paths to the sys.path.
    """
    try:
        from main import load_extra_path_config
    except ImportError:
        print(
            "Could not import load_extra_path_config from main.py. Looking in utils.extra_config instead."
        )
        from utils.extra_config import load_extra_path_config

    extra_model_paths = find_path("extra_model_paths.yaml")

    if extra_model_paths is not None:
        load_extra_path_config(extra_model_paths)
    else:
        print("Could not find the extra_model_paths config file.")


add_comfyui_directory_to_sys_path()
add_extra_model_paths()


def import_custom_nodes() -> None:
    """Find all custom nodes in the custom_nodes folder and add those node objects to NODE_CLASS_MAPPINGS

    This function sets up a new asyncio event loop, initializes the PromptServer,
    creates a PromptQueue, and initializes the custom nodes.
    """
    import asyncio
    import execution
    import server

    # Creating a new event loop and setting it as the default loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Creating an instance of PromptServer with the loop
    server_instance = server.PromptServer(loop)
    execution.PromptQueue(server_instance)




from nodes import NODE_CLASS_MAPPINGS


def main():
    #CONFIGS
    image_to_generate_count = 5 #how many images to generate
    neg_prompt = 'text, error, cropped, worst quality, low quality, duplicate, morbid, mutilated, out of frame, deformed, blurry, watermark, blurry grass, animated, cartoon, high contrast, high saturation, blurry leaves, blurry trees, incorrect number of fingers'
    pos_prompt = 'earthquake natural disaster aftermath of broken houses in a neighborhood in south east asian country'
    lora_name = "dizhen_optimizeV2.safetensors" #copy filename from \models\loras with extension
    ckpt_path = "realisticVisionV60B1_v51HyperVAE.safetensors" #base model
    output_folder = r'D:\SeeThrough\ComfyUI_windows_portable\ComfyUI\retirement_dataset_fake' #folder to save generate images to, defaults to output folder in root comfyui
    upscale_model = 'RealESRGAN_x8.pth'
    os.makedirs(output_folder,exist_ok=True)
    import_custom_nodes()
    
    with torch.inference_mode():
        checkpointloadersimple = NODE_CLASS_MAPPINGS["CheckpointLoaderSimple"]()
        checkpointloadersimple_4 = checkpointloadersimple.load_checkpoint(
            ckpt_name= ckpt_path
        )

        emptylatentimage = NODE_CLASS_MAPPINGS["EmptyLatentImage"]()
        emptylatentimage_5 = emptylatentimage.generate(
            width=512, height=512, batch_size=1
        )

        loraloader = NODE_CLASS_MAPPINGS["LoraLoader"]()
        loraloader_43 = loraloader.load_lora(
            lora_name=lora_name,
            strength_model=1,
            strength_clip=1,
            model=get_value_at_index(checkpointloadersimple_4, 0),
            clip=get_value_at_index(checkpointloadersimple_4, 1),
        )

        cliptextencode = NODE_CLASS_MAPPINGS["CLIPTextEncode"]()
        cliptextencode_7 = cliptextencode.encode(
            text=neg_prompt,
            clip=get_value_at_index(loraloader_43, 1),
        )

        cliptextencode_16 = cliptextencode.encode(
            text=pos_prompt,
            clip=get_value_at_index(loraloader_43, 1),
        )

        upscalemodelloader = NODE_CLASS_MAPPINGS["UpscaleModelLoader"]()
        upscalemodelloader_32 = upscalemodelloader.load_model(
            model_name=upscale_model
        )
      
        saveimage = NODE_CLASS_MAPPINGS["SaveImage"]()

        for q in range(image_to_generate_count):
            ksampler = NODE_CLASS_MAPPINGS["KSampler"]()
            ksampler_3 = ksampler.sample(
                seed=random.randint(1, 2**64),
                steps=20,
                cfg=8,
                sampler_name="dpmpp_2m",
                scheduler="karras",
                denoise=1,
                model=get_value_at_index(loraloader_43, 0),
                positive=get_value_at_index(cliptextencode_16, 0),
                negative=get_value_at_index(cliptextencode_7, 0),
                latent_image=get_value_at_index(emptylatentimage_5, 0),
            )

            vaedecode = NODE_CLASS_MAPPINGS["VAEDecode"]()
            vaedecode_8 = vaedecode.decode(
                samples=get_value_at_index(ksampler_3, 0),
                vae=get_value_at_index(checkpointloadersimple_4, 2),
            )

            imageupscalewithmodel = NODE_CLASS_MAPPINGS["ImageUpscaleWithModel"]()
            imageupscalewithmodel_45 = imageupscalewithmodel.upscale(
                upscale_model=get_value_at_index(upscalemodelloader_32, 0),
                image=get_value_at_index(vaedecode_8, 0),
            )

            imagescale = NODE_CLASS_MAPPINGS["ImageScale"]()
            imagescale_46 = imagescale.upscale(
                upscale_method="area",
                width=1024,
                height=1024,
                crop="disabled",
                image=get_value_at_index(imageupscalewithmodel_45, 0),
            )

            vaeencode = NODE_CLASS_MAPPINGS["VAEEncode"]()
            vaeencode_47 = vaeencode.encode(
                pixels=get_value_at_index(imagescale_46, 0),
                vae=get_value_at_index(checkpointloadersimple_4, 2),
            )

            ksampler_48 = ksampler.sample(
                seed=random.randint(1, 2**64),
                steps=20,
                cfg=8,
                sampler_name="dpmpp_2m",
                scheduler="karras",
                denoise=0.36,
                model=get_value_at_index(loraloader_43, 0),
                positive=get_value_at_index(cliptextencode_16, 0),
                negative=get_value_at_index(cliptextencode_7, 0),
                latent_image=get_value_at_index(vaeencode_47, 0),
            )

            vaedecode_49 = vaedecode.decode(
                samples=get_value_at_index(ksampler_48, 0),
                vae=get_value_at_index(checkpointloadersimple_4, 2),
            )

            saveimage_50 = saveimage.save_images(
                filename_prefix="img_encoded",
                count = q,
                output_folder = output_folder,
                images=get_value_at_index(vaedecode_49, 0),
            )


if __name__ == "__main__":
    main()
