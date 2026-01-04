# Audit Trail - Code Reference

Quick reference for the audit trail implementation.

## Database Schema

### Audit Log Table
```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_value TEXT,  -- JSON
    new_value TEXT,  -- JSON
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
```

### Soft Delete Column
```sql
ALTER TABLE patients ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE visits ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE investigations ADD COLUMN is_deleted INTEGER DEFAULT 0;
ALTER TABLE procedures ADD COLUMN is_deleted INTEGER DEFAULT 0;
```

## Core Functions

### Log Audit Entry
```python
def log_audit(self, table_name: str, record_id: int, operation: str,
              old_value: dict = None, new_value: dict = None):
    """Log an audit entry."""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        old_json = json.dumps(old_value) if old_value else None
        new_json = json.dumps(new_value) if new_value else None

        cursor.execute("""
            INSERT INTO audit_log (table_name, record_id, operation, old_value, new_value)
            VALUES (?, ?, ?, ?, ?)
        """, (table_name, record_id, operation, old_json, new_json))
```

### Get Audit History
```python
def get_audit_history(self, table_name: str = None, record_id: int = None,
                      limit: int = 100) -> list[dict]:
    """Get audit history, optionally filtered by table/record."""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if table_name:
            query += " AND table_name = ?"
            params.append(table_name)

        if record_id is not None:
            query += " AND record_id = ?"
            params.append(record_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            entry = dict(row)
            # Parse JSON values
            if entry.get('old_value'):
                try:
                    entry['old_value'] = json.loads(entry['old_value'])
                except:
                    pass
            if entry.get('new_value'):
                try:
                    entry['new_value'] = json.loads(entry['new_value'])
                except:
                    pass
            results.append(entry)

        return results
```

### Get Patient Audit History
```python
def get_patient_audit_history(self, patient_id: int) -> list[dict]:
    """Get all audit entries related to a patient."""
    audit_entries = []

    # Patient record changes
    patient_audits = self.get_audit_history(table_name="patients", record_id=patient_id, limit=1000)
    audit_entries.extend(patient_audits)

    # Visit changes
    visit_ids = [row[0] for row in cursor.execute("SELECT id FROM visits WHERE patient_id = ?", (patient_id,))]
    for visit_id in visit_ids:
        visit_audits = self.get_audit_history(table_name="visits", record_id=visit_id, limit=1000)
        audit_entries.extend(visit_audits)

    # Investigation changes
    inv_ids = [row[0] for row in cursor.execute("SELECT id FROM investigations WHERE patient_id = ?", (patient_id,))]
    for inv_id in inv_ids:
        inv_audits = self.get_audit_history(table_name="investigations", record_id=inv_id, limit=1000)
        audit_entries.extend(inv_audits)

    # Procedure changes
    proc_ids = [row[0] for row in cursor.execute("SELECT id FROM procedures WHERE patient_id = ?", (patient_id,))]
    for proc_id in proc_ids:
        proc_audits = self.get_audit_history(table_name="procedures", record_id=proc_id, limit=1000)
        audit_entries.extend(proc_audits)

    # Sort by timestamp descending
    audit_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    return audit_entries
```

## Integration Examples

### Add Patient with Audit
```python
def add_patient(self, patient: Patient) -> Patient:
    """Add a new patient."""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        uhid = self._generate_uhid()
        cursor.execute("""
            INSERT INTO patients (uhid, name, age, gender, phone, address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (uhid, patient.name, patient.age, patient.gender,
              patient.phone, patient.address))
        patient.id = cursor.lastrowid
        patient.uhid = uhid

        # Log audit
        self.log_audit(
            table_name="patients",
            record_id=patient.id,
            operation="INSERT",
            new_value={
                "uhid": uhid,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "phone": patient.phone,
                "address": patient.address
            }
        )

        return patient
```

### Update Patient with Audit (Changed Fields Only)
```python
def update_patient(self, patient: Patient) -> bool:
    """Update patient details."""
    with self.get_connection() as conn:
        cursor = conn.cursor()

        # Get old values for audit log
        cursor.execute("SELECT * FROM patients WHERE id = ?", (patient.id,))
        old_row = cursor.fetchone()
        if not old_row:
            return False

        old_data = dict(old_row)

        # Update patient
        cursor.execute("""
            UPDATE patients
            SET name = ?, age = ?, gender = ?, phone = ?, address = ?
            WHERE id = ?
        """, (patient.name, patient.age, patient.gender,
              patient.phone, patient.address, patient.id))

        if cursor.rowcount > 0:
            # Log only changed fields
            new_data = {
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "phone": patient.phone,
                "address": patient.address
            }

            changed_fields_old = {}
            changed_fields_new = {}

            for key in new_data:
                if old_data.get(key) != new_data[key]:
                    changed_fields_old[key] = old_data.get(key)
                    changed_fields_new[key] = new_data[key]

            if changed_fields_old:  # Only log if something actually changed
                self.log_audit(
                    table_name="patients",
                    record_id=patient.id,
                    operation="UPDATE",
                    old_value=changed_fields_old,
                    new_value=changed_fields_new
                )

            return True

        return False
```

### Soft Delete with Audit
```python
def delete_patient(self, patient_id: int) -> bool:
    """Soft delete a patient."""
    with self.get_connection() as conn:
        cursor = conn.cursor()

        # Get patient data for audit
        cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        old_row = cursor.fetchone()
        if not old_row:
            return False

        old_data = dict(old_row)

        # Soft delete
        cursor.execute("UPDATE patients SET is_deleted = 1 WHERE id = ?", (patient_id,))

        if cursor.rowcount > 0:
            self.log_audit(
                table_name="patients",
                record_id=patient_id,
                operation="DELETE",
                old_value={
                    "uhid": old_data.get("uhid"),
                    "name": old_data.get("name"),
                    "age": old_data.get("age"),
                    "gender": old_data.get("gender")
                }
            )
            return True

        return False
```

### Query with Soft Delete Filter
```python
def get_all_patients(self) -> List[Patient]:
    """Get all patients."""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE is_deleted = 0 ORDER BY name")
        return [Patient(**dict(row)) for row in cursor.fetchall()]

def get_patient(self, patient_id: int) -> Optional[Patient]:
    """Get patient by ID."""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE id = ? AND is_deleted = 0", (patient_id,))
        row = cursor.fetchone()
        if row:
            return Patient(**dict(row))
        return None
```

## UI Integration

### Add Audit History Button
```python
# In central_panel.py set_patient() method

# Create audit history button
self.audit_history_btn = ft.IconButton(
    icon=ft.Icons.HISTORY,
    tooltip="View audit history",
    on_click=self._show_audit_history,
    icon_size=20,
)

self.patient_header.content = ft.Row([
    ft.Column([
        ft.Text(header_text, size=18, weight=ft.FontWeight.BOLD),
        ft.Text(" | ".join(details), size=13, color=ft.Colors.GREY_600),
    ], spacing=2),
    self.audit_history_btn,  # Add button to header
], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
```

### Show Audit Dialog
```python
def _show_audit_history(self, e):
    """Show audit history dialog for current patient."""
    if self.current_patient and e.page:
        self.audit_dialog.show(e.page, self.current_patient)
```

## Query Examples

### SQL Direct Queries
```sql
-- Get all audit entries for a patient
SELECT * FROM audit_log
WHERE table_name = 'patients'
AND record_id = 1
ORDER BY timestamp DESC;

-- Get all UPDATE operations
SELECT * FROM audit_log
WHERE operation = 'UPDATE'
ORDER BY timestamp DESC;

-- Get recent changes (last 7 days)
SELECT * FROM audit_log
WHERE timestamp >= datetime('now', '-7 days')
ORDER BY timestamp DESC;

-- Get changes to specific field
SELECT * FROM audit_log
WHERE new_value LIKE '%phone%'
ORDER BY timestamp DESC;
```

### Python Queries
```python
# Get patient audit history
audits = db.get_patient_audit_history(patient_id)
for audit in audits:
    print(f"{audit['timestamp']} - {audit['operation']} on {audit['table_name']}")
    if audit['operation'] == 'UPDATE':
        print(f"  Old: {audit['old_value']}")
        print(f"  New: {audit['new_value']}")

# Get specific table audit
visit_audits = db.get_audit_history(table_name="visits", record_id=visit_id)

# Get all recent audits
recent_audits = db.get_audit_history(limit=50)
```

## Testing

### Create and Verify Audit
```python
# Create patient
patient = Patient(name="John Doe", age=45, gender="M")
saved_patient = db.add_patient(patient)

# Verify INSERT audit
audits = db.get_audit_history(table_name="patients", record_id=saved_patient.id)
assert audits[0]['operation'] == 'INSERT'
assert audits[0]['new_value']['name'] == "John Doe"

# Update patient
saved_patient.phone = "9999999999"
db.update_patient(saved_patient)

# Verify UPDATE audit
audits = db.get_audit_history(table_name="patients", record_id=saved_patient.id)
assert audits[0]['operation'] == 'UPDATE'
assert 'phone' in audits[0]['new_value']

# Delete patient
db.delete_patient(saved_patient.id)

# Verify DELETE audit
audits = db.get_audit_history(table_name="patients", record_id=saved_patient.id)
assert audits[0]['operation'] == 'DELETE'

# Verify soft delete
patient = db.get_patient(saved_patient.id)
assert patient is None  # Should not return deleted patient
```

## Best Practices

1. **Always log audits within the same transaction as data changes**
2. **Only log changed fields for UPDATE operations** (not full record)
3. **Never modify or delete audit_log records**
4. **Include meaningful data in old_value and new_value**
5. **Filter deleted records in all SELECT queries** (`WHERE is_deleted = 0`)
6. **Use consistent JSON structure for old/new values**
7. **Handle JSON parsing errors gracefully**
8. **Index on (table_name, record_id) for fast lookups**

## Troubleshooting

### Audit not logging
- Check that the audit_log table exists
- Verify the operation completed successfully (cursor.rowcount > 0)
- Check for transaction rollback errors

### UI not showing history
- Verify patient is selected
- Check that db parameter is passed to CentralPanel
- Verify AuditHistoryDialog is imported correctly

### Deleted records appearing
- Check that `is_deleted = 0` filter is applied
- Verify soft delete is setting is_deleted = 1

### Performance issues
- Verify indexes exist: `idx_audit_table_record`, `idx_audit_timestamp`
- Use limit parameter to reduce result set size
- Consider archiving old audit logs
