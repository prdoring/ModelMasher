from flask import Flask, request, jsonify, send_from_directory
import cv2
import numpy as np
import os
import json;

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


def save_transformations(modded_pieces):
    
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

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
