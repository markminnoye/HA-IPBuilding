# Local Development

This project includes a Docker Compose configuration to easily run a local Home Assistant instance for testing the `ipbuilding` custom component.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

## Getting Started

1.  **Start the environment:**

    ```bash
    docker compose up -d
    ```

    This will start Home Assistant and mount the `custom_components` directory. A `config` directory will be created in the project root to store the local Home Assistant configuration.

2.  **Access Home Assistant:**

    Open your browser and navigate to: [http://localhost:8123](http://localhost:8123)

    You will need to go through the initial Home Assistant onboarding process (create a user, etc.). This data is stored in the `config` directory and will persist between restarts.

3.  **Add the Integration:**

    - Go to **Settings** -> **Devices & Services**.
    - Click **Add Integration**.
    - Search for **IPBuilding** (or whatever the integration name is in `manifest.json`).
    - Follow the configuration steps.

## Stopping the Environment

To stop the container:

```bash
docker compose down
```

## Logs

To view the Home Assistant logs:

```bash
docker compose logs -f homeassistant
```

## Option 2: Python Virtual Environment (No Docker)

If you cannot or prefer not to use Docker, you can run Home Assistant Core directly in a Python virtual environment.

### Prerequisites

-   Python 3.14 or higher installed (the project now uses Python 3.14).
-   The virtual environment is created in the `venv` directory. The old `.venv` directory has been removed, so only `venv` should be used.

### Setup

1.  **Run the setup script:**

    ```bash
    ./setup_local_ha.sh
    ```

    This creates (or recreates) the `venv` virtual environment, installs Home Assistant and links the custom component.

2.  **Start Home Assistant:**

    ```bash
    ./venv/bin/hass -c config
    ```

    Or activate the venv first:

    ```bash
    source venv/bin/activate
    hass -c config
    ```

1.  **Run the setup script:**

    ```bash
    ./setup_local_ha.sh
    ```

    This will create a virtual environment, install Home Assistant, and link your component.

2.  **Start Home Assistant:**

    ```bash
    ./venv/bin/hass -c config
    ```

    Or activate the venv first:

    ```bash
    source venv/bin/activate
    hass -c config
    ```

3.  **Access Home Assistant:**

    Open your browser and navigate to: [http://localhost:8123](http://localhost:8123)

### Rebuilding

Since the component is symlinked, changes to the Python files should be picked up after restarting Home Assistant.

To restart, press `Ctrl+C` in the terminal to stop the process, then run `./venv/bin/hass -c config` again.

