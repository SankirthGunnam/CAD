# Enhanced Wire Functionality - Phase 3

## Overview

The enhanced wire system in Phase 3 provides advanced routing capabilities for electrical connections between component pins. This system implements three key features as requested:

1. **Perpendicular (Right-Angle) Routing** - Wires form clean, professional-looking right-angle paths
2. **Collision Avoidance** - Wires automatically route around components to avoid passing over them
3. **Intersection Bumps** - When wires cross, one wire forms a visual bump to indicate the crossing

## Architecture

### Core Classes

#### `WirePath`
- **Purpose**: Represents the mathematical path of a wire with multiple segments
- **Key Methods**:
  - `_calculate_path()`: Determines optimal routing strategy
  - `_route_horizontal_first()`: Routes horizontally then vertically
  - `_route_vertical_first()`: Routes vertically then horizontally
  - `add_intersection_bump()`: Adds visual bumps at intersections

#### `Wire`
- **Purpose**: Enhanced wire graphics item with advanced routing logic
- **Inherits**: `QGraphicsPathItem` (instead of `QGraphicsLineItem`)
- **Key Methods**:
  - `update_path()`: Updates wire path and routing
  - `_calculate_optimal_path()`: Calculates optimal path avoiding obstacles
  - `_avoid_component_collisions()`: Reroutes wire to avoid components
  - `_handle_wire_intersections()`: Adds bumps at wire crossings

#### `Wire` (Backward Compatibility)
- **Purpose**: Backward compatibility wrapper for existing code
- **Inherits**: `Wire`

## Features in Detail

### 1. Perpendicular Routing

Wires automatically form right-angle paths between pins:

```
Pin A ────┐
          │
          └─── Pin B
```

**Routing Strategy**:
- **Horizontal First**: When horizontal distance > vertical distance
- **Vertical First**: When vertical distance > horizontal distance
- **Midpoint Calculation**: Uses geometric center for optimal routing

**Benefits**:
- Professional appearance
- Consistent visual style
- Easy to follow connections
- Standard in electrical schematics

### 2. Collision Avoidance

Wires automatically detect and avoid passing over components:

```
Component A ────┐
               │
               └─── Component B
                    │
                    └─── Component C (avoided)
```

**Detection Algorithm**:
- Bounding box intersection testing
- Line segment vs. rectangle collision detection
- Real-time collision checking during routing

**Avoidance Strategy**:
- **Horizontal Segments**: Add vertical detours below/above components
- **Vertical Segments**: Add horizontal detours to left/right of components
- **Detour Distance**: 20px buffer from component boundaries
- **Automatic Rerouting**: Seamless path modification

**Benefits**:
- Clear visual separation
- No overlapping with components
- Maintains readability
- Professional appearance

### 3. Intersection Bumps

When wires cross, visual bumps indicate the crossing:

```
Wire 1: ────┐
             │
             └─── Wire 2: ────┐
                              │
                              └───
```

**Bump Implementation**:
- **Size**: 8px bump at intersection points
- **Direction**: Perpendicular to the wire segment
- **Visual Style**: Clear indication of wire hierarchy
- **Automatic Detection**: Real-time intersection calculation

**Intersection Algorithm**:
- Parametric line segment intersection
- Determinant-based calculation
- Bounds checking (0 ≤ t ≤ 1)
- Direction determination for bump orientation

**Benefits**:
- Clear wire crossing indication
- Maintains electrical connection clarity
- Professional schematic appearance
- Prevents visual confusion

## Technical Implementation

### Data Structures

```python
class WirePath:
    segments: List[Tuple[QPointF, QPointF]]  # Line segments
    intersection_bumps: List[Tuple[QPointF, QPointF]]  # Bump coordinates
    start_point: QPointF  # Starting pin position
    end_point: QPointF    # Ending pin position
```

### Graphics Rendering

- **Base Class**: `QGraphicsPathItem` for complex path rendering
- **Path Construction**: `QPainterPath` for multi-segment wires
- **Visual Updates**: Real-time path recalculation and rendering
- **Z-Ordering**: Wires above components, below pins

### Performance Considerations

- **Lazy Calculation**: Paths calculated only when needed
- **Efficient Collision Detection**: Bounding box optimization
- **Minimal Redraws**: Update only when positions change
- **Memory Management**: Efficient segment storage

## Usage Examples

### Basic Wire Creation

```python
# Create wire between two pins
wire = Wire(start_pin, scene=scene)
wire.complete_wire(end_pin)

# Add to scene
scene.addItem(wire)
scene.wires.append(wire)
```

### Manual Path Updates

```python
# Update wire position when pins move
wire.update_wire_position()

# Force path recalculation
wire.update_path()
```

### Custom Routing

```python
# Access wire path for custom modifications
if wire.wire_path:
    segments = wire.wire_path.segments
    bumps = wire.wire_path.intersection_bumps
```

## Testing

### Test Script

Run the comprehensive test suite:

```bash
cd SDTS/development_phases/phase3
python test_enhanced_wires.py
```

### Test Scenarios

1. **Perpendicular Routing Test**
   - Add 2+ components
   - Create wire connections
   - Verify right-angle paths

2. **Collision Avoidance Test**
   - Add 3+ components in blocking positions
   - Create wire connections
   - Verify routing around obstacles

3. **Intersection Test**
   - Add 4+ components in crossing pattern
   - Create multiple wire connections
   - Verify intersection bumps

## Configuration

### Wire Properties

```python
# Customizable wire appearance
wire.wire_width = 3        # Line thickness
wire.wire_color = QColor(0, 0, 255)  # Blue wires
wire.temp_color = QColor(255, 0, 0)  # Red temporary wires
```

### Routing Parameters

```python
# Collision avoidance settings
DETOUR_BUFFER = 20         # Pixels from component boundary
BUMP_SIZE = 8              # Intersection bump size
SEGMENT_TOLERANCE = 1      # Horizontal/vertical detection threshold
```

## Future Enhancements

### Planned Features

1. **Smart Routing Algorithms**
   - A* pathfinding for complex scenarios
   - Multi-layer routing support
   - Automatic wire bundling

2. **Advanced Collision Detection**
   - Polygon-based collision detection
   - Dynamic obstacle avoidance
   - Real-time collision prediction

3. **Enhanced Intersection Handling**
   - Multiple wire crossing styles
   - Custom bump designs
   - Intersection priority system

4. **Performance Optimizations**
   - Spatial partitioning for collision detection
   - GPU-accelerated rendering
   - Lazy evaluation strategies

## Migration Guide

### From Phase 2.5

The enhanced wire system maintains backward compatibility:

```python
# Old code continues to work
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.connection import Wire

# New enhanced functionality automatically available
wire = Wire(start_pin, end_pin)
wire.update_path()  # Enhanced routing
```

### Breaking Changes

- **None**: All existing code continues to work
- **New Features**: Available through existing API
- **Performance**: Improved routing and rendering

## Troubleshooting

### Common Issues

1. **Wires Not Routing Around Components**
   - Ensure scene reference is passed to Wire constructor
   - Check component boundingRect() implementation
   - Verify collision detection is enabled

2. **Intersection Bumps Not Appearing**
   - Check wire intersection detection algorithm
   - Verify wire segments are properly calculated
   - Ensure intersection points are within bounds

3. **Performance Issues**
   - Limit number of simultaneous wires
   - Use efficient collision detection
   - Implement lazy path calculation

### Debug Mode

Enable debug logging for detailed wire routing information:

```python
import logging
logging.getLogger('wire_routing').setLevel(logging.DEBUG)
```

## Contributing

### Development Guidelines

1. **Code Style**: Follow existing patterns and autopep8 formatting
2. **Testing**: Add tests for new functionality
3. **Documentation**: Update this README for new features
4. **Performance**: Profile changes for performance impact

### Testing Requirements

- All new features must have corresponding tests
- Performance benchmarks for routing algorithms
- Visual regression tests for wire appearance
- Integration tests with existing components

## License

This enhanced wire system is part of the SDTS project and follows the project's licensing terms.

---

**Note**: This enhanced wire system represents a significant improvement in the visual representation and routing capabilities of electrical connections, providing a professional-grade schematic drawing experience.
