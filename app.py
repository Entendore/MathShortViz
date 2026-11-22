import sys
import numpy as np
import itertools
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, 
    QPushButton, QMessageBox, QLineEdit, QLabel, QSpinBox, QFormLayout, QFrame
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation

class MathShortsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Shorts Math Generator")
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.setGeometry(100, 100, 1000, 700)

        # Main Widget and Layout (Horizontal split)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- LEFT PANEL: Controls ---
        left_panel = QFrame()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet("background-color: #2b2b2b; padding: 15px;")
        form_layout = QFormLayout(left_panel)

        # Inputs
        self.input_term = QLineEdit("(1/(2*k+1)) * sin((2*k+1)*x)")
        self.input_term.setToolTip("Use 'x' for the x-axis and 'k' for the current term. Supports sin, cos, pi, etc.")
        
        self.input_mult = QLineEdit("6")
        self.input_max_terms = QSpinBox()
        self.input_max_terms.setMinimum(1)
        self.input_max_terms.setMaximum(50)
        self.input_max_terms.setValue(12)
        
        self.input_top_text = QLineEdit("Why is this\nSO satisfying? :) :) :)")

        # Styling inputs
        input_style = "background-color: #3c3c3c; color: white; border: 1px solid #555; padding: 5px; border-radius: 3px;"
        for widget in [self.input_term, self.input_mult, self.input_top_text]:
            widget.setStyleSheet(input_style)
        self.input_max_terms.setStyleSheet(input_style)

        form_layout.addRow(QLabel("Equation Term (use x, k):"), self.input_term)
        form_layout.addRow(QLabel("Multiplier:"), self.input_mult)
        form_layout.addRow(QLabel("Max Terms (k):"), self.input_max_terms)
        form_layout.addRow(QLabel("Top Text:"), self.input_top_text)

        # Buttons
        self.btn_apply = QPushButton("Apply & Preview")
        self.btn_apply.setStyleSheet("background-color: #007acc; color: white; padding: 10px; font-weight: bold; border-radius: 4px;")
        self.btn_apply.clicked.connect(self.apply_settings)
        form_layout.addRow(self.btn_apply)

        self.btn_export = QPushButton("Generate MP4 (Shorts)")
        self.btn_export.setStyleSheet("background-color: #FF0000; color: white; padding: 15px; font-weight: bold; border-radius: 4px; margin-top: 20px;")
        self.btn_export.clicked.connect(self.generate_mp4)
        form_layout.addRow(self.btn_export)

        main_layout.addWidget(left_panel)

        # --- RIGHT PANEL: Matplotlib Canvas ---
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: black;")
        canvas_layout = QVBoxLayout(right_panel)
        canvas_layout.setContentsMargins(0, 0, 0, 0)

        self.fig = Figure(figsize=(9, 16), dpi=100, facecolor='black')
        self.canvas = FigureCanvas(self.fig)
        canvas_layout.addWidget(self.canvas, stretch=1)
        
        main_layout.addWidget(right_panel, stretch=1)

        # State variables
        self.current_term_expr = self.input_term.text()
        self.current_mult = float(self.input_mult.text())
        self.current_max_terms = self.input_max_terms.value()
        
        self.t = 0 # Animation step counter
        self.setup_plot()

    def setup_plot(self):
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('black')
        self.ax.set_xlim(-np.pi, np.pi)
        self.ax.set_ylim(-10, 10) # Default limits, can be expanded
        self.ax.axis('off')

        self.x = np.linspace(-np.pi, np.pi, 2000)
        self.line, = self.ax.plot(self.x, np.zeros_like(self.x), color='#FFE800', linewidth=3)

        self.dialog_text = self.fig.text(
            0.15, 0.85, self.input_top_text.text(), 
            color='black', fontsize=18, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.8", facecolor="white", edgecolor="none")
        )

        # Animation setup using an infinite generator
        self.anim = animation.FuncAnimation(
            self.fig, self.update_wave, frames=self.frame_generator, interval=30, blit=False, save_count=300
        )

    def frame_generator(self):
        """Infinite generator for ping-pong animation effect"""
        while True:
            max_k = self.current_max_terms
            cycle = max_k * 2
            step = self.t % cycle
            
            if step < max_k:
                frame = step + 1
            else:
                frame = cycle - step + 1
            
            yield max(1, int(frame))
            self.t += 1

    def update_wave(self, frame):
        """Calculates the custom Fourier series for the current frame"""
        try:
            y = np.zeros_like(self.x)
            # Calculate sum based on the current frame (k)
            for k in range(1, frame + 1):
                # Safe evaluation environment
                safe_dict = {
                    "sin": np.sin, "cos": np.cos, "tan": np.tan, 
                    "pi": np.pi, "x": self.x, "k": k
                }
                term_val = float(self.current_mult) * eval(self.current_term_expr, {"__builtins__": {}}, safe_dict)
                y += term_val
            
            self.line.set_ydata(y)
        except Exception as e:
            # If math fails, keep line at 0 so animation doesn't crash
            self.line.set_ydata(np.zeros_like(self.x))
            
        return self.line,

    def apply_settings(self):
        """Applies UI settings to the plot"""
        try:
            self.current_mult = float(self.input_mult.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Multiplier must be a number.")
            return

        # Test the equation to make sure it's valid before applying
        try:
            safe_dict = {"sin": np.sin, "cos": np.cos, "tan": np.tan, "pi": np.pi, "x": self.x, "k": 1}
            eval(self.input_term.text(), {"__builtins__": {}}, safe_dict)
        except Exception as e:
            QMessageBox.warning(self, "Equation Error", f"Invalid equation syntax:\n{str(e)}")
            return

        # Apply settings
        self.current_term_expr = self.input_term.text()
        self.current_max_terms = self.input_max_terms.value()
        self.dialog_text.set_text(self.input_top_text.text())
        self.t = 0 # Reset animation
        
        self.canvas.draw_idle()

    def generate_mp4(self):
        """Exports the animation to an MP4 file"""
        self.btn_export.setText("Generating MP4... Please Wait")
        self.btn_export.setEnabled(False)
        QApplication.processEvents()

        try:
            output_file = "math_shorts_video.mp4"
            # Save 240 frames (approx 8 seconds at 30fps) - perfect for a Short
            self.anim.save(
                output_file, 
                writer='ffmpeg', 
                fps=30, 
                dpi=120, # 9x16 * 120dpi = 1080x1920
                savefig_kwargs={'facecolor': 'black'},
                frames=240 
            )
            QMessageBox.information(self, "Success", f"MP4 successfully generated as {output_file}!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate MP4.\nMake sure FFmpeg is installed.\n\nError: {str(e)}")
        
        self.btn_export.setText("Generate MP4 (Shorts)")
        self.btn_export.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MathShortsApp()
    window.show()
    sys.exit(app.exec())