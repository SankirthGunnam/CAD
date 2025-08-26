# Single Source of Truth: Components and Connections as Lists of Dictionaries

## 🎯 **Overview**

The refactored system now uses a **single source of truth** approach where:
- **Components and connections are stored as lists of dictionaries** in Visual BCF tables
- **Each dictionary contains ALL related information** for both Visual BCF and Legacy BCF compatibility
- **Tables display specific fields** by extracting them from the same data source
- **No synchronization needed** since everything uses the same underlying data

## 🏗️ **Data Structure**

### **Component Dictionary Structure**
```python
{
    # Visual BCF Fields
    'id': 'uuid-string',
    'name': 'Component Name',
    'component_type': 'modem|rfic|chip|filter',
    'visual_properties': {
        'position': {'x': 100, 'y': 100},
        'size': {'width': 120, 'height': 100},
        'rotation': 0
    },
    'pins': ['TX1', 'RX1', 'TX2', 'RX2', 'CLK', 'RST'],
    
    # Legacy BCF Compatibility Fields
    'function_type': 'modem',
    'interface_type': 'MIPI',
    'interface': {},
    'config': {},
    'usid': 'uuid-8chars',
    'mid_msb': '00',
    'mid_lsb': '01',
    'pid': '0000',
    'ext_pid': '0000',
    'rev_id': '1.0',
    'dcf_type': 'Standard',
    
    # Properties (merged from external config + custom)
    'properties': {
        'function_type': 'modem',
        'interface_type': 'MIPI',
        'custom_prop': 'custom_value'
    }
}
```

### **Connection Dictionary Structure**
```python
{
    # Visual BCF Fields
    'id': 'uuid-string',
    'from_component_id': 'source-component-uuid',
    'from_pin_id': 'TX1',
    'to_component_id': 'dest-component-uuid',
    'to_pin_id': 'RX1',
    'connection_type': 'wire',
    'visual_properties': {
        'path_points': [],
        'line_style': 'solid',
        'color': '#000000'
    },
    
    # Legacy BCF Compatibility Fields
    'source_device': 'Source Component Name',
    'source_pin': 'TX1',
    'dest_device': 'Dest Component Name',
    'dest_pin': 'RX1',
    'source_sub_block': 'Main Block',
    'dest_sub_block': 'Main Block',
    'status': 'Active',
    
    # Properties
    'properties': {}
}
```

## 🔄 **How It Works**

### **1. Data Storage**
```
Visual BCF Tables (Single Source of Truth)
├── components: [component_dict1, component_dict2, ...]
└── connections: [connection_dict1, connection_dict2, ...]
```

### **2. Table Views (Same Data, Different Display)**
```
Available Devices Table View
├── Device Name ← component['name']
├── Control Type ← component['interface_type']
├── Module ← component['component_type'].upper()
├── USID ← component['usid']
├── MID (MSB) ← component['mid_msb']
├── MID (LSB) ← component['mid_lsb']
├── PID ← component['pid']
├── EXT PID ← component['ext_pid']
├── REV ID ← component['rev_id']
└── DCF Type ← component['dcf_type']

IO Connections Table View
├── Connection ID ← connection['id']
├── Source Device ← connection['source_device']
├── Source Pin ← connection['source_pin']
├── Source Sub Block ← connection['source_sub_block']
├── Dest Device ← connection['dest_device']
├── Dest Pin ← connection['dest_pin']
├── Dest Sub Block ← connection['dest_sub_block']
├── Connection Type ← connection['connection_type']
└── Status ← connection['status']
```

### **3. Legacy BCF Compatibility**
```
Legacy BCF Device Format
├── name ← component['name']
├── function_type ← component['function_type']
├── interface_type ← component['interface_type']
├── interface ← component['interface']
├── config ← component['config']
├── usid ← component['usid']
├── mid_msb ← component['mid_msb']
├── mid_lsb ← component['mid_lsb']
├── pid ← component['pid']
├── ext_pid ← component['ext_pid']
├── rev_id ← component['rev_id']
└── dcf_type ← component['dcf_type']
```

## 🚀 **Benefits**

### **1. No Data Duplication**
- **Before**: Separate tables for Visual BCF, Available Devices, IO Connections
- **After**: Single Visual BCF tables with all information embedded

### **2. Automatic Consistency**
- **Before**: Manual synchronization between different table structures
- **After**: All views automatically show the same data

### **3. Easy Maintenance**
- **Before**: Update data in multiple places
- **After**: Update once, all views automatically reflect changes

### **4. Legacy BCF Compatibility**
- **Before**: Separate export/import processes
- **After**: Automatic compatibility through embedded fields

## 🔧 **Usage Examples**

### **Adding a Component**
```python
component_id = data_model.add_component(
    name="Test Modem",
    component_type="modem",
    position=(100, 100),
    properties={"custom_prop": "custom_value"}
)
# Automatically creates component with ALL fields for both Visual BCF and Legacy BCF
```

### **Getting Table Views**
```python
# Available Devices table view
available_devices = data_model.get_available_devices_for_table()

# IO Connections table view
io_connections = data_model.get_io_connections_for_table()

# Legacy BCF format
legacy_devices = data_model.get_legacy_bcf_devices()
```

### **Updating Data**
```python
# Update component properties
data_model.update_component_properties(component_id, {"new_prop": "new_value"})

# All table views automatically reflect the change
# No need to sync separate tables
```

## 📊 **Data Flow**

```
User Action (Add/Update/Delete Component/Connection)
           ↓
Visual BCF Data Model (Single Source of Truth)
           ↓
    ┌─────────────────┬─────────────────┬─────────────────┐
    ↓                 ↓                 ↓                 ↓
Graphics Scene    Available Devices   IO Connections   Legacy BCF
(Visual Display)   Table View        Table View       Export
    ↑                 ↑                 ↑                 ↑
    └─────────────────┴─────────────────┴─────────────────┘
           All use the same underlying data
```

## 🧪 **Testing**

Run the test script to see the single source of truth in action:
```bash
python3 test_single_source_truth.py
```

This will demonstrate:
1. Adding components with complete information
2. Adding connections with complete information
3. Displaying table views from the same data
4. Verifying data consistency across all views
5. Legacy BCF compatibility

## ✅ **Verification**

The system ensures data consistency by:
- **Component Count**: `component_count == available_devices_count`
- **Connection Count**: `connection_count == io_connections_count`
- **Single Source**: All data comes from `config.visual_bcf.components` and `config.visual_bcf.connections`
- **Automatic Updates**: Changes in one view automatically appear in all other views

## 🎉 **Result**

With this approach:
- ✅ **All Devices table**: Shows data from Visual BCF components
- ✅ **IO Connect table**: Shows data from Visual BCF connections  
- ✅ **Graphics Scene**: Displays the same data
- ✅ **Data Consistency**: All views are automatically synchronized
- ✅ **No Sync Code**: Changes automatically propagate to all views
- ✅ **Legacy BCF Compatible**: All required fields are embedded in the data
