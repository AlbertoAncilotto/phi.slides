import cv2
import yaml
import importlib
import os
import argparse

parser = argparse.ArgumentParser(description="Custom Slide Presentation Tool")
parser.add_argument(
    "base_folder",
    type=str,
    help="Base folder containing slides.yaml, slides, and interactive_functions folders",
)
args = parser.parse_args()
base_folder = args.base_folder

if not os.path.isdir(base_folder):
    raise FileNotFoundError(f"Base folder '{base_folder}' not found.")

yaml_path = os.path.join(base_folder, "slides.yaml")
slides_folder = os.path.join(base_folder, "slides")
video_folder = os.path.join(base_folder, "videos")
interactive_functions_folder = os.path.join(base_folder, "interactive_functions")

with open(yaml_path, "r") as file:
    slide_config = yaml.safe_load(file)["slides"]

interactive_content = []
background_images = []

for slide in slide_config:
    img_slide_path = os.path.join(slides_folder, slide["img_slide"])
    if not os.path.exists(img_slide_path):
        raise FileNotFoundError(f"Slide image '{img_slide_path}' not found.")
    bg_img = cv2.imread(img_slide_path)
    bg_img = cv2.resize(bg_img, (1800, 900), interpolation=cv2.INTER_LANCZOS4)
    background_images.append(bg_img)

    frames = []
    if slide.get("interactive_frames"):
        for interactive_frame in slide["interactive_frames"]:
            func_path = interactive_frame.get("function")
            if func_path and os.path.splitext(func_path)[1].lower() in [".mp4", ".gif"]:
                video_path = os.path.join(video_folder, func_path)
                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"Video file '{video_path}' not found.")
                video_cap = cv2.VideoCapture(video_path)
                frames.append({"type": "video", "cap": video_cap, "last_frame": None})
            else:
                try:
                    module_name, func_name = func_path.rsplit(".", 1)
                    module_path = os.path.join(interactive_functions_folder, module_name + ".py")
                    if not os.path.exists(module_path):
                        raise FileNotFoundError(f"Function file '{module_path}' not found.")
                    module = importlib.import_module(f"{base_folder}.interactive_functions.{module_name}")
                    process_func = getattr(module, func_name)
                    frames.append({"type": "function", "func": process_func})
                except Exception as e:
                    print(f"Error loading function '{func_path}': {e}")
                    frames.append(None)
    interactive_content.append(frames)

current_mode = 0
bg_img = background_images[current_mode]

cap = cv2.VideoCapture(0)  
cv2.namedWindow("Phi.Slides v0.0.3")


def switch_mode(delta):
    """Switch to a different mode (slide)."""
    global current_mode, bg_img
    current_mode = (current_mode + delta) % len(slide_config)
    bg_img = background_images[current_mode]


def process_frame(content, frame):
    """Process the current frame based on the interactive content type."""
    if isinstance(content, dict) and content.get("type") == "video":  # Video mode
        video_cap = content["cap"]
        ret, video_frame = video_cap.read()
        if ret:
            content["last_frame"] = video_frame
            return video_frame
        else:
            return content["last_frame"]  # Keep showing the last frame
    elif isinstance(content, dict) and content.get("type") == "function":  # Interactive function mode
        process_func = content["func"]
        return process_func(frame)
    return frame


while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    if not ret:
        break

    slide = slide_config[current_mode]
    frames = interactive_content[current_mode]

    interactive_frames = slide.get("interactive_frames") or []
    for idx, frame_config in enumerate(interactive_frames):
        content = frames[idx]
        interactive_frame = process_frame(content, frame)

        x_frac, y_frac = frame_config["position"][:2]
        h, w = bg_img.shape[:2]

        center_x = int(x_frac * w)
        center_y = int(y_frac * h)

        if len(frame_config["position"]) == 3:  # [x_frac, y_frac, scale]
            scale = frame_config["position"][2]
            aspect_ratio = interactive_frame.shape[1] / interactive_frame.shape[0]
            new_height = int(h * scale)
            new_width = int(new_height * aspect_ratio)
            resized_frame = cv2.resize(interactive_frame, (new_width, new_height))
        elif len(frame_config["position"]) == 4:  # [x_frac, y_frac, width_frac, height_frac]
            width_frac, height_frac = frame_config["position"][2:4]
            target_width = int(width_frac * w)
            target_height = int(height_frac * h)
            resized_frame = cv2.resize(interactive_frame, (target_width, target_height))
        else:
            continue

        h_resized, w_resized = resized_frame.shape[:2]
        top_left_y = max(0, center_y - h_resized // 2)
        top_left_x = max(0, center_x - w_resized // 2)
        bottom_right_y = min(h, center_y + h_resized // 2)
        bottom_right_x = min(w, center_x + w_resized // 2)

        cropped_frame = resized_frame[
            0 : bottom_right_y - top_left_y, 0 : bottom_right_x - top_left_x
        ]
        bg_img[top_left_y:bottom_right_y, top_left_x:bottom_right_x] = cropped_frame

    cv2.imshow("Phi.Slides v0.0.3", bg_img)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):  # Quit
        break
    elif key == ord('d'):  # Next slide
        switch_mode(1)
    elif key == ord('a'):  # Previous slide
        switch_mode(-1)
    elif key == ord('r'):  # Restart all videos in the current slide
        for content in frames:
            if isinstance(content, dict) and content.get("type") == "video":
                content["cap"].set(cv2.CAP_PROP_POS_FRAMES, 0)

cap.release()
for slide_frames in interactive_content:
    for content in slide_frames:
        if isinstance(content, dict) and content.get("type") == "video":
            content["cap"].release()
cv2.destroyAllWindows()
