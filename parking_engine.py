import os
import time
import math
from datetime import datetime

FILE_NAME = "parking_records.txt"
DEMO_MODE = True
TIME_MULTIPLIER = 60 if DEMO_MODE else 1

def format_time(timestamp: int) -> str:
    if not timestamp or timestamp <= 0:
        return "N/A"
    try:
        dt = datetime.fromtimestamp(timestamp)
        # Formatted like C++ put_time: "%d-%m-%Y %I:%M:%S %p"
        return dt.strftime("%d-%m-%Y %I:%M:%S %p")
    except Exception:
        return "N/A"

def date_key(timestamp: int) -> str:
    if not timestamp or timestamp <= 0:
        return ""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""

class VehicleNode:
    """Doubly linked list node for a vehicle record matching C++ struct Vehicle"""
    def __init__(self, registration="", vtype="4", slot=0,
                 entry_real=0, entry_sim=0, exit_real=0, exit_sim=0,
                 charge=0.0, status="PARKED"):
        self.registration = registration.upper().strip()
        self.type = str(vtype)              # "2" (two-wheeler) or "4" (four-wheeler)
        self.slot = int(slot)
        self.entry_real = int(entry_real)
        self.entry_sim = int(entry_sim)
        self.exit_real = int(exit_real)
        self.exit_sim = int(exit_sim)
        self.charge = float(charge)
        self.status = status                # "PARKED", "COMPLETED", "CANCELLED"
        self.prev = None
        self.next = None

    def to_dict(self, current_sim_calc=None):
        sim_exit = self.exit_sim
        if self.status == "PARKED" and current_sim_calc:
            sim_now = current_sim_calc(self)
        else:
            sim_now = sim_exit

        elapsed_sec = max(0, sim_now - self.entry_sim) if sim_now and self.entry_sim else 0
        elapsed_mins = round(elapsed_sec / 60.0, 1)
        elapsed_hours = round(elapsed_sec / 3600.0, 2)
        chargeable_hours = max(1, math.ceil(elapsed_sec / 3600.0)) if elapsed_sec > 0 else 1
        est_charge = chargeable_hours * (20.0 if self.type == "2" else 40.0)

        return {
            "registration": self.registration,
            "type": self.type,
            "type_label": "Two-wheeler (🏍️)" if self.type == "2" else "Four-wheeler (🚗)",
            "rate": 20.0 if self.type == "2" else 40.0,
            "slot": self.slot,
            "entry_real": self.entry_real,
            "entry_sim": self.entry_sim,
            "entry_time_str": format_time(self.entry_sim),
            "exit_real": self.exit_real,
            "exit_sim": self.exit_sim,
            "exit_time_str": format_time(self.exit_sim) if self.exit_sim else "Active",
            "sim_now": sim_now,
            "sim_now_str": format_time(sim_now),
            "elapsed_seconds": elapsed_sec,
            "elapsed_minutes": elapsed_mins,
            "elapsed_hours": elapsed_hours,
            "chargeable_hours": chargeable_hours,
            "charge": self.charge if self.status != "PARKED" else est_charge,
            "status": self.status
        }


class SmartParkingEngine:
    """Core Parking Management Engine using Doubly Linked List matching C++ implementation"""
    def __init__(self, file_path=FILE_NAME):
        self.file_path = file_path
        self.head = None
        self.tail = None
        self.capacity = 20  # Default initial capacity if none set
        self.load_from_file()

    def hourly_rate(self, vtype: str) -> float:
        return 20.0 if str(vtype) == "2" else 40.0

    def current_sim_time(self, v: VehicleNode) -> int:
        if v.status != "PARKED":
            return v.exit_sim
        real_now = int(time.time())
        elapsed = real_now - v.entry_real
        if elapsed < 0:
            elapsed = 0
        return int(v.entry_sim + (elapsed * TIME_MULTIPLIER))

    def append_node(self, node: VehicleNode):
        if self.head is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            node.prev = self.tail
            self.tail = node

    def is_slot_occupied(self, slot: int) -> bool:
        curr = self.head
        while curr:
            if curr.status == "PARKED" and curr.slot == slot:
                return True
            curr = curr.next
        return False

    def find_free_slot(self) -> int:
        for i in range(1, self.capacity + 1):
            if not self.is_slot_occupied(i):
                return i
        return -1

    def find_vehicle(self, registration: str):
        reg = registration.upper().strip()
        curr = self.head
        latest_match = None
        while curr:
            if curr.registration.upper() == reg:
                if curr.status == "PARKED":
                    return curr
                latest_match = curr
            curr = curr.next
        return latest_match

    def save_to_file(self) -> bool:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(f"CAPACITY|{self.capacity}\n")
                curr = self.head
                while curr:
                    line = (
                        f"{curr.registration}|"
                        f"{curr.type}|"
                        f"{curr.slot}|"
                        f"{curr.entry_real}|"
                        f"{curr.entry_sim}|"
                        f"{curr.exit_real}|"
                        f"{curr.exit_sim}|"
                        f"{curr.charge:.2f}|"
                        f"{curr.status}\n"
                    )
                    f.write(line)
                    curr = curr.next
            return True
        except Exception as e:
            print(f"Error saving to file: {e}")
            return False

    def load_from_file(self):
        self.head = None
        self.tail = None
        if not os.path.exists(self.file_path):
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if not lines:
                    return

                first = lines[0].strip()
                if first.startswith("CAPACITY|"):
                    try:
                        self.capacity = int(first.split("|")[1])
                    except Exception:
                        self.capacity = 20
                    data_lines = lines[1:]
                else:
                    data_lines = lines

                for line in data_lines:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split("|")
                    if len(parts) >= 9:
                        v = VehicleNode(
                            registration=parts[0],
                            vtype=parts[1],
                            slot=int(parts[2]),
                            entry_real=int(parts[3]),
                            entry_sim=int(parts[4]),
                            exit_real=int(parts[5]),
                            exit_sim=int(parts[6]),
                            charge=float(parts[7]),
                            status=parts[8]
                        )
                        self.append_node(v)
                    elif len(parts) >= 7:
                        # Legacy 7 fields format
                        v = VehicleNode(
                            registration=parts[0],
                            vtype=parts[1],
                            slot=int(parts[2]),
                            entry_real=int(parts[3]),
                            entry_sim=int(parts[3]),
                            exit_real=int(parts[4]),
                            exit_sim=int(parts[4]),
                            charge=float(parts[5]),
                            status=parts[6]
                        )
                        self.append_node(v)
        except Exception as e:
            print(f"Error loading records: {e}")

    def set_capacity(self, cap: int) -> dict:
        if cap < 1 or cap > 100:
            return {"success": False, "message": "Capacity must be between 1 and 100."}
        # Check if current parked count exceeds new capacity
        occupied = 0
        curr = self.head
        while curr:
            if curr.status == "PARKED":
                occupied += 1
            curr = curr.next
        if cap < occupied:
            return {
                "success": False,
                "message": f"Cannot set capacity to {cap}. There are currently {occupied} parked vehicles."
            }
        self.capacity = cap
        self.save_to_file()
        return {"success": True, "capacity": self.capacity}

    def vehicle_entry(self, registration: str, vtype: str) -> dict:
        self.load_from_file() # Ensure sync with any external updates
        reg = registration.upper().strip()
        if not reg:
            return {"success": False, "message": "Registration number cannot be empty."}
        if "|" in reg:
            return {"success": False, "message": "Registration number cannot contain '|'."}

        # Check total occupied
        occupied = 0
        curr = self.head
        while curr:
            if curr.status == "PARKED":
                occupied += 1
            curr = curr.next

        if occupied >= self.capacity:
            return {"success": False, "message": f"Parking is FULL! (Capacity: {self.capacity})"}

        # Check if already parked
        existing = self.find_vehicle(reg)
        if existing and existing.status == "PARKED":
            return {
                "success": False,
                "message": f"Vehicle {reg} is already parked in Slot #{existing.slot}!"
            }

        slot = self.find_free_slot()
        if slot == -1:
            return {"success": False, "message": "No available parking slot found."}

        now_real = int(time.time())
        now_sim = now_real

        v = VehicleNode(
            registration=reg,
            vtype="2" if str(vtype) == "2" else "4",
            slot=slot,
            entry_real=now_real,
            entry_sim=now_sim,
            status="PARKED"
        )
        self.append_node(v)
        self.save_to_file()

        return {
            "success": True,
            "message": f"Vehicle {reg} parked successfully in Slot #{slot}!",
            "slot": slot,
            "vehicle": v.to_dict(self.current_sim_time)
        }

    def vehicle_exit(self, registration: str) -> dict:
        self.load_from_file()
        reg = registration.upper().strip()
        v = self.find_vehicle(reg)

        if not v or v.status != "PARKED":
            return {"success": False, "message": f"No active parked vehicle found for '{reg}'."}

        now_real = int(time.time())
        sim_exit = self.current_sim_time(v)

        duration = max(0, sim_exit - v.entry_sim)
        hours = math.ceil(duration / 3600.0)
        if hours < 1:
            hours = 1

        rate = self.hourly_rate(v.type)
        total_bill = hours * rate

        v.exit_real = now_real
        v.exit_sim = sim_exit
        v.charge = total_bill
        v.status = "COMPLETED"

        self.save_to_file()

        details = v.to_dict()
        details["duration_seconds"] = duration
        details["duration_hours_sim"] = round(duration / 3600.0, 2)
        details["chargeable_hours"] = hours
        details["hourly_rate"] = rate

        return {
            "success": True,
            "message": f"Vehicle {reg} exited. Bill: Rs. {total_bill:.2f}",
            "bill": details
        }

    def cancel_entry(self, registration: str) -> dict:
        self.load_from_file()
        reg = registration.upper().strip()
        v = self.find_vehicle(reg)

        if not v or v.status != "PARKED":
            return {"success": False, "message": f"No active parked vehicle found for '{reg}'."}

        now_real = int(time.time())
        sim_exit = self.current_sim_time(v)

        v.exit_real = now_real
        v.exit_sim = sim_exit
        v.charge = 0.0
        v.status = "CANCELLED"

        self.save_to_file()

        return {
            "success": True,
            "message": f"Parking entry for {reg} has been CANCELLED. Charge: Rs. 0.00",
            "vehicle": v.to_dict()
        }

    def search_vehicle(self, query: str) -> dict:
        self.load_from_file()
        q = query.upper().strip()
        if not q:
            return {"success": False, "message": "Search query cannot be empty.", "results": []}

        matches = []
        curr = self.head
        while curr:
            if q in curr.registration.upper():
                matches.append(curr.to_dict(self.current_sim_time))
            curr = curr.next

        # Sort so active parked vehicles appear first, then newest
        matches.reverse()
        matches.sort(key=lambda x: 0 if x["status"] == "PARKED" else 1)

        return {
            "success": True,
            "query": q,
            "count": len(matches),
            "results": matches
        }

    def get_parking_status(self) -> dict:
        self.load_from_file()
        slots = []
        occupied_count = 0
        two_wheeler_count = 0
        four_wheeler_count = 0

        # Build slot map
        slot_map = {}
        curr = self.head
        while curr:
            if curr.status == "PARKED":
                slot_map[curr.slot] = curr
            curr = curr.next

        for slot_num in range(1, self.capacity + 1):
            if slot_num in slot_map:
                v = slot_map[slot_num]
                occupied_count += 1
                if v.type == "2":
                    two_wheeler_count += 1
                else:
                    four_wheeler_count += 1
                slots.append({
                    "slot": slot_num,
                    "is_occupied": True,
                    "vehicle": v.to_dict(self.current_sim_time)
                })
            else:
                slots.append({
                    "slot": slot_num,
                    "is_occupied": False,
                    "vehicle": None
                })

        available_count = self.capacity - occupied_count
        occupancy_rate = round((occupied_count / self.capacity) * 100, 1) if self.capacity > 0 else 0

        return {
            "capacity": self.capacity,
            "occupied": occupied_count,
            "available": available_count,
            "two_wheelers": two_wheeler_count,
            "four_wheelers": four_wheeler_count,
            "occupancy_rate": occupancy_rate,
            "slots": slots,
            "demo_mode": DEMO_MODE,
            "time_multiplier": TIME_MULTIPLIER,
            "system_time": format_time(int(time.time()))
        }

    def daily_report(self) -> dict:
        self.load_from_file()
        today = date_key(int(time.time()))
        entries = 0
        exits = 0
        cancellations = 0
        revenue = 0.0

        curr = self.head
        while curr:
            if date_key(curr.entry_sim) == today:
                entries += 1
            if curr.status == "COMPLETED" and date_key(curr.exit_sim) == today:
                exits += 1
                revenue += curr.charge
            if curr.status == "CANCELLED" and date_key(curr.exit_sim) == today:
                cancellations += 1
            curr = curr.next

        return {
            "date": today,
            "entries_today": entries,
            "exits_today": exits,
            "cancellations_today": cancellations,
            "total_revenue": revenue,
            "formatted_revenue": f"Rs. {revenue:.2f}"
        }

    def all_records(self) -> list:
        self.load_from_file()
        records = []
        curr = self.head
        while curr:
            records.append(curr.to_dict(self.current_sim_time))
            curr = curr.next
        records.reverse()  # Latest first
        return records


if __name__ == "__main__":
    # Self-test
    engine = SmartParkingEngine()
    print("Capacity:", engine.capacity)
    status = engine.get_parking_status()
    print("Occupied:", status["occupied"], "Available:", status["available"])
    print("Report:", engine.daily_report())
