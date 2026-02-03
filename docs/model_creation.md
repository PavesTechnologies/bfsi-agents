# 📄 How to Create a New Database Model

This guide explains how to create a new database table (model) in the project and apply migrations correctly.

---

## ✅ Step 1: Navigate to the Specific Agent

First, go to the required agent directory.

Example:

```bash
cd agents/intake
```

(Adjust the path based on your agent name.)

---

## ✅ Step 2: Create a New Model File

Inside the `src/models/` folder, create a new Python file for your table.

Example:

```bash
touch src/models/user.py
```

Each file should represent one logical table (or related group of tables).

---

## ✅ Step 3: Define the Model Class

Open the new file and define your model.

Example: `src/models/user.py`

```python
from sqlalchemy import Column, Integer, String
from src.utils.migration_database import Base   # <-- import Base compulsory if not table not created

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
```

### Important Rules

* Always import `Base` from `src.utils.migration_database`.
* All models must inherit from `Base`.
* Define `__tablename__` explicitly.
* Use existing model files as references.

---

## ✅ Step 4: Verify Model Structure

Before migrating, make sure:

* The file is inside `src/models/`.
* The class extends `Base`.
* Column types and constraints are correct.
* No syntax errors exist.

You can compare with other model files for guidance.

---

## ✅ Step 5: Generate and Apply Migration

After creating or updating the model, run the migration command.

```bash
poetry run migration "description"
```

Example:

```bash
poetry run migration "add user table"
```

This will:

1. Auto-generate the migration file
2. Apply it to the database
3. Update schema version

---

## ✅ Step 6: Verify Database Changes

After migration, confirm that the table exists:

* Check in your database client
* Or use SQL queries

Example:

```sql
SELECT * FROM users LIMIT 1;
```

---

## ⚠️ Best Practices

* Always review generated migration files before committing.
* Do not edit the database manually.
* Keep one logical table per model file.
* Commit model and migration together.
* Everytime keep pushing to repo after migration
---

## 📌 Recommended Workflow (Summary)

```text
1. cd agents/<agent_name>
2. Create new file in src/models/
3. Define model class using Base
4. Verify code
5. Run: poetry run migration "description"
6. Check database
```

---

## 🚀 Example End-to-End

```bash
cd agents/intake
touch src/models/payment.py
# Edit file and add model
poetry run migration "add payment table"
```

Done ✅

---