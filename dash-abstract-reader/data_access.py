# Data access interface for EMMA. Separated DB access logic from core logic.
#

import pandas
from sqlalchemy import MetaData, Table
from sqlalchemy.sql import select


class DataHelper:

    def __init__(self, engine):
        self.engine = engine
        self.terms_cache = {}

        meta = MetaData(bind=engine)
        self.scored_concepts = Table('VsChildAsthmaScore', meta, autoload=True)
        self.concepts = Table('Concept', meta, autoload=True)
        self.abstracts = Table('Abstract', meta, autoload=True)
        self.positionals = Table('Positional', meta, autoload=True)
        self.individual_scores = Table('Score', meta, autoload=True)
        self.query_results = Table('QueryResult', meta, autoload=True)
        self.queries = Table('Query', meta, autoload=True)
        self.query_sizes = Table('QuerySize', meta, autoload=True)

        self._query_df = pandas.read_sql(
            select([self.queries.c.query_id,
                    self.queries.c.name,
                    self.queries.c.query_string,
                    self.query_sizes.c.size]).
            where(self.queries.c.query_id == self.query_sizes.c.query_id),
            self.engine).set_index('query_id', drop=False)

        self._concepts_df = pandas.read_sql(select([self.concepts]), self.engine).set_index('concept_id', drop=False)

    def terms(self, bg_query_id: int, fg_query_id: int) -> pandas.DataFrame:
        """Gets a pandas DataFrame representing concepts sorted by score"""
        # Hard coded bg=0 for now
        assert bg_query_id == 0, "We haven't implemented alternate bg queries yet"
        key = (bg_query_id, fg_query_id)
        if key not in self.terms_cache.keys():

            selection = select([
                self.concepts.c.concept_id,
                self.concepts.c.concept,
                self.scored_concepts.c.pertinence,
                self.scored_concepts.c.pertinence_ratio,
                self.scored_concepts.c.n_abstracts]).\
                where(self.concepts.c.concept_id == self.scored_concepts.c.concept_id).\
                where(self.scored_concepts.c.query_id == fg_query_id).\
                order_by(self.scored_concepts.c.pertinence.desc())

            df = pandas.read_sql(selection, self.engine)

            self.terms_cache[key] = df

        return self.terms_cache[key]

    def pmids(self, concept_id: str, bg_query_id: int, fg_query_id: int):
        """Gets PMIDs for a given concept id and query context"""
        # Hard coded bg=0 for now
        assert bg_query_id == 0, "We haven't implemented alternate bg queries yet"
        return pandas.read_sql(
            select([self.individual_scores.c.pmid]).
            where(self.individual_scores.c.pmid == self.query_results.c.pmid).
            where(self.query_results.c.query_id == fg_query_id).
            where(self.individual_scores.c.concept_id == concept_id),
            self.engine)['pmid']

    @property
    def query_df(self):
        return self._query_df

    def get_abstract(self, pmid: int):
        return pandas.read_sql(
            select([self.abstracts]).where(self.abstracts.c.pmid == pmid),
            self.engine).iloc[0]

    def get_term_locations(self, pmid: int, concept_id: str):
        return pandas.read_sql(
            select([self.positionals.c.beginning, self.positionals.c.end]).
            where(self.positionals.c.concept_id == concept_id).
            where(self.positionals.c.pmid == pmid).
            order_by(self.positionals.c.beginning),
            self.engine)

    def get_concept_name(self, concept_id):
        return self._concepts_df['concept'][concept_id]
