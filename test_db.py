from database_mgr import DatabaseMgr
import os

def test_db():
    print("Starting DatabaseMgr test...")
    if os.path.exists("database.bin"):
        os.remove("database.bin")
        print("Removed existing database.bin")

    db = DatabaseMgr()
    db['test_key'] = 'test_value'
    db.other_key = 'other_value'
    
    print("Saving data...")
    db.save()
    print("Data saved.")

    print("\nLoading data into a new instance...")
    db2 = DatabaseMgr()
    db2.load()
    
    print(f"Loaded data: {db2.data}")
    
    assert db2['test_key'] == 'test_value'
    assert db2.other_key == 'other_value'
    print("\nVerification successful! Data matches.")

if __name__ == '__main__':
    try:
        test_db()
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
