from flask import Flask, request, jsonify, send_from_directory
import cv2
import numpy as np
import os
import json;
from PIL import Image

app = Flask(__name__)

# Assuming a folder named 'uploads' for storing uploaded images
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

puzzle_pieces = []
uploadname = "nofile"
uploadX = 0
uploadY = 0

@app.route('/upload', methods=['POST'])
def upload_image():
    global puzzle_pieces
    global uploadname
    global uploadHeight
    global uploadWidth
    
    puzzle_pieces = []
    
    if 'image' not in request.files:
        return jsonify({"message": "No image part in the request"}), 400

    image_file = request.files['image']
    thresh = float(request.form['threshold'])
    uploadname = request.form['filename']
    filename = os.path.join(UPLOAD_FOLDER, uploadname)
    image_file.save(filename)

    # Load and process the image using OpenCV
    image = cv2.imread(filename)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Check if it's a wireframe or a black and white image
    avg_intensity = gray_image.mean()
    is_wireframe = avg_intensity > 200  # Adjust this threshold if needed
    uploadHeight, uploadWidth = gray_image.shape
    # If it's a wireframe, preprocess it
    if is_wireframe:
        wireframe_rgb = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2RGB)

        # Isolate non-white and non-black/gray pixels
        non_white_mask = cv2.inRange(wireframe_rgb, np.array([1, 1, 1]), np.array([254, 254, 254]))
        non_black_mask = cv2.inRange(wireframe_rgb, np.array([40, 40, 40]), np.array([255, 255, 255]))
        border_mask = cv2.bitwise_and(non_white_mask, non_black_mask)

        # Binary Threshold
        _, binary_mask = cv2.threshold(border_mask, 1, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    else:
        _, binary_mask = cv2.threshold(gray_image, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


    min_area_threshold = thresh
    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= min_area_threshold:
            M = cv2.moments(contour)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            position = (cX, cY)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            x, y, w, h = cv2.boundingRect(contour)
            bounding_box = {"x": x, "y": y, "width": w, "height": h}
            puzzle_pieces.append({
                'original_piece': contour.tolist(),
                'piece': contour.tolist(),
                'original_position': position,
                'position': position,
                'original_center': center,
                'center': center,
                'original_angle': 0,
                'angle': 0,
                'bounding_box': bounding_box
            })

    return jsonify({"message": "Image processed successfully"})

@app.route('/get_puzzle_pieces', methods=['GET'])
def get_puzzle_pieces_data():
    print(len(puzzle_pieces))
    return jsonify(puzzle_pieces)

@app.route('/save_modified_data', methods=['POST'])
def save_modified_data():
    piece_data = request.json
    save_transformations(piece_data)
    return jsonify({"message": "Sent Modified Data"})


data = []
def save_transformations(modded_pieces):
    global data
    base_parameters = {
        'source_width': uploadWidth,
        'source_height': uploadHeight,
    }
    data = {
        'base_parameters': base_parameters,
        'transformations': []
    }
    #puzzle_pieces[]
    for idx, piece_data in enumerate(modded_pieces):
        
        transformation = {
            'translation_vector': (piece_data['position'][0] - puzzle_pieces[idx]['original_position'][0], piece_data['position'][1] - puzzle_pieces[idx]['original_position'][1]),
            'rotation_angle': -piece_data['angle'],
            'center_of_rotation': puzzle_pieces[idx]['center'],
            'original_contour': puzzle_pieces[idx]['original_piece'],
            'original_center': puzzle_pieces[idx]['original_center']
        }
        data['transformations'].append(transformation)
    with open("output/"+os.path.splitext(uploadname)[0]+'_map.json', 'w') as file:
        json.dump(data, file, indent=4)
    return jsonify({"message": "Transformations saved successfully"})



@app.route('/seg', methods=['POST'])
def process_seg():
    # Grab The Image
    if 'image' not in request.files:
        return jsonify({"message": "No image part in the request"}), 400

    img_file = request.files['image']
    filename = os.path.join(UPLOAD_FOLDER, "SEG_"+uploadname)
    img_file.save(filename)
    image_file = cv2.imread(os.path.join(UPLOAD_FOLDER, "SEG_"+uploadname))
    # Mash it
    #pil_image = image_file.convert('RGB') 
    #open_cv_image = np.array(pil_image) 
    # Convert RGB to BGR 
    image = image_file #open_cv_image[:, :, ::-1].copy() 

    transformations = data['transformations']
    params = data['base_parameters']

    # Assuming the source (or original) image dimensions are `source_width` and `source_height`
    source_width = params['source_width']
    source_height = params['source_height']

    scale_factor_x = image.shape[1] / source_width
    scale_factor_y = image.shape[0] / source_height
    output_image = np.zeros_like(image)

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
    img_cv2 = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_cv2)
    filename = os.path.join(OUTPUT_FOLDER, "SEG_"+uploadname)
    img_pil.save(filename)
    return jsonify({"message": "Segmentation Image Generated Succesfully"})



@app.route('/')
def index():
    return send_from_directory('.', 'index.html')




if __name__ == '__main__':
    app.run(debug=True)
