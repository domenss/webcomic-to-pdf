"""PDF generation functionality."""

from pathlib import Path

import img2pdf


def create_pdf(image_paths: list[Path], output_path: Path) -> Path:
    """Create a PDF from images.
    
    Args:
        image_paths: List of paths to image files
        output_path: Path where PDF should be saved
        
    Returns:
        Path to the created PDF file
        
    Raises:
        ValueError: If no images are provided
    """
    if not image_paths:
        raise ValueError("No images provided")
    
    if not output_path.suffix == ".pdf":
        output_path = output_path.with_suffix(".pdf")
    
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert([str(p) for p in image_paths]))
    
    print(f"  PDF created: {output_path} ({len(image_paths)} pages)")
    return output_path
