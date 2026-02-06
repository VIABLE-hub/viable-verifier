"""
CSV Import Module for Student Data
Allows importing student data from CSV files for credential issuance
"""
import csv
import io
import uuid
from datetime import datetime
from logging import getLogger

logger = getLogger("LOGGER")

# Expected CSV columns (German and English support)
COLUMN_MAPPINGS = {
    # German column names
    'vorname': 'firstName',
    'nachname': 'lastName',
    'matrikelnummer': 'studentId',
    'matrikelnummer_prefix': 'studentIdPrefix',
    'matrikelnummerpräfix': 'studentIdPrefix',
    'email': 'email',
    # English column names
    'firstname': 'firstName',
    'first_name': 'firstName',
    'lastname': 'lastName',
    'last_name': 'lastName',
    'studentid': 'studentId',
    'student_id': 'studentId',
    'studentidprefix': 'studentIdPrefix',
    'student_id_prefix': 'studentIdPrefix',
}


def normalize_column_name(column: str) -> str:
    """Normalize column name to standard field name"""
    normalized = column.strip().lower().replace(' ', '_').replace('-', '_')
    return COLUMN_MAPPINGS.get(normalized, COLUMN_MAPPINGS.get(column.strip(), None))


def parse_csv_students(file_content: bytes, encoding: str = 'utf-8') -> dict:
    """
    Parse CSV file content and return list of student records

    Returns:
        dict with 'students' list and 'errors' list
    """
    result = {
        'students': [],
        'errors': [],
        'total_rows': 0,
        'valid_rows': 0
    }

    try:
        # Try to decode with specified encoding, fallback to latin-1
        try:
            content = file_content.decode(encoding)
        except UnicodeDecodeError:
            content = file_content.decode('latin-1')
            logger.info("CSV: Fallback to latin-1 encoding")

        # Detect delimiter (comma or semicolon)
        first_line = content.split('\n')[0]
        delimiter = ';' if ';' in first_line and ',' not in first_line else ','
        if ';' in first_line and ',' in first_line:
            delimiter = ';' if first_line.count(';') > first_line.count(',') else ','
        logger.info(f"CSV: Detected delimiter: '{delimiter}'")

        # Parse CSV
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

        # Map columns
        column_map = {}
        if reader.fieldnames:
            for col in reader.fieldnames:
                normalized = normalize_column_name(col)
                if normalized:
                    column_map[col] = normalized
                    logger.info(f"CSV: Mapped column '{col}' -> '{normalized}'")

        # Process rows
        for row_num, row in enumerate(reader, start=2):
            result['total_rows'] += 1

            student = {
                'id': str(uuid.uuid4()),
                'status': 'pending',
                'importedAt': datetime.now().isoformat()
            }
            missing_fields = []

            # Map row data to student fields
            for original_col, normalized_col in column_map.items():
                value = row.get(original_col, '').strip()
                if value:
                    student[normalized_col] = value

            # Validate required fields
            required = ['firstName', 'lastName', 'studentId']
            for field in required:
                if field not in student or not student[field]:
                    missing_fields.append(field)

            if missing_fields:
                result['errors'].append({
                    'row': row_num,
                    'error': f"Missing required fields: {', '.join(missing_fields)}",
                    'data': dict(row)
                })
            else:
                if 'studentIdPrefix' not in student:
                    student['studentIdPrefix'] = ''
                result['students'].append(student)
                result['valid_rows'] += 1

        logger.info(f"CSV: Parsed {result['valid_rows']}/{result['total_rows']} valid students")

    except Exception as e:
        logger.error(f"CSV: Parse error: {e}")
        result['errors'].append({
            'row': 0,
            'error': f"File parse error: {str(e)}",
            'data': None
        })

    return result


def get_csv_template() -> str:
    """Generate a CSV template with example data"""
    return """firstName;lastName;studentId;studentIdPrefix;email
Anna;Müller;123456;54321;anna.mueller@tu-berlin.de
Max;Schmidt;234567;65432;max.schmidt@tu-berlin.de
Laura;Schneider;345678;76543;laura.schneider@tu-berlin.de
"""