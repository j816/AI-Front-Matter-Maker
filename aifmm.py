import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QTabWidget, 
                             QFileDialog, QMessageBox, QDoubleSpinBox, QSpinBox, QComboBox, 
                             QGroupBox, QFormLayout, QSlider, QSizePolicy, QListWidget, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os
import tempfile
import json
import configparser
from api_services import get_service, get_available_services

# Constants
API_CONFIG_FILE = 'api_config.json'
DEFAULT_MODEL = "claude-3-opus-20240229"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.0

def handle_error(error_code, message):
    print(f"Error {error_code}: {message}")
    return error_code

def load_api_config():
    default_config = {
        'anthropic_api_key': '',
        'openai_api_key': '',
        'temperature': DEFAULT_TEMPERATURE,
        'service': 'Anthropic',
        'model': DEFAULT_MODEL
    }
    if not os.path.exists(API_CONFIG_FILE):
        # If the file doesn't exist, create it with default values
        with open(API_CONFIG_FILE, 'w') as f:
            json.dump(default_config, f)
        return default_config
    else:
        # If the file exists, load it and use saved values
        with open(API_CONFIG_FILE, 'r') as f:
            return json.load(f)

def save_api_config(anthropic_api_key: str, openai_api_key: str, temperature: float, service: str, model: str):
    current_config = load_api_config()
    # Only update non-empty values
    if anthropic_api_key:
        current_config['anthropic_api_key'] = anthropic_api_key
    if openai_api_key:
        current_config['openai_api_key'] = openai_api_key
    current_config['temperature'] = temperature
    current_config['service'] = service
    current_config['model'] = model
    
    with open(API_CONFIG_FILE, 'w') as f:
        json.dump(current_config, f)

class ProcessThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, gui, prompt_file, text_files, output_dir):
        super().__init__()
        self.gui = gui
        self.prompt_file = prompt_file
        self.text_files = text_files
        self.output_dir = output_dir
        self.reference = gui.reference_entry.text()
        self.model = gui.model_combo.currentText()
        self.max_tokens = min(gui.max_tokens_slider.value(), 4096)
        self.temperature = gui.temperature_slider.value() / 100
        self.service = get_service(gui.service_combo.currentText(), gui.get_current_api_key())

    def run(self):
        if not self.validate_input(self.prompt_file, self.text_files, self.output_dir):
            return

        self.log_signal.emit("Processing started...")
        try:
            for text_file in self.text_files:
                self.log_signal.emit(f"Processing file: {text_file}")
                self.process_single_file(self.prompt_file, text_file, self.output_dir)
            self.log_signal.emit("Processing complete!")
        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")
        finally:
            self.finished_signal.emit()

    def process_single_file(self, prompt_file, text_file, output_dir):
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as temp_file:
            merged_content = self.merge_prompt_and_text(prompt_file, text_file)
            temp_file.write(merged_content)
            temp_file.flush()

            api_response = self.call_api(temp_file.name)

        markdown_content = self.convert_to_markdown(api_response)
        if markdown_content:
            base_name = os.path.splitext(os.path.basename(text_file))[0]
            output_file = os.path.join(output_dir, f"{base_name}.md")
            self.append_markdown_to_file(markdown_content, text_file, output_file)
            self.log_signal.emit(f"Markdown content appended to {output_file}")
        else:
            self.log_signal.emit("No valid content found in the API response.")

        os.unlink(temp_file.name)

    def merge_prompt_and_text(self, prompt_path: str, text_path: str) -> str:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
        
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return prompt.replace('{{TEXT}}', text)

    def call_api(self, input_file: str) -> str:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.service.call_api(content, self.model, self.max_tokens, self.temperature)

    def convert_to_markdown(self, content: str) -> str:
        return content.strip()

    def append_markdown_to_file(self, markdown_content: str, original_file: str, output_file: str):
        with open(original_file, 'r', encoding='utf-8') as original:
            original_content = original.read()
        
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write(markdown_content + "\n\n")
            if self.reference and self.reference.strip():
                output.write(f"Reference: {self.reference.strip()}\n\n")
            output.write(original_content)

    def validate_input(self, prompt_file, text_files, output_dir):
        if not prompt_file or not text_files or not output_dir:
            QMessageBox.critical(self.gui, "Error", "Please select all required files and directories.")
            return False
        if not os.path.exists(prompt_file):
            QMessageBox.critical(self.gui, "Error", f"Prompt file not found: {prompt_file}")
            return False
        for text_file in text_files:
            if not os.path.exists(text_file):
                QMessageBox.critical(self.gui, "Error", f"Text file not found: {text_file}")
                return False
        if not os.path.exists(output_dir):
            QMessageBox.critical(self.gui, "Error", f"Output directory not found: {output_dir}")
            return False
        return True

class AIFrontMatterMaker(QMainWindow):  # Changed class name
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Front-Matter Maker")  # Updated window title
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.main_tab = QWidget()
        self.settings_tab = QWidget()
        self.tab_widget.addTab(self.main_tab, "Main")
        self.tab_widget.addTab(self.settings_tab, "Settings")

        self.setup_main_tab()
        self.setup_settings_tab()

        api_config = load_api_config()
        self.api_key_entry.setText(api_config.get('anthropic_api_key', ''))
        self.openai_api_key_entry.setText(api_config.get('openai_api_key', ''))
        self.temperature_slider.setValue(int(api_config.get('temperature', DEFAULT_TEMPERATURE) * 100))
        self.service_combo.setCurrentText(api_config.get('service', 'Anthropic'))
        self.update_available_models()
        self.model_combo.setCurrentText(api_config.get('model', DEFAULT_MODEL))

    def setup_main_tab(self):
        layout = QVBoxLayout(self.main_tab)

        prompt_layout = QHBoxLayout()
        self.prompt_label = QLabel("Prompt File:")
        self.prompt_entry = QLineEdit()
        self.prompt_button = QPushButton("Browse")
        prompt_layout.addWidget(self.prompt_label)
        prompt_layout.addWidget(self.prompt_entry)
        prompt_layout.addWidget(self.prompt_button)
        layout.addLayout(prompt_layout)

        # Use QListWidget for displaying selected files
        self.text_list_widget = QListWidget()
        self.text_list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.text_list_widget)

        # Add buttons for adding and removing files
        file_buttons_layout = QHBoxLayout()
        self.add_file_button = QPushButton("Add Files")
        self.remove_file_button = QPushButton("Remove Selected")
        file_buttons_layout.addWidget(self.add_file_button)
        file_buttons_layout.addWidget(self.remove_file_button)
        layout.addLayout(file_buttons_layout)

        output_layout = QHBoxLayout()
        self.output_label = QLabel("Output Directory:")
        self.output_entry = QLineEdit()
        self.output_button = QPushButton("Browse")
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_entry)
        output_layout.addWidget(self.output_button)
        layout.addLayout(output_layout)

        reference_layout = QHBoxLayout()
        self.reference_label = QLabel("Reference:")
        self.reference_entry = QLineEdit()
        reference_layout.addWidget(self.reference_label)
        reference_layout.addWidget(self.reference_entry)
        layout.addLayout(reference_layout)

        self.process_button = QPushButton("Process")
        layout.addWidget(self.process_button)

        # Add a progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        layout.addWidget(self.log_window)

        button_layout = QHBoxLayout()
        self.save_config_button = QPushButton("Save Config")
        self.load_config_button = QPushButton("Load Config")
        button_layout.addWidget(self.save_config_button)
        button_layout.addWidget(self.load_config_button)
        layout.addLayout(button_layout)

        # Connect signals
        self.prompt_button.clicked.connect(self.browse_prompt)
        self.add_file_button.clicked.connect(self.browse_text)
        self.remove_file_button.clicked.connect(self.remove_selected_files)
        self.output_button.clicked.connect(self.browse_output)
        self.process_button.clicked.connect(self.start_process)
        self.save_config_button.clicked.connect(self.save_config)
        self.load_config_button.clicked.connect(self.load_config)

        # Enable drag-and-drop
        self.text_list_widget.setAcceptDrops(True)
        self.text_list_widget.dragEnterEvent = self.dragEnterEvent
        self.text_list_widget.dropEvent = self.dropEvent

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.text_list_widget.addItem(file_path)

    def browse_text(self):
        filenames, _ = QFileDialog.getOpenFileNames(self, "Select Text File(s)", "", "Text Files (*.txt)")
        if filenames:
            self.text_list_widget.addItems(filenames)

    def remove_selected_files(self):
        for item in self.text_list_widget.selectedItems():
            self.text_list_widget.takeItem(self.text_list_widget.row(item))

    def browse_prompt(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Prompt File", "", "Text Files (*.txt)")
        if filename:
            self.prompt_entry.setText(filename)

    def browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_entry.setText(directory)

    def start_process(self):
        self.process_button.setEnabled(False)
        prompt_file = self.prompt_entry.text()
        text_files = [self.text_list_widget.item(i).text() for i in range(self.text_list_widget.count())]
        output_dir = self.output_entry.text()
        self.process_thread = ProcessThread(self, prompt_file, text_files, output_dir)
        self.process_thread.log_signal.connect(self.log)
        self.process_thread.finished_signal.connect(self.on_process_finished)
        self.process_thread.start()

    def on_process_finished(self):
        self.process_button.setEnabled(True)
        self.progress_bar.setValue(0)

    def log(self, message):
        self.log_window.append(message)
        # Update progress bar based on log messages
        if "Processing file:" in message:
            current_value = self.progress_bar.value()
            self.progress_bar.setValue(current_value + 1)

    def setup_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)

        # Create a form layout for better organization
        form_layout = QFormLayout()

        # API Keys section
        api_keys_group = QGroupBox("API Keys")
        api_keys_layout = QFormLayout()
        
        self.api_key_entry = QLineEdit()
        api_keys_layout.addRow("Anthropic API Key:", self.api_key_entry)
        
        self.openai_api_key_entry = QLineEdit()
        api_keys_layout.addRow("OpenAI API Key:", self.openai_api_key_entry)
        
        api_keys_group.setLayout(api_keys_layout)
        form_layout.addRow(api_keys_group)

        # Model Selection section
        model_group = QGroupBox("Model Selection")
        model_layout = QFormLayout()
        
        self.service_combo = QComboBox()
        self.service_combo.addItems(get_available_services())
        self.service_combo.currentTextChanged.connect(self.on_service_changed)
        model_layout.addRow("API Service:", self.service_combo)
        
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.update_max_tokens)
        model_layout.addRow("Model:", self.model_combo)
        
        model_group.setLayout(model_layout)
        form_layout.addRow(model_group)

        # Parameters section
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout()
        
        self.max_tokens_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_tokens_slider.setRange(1, 4096)
        self.max_tokens_slider.setValue(4096)
        self.max_tokens_slider.valueChanged.connect(self.update_max_tokens_display)
        self.max_tokens_display = QLabel(str(self.max_tokens_slider.value()))
        params_layout.addRow("Max Tokens:", self.max_tokens_slider)
        params_layout.addRow("Max Tokens Value:", self.max_tokens_display)
        
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 100)
        self.temperature_slider.setValue(int(DEFAULT_TEMPERATURE * 100))
        self.temperature_slider.valueChanged.connect(self.update_temperature_display)
        self.temperature_display = QLabel(str(self.temperature_slider.value() / 100))
        params_layout.addRow("Temperature:", self.temperature_slider)
        params_layout.addRow("Temperature Value:", self.temperature_display)
        
        params_group.setLayout(params_layout)
        form_layout.addRow(params_group)

        layout.addLayout(form_layout)

        # Save Settings button
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_settings_button)

        # Initialize available models
        self.update_available_models()

    def update_max_tokens_display(self):
        self.max_tokens_display.setText(str(self.max_tokens_slider.value()))

    def update_temperature_display(self):
        self.temperature_display.setText(str(self.temperature_slider.value() / 100))

    def update_max_tokens(self):
        service = get_service(self.service_combo.currentText(), self.get_current_api_key())
        model = self.model_combo.currentText()
        max_tokens = service.get_max_tokens(model)
        
        # Set the maximum tokens based on the service's response
        self.max_tokens_slider.setMaximum(max_tokens)
        self.max_tokens_slider.setValue(max_tokens)

    def on_service_changed(self, service: str):
        self.update_available_models()
        self.update_max_tokens()

    def update_available_models(self):
        self.model_combo.clear()
        service = get_service(self.service_combo.currentText(), self.get_current_api_key())
        self.model_combo.addItems(service.get_available_models())
        self.update_max_tokens()

    def get_current_api_key(self) -> str:
        if self.service_combo.currentText() == "Anthropic":
            return self.api_key_entry.text()
        elif self.service_combo.currentText() == "OpenAI":
            return self.openai_api_key_entry.text()
        return ""

    def save_config(self):
        config = configparser.ConfigParser()
        config['Paths'] = {
            'prompt_file': self.prompt_entry.text(),
            'text_files': ';'.join([self.text_list_widget.item(i).text() for i in range(self.text_list_widget.count())]),
            'output_dir': self.output_entry.text(),
            'reference': self.reference_entry.text()
        }
        config['API'] = {
            'anthropic_api_key': self.api_key_entry.text(),
            'openai_api_key': self.openai_api_key_entry.text(),
            'service': self.service_combo.currentText(),
            'model': self.model_combo.currentText(),
            'max_tokens': str(self.max_tokens_slider.value()),
            'temperature': str(self.temperature_slider.value() / 100)
        }
        config['Reference'] = {
            'reference': self.reference_entry.text()
        }
        
        filename, _ = QFileDialog.getSaveFileName(self, "Save Config", "", "INI Files (*.ini)")
        if filename:
            with open(filename, 'w') as configfile:
                config.write(configfile)
            self.log(f"Configuration saved to {filename}")

    def load_config(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "INI Files (*.ini)")
        if filename:
            config = configparser.ConfigParser()
            config.read(filename)
            
            # Update only the main tab fields
            self.prompt_entry.setText(config['Paths'].get('prompt_file', ''))
            self.text_list_widget.clear()
            self.text_list_widget.addItems(config['Paths'].get('text_files', '').split(';'))
            self.output_entry.setText(config['Paths'].get('output_dir', ''))
            self.reference_entry.setText(config['Paths'].get('reference', ''))
            
            # Log the configuration load
            self.log(f"Configuration loaded from {filename}")

    def save_settings(self):
        anthropic_api_key = self.api_key_entry.text()
        openai_api_key = self.openai_api_key_entry.text()
        temperature = self.temperature_slider.value() / 100
        service = self.service_combo.currentText()
        model = self.model_combo.currentText()
        save_api_config(anthropic_api_key, openai_api_key, temperature, service, model)
        self.log("Settings saved")

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    gui = AIFrontMatterMaker()  # Updated instantiation
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()