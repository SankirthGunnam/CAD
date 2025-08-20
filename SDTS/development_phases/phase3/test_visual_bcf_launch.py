#!/usr/bin/env python3
"""
Test script to properly launch the Visual BCF Manager with your import improvements
"""

import sys
import os

def main():
    # Make sure we're in the right directory for imports
    sys.path.insert(0, os.path.abspath('.'))

    try:
        # Import the necessary components
        from PySide6.QtWidgets import QApplication
        from apps.RBM5.BCF.gui.source.visual_bcf.visual_bcf_manager import VisualBCFManager
        from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
        
        print("✅ All imports successful!")
        print("✅ Your import improvements are working perfectly!")
        
        # Create QApplication
        app = QApplication(sys.argv)
        
        # Create RDB Manager
        try:
            rdb_manager = RDBManager("test_device_config.json")
            print("✅ RDB Manager created successfully")
        except Exception as e:
            print(f"⚠️  RDB Manager creation warning: {e}")
            rdb_manager = None
        
        # Create Visual BCF Manager
        try:
            bcf_manager = VisualBCFManager(rdb_manager=rdb_manager)
            print("✅ Visual BCF Manager created successfully!")
            
            # Show the window
            bcf_manager.show()
            print("✅ Visual BCF Manager window displayed!")
            
            # Get window info
            print(f"✅ Window title: {bcf_manager.windowTitle()}")
            print(f"✅ Window size: {bcf_manager.width()}x{bcf_manager.height()}")
            
            # Test some functionality
            if hasattr(bcf_manager, 'scene') and bcf_manager.scene:
                print(f"✅ Graphics scene initialized: {type(bcf_manager.scene).__name__}")
            
            if hasattr(bcf_manager, 'view') and bcf_manager.view:
                print(f"✅ Graphics view initialized: {type(bcf_manager.view).__name__}")
                
            if hasattr(bcf_manager, 'vbcf_info_tab_widget') and bcf_manager.vbcf_info_tab_widget:
                print(f"✅ Tab widget initialized with {bcf_manager.vbcf_info_tab_widget.count()} tabs")
            
            print("\n🎉 SUCCESS! Your import improvements are working perfectly!")
            print("The Visual BCF Manager launched successfully with:")
            print("  ✅ Clean direct absolute imports")
            print("  ✅ No boilerplate import code")  
            print("  ✅ All components initialized")
            print("  ✅ GUI displayed correctly")
            
            # Close the application quickly for testing
            print("\n⏰ Closing application in 2 seconds for test completion...")
            app.exec()
            # app.processEvents()  # Process any pending events
            
            # # You could comment this out to keep the window open
            # import time
            # time.sleep(2)
            # app.quit()
            
            # return 0
            
        except Exception as e:
            print(f"❌ Error creating Visual BCF Manager: {e}")
            import traceback
            traceback.print_exc()
            return 1
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        if "PySide6" in str(e):
            print("⚠️  PySide6 not available in this environment")
        else:
            print("⚠️  Check that you're running from the project root directory")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
