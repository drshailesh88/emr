"""Performance benchmarks for DocAssist EMR.

These benchmarks define target and maximum acceptable performance metrics.
Tests should aim for target values and fail if they exceed max values.
"""

# Time benchmarks (in milliseconds)
BENCHMARKS = {
    # Database operations
    'patient_search': {
        'target_ms': 100,
        'max_ms': 500,
        'description': 'Patient search across 10K patients'
    },
    'patient_list_pagination': {
        'target_ms': 50,
        'max_ms': 200,
        'description': 'List 100 patients with pagination'
    },
    'visit_save': {
        'target_ms': 50,
        'max_ms': 200,
        'description': 'Save a single visit record'
    },
    'visit_history_load': {
        'target_ms': 200,
        'max_ms': 1000,
        'description': 'Load 100 visits for a patient'
    },
    'bulk_patient_import': {
        'target_ms': 10000,  # 10 seconds
        'max_ms': 30000,     # 30 seconds
        'description': 'Import 1000 patients'
    },

    # Search operations
    'phonetic_search': {
        'target_ms': 200,
        'max_ms': 500,
        'description': 'Phonetic search in 10K patients'
    },
    'fuzzy_search': {
        'target_ms': 300,
        'max_ms': 800,
        'description': 'Fuzzy search with typo tolerance'
    },
    'natural_language_search': {
        'target_ms': 500,
        'max_ms': 2000,
        'description': 'Natural language search query'
    },
    'filtered_search': {
        'target_ms': 200,
        'max_ms': 600,
        'description': 'Search with age/gender filters'
    },

    # Report generation
    'daily_summary': {
        'target_ms': 1000,
        'max_ms': 3000,
        'description': 'Calculate daily summary report'
    },
    'monthly_analytics': {
        'target_ms': 5000,
        'max_ms': 15000,
        'description': 'Generate monthly analytics'
    },
    'audit_trail_export': {
        'target_ms': 10000,
        'max_ms': 30000,
        'description': 'Export 1 year audit log'
    },
    'pdf_prescription_generation': {
        'target_ms': 300,
        'max_ms': 1000,
        'description': 'Generate single PDF prescription'
    },
    'bulk_pdf_generation': {
        'target_ms': 30000,
        'max_ms': 60000,
        'description': 'Generate 100 PDF prescriptions'
    },

    # LLM operations
    'soap_extraction': {
        'target_ms': 2000,
        'max_ms': 5000,
        'description': 'SOAP note extraction via LLM'
    },
    'differential_diagnosis': {
        'target_ms': 2000,
        'max_ms': 5000,
        'description': 'Generate differential diagnosis'
    },
    'llm_queue_processing': {
        'target_ms': 20000,
        'max_ms': 50000,
        'description': 'Process 10 queued LLM requests'
    },

    # Startup and initialization
    'app_startup': {
        'target_ms': 2000,
        'max_ms': 5000,
        'description': 'Application startup time'
    },
    'database_init': {
        'target_ms': 500,
        'max_ms': 2000,
        'description': 'Database initialization'
    },
}

# Memory benchmarks (in MB)
MEMORY_BENCHMARKS = {
    'baseline': {
        'target_mb': 100,
        'max_mb': 200,
        'description': 'App startup memory'
    },
    'with_10k_patients': {
        'target_mb': 500,
        'max_mb': 1000,
        'description': 'Memory with 10K patients loaded'
    },
    'large_patient_timeline': {
        'target_mb': 200,
        'max_mb': 500,
        'description': 'Load patient with 500 visits'
    },
    'memory_leak_threshold': {
        'target_mb': 50,
        'max_mb': 100,
        'description': 'Memory growth after 1000 operations'
    },
}

# Concurrency benchmarks
CONCURRENCY_BENCHMARKS = {
    'concurrent_searches': {
        'target_ms': 1000,
        'max_ms': 3000,
        'description': '10 concurrent patient searches'
    },
    'concurrent_writes': {
        'target_ms': 500,
        'max_ms': 2000,
        'description': '10 concurrent visit saves'
    },
    'mixed_workload': {
        'target_ms': 5000,
        'max_ms': 15000,
        'description': 'Simulate 3 doctors + 2 searches + 1 report'
    },
    'burst_load': {
        'target_ms': 2000,
        'max_ms': 5000,
        'description': '50 requests in 1 second'
    },
}


def get_benchmark(category: str, operation: str) -> dict:
    """Get benchmark for a specific operation.

    Args:
        category: 'time', 'memory', or 'concurrency'
        operation: Name of the operation

    Returns:
        Dict with target and max values
    """
    if category == 'time':
        return BENCHMARKS.get(operation, {'target_ms': 1000, 'max_ms': 5000})
    elif category == 'memory':
        return MEMORY_BENCHMARKS.get(operation, {'target_mb': 100, 'max_mb': 500})
    elif category == 'concurrency':
        return CONCURRENCY_BENCHMARKS.get(operation, {'target_ms': 1000, 'max_ms': 5000})
    else:
        raise ValueError(f"Unknown benchmark category: {category}")


def format_benchmark_result(operation: str, actual_value: float,
                           benchmark: dict, unit: str = 'ms') -> str:
    """Format a benchmark result for display.

    Args:
        operation: Name of the operation
        actual_value: Actual measured value
        benchmark: Benchmark dict with target and max
        unit: Unit of measurement (ms, MB, etc.)

    Returns:
        Formatted string with color coding
    """
    target_key = f'target_{unit.lower()}'
    max_key = f'max_{unit.lower()}'

    target = benchmark.get(target_key, 0)
    max_val = benchmark.get(max_key, 0)

    if actual_value <= target:
        status = '✓ EXCELLENT'
        color = '\033[92m'  # Green
    elif actual_value <= max_val:
        status = '⚠ ACCEPTABLE'
        color = '\033[93m'  # Yellow
    else:
        status = '✗ FAILED'
        color = '\033[91m'  # Red

    reset = '\033[0m'

    return (f"{color}{operation}: {actual_value:.2f}{unit} "
            f"(target: {target}{unit}, max: {max_val}{unit}) - {status}{reset}")
