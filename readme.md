# Phislides: Interactive Presentation Tool

Phislides allows you to enhance your PDF-based slides with videos or interactive demos using **AprilTag** markers.

## Usage

1. **Prepare Your Slides**  
   Create your presentation using any software you prefer.

2. **Add AprilTag Markers**  
   Insert the **AprilTag `tag36h11`** (provided as `tag.png` in this repository) where you want videos or interactive demos to appear.

3. **Render the Presentation**  
   Export your slides as a **PDF** file.

4. **Convert Your Slides**  
   Run the converter script to process the PDF:  
   ```bash
   python phislides_converter.py
   ```

5. **Use the main program to display the interactive slides**
   ```bash
   python phislides_main.py slides_directory
   ````

## Requirements

Install the dependencies using pip:

```bash
pip install pymupdf opencv-python numpy pyyaml tqdm
```
