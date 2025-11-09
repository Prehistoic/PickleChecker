from reportlab.lib import colors
from reportlab.platypus import Flowable


class PdfIcons(Flowable):
    """
    Small vector icon drawn directly on the PDF canvas to avoid emoji/font issues.
    icon_type: 'dir' | 'file' | 'hf' | 'gear' | 'download'
    """

    def __init__(self, icon_type: str, size: int = 36):
        super().__init__()
        self.icon_type = icon_type
        self.size = size
        self.width = size
        self.height = size

    def draw(self):
        c = self.canv
        s = self.size
        # Draw a folder icon
        if self.icon_type == "dir":
            c.setFillColor(colors.HexColor("#F5C542"))
            c.roundRect(0, s * 0.18, s * 0.9, s * 0.6, s * 0.06, stroke=0, fill=1)
            c.setFillColor(colors.HexColor("#E3A900"))
            c.roundRect(s * 0.02, s * 0.55, s * 0.35, s * 0.25, s * 0.04, stroke=0, fill=1)
            c.setStrokeColor(colors.HexColor("#C48A00"))
            c.roundRect(0, s * 0.18, s * 0.9, s * 0.6, s * 0.06, stroke=1, fill=0)

        # Draw a file/page icon
        elif self.icon_type == "file":
            c.setFillColor(colors.white)
            c.roundRect(0, 0, s * 0.7, s, s * 0.04, stroke=1, fill=1)
            c.setFillColor(colors.HexColor("#EFEFEF"))
            p = c.beginPath()
            p.moveTo(s * 0.46, s * 0.68)
            p.lineTo(s * 0.7, s)
            p.lineTo(s * 0.46, s)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
            c.setStrokeColor(colors.HexColor("#CCCCCC"))
            c.roundRect(0, 0, s * 0.7, s, s * 0.04, stroke=1, fill=0)

        # Draw a huggingface-like circle icon (smiley) for HF models
        elif self.icon_type == "hf":
            c.setFillColor(colors.HexColor("#FFD54F"))
            c.circle(s * 0.35, s * 0.5, s * 0.45, stroke=0, fill=1)
            c.setFillColor(colors.HexColor("#5D4037"))
            c.circle(s * 0.24, s * 0.62, s * 0.05, stroke=0, fill=1)
            c.circle(s * 0.46, s * 0.62, s * 0.05, stroke=0, fill=1)
            c.setStrokeColor(colors.HexColor("#5D4037"))
            c.setLineWidth(1.5)
            c.arc(s * -0.05, s * 0.25, s * 0.75, s * 0.75, startAng=200, extent=140)

        # Simple gear icon (for Scanner Results header)
        elif self.icon_type == "gear":
            c.setStrokeColor(colors.HexColor("#444444"))
            c.setFillColor(colors.HexColor("#CCCCCC"))
            # central circle
            c.circle(s * 0.5, s * 0.5, s * 0.18, stroke=1, fill=1)
            # 8 small teeth as rotated rectangles
            for i in range(8):
                angle = i * 45
                c.saveState()
                c.translate(s * 0.5, s * 0.5)
                c.rotate(angle)
                c.rect(s * 0.28, -s * 0.03, s * 0.08, s * 0.06, stroke=0, fill=1)
                c.restoreState()
            c.setStrokeColor(colors.HexColor("#666666"))
            c.circle(s * 0.5, s * 0.5, s * 0.22, stroke=1, fill=0)

        # Simple download icon (for Global Imports header)
        elif self.icon_type == "download":
            c.setStrokeColor(colors.HexColor("#444444"))
            c.setFillColor(colors.HexColor("#CCCCCC"))
            # box
            c.rect(s * 0.1, s * 0.25, s * 0.8, s * 0.5, stroke=1, fill=1)
            # arrow stem
            c.setFillColor(colors.HexColor("#444444"))
            c.rect(s * 0.45, s * 0.55, s * 0.1, s * 0.18, stroke=0, fill=1)
            # arrow head (triangle)
            p = c.beginPath()
            p.moveTo(s * 0.35, s * 0.55)
            p.lineTo(s * 0.65, s * 0.55)
            p.lineTo(s * 0.5, s * 0.35)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
