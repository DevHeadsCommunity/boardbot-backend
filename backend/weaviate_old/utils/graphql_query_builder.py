from typing import List


class ClauseBuilder:
    def build(self) -> str:
        raise NotImplementedError


class GraphQLQueryBuilder:
    """
    A class to build GraphQL queries for Weaviate using the Builder pattern.
    """

    def __init__(self):
        self._clauses = []
        self.operation = None
        self.class_name = None
        self.properties = []

    def set_operation(self, operation: str) -> "GraphQLQueryBuilder":
        self.operation = operation
        return self

    def set_class_name(self, class_name: str) -> "GraphQLQueryBuilder":
        self.class_name = class_name
        return self

    def set_properties(self, properties: List[str]) -> "GraphQLQueryBuilder":
        self.properties = properties
        return self

    def add_clauses(self, *clause_builders: ClauseBuilder) -> "GraphQLQueryBuilder":
        for clause_builder in clause_builders:
            self._clauses.append(clause_builder.build())
        return self

    def build(self) -> str:
        properties_str = ", ".join(self.properties)
        clauses_str = ", ".join(self._clauses)
        clauses_str = f"({clauses_str})" if clauses_str else ""
        return f"{{ {self.operation} {{ {self.class_name} {clauses_str} {{ {properties_str} }} }} }}"
