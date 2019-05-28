import re

import records

from .exceptions import NotFoundError, NotUniqueError


db = records.Database()


class Repository:

    table = None

    def __init__(self, model):
        """Initializes the repository."""
        if type(self).table is None:
            type(self).table = "_".join(
                word
                for word in re.split(r"([A-Z][^A-Z]*)", self.model.__name__)
                if word
            ).lower()

        self.db = db
        self.model = model
        self.create_table()

    @property
    def last_id(self):
        """Returns the last auto-incremented id."""
        rows = self.db.query("""
            SELECT LAST_INSERT_ID() AS id
        """)

        for row in rows:
            return row['id']

    def filter(self, **search_terms):
        """Searches objects in the database matching the provided criteria."""
        conditions = " AND ".join(
            f"{term} = :{term}"
            for term, value in search_terms.items()
            if value is not None
        ).strip()

        if conditions:
            conditions = f"WHERE {conditions}"

        instances = self.db.query(f"""
            SELECT * from {self.table}
            {conditions}
        """, **search_terms).all(as_dict=True)

        return [
            self.model(**instance)
            for instance in instances
        ]

    def get(self, **search_terms):
        """Gets one object from the database matching the provided criteria."""
        instances = self.filter(**search_terms)

        if not instances:
            raise NotFoundError("Nothing has been found.")

        if len(instances) > 1:
            raise NotUniqueError("Serveral instance have been found.")

        return instances[0]

    def get_or_create(self, **search_terms):
        """Gets one object from the database matching the provided criteria or
        creates it if it does not exist.
        """
        try:
            instance = self.get(**search_terms)
        except NotFoundError:
            instance = self.create(**search_terms)
        return instance

    def all(self):
        """Returns all the objects of the current type in the database."""
        return self.filter()

    def create(self, **attributes):
        """Create a new instance of the model and saves it in the database."""
        return self.save(self.model(**attributes))

    def create_table(self):
        """Creates the necessary tables for the current model to work."""
        pass

    def save(self, instance):
        """Saves or updates the current model instance in the database."""
        return instance


class Model:

    objects = None

    def save(self):
        """Saves the model in the database."""
        self.objects.save(self)

    def __repr__(self):
        """Formats a string representing the model."""
        attributes = ", ".join(
            f"{key}={value}"
            for key, value in vars(self).items()
        )
        return f"{type(self).__name__}({attributes})"
