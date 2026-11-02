#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <ctime>
#include <iomanip>
#include <cmath>
#include <limits>
#include <cctype>
#include <cstdlib>
using namespace std;

const string FILE_NAME = "parking_records.txt";
const bool DEMO_MODE = true;

// Demo: 1 real second = 1 simulated minute.
// Therefore, 1 real minute = 1 simulated hour.
const int TIME_MULTIPLIER = DEMO_MODE ? 60 : 1;

string normalize(string s) {
    for (size_t i = 0; i < s.size(); i++)
        s[i] = toupper(static_cast<unsigned char>(s[i]));
    return s;
}

string formatTime(time_t t) {
    if (t <= 0) return "N/A";
    tm *p = localtime(&t);
    if (!p) return "N/A";

    stringstream ss;
    ss << put_time(p, "%d-%m-%Y %I:%M:%S %p");
    return ss.str();
}

string dateKey(time_t t) {
    if (t <= 0) return "";
    tm *p = localtime(&t);
    if (!p) return "";

    stringstream ss;
    ss << put_time(p, "%Y-%m-%d");
    return ss.str();
}

string readText(string prompt) {
    string value;
    cout << prompt;
    getline(cin, value);
    return value;
}

int readInt(string prompt, int minimum, int maximum) {
    while (true) {
        string input = readText(prompt);
        stringstream ss(input);
        int value;
        char extra;

        if (ss >> value && !(ss >> extra) &&
            value >= minimum && value <= maximum)
            return value;

        cout << "Invalid input. Enter a number from "
             << minimum << " to " << maximum << ".\n";
    }
}

// Doubly Linked List Node representing a Vehicle record
struct Vehicle {
    string registration;
    string type;        // "2" for Two-wheeler, "4" for Four-wheeler
    int slot;
    time_t entryReal;
    time_t entrySim;
    time_t exitReal;
    time_t exitSim;
    double charge;
    string status;      // "PARKED", "COMPLETED", "CANCELLED"
    Vehicle *prev;
    Vehicle *next;

    Vehicle() {
        slot = 0;
        entryReal = entrySim = 0;
        exitReal = exitSim = 0;
        charge = 0;
        prev = next = NULL;
    }
};

class SmartParkingSystem {
private:
    Vehicle *head;
    Vehicle *tail;
    int capacity;

public:
    double hourlyRate(string type) {
        return type == "2" ? 20.0 : 40.0;
    }

    // Calculate current simulated time for an active vehicle
    time_t currentSimTime(Vehicle *v) {
        if (v->status != "PARKED")
            return v->exitSim;

        time_t realNow = time(NULL);
        double elapsed = difftime(realNow, v->entryReal);

        if (elapsed < 0) elapsed = 0;

        return v->entrySim + static_cast<time_t>(elapsed * TIME_MULTIPLIER);
    }

    Vehicle* findVehicle(string registration) {
        registration = normalize(registration);
        Vehicle *current = head;
        Vehicle *latestMatch = NULL;

        while (current != NULL) {
            if (normalize(current->registration) == registration) {
                if (current->status == "PARKED")
                    return current;
                latestMatch = current;
            }
            current = current->next;
        }
        return latestMatch;
    }

    bool isSlotOccupied(int slot) {
        Vehicle *current = head;
        while (current != NULL) {
            if (current->status == "PARKED" && current->slot == slot)
                return true;
            current = current->next;
        }
        return false;
    }

    int findFreeSlot() {
        for (int i = 1; i <= capacity; i++)
            if (!isSlotOccupied(i))
                return i;
        return -1;
    }

    void appendVehicle(Vehicle *v) {
        if (head == NULL) {
            head = tail = v;
        } else {
            tail->next = v;
            v->prev = tail;
            tail = v;
        }
    }

    void displayVehicle(Vehicle *v) {
        cout << "\n--- Vehicle Details ---\n";
        cout << "Registration : " << v->registration << "\n";
        cout << "Vehicle type : "
             << (v->type == "2" ? "Two-wheeler" : "Four-wheeler")
             << "\n";
        cout << "Parking slot : " << v->slot << "\n";
        cout << "Entry time   : " << formatTime(v->entrySim) << "\n";

        if (v->status == "PARKED") {
            time_t nowSim = currentSimTime(v);
            double seconds = difftime(nowSim, v->entrySim);

            cout << "Current demo time : " << formatTime(nowSim) << "\n";
            cout << "Elapsed duration  : "
                 << fixed << setprecision(0)
                 << seconds / 60.0 << " simulated minute(s)\n";
            cout << "Status       : PARKED\n";
        } else {
            cout << "Exit time    : " << formatTime(v->exitSim) << "\n";
            cout << "Bill         : Rs. " << fixed
                 << setprecision(2) << v->charge << "\n";
            cout << "Status       : " << v->status << "\n";
        }
    }

    SmartParkingSystem() {
        head = tail = NULL;
        capacity = 0;
        loadFromFile();
    }

    ~SmartParkingSystem() {
        Vehicle *current = head;
        while (current != NULL) {
            Vehicle *next = current->next;
            delete current;
            current = next;
        }
    }

    int getCapacity() const { return capacity; }
    void setCapacity(int cap) { capacity = cap; saveToFile(); }
    Vehicle* getHead() const { return head; }

    bool saveToFile() {
        ofstream file(FILE_NAME.c_str());
        if (!file) {
            cout << "ERROR: Could not save parking_records.txt\n";
            return false;
        }

        file << "CAPACITY|" << capacity << "\n";

        Vehicle *v = head;
        while (v != NULL) {
            file << v->registration << "|"
                 << v->type << "|"
                 << v->slot << "|"
                 << static_cast<long long>(v->entryReal) << "|"
                 << static_cast<long long>(v->entrySim) << "|"
                 << static_cast<long long>(v->exitReal) << "|"
                 << static_cast<long long>(v->exitSim) << "|"
                 << v->charge << "|"
                 << v->status << "\n";
            v = v->next;
        }

        file.close();
        if (!file) {
            cout << "ERROR: File write failed.\n";
            return false;
        }
        return true;
    }

    void loadFromFile() {
        ifstream file(FILE_NAME.c_str());
        if (!file) {
            cout << "No saved records found. Starting a new system.\n";
            return;
        }

        string line;
        if (!getline(file, line)) return;

        if (line.find("CAPACITY|") == 0) {
            capacity = atoi(line.substr(9).c_str());
        } else {
            cout << "File header invalid. Starting without loaded records.\n";
            return;
        }

        while (getline(file, line)) {
            if (line.empty()) continue;

            string fields[9];
            stringstream ss(line);
            int count = 0;
            string field;

            while (getline(ss, field, '|') && count < 9)
                fields[count++] = field;

            Vehicle *v = new Vehicle();

            if (count == 9) {
                v->registration = fields[0];
                v->type = fields[1];
                v->slot = atoi(fields[2].c_str());
                v->entryReal = static_cast<time_t>(atoll(fields[3].c_str()));
                v->entrySim = static_cast<time_t>(atoll(fields[4].c_str()));
                v->exitReal = static_cast<time_t>(atoll(fields[5].c_str()));
                v->exitSim = static_cast<time_t>(atoll(fields[6].c_str()));
                v->charge = atof(fields[7].c_str());
                v->status = fields[8];
            } else if (count == 7) {
                v->registration = fields[0];
                v->type = fields[1];
                v->slot = atoi(fields[2].c_str());
                v->entryReal = static_cast<time_t>(atoll(fields[3].c_str()));
                v->entrySim = v->entryReal;
                v->exitReal = static_cast<time_t>(atoll(fields[4].c_str()));
                v->exitSim = v->exitReal;
                v->charge = atof(fields[5].c_str());
                v->status = fields[6];
            } else {
                delete v;
                cout << "Skipped an invalid record.\n";
                continue;
            }

            if (v->registration.empty() ||
                (v->type != "2" && v->type != "4") ||
                v->slot < 1 || (capacity > 0 && v->slot > capacity) ||
                v->entryReal <= 0 || v->entrySim <= 0 ||
                (v->status != "PARKED" &&
                 v->status != "COMPLETED" &&
                 v->status != "CANCELLED")) {
                delete v;
                cout << "Skipped an invalid record.\n";
                continue;
            }

            appendVehicle(v);
        }

        cout << "Saved records loaded successfully.\n";
    }

    bool addEntryDirect(string reg, string type, int &assignedSlot) {
        reg = normalize(reg);
        if (reg.empty() || reg.find('|') != string::npos) return false;

        int occupied = 0;
        for (Vehicle *v = head; v != NULL; v = v->next)
            if (v->status == "PARKED") occupied++;

        if (capacity <= 0 || occupied >= capacity) return false;

        Vehicle *existing = findVehicle(reg);
        if (existing != NULL && existing->status == "PARKED") return false;

        int slot = findFreeSlot();
        if (slot == -1) return false;

        Vehicle *v = new Vehicle();
        v->registration = reg;
        v->type = (type == "2" ? "2" : "4");
        v->slot = slot;
        v->entryReal = time(NULL);
        v->entrySim = v->entryReal;
        v->status = "PARKED";

        appendVehicle(v);

        if (!saveToFile()) {
            if (v->prev) v->prev->next = NULL;
            else head = NULL;
            tail = v->prev;
            delete v;
            return false;
        }

        assignedSlot = slot;
        return true;
    }

    void vehicleEntry() {
        if (capacity <= 0) {
            capacity = readInt("Set parking capacity (1-100): ", 1, 100);
        }

        int occupied = 0;
        for (Vehicle *v = head; v != NULL; v = v->next)
            if (v->status == "PARKED") occupied++;

        if (occupied >= capacity) {
            cout << "Parking is FULL!\n";
            return;
        }

        string reg = normalize(readText("Registration number: "));
        if (reg.empty() || reg.find('|') != string::npos) {
            cout << "Invalid registration number.\n";
            return;
        }

        Vehicle *existing = findVehicle(reg);
        if (existing != NULL && existing->status == "PARKED") {
            cout << "This vehicle is already parked.\n";
            return;
        }

        cout << "1. Two-wheeler (Rs.20/hour)\n";
        cout << "2. Four-wheeler (Rs.40/hour)\n";
        int choice = readInt("Choose vehicle type: ", 1, 2);

        Vehicle *v = new Vehicle();
        v->registration = reg;
        v->type = (choice == 1 ? "2" : "4");
        v->slot = findFreeSlot();
        v->entryReal = time(NULL);
        v->entrySim = v->entryReal;
        v->status = "PARKED";

        appendVehicle(v);

        if (!saveToFile()) {
            if (v->prev) v->prev->next = NULL;
            else head = NULL;
            tail = v->prev;
            delete v;
            cout << "Entry cancelled because saving failed.\n";
            return;
        }

        cout << "\nVehicle entry successful!\n";
        cout << "Assigned slot: " << v->slot << "\n";
        cout << "Entry timestamp: " << formatTime(v->entrySim) << "\n";
        cout << "Demo Mode: " << (DEMO_MODE ? "ON" : "OFF") << "\n";
    }

    void vehicleExit() {
        string reg = normalize(readText("Registration number to exit: "));
        Vehicle *v = findVehicle(reg);

        if (v == NULL || v->status != "PARKED") {
            cout << "No active parked vehicle found.\n";
            return;
        }

        time_t oldExitReal = v->exitReal;
        time_t oldExitSim = v->exitSim;
        double oldCharge = v->charge;
        string oldStatus = v->status;

        v->exitReal = time(NULL);
        v->exitSim = currentSimTime(v);

        double duration = difftime(v->exitSim, v->entrySim);
        if (duration < 0) duration = 0;

        int hours = static_cast<int>(ceil(duration / 3600.0));
        if (hours < 1) hours = 1;

        v->charge = hours * hourlyRate(v->type);
        v->status = "COMPLETED";

        if (!saveToFile()) {
            v->exitReal = oldExitReal;
            v->exitSim = oldExitSim;
            v->charge = oldCharge;
            v->status = oldStatus;
            cout << "Exit update rolled back because saving failed.\n";
            return;
        }

        cout << "\n========== PARKING BILL ==========\n";
        cout << "Registration : " << v->registration << "\n";
        cout << "Vehicle type : "
             << (v->type == "2" ? "Two-wheeler" : "Four-wheeler")
             << "\n";
        cout << "Entry time   : " << formatTime(v->entrySim) << "\n";
        cout << "Exit time    : " << formatTime(v->exitSim) << "\n";
        cout << "Duration     : " << fixed << setprecision(0)
             << duration / 3600.0 << " simulated hour(s)\n";
        cout << "Chargeable hours: " << hours << "\n";
        cout << "Hourly rate  : Rs. " << hourlyRate(v->type) << "\n";
        cout << "TOTAL BILL   : Rs. " << v->charge << "\n";
        cout << "==================================\n";
    }

    void parkingStatus() {
        int occupied = 0;
        cout << "\n--- Parking Status ---\n";

        for (int slot = 1; slot <= capacity; slot++) {
            Vehicle *v = head;
            bool found = false;

            while (v != NULL) {
                if (v->status == "PARKED" && v->slot == slot) {
                    cout << "Slot " << slot << ": OCCUPIED - "
                         << v->registration << "\n";
                    occupied++;
                    found = true;
                    break;
                }
                v = v->next;
            }

            if (!found)
                cout << "Slot " << slot << ": AVAILABLE\n";
        }

        cout << "Occupied: " << occupied
             << " | Available: " << capacity - occupied << "\n";
    }

    void searchVehicle() {
        string reg = normalize(readText("Registration to search: "));
        Vehicle *v = findVehicle(reg);

        if (v == NULL) cout << "Vehicle not found.\n";
        else displayVehicle(v);
    }

    void cancelEntry() {
        string reg = normalize(readText("Registration to cancel: "));
        Vehicle *v = findVehicle(reg);

        if (v == NULL || v->status != "PARKED") {
            cout << "No active parked vehicle found.\n";
            return;
        }

        string confirm = normalize(readText("Confirm cancellation? (Y/N): "));
        if (confirm != "Y") {
            cout << "Cancellation aborted.\n";
            return;
        }

        time_t oldExitReal = v->exitReal;
        time_t oldExitSim = v->exitSim;
        string oldStatus = v->status;
        double oldCharge = v->charge;

        v->exitReal = time(NULL);
        v->exitSim = currentSimTime(v);
        v->charge = 0;
        v->status = "CANCELLED";

        if (!saveToFile()) {
            v->exitReal = oldExitReal;
            v->exitSim = oldExitSim;
            v->status = oldStatus;
            v->charge = oldCharge;
            cout << "Cancellation rolled back because saving failed.\n";
            return;
        }

        cout << "Entry cancelled. Charge: Rs. 0\n";
    }

    void dailyReport() {
        string today = dateKey(time(NULL));
        int entries = 0, exits = 0, cancellations = 0;
        double revenue = 0;

        for (Vehicle *v = head; v != NULL; v = v->next) {
            if (dateKey(v->entrySim) == today)
                entries++;

            if (v->status == "COMPLETED" &&
                dateKey(v->exitSim) == today) {
                exits++;
                revenue += v->charge;
            }

            if (v->status == "CANCELLED" &&
                dateKey(v->exitSim) == today)
                cancellations++;
        }

        cout << "\n--- Daily Report (system date: " << today << ") ---\n";
        cout << "Entries recorded today : " << entries << "\n";
        cout << "Completed exits today  : " << exits << "\n";
        cout << "Cancellations today    : " << cancellations << "\n";
        cout << "Total revenue today    : Rs. "
             << fixed << setprecision(2) << revenue << "\n";
        cout << "Note: Demo timestamps are simulated.\n";
    }

    void allRecords() {
        if (head == NULL) {
            cout << "No vehicle records available.\n";
            return;
        }

        Vehicle *v = head;
        while (v != NULL) {
            displayVehicle(v);
            v = v->next;
        }
    }

    void run() {
        cout << "\n====================================\n";
        cout << " SMART VEHICLE PARKING AND BILLING\n";
        cout << "====================================\n";
        cout << "Demo Mode: " << (DEMO_MODE ? "ON" : "OFF") << "\n";
        cout << "1 real minute = 1 simulated hour\n";

        if (capacity <= 0) {
            capacity = readInt("Enter parking capacity (1-100): ", 1, 100);
            saveToFile();
        }

        while (true) {
            cout << "\n========== MAIN MENU ==========\n";
            cout << "1. Vehicle Entry\n";
            cout << "2. Vehicle Exit and Billing\n";
            cout << "3. Parking Status\n";
            cout << "4. Search Vehicle\n";
            cout << "5. Cancel Parking Entry\n";
            cout << "6. Daily Revenue Report\n";
            cout << "7. Display All Records\n";
            cout << "8. Save and Exit\n";

            int choice = readInt("Enter choice (1-8): ", 1, 8);

            switch (choice) {
                case 1: vehicleEntry(); break;
                case 2: vehicleExit(); break;
                case 3: parkingStatus(); break;
                case 4: searchVehicle(); break;
                case 5: cancelEntry(); break;
                case 6: dailyReport(); break;
                case 7: allRecords(); break;
                case 8:
                    saveToFile();
                    cout << "Records saved. Goodbye!\n";
                    return;
            }
        }
    }
};

int main() {
    SmartParkingSystem system;
    system.run();
    return 0;
}
