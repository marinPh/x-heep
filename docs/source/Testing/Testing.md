# Automatic testing

X-HEEP includes a script to perform automatic tests on your modifications. In addition, it also has a CI setup that checks the code by simulating all the existing applications and handles publishing new X-HEEP releases.

## Simulation script

The testing script (`test/test_apps/test_apps.py`) can be used to perform local tests. For quick
debugging, you can check the global variables in the script such as the `BLACKLIST` and `WHITELIST`.

You can run it with the following command:

```bash
make test
```

This will output the results in the terminal and in the `test/test_apps/test_apps.log` file.

Additionally, you can check only the compilation of the applications with the following command:

```bash
make test TEST_FLAGS=--compile-only
```

This script is also integrated in the CI workflow.

## Pad configuration tests

The pad configuration framework includes two levels of testing: **unit tests** for isolated logic validation and **scenario-based integration tests** for end-to-end validation across multiple configurations.

### Test directory structure

All pad configuration tests are located in `test/test_x_heep_gen/pads/`:

```text
test/test_x_heep_gen/pads/
├── unit/                           # Unit tests
├── scenarios/                      # Integration test configurations
├── test_scenarios.py               # Scenario test runner
├── test_pad_integration.py         # Integration tests
├── generate_goldens.py             # Golden reference generator
└── conftest.py                     # Pytest configuration
```

### Unit tests

Unit tests validate the core logic of the pad configuration framework in isolation, without invoking `mcu-gen` or requiring golden files. These tests run quickly and focus on three critical components:

1. **JSON comparison logic** (`unit/test_compare_json.py`)
   - Validates the comparison engine used by all integration tests
   - Tests value changes, type mismatches, nested structures, list modifications
   - Ensures accurate diff reporting with floating-point precision handling

2. **Geometric positioning calculations** (`unit/test_pad_positions.py`)
   - Tests pad centering on chip edges
   - Validates spacing calculations between multiple pads
   - Checks bondpad offset and skip parameter computation
   - Ensures error detection when pads don't fit within floorplan constraints

3. **PadRing orchestration** (`unit/test_padring_build.py`)
   - Tests transformation from configuration objects to generation-ready pads
   - Validates RangePad expansion (e.g., `gpio[0:4]` → 5 individual pads)
   - Checks MultiplexedPad mux selector width calculation (e.g., 4 alternatives → 2 bits)
   - Verifies side-based pad separation (top/bottom/left/right)

**When to use unit tests:**
- During development of new pad configuration features
- For quick validation of logic changes
- To test edge cases and error handling in isolation
- Before running slower integration tests

**Run unit tests:**

```bash
make test_pads_unit                              # Run all unit tests
make test_pads_unit PYTEST_FLAGS="-k compare"    # Run specific tests
```

### Scenario-based integration tests

The integration test framework validates that HJSON and Python pad configurations produce identical outputs. Each test scenario is automatically discovered from the `scenarios/` directory structure.

**Test scenarios:**

The integration test suite includes 11 scenarios covering diverse pad configurations:

- `basic_pads`: Standard reference configuration (default)
- `minimal_pads`: Minimal viable pad setup
- `ultra_minimal`: Absolute minimum configuration (1 pad)
- `single_pad`: Edge case with exactly 1 pad
- `max_pads`: Stress test with maximum pad density
- `tight_spacing`: Minimal spacing between pads
- `all_edges`: Pads distributed across all 4 chip edges
- `all_orientations`: Tests all 8 pad orientations (R0, R90, R180, R270, MX, MY, MX90, MY90)
- `max_mux`: Maximum multiplexing complexity (16 alternatives)
- `asic_standard`: Standard ASIC padring configuration
- `fpga_pynq`: FPGA-specific layout with IO constraints

**Run integration tests:**

```bash
make test_pads                              # Run all scenarios
make test_pads PYTEST_FLAGS="-k minimal"    # Run specific scenario
make test_pads PYTEST_FLAGS="-k hjson"      # Test only hjson format
make test_pads PYTEST_FLAGS="-n auto"       # Run in parallel (requires pytest-xdist)
make test_pads_list                         # List discovered scenarios
```

**How scenario tests work:**

For each scenario, the test runner:

1. Discovers all scenario directories in `test/test_x_heep_gen/pads/scenarios/`
2. For each format (HJSON and Python):
   - Runs `mcu-gen` with the scenario configuration
   - Generates `kwargs_output.json` from the template
   - Compares output against golden reference
3. Validates that HJSON and Python produce identical results (cross-format consistency)

**Adding new test scenarios:**

To add a new scenario, simply create a directory structure:

```bash
test/test_x_heep_gen/pads/scenarios/<scenario_name>/
├── hjson/
│   └── config.hjson              # HJSON pad configuration
├── python/
│   └── config.py                 # Python pad configuration
└── golden/
    └── kwargs_output.json        # Expected output (generate with generate_goldens.py)
```

The test framework automatically discovers and runs the new scenario.

**Generating golden references:**

```bash
cd test/test_x_heep_gen/pads
python3 generate_goldens.py --help              # Show all options
python3 generate_goldens.py                     # Generate for all scenarios
python3 generate_goldens.py --scenario basic    # Generate for specific scenario
python3 generate_goldens.py --verify            # Verify after generation
```

**When to use integration tests:**
- To verify HJSON and Python equivalence after configuration changes
- Before committing changes to pad configuration logic
- To validate that generator outputs haven't regressed
- To ensure RTL generation consistency across input formats
- When adding new pad configuration scenarios

## Github CIs

The project's Continuous Integration (CI) is managed through GitHub Actions. The workflows are defined in the `.github/workflows` directory. The main CI workflow is `ci.yml`, which is triggered on every push and pull request to the `main` branch.

### CI Workflow (`ci.yml`)

This workflow ensures the stability and integrity of the codebase by running a series of checks, compilations, and simulations.

**Triggers:**

*   Push to any branch (`push: branches: [ "**" ]`).
*   Pull request to the `main` branch (`pull_request: branches: [ "main" ]`).

**Jobs:**

1.  **`determine-image-tag`**:
    *   **Purpose**: Determines the Docker image tag to be used by subsequent jobs.
    *   **Details**: It checks the Git history for the most recent tag. If no tag is found in the current branch, it looks for one in the `main` branch. If no tags are found at all, it defaults to `latest`. This ensures that the CI always uses a relevant toolchain version.

2.  **`compile-apps`**:
    *   **Purpose**: Compiles all software applications with both GCC and Clang to ensure they build correctly.
    *   **Dependencies**: Depends on `determine-image-tag` to select the correct Docker image.
    *   **Environment**: Runs inside the `ghcr.io/x-heep/x-heep/x-heep-toolchain` Docker container.
    *   **Steps**:
        *   Generates the MCU configuration using `make mcu-gen X_HEEP_CFG=configs/ci.hjson`.
        *   Executes `test/test_apps/test_apps.py` with the `--compile-only` flag to build all applications, without simulating them. This is done to offer a quick feedback about the apps' integrity, before their runtime behaviour is checked in RTL simulation.

3.  **`simulate-apps`**:
    *   **Purpose**: Runs Verilator RTL simulations for all applications (except the blacklisted ones) to verify their runtime behavior.
    *   **Condition**: This job only runs on pull requests to `main`.
    *   **Dependencies**: Depends on `determine-image-tag`.
    *   **Environment**: Runs inside the `x-heep-toolchain` Docker container.
    *   **Steps**:
        *   Generates the MCU configuration using `make mcu-gen X_HEEP_CFG=configs/ci.hjson`.
        *   Executes `test/test_apps/test_apps.py` to compile and simulate all applications.

4.  **`lint`**:
    *   **Purpose**: Checks that all auto-generated hardware files are up-to-date and have been formatted .
    *   **Dependencies**: Depends on `determine-image-tag`.
    *   **Environment**: Runs inside the `x-heep-toolchain` Docker container.
    *   **Steps**:
        *   Runs `make mcu-gen` to regenerate all hardware files.
        *   Uses `util/git-diff.py` to check for any differences between the working directory and the git HEAD. The job fails if any differences are found.

5.  **`gen-peripherals`**:
    *   **Purpose**: Tests the Python-based peripheral generation scripts and templates.
    *   **Dependencies**: Depends on `determine-image-tag`.
    *   **Environment**: Runs inside the `x-heep-toolchain` Docker container.
    *   **Steps**:
        *   Runs `make clean-all` to ensure a clean state.
        *   Executes `test/test_x_heep_gen/test_peripherals.py`.

6.  **`check-vendor`**:
    *   **Purpose**: Verifies that all third-party vendored dependencies are up-to-date.
    *   **Environment**: Runs inside a `ubuntu-latest` VM.
    *   **Steps**:
        *   Installs Python dependencies.
        *   Runs the `util/vendor.py` script for all `.vendor.hjson` files to re-vendor all dependencies.
        *   Uses `util/git-diff.py` to check for any differences, ensuring that any changes to vendored repositories are properly committed.

7.  **`black-formatter`**:
    *   **Purpose**: Checks that all Python code adheres to the `black` formatting standard.
    *   **Environment**: Runs inside a `ubuntu-latest` VM.
    *   **Steps**:
        *   Uses the `psf/black` GitHub Action to check the formatting of all relevant Python files.

8.  **`Pad-generation`**:
    *   **Purpose**: Checks that all pad generation still produces the exact same as the golden output.
    *   **Environment**: Runs inside a `ubuntu-latest` VM.
    *   **Steps**:
        * call `make test_pads`.
        * call `make test_pads_unit`.

### Release Workflows

The project includes a robust, automated process for creating and publishing releases. This is handled by two GitHub Actions workflows: `create-release.yml` and `publish-release.yml`. This system ensures that every release is consistently built, tested, and published with its corresponding toolchain and Docker image.

#### Create X-HEEP Release Workflow (`create-release.yml`)

This workflow prepares a new release. It is a comprehensive process that builds the toolchain, packages it, creates a draft release, builds a Docker container, and opens a version bump pull request. It's designed to be triggered manually when a new release is needed.

**Trigger:**

*   Manual dispatch (`workflow_dispatch`) from the GitHub Actions tab.
*   **Inputs**:
    *   `llvm_version`: The LLVM version tag to build (default: `llvmorg-19.1.4`).
    *   `gcc_version`: The GCC version tag to build (default: `2023.01.03`).
    *   `release_tag`: The tag for the new GitHub release (e.g., `v1.0.0`).

```{note}
This workflow is intended for major releases that:
- Introduce support for new tools
- Bump existing tools to newer versions
- Modify the CI workflows
- Represent a significant update in general

Minor bug fixes or feature improvements may not require/justify a full new release.
```

**Jobs:**

1.  **`check-changes`**:
    *   Checks previous release tag.
    *   Downloads `tool-versions.env` from the previous release to compare GCC, LLVM, Verilator, and Verible versions.
    *   Checks for changes in Docker-related files (`util/docker/`, `util/conda_environment.yml`, `util/python-requirements.txt`, `docs/python-requirements.txt`).
    *   Sets outputs `rebuild_toolchain` and `rebuild_docker` to avoid unnecessary rebuilds.

2.  **`prepare-release`**:
    *   Creates a new release branch (`release/<release_tag>`).
    *   Updates the version in `core-v-mini-mcu.core` and the toolchain version in `util/docker/dockerfile`.
    *   Commits and pushes the changes to the new branch.
    *   Creates a **draft** GitHub release.

3.  **`build-and-upload-toolchain`**:
    *   **Conditional**: Runs the build only if `rebuild_toolchain` is true.
    *   Builds the RISC-V GCC and Clang/LLVM toolchains from the sources specified in the workflow inputs.
    *   Packages the compiled toolchains into a `.tar.gz` file.
    *   If `rebuild_toolchain` is false, it downloads the toolchain asset from the previous release.
    *   Uploads the toolchain tarball as an asset to the draft GitHub release.
    *   Uploads a `tool-versions.env` file containing version metadata.

4.  **`build-docker`**:
    *   **Conditional**: Runs the build only if `rebuild_docker` is true.
    *   Downloads the toolchain asset from the draft release.
    *   Builds the `x-heep-toolchain` Docker image, injecting the new toolchain.
    *   Pushes the new Docker image to the GitHub Container Registry (GHCR) with the release tag.
    *   If `rebuild_docker` is false, it retags the previous release's Docker image with the new tag.

5.  **`create-version-pr`**:
    *   Creates a new pull request to merge the release branch back into `main`. This PR contains the version bumps.

6.  **`cleanup-on-failure`**:
    *   This job runs only if any of the previous jobs fail.
    *   It automatically cleans up by deleting the draft release, the release tag, the remote release branch, and the pushed Docker image from GHCR. This prevents leftovers from partial, broken releases.

#### Publish Release Workflow (`publish-release.yml`)

This workflow finalizes the release process. It is triggered automatically after the version bump PR (created by the `create-release.yml` workflow) is merged into the `main` branch.

**Trigger:**

*   A pull request from a `release/*` branch is merged into `main`.

**Jobs:**

1.  **`publish-release`**:
    *   Identifies the release tag from the merged branch name.
    *   Converts the corresponding draft release into a **public release**.
    *   Deletes the now-merged remote release branch to keep the repository clean.

2.  **`tag-latest`**:
    *   After the release is published, this job pulls the newly released Docker image from GHCR.
    *   It then re-tags this image with the `latest` tag and pushes it.
    *   This ensures that the main `ci.yml` workflow will use the most up-to-date toolchain for future runs on the `main` branch.
