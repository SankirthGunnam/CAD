"""
Wire Thread Manager for Scene-based Multi-threaded Wire Calculations

This implementation uses a "latest data wins" approach:
- No mutex locks to avoid blocking during rapid position changes
- Old calculations are discarded when new ones start
- Component positions are read at calculation time (latest data)
- Prioritizes responsiveness over thread safety
"""

import uuid
from typing import Optional, Dict, Callable
from PySide6.QtCore import QThread, Signal, QObject, QPointF
from PySide6.QtGui import QPainterPath

from .pin import ComponentPin


class WireCalculationWorker(QThread):
    """Worker thread for calculating a single wire path"""
    
    calculation_complete = Signal(str, object)  # wire_id, WirePathCalculator
    calculation_failed = Signal(str, str)  # wire_id, error_message
    
    def __init__(self, wire_id: str, start_pin: ComponentPin, end_pin: ComponentPin, 
                 scene, parent=None):
        super().__init__(parent)
        self.wire_id = wire_id
        self.start_pin = start_pin
        self.end_pin = end_pin
        self.scene = scene
        self._should_stop = False
    
    def run(self):
        """Calculate wire path in separate thread"""
        try:
            if self._should_stop:
                return
            
            # Get pin positions (latest data)
            start_pos = self.start_pin.get_connection_point()
            end_pos = self.end_pin.get_connection_point()
            
            # Import WirePath here to avoid circular imports
            from .connection import WirePath
            
            # Calculate wire path
            wire_path = WirePath(start_pos, end_pos, self.start_pin, self.end_pin, self.scene)
            
            if self._should_stop:
                return
            
            # Emit result
            self.calculation_complete.emit(self.wire_id, wire_path)
            
        except Exception as e:
            self.calculation_failed.emit(self.wire_id, str(e))
    
    def stop(self):
        """Stop the calculation"""
        self._should_stop = True
        if self.isRunning():
            self.quit()
            self.wait()


class SceneWireThreadManager(QObject):
    """Thread manager for wire calculations in the scene"""
    
    def __init__(self, max_threads: int = 10, parent=None):
        super().__init__(parent)
        self.max_threads = max_threads
        self.active_workers: Dict[str, WireCalculationWorker] = {}
        self.pending_calculations = []
        
        # Statistics
        self.total_calculations = 0
        self.completed_calculations = 0
        self.failed_calculations = 0
    
    def calculate_wire_async(self, wire_id: str, start_pin: ComponentPin, 
                           end_pin: ComponentPin, scene, callback: Optional[Callable] = None):
        """Start wire calculation in separate thread - latest data wins approach"""
        self.total_calculations += 1
        
        # Stop existing calculation for this wire (discard old data)
        if wire_id in self.active_workers:
            self.active_workers[wire_id].stop()
            del self.active_workers[wire_id]
        
        # Start new calculation if we have available threads
        if len(self.active_workers) < self.max_threads:
            worker = WireCalculationWorker(wire_id, start_pin, end_pin, scene)
            worker.calculation_complete.connect(
                lambda wid, path: self._on_calculation_complete(wid, path, callback)
            )
            worker.calculation_failed.connect(
                lambda wid, err: self._on_calculation_failed(wid, err, callback)
            )
            worker.finished.connect(lambda: self._cleanup_thread(wire_id))
            
            self.active_workers[wire_id] = worker
            worker.start()
            
            print(f"🚀 Started wire calculation thread for {wire_id} (Active: {len(self.active_workers)}/{self.max_threads})")
        else:
            # Queue for later
            self.pending_calculations.append({
                'wire_id': wire_id,
                'start_pin': start_pin,
                'end_pin': end_pin,
                'scene': scene,
                'callback': callback
            })
            print(f"⏳ Queued wire calculation for {wire_id} (Queue: {len(self.pending_calculations)})")
    
    def _on_calculation_complete(self, wire_id: str, wire_path, callback):
        """Handle completed calculation"""
        self.completed_calculations += 1
        
        if callback:
            callback(wire_id, wire_path)
        
        print(f"✅ Completed wire calculation for {wire_id}")
        
        # Start next pending calculation
        self._start_next_pending()
    
    def _on_calculation_failed(self, wire_id: str, error: str, callback):
        """Handle failed calculation"""
        self.failed_calculations += 1
        
        print(f"❌ Wire calculation failed for {wire_id}: {error}")
        
        if callback:
            callback(wire_id, None)
        
        # Start next pending calculation
        self._start_next_pending()
    
    def _cleanup_thread(self, wire_id: str):
        """Clean up completed thread"""
        if wire_id in self.active_workers:
            thread = self.active_workers[wire_id]
            thread.deleteLater()
            del self.active_workers[wire_id]
    
    def _start_next_pending(self):
        """Start the next pending calculation"""
        if self.pending_calculations and len(self.active_workers) < self.max_threads:
            calc = self.pending_calculations.pop(0)
            self.calculate_wire_async(
                calc['wire_id'], calc['start_pin'], calc['end_pin'], 
                calc['scene'], calc['callback']
            )
    
    def stop_all_calculations(self):
        """Stop all active calculations"""
        for worker in self.active_workers.values():
            worker.stop()
        self.active_workers.clear()
        self.pending_calculations.clear()
        print("🛑 Stopped all wire calculations")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get calculation statistics"""
        return {
            'total_calculations': self.total_calculations,
            'completed_calculations': self.completed_calculations,
            'failed_calculations': self.failed_calculations,
            'active_threads': len(self.active_workers),
            'pending_calculations': len(self.pending_calculations)
        }
    
    def cleanup(self):
        """Clean up all resources"""
        self.stop_all_calculations()
        print("🧹 Wire thread manager cleaned up")
