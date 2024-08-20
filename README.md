# AI Front-Matter Maker

AI Front-Matter Maker is a PyQt6-based GUI application designed to help you generate markdown files with YAML front matter (or whatever else you want at the top of a text file. It depends on your prompt). This tool is particularly useful for quickly importing structured data into markdown files, allowing you to efficiently sort through and manage multiple documents in something like Obsidian, or DevonThink.

## Features

- **Drag-and-Drop Interface**: Easily add text files to be processed.
- **API Integration**: Supports both Anthropic and OpenAI services for generating content.
- **Customizable Parameters**: Adjust model, max tokens, and temperature settings.
- **Configuration Management**: Save and load API keys and settings.
- **Batch Processing**: Process multiple text files in one go.

<img width="808" alt="Main Settings" src="https://github.com/user-attachments/assets/61615713-5149-43f2-8873-ba22f9715eb4">
<img width="807" alt="API Settings" src="https://github.com/user-attachments/assets/aff55b14-17c7-4d0b-8b72-ab9298a878fe">


## Installation

### Prerequisites

- Python 3.8 or higher
- [PyQt6]
- [Anthropic]
- [OpenAI]

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/ai-front-matter-maker.git
   cd ai-front-matter-maker
   ```

2. **Install Dependencies**

   Use pip to install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**

   Execute the main script:

   ```bash
   python aifmm.py
   ```

## Usage

### Setting Up

1. **API Keys**: Enter your Anthropic and OpenAI API keys in the "Settings" tab.
2. **Model Selection**: Choose the desired API service and model.
3. **Parameters**: Adjust the max tokens and temperature sliders as needed.

### Processing Files

1. **Add Files**: Use the "Add Files" button or drag-and-drop text files into the main window.
2. **Select Prompt File**: Click "Browse" next to the "Prompt File" field to select a prompt template.
3. **Output Directory**: Choose where the processed markdown files will be saved.
4. **Reference**: Optionally, add a reference note to be included in the markdown files.
5. **Start Processing**: Click "Process" to begin generating markdown files.

### Example Workflow

1. **Prepare a Prompt Template**: Create a text file with placeholders, e.g., `{{TEXT}}`, to be replaced with content from your text files.
2. **Load Text Files**: Add multiple text files that you want to process.
3. **Generate Markdown**: The application will merge the prompt with each text file, call the API, and save the output as markdown files with YAML front matter.
