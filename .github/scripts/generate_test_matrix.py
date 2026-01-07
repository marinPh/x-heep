#!/usr/bin/env python3
"""
Generate a GitHub Actions matrix for parallel testing of X-HEEP applications.

This script scans the sw/applications directory, filters out blacklisted apps,
and generates a matrix configuration that splits apps across multiple runners
for parallel execution.
"""

import os
import json
import math
import sys

# Import BLACKLIST and WHITELIST from test_apps.py to avoid duplication
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../test/test_apps'))
try:
    from test_apps import BLACKLIST, WHITELIST
except ImportError as e:
    print(f"Error: Could not import from test_apps.py: {e}", file=sys.stderr)
    print("Make sure test_apps.py is in test/test_apps/ directory", file=sys.stderr)
    sys.exit(1)

# Target number of apps per runner (for load balancing)
TARGET_APPS_PER_RUNNER = 6


def in_list(name, item_list):
    """
    Checks if the given name is in the list. This allows for pattern matching.
    For example, if "example" is in the list, in_list("my_example_app")
    will return True.
    """
    return any(word in name for word in item_list)


def get_apps(apps_dir):
    """
    Get all apps from apps_dir, applying WHITELIST and BLACKLIST filters.
    Returns a sorted list of app names.
    """
    if not os.path.isdir(apps_dir):
        print(f"Error: {apps_dir} is not a valid directory", file=sys.stderr)
        sys.exit(1)

    all_apps = sorted([
        d for d in os.listdir(apps_dir)
        if os.path.isdir(os.path.join(apps_dir, d))
    ])

    # Apply whitelist if provided
    if WHITELIST:
        all_apps = [app for app in all_apps if in_list(app, WHITELIST)]

    # Apply blacklist
    testable_apps = [app for app in all_apps if not in_list(app, BLACKLIST)]

    return testable_apps


def split_into_batches(apps, target_per_batch):
    """
    Split a list of apps into balanced batches using round-robin distribution.
    This ensures even load distribution across runners.
    """
    if not apps:
        return []

    num_batches = max(1, math.ceil(len(apps) / target_per_batch))
    batches = [[] for _ in range(num_batches)]

    # Distribute apps using round-robin for even distribution
    for i, app in enumerate(apps):
        batches[i % num_batches].append(app)

    return batches


def generate_matrix(batches):
    """
    Generate GitHub Actions matrix format from app batches.
    Returns a dict with 'include' key containing batch configurations.
    """
    matrix = {
        "include": [
            {
                "batch": str(i + 1),
                "apps": ",".join(batch)
            }
            for i, batch in enumerate(batches) if batch
        ]
    }
    return matrix


def main():
    """Main entry point."""
    apps_dir = "sw/applications"

    # Get all testable apps
    apps = get_apps(apps_dir)

    if not apps:
        print("Error: No apps found to test", file=sys.stderr)
        sys.exit(1)

    # Split into batches
    batches = split_into_batches(apps, TARGET_APPS_PER_RUNNER)

    # Generate matrix
    matrix = generate_matrix(batches)

    # Output as JSON
    print(json.dumps(matrix))


if __name__ == "__main__":
    main()
