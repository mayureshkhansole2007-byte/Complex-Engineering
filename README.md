# Smart Vehicle Parking and Billing System (DS Project)

A full-stack, data-structure-powered Smart Parking System featuring a **Doubly Linked List** backend engine in C++, bidirectional synchronization with `parking_records.txt`, and an interactive **Web UI Dashboard**.

---

## 🏗️ Architecture & Data Structures

```
  +------------------------------------------------------------------+
  |                        Web UI Dashboard                          |
  | (2D Parking Bay, Live Elapsed Clocks, Search, Receipts, Reports) |
  +---------------------------------+--------------------------------+
                                    | HTTP / REST API (port 8000)
                                    v
  +------------------------------------------------------------------+
  |              Python Bridge Engine (parking_engine.py)            |
  |                - Doubly Linked List (VehicleNode)                |
  |                - Real-Time Simulation (1s = 1min)                |
  +---------------------------------+--------------------------------+
                                    | File Persistence
                                    v
  +------------------------------------------------------------------+
  |                    parking_records.txt                           |
  |      CAPACITY|20                                                 |
  |      REG|TYPE|SLOT|ENTRY_R|ENTRY_S|EXIT_R|EXIT_S|CHARGE|STATUS  |
  +---------------------------------+--------------------------------+
                                    ^ File Persistence
                                    |
  +---------------------------------+--------------------------------+
  |               C++ Core Engine (parking_system.cpp)               |
  |                - Doubly Linked List (struct Vehicle)             |
  |                - Console Interactive CLI Menu                    |
  +------------------------------------------------------------------+
```

### 1. Core Data Structure: Doubly Linked List
- **Node (`Vehicle` / `VehicleNode`)**:
  - `registration`: String (License plate, e.g. `MH-12-AB-1234`)
  - `type`: `"2"` (Two-wheeler) or `"4"` (Four-wheeler)
  - `slot`: Integer slot number ($1 \le \text{slot} \le \text{capacity}$)
  - `entryReal`, `entrySim`: Epoch timestamps
  - `exitReal`, `exitSim`: Epoch timestamps
  - `charge`: Calculated bill in ₹
  - `status`: `"PARKED"`, `"COMPLETED"`, or `"CANCELLED"`
  - `prev`, `next`: Pointers linking nodes in both directions for efficient sequential traversal, deletion, and rollback.

### 2. Time Complexities
- **Slot Allocation & Free-Slot Search**: $\mathcal{O}(N)$ where $N \le \text{Capacity}$
- **Vehicle Search by Plate**: $\mathcal{O}(N)$ traversal over the Doubly Linked List
- **Vehicle Exit & Billing**: $\mathcal{O}(N)$ lookup + $\mathcal{O}(1)$ in-place node update
- **Cancellation**: $\mathcal{O}(N)$ lookup + $\mathcal{O}(1)$ rollback
- **Daily Revenue Audit**: $\mathcal{O}(N)$ linear scan

### 3. Pricing & Billing Model
- **Two-Wheeler Rate**: ₹20.00 / hour
- **Four-Wheeler Rate**: ₹40.00 / hour
- **Formula**:
  $$\text{Duration} = \text{exitSim} - \text{entrySim}$$
  $$\text{Hours} = \max\left(1, \left\lceil \frac{\text{Duration}}{3600} \right\rceil\right)$$
  $$\text{Bill} = \text{Hours} \times \text{Rate}$$
- **Demo Mode**: 1 real second = 1 simulated minute (1 real minute = 1 simulated hour).

---

## 🚀 How to Run the Web UI

1. **Option 1 (One-click)**:
   - Double-click **`start.bat`**.
   - Your browser will automatically open to `http://localhost:8000`.

2. **Option 2 (Terminal)**:
   ```powershell
   python server.py 8000
   ```
   Open `http://localhost:8000` in your web browser.

---

## 💻 How to Run the C++ CLI Engine

The C++ source code is located in [`parking_system.cpp`](file:///c:/Users/Admin/Desktop/ds%20project/parking_system.cpp).

1. **Compile with g++**:
   ```powershell
   g++ -std=c++11 parking_system.cpp -o parking_system.exe
   ```
   *(Or double-click `compile_cpp.bat`)*

2. **Run the C++ Console Program**:
   ```powershell
   .\parking_system.exe
   ```
   Both the C++ executable and the Web UI share and update the exact same records in [`parking_records.txt`](file:///c:/Users/Admin/Desktop/ds%20project/parking_records.txt).

---

## ✨ Web UI Features

- 🅿️ **Interactive 2D Parking Bay**: Real-time visualization of slots, license plates, vehicle types, and live ticking timers.
- ⚡ **Live Billing Counter**: See simulated elapsed minutes and current estimated bill ticking up in real time.
- 🚗 **Vehicle Entry Modal**: Auto-allocates the next available slot and supports Two-Wheelers and Four-Wheelers.
- 🧾 **Exit & Printable Invoice**: Generates a clean receipt with duration breakdown and total charge.
- 🔍 **Search Engine**: Instant plate search traversing the linked list.
- 📊 **Daily Audit Report**: Tracks entries, exits, cancellations, and daily revenue.
- 📜 **Audit History Table**: Complete table of all past and current vehicle records.
