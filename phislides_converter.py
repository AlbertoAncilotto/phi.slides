import pymupdf   
import cv2
import numpy as np
import os
import yaml
import argparse

def pdf_to_slides_with_yaml(pdf_path, output_dir, output_resolution=(2000, 1000)):
    os.makedirs(output_dir, exist_ok=True)
    slides_dir = os.path.join(output_dir, "slides")
    interactive_functions_dir = os.path.join(output_dir, "interactive_functions")
    video_dir = os.path.join(output_dir, "videos")
    os.makedirs(slides_dir, exist_ok=True)
    os.makedirs(interactive_functions_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)
    interactive_script_path = os.path.join(interactive_functions_dir, "loopback.py")
    with open(interactive_script_path, "w") as script_file:
        script_file.write("def process_frame(frame):\n    return frame")
    slides_yaml = []

    
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    parameters =  cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)

    pdf_document = pymupdf.open(pdf_path)
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(output_resolution[0] / page.rect.width, 
                                                 output_resolution[1] / page.rect.height))
        img = cv2.imdecode(np.frombuffer(pix.tobytes(), np.uint8), cv2.IMREAD_UNCHANGED)
        
        slide_filename = f"slide_{page_number + 1}.png"
        slide_path = os.path.join(slides_dir, slide_filename)
        cv2.imwrite(slide_path, img)

        slide_entry = {
            "img_slide": slide_filename,
            "interactive_frames": []
        }

        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = detector.detectMarkers(gray_img)

        if ids is not None:
            for corner_set in corners:
                x_min = min(corner_set[0][:, 0])
                x_max = max(corner_set[0][:, 0])
                y_min = min(corner_set[0][:, 1])
                y_max = max(corner_set[0][:, 1])
                width = x_max - x_min
                height = y_max - y_min

                x_frac = 0.5*(x_min+x_max) / img.shape[1]
                y_frac = 0.5*(y_min+y_max+1) / img.shape[0]
                width_frac = width / img.shape[1]
                height_frac = height / img.shape[0] + 0.05
                
                slide_entry["interactive_frames"].append({
                    "position": [float(x_frac), float(y_frac), float(max(width_frac, height_frac))],
                    "function": "loopback.process_frame"
                })

        if not slide_entry["interactive_frames"]:
            slide_entry["interactive_frames"] = None

        slides_yaml.append(slide_entry)

    pdf_document.close()

    yaml_path = os.path.join(output_dir, "slides.yaml")
    with open(yaml_path, "w") as yaml_file:
        yaml.dump({"slides": slides_yaml}, yaml_file, default_flow_style=False)

    print(f"Slides and YAML configuration generated in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PDF to slides with YAML configuration.")
    parser.add_argument("pdf_path", type=str, help="Path to the input PDF file.")
    parser.add_argument("--output_dir", type=str, default="output_slides", help="Directory to save PNGs and YAML (default: output_slides).")
    parser.add_argument("--output_resolution", type=tuple, default=(1800, 900), help="Desired resolution for the slides (default: (2000, 1000)).")
    
    args = parser.parse_args()
    
    pdf_to_slides_with_yaml(args.pdf_path, args.output_dir, args.output_resolution)
