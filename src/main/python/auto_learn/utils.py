import random
import uuid
import pandas as pd


def change_suggestion(df, day):
    suggestion_list = [tuple[0] for tuple in df.suggestion_list]
    if 'more_option_list' in df:
        more_option_list = [tuple[0] for tuple in df.more_option_list]
        if random.random() < 0.8 ** day:
            max_pos = len(more_option_list) - 1
            if max_pos > 0:
                pos = random.randint(0, max_pos)
            else:
                pos = 0
            df.request_input_suggestion_id = more_option_list[pos]

        else:
            if day == 0:
                chance = 0.95
            else:
                chance = 0.9 / day
            if random.random() < chance:
                pos = len(suggestion_list) - 1
            else:
                better_chance = 1 - 0.9 ** day
                if random.random() < better_chance:
                    pos = 0
                else:
                    max_pos = len(suggestion_list) - 1
                    pos = random.randint(0, max_pos)
            df.request_input_suggestion_id = suggestion_list[pos]
    df.log_id = uuid.uuid1()
    if random.random() < .5:
        df.response_context_conversation_id = uuid.uuid1()
    return df


def no_suggestion(df):
    df.request_input_suggestion_id = None
    df.log_id= uuid.uuid1()
    if random.random() < .5:
        df.response_context_conversation_id = uuid.uuid1()
    return df


def generate_disambiguations(disambiguation_utterances, day):
    df_dups = None

    for idx, utterance in disambiguation_utterances.iterrows():
        while True:
            if random.random() < .3:
                break
            modified_utterance = change_suggestion(utterance, day)
            if df_dups is None:
                df_dups = pd.DataFrame([modified_utterance])
            else:
                df_dups = df_dups.append(modified_utterance)

            better_chance = 1 - 0.9 ** day
            while random.random() < better_chance:
                normal_utterance = no_suggestion(utterance)
                if df_dups is None:
                    df_dups = pd.DataFrame([normal_utterance])
                else:
                    df_dups = df_dups.append(normal_utterance)

    df_dups.request_timestamp = df_dups.request_timestamp + pd.Timedelta(days=day)
    return df_dups.reset_index(drop=True)