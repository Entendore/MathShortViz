import sys
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, 
    QPushButton, QMessageBox, QPlainTextEdit, QLineEdit, QSpinBox, QFormLayout, QFrame, QLabel
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation

class MathShortsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Shorts Math Generator - Multi Equation")
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.setGeometry(100, 100, 1100, 750)

        # Main Widget and Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- LEFT PANEL: Controls ---
        left_panel = QFrame()
        left_panel.setFixedWidth(400)
        left_panel.setStyleSheet("background-color: #2b2b2b; padding: 15px;")
        form_layout = QFormLayout(left_panel)

        # Inputs
        self.input_terms = QPlainTextEdit()
        self.input_terms.setPlainText(
            "(1/(2*k+1)) * sin((2*k+1)*x)\n"
            "(1/k) * sin(k*x)\n"
            "(1/k**2) * cos(k*x)"
        )
        self.input_terms.setMinimumHeight(100)
        self.input_terms.setToolTip("Enter one equation per line. Use 'x' for the axis and 'k' for the term. Supports sin, cos, pi, etc.")

        self.input_mult = QLineEdit("6")
        self.input_max_terms = QSpinBox()
        self.input_max_terms.setMinimum(1)
        self.input_max_terms.setMaximum(50)
        self.input_max_terms.setValue(12)
        
        self.input_top_text = QLineEdit("Why is this\nSO satisfying? :) :) :)")

        # Styling inputs
        input_style = "background-color: #3c3c3c; color: white; border: 1px solid #555; padding: 5px; border-radius: 3px;"
        for widget in [self.input_terms, self.input_mult, self.input_top_text]:
            widget.setStyleSheet(input_style)
        self.input_max_terms.setStyleSheet(input_style)

        form_layout.addRow(QLabel("Equations (one per line):"), self.input_terms)
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
        self.equations = []
        self.current_mult = 6.0
        self.current_max_terms = 12
        
        self.t = 0 # Animation step counter
        self.setup_plot()
        self.apply_settings() # Load initial defaults

    def setup_plot(self):
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('black')
        self.ax.set_xlim(-np.pi, np.pi)
        self.ax.set_ylim(-10, 10)
        self.ax.axis('off')

        self.x = np.linspace(-np.pi, np.pi, 2000)
        
        # Plot line (with alpha for fading transitions)
        self.line, = self.ax.plot(self.x, np.zeros_like(self.x), color='#FFE800', linewidth=3, alpha=1.0)

        self.dialog_text = self.fig.text(
            0.15, 0.85, "Top Text", 
            color='black', fontsize=18, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.8", facecolor="white", edgecolor="none")
        )

        # Dynamic Formula Text
        self.formula_text = self.fig.text(
            0.5, 0.15, "", 
            color='white', fontsize=16, ha='center'
        )

        # Animation setup
        self.anim = animation.FuncAnimation(
            self.fig, self.update_wave, frames=self.frame_generator, 
            interval=30, blit=False, save_count=1000
        )

    def frame_generator(self):
        """Infinite generator that cycles through equations and handles fade in/out"""
        while True:
            if not self.equations:
                yield ("", 1, 0.0)
                continue

            for eq_str in self.equations:
                # 1. Build up phase (k = 1 to max_terms)
                for k in range(1, self.current_max_terms + 1):
                    yield (eq_str, k, 1.0) # (equation, current_k, alpha)
                
                # 2. Hold phase (keep max terms for a moment)
                for _ in range(15): 
                    yield (eq_str, self.current_max_terms, 1.0)
                
                # 3. Fade out phase
                for fade_step in np.linspace(1.0, 0.0, 10):
                    yield (eq_str, self.current_max_terms, fade_step)

    def update_wave(self, frame_data):
        """Calculates the custom Fourier series for the current frame"""
        eq_str, frame, alpha = frame_data
        
        try:
            # Update formula text dynamically
            display_eq = eq_str.replace("*", " ") # Make it look a bit cleaner on screen
            self.formula_text.set_text(f"y = {self.current_mult} * Σ ( {display_eq} )")
            
            # Update line transparency for transitions
            self.line.set_alpha(alpha)
            
            if alpha > 0.0:
                y = np.zeros_like(self.x)
                for k in range(1, frame + 1):
                    safe_dict = {
                        "sin": np.sin, "cos": np.cos, "tan": np.tan, 
                        "pi": np.pi, "x": self.x, "k": k
                    }
                    term_val = float(self.current_mult) * eval(eq_str, {"__builtins__": {}}, safe_dict)
                    y += term_val
                self.line.set_ydata(y)
            else:
                self.line.set_ydata(np.zeros_like(self.x))
                
        except Exception as e:
            self.line.set_ydata(np.zeros_like(self.x))
            
        return self.line,

    def apply_settings(self):
        """Applies UI settings to the plot"""
        try:
            self.current_mult = float(self.input_mult.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Multiplier must be a number.")
            return

        # Parse and validate all equations
        raw_lines = self.input_terms.toPlainText().split('\n')
        self.equations = [line.strip() for line in raw_lines if line.strip()]
        
        if not self.equations:
            QMessageBox.warning(self, "Input Error", "Please enter at least one equation.")
            return

        for eq in self.equations:
            try:
                safe_dict = {"sin": np.sin, "cos": np.cos, "tan": np.tan, "pi": np.pi, "x": self.x, "k": 1}
                eval(eq, {"__builtins__": {}}, safe_dict)
            except Exception as e:
                QMessageBox.warning(self, "Equation Error", f"Invalid equation syntax:\n'{eq}'\n\nError: {str(e)}")
                return

        # Apply remaining settings
        self.current_max_terms = self.input_max_terms.value()
        self.dialog_text.set_text(self.input_top_text.text())
        self.t = 0 # Reset animation
        
        self.canvas.draw_idle()

    def generate_mp4(self):
        """Exports the animation to an MP4 file"""
        if not self.equations:
            QMessageBox.warning(self, "Error", "No equations applied to export.")
            return

        self.btn_export.setText("Generating MP4... Please Wait")
        self.btn_export.setEnabled(False)
        QApplication.processEvents()

        try:
            output_file = "math_shorts_video.mp4"
            
            # Calculate total frames for exactly 1 full cycle of all equations
            # (build up + hold + fade out) per equation
            frames_per_eq = self.current_max_terms + 15 + 10
            total_frames = len(self.equations) * frames_per_eq
            
            self.anim.save(
                output_file, 
                writer='ffmpeg', 
                fps=30, 
                dpi=120, # 9x16 * 120dpi = 1080x1920
                savefig_kwargs={'facecolor': 'black'},
                frames=total_frames 
            )
            QMessageBox.information(self, "Success", f"MP4 successfully generated as {output_file}!\nLength: {total_frames/30:.1f} seconds")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate MP4.\nMake sure FFmpeg is installed.\n\nError: {str(e)}")
        
        self.btn_export.setText("Generate MP4 (Shorts)")
        self.btn_export.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MathShortsApp()
    window.show()
    sys.exit(app.exec())