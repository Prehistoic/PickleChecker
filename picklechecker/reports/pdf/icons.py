"""
Module for loading and displaying icons in PDF reports.
"""

from pathlib import Path
from reportlab.lib import colors  # type: ignore
from reportlab.platypus import Flowable  # type: ignore


class PdfIcons(Flowable):
    """
    Icon displayed from image files stored in the data/icons/ directory.
    Falls back to vector drawing if image not found.
    icon_type: 'dir' | 'file' | 'hf'
    """

    def __init__(self, icon_type: str, size: int = 36):
        """
        Initializes the icon with type and size.

        Args:
            icon_type (str): The type of icon ('dir', 'file', 'hf').
            size (int): The size of the icon in points.
        """
        super().__init__()
        self.icon_type = icon_type
        self.size = size
        self.width = size
        self.height = size
        
        # Get path to icon image
        icons_dir = Path(__file__).parent.parent.parent / "data" / "icons"
        self.icon_path = icons_dir / f"{icon_type}.png"
        
        # Check if image exists
        if not self.icon_path.exists():
            self.icon_path = None

    def draw(self) -> None:
        """
        Draws the icon on the PDF canvas.
        Uses image if available, otherwise falls back to vector drawing.
        """
        if self.icon_path:
            self._draw_image()
        else:
            self._draw_vector()

    def _draw_image(self) -> None:
        """
        Draws the icon from an image file.
        """
        from reportlab.lib.utils import ImageReader
        
        c = self.canv
        s = self.size
        
        try:
            img = ImageReader(str(self.icon_path))
            # Draw image scaled to exactly the icon size
            c.drawImage(img, 0, 0, width=s, height=s, preserveAspectRatio=True, mask='auto')
        except Exception:
            # If image loading fails, fall back to vector drawing
            self._draw_vector()

    def _draw_vector(self) -> None:
        """
        Draws the icon as vector graphics (fallback).
        """
        c = self.canv
        s = self.size

        # Draw a folder icon
        if self.icon_type == "dir":
            # Main folder body
            c.setFillColor(colors.HexColor("#F5C542"))
            c.roundRect(0, s * 0.18, s * 0.9, s * 0.6, s * 0.06, stroke=0, fill=1)
            # Folder tab
            c.setFillColor(colors.HexColor("#E3A900"))
            c.roundRect(s * 0.02, s * 0.55, s * 0.35, s * 0.25, s * 0.04, stroke=0, fill=1)
            # Outline
            c.setStrokeColor(colors.HexColor("#C48A00"))
            c.roundRect(0, s * 0.18, s * 0.9, s * 0.6, s * 0.06, stroke=1, fill=0)

        # Draw a file/page icon
        elif self.icon_type == "file":
            # Main file body
            c.setFillColor(colors.white)
            c.roundRect(0, 0, s * 0.7, s, s * 0.04, stroke=1, fill=1)
            # Folded corner
            c.setFillColor(colors.HexColor("#EFEFEF"))
            p = c.beginPath()
            p.moveTo(s * 0.46, s * 0.68)
            p.lineTo(s * 0.7, s)
            p.lineTo(s * 0.46, s)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
            # Outline
            c.setStrokeColor(colors.HexColor("#CCCCCC"))
            c.roundRect(0, 0, s * 0.7, s, s * 0.04, stroke=1, fill=0)

        # Draw a huggingface-like circle icon (smiley) for HF models
        elif self.icon_type == "hf":
            # Face circle
            c.setFillColor(colors.HexColor("#FFD54F"))
            c.circle(s * 0.35, s * 0.5, s * 0.45, stroke=0, fill=1)
            # Eyes
            c.setFillColor(colors.HexColor("#5D4037"))
            c.circle(s * 0.24, s * 0.62, s * 0.05, stroke=0, fill=1)
            c.circle(s * 0.46, s * 0.62, s * 0.05, stroke=0, fill=1)
            # Smile
            c.setStrokeColor(colors.HexColor("#5D4037"))
            c.setLineWidth(1.5)
            c.arc(s * -0.05, s * 0.25, s * 0.75, s * 0.75, startAng=200, extent=140)
