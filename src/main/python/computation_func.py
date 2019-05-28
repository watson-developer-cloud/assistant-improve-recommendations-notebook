import decimal
import pandas as pd
import datetime
import re


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


def get_effective_df(df_tbot_raw, ineffective_intents, df_escalate_nodes, filter_non_intent_node, workspace_nodes=None):
    """This function checks the conversations in df_Tbot_raw for escalations, flags them and returns the resulting
    updated dataframe.
       Parameters
       ----------
       df_tbot_raw : Dataframe with workspace logs
       ineffective_intents: list of intents
       df_escalate_nodes: dataframe with escalation dialog nodes
       filter_non_intent_node: whether to filter out utterances whose last visited node does not contain intents
       workspace_nodes: workspace nodes
       Returns
       ----------
       df_tbot_raw : Dataframe with 'Escalated conversation' flag added and updated for each conversation
    """
    # Add an 'Escalated_conversation' flag to dataframe
    df_tbot_raw['Escalated_conversation'] = False

    # Get the list of valid effective dialog node ids
    ineffective_nodes = df_escalate_nodes[df_escalate_nodes['Valid']]['Node ID'].tolist()

    # If nodes visited contains any of the ineffective node ids, get the conversation id
    if filter_non_intent_node:
        df_tbot_raw['last_node'] = df_tbot_raw['response.output.nodes_visited_s'].str[-1].apply(
            lambda x: x if x else [''])
        df_tbot_raw['last_node_value'] = df_tbot_raw['last_node'].apply(
            lambda x: workspace_nodes.loc[workspace_nodes['dialog_node'] == x]['conditions'].values)
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
        conversation_id = [conversation for conversation in df_tbot_raw.loc[
            df_tbot_raw['response.output.nodes_visited_s'].apply(
                lambda x: bool(intersection(x, ineffective_nodes)))].loc[df_tbot_raw['contain_intent']][
            'response.context.conversation_id']]

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
    df_coverage_valid = df_coverage_nodes[df_coverage_nodes['Valid']]  # ['dialog_node'].tolist()

    # (1) Mark all messages that hit any non-coverage node including but not limited to 'anything_else' as 'Not covered'
    #  and update the 'Not Covered cause' column
    for node in df_coverage_valid['Node ID'].tolist():
        cause = "'{}' node".format(df_coverage_valid.loc[df_coverage_valid['Node ID'] == node, 'Condition'].values[0])
        df_tbot_raw.loc[
            (df_tbot_raw['response.output.nodes_visited_s'].apply(lambda x: bool(intersection(x, node.split())))), [
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

    # Separate the fields in request and response
    df1 = pd.concat([df.drop(['request', 'response'], axis=1).reset_index(drop=True),
                     df['request'].apply(pd.Series).add_prefix('request_').reset_index(drop=True),
                     pd.DataFrame(df['response']
                                  .tolist()).add_prefix('response_')], axis=1)  # type: pd.DataFrame
    df1['request_input'] = pd.io.json.json_normalize(df['request'])['input.text']

    # Add context and output fields
    df2 = pd.concat([df1.drop(['response_context', 'response_output'], axis=1),
                     df1['response_context'].apply(pd.Series, dtype='int64').add_prefix('response_context_'),
                     pd.DataFrame(df1['response_output'].tolist()).add_prefix('response_')],
                    axis=1)  # type: pd.DataFrame
    # Add context_system fields
    df3 = pd.concat([df2.drop(['response_context_system'], axis=1),
                     df2['response_context_system'].apply(pd.Series).add_prefix('response_')],
                    axis=1)  # type: pd.DataFrame
    cols = ['log_id', 'response_timestamp', 'response_context_conversation_id', 'request_input', 'response_text',
            'response_intents', 'response_entities', 'response_nodes_visited', 'response_dialog_request_counter',
            'response_dialog_stack', 'response_dialog_turn_counter']
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
    df6.rename(columns={'response_nodes_visited': 'response.output.nodes_visited_s',
                        'response_context_conversation_id': 'response.context.conversation_id',
                        'response_timestamp': 'response.timestamp'}, inplace=True)
    # Change format of numeric and date columns
    df6['response.top_intent_confidence'] = pd.to_numeric(df6['response.top_intent_confidence'])
    df6['response.timestamp'] = pd.to_datetime(df6['response.timestamp'])
    df6['Date'] = [datetime.datetime.date(d) for d in df6['response.timestamp']]  # extracting date from timestamp
    df6['Customer ID (must retain for delete)'] = ''  # Adding a column to retain customer id
    return df6
