
# Model Masher

I initally built these tools in an effort to better generate ACC Liveries with stable diffusion.  After much experimentation with controlnet and custom LORAs we soon ran into the limitations of SDs ability to "stitch" pieces of UV files that a physically seperate on a texture sheet, but logically together in the complied OBJ.



## Installation

To use these tools place the modelmasher.py file in the stable diffusion scripts folder, then download the ArrangementTool folder and run 

```bash
  python server.py
```
    

## Example Workflow

Here is an example workflow for generating an ACC Livery.  This should work for most complex UV maps but your mielage may vary.  I will skip the specifics of setting up a custom livery for ACC as if you are here I am sure you allready know how to do so. If you don't you can check out my [video tutorial](https://www.youtube.com/watch?v=gyHiSUuZmRA) for the base setup.

Steps 0-2 will only need to be done once per model to generate the base files needed for as many ai liveries as you want.

**Prereqs**
* [Automatic111's stable diffusion UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
* [Controlnet extension](https://github.com/Mikubill/sd-webui-controlnet)

***

**Step 0 - Download Your Template Files**
* Find the PSD template for the car you wish to skin.
    * I use [this](https://drive.google.com/drive/folders/1xh92HjkVp1ilkmx4F3_tpRB7dWt8pHlP) gdrive folder but there are many out there
* (Optional) Find the 3DOBJ template if you wish to use armorpainter to create a segmentation map
    * I use [this](https://drive.google.com/drive/folders/1Vx2_fFr_LlEavvqd0rdJvkN7-Ly5lGNE) gdrive folder but there are many out there

**Step 1 - Prepare your wireframe**
* Open your wireframe template in photoshop.
* Hide all layers except for the UV, you are looking for a white background with black wireframes, and a colored outline for each piece.
    * Using a wireframe is super simple but some parts may get lost with others, if you want more control you can mask each "piece" in white, with a black background and the arrangement tool may be more accurate.
* Save these files as PNGs no larger than 2048X2048

Your output should look something like one of the two images below.
![Wireframe](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/Porche_wire.png?raw=true)
![BlackWhite](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/blackwhite.png?raw=true)

**Step 1.5 (Optional) - For finer control of the "Look" you can generate a segmentation file**
* You could base this on an existing livery, create it in photoshop, or through other means, but the quick and dirty way is with [Armorpaint](https://armorpaint.org/).
* Open armorpaint and Import the obj file you downloaded earlier.
* With Xray on ramp up your brush size to max and paint the whole thing a bright color.
* Turn off Xray, and use the tools provided to color segments that you wish to have a seperate look distinct colors. 
    * No need to be exact, just get the idea of what you want in there.
    * X mirror us useful if you want symmetry
    * Controlnet segmentation works well with larger color blocks, so try not to get too details, but who knows, experimentation is fun.
* File->Export Texture
    * preset base_color
    * all other settings the same
* Hit export and save this file in the same location as your wireframe image.  
![Armorpaint](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/apcolor.png?raw=true)
![Armorpaint output](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/SEGIMG_base.png?raw=true)

**Step 2 - Create Your Arrangement**
* Open up a terminal
* ```cd [directory you placed server.py and index.html]```
* ```python server.py```
* In a browser navigate to http://127.0.0.1:5000/ or the URL output in the server startup.
* For the wireframe, select the wireframe or black and white image you generated in step 1.
* Threshold determinse how large of a piece will be rendered.  Set this higher for only large pieces, smaller if you want all the details.
* Click 'Upload Image'
* Arrange the pieces in the way they best fit the logical locations of the car
    * Right click will rotate the piece.
    * Shift + Scroll Wheel will zoom  
    * Overlaps are okay, and sometimes better, I don't have warping figured out yet so this is best effort.
    * Anything outside of the bounding rect will be rendered black.
* Below is the before and after for the model I am working on in this example.
* (Optional) Upload the segmentation image we generated in step 1.5
* When you are happy with your arrangement Click 'Save Mapping'
* This should output a JSON file and if you used a segmentation image, a segmentation file in the output folder of your server directory.
![before](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/before.png?raw=true)
![after](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/after.png?raw=true)

**Step 3 - GENERATE SOME LIVERIES!**
* Launch Automatic111's webUI for stable diffusion.
* In the text to img tab set your parameters.
    * I like the following but part of the fun is playing with these values.
    * [deliberate_v3](https://civitai.com/models/4823/deliberate) checkpoint
    * DPM++ 2m Karras Sampling method
    * 60 Sampling Steps
    * 512X512
    * I like a batch count of 4 so I can choose my favorite
* (OPTIONAL) If using a segmentation image open up control net which you totally allready installed RIGHT?!
    * Under single image select the generated segmentation image from step 2. NOT the segmentation image you provided for step 2, but the one output in the same folder as your json file. ([serverfolder]/output)
    * Under model select whichever one ends with "_seg"
    * Modify your control weight, this determins how strongly it will conform to your segmentation image. Super fun to play around with. But if it is too high it can make your image have odd artifacts around segment edges.  For this example I'll set it to 0.6.
        * It may be fun to play with start and end steps as well, I find that setting a lower end step lets SD blend the segmentation better.
* Under script select 'Model Masher'
    * Select the JSON file output by step 2 ([serverfolder]/output)
    * Select black background if you want any pieces that werent part of your arrangement to be unskinned
        * I prefer to leave this unchecked as it at-least puts the smaller pieces in the same pallate.
* Enter a text prompt! for this example I will use "wooded forrest, creatures, streams, trees, cliffs, painting"
* After it runs, model masher will output the base images first, and then the mashed ones after.  Find the ones that look to have weird blocking, of a contiguous image.
* Save this 512 version as your decals.png by hitting the download button in the top right of the image.
* Give it a look in ACC, and we can see if we want to move on to upscaling!

![base](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/BASE.png?raw=true)
![mashed](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/MASHED.png?raw=true)
![low-res-test](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/512acc.png?raw=true)
