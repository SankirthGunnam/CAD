# Interactive PySide6 Widget

An interactive PySide6 widget featuring a progress tracker, tab widget with QDialog widgets, and navigation controls.

## Features

- **Progress Tracker**: Visual progress indicator with bubbles and arrows
- **Tab Widget**: Contains QDialog widgets without dialog buttons
- **Arrow Button**: Navigation button in bottom-right corner
- **Hover Tooltips**: Progress bubbles show tab titles on hover
- **Data Collection**: Collects user selections from each tab
- **Dynamic Tab Creation**: New tabs are added when arrow button is clicked

## Components

### Progress Tracker (`progress_tracker.py`)
- `ProgressBubble`: Individual progress bubbles with hover tooltips
- `ProgressArrow`: Arrows connecting progress bubbles
- `ProgressTracker`: Main progress tracker widget

### Dialog Tabs (`dialog_tab.py`)
- `DialogTab`: Base dialog widget for tabs
- `TextInputDialog`: Text input dialog
- `CheckboxDialog`: Multiple selection dialog
- `RadioDialog`: Single selection dialog
- `NumberInputDialog`: Number input dialog

### Main Widget (`main_widget.py`)
- `InteractiveWidget`: Main widget combining all components
- `ArrowButton`: Custom navigation button

## Usage

### Running the Example

```bash
# Install dependencies
pip install -r requirements.txt

# Run the example application
python main.py
```

### Using in Your Application

```python
from main_widget import InteractiveWidget
from PySide6.QtWidgets import QApplication, QMainWindow

app = QApplication([])
window = QMainWindow()

# Create the interactive widget
widget = InteractiveWidget()
window.setCentralWidget(widget)

window.show()
app.exec()
```

## How It Works

1. **Initial State**: Widget starts with one tab containing a dialog widget
2. **User Interaction**: User selects values in the current tab
3. **Navigation**: Clicking the arrow button:
   - Prints the selected value
   - Completes the current progress step
   - Adds a new tab with a different dialog type
   - Updates the progress tracker
4. **Progress Tracking**: Each tab addition adds a new bubble to the progress tracker
5. **Data Collection**: All user selections are stored and can be retrieved

## Customization

### Adding New Dialog Types

Create a new dialog class inheriting from `DialogTab`:

```python
class CustomDialog(DialogTab):
    def __init__(self, title="Custom Dialog", parent=None):
        super().__init__(title, parent)
        
    def setupUI(self):
        layout = QVBoxLayout(self)
        # Add your custom widgets here
        # Connect signals to onSelectionChanged
```

### Modifying Progress Tracker

The progress tracker can be customized by modifying the `ProgressBubble` and `ProgressArrow` classes in `progress_tracker.py`.

### Styling

The arrow button uses CSS styling that can be modified in the `ArrowButton` class.