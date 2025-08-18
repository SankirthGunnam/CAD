from apps.RBM.BCF.source.db.memory_db import MemoryDB


def init_database():
    """Initialize the database with sample chips"""
    db = MemoryDB()

    # Sample chips
    sample_chips = [
        {
            "name": "MCU-001",
            "width": 10.0,
            "height": 10.0,
            "parameters": {"material": "Silicon", "thickness": 0.5},
        },
        {
            "name": "FPGA-001",
            "width": 15.0,
            "height": 15.0,
            "parameters": {"material": "GaAs", "thickness": 0.7},
        },
        {
            "name": "ADC-001",
            "width": 8.0,
            "height": 8.0,
            "parameters": {"material": "Silicon", "thickness": 0.4},
        },
        {
            "name": "DAC-001",
            "width": 8.0,
            "height": 8.0,
            "parameters": {"material": "Silicon", "thickness": 0.4},
        },
        {
            "name": "POWER-001",
            "width": 12.0,
            "height": 12.0,
            "parameters": {"material": "InP", "thickness": 0.6},
        },
    ]

    # Add chips to database
    for chip in sample_chips:
        db._add_chip(chip)

    return db


if __name__ == "__main__":
    db = init_database()
    print("Database initialized with sample chips:")
    for chip in db.get_all_chips():
        print(
            f"- {chip['name']} ({chip['width']}x{chip['height']}mm, {chip['parameters']['material']})"
        )
