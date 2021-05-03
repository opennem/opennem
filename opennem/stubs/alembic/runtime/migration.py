from typing import Any


class MigrationContext:
    def begin_transaction(self, _per_migration: bool) -> Any:
        ...
