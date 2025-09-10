# Interactive PySide6 Widget

A comprehensive interactive widget built with PySide6 that provides a step-by-step configuration interface with progress tracking.

## Features

### 🎯 Core Functionality
- **Vertical Layout**: Clean vertical layout with progress tracker at top, tab widget in middle, and arrow button at bottom right
- **Progress Tracker**: Visual progress indicator with bubbles and arrows showing completion status
- **Tab Widget**: Contains QDialog widgets without dialog buttons for seamless user experience
- **Dynamic Tab Creation**: New tabs are added when user clicks the arrow button
- **Data Persistence**: Selected values are stored and can be retrieved at any time

### 🎨 Visual Features
- **Progress Bubbles**: Circular indicators with step numbers and completion checkmarks
- **Hover Tooltips**: Progress bubbles show corresponding tab titles on hover
- **Modern Styling**: Clean, professional UI with consistent color scheme
- **Responsive Design**: Adapts to different window sizes with proper spacing

### 🔧 Dialog Types
The widget supports four different dialog types that cycle through:
1. **Text Input Dialog**: Single-line text input with placeholder
2. **Checkbox Dialog**: Multiple selection with checkboxes
3. **Radio Dialog**: Single selection with radio buttons
4. **Number Input Dialog**: Numeric input with spin box

## File Structure

```
├── main_widget.py              # Main interactive widget class
├── dialog_tab.py               # Dialog tab implementations
├── progress_tracker.py         # Progress tracking components
├── test_interactive_widget.py  # Test/demo application
├── install_requirements.sh     # Installation script
└── INTERACTIVE_WIDGET_README.md # This file
```

## Installation

### Prerequisites
- Python 3.7 or higher
- Linux/Windows/macOS

### Quick Install
```bash
# Make installation script executable
chmod +x install_requirements.sh

# Run installation
./install_requirements.sh
```

### Manual Install
```bash
# Install pip if needed
sudo apt install python3-pip

# Install PySide6
pip3 install PySide6
```

## Usage

### Basic Usage
```python
from main_widget import InteractiveWidget
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
widget = InteractiveWidget()
widget.show()
sys.exit(app.exec())
```

### Advanced Usage
```python
# Get collected data
data = widget.getCollectedData()
print("Collected data:", data)

# Reset widget
widget.resetWidget()

# Check progress
current_step = widget.progress_tracker.getCurrentStep()
total_steps = widget.progress_tracker.getTotalSteps()
```

### Running the Demo
```bash
python3 test_interactive_widget.py
```

## API Reference

### InteractiveWidget Class

#### Methods
- `addNewTab()`: Adds a new tab with the next dialog type
- `onDialogSelectionChanged(tab_title, selected_value)`: Handles selection changes
- `onArrowButtonClicked()`: Handles arrow button clicks
- `getCollectedData()`: Returns all collected data as dictionary
- `resetWidget()`: Resets widget to initial state

#### Properties
- `tab_data`: Dictionary storing selected values from each tab
- `dialog_types`: List of available dialog classes
- `current_dialog_index`: Index of current dialog type

### ProgressTracker Class

#### Methods
- `addStep(title)`: Adds a new step to the tracker
- `completeCurrentStep()`: Marks current step as completed
- `getCurrentStep()`: Returns current step number (0-based)
- `getTotalSteps()`: Returns total number of steps
- `reset()`: Resets the progress tracker

### DialogTab Classes

#### Base Class: DialogTab
- `selection_changed`: Signal emitted when selection changes
- `getSelectedValue()`: Returns currently selected value

#### Implemented Classes
- `TextInputDialog`: Text input with QLineEdit
- `CheckboxDialog`: Multiple selection with QCheckBox
- `RadioDialog`: Single selection with QRadioButton
- `NumberInputDialog`: Numeric input with QSpinBox

## Customization

### Adding New Dialog Types
```python
class CustomDialog(DialogTab):
    def __init__(self, title="Custom", parent=None):
        super().__init__(title, parent)
        
    def setupUI(self):
        # Implement your custom UI
        pass
        
    def getSelectedValue(self):
        # Return the selected value
        return "custom_value"
```

### Styling
The widget uses CSS-like styling through `setStyleSheet()`. You can customize:
- Colors and backgrounds
- Fonts and text styling
- Borders and spacing
- Hover and focus effects

### Progress Tracker Customization
- Modify bubble colors in `ProgressBubble.paintEvent()`
- Change arrow styling in `ProgressArrow.paintEvent()`
- Adjust spacing and sizing in `ProgressTracker.__init__()`

## Example Workflow

1. **Start**: Widget opens with first tab (Text Input)
2. **Select**: User makes a selection in the current tab
3. **Proceed**: User clicks the green arrow button
4. **Progress**: Current step is marked complete, progress tracker updates
5. **Next Tab**: New tab is created with next dialog type
6. **Repeat**: Process continues with different dialog types
7. **Data Collection**: All selections are stored and can be retrieved

## Troubleshooting

### Common Issues

1. **Import Error**: `ModuleNotFoundError: No module named 'PySide6'`
   - Solution: Run `./install_requirements.sh` or `pip3 install PySide6`

2. **Widget Not Showing**: Widget appears but is not visible
   - Solution: Ensure proper layout and call `show()` method

3. **Styling Issues**: Widget appears unstyled
   - Solution: Check that `applyStyling()` is called in `__init__`

### Debug Mode
Enable debug output by adding print statements in key methods:
- `onDialogSelectionChanged()`: Shows selection changes
- `onArrowButtonClicked()`: Shows button clicks and data collection
- `addNewTab()`: Shows new tab creation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API reference
3. Create an issue with detailed description
4. Include system information and error messages
