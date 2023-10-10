
## Example Workflow

This workflow provides an example for generating an ACC Livery. It should be effective for most complex UV maps, though results might vary. If you're reading this, it's assumed you know how to set up a custom livery for ACC. If not, you can view my [video tutorial](https://www.youtube.com/watch?v=gyHiSUuZmRA) for the base setup.

The initial steps (0-2) are required once per model to produce the necessary base files for as many AI liveries as desired.

### Prerequisites:
- [Automatic111's Stable Diffusion UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
- [Controlnet Extension](https://github.com/Mikubill/sd-webui-controlnet)

---

### Step 0: Download Template Files

- Locate the PSD template for your desired car skin.
  - I use [this Google Drive folder](https://drive.google.com/drive/folders/1xh92HjkVp1ilkmx4F3_tpRB7dWt8pHlP), but there are other options available.
- **Optional**: For those wanting to use Armorpainter to create a segmentation map, find the 3DOBJ template.
  - Again, I use [this Google Drive folder](https://drive.google.com/drive/folders/1Vx2_fFr_LlEavvqd0rdJvkN7-Ly5lGNE).

---

### Step 1: Prepare Your Wireframe

- Open the wireframe template in Photoshop.
- Keep only the UV layer visible. Aim for a white background with black wireframes and a colored outline for each segment.
  - While wireframes are straightforward, some segments might overlap. For more precision, mask each segment in white against a black background.
- Save the file as a PNG, ensuring dimensions do not exceed 2048x2048.

Your output should resemble one of these:
![Wireframe](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/Porche_wire.png?raw=true)
![BlackWhite](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/blackwhite.png?raw=true)

---

### Step 1.5 (Optional): Enhance Control Over Appearance

For this step, [segmentation details truncated for brevity]

---

### Step 4: Upscale

If satisfied with a generated image:

- Click the painting below it to navigate to the `img2img` tab.
- Set sampling steps to a minimum of 60.
- Choose the DPM++ 2m Karras Sampling method.
- Opt for a low denoising strength, typically around 0.2.
- I prefer a moderate cfg scale, so I set it to 17.
- In scripts, select the SD upscale option:
  - Set the scale factor to 4.
  - Choose the ESRGAN_4x upscaler.
- Generate and save this as `decals.png` to preview in ACC.
- For those with powerful systems, repeat this process to upscale to 4096x4096. If not, navigate to the extras tab > single image upscaler 1 and set it to ESRGAN_4x.

![Final Image](https://github.com/prdoring/ModelMasher/blob/main/readmeimg/4080acc.png?raw=true)
