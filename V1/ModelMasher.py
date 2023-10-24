import modules.scripts as scripts
import gradio as gr
import os
import cv2
import json
import numpy as np
from modules import images
from modules.processing import process_images, Processed
from modules.processing import Processed
from modules.shared import opts, cmd_opts, state
from PIL import Image


class Script(scripts.Script):  

# The title of the script. This is what will be displayed in the dropdown menu.
    def title(self):

        return "Model Masher"


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
        mappings = gr.File(label="JSON File Containing Mapping Vectors", type="file", file_types=[".json"])
        blackBackground = gr.Checkbox(False, label="Black Background")
        reverseTransform = gr.Checkbox(False, label="Reverse Transformations")  # Add this line
        return [mappings, blackBackground, reverseTransform]  # Add reverseTransform to the return

    

  
# This is where the additional processing is implemented. The parameters include
# self, the model object "p" (a StableDiffusionProcessing class, see
# processing.py), and the parameters returned by the ui method.
# Custom functions can be defined here, and additional libraries can be imported 
# to be used in processing. The return value should be a Processed object, which is
# what is returned by the process_images method.

    def run(self, p, mappings, blackBackground, reverseTransform):

        # function which takes an image from the Processed object, 
        # and the angle and two booleans indicating horizontal and
        # vertical flips from the UI, then returns the 
        # image rotated and flipped accordingly
        def mash(im, inputJSON, blackBackground):  
            raf=im
            pil_image = im.convert('RGB') 
            open_cv_image = np.array(pil_image) 
            # Convert RGB to BGR 
            image = open_cv_image[:, :, ::-1].copy() 

            transformations = inputJSON['transformations']
            params = inputJSON['base_parameters']

            # Assuming the source (or original) image dimensions are `source_width` and `source_height`
            source_width = params['source_width']
            source_height = params['source_height']

            scale_factor_x = image.shape[1] / source_width
            scale_factor_y = image.shape[0] / source_height

            if blackBackground:
                output_image = np.zeros_like(image)
            else: 
                output_image = image.copy() # base image background

            for transformation in transformations:
                # Scale the original contour points
                original_contour = np.array(transformation['original_contour'], dtype=np.int32)
                original_contour[:, 0, 0] = (original_contour[:, 0, 0] * scale_factor_x).astype(np.int32)
                original_contour[:, 0, 1] = (original_contour[:, 0, 1] * scale_factor_y).astype(np.int32)

                # Scale the translation vector
                translation_vector = (int(transformation['translation_vector'][0] * scale_factor_x),
                                    int(transformation['translation_vector'][1] * scale_factor_y))

                # Scale the center of rotation
                center_of_rotation = (int(transformation['center_of_rotation'][0] * scale_factor_x),
                                    int(transformation['center_of_rotation'][1] * scale_factor_y))
                
                # Extract and scale the original_center
                original_center = (int(transformation['original_center'][0] * scale_factor_x),
                                    int(transformation['original_center'][1] * scale_factor_y))
                
                # Create the original mask using the original_contour
                original_mask = np.zeros(image.shape[:2], dtype=np.uint8)


                rotation_angle = transformation['rotation_angle']   

                # Compute the transformation matrix
                M_rotation = cv2.getRotationMatrix2D(center_of_rotation, rotation_angle, 1)
                M_rotation[0, 2] += translation_vector[0]
                M_rotation[1, 2] += translation_vector[1]  
                                

                
                 # If reverseTransform is checked:
                if reverseTransform:
                    # Forward operation

                    # Create a mask from the original contour
                    cv2.drawContours(original_mask, [original_contour], -1, (255), thickness=cv2.FILLED)

                    # Extract the puzzle piece from the original image using the original mask
                    piece = np.zeros_like(image)
                    piece[original_mask == 255] = image[original_mask == 255]

                    # Apply the transformation to the piece
                    transformed_piece = cv2.warpAffine(piece, M_rotation, (image.shape[1], image.shape[0]))

                    # Update the mask to match the transformed piece
                    transformed_mask = cv2.warpAffine(original_mask, M_rotation, (image.shape[1], image.shape[0]))
                    transformed_piece[transformed_mask == 0] = 0

                    # Add the transformed piece to the output image
                    output_image[transformed_mask == 255] = transformed_piece[transformed_mask == 255]

                else:                    
                    # Compute the inverse of the transformation matrix
                    M_inverse = cv2.invertAffineTransform(M_rotation)

                    # Apply the inverse transformation to the entire image
                    inversely_transformed_image = cv2.warpAffine(image, M_inverse, (image.shape[1], image.shape[0]))

                    cv2.drawContours(original_mask, [original_contour], -1, (255), thickness=cv2.FILLED)
                    reverted_piece = np.zeros_like(image)
                    reverted_piece[original_mask == 255] = inversely_transformed_image[original_mask == 255]

                    # Place this piece on the output image
                    output_image[original_mask == 255] = reverted_piece[original_mask == 255]

            img_cv2 = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_cv2)
            return img_pil

  

        # If overwrite is false, append the rotation information to the filename
        # using the "basename" parameter and save it in the same directory.
        # If overwrite is true, stop the model from saving its outputs and
        # save the rotated and flipped images instead.
        basename = ""
        basename += "_vflip"
        
        proc = process_images(p)

            # Load the transformations
        print(mappings.name)
        with open(mappings.name, 'r') as file:
            mapping = json.load(file)

        # rotate and flip each image in the processed images
        # use the save_images method from images.py to save
        # them.
        for i in range(len(proc.images)):
            images.save_image(proc.images[i], p.outpath_samples, basename+"_mash",
            proc.seed + i, proc.prompt, opts.samples_format, info= proc.info, p=p)


        for i in range(len(proc.images)):
            mashedImage =  mash(proc.images[i], mapping, blackBackground)
            proc.images.append(mashedImage)

            images.save_image(mashedImage, p.outpath_samples, basename+"_mash",
            proc.seed + i, proc.prompt, opts.samples_format, info= proc.info, p=p)

        return proc