To ensure a property is **always** present with a file—especially through **Perforce** and across different computers—it must be part of the file's **internal byte structure**.

Standard Windows "File Properties" (like the ones you see in the Details tab) are metadata stored by the Operating System, not the file. When you move that file to a server like Perforce, the OS metadata is stripped, but the internal bytes remain.

Since you are using a custom extension and writing bytes, here is the professional way to implement a "Permanent Header" that acts exactly like system properties.

---

## 1. The "Permanent Header" Strategy

Think of your file like a **JPEG** or a **PDF**. Even if you rename a `.jpg` to `.txt`, the "Date Taken" and "Camera Model" are still hidden inside the bytes.

You should reserve the first **256 bytes** of your custom file format for metadata.

### The Binary Layout

| Offset | Field | Size | Why it's "Always Present" |
| --- | --- | --- | --- |
| 0 | Magic Number | 4 Bytes | Identifies the file type (e.g., `RFD!`) |
| 4 | File Version | 2 Bytes | Helps your app handle old vs. new files. |
| 6 | Created Date | 8 Bytes | Stored as a Unix Timestamp (integer). |
| 14 | Author | 64 Bytes | Encoded string (UTF-8). |
| 78 | Email | 64 Bytes | Encoded string (UTF-8). |
| 142 | ... | ... | Rest of the header (padded with zeros). |
| 256 | Data | Variable | Your actual RF driver code or binary data. |

---

## 2. Python Implementation

This script creates a file where the "Date Created" and "Author" are physically baked into the data.

```python
import struct
import time
import os

def create_file_with_permanent_props(path, author, email, data):
    # Format: 4s (Magic), H (Version), d (Timestamp/Date), 64s (Author), 64s (Email)
    header_format = "<4sH d 64s 64s"
    magic = b"RFD!"
    version = 1
    created_date = time.time() # Current time as a double
    
    author_b = author.encode('utf-8').ljust(64, b'\0')
    email_b = email.encode('utf-8').ljust(64, b'\0')
    
    header = struct.pack(header_format, magic, version, created_date, author_b, email_b)
    
    # Pad header to exactly 256 bytes to keep data alignment clean
    header = header.ljust(256, b'\0')
    
    with open(path, "wb") as f:
        f.write(header)
        f.write(data)

# Save the file
create_file_with_permanent_props("test_config.myext", "John Doe", "john@company.com", b"\x01\x02\x03")

```

---

## 3. Reading the Properties (Instant Access)

Because the properties are at the start, you can read them without loading a massive file. This is how Windows handles "Date Created" internally for its own formats.

```python
def get_permanent_props(path):
    with open(path, "rb") as f:
        # Read just the header
        header_bytes = f.read(256)
        
    header_format = "<4sH d 64s 64s"
    magic, ver, timestamp, author, email = struct.unpack(header_format, header_bytes[:struct.calcsize(header_format)])
    
    return {
        "Created": time.ctime(timestamp),
        "Author": author.decode('utf-8').strip('\x00'),
        "Email": email.decode('utf-8').strip('\x00')
    }

print(get_permanent_props("test_config.myext"))

```

---

## 4. Why this is the best solution for your RF Project

1. **Perforce Persistence:** Since the properties are bytes inside the file, Perforce treats them as part of the content. When a teammate syncs, they get the **exact** creation date and author info you wrote.
2. **No OS Dependence:** This works even if someone moves the file to Linux, macOS, or a cloud drive.
3. **Future Proofing:** If you later decide you need to store "Frequency Band" or "Calibration Value," you just add them to the `header_format`.

### Integrating with your PyQt App

In your PyQt application, you can make these "Properties" visible by:

* Adding a **"File Info"** menu item that runs the `get_permanent_props` function.
* Displaying the **Author** and **Date Created** in the bottom Status Bar as soon as a file is opened.

Would you like me to show you how to add a "Property Editor" dialog in PyQt so you can update these internal properties easily?
