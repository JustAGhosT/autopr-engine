import asyncio
import os
import pathlib

import pydantic

from autopr.actions.base.action import Action


class Inputs(pydantic.BaseModel):
    # This would be a secret in a real workflow, e.g., "postgresql://user:pass@host:port/db"
    database_connection_string: str
    migrations_path: str = "migrations"


class Outputs(pydantic.BaseModel):
    success: bool
    log: str


class RunDBMigrations(Action[Inputs, Outputs]):
    """
    Runs SQL migration files from a specified directory against a database.
    This is a simulation assuming a CLI tool like 'psql' is available.
    """

    id = "run_db_migrations"

    async def run(self, inputs: Inputs) -> Outputs:
        logs = []
        success = True

        if not pathlib.Path(inputs.migrations_path).is_dir():
            return Outputs(
                success=False,
                log=f"Error: Migrations directory '{inputs.migrations_path}' not found.",
            )

        migration_files = sorted(
            [f for f in os.listdir(inputs.migrations_path) if f.endswith(".sql")]
        )

        for filename in migration_files:
            filepath = os.path.join(inputs.migrations_path, filename)
            # In a real scenario, you'd use a proper DB client or CLI
            # Simulating with a command: psql -d <conn_string> -f <file>
            command = f'echo "psql -d {inputs.database_connection_string} -f {filepath}"'

            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            log_entry = f"--- Running {filename} ---\n"
            log_entry += stdout.decode("utf-8")
            log_entry += stderr.decode("utf-8")
            logs.append(log_entry)

            if process.returncode != 0:
                success = False
                logs.append(f"--- FAILED: {filename} ---")
                break  # Stop on failure

        return Outputs(success=success, log="\n".join(logs))


if __name__ == "__main__":
    from autopr.tests.utils import run_action_manually

    # Create dummy migration files for testing
    os.makedirs("migrations", exist_ok=True)
    with open("migrations/01_init.sql", "w", encoding="utf-8") as f:
        f.write("CREATE TABLE users;")
    with open("migrations/02_add_col.sql", "w", encoding="utf-8") as f:
        f.write("ALTER TABLE users ADD COLUMN name;")
    asyncio.run(
        run_action_manually(
            action=RunDBMigrations,
            inputs=Inputs(database_connection_string="dummy_connection_string"),
        )
    )
