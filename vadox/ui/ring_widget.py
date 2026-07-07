import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QConicalGradient


class RingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.angles = [0, 0, 0]
        self.speeds = [0.8, -0.5, 0.3]
        self.listening = False
        self.speaking = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def _tick(self):
        for i in range(3):
            self.angles[i] = (self.angles[i] + self.speeds[i]) % 360
        self.update()

    def set_state(self, listening=False, speaking=False):
        self.listening = listening
        self.speaking = speaking

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        base_r = min(w, h) // 2 - 10

        if self.speaking:
            arc_color = QColor(0, 255, 136)
        elif self.listening:
            arc_color = QColor(255, 60, 120)
        else:
            arc_color = QColor(0, 200, 255)

        rings = [
            (base_r,       QColor(0, 200, 255, 30),  arc_color,         1.5, 80,  self.angles[0]),
            (base_r - 22,  QColor(255, 0, 170, 25),  QColor(255, 0, 170), 1.2, 60, self.angles[1]),
            (base_r - 44,  QColor(0, 255, 204, 20),  QColor(0, 255, 204), 1.0, 40, self.angles[2]),
        ]

        for radius, dash_color, arc_color_r, width, arc_span, angle in rings:
            rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

            pen = QPen(dash_color, width)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawEllipse(rect)

            pen2 = QPen(arc_color_r, width + 0.5)
            pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen2)
            painter.drawArc(rect, int(angle * 16), int(arc_span * 16))

        center_r = base_r - 70
        center_rect = QRectF(cx - center_r, cy - center_r, center_r * 2, center_r * 2)
        pen3 = QPen(QColor(10, 48, 96), 2)
        painter.setPen(pen3)
        painter.setBrush(QColor(6, 15, 30))
        painter.drawEllipse(center_rect)

        painter.end()
