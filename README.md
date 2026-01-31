# SAT Solver 🧩

This project is a **Python** implementation of a Boolean satisfiability (**SAT**) solver.

It was developed as a group of 3 for the **Fundamental Computer Science** (*Informatique Fondamentale*) course at the **Université Libre de Bruxelles (ULB)** during the third year of the Bachelor's degree (Academic Year 2025-2026).

The program accepts logical formulas (typically in CNF format) as input and determines their satisfiability—checking if there exists an assignment of variables that makes the formula true.

## 🚀 Features

* **SAT Resolution:** Implementation of resolution algorithms based on inference and propagation.
* **CNF Handling:** Efficient management of formulas in Conjunctive Normal Form.
* **Unit Tests:** Integrated test suite to verify the validity of solutions.
* **Modular Design:** Code separated into main logic (`project.py`) and utility functions (`utils.py`).

## 📂 Project Structure

Here is the file organization of the repository:

* `project.py`: The core of the solver, containing the main algorithm.
* `utils.py`: Helper functions for managing clauses and literals.
* `tests.py`: Test script to validate the solver's performance on various instances.
* `Rapport.pdf`: Detailed report explaining the theoretical approach, algorithms used, and results obtained.

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone https://github.com/stephanebdbd/SAT-solver.git
cd SAT-solver

```


2. **Prerequisites:**
* Python 3.x installed.
* No heavy external dependencies required (standard library only).



## 💻 Usage

To run the solver on a specific file or instance:

```bash
python3 project.py [arguments]

```

*(Note: Please adapt the command above according to the exact arguments expected by your script, e.g., the path to a `.cnf` file)*.

### Running Tests

To ensure everything is working correctly, you can execute the provided test suite:

```bash
python3 tests.py

```

## 📄 Documentation

For more details on the implementation, algorithm complexity, and design choices, please refer to the [Rapport.pdf](https://www.google.com/search?q=Rapport.pdf) file included in this repository.

## 👥 Authors

* **Stéphane Badi Budu** - [stephanebdbd](https://www.google.com/search?q=https://github.com/stephanebdbd)
* **Pietro NARCISI**
* **Nicolas NGANDO NGENA**

---

*Project realized for the Faculty of Sciences, ULB.*
