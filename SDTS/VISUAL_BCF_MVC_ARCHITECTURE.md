# Visual BCF MVC Architecture Implementation

## Overview

This document describes the complete MVC (Model-View-Controller) architecture implementation for Visual BCF that aligns with the existing Legacy BCF table-based data storage.

## Architecture Goals

1. **Align with Legacy BCF**: Use existing Legacy BCF table structures as the data source
2. **Proper MVC Separation**: Clear separation between data (Model), visualization (View), and user interaction (Controller)  
3. **No Data Duplication**: Visual BCF graphics items only reference data, don't store it
4. **Real-time Synchronization**: Changes in Legacy BCF tables reflect in Visual BCF and vice versa
5. **Maintainable Code**: Clear interfaces and responsibilities

## Component Architecture

### 1. Model Layer: `VisualBCFDataModel`

**Purpose**: Bridge between Visual BCF and Legacy BCF table data

**Responsibilities**:
- Access Legacy BCF tables through RDBManager
- Manage Visual BCF specific data (positions, visual properties)
- Provide unified data access interface
- Handle data synchronization with Legacy BCF
- Emit signals when data changes

**Key Features**:
- **ComponentData**: Represents components with both functional and visual properties
- **ConnectionData**: Represents connections between components  
- **Cache Management**: In-memory cache for performance
- **Database Integration**: Uses existing JSON database structure
- **Legacy BCF Sync**: Methods to sync with Legacy BCF tables

**Database Schema**:
```json
{
  "config": {
    "visual_bcf": {
      "components": [
        {
          "id": "uuid",
          "name": "LTE Modem", 
          "component_type": "modem",
          "function_type": "LTE",
          "properties": {...},  // From Legacy BCF
          "visual_properties": {
            "position": {"x": 100, "y": 200},
            "size": {"width": 120, "height": 80},
            "rotation": 0
          },
          "pins": [...]
        }
      ],
      "connections": [
        {
          "id": "uuid",
          "from_component_id": "comp1", 
          "from_pin_id": "pin1",
          "to_component_id": "comp2",
          "to_pin_id": "pin2",
          "connection_type": "wire",
          "properties": {...},
          "visual_properties": {
            "path_points": [...],
            "line_style": "solid",
            "color": "#000000"
          }
        }
      ]
    },
    // Existing Legacy BCF data
    "device": { "settings": [...] },
    "band": { "settings": [...] },
    "board": { "settings": [...] }
  }
}
```

### 2. View Layer: `RFScene` + `RFView`

**Purpose**: Handle graphics visualization and user input

**Responsibilities**:
- Display graphics items (components, connections)
- Handle user interactions (mouse, keyboard)
- Provide visual feedback (selection, highlighting)
- Graphics-only operations (zoom, pan, selection)

**Key Principles**:
- **No Data Storage**: Graphics items only reference model data by ID
- **Lightweight Items**: Minimal data in graphics objects  
- **Signal-Based**: Emit signals for user actions, don't handle business logic

### 3. Controller Layer: `VisualBCFController`

**Purpose**: Coordinate between Model and View, handle business logic

**Responsibilities**:
- Handle user interactions from Scene/View
- Perform operations on Model based on user actions
- Update View when Model changes
- Manage selection and clipboard operations
- Handle Legacy BCF synchronization

**Key Features**:
- **Event Handling**: Process user interactions from scene
- **Model Coordination**: Call appropriate model methods for operations
- **Graphics Management**: Create/update graphics items based on model
- **Mode Management**: Handle different interaction modes (select, connect, etc.)

## Data Flow

### Adding a Component
1. **User Action**: Right-click → "Add Component" in scene  
2. **View**: Scene emits `add_chip_requested` signal
3. **Controller**: Receives signal, calls `data_model.add_component()`
4. **Model**: Adds component to database, emits `component_added` signal
5. **Controller**: Receives model signal, creates graphics item 
6. **View**: Graphics item appears in scene

### Syncing with Legacy BCF  
1. **Controller**: Calls `data_model.sync_with_legacy_bcf()`
2. **Model**: Reads Legacy BCF tables (`config.device.settings`)
3. **Model**: Updates component properties, emits `component_updated` signals
4. **Controller**: Updates graphics items with new properties
5. **View**: Graphics items reflect updated data

### Legacy BCF Changes
1. **External Change**: Legacy BCF table modified
2. **RDBManager**: Emits `data_changed` signal
3. **Model**: Detects change, reloads data, emits update signals
4. **Controller**: Updates graphics items
5. **View**: Visual representation updates automatically

## Implementation Benefits

### 1. **Single Source of Truth**
- All functional data stored in Legacy BCF tables
- Visual properties stored in dedicated Visual BCF section
- No data duplication between Visual and Legacy modes

### 2. **Real-time Synchronization**
- Changes in Legacy BCF automatically update Visual BCF
- Changes in Visual BCF can be exported to Legacy BCF
- Consistent data across both interfaces

### 3. **Clean Architecture**
- Clear separation of concerns
- Easy to test individual components
- Maintainable and extensible code

### 4. **Performance**
- In-memory caching for fast access
- Signal-based updates only when needed
- Lightweight graphics items

### 5. **Flexibility** 
- Easy to add new component types
- Support for different visualization modes
- Pluggable architecture for extensions

## Usage Example

```python
# Create MVC components
rdb_manager = RDBManager("device_config.json")
data_model = VisualBCFDataModel(rdb_manager)
scene = RFScene()
view = RFView(scene)
controller = VisualBCFController(scene, view, data_model)

# Add component through controller
component_id = controller.add_component(
    name="LTE Modem",
    component_type="modem", 
    position=(100, 100),
    properties={"function_type": "LTE"}
)

# Sync with Legacy BCF
controller.sync_with_legacy_bcf()

# Export to Legacy BCF
controller.export_to_legacy_bcf()
```

## Migration Strategy

### Phase 1: Create New Components
1. Implement `VisualBCFDataModel`
2. Implement `VisualBCFController` 
3. Create unit tests

### Phase 2: Integrate with Existing Scene
1. Update `RFScene` to work with controller
2. Modify graphics items to reference model data
3. Test basic operations

### Phase 3: Replace Current Manager
1. Create new `VisualBCFManagerMVC`
2. Maintain compatibility with existing interface
3. Gradual migration from old to new system

### Phase 4: Legacy BCF Integration
1. Implement sync methods
2. Test bidirectional data flow
3. Validate data consistency

## File Structure

```
apps/RBM/BCF/src/
├── models/
│   ├── visual_bcf_data_model.py      # Main data model
│   └── ...
├── controllers/
│   ├── visual_bcf_controller.py      # Main controller
│   └── ...
└── gui/src/visual_bcf/
    ├── scene.py                      # Graphics scene (View)
    ├── view.py                       # Graphics view (View)
    └── visual_bcf_manager_mvc.py     # Updated manager
```

## Conclusion

This MVC architecture provides a robust foundation for Visual BCF that:
- Aligns with existing Legacy BCF data structures
- Maintains clean separation of concerns
- Enables real-time synchronization between Visual and Legacy modes
- Provides a maintainable and extensible codebase

The implementation allows Visual BCF to leverage all the existing Legacy BCF table data while providing a modern, visual interface for circuit design.
