# Phase 3: Data Management Architecture

## Overview
Phase 3 builds upon Phase 2.5's core functionality fixes to add comprehensive data management features, including save/load functionality, component properties, and data persistence.

## Key Features

### 1. Save/Load Project Functionality
- **File Menu**: New, Open, Save, Save As, Recent Files
- **Project Format**: JSON-based project file format (.sdts extension)
- **Scene Serialization**: Complete scene state preservation
- **Auto-save**: Periodic automatic saving with recovery options

### 2. Component Properties Management
- **Properties Dialog**: Detailed component property editing
- **Component Metadata**: Name, type, properties, custom parameters
- **Property Validation**: Type-specific property validation
- **Bulk Edit**: Multi-component property editing

### 3. Data Persistence Layer
- **Project Manager**: Centralized project state management
- **Change Tracking**: Track unsaved changes
- **Version Control**: Basic version management within projects
- **Export/Import**: Multiple format support (JSON, XML, CSV)

## Implementation Plan

### Core Components

#### 1. ProjectManager Class
```python
class ProjectManager(QObject):
    """Manages project lifecycle and data persistence"""
    - save_project(file_path: str) -> bool
    - load_project(file_path: str) -> bool
    - create_new_project() -> bool
    - get_project_data() -> dict
    - set_project_data(data: dict) -> bool
    - is_project_modified() -> bool
    - mark_project_clean() / mark_project_dirty()
```

#### 2. ComponentPropertiesDialog
```python
class ComponentPropertiesDialog(QDialog):
    """Advanced component property editor"""
    - edit_component_properties(component: ComponentWithPins) -> dict
    - validate_properties(properties: dict) -> bool
    - apply_properties_to_component(component, properties) -> bool
```

#### 3. FileMenuHandler
```python
class FileMenuHandler(QObject):
    """Handles file menu operations"""
    - handle_new_project()
    - handle_open_project()
    - handle_save_project()
    - handle_save_as_project()
    - handle_recent_files()
    - handle_export_project()
```

#### 4. SceneSerializer
```python
class SceneSerializer:
    """Serializes and deserializes scene data"""
    - serialize_scene(scene: ComponentScene) -> dict
    - deserialize_scene(data: dict) -> ComponentScene
    - serialize_component(component: ComponentWithPins) -> dict
    - deserialize_component(data: dict) -> ComponentWithPins
```

### Project File Format

#### SDTS Project File Structure (.sdts)
```json
{
  "project_info": {
    "name": "Project Name",
    "version": "1.0.0",
    "created": "2024-01-01T00:00:00Z",
    "modified": "2024-01-01T00:00:00Z",
    "sdts_version": "3.0",
    "description": "Project description"
  },
  "scene_data": {
    "scene_rect": [-2000, -2000, 4000, 4000],
    "zoom_level": 1.0,
    "view_center": [0, 0]
  },
  "components": [
    {
      "id": "chip_001",
      "type": "chip",
      "name": "Chip1",
      "position": [100, 200],
      "rotation": 0,
      "properties": {
        "chip_type": "Digital Processor",
        "package": "BGA-256",
        "voltage": "3.3V",
        "frequency": "100MHz"
      },
      "pins": [
        {
          "id": "pin_001",
          "name": "CLK",
          "type": "input",
          "position": "left",
          "index": 0
        }
      ]
    }
  ],
  "connections": [
    {
      "id": "wire_001",
      "start_component": "chip_001",
      "start_pin": "pin_001",
      "end_component": "chip_002",
      "end_pin": "pin_005",
      "properties": {
        "signal_type": "clock",
        "impedance": "50_ohm"
      }
    }
  ],
  "design_rules": {
    "min_trace_width": 0.1,
    "min_via_size": 0.2,
    "layer_count": 4
  }
}
```

## Enhanced UI Features

### File Menu Integration
- Add QMenuBar with File menu
- Keyboard shortcuts (Ctrl+N, Ctrl+O, Ctrl+S)
- Recent files list with thumbnails
- Auto-save indicator in status bar

### Enhanced Status Bar
- Project name display
- Modification indicator (*) for unsaved changes
- Auto-save status and last save time
- Component count and selection info

### Toolbar Enhancements
- Add save/load buttons to floating toolbar
- Project properties button
- Quick export button

## Advanced Features

### 1. Auto-save and Recovery
- Periodic auto-save every 5 minutes
- Crash recovery with auto-saved files
- Version history within project files

### 2. Component Libraries
- Built-in component library management
- Custom component creation and saving
- Component templates and presets

### 3. Export Capabilities
- Export to various formats (PDF, PNG, SVG)
- Export component lists to CSV/Excel
- Export connection matrices

## Integration with Phase 2.5
- Builds on enhanced pin system
- Uses modular floating toolbar
- Leverages ComponentWithPins architecture
- Maintains zoom and delete functionality

## Testing Strategy
- Test project save/load with complex scenes
- Test component property editing and validation  
- Test auto-save and recovery functionality
- Test export/import capabilities

## Files to Create/Modify

### New Files:
- `project_manager.py`
- `component_properties_dialog.py`
- `scene_serializer.py`
- `file_menu_handler.py`
- `export_dialog.py`

### Modified Files:
- `visual_bcf_manager.py` - Add file menu and project management
- `artifacts/chip.py` - Add property management
- `scene.py` - Add serialization support
- `test_phase3.py` - Comprehensive Phase 3 test

This architecture ensures Phase 3 provides robust data management while maintaining the solid foundation built in Phases 1, 2, and 2.5.
