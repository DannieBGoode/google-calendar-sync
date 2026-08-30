from dataclasses import dataclass

from calendar_sync.application.errors import DuplicateDirectionalRelationship
from calendar_sync.application.ports import UnitOfWorkFactory
from calendar_sync.domain.model import SyncRule


@dataclass(slots=True)
class CreateSyncRule:
    unit_of_work: UnitOfWorkFactory

    def execute(self, rule: SyncRule) -> SyncRule:
        with self.unit_of_work() as uow:
            if uow.rules.relationship_exists(rule.source, rule.destination):
                raise DuplicateDirectionalRelationship(
                    "a rule already exists for this source and destination"
                )
            uow.rules.add(rule)
            uow.commit()
        return rule
