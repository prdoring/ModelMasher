import modules.scripts as scripts
import gradio as gr
import os
from os.path import join
import cv2
import json
import numpy as np
from modules import images
from modules.processing import process_images, Processed
from modules.processing import Processed
from modules.shared import opts, cmd_opts, state
from PIL import Image
import subprocess
import time

class Script(scripts.Script):  

# The title of the script. This is what will be displayed in the dropdown menu.
    def title(self):

        return "Model MasherV2"


# Determines when the script should be shown in the dropdown menu via the 
# returned value. As an example:
# is_img2img is True if the current tab is img2img, and False if it is txt2img.
# Thus, return is_img2img to only show the script on the img2img tab.

    def show(self, is_img2img):

        return True

# How the script's is displayed in the UI. See https://gradio.app/docs/#components
# for the different UI components you can use and how to create them.
# Most UI components can return a value, such as a boolean for a checkbox.
# The returned values are passed to the run method as parameters.

    def ui(self, is_img2img):
        obj_file = gr.File(label="OBJ For your Model", type="file", file_types=[".obj"])
        return [obj_file]  # Add reverseTransform to the return

    
    def get_image_dimensions(image_path):
        with Image.open(image_path) as img:
            width, height = img.size
        return width, height
  

    def run(self, p, obj_file):  


        basename = ""
        basename += "_vflip"
        
        proc = process_images(p)

        # Load the transformations
        print(obj_file.name)
        # Correct the path setup
        script_dir = os.path.dirname(__file__)
        base_dir = os.path.dirname(script_dir)

        # Construct the mashout_tmp_path using the base_dir
        mashout_tmp_path = os.path.join(base_dir, 'mashout', 'tmp')
        width = p.width
        # Construct the command
        command = [
            'blender',
            os.path.join(script_dir, 'modelmasher', 'material2.blend'),
            '-b',
            '-P',
            os.path.join(script_dir, 'modelmasher', 'blenderApply.py'),
            '--',
            obj_file.name,
            mashout_tmp_path,
            str(width)
        ]

        # Loop through proc.images
        for i in range(len(proc.images)):
            saved_img_path = images.save_image(proc.images[i], p.outpath_samples, basename+"_mash",
                                            proc.seed + i, proc.prompt, opts.samples_format, info=proc.info, p=p)
            absolute_saved_img_path = os.path.join(base_dir, saved_img_path[0])
            print(absolute_saved_img_path)
            command.append(absolute_saved_img_path)
        subprocess.run(command)       
        for i in range(len(proc.images)):
            print("MASHING")
            
            # Construct the image path using base_dir
            output_dir = os.path.join(base_dir, 'mashout')
            image_path = os.path.join(output_dir, f"tmp_{i}.png")
            
            if not os.path.exists(image_path):
                print(f"The file does not exist at path: {image_path}")
                continue
            
            # Load the image
            mashedImage = cv2.imread(image_path)
            if(mashedImage.any()):
                mashedImage_PIL = Image.fromarray(cv2.cvtColor(mashedImage, cv2.COLOR_BGR2RGB))
            
                # Append the loaded image to proc.images
                proc.images.append(mashedImage_PIL)

                # Save the image if required
                images.save_image(mashedImage_PIL, p.outpath_samples, basename+"_mash",
                                proc.seed + i, proc.prompt, opts.samples_format, info=proc.info, p=p)
        return proc