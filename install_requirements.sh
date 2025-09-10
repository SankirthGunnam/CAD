#!/bin/bash
# Installation script for PySide6

echo "Installing PySide6 and required dependencies..."

# Update package list
sudo apt update

# Install pip if not available
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip3..."
    sudo apt install -y python3-pip
fi

# Install PySide6
echo "Installing PySide6..."
pip3 install PySide6

# Verify installation
echo "Verifying installation..."
python3 -c "import PySide6; print('PySide6 successfully installed!')"

echo "Installation complete!"
echo "You can now run: python3 test_interactive_widget.py"
