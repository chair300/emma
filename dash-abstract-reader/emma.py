# Backend for the app. Contains functions for accessing data.
#
#   MIT License
#   Copyright 2019 Yuriy Sverchkov
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
#   documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
#   rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#   permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or substantial portions of
#   the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
#   THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.


from numpy import where


# EMMA class instance
class EMMA:

    def __init__(self, dh):

        self.data = dh
        self._query_options_dict = [
            {'label': f"{row['name']} ({row['size']} abstract{'' if row['size'] == 1 else 's'})",
             'value': str(row['query_id'])}
            for index, row in self.data.query_df.iterrows()]

    def dict_terms_table(self, bg_query_id: int, fg_query_id: int):
        """Part of the interface"""
        return self.data.terms(bg_query_id, fg_query_id).to_dict(orient='records')

    def look_up_concept_id(self, row: int, bg_query_id: int, fg_query_id: int) -> str:
        """
        Get concept id from table row number and query context
        :param row: Row number
        :param bg_query_id: Background query ID
        :param fg_query_id: Foreground query ID
        :return: Concept ID string
        """
        return self.data.terms(bg_query_id, fg_query_id)['concept_id'][row]

    def find_row_matching(self, concept_id: str, bg_query_id: int, fg_query_id: int) -> int or None:
        """
        Get row number from concept ID (inverse of look_up_concept_id)
        :param concept_id: Concept ID
        :param bg_query_id: Background query ID
        :param fg_query_id: Foreground query ID
        :return: Row number or None if not found
        """
        table = self.data.terms(bg_query_id, fg_query_id)
        row = where(table['concept_id'] == concept_id)
        return row[0] if row else None

    def query_string(self, query_id):
        """Part of the interface"""
        return self.data.query_df.at[query_id, 'query_string']

    def get_concept_str(self, row: int, bg_query_id: int, fg_query_id: int) -> str:
        """
        Get concept string from table row number and query context
        :param row: Row number
        :param bg_query_id: Background query ID
        :param fg_query_id: Foreground query ID
        :return: Concept (name) string
        """
        return self.data.terms(bg_query_id, fg_query_id)['concept'][row]

    def get_concept_name(self, concept_id):
        return self.data.get_concept_name(concept_id)

    def get_annotated_abstract(self, pmid: int, concept_id: str):
        """Part of the interface"""

        the_abstract = self.data.get_abstract(pmid)

        mm_locations = self.data.get_term_locations(pmid, concept_id)

        have_text = the_abstract.text is not None

        if have_text:

            assert the_abstract.title_pos < the_abstract.text_pos, \
                f'pmid {pmid}: failed assertion that abstract starts before text'

            text_annotations = mm_locations.loc[mm_locations['beginning'] >= the_abstract.text_pos] \
                .assign(s=lambda x: x['beginning'] - the_abstract.text_pos,
                        end=lambda x: x['end'] - the_abstract.text_pos)

            title_locs = mm_locations.loc[mm_locations['beginning'] < the_abstract.text_pos]

        else:
            title_locs = mm_locations

        title_annotations = title_locs \
            .assign(s=lambda x: x['beginning'] - the_abstract.title_pos,
                    end=lambda x: x['end'] - the_abstract.title_pos)

        return {'pmid': str(pmid),
                'title': the_abstract.title,
                'text': the_abstract.text if have_text else '',  # This is here for text-less abstracts
                'title annotations': title_annotations[['s', 'end']].itertuples(index=False, name=None),
                'text annotations': text_annotations[['s', 'end']].itertuples(index=False,
                                                                              name=None) if have_text else []}

    def get_annotated_abstracts(self, concept_id: str, bg_query_id: int, fg_query_id: int):
        """Get annotated abstracts for a concept and query context."""

        pmids = self.data.pmids(concept_id, bg_query_id, fg_query_id)

        return [self.get_annotated_abstract(pmid, concept_id) for pmid in pmids]

    @property
    def fg_query_options_dict(self):
        """Part of the interface."""
        return self._query_options_dict[1:]  # Hardcoded for now

    @property
    def bg_query_options_dict(self):
        """Part of the interface."""
        return self._query_options_dict[:1]  # Hardcoded for now
