"""
Render PPTX slides to PNG images for visual inspection using COM automation.
"""
import os
import win32com.client

def render_pptx(pptx_filename, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    abs_pptx = os.path.abspath(pptx_filename)
    abs_out = os.path.abspath(output_dir)
    
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    try:
        presentation = powerpoint.Presentations.Open(abs_pptx, WithWindow=False)
        for i, slide in enumerate(presentation.Slides):
            out_file = os.path.join(abs_out, f"slide_{i+1}.png")
            slide.Export(out_file, "PNG", 1920, 1080)
            print(f"Exported Slide {i+1} -> {out_file}")
        presentation.Close()
    finally:
        powerpoint.Quit()

if __name__ == '__main__':
    render_pptx('The_Asymmetric_Wave_Presentation_Deck_Championship.pptx', 'slide_previews_v3')
