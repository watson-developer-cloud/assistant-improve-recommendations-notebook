import pandas as pd
import numpy as np
from tqdm.notebook import tqdm
import itertools
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


def extract_disambiguation_utterances(df_formatted):
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
    for (idx, conversation_id) in enumerate(conversation_ids):
        print('\rProcessing conversation {} ...'.format(idx + 1), end='')
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
                auto_learn_preview = utterance.auto_learn_preview
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


def generate_cooccurrence_matrix(data, workspace_nodes=None):

    all_suggestion_list = list()
    for idx, item in data.iterrows():
        suggestion_dialog_node_list = [s[3] for s in item.suggestion_list]
        if len(suggestion_dialog_node_list) > 0:
            all_suggestion_list.append(suggestion_dialog_node_list)
    combinations = [list(itertools.combinations(i,2)) for i in all_suggestion_list]
    combinations = list(itertools.chain.from_iterable((i, i[::-1]) for c_ in combinations for i in c_))
    combination_pd = pd.DataFrame(combinations)
    cooccurrence_matrix = pd.pivot_table(combination_pd, index=0, columns=1, aggfunc='size', fill_value=0)

    if workspace_nodes is not None:
        node_title_map = dict()
        for idx, node in workspace_nodes.iterrows():
            if str(node['title']) != 'nan':
                node_title_map[node['dialog_node']] = node['title']

        cooccurrence_matrix.index = [node_title_map[i] if i in node_title_map else i for i in cooccurrence_matrix.index]
        cooccurrence_matrix.columns = [node_title_map[i] if i in node_title_map else i for i in
                                       cooccurrence_matrix.columns]

    return cooccurrence_matrix


def extract_suggestions(items):
    suggestions = list()
    for item in items:
        if item['label'] == 'None of the above':
            dialog_node = 'None of the above'
        else:
            dialog_node = item['dialog_node']
        if 'intents' in item['value']:
            suggestions.append(
                (item['value']['input']['suggestion_id'], item['value']['intents'], item['label'], dialog_node))
        else:
            suggestions.append((item['value']['input']['suggestion_id'], item['value']['input']['intents'],
                                item['label'], dialog_node))
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
    if item.request_input_suggestion_id in suggestion_id_list:
        select_pos = suggestion_id_list.index(item.request_input_suggestion_id)
        return select_pos, None, suggestion_dialog_node_list[select_pos]
    elif 'more_option_list' in item.index.values:
        more_option_id_list = [s[0] for s in item.more_option_list]
        more_option_dialog_node_list = [s[3] for s in item.more_option_list]
        if item.request_input_suggestion_id in more_option_id_list:
            select_pos = more_option_id_list.index(item.request_input_suggestion_id)
            if item.more_option_list[select_pos][2] == 'None of the above':
                select_pos = -1
            return None, select_pos, more_option_dialog_node_list[select_pos]
        else:
            return None, None, None
    else:
        return None, None, None


def calculate_preview_effort(item):
    effort_score = -1
    preview_data = item.auto_learn_preview
    if preview_data is None:
        return effort_score
    disambiguation_id_intent = {s[0]: s[1][0]['intent'] if len(s[1]) > 0 else s[2] for s in item.suggestion_list}
    more_option_id_intent = {s[0]: s[1][0]['intent'] if len(s[1]) > 0 else s[2] for s in item.more_option_list}
    if item.request_input_suggestion_id in disambiguation_id_intent:
        selected_disambiguation_intent = disambiguation_id_intent[item.request_input_suggestion_id]
        preview_disambiguation_intents = [s['intent'] if 'intent' in s else s['label'] for s in preview_data['disambiguation']]
        if selected_disambiguation_intent in preview_disambiguation_intents:
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
                print('!!!')
                selected_more_option_intent = more_option_id_intent[item.request_input_suggestion_id]
                preview_more_option_intents = [s['intent'] if 'intent' in s else s['label'] for s in
                                               preview_data['more_option']]
                if selected_more_option_intent == 'None of the above':
                    effort_score = 200
                else:
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
                        effort_score = 200
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
        else:
            clicked_suggestion_rank, clicked_more_option_rank, selected_dialog_node = get_rank(item)
            if clicked_suggestion_rank is not None:
                disambiguation_rank_multiplier = (1 / (MAX_DISAMBIGUATION_LENGTH - 1)) * (clicked_suggestion_rank)
                effort_score = DISAMBIGUATION_OCCURRED_CONTRIBUTION * disambiguation_occurred_multiplier \
                               + DISAMBIGUATION_LENGTH_CONTRIBUTION * disambiguation_length_multiplier \
                               + DISAMBIGUATION_RANK_CONTRIBUTION * disambiguation_rank_multiplier
            #                 if idx<20:
            #                     print('suggestion click: {}'.format(clicked_suggestion_rank))
            #                     print('disambiguation length: {}'.format(len(item.suggestion_list)))
            #                     print('disambiguation_length_multiplier: {}'.format(disambiguation_length_multiplier))
            #                     print('disambiguation_occurred_multiplier: {}'.format(disambiguation_occurred_multiplier))
            #                     print('disambiguation_rank_multiplier: {}'.format(disambiguation_rank_multiplier))
            #                     print('effort_score: {}*{}+{}*{}+{}*{}={}'.format(DISAMBIGUATION_OCCURRED_CONTRIBUTION,
            #                                                                    disambiguation_occurred_multiplier,
            #                                                                    DISAMBIGUATION_LENGTH_CONTRIBUTION,
            #                                                                    disambiguation_length_multiplier,
            #                                                                    DISAMBIGUATION_RANK_CONTRIBUTION,
            #                                                                    disambiguation_rank_multiplier,
            #                                                                    effort_score))
            else:
                if clicked_more_option_rank is not None:
                    if clicked_more_option_rank < 0:
                        effort_score = NONE_OF_THE_OPTIONS
                    else:
                        more_option_rank_multiplier = (1 / (MAX_MORE_OPTION_LENGTH - 1)) * (clicked_more_option_rank)
                        effort_score = MORE_OPTIONS_CONTRIBUTION * more_option_occurred_multiplier + \
                                       MORE_OPTIONS_LENGTH_CONTRIBUTION * more_option_length_multiplier + \
                                       MORE_OPTIONS_RANK_CONTRIBUTION * more_option_rank_multiplier
                else:
                    effort_score = 0.0

        #                 if idx<20:
        #                         print('more option click: {}'.format(clicked_more_option_rank))
        #                         print('more option length: {}'.format(len(item.more_option_list)))
        #                         print('more_option_length_multiplier: {}'.format(more_option_length_multiplier))
        #                         print('more_option_occurred_multiplier: {}'.format(more_option_occurred_multiplier))
        #                         print('more_option_rank_multiplier: {}'.format(more_option_rank_multiplier))
        #                         print('effort_score: {}*{}+{}*{}+{}*{}={}'.format(MORE_OPTIONS_CONTRIBUTION,
        #                                                                        more_option_occurred_multiplier,
        #                                                                        MORE_OPTIONS_LENGTH_CONTRIBUTION,
        #                                                                        more_option_length_multiplier,
        #                                                                        MORE_OPTIONS_RANK_CONTRIBUTION,
        #                                                                        more_option_rank_multiplier,
        #                                                                        effort_score))

        data.at[idx, 'effort_score'] = effort_score
        data.at[idx, 'select_rank_d'] = clicked_suggestion_rank
        data.at[idx, 'select_rank_a'] = clicked_more_option_rank
        data.at[idx, 'selected_dialog_node'] = selected_dialog_node
        data.at[idx, 'preview_effort_score'] = calculate_preview_effort(item)

    data['preview_effort_score'] = np.where(data['preview_effort_score'] == -1, data['effort_score'],
                                            data['preview_effort_score'])
