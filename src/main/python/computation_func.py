# coding: utf-8

# (C) Copyright IBM Corp. 2019, 2020.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import decimal
import pandas as pd
import datetime
import re
import itertools
import numpy as np
from IPython.display import HTML

MAX_DISAMBIGUATION_LENGTH = 5
MAX_MORE_OPTION_LENGTH = 5
DISAMBIGUATION_OCCURRED_CONTRIBUTION = 10
DISAMBIGUATION_LENGTH_CONTRIBUTION = 20
DISAMBIGUATION_RANK_CONTRIBUTION = 20
MORE_OPTIONS_CONTRIBUTION = 70
MORE_OPTIONS_LENGTH_CONTRIBUTION = 15
MORE_OPTIONS_RANK_CONTRIBUTION = 15
NONE_OF_THE_OPTIONS = 200


def round_decimal(x, digits=0):
    """This function returns the round up float.
       Parameters
       ----------
       x : a float
       digits : decimal point

       Returns
       ----------
       Rounded up float
    """
    x = decimal.Decimal(str(x))
    if digits == 0:
        return int(x.quantize(decimal.Decimal("1"), rounding='ROUND_HALF_UP'))
    if digits > 1:
        string = '1e' + str(-1 * digits)
    else:
        string = '1e' + str(-1 * digits)
    return float(x.quantize(decimal.Decimal(string), rounding='ROUND_HALF_UP'))


def intersection(list1, list2):
    """This function computes intersection between two input lists and returns the result.
       Parameters
       ----------
       list1 : First list
       list2 : Second list

       Returns
       ----------
       list3 : Intersection of list1 and list2
    """
    list3 = [value for value in list1 if value in list2]
    return list3


def get_effective_df(df_tbot_raw, ineffective_intents, df_escalate_nodes, filter_non_intent_node=False, assistant_nodes=None):
    """This function checks the conversations in df_Tbot_raw for escalations, flags them and returns the resulting
    updated dataframe.
       Parameters
       ----------
       df_tbot_raw : Dataframe with workspace logs
       ineffective_intents: list of intents
       df_escalate_nodes: dataframe with escalation dialog nodes
       filter_non_intent_node: whether to filter out utterances whose last visited node does not contain intents
       assistant_nodes: assistant nodes
       Returns
       ----------
       df_tbot_raw : Dataframe with 'Escalated conversation' flag added and updated for each conversation
    """
    # Add an 'Escalated_conversation' flag to dataframe
    df_tbot_raw['Escalated_conversation'] = False

    # Load node titles
    node_title_map = dict()
    for idx, node in assistant_nodes.iterrows():
        if str(node['title']) != 'nan':
            node_title_map[node['dialog_node']] = node['title']

    # Use node title in nodes_visited_s and response_dialog_stack if it exists
    for idx, item in df_tbot_raw.iterrows():
        node_id_visit_list = item['response.output.nodes_visited_s']
        for seq_id, node_id in enumerate(node_id_visit_list):
            if node_id in node_title_map:
                node_id_visit_list[seq_id] = node_title_map[node_id]

        node_stack_list = item['response_dialog_stack']
        for stack_id, stack_item in enumerate(node_stack_list):
            for key, value in stack_item.items():
                if value in node_title_map:
                    stack_item[key] = node_title_map[value]

    ineffective_nodes = None
    if df_escalate_nodes.size > 0:
        # Get the list of valid effective dialog node ids
        ineffective_nodes = df_escalate_nodes[df_escalate_nodes['Valid']]['Node ID'].tolist()
        ineffective_nodes = [node if node not in node_title_map else node_title_map[node] for node in ineffective_nodes]

    # If nodes visited contains any of the ineffective node ids, get the conversation id
    if filter_non_intent_node:
        conversation_id = list()
        if ineffective_nodes:
            df_tbot_raw['last_node'] = df_tbot_raw['response.output.nodes_visited_s'].str[-1].apply(
                lambda x: x if x else [''])
            df_tbot_raw['last_node_value'] = df_tbot_raw['last_node'].apply(
                lambda x: assistant_nodes.loc[assistant_nodes['dialog_node'] == x]['conditions'].values)
            df_tbot_raw['last_node_value'] = df_tbot_raw['last_node_value'].apply(lambda x: x if x else ['']).str[0]
            df_tbot_raw['contain_intent'] = df_tbot_raw['last_node_value'].apply(
                lambda x: bool(re.match('#[a-zA-Z_0-9]+', str(x))))
            conversation_id = [conversation for conversation in df_tbot_raw.loc[
                df_tbot_raw['response.output.nodes_visited_s'].apply(
                    lambda x: bool(intersection(x, ineffective_nodes)))].loc[df_tbot_raw['contain_intent']][
                'response.context.conversation_id']]

        # If top intent for a message is present in ineffective_intents list, get the conversation id
        conversation_id.extend(df_tbot_raw.loc[(df_tbot_raw['response.top_intent_intent'].isin(
            ineffective_intents)), 'response.context.conversation_id'].loc[
                                   df_tbot_raw['contain_intent']].tolist())

    else:
        conversation_id = list()
        if ineffective_nodes:
            conversation_id = [conversation for conversation in df_tbot_raw.loc[
                df_tbot_raw['response.output.nodes_visited_s'].apply(
                    lambda x: bool(intersection(x, ineffective_nodes)))]['response.context.conversation_id']]

        # If top intent for a message is present in ineffective_intents list, get the conversation id
        conversation_id.extend(df_tbot_raw.loc[(df_tbot_raw['response.top_intent_intent'].isin(
            ineffective_intents)), 'response.context.conversation_id'].tolist())

    # Remove duplicate conversation ids from conversation_id list
    conv_id = list(set(conversation_id))

    # Flag all conversations in conv_id list as 'Escalated'
    df_tbot_raw.loc[df_tbot_raw['response.context.conversation_id'].isin(conv_id), ['Escalated_conversation']] = True

    # Return dataframe with 'Escalated' flag information
    return df_tbot_raw


def get_coverage_df(df_tbot_raw, df_coverage_nodes, conf_threshold):
    """This function computes intersection between two input lists and returns the result.
       Parameters
       ----------
       df_tbot_raw : Dataframe with workspace logs
       df_coverage_nodes: dataframe with non-coverage dialog nodes
       conf_threshold: float, confidence threshold for identifying top intent from assistant

       Returns
       ----------
       df_tbot_raw : Dataframe with 'Covered' flag and 'Not Covered cause' added and updated for each message
    """
    # Convert confidence to numeric type
    # df_tbot_raw['response.top_intent_confidence'] = pd.to_numeric(df_Tbot_raw['response.top_intent_confidence'])

    # Create a 'covered' flag and 'Not covered cause' in dataframe
    df_tbot_raw['Covered'] = True
    df_tbot_raw['Not Covered cause'] = None

    # Filter all the valid dialog node ids for non-coverage
    df_coverage_valid = df_coverage_nodes[df_coverage_nodes['Valid']]
    df_coverage_valid_dict = dict()
    for idx, row in df_coverage_nodes[df_coverage_nodes['Valid']].iterrows():
        df_coverage_valid_dict[row['Node ID']] = {row['Node ID'], row['Node Name']}

    # (1) Mark all messages that hit any non-coverage node including but not limited to 'anything_else' as 'Not covered'
    #  and update the 'Not Covered cause' column
    for node_id, name_set in df_coverage_valid_dict.items():
        cause = "'{}' node".format(df_coverage_valid.loc[df_coverage_valid['Node ID'] == node_id, 'Condition'].values[0])
        df_tbot_raw.loc[
            (df_tbot_raw['response.output.nodes_visited_s'].apply(lambda x: bool(intersection(x, name_set)))), [
                'Covered', 'Not Covered cause']] = [False, cause]

    # (2) Mark all messages  that did not meet confidence threshold set as 'Not covered' and update the 'Not Covered
    # cause' column
    df_tbot_raw.loc[df_tbot_raw['response.top_intent_confidence'] < conf_threshold, ['Covered']] = False
    df_tbot_raw.loc[df_tbot_raw['response.top_intent_confidence'] < conf_threshold, [
        'Not Covered cause']] = 'Classified below confidence threshold'
    return df_tbot_raw


def chk_is_valid_node(node_ids, node_name, node_conditions, nodes):
    """This function checks if the nodes(id's, names and conditions) are present in the workspace.
       Parameters
       ----------
       node_ids : List with node ids'
       node_name: List with node names
       node_conditions: List with node conditions
       nodes: All nodes present in current version of workspace

       Returns
       ----------
       df_valid_nodes : Dataframe with 'Valid' flag added and updated for each node
    """
    # Add a valid flag to dataframe
    nodes['valid'] = True

    # Create a dataframe to store node ids, title, validity, type and conditions
    df_valid_nodes = pd.DataFrame(columns=['conditions', 'dialog_node', 'title', 'type', 'valid'])
    for node in node_ids:
        # Check if the node id is present in current version of workspace
        if node not in nodes['dialog_node'].tolist():
            # Update validity of node to False
            df_valid_nodes.loc[len(df_valid_nodes)] = ['', node, '', '', False]
        else:
            # Add node to valid nodes dataframe
            df_valid_nodes = df_valid_nodes.append(
                nodes[nodes['dialog_node'] == node][['conditions', 'dialog_node', 'title', 'type', 'valid']],
                ignore_index=True)
    for condition in node_conditions:
        # Check if the node condition is present in current version of workspace
        if condition not in nodes['conditions'].tolist():
            # Update validity of node to False
            df_valid_nodes.loc[len(df_valid_nodes)] = [condition, '', '', '', False]
        else:
            # Add node to valid nodes dataframe
            df_valid_nodes = df_valid_nodes.append(
                nodes[nodes['conditions'] == condition][['conditions', 'dialog_node', 'title', 'type', 'valid']],
                ignore_index=True)
    for name in node_name:
        # Check if the node name is present in current version of workspace
        if name not in nodes['title'].tolist():
            # Update validity of node to False
            df_valid_nodes.loc[len(df_valid_nodes)] = ['', '', name, '', False]
        else:
            # Add node to valid nodes dataframe
            df_valid_nodes = df_valid_nodes.append(
                nodes[nodes['title'] == name][['conditions', 'dialog_node', 'title', 'type', 'valid']],
                ignore_index=True)
    # Remove duplicates
    df_valid_nodes = df_valid_nodes.drop_duplicates(keep='first')
    df_valid_nodes.columns = ['Condition', 'Node ID', 'Node Name', 'Type', 'Valid']
    df_valid_nodes = df_valid_nodes.drop('Type', 1)
    return df_valid_nodes


def format_data(df):
    """This function formats the log data from watson assistant by separating columns and changing datatypes
       Parameters
       ----------
       df : Dataframe with logs from the workspace

       Returns
       ----------
       df6 : Dataframe formatted by separating columns and changing datatypes
    """

    if len(df) == 0:
        print('No logs found, please check your data')
        return None

    # Separate the fields in request and response
    print('Extracting request and response ...')
    df1 = pd.concat([df.drop(['request', 'response'], axis=1).reset_index(drop=True),
                     df['request'].apply(pd.Series).add_prefix('request_').reset_index(drop=True),
                     pd.DataFrame(df['response']
                                  .tolist()).add_prefix('response_')], axis=1)  # type: pd.DataFrame
    df1['request_input'] = pd.json_normalize(df['request'])['input.text']

    # Add context and output fields
    print('Extracting context and output ...')
    df2 = pd.concat([df1.drop(['response_context', 'response_output'], axis=1),
                     df1['response_context'].apply(pd.Series).add_prefix('response_context_'),
                     pd.DataFrame(df1['response_output'].tolist()).add_prefix('response_')],
                    axis=1)  # type: pd.DataFrame
    # Add context_system fields
    df3 = pd.concat([df2.drop(['response_context_system'], axis=1),
                     df2['response_context_system'].apply(pd.Series).add_prefix('response_')],
                    axis=1)  # type: pd.DataFrame

    if 'response_context_response_context_IntentStarted' in df3.columns \
            and 'response_context_response_context_IntentCompleted' in df3.columns:
        cols = ['log_id', 'response_timestamp', 'response_context_conversation_id', 'request_input', 'response_text',
                'response_intents', 'response_entities', 'response_nodes_visited', 'response_dialog_request_counter',
                'response_dialog_stack', 'response_dialog_turn_counter',
                'response_context_response_context_IntentStarted', 'response_context_response_context_IntentCompleted']
    else:
        cols = ['log_id', 'response_timestamp', 'response_context_conversation_id', 'request_input', 'response_text',
                'response_intents', 'response_entities', 'response_nodes_visited', 'response_dialog_request_counter',
                'response_dialog_stack', 'response_dialog_turn_counter']

    print('Extracting intents ...')
    # Select a few required columns
    df4 = df3[cols].copy(deep=True)  # type: pd.DataFrame
    # Limit fetched intents to a maximum value of 3
    df4.loc[:, 'response_intents'] = df4['response_intents'].apply(lambda x: x[:3])
    # Separate intents into different fields
    df5 = pd.concat([df4.drop(['response_intents'], axis=1),
                     pd.DataFrame(df4['response_intents'].values.tolist()).add_prefix(
                         'response_intent_')], axis=1)  # type: pd.DataFrame
    # Check if at least 3 intents are identified
    if 'response_intent_2' in df5.columns:
        # Put the 3 intents and confidences into separate fields
        df6 = pd.concat([df5.drop(['response_intent_0', 'response_intent_1',
                                   'response_intent_2'], axis=1),
                         df5['response_intent_0'].apply(pd.Series).add_prefix('response.top_intent_'),
                         df5['response_intent_1'].apply(pd.Series).add_prefix('Intent 2 '),
                         df5['response_intent_2'].apply(pd.Series).add_prefix('Intent 3 ')],
                        axis=1)  # type: pd.DataFrame
        # Convert confidence to numeric type
        cols = ['response.top_intent_confidence', 'Intent 2 confidence', 'Intent 3 confidence']
        df6[cols] = df6[cols].apply(pd.to_numeric, errors='coerce', axis=1)
        # Add confidence gap column
        df6['Confidence gap (between 1 and 2)'] = df6['response.top_intent_confidence'] - df6['Intent 2 confidence']
    elif 'response_intent_1' in df5.columns:
        # Put the 3 intents and confidences into separate fields
        df6 = pd.concat([df5.drop(['response_intent_0', 'response_intent_1'], axis=1),
                         df5['response_intent_0'].apply(pd.Series).add_prefix('response.top_intent_'),
                         df5['response_intent_1'].apply(pd.Series).add_prefix('Intent 2 ')],
                        axis=1)  # type: pd.DataFrame
        # Convert confidence to numeric type
        cols = ['response.top_intent_confidence', 'Intent 2 confidence']
        df6[cols] = df6[cols].apply(pd.to_numeric, errors='coerce', axis=1)
        df6['Intent 3 intent'] = ''
        df6['Intent 3 confidence'] = ''
        # Add confidence gap column
        df6['Confidence gap (between 1 and 2)'] = df6['response.top_intent_confidence'] - df6['Intent 2 confidence']
    else:
        # Create the top intent and its confidence column
        df6 = pd.concat([df5.drop(['response_intent_0'], axis=1),
                         df5['response_intent_0'].apply(pd.Series).add_prefix('response.top_intent_')],
                        axis=1)  # type: pd.DataFrame
        # df6['Confidence gap (between 1 and 2)'] = ''
        # df6['Intent 2 intent'] =''
        # df6['Intent 2 confidence'] = ''
        # df6['Intent 3 intent'] =''
        # df6['Intent 3 confidence'] = ''
        new_cols_list = ['Confidence gap (between 1 and 2)', 'Intent 2 intent', 'Intent 2 confidence',
                         'Intent 3 intent', 'Intent 3 confidence']

        df6.reindex(columns=[*df6.columns.tolist(), *new_cols_list], fill_value='')

    # Rename columns
    if 'response_context_response_context_IntentStarted' in df6.columns \
            and 'response_context_response_context_IntentCompleted' in df6.columns:
        df6.rename(columns={'response_nodes_visited': 'response.output.nodes_visited_s',
                            'response_context_conversation_id': 'response.context.conversation_id',
                            'response_timestamp': 'response.timestamp',
                            'response_context_response_context_IntentStarted': 'response_context_IntentStarted',
                            'response_context_response_context_IntentCompleted': 'response_context_IntentCompleted'},
                   inplace=True)
    else:
        df6.rename(columns={'response_nodes_visited': 'response.output.nodes_visited_s',
                            'response_context_conversation_id': 'response.context.conversation_id',
                            'response_timestamp': 'response.timestamp'},
                   inplace=True)
    # Change format of numeric and date columns
    df6['response.top_intent_confidence'] = pd.to_numeric(df6['response.top_intent_confidence'])
    df6['response.timestamp'] = pd.to_datetime(df6['response.timestamp'])
    df6['Date'] = [datetime.datetime.date(d) for d in df6['response.timestamp']]  # extracting date from timestamp
    df6['Customer ID (must retain for delete)'] = ''  # Adding a column to retain customer id

    print('Completed!')
    return df6


def format_logs_disambiguation(df):
    print('Extracting request and response ...')
    df = pd.concat([df.drop(['request', 'response'], axis=1).reset_index(drop=True),
                     df['request'].apply(pd.Series).add_prefix('request_').reset_index(drop=True),
                     pd.DataFrame(df['response']
                                  .tolist()).add_prefix('response_')], axis=1)

    print('Extracting response input ...')
    df = pd.concat([df.drop(['request_input'], axis=1),
                    df['request_input'].apply(pd.Series).add_prefix('request_input_')], axis=1)

    print('Extracting response output and context ...')
    df = pd.concat([df.drop(['response_context', 'response_output'], axis=1),
                    df['response_context'].apply(pd.Series).add_prefix('response_context_'),
                    pd.DataFrame(df['response_output'].tolist()).add_prefix('response_')], axis=1)

    print('Extracting disambiguation traffic ...')
    df = pd.concat([df.drop(['response_generic'], axis=1),
                    df['response_generic'].apply(pd.Series).add_prefix('response_generic_')], axis=1)
    df = pd.concat([df.drop(['response_generic_0'], axis=1),
                    df['response_generic_0'].apply(pd.Series).add_prefix('response_generic_0_')], axis=1).copy()

    for row in df.loc[df.response_generic_0_suggestions.isnull(), 'response_generic_0_suggestions'].index:
        df.at[row, 'response_generic_0_suggestions'] = []

    for row in df.loc[df.request_input_suggestion_id.isnull(), 'request_input_suggestion_id'].index:
        df.at[row, 'request_input_suggestion_id'] = ''

    df.response_generic_0_suggestions = df.response_generic_0_suggestions.apply(extract_suggestions)

    if 'response_debug' in df:
        df = pd.concat([df.drop(['response_debug'], axis=1),
                        df.response_debug.replace({np.nan: None}).apply(extract_autolearn_debug)], axis=1)

    if 'response_alternate_responses' in df:
        print('Extracting more options traffic ...')
        df = pd.concat([df.drop(['response_alternate_responses'], axis=1),
                         df['response_alternate_responses'].apply(pd.Series).add_prefix('response_alternate_responses_')],
                        axis=1)

        df = pd.concat([df.drop(['response_alternate_responses_0'], axis=1),
                         df['response_alternate_responses_0'].apply(pd.Series).add_prefix(
                             'response_alternate_responses_0_')], axis=1)

        for row in df.loc[
            df.response_alternate_responses_0_suggestions.isnull(), 'response_alternate_responses_0_suggestions'].index:
            df.at[row, 'response_alternate_responses_0_suggestions'] = []

        df.response_alternate_responses_0_suggestions = df.response_alternate_responses_0_suggestions.apply(
            extract_suggestions)

    df.request_timestamp = pd.to_datetime(df.request_timestamp)

    print('Completed!')
    return df


def extract_disambiguation_utterances(df_formatted):
    df_formatted['request_datetime_interval'] = [d.replace(second=0, microsecond=0, minute=0, hour=0)
                                                          for d in df_formatted.request_timestamp]
    unique_days = df_formatted['request_datetime_interval'].unique()
    conversation_ids = df_formatted.response_context_conversation_id.unique()
    print('Extracting disambiguation logs from {} conversations ...'.format(len(conversation_ids)))
    list_conversations = list()
    disambiguation_utterances = None
    num_disambiguation_utterances = 0
    num_disambiguation_conversations = 0
    num_more_utterances = 0
    num_both_utterances = 0
    num_more_conversations = 0
    num_both_conversations = 0
    for conversation_id in conversation_ids:
        utterances = df_formatted.loc[df_formatted.response_context_conversation_id == conversation_id].sort_values(
            by='request_timestamp').reset_index(drop=True)
        utterances['suggestion_list'] = np.empty((len(utterances), 0)).tolist()
        if 'response_alternate_responses_0_suggestions' in utterances:
            utterances['more_option_list'] = np.empty((len(utterances), 0)).tolist()
        suggestions = None
        more_options = None
        auto_learn_preview = None
        auto_learn_apply = None
        contain_disambiguation = False
        contain_more = False
        list_conversations.append(utterances)
        for idx, utterance in utterances.iterrows():
            if suggestions:
                if len(utterance.request_input_suggestion_id) != 0:
                    utterance.suggestion_list = suggestions
                    utterance.auto_learn_preview = auto_learn_preview
                    utterance.auto_learn_apply = auto_learn_apply
                    if more_options:
                        utterance.more_option_list = more_options
                        more_options = None
                    suggestions = None
                    if disambiguation_utterances is None:
                        disambiguation_utterances = pd.DataFrame([utterance])
                    else:
                        disambiguation_utterances = disambiguation_utterances.append(utterance)
                else:
                    suggestions = None
                    more_options = None
                    auto_learn_preview = None
                    auto_learn_apply = None
            if utterance.response_generic_0_response_type == 'suggestion':
                suggestions = utterance.response_generic_0_suggestions
                if 'auto_learn_preview' in utterance:
                    auto_learn_preview = utterance.auto_learn_preview
                if 'auto_learn_apply' in utterance:
                    auto_learn_apply = utterance.auto_learn_apply
                num_disambiguation_utterances += 1
                if not contain_disambiguation:
                    contain_disambiguation = True
            if 'response_alternate_responses_0_response_type' in utterance:
                if utterance.response_alternate_responses_0_response_type == 'suggestion':
                    more_options = utterance.response_alternate_responses_0_suggestions
                    if not contain_more:
                        contain_more = True
                    if utterance.response_generic_0_response_type == 'suggestion':
                        num_both_utterances += 1
                    else:
                        num_more_utterances += 1
        if contain_disambiguation and not contain_more:
            num_disambiguation_conversations += 1
        if contain_more and not contain_disambiguation:
            num_more_conversations += 1
        if contain_disambiguation and contain_more:
            num_both_conversations += 1

    print('\n\nData Statistics:')
    print('Number of days: {}'.format(len(unique_days)))
    print('Disambiguation events per day: {}'.format(round(num_disambiguation_utterances / len(unique_days))))

    utterance_statistics = {}
    utterance_statistics['Utterance'] = ['Total', 'Disambiguation', 'More Options', 'Both']
    utterance_statistics['Count'] = [len(df_formatted.log_id.unique()), num_disambiguation_utterances, num_more_utterances, num_both_utterances]
    utterance_statistics['Percentage'] = ['100.0%', '{}%'.format(round(
        num_disambiguation_utterances / len(df_formatted.log_id.unique()) * 100, 1)), '{}%'.format(round(
        num_more_utterances / len(df_formatted.log_id.unique()) * 100, 1)), '{}%'.format(round(
        num_both_utterances / len(df_formatted.log_id.unique()) * 100, 1))]

    statistics_pd = pd.DataFrame.from_dict(utterance_statistics)
    statistics_pd = statistics_pd.set_index('Utterance')
    utterance_html = statistics_pd.to_html().replace('     <th>Utterance</th>\n      <th></th>\n      <th></th>\n    </tr>\n', '').replace('<th></th>\n', '<th>Utterance</th>\n')

    conversation_statistics = {}
    conversation_statistics['Conversation'] = ['Total', 'Disambiguation', 'More Options', 'Both']
    conversation_statistics['Count'] = [len(conversation_ids), num_disambiguation_conversations, num_more_conversations, num_both_conversations]
    conversation_statistics['Percentage'] = ['100.0%', '{}%'.format(round(
        num_disambiguation_conversations / len(conversation_ids) * 100, 1)), '{}%'.format(round(
        num_more_conversations / len(conversation_ids) * 100, 1)), '{}%'.format(round(num_both_conversations / len(conversation_ids) * 100,
                                                                   1))]

    statistics_pd = pd.DataFrame.from_dict(conversation_statistics)
    statistics_pd = statistics_pd.set_index('Conversation')
    conversation_html = statistics_pd.to_html().replace('     <th>Conversation</th>\n      <th></th>\n      <th></th>\n    </tr>\n', '').replace('<th></th>\n', '<th>Conversation</th>\n')

    display(HTML('<style>.aParent div {{\n float: left;\nclear: none;padding: 20px; \n\}}</style><div class="aParent"><div>{}</div><div>{}</div></div>'.format(utterance_html, conversation_html)))

    return disambiguation_utterances.sort_values(by='request_timestamp').reset_index(drop=True)


def generate_cooccurrence_matrix(data, assistant_nodes=None, exclude_nodes=None):
    if exclude_nodes is None:
        exclude_nodes = set()
    all_suggestion_list = list()
    for idx, item in data.iterrows():
        suggestion_dialog_node_list = [s[3] for s in item.suggestion_list]
        if len(suggestion_dialog_node_list) > 0:
            all_suggestion_list.append(suggestion_dialog_node_list)

    none_above_node_name = list(data[data['is_none_above_node'] == True].selected_dialog_node.unique())

    if len(none_above_node_name) > 1:
        print('Found more than one \'None of the Above\' nodes.')
    elif len(none_above_node_name) == 0:
        print('No \'None of the Above\' node found')
    else:
        for i in all_suggestion_list:
            if none_above_node_name[0] in i:
                i.remove(none_above_node_name[0])

    if assistant_nodes is not None:
        node_title_map = dict()
        for idx, node in assistant_nodes.iterrows():
            if str(node['title']) != 'nan':
                node_title_map[node['dialog_node']] = node['title']

        def find_node_name(node_list):
            for idx, node in enumerate(node_list):
                if node in node_title_map:
                    node_list[idx] = node_title_map[node]
            return node_list

        list(map(find_node_name, all_suggestion_list))

    combinations = [list(itertools.combinations(i, 2)) for i in all_suggestion_list if
                    len(set(i) & set(exclude_nodes)) == 0]
    combinations = list(itertools.chain.from_iterable((i, i[::-1]) for c_ in combinations for i in c_))
    combination_pd = pd.DataFrame(combinations)
    cooccurrence_matrix = pd.pivot_table(combination_pd, index=0, columns=1, aggfunc='size', fill_value=0)

    return cooccurrence_matrix


def extract_suggestions(items):
    suggestions = list()
    for item in items:
        if 'intents' in item['value']:
            if len(item['value']['intents']) == 0:
                dialog_node = item['label']
                none_node = True
                if len(item['output']['generic']) > 0:
                    if item['output']['generic'][0]['response_type'] == 'search_skill':
                        none_node = False
            else:
                dialog_node = item['dialog_node']
                none_node = False
            suggestions.append((item['value']['input']['suggestion_id'], item['value']['intents'], item['label'],
                                dialog_node, none_node))
        elif 'input' in item['value']:
            if len(item['value']['input']['intents']) == 0:
                dialog_node = item['label']
                none_node = True
                if len(item['output']['generic']) > 0:
                    if item['output']['generic'][0]['response_type'] == 'search_skill':
                        none_node = False
            else:
                dialog_node = item['dialog_node']
                none_node = False
            suggestions.append((item['value']['input']['suggestion_id'], item['value']['input']['intents'],
                                item['label'], dialog_node, none_node))
        else:
            print('Please check item value {}'.format(item))
    return suggestions


def extract_autolearn_debug(item):
    auto_learn_preview = None
    auto_learn_apply = None
    disambiguation_dict_list = list()
    more_option_dict_list = list()
    disambiguation_dict = dict()
    more_option_dict = dict()
    if item:
        if 'auto_learn' in item:
            if 'preview' in item['auto_learn']:
                if 'disambiguation' in item['auto_learn']['preview']:
                    if 'suggestions' in item['auto_learn']['preview']['disambiguation']:
                        for suggestion in item['auto_learn']['preview']['disambiguation']['suggestions']:
                            suggestion_dict = dict()
                            if 'label' in suggestion:
                                suggestion_dict['label'] = suggestion['label']
                            if 'value' in suggestion:
                                value = suggestion['value']
                                if 'intents' in value:
                                    if len(value['intents']) == 1:
                                        if 'intent' in value['intents'][0]:
                                            suggestion_dict['intent'] = value['intents'][0]['intent']
                                        if 'confidence' in value['intents'][0]:
                                            suggestion_dict['confidence'] = value['intents'][0]['confidence']
                                    elif len(value['intents']) > 1:
                                        print('Error: find multiple intents in preview disambiguation')
                                if 'input' in value:
                                    if 'suggestion_id' in value['input']:
                                        suggestion_dict['suggestion_id'] = value['input']['suggestion_id']
                                    if 'text' in value['input']:
                                        suggestion_dict['text'] = value['input']['text']
                            disambiguation_dict_list.append(suggestion_dict)

                if 'alternate_responses' in item['auto_learn']['preview']:
                    if 'suggestions' in item['auto_learn']['preview']['alternate_responses']:
                        for suggestion in item['auto_learn']['preview']['alternate_responses']['suggestions']:
                            suggestion_dict = dict()
                            if 'label' in suggestion:
                                suggestion_dict['label'] = suggestion['label']
                            if 'value' in suggestion:
                                value = suggestion['value']
                                if 'intents' in value:
                                    if len(value['intents']) == 1:
                                        if 'intent' in value['intents'][0]:
                                            suggestion_dict['intent'] = value['intents'][0]['intent']
                                        if 'confidence' in value['intents'][0]:
                                            suggestion_dict['confidence'] = value['intents'][0]['confidence']
                                    elif len(value['intents']) > 1:
                                        print('Error: find multiple intents in preview disambiguation')
                                if 'input' in value:
                                    if 'suggestion_id' in value['input']:
                                        suggestion_dict['suggestion_id'] = value['input']['suggestion_id']
                                    if 'text' in value['input']:
                                        suggestion_dict['text'] = value['input']['text']
                            more_option_dict_list.append(suggestion_dict)

                auto_learn_preview = {'disambiguation': disambiguation_dict_list, 'more_option': more_option_dict_list}
            else:
                if 'disambiguation' in item['auto_learn']:
                    if 'model_id' in item['auto_learn']['disambiguation']:
                        disambiguation_dict['model_id'] = item['auto_learn']['disambiguation']['model_id']
                    if 'model_type' in item['auto_learn']['disambiguation']:
                        disambiguation_dict['model_type'] = item['auto_learn']['disambiguation']['model_type']

                if 'alternate_responses' in item['auto_learn']:
                    if 'model_id' in item['auto_learn']['alternate_responses']:
                        more_option_dict['model_id'] = item['auto_learn']['alternate_responses']['model_id']
                    if 'model_type' in item['auto_learn']['alternate_responses']:
                        more_option_dict['model_type'] = item['auto_learn']['alternate_responses']['model_type']
                auto_learn_apply = {'disambiguation': disambiguation_dict, 'more_option': more_option_dict}

    return pd.Series({'auto_learn_preview': auto_learn_preview, 'auto_learn_apply': auto_learn_apply})


def format_logs(df):
    print('Extracting request and response ...')
    df = pd.concat([df.drop(['request', 'response'], axis=1).reset_index(drop=True),
                     df['request'].apply(pd.Series).add_prefix('request_').reset_index(drop=True),
                     pd.DataFrame(df['response']
                                  .tolist()).add_prefix('response_')], axis=1)

    print('Extracting response input ...')
    df = pd.concat([df.drop(['request_input'], axis=1),
                    df['request_input'].apply(pd.Series).add_prefix('request_input_')], axis=1)

    print('Extracting response output and context ...')
    df = pd.concat([df.drop(['response_context', 'response_output'], axis=1),
                    df['response_context'].apply(pd.Series).add_prefix('response_context_'),
                    pd.DataFrame(df['response_output'].tolist()).add_prefix('response_')], axis=1)

    print('Extracting disambiguation traffic ...')
    df = pd.concat([df.drop(['response_generic'], axis=1),
                    df['response_generic'].apply(pd.Series).add_prefix('response_generic_')], axis=1)
    df = pd.concat([df.drop(['response_generic_0'], axis=1),
                    df['response_generic_0'].apply(pd.Series).add_prefix('response_generic_0_')], axis=1).copy()

    for row in df.loc[df.response_generic_0_suggestions.isnull(), 'response_generic_0_suggestions'].index:
        df.at[row, 'response_generic_0_suggestions'] = []

    for row in df.loc[df.request_input_suggestion_id.isnull(), 'request_input_suggestion_id'].index:
        df.at[row, 'request_input_suggestion_id'] = ''

    df.response_generic_0_suggestions = df.response_generic_0_suggestions.apply(extract_suggestions)

    if 'response_debug' in df:
        df = pd.concat([df.drop(['response_debug'], axis=1),
                        df.response_debug.replace({np.nan: None}).apply(extract_autolearn_debug)], axis=1)

    if 'response_alternate_responses' in df:
        print('Extracting more options traffic ...')
        df = pd.concat([df.drop(['response_alternate_responses'], axis=1),
                         df['response_alternate_responses'].apply(pd.Series).add_prefix('response_alternate_responses_')],
                        axis=1)

        df = pd.concat([df.drop(['response_alternate_responses_0'], axis=1),
                         df['response_alternate_responses_0'].apply(pd.Series).add_prefix(
                             'response_alternate_responses_0_')], axis=1)

        for row in df.loc[
            df.response_alternate_responses_0_suggestions.isnull(), 'response_alternate_responses_0_suggestions'].index:
            df.at[row, 'response_alternate_responses_0_suggestions'] = []

        df.response_alternate_responses_0_suggestions = df.response_alternate_responses_0_suggestions.apply(
            extract_suggestions)

    df.request_timestamp = pd.to_datetime(df.request_timestamp)

    print('Completed!')
    return df


def get_rank(item):
    suggestion_id_list = [s[0] for s in item.suggestion_list]
    suggestion_dialog_node_list = [s[3] for s in item.suggestion_list]
    suggestion_none_above_node_list = [s[4] for s in item.suggestion_list]
    if item.request_input_suggestion_id in suggestion_id_list:
        select_pos = suggestion_id_list.index(item.request_input_suggestion_id)
        return select_pos, None, suggestion_dialog_node_list[select_pos], suggestion_none_above_node_list[select_pos]
    elif 'more_option_list' in item.index.values:
        more_option_id_list = [s[0] for s in item.more_option_list]
        more_option_dialog_node_list = [s[3] for s in item.more_option_list]
        more_option_none_above_node_list = [s[4] for s in item.more_option_list]
        if item.request_input_suggestion_id in more_option_id_list:
            select_pos = more_option_id_list.index(item.request_input_suggestion_id)
            return None, select_pos, more_option_dialog_node_list[select_pos], more_option_none_above_node_list[select_pos]
        else:
            return None, None, None, None
    else:
        return None, None, None, None


def calculate_preview_effort(item):
    effort_score = -1
    if 'auto_learn_preview' in item:
        preview_data = item.auto_learn_preview
        if preview_data is None:
            return effort_score
    else:
        return effort_score
    disambiguation_id_intent = {s[0]: s[1][0]['intent'] if len(s[1]) > 0 else s[2] for s in item.suggestion_list}
    disambiguation_id_none_above = {s[0]: s[4] for s in item.suggestion_list}
    if 'more_option_list' in item:
        more_option_id_intent = {s[0]: s[1][0]['intent'] if len(s[1]) > 0 else s[2] for s in item.more_option_list}
        more_option_id_none_above = {s[0]: s[4] for s in item.more_option_list}
    else:
        more_option_id_intent = {}
        more_option_id_none_above = {}
    if item.request_input_suggestion_id in disambiguation_id_intent:
        selected_disambiguation_intent = disambiguation_id_intent[item.request_input_suggestion_id]
        preview_disambiguation_intents = [s['intent'] if 'intent' in s else s['label'] for s in preview_data['disambiguation']]
        if selected_disambiguation_intent in preview_disambiguation_intents:
            if disambiguation_id_none_above[item.request_input_suggestion_id] is True:
                effort_score = NONE_OF_THE_OPTIONS
            else:
                preview_disambiguation_rank = preview_disambiguation_intents.index(selected_disambiguation_intent)
                if len(preview_disambiguation_intents) == 1:
                    effort_score = 0
                else:
                    disambiguation_occurred_multiplier = 1
                    disambiguation_length_multiplier = (1 / (MAX_DISAMBIGUATION_LENGTH - 1)) * (
                            len(preview_disambiguation_intents) - 1)
                    disambiguation_rank_multiplier = (1 / (MAX_DISAMBIGUATION_LENGTH - 1)) * (preview_disambiguation_rank)
                    effort_score = DISAMBIGUATION_OCCURRED_CONTRIBUTION * disambiguation_occurred_multiplier \
                                   + DISAMBIGUATION_LENGTH_CONTRIBUTION * disambiguation_length_multiplier \
                                   + DISAMBIGUATION_RANK_CONTRIBUTION * disambiguation_rank_multiplier
        else:
            if item.request_input_suggestion_id in more_option_id_intent:
                if more_option_id_none_above[item.request_input_suggestion_id] is True:
                    effort_score = NONE_OF_THE_OPTIONS
                else:
                    selected_more_option_intent = more_option_id_intent[item.request_input_suggestion_id]
                    preview_more_option_intents = [s['intent'] if 'intent' in s else s['label'] for s in
                                                   preview_data['more_option']]
                    if selected_more_option_intent in preview_more_option_intents:
                        preview_more_option_rank = preview_more_option_intents.index(selected_more_option_intent)
                        more_option_occurred_multiplier = 1
                        more_option_length_multiplier = (1 / (MAX_MORE_OPTION_LENGTH - 1)) * (
                                len(preview_more_option_intents) - 1)
                        more_option_rank_multiplier = (1 / (MAX_MORE_OPTION_LENGTH - 1)) * preview_more_option_rank
                        effort_score = MORE_OPTIONS_CONTRIBUTION * more_option_occurred_multiplier + \
                                       MORE_OPTIONS_LENGTH_CONTRIBUTION * more_option_length_multiplier + \
                                       MORE_OPTIONS_RANK_CONTRIBUTION * more_option_rank_multiplier
                    else:
                        effort_score = NONE_OF_THE_OPTIONS
    return effort_score


def calculate_effort(data):
    disambiguation_occurred_multiplier = 1
    more_option_occurred_multiplier = 1
    data['effort_score'] = 0.0
    for idx, item in data.iterrows():
        disambiguation_length_multiplier = (1 / (MAX_DISAMBIGUATION_LENGTH - 1)) * (len(item.suggestion_list) - 1)
        if 'more_option_list' in item:
            more_option_length_multiplier = (1 / (MAX_MORE_OPTION_LENGTH - 1)) * (len(item.more_option_list) - 1)
        else:
            more_option_length_multiplier = 0

        if item.request_input_suggestion_id is None:
            clicked_suggestion_rank = None
            clicked_more_option_rank = None
            effort_score = 0.0
            selected_dialog_node = None
            is_none_above = False
        else:
            clicked_suggestion_rank, clicked_more_option_rank, selected_dialog_node, is_none_above = get_rank(item)
            if clicked_suggestion_rank is not None:
                if is_none_above is True:
                    effort_score = NONE_OF_THE_OPTIONS
                else:
                    disambiguation_rank_multiplier = (1 / (MAX_DISAMBIGUATION_LENGTH - 1)) * (clicked_suggestion_rank)
                    effort_score = DISAMBIGUATION_OCCURRED_CONTRIBUTION * disambiguation_occurred_multiplier \
                                   + DISAMBIGUATION_LENGTH_CONTRIBUTION * disambiguation_length_multiplier \
                                   + DISAMBIGUATION_RANK_CONTRIBUTION * disambiguation_rank_multiplier

            else:
                if clicked_more_option_rank is not None:
                    if is_none_above is True:
                        effort_score = NONE_OF_THE_OPTIONS
                    else:
                        more_option_rank_multiplier = (1 / (MAX_MORE_OPTION_LENGTH - 1)) * (clicked_more_option_rank)
                        effort_score = MORE_OPTIONS_CONTRIBUTION * more_option_occurred_multiplier + \
                                       MORE_OPTIONS_LENGTH_CONTRIBUTION * more_option_length_multiplier + \
                                       MORE_OPTIONS_RANK_CONTRIBUTION * more_option_rank_multiplier
                else:
                    effort_score = 0.0

        data.at[idx, 'effort_score'] = effort_score
        data.at[idx, 'select_rank_d'] = clicked_suggestion_rank
        data.at[idx, 'select_rank_a'] = clicked_more_option_rank
        data.at[idx, 'selected_dialog_node'] = selected_dialog_node
        data.at[idx, 'is_none_above_node'] = is_none_above
        data.at[idx, 'preview_effort_score'] = calculate_preview_effort(item)

    data['preview_effort_score'] = np.where(data['preview_effort_score'] == -1, data['effort_score'],
                                            data['preview_effort_score'])

