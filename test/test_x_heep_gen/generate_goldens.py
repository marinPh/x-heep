#!/usr/bin/env python3
"""
Generate golden reference files for all test scenarios.

This script automates the process of creating golden reference outputs
from known-good configurations, typically from the main branch.

Usage:
    python generate_goldens.py                       # Generate from current state
    python generate_goldens.py --from-main           # Checkout main first
    python generate_goldens.py --scenario basic_pads # Generate specific scenario
    python generate_goldens.py --verify              # Verify after generation
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import shutil


class Color:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


def log_info(msg: str):
    print(f"{Color.BLUE}[INFO]{Color.NC} {msg}")


def log_success(msg: str):
    print(f"{Color.GREEN}[SUCCESS]{Color.NC} {msg}")


def log_warning(msg: str):
    print(f"{Color.YELLOW}[WARNING]{Color.NC} {msg}")


def log_error(msg: str):
    print(f"{Color.RED}[ERROR]{Color.NC} {msg}")


class GoldenGenerator:
    """Generator for golden reference files."""

    def __init__(self, repo_root: Path, scenarios_dir: Path):
        self.repo_root = repo_root
        self.scenarios_dir = scenarios_dir
        self.template_file = scenarios_dir.parent / "pads" / "output" / "kwargs_output.json.tpl"
        self.xheep_config_cache = repo_root / "build" / "xheep_config_cache.pickle"
        self.python_cmd = self._find_python()

    def _find_python(self) -> str:
        """Find the appropriate Python executable."""
        venv_python = self.repo_root / ".venv" / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)
        return "python3"

    def discover_scenarios(self, specific_scenario: str = None) -> List[str]:
        """
        Discover all test scenarios.

        Args:
            specific_scenario: If provided, only return this scenario

        Returns:
            List of scenario names
        """
        if specific_scenario:
            scenario_path = self.scenarios_dir / specific_scenario
            if not scenario_path.exists():
                raise ValueError(f"Scenario '{specific_scenario}' not found")
            return [specific_scenario]

        scenarios = []
        for path in self.scenarios_dir.iterdir():
            if path.is_dir() and not path.name.startswith("_"):
                # Check if it has hjson or python subdirectories
                hjson_dir = path / "hjson"
                python_dir = path / "python"
                if hjson_dir.exists() or python_dir.exists():
                    scenarios.append(path.name)

        return sorted(scenarios)

    def get_scenario_configs(self, scenario: str) -> Dict[str, Path]:
        """
        Get configuration paths for a scenario.

        Args:
            scenario: Scenario name

        Returns:
            Dictionary with 'hjson', 'python', 'output', 'golden' paths
        """
        scenario_dir = self.scenarios_dir / scenario

        return {
            "hjson": scenario_dir / "hjson" / "config.hjson",
            "python": scenario_dir / "python" / "config.py",
            "output_dir": scenario_dir / "output",
            "golden_dir": scenario_dir / "golden",
        }

    def run_mcu_gen(self, pads_cfg: Path, dry_run: bool = False) -> bool:
        """
        Run mcu-gen with the specified pad configuration.

        Args:
            pads_cfg: Path to pad configuration file
            dry_run: If True, don't actually run

        Returns:
            True if successful, False otherwise
        """
        relative_config = pads_cfg.relative_to(self.repo_root)

        cmd = [
            "make",
            "mcu-gen",
            f"X_HEEP_CFG=configs/ci.hjson",
            f"PADS_CFG={relative_config}",
        ]

        if dry_run:
            log_info(f"  [DRY-RUN] Would run: {' '.join(cmd)}")
            return True

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            log_error(f"  mcu-gen failed: {e.stderr}")
            return False

    def generate_output(self, template_path: Path, dry_run: bool = False) -> bool:
        """
        Generate output from template.

        Args:
            template_path: Path to template file
            dry_run: If True, don't actually run

        Returns:
            True if successful, False otherwise
        """
        cmd = [
            self.python_cmd,
            str(self.repo_root / "util" / "mcu_gen.py"),
            "--cached_path",
            str(self.xheep_config_cache),
            "--cached",
            "--outtpl",
            str(template_path),
        ]

        if dry_run:
            log_info(f"  [DRY-RUN] Would run: {' '.join(cmd)}")
            return True

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            log_error(f"  Template generation failed: {e.stderr}")
            return False

    def generate_golden(
        self,
        scenario: str,
        config_format: str,
        config_path: Path,
        dry_run: bool = False,
    ) -> bool:
        """
        Generate golden reference for a scenario and format.

        Args:
            scenario: Scenario name
            config_format: 'hjson' or 'python'
            config_path: Path to configuration file
            dry_run: If True, show what would be done without doing it

        Returns:
            True if successful, False otherwise
        """
        log_info(f"Processing: {scenario} ({config_format})")

        configs = self.get_scenario_configs(scenario)
        output_dir = configs["output_dir"]
        golden_dir = configs["golden_dir"]

        # Create directories
        output_dir.mkdir(parents=True, exist_ok=True)
        golden_dir.mkdir(parents=True, exist_ok=True)

        # Copy template if needed
        template_output = output_dir / "kwargs_output.json.tpl"
        if not template_output.exists() and self.template_file.exists():
            if not dry_run:
                shutil.copy(self.template_file, template_output)
            log_info(f"  Copied template to {template_output.relative_to(self.repo_root)}")

        if dry_run:
            log_info(f"  [DRY-RUN] Would generate golden for {scenario} ({config_format})")
            return True

        # Step 1: Run mcu-gen
        log_info("  Running mcu-gen...")
        if not self.run_mcu_gen(config_path):
            return False

        # Step 2: Generate output from template
        log_info("  Generating output from template...")
        if not self.generate_output(template_output):
            return False

        # Step 3: Verify output was created
        generated_output = output_dir / "kwargs_output.json"
        if not generated_output.exists():
            log_error(f"  Generated output not found: {generated_output}")
            return False

        # Step 4: Copy to golden
        log_info("  Copying to golden reference...")
        golden_output = golden_dir / "kwargs_output.json"
        shutil.copy(generated_output, golden_output)

        log_success(f"  Generated golden for {scenario} ({config_format})")
        log_info(f"    → {golden_output.relative_to(self.repo_root)}")

        return True

    def verify_golden(self, scenario: str) -> Tuple[bool, str]:
        """
        Verify that a golden reference is valid JSON.

        Args:
            scenario: Scenario name

        Returns:
            Tuple of (is_valid, message)
        """
        configs = self.get_scenario_configs(scenario)
        golden_file = configs["golden_dir"] / "kwargs_output.json"

        if not golden_file.exists():
            return False, f"Golden file not found: {golden_file}"

        try:
            with open(golden_file, "r") as f:
                data = json.load(f)

            # Basic validation - check for expected keys
            if not isinstance(data, dict):
                return False, "Golden file is not a JSON object"

            # Could add more specific validation here
            return True, f"Valid JSON with {len(data)} top-level keys"

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except Exception as e:
            return False, f"Error reading golden file: {e}"


def checkout_main() -> str:
    """
    Checkout main branch and return the original branch name.

    Returns:
        Original branch name

    Raises:
        RuntimeError: If there are uncommitted changes or git operations fail
    """
    try:
        # Get current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        original_branch = result.stdout.strip()

        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "diff-index", "--quiet", "HEAD", "--"],
            capture_output=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "You have uncommitted changes. Please commit or stash them first."
            )

        # Checkout main
        log_info("Checking out main branch...")
        subprocess.run(
            ["git", "checkout", "main"],
            capture_output=True,
            check=True,
        )

        return original_branch

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git operation failed: {e}")


def return_to_branch(branch: str):
    """Return to the specified branch."""
    if branch and branch != "main":
        log_info(f"Returning to branch: {branch}")
        subprocess.run(
            ["git", "checkout", branch],
            capture_output=True,
            check=True,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Generate golden reference files for test scenarios"
    )
    parser.add_argument(
        "--from-main",
        action="store_true",
        help="Checkout main branch before generating (returns to original branch after)",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="Generate only for specific scenario",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify golden files after generation",
    )

    args = parser.parse_args()

    # Setup paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    scenarios_dir = script_dir / "scenarios"

    log_info("Starting golden reference generation")
    log_info(f"Repository root: {repo_root}")
    log_info(f"Scenarios directory: {scenarios_dir}")

    # Handle main branch checkout
    original_branch = None
    if args.from_main:
        try:
            original_branch = checkout_main()
        except RuntimeError as e:
            log_error(str(e))
            return 1

    try:
        # Create generator
        generator = GoldenGenerator(repo_root, scenarios_dir)

        # Discover scenarios
        log_info("Discovering scenarios...")
        scenarios = generator.discover_scenarios(args.scenario)

        if not scenarios:
            log_error(f"No scenarios found in {scenarios_dir}")
            return 1

        log_info(f"Found {len(scenarios)} scenario(s): {', '.join(scenarios)}")
        print()

        # Process each scenario
        total = 0
        success = 0
        failed = 0

        for scenario in scenarios:
            log_info(f"=== Processing scenario: {scenario} ===")

            configs = generator.get_scenario_configs(scenario)

            # Process hjson config
            if configs["hjson"].exists():
                total += 1
                if generator.generate_golden(
                    scenario, "hjson", configs["hjson"], args.dry_run
                ):
                    success += 1
                else:
                    failed += 1

            # Process python config
            if configs["python"].exists():
                total += 1
                if generator.generate_golden(
                    scenario, "python", configs["python"], args.dry_run
                ):
                    success += 1
                else:
                    failed += 1

            print()

        # Verify if requested
        if args.verify and not args.dry_run:
            log_info("=== Verifying golden references ===")
            for scenario in scenarios:
                is_valid, message = generator.verify_golden(scenario)
                if is_valid:
                    log_success(f"{scenario}: {message}")
                else:
                    log_error(f"{scenario}: {message}")
            print()

        # Summary
        print()
        log_info("=== Summary ===")
        log_info(f"Total configurations: {total}")
        log_success(f"Successfully generated: {success}")

        if failed > 0:
            log_error(f"Failed: {failed}")
            return 1
        else:
            log_success("All golden references generated successfully!")

            if not args.dry_run:
                print()
                log_info("Next steps:")
                print("  1. Review the generated golden files:")
                print(f"     ls -la {scenarios_dir}/*/golden/*.json")
                print()
                print("  2. Verify they are correct:")
                print(f"     cat {scenarios_dir}/<scenario>/golden/kwargs_output.json | less")
                print()
                print("  3. Run tests to validate:")
                print("     make test_pads")
                print()
                print("  4. If everything looks good, commit the golden files:")
                print("     git add test/test_x_heep_gen/scenarios/*/golden/")
                print('     git commit -m "Generate golden reference files from main branch"')

        return 0

    finally:
        # Always return to original branch
        if original_branch:
            return_to_branch(original_branch)


if __name__ == "__main__":
    sys.exit(main())
