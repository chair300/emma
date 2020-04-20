# -*- coding: utf-8 -*-
#
# Adapted from the dash tutorial

from emma import EMMA
from data_access import DataHelper
import dash
import dash_table
from dash_table.Format import Format, Scheme
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from sqlalchemy import create_engine


engine = create_engine('sqlite:///data/term_miner.sqlite3')
dh = DataHelper(engine)
backend = EMMA(dh)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    dcc.Store(id='selected-concept'),

    html.H1(children='Explore MetaMap Annotations (EMMA)'),

    html.Div(children=['Database last updated March 12, 2019'], className='small-note'),

    html.Div(
        children=[
            html.H2(children='Background Query'),
            dcc.Dropdown(
                id='bg-query-selection',
                options=backend.bg_query_options_dict,
                value='0'
            ),
            html.P(children=['PubMed query string:']),
            html.Div(id='bg-query-details', className='verbatim-box'),
            html.H2(children='Foreground Query'),
            dcc.Dropdown(
                id='fg-query-selection',
                options=backend.fg_query_options_dict,
                value='1'
            ),
            html.P(children=['PubMed query string:']),
            html.Div(id='fg-query-details', className='verbatim-box'),
            html.H2('UMLS Concept'),
            html.P(id='selection-info'),
            dcc.Loading(
                children=[dash_table.DataTable(
                    id='table',
                    columns=[{'name': 'Concept', 'id': 'concept', 'type': 'text'},
                             {'name': 'Pertinence',
                              'id': 'pertinence',
                              'type': 'numeric',
                              'format': Format(precision=2, scheme=Scheme.fixed)},
                             {'name': 'Count', 'id': 'n_abstracts', 'type': 'numeric'}],
                    data=[],
                    n_fixed_rows=1,
                    row_selectable='single',
                    filtering=False,
                    sorting=False,
                    pagination_mode=False,
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'concept'},
                            'textAlign': 'left',
                            'width': '10em'
                        }
                    ],
                    style_as_list_view=True,
                    style_data={'whiteSpace': 'normal'},
                    css=[{
                        'selector': '.dash-cell div.dash-cell-value',
                        'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
                    }],
                )],
                type='default'
            )
        ],
        style={'width': '40em', 'display': 'inline-block', 'vertical-align': 'top'}
    ),

    html.Div(style={'width': '2em', 'display': 'inline-block'}),

    html.Div(
        children=[dcc.Loading(
            children=html.Div(id='abstracts-div'),
            type='default'
        )],
        style={'width': '40em', 'display': 'inline-block', 'vertical-align': 'top'})
])


@app.callback(
    Output(component_id='table', component_property='data'),
    [Input(component_id='bg-query-selection', component_property='value'),
     Input(component_id='fg-query-selection', component_property='value')]
)
def update_terms_table(bg_query_id, fg_query_id):
    if not fg_query_id or not bg_query_id:
        return []
    else:
        return backend.dict_terms_table(int(bg_query_id), int(fg_query_id))


@app.callback(
    Output(component_id='table', component_property='selected_rows'),
    [Input(component_id='bg-query-selection', component_property='value'),
     Input(component_id='fg-query-selection', component_property='value')]
)
def update_table_selection(bg_query_id, fg_query_id):
    return []


@app.callback(
    Output(component_id='bg-query-details', component_property='children'),
    [Input(component_id='bg-query-selection', component_property='value')]
)
def update_query_details(query_id):
    return backend.query_string(int(query_id))


@app.callback(
    Output(component_id='fg-query-details', component_property='children'),
    [Input(component_id='fg-query-selection', component_property='value')]
)
def update_query_details(query_id):
    return backend.query_string(int(query_id))


@app.callback(
    Output(component_id='selected-concept', component_property='data'),
    [Input(component_id='table', component_property='selected_rows'),
     Input(component_id='bg-query-selection', component_property='value'),
     Input(component_id='fg-query-selection', component_property='value')]
)
def update_selected_concept(row, bg_query, fg_query):
    if not row or bg_query is None or fg_query is None:
        return None
    return backend.look_up_concept_id(row[0], int(bg_query), int(fg_query))


@app.callback(
    Output(component_id='selection-info', component_property='children'),
    [Input(component_id='selected-concept', component_property='data')]
)
def update_selected_row(concept_id):
    if not concept_id:
        return 'Select a UMLS concept using the radio buttons on the left.'
    else:
        return f'Selected UMLS concept: {backend.get_concept_name(concept_id)}'


# Helper functions for formatting abstracts

# Decorates text
def decorate_text(text_str, annotations):
    decorated_text = []

    cursor: int = 0
    for (start, end) in sorted(annotations):
        decorated_text += [
            text_str[cursor:start],
            html.Span(
                children=text_str[start:end],
                style={'background-color': 'yellow'}
            )
        ]
        cursor = end

    decorated_text += [text_str[cursor:]]

    return decorated_text


# Makes html element for abstract
def format_abstract(abstract):

    # Build the decorated title
    decorated_title = decorate_text(abstract['title'], abstract['title annotations'])

    # Build the decorated text
    decorated_text = decorate_text(abstract['text'], abstract['text annotations'])

    return html.Details(
        children=[
            html.Summary(children=decorated_title + [f' (PMID {abstract["pmid"]})'], className='abstract-title'),
            html.Div(children=decorated_text)
        ]
    )


@app.callback(
    Output(component_id='abstracts-div', component_property='children'),
    [Input(component_id='selected-concept', component_property='data'),
     Input(component_id='bg-query-selection', component_property='value'),
     Input(component_id='fg-query-selection', component_property='value')]
)
def update_abstracts(concept_id, bg_query, fg_query):
    if concept_id is None:
        return []
    abstract_data = backend.get_annotated_abstracts(concept_id, int(bg_query), int(fg_query))
    return [format_abstract(a) for a in abstract_data]


if __name__ == '__main__':
    app.run_server(debug=True)
