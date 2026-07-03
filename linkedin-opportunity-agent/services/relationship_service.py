from database.crud import get_people, upsert_person
from database.db import get_db
from schemas.people_schema import PersonSchema
from utils.ranking import rank_items


class RelationshipService:
    def get_all(self, limit: int = 50, min_score: float = 0.0) -> list[PersonSchema]:
        with get_db() as db:
            people = get_people(db, limit=limit, min_score=min_score)
            return [self._to_schema(p) for p in people]

    def get_top_connections(self, n: int = 10) -> list[PersonSchema]:
        people = self.get_all(limit=100)
        ranked = rank_items([p.model_dump() for p in people])
        return [PersonSchema(**p) for p in ranked[:n]]

    def save_person(self, person: PersonSchema) -> PersonSchema:
        with get_db() as db:
            db_person = upsert_person(db, person)
            return self._to_schema(db_person)

    @staticmethod
    def _to_schema(person) -> PersonSchema:
        return PersonSchema(
            id=person.id,
            name=person.name,
            title=person.title,
            company=person.company,
            profile_url=person.profile_url,
            relationship_type=person.relationship_type,
            relevance_score=person.relevance_score,
            mutual_connections=person.mutual_connections,
            shared_interests=person.shared_interests or [],
            recent_activity=person.recent_activity,
            last_seen=person.last_seen,
            notes=person.notes,
        )
