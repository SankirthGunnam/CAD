# Model-Aware Scene Architecture for CAD Applications

**Document Version:** 1.0  
**Date:** August 2025  
**Author:** SDTS Development Team  
**Project:** Schematic Design Tool Suite (SDTS)

## Executive Summary

This document presents and validates the **Model-Aware Scene** architectural pattern adopted in the SDTS project for managing complex CAD graphics and data. This approach integrates business logic directly into Qt's QGraphicsScene, creating a "Rich Domain Model" that combines the benefits of traditional Model-View patterns with the practical needs of interactive CAD applications.

## 1. Background and Context

### 1.1 Traditional Qt Model-View Pattern

Qt's graphics framework traditionally separates concerns between:
- **QGraphicsScene**: Container for graphics items and coordinate system
- **QGraphicsView**: Viewport that displays portions of the scene
- **Separate Models**: Business logic and data storage

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Data Model  │───▶│ Controller/  │───▶│ Graphics    │
│ (Business   │    │ Manager      │    │ Scene       │
│  Logic)     │    │              │    │ (Display)   │
└─────────────┘    └──────────────┘    └─────────────┘
```

### 1.2 The Challenge in CAD Applications

CAD applications present unique challenges:
1. **Graphics ARE the primary data interface** - users interact directly with visual representations
2. **Real-time synchronization** - graphics and data must remain perfectly synchronized
3. **Complex relationships** - components have intricate spatial and logical relationships
4. **Performance requirements** - frequent updates during interactive editing
5. **Direct manipulation** - users expect to directly manipulate visual elements

## 2. The Model-Aware Scene Approach

### 2.1 Architecture Overview

In our approach, the QGraphicsScene becomes "model-aware" - it directly manages both graphics rendering and business logic data:

```
┌─────────────────────────────────────┐
│          Model-Aware Scene          │
│  ┌─────────────┐  ┌───────────────┐ │    ┌─────────────┐
│  │ Graphics    │  │ Business      │ │───▶│ Database    │
│  │ Items       │  │ Logic Models  │ │    │ Persistence │
│  │ (Visual)    │  │ (Data)        │ │    └─────────────┘
│  └─────────────┘  └───────────────┘ │
└─────────────────────────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ QGraphicsView   │
            │ (Viewport)      │
            └─────────────────┘
```

### 2.2 Implementation Pattern

```python
class RFScene(QGraphicsScene):
    """Model-aware scene that manages both graphics and business logic"""
    
    # Signals for external communication
    data_changed = Signal(dict)
    selection_changed = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self._components = []  # Business logic models
        
    def add_component(self, chip_widget):
        """Add component with both graphics and model data"""
        # Handle graphics
        self.addItem(chip_widget)
        
        # Handle business logic
        if hasattr(chip_widget, 'model'):
            self._components.append(chip_widget.model)
            
        # Notify external systems
        self.data_changed.emit({
            "action": "add_component",
            "component_data": chip_widget.model.to_dict()
        })
    
    def get_business_data(self):
        """Clean interface to extract business data"""
        return [comp.to_dict() for comp in self._components]
    
    def save_state(self):
        """Serialize current state for persistence"""
        return {
            "components": self.get_business_data(),
            "scene_settings": {
                "rect": [self.sceneRect().x(), self.sceneRect().y(), 
                        self.sceneRect().width(), self.sceneRect().height()]
            }
        }
```

## 3. Benefits and Justification

### 3.1 Performance Benefits

| **Aspect** | **Traditional Approach** | **Model-Aware Scene** |
|------------|--------------------------|----------------------|
| **Synchronization** | Constant model↔graphics sync needed | Always synchronized by design |
| **Updates** | Two-phase: update model, then graphics | Single-phase: update both together |
| **Memory** | Duplicate data in model and graphics | Single source of truth |
| **Rendering** | May render stale data during sync | Always renders current data |

### 3.2 Development Benefits

1. **Reduced Complexity**: Single point of truth eliminates synchronization bugs
2. **Faster Development**: Direct manipulation without complex coordination layers
3. **Easier Debugging**: One place to examine both graphics and data state
4. **Natural APIs**: Graphics operations directly affect business data

### 3.3 User Experience Benefits

1. **Immediate Feedback**: Visual changes instantly reflect in business logic
2. **Consistency**: No possibility of graphics/data desynchronization
3. **Performance**: Smoother interactions during complex operations
4. **Direct Manipulation**: Natural CAD workflow where graphics ARE the interface

## 4. Industry Validation

### 4.1 Similar Approaches in Industry

This pattern is successfully used by major CAD and graphics applications:

- **AutoCAD**: Entity objects contain both graphics and business data
- **Solidworks**: Feature tree items integrate 3D graphics with parametric data
- **Blender**: Scene graph objects contain geometry, materials, and metadata
- **Unity Engine**: GameObjects combine transform, rendering, and logic components

### 4.2 Academic Support

The approach aligns with established software architecture patterns:
- **Rich Domain Model** (Domain-Driven Design)
- **Active Record Pattern** (where objects manage their own persistence)
- **Component-Entity Systems** (game development)

## 5. Implementation Guidelines

### 5.1 Best Practices

```python
class ModelAwareScene(QGraphicsScene):
    """Template for implementing model-aware scenes"""
    
    def __init__(self):
        super().__init__()
        self._business_models = {}  # Key: graphics_item_id, Value: business_model
        
    def add_item_with_model(self, graphics_item, business_model):
        """Add item maintaining graphics-model relationship"""
        self.addItem(graphics_item)
        self._business_models[id(graphics_item)] = business_model
        self._emit_change_notification("add", business_model)
    
    def remove_item_with_model(self, graphics_item):
        """Remove item and its associated model"""
        if id(graphics_item) in self._business_models:
            model = self._business_models.pop(id(graphics_item))
            self._emit_change_notification("remove", model)
        self.removeItem(graphics_item)
    
    def get_model_for_item(self, graphics_item):
        """Retrieve business model for graphics item"""
        return self._business_models.get(id(graphics_item))
    
    def _emit_change_notification(self, action, model):
        """Notify external systems of changes"""
        self.data_changed.emit({
            "action": action,
            "model": model.to_dict() if hasattr(model, 'to_dict') else str(model),
            "timestamp": time.time()
        })
```

### 5.2 Interface Design Principles

1. **Clean Separation of External APIs**: External components should interact through well-defined signals and methods
2. **Model Abstraction**: Provide methods to extract pure business data when needed
3. **Change Notifications**: Emit signals for external systems (persistence, undo/redo, etc.)
4. **Serialization Support**: Enable easy save/load of complete scene state

## 6. Addressing Common Concerns

### 6.1 "Violation of Separation of Concerns"

**Concern**: Mixing graphics and business logic violates clean architecture.

**Response**: In CAD applications, graphics ARE the primary business interface. The separation that matters is between:
- **Internal Implementation** (how graphics and data are managed)
- **External Interface** (how other systems interact with the scene)

### 6.2 "Difficult to Unit Test"

**Concern**: Tightly coupled graphics and data are hard to test.

**Response**: Provide clean data extraction methods for testing:

```python
def test_chip_positioning():
    scene = RFScene()
    chip_model = ChipModel("TestChip", x=100, y=200)
    chip_widget = ChipWidget(chip_model)
    
    scene.add_component(chip_widget)
    
    # Test business logic without graphics dependency
    business_data = scene.get_business_data()
    assert business_data[0]["position"] == [100, 200]
```

### 6.3 "Hard to Persist Data"

**Concern**: Mixed graphics/data is difficult to save/load.

**Response**: Provide serialization methods that extract pure business data:

```python
def save_to_file(self, filename):
    """Save only business data, not graphics state"""
    business_state = {
        "version": "1.0",
        "components": self.get_business_data(),
        "scene_metadata": self.get_scene_metadata()
    }
    with open(filename, 'w') as f:
        json.dump(business_state, f)
```

## 7. Migration Strategy

### 7.1 For Existing Codebases

If migrating from traditional model-view separation:

1. **Phase 1**: Create model-aware scene alongside existing architecture
2. **Phase 2**: Migrate components one by one to new scene
3. **Phase 3**: Remove old model-controller layers
4. **Phase 4**: Optimize and refactor for new architecture

### 7.2 Risk Mitigation

- **Maintain External APIs**: Keep existing interfaces during migration
- **Comprehensive Testing**: Test both graphics and business logic together
- **Rollback Plan**: Ability to revert to old architecture if needed

## 8. Conclusion

The **Model-Aware Scene** approach is a pragmatic architectural decision that aligns with the realities of CAD application development. While it challenges traditional separation of concerns, it provides significant benefits in terms of:

- **Performance**: Eliminated synchronization overhead
- **Maintainability**: Single source of truth
- **User Experience**: Immediate visual feedback
- **Development Speed**: Reduced complexity

This approach is validated by successful implementation in major industry applications and aligns with modern software architecture patterns focused on domain-driven design and rich models.

## 9. References and Further Reading

- **Domain-Driven Design** by Eric Evans
- **Qt Graphics View Framework Documentation**
- **Enterprise Application Architecture Patterns** by Martin Fowler
- **Game Programming Patterns** by Robert Nystrom
- **CAD System Architecture** - Various academic papers on computer-aided design systems

---

**Appendix A: Code Examples**  
**Appendix B: Performance Benchmarks**  
**Appendix C: Migration Checklist**

---

*This document is part of the SDTS project documentation and should be reviewed with the development team before implementation of any major architectural changes.*
