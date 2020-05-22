from bokeh.io import push_notebook, show, output_notebook
from bokeh.models import ColumnDataSource, DataTable, TableColumn, LinearColorMapper, ColorBar, LinearColorMapper, \
    BasicTicker, PrintfTickFormatter, Select, CustomJS, LinearAxis, Range1d, BoxAnnotation, Toggle
from bokeh.layouts import row, column
from bokeh.plotting import figure
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models import HoverTool
from bokeh.models import DataRange1d
from bokeh.palettes import brewer
from bokeh.transform import transform
import pandas as pd
from datetime import date, datetime, timedelta
import numpy as np


def show_top_node_effort(disambiguation_utterances, top=10, assistant_nodes=None):
    node_title_map = dict()
    for idx, node in assistant_nodes.iterrows():
        if str(node['title']) != 'nan':
            node_title_map[node['dialog_node']] = node['title']

    none_above_node_name = list(disambiguation_utterances[disambiguation_utterances[
                                                              'is_none_above_node'] == True].selected_dialog_node.unique())
    if len(none_above_node_name) > 1:
        print('Found more than one \'None of the Above\' nodes.')

    dialog_node_effort_overall_df = disambiguation_utterances[['selected_dialog_node', 'effort_score']].groupby(
        'selected_dialog_node').agg({'effort_score': 'mean', 'selected_dialog_node': 'size'}).sort_values(
        ['effort_score'],
        ascending=False)
    dialog_node_effort_overall_df.columns = ['effort_score', 'num_utterances']
    dialog_node_effort_overall_df = dialog_node_effort_overall_df.reset_index()

    dialog_node_effort_overall_df = dialog_node_effort_overall_df[
        ~dialog_node_effort_overall_df['selected_dialog_node'].isin(none_above_node_name)]

    for idx, item in dialog_node_effort_overall_df.iterrows():
        if item.selected_dialog_node in node_title_map:
            dialog_node_effort_overall_df.at[idx, 'selected_dialog_node_name'] = node_title_map[
                item.selected_dialog_node]
        else:
            dialog_node_effort_overall_df.at[idx, 'selected_dialog_node_name'] = item.selected_dialog_node

    output_notebook(hide_banner=True)

    source = ColumnDataSource(dialog_node_effort_overall_df.head(top))

    p = figure(plot_width=950, plot_height=350,
               y_range=dialog_node_effort_overall_df.head(top)['selected_dialog_node_name'].iloc[::-1],
               x_range=DataRange1d(start=0), title='Nodes yield the highest customer effort')

    p.hbar(y='selected_dialog_node_name', left='effort_score', source=source, height=0.4, fill_color='#BFC5CD',
           line_color='#BFC5CD', hover_fill_color='#1C679A', hover_line_color='#1C679A')

    hover = HoverTool(
        tooltips=[
            ("Node Name", "@selected_dialog_node_name"),
            ("Number of Logs", "@num_utterances"),
            ("Avg Customer Effort", "@effort_score{0.0f}")
        ]
    )
    p.title.align = 'center'
    p.title.text_font_size = '12pt'
    p.axis.major_label_text_font_size = "10pt"

    p.add_tools(hover)

    show(p)


def datetime_range(start, end, delta):
    current = start
    while current <= end:
        yield current
        current += delta


def show_node_effort(disambiguation_utterances, assistant_nodes=None, interval=None):
    start_delta = None
    end_delta = None
    delta = None
    bar_width = None
    if interval == 'minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=d.minute, hour=d.hour) + timedelta(minutes=(d.second // 30)) for d
            in
            disambiguation_utterances.request_timestamp]
        start_delta = timedelta(minutes=1)
        end_delta = timedelta(minutes=1)
        delta = timedelta(minutes=1)
        bar_width = 50 * 1000
    elif interval == '5-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 5) * 5) for d in
            disambiguation_utterances.request_timestamp]
        start_delta = timedelta(minutes=3)
        end_delta = timedelta(minutes=3)
        delta = timedelta(minutes=5)
        bar_width = 4 * 60 * 1000
    elif interval == '15-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 15) * 15) for d
            in disambiguation_utterances.request_timestamp]
        start_delta = timedelta(minutes=8)
        end_delta = timedelta(minutes=8)
        delta = timedelta(minutes=15)
        bar_width = 13 * 60 * 1000
    elif interval == '30-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 30) * 30) for d
            in disambiguation_utterances.request_timestamp]
        start_delta = timedelta(minutes=15)
        end_delta = timedelta(minutes=15)
        delta = timedelta(minutes=30)
        bar_width = 25 * 60 * 1000
    elif interval == 'hour':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) for d in
            disambiguation_utterances.request_timestamp]
        start_delta = timedelta(minutes=30)
        end_delta = timedelta(minutes=30)
        delta = timedelta(minutes=60)
        bar_width = 50 * 60 * 1000
    elif interval == 'day':
        disambiguation_utterances['request_datetime_interval'] = [d.replace(second=0, microsecond=0, minute=0, hour=0)
                                                                  for d in disambiguation_utterances.request_timestamp]
        start_delta = timedelta(days=1)
        end_delta = timedelta(days=1)
        delta = timedelta(days=1)
        bar_width = 20 * 60 * 60 * 1000
    elif interval == 'week':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) + timedelta(minutes=(d.day // 7) * 7) for d in
            disambiguation_utterances.request_timestamp]
        start_delta = timedelta(days=3)
        end_delta = timedelta(days=3)
        delta = timedelta(days=7)
        bar_width = 5 * 24 * 60 * 60 * 1000
    elif interval == 'month':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) for d in
            disambiguation_utterances.request_timestamp]
        start_delta = timedelta(days=15)
        end_delta = timedelta(days=15)
        delta = timedelta(days=30)
        bar_width = 15 * 24 * 60 * 60 * 1000
    else:
        print(
            'Invalid interval, please choose from {"minute", "5-minute", "15-minute", "30-minute", "hour", "day", "week", "month"}')

    if delta:
        dialog_node_effort_df = disambiguation_utterances[
            ['request_datetime_interval', 'selected_dialog_node', 'effort_score']].groupby(
            ['request_datetime_interval', 'selected_dialog_node'], as_index=False).agg({'effort_score': 'mean'})

        valid_effort_nodes = dialog_node_effort_df['selected_dialog_node'].unique()

        none_above_node_name = list(disambiguation_utterances[disambiguation_utterances[
                                                                  'is_none_above_node'] == True].selected_dialog_node.unique())
        if len(none_above_node_name) > 1:
            print('Found more than one \'None of the Above\' nodes.')

        if len(none_above_node_name) > 0:
            index = np.argwhere(valid_effort_nodes == none_above_node_name[0])
            valid_effort_nodes = np.delete(valid_effort_nodes, index)

        node_title_map = dict()
        for idx, node in assistant_nodes.iterrows():
            if str(node['title']) != 'nan':
                node_title_map[node['dialog_node']] = node['title']

        dialog_node_effort_df = disambiguation_utterances[
            ['request_datetime_interval', 'selected_dialog_node', 'effort_score']].groupby(
            ['request_datetime_interval', 'selected_dialog_node'], as_index=False).agg({'effort_score': 'mean'})

        start_datetime = dialog_node_effort_df.request_datetime_interval.iloc[0]
        end_datetime = dialog_node_effort_df.request_datetime_interval.iloc[-1]

        if start_datetime == end_datetime:
            start_datetime -= delta
            end_datetime += delta
        time_index_df = pd.DataFrame([dt for dt in datetime_range(start_datetime, end_datetime, delta)],
                                     columns=['request_datetime_interval'])
        for node_id in valid_effort_nodes:
            node_effort_df = dialog_node_effort_df.loc[dialog_node_effort_df['selected_dialog_node'] == node_id][
                ['request_datetime_interval', 'effort_score']]
            time_index_df = time_index_df.merge(node_effort_df, how='left', on=['request_datetime_interval'])
            if node_id in node_title_map:
                node_name = node_title_map[node_id]
            else:
                node_name = node_id
            time_index_df.rename(columns={'effort_score': 'effort_score_{}'.format(node_name)}, inplace=True)
        time_index_df = time_index_df.fillna(0)

        if valid_effort_nodes[0] in node_title_map:
            default_node_name = node_title_map[valid_effort_nodes[0]]
        else:
            default_node_name = valid_effort_nodes[0]
        node_effort_df = time_index_df[['request_datetime_interval', 'effort_score_{}'.format(default_node_name)]]
        node_effort_df.columns = ['request_datetime_interval', 'effort_score']
        output_notebook(hide_banner=True)

        source = ColumnDataSource(node_effort_df)
        source_all = ColumnDataSource(time_index_df)

        p = figure(plot_width=950, plot_height=350, x_axis_type="datetime",
                   x_range=(start_datetime - start_delta, end_datetime + end_delta),
                   y_range=DataRange1d(start=0), title='Dialog node: "{}"'.format(default_node_name))

        p.vbar(x='request_datetime_interval', top='effort_score', source=source, width=bar_width, fill_color='#BFC5CD',
               line_color='#BFC5CD', hover_fill_color='#1C679A', hover_line_color='#1C679A')

        p.xaxis.formatter = DatetimeTickFormatter(
            seconds=["%Y-%m-%d %H:%M:%S"],
            minsec=["%Y-%m-%d %H:%M:%S"],
            minutes=["%Y-%m-%d %H:%M:%S"],
            hourmin=["%Y-%m-%d %H:%M:%S"],
            hours=["%Y-%m-%d %H:%M:%S"],
            days=["%Y-%m-%d %H:%M:%S"],
            months=["%Y-%m-%d %H:%M:%S"],
            years=["%Y-%m-%d %H:%M:%S"],
        )
        p.xaxis.major_label_orientation = 0.5
        p.yaxis.axis_label = 'Customer Effort'
        hover = HoverTool(
            tooltips=[
                ("Date & Time", "@request_datetime_interval{%Y-%m-%d %H:%M:%S}"),
                ("Customer Effort", "@effort_score{0.0f}")
            ],
            formatters={
                '@request_datetime_interval': 'datetime'
            },
        )
        p.title.align = 'center'
        p.title.text_font_size = '12pt'
        p.add_tools(hover)

        select = Select(title="Select a dialog node:", value=default_node_name,
                        options=[node_title_map[n] if n in node_title_map else n for n in valid_effort_nodes])
        select_callback = CustomJS(args=dict(source=source, source_all=source_all, title=p.title), code="""
                var data = source_all.data;
                title.text = 'Node: "' + cb_obj.value + '"'
                var new_data = [];
                var selected_node_id = cb_obj.value
                var effort_scores = data['effort_score' + '_' + selected_node_id]
                var new_effort_scores = [];

                for (var i = 0; i < effort_scores.length; i++) {
                    new_effort_scores.push(effort_scores[i])
                }

                source.data['effort_score'] = new_effort_scores
                source.change.emit();
            """)
        select.js_on_change('value', select_callback)

        layout = column(select, p)

        show(layout)


def show_input_effort(disambiguation_utterances, top, interval=None):
    start_delta = None
    end_delta = None
    delta = None
    bar_width = None
    if interval == 'minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=d.minute, hour=d.hour) + timedelta(minutes=(d.second // 30)) for d
            in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=1)
        start_delta = timedelta(minutes=1)
        end_delta = timedelta(minutes=1)
        bar_width = 50 * 1000
    elif interval == '5-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 5) * 5) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=5)
        start_delta = timedelta(minutes=3)
        end_delta = timedelta(minutes=3)
        bar_width = 4 * 60 * 1000
    elif interval == '15-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 15) * 15) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=15)
        start_delta = timedelta(minutes=8)
        end_delta = timedelta(minutes=8)
        bar_width = 13 * 60 * 1000
    elif interval == '30-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 30) * 30) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=30)
        start_delta = timedelta(minutes=15)
        end_delta = timedelta(minutes=15)
        bar_width = 25 * 60 * 1000
    elif interval == 'hour':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=60)
        start_delta = timedelta(minutes=30)
        end_delta = timedelta(minutes=30)
        bar_width = 50 * 60 * 1000
    elif interval == 'day':
        disambiguation_utterances['request_datetime_interval'] = [d.replace(second=0, microsecond=0, minute=0, hour=0)
                                                                  for d in disambiguation_utterances.request_timestamp]
        delta = timedelta(days=1)
        start_delta = timedelta(days=1)
        end_delta = timedelta(days=1)
        bar_width = 20 * 60 * 60 * 1000
    elif interval == 'week':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) + timedelta(minutes=(d.day // 7) * 7) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(days=7)
        start_delta = timedelta(days=3)
        end_delta = timedelta(days=3)
        bar_width = 5 * 24 * 60 * 60 * 1000
    elif interval == 'month':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(days=30)
        start_delta = timedelta(days=15)
        end_delta = timedelta(days=15)
        bar_width = 15 * 24 * 60 * 60 * 1000
    else:
        print(
            'Invalid interval, please choose from {"minute", "5-minute", "15-minute", "30-minute", "hour", "day", "week", "month"}')

    if delta:
        input_effort_df = disambiguation_utterances[
            ['request_datetime_interval', 'request_input_text', 'effort_score']].groupby(
            ['request_datetime_interval', 'request_input_text']).agg(
            {'effort_score': 'mean', 'request_input_text': 'count'})

        input_effort_df.columns = ['effort_score', 'count']

        input_effort_df = input_effort_df.reset_index()

        input_effort_top = disambiguation_utterances[['request_input_text', 'effort_score']].groupby(
            'request_input_text').agg({'effort_score': 'mean', 'request_input_text': 'size'}).sort_values(
            ['effort_score'], ascending=False)
        input_effort_options = input_effort_top.index.tolist()[:top]

        start_datetime = input_effort_df.request_datetime_interval.iloc[0]
        end_datetime = input_effort_df.request_datetime_interval.iloc[-1]

        if start_datetime == end_datetime:
            start_datetime -= delta
            end_datetime += delta

        time_index_df = pd.DataFrame([dt for dt in datetime_range(start_datetime, end_datetime, delta)],
                                     columns=['request_datetime_interval'])
        for input_id, input_text in enumerate(input_effort_options):
            node_effort_df = input_effort_df.loc[input_effort_df['request_input_text'] == input_text][
                ['request_datetime_interval', 'effort_score']]
            time_index_df = time_index_df.merge(node_effort_df, how='left', on=['request_datetime_interval'])
            time_index_df.rename(columns={'effort_score': 'effort_score_{}'.format(input_id)}, inplace=True)
        time_index_df = time_index_df.fillna(0)

        node_effort_df = time_index_df[['request_datetime_interval', 'effort_score_0']]
        node_effort_df.columns = ['request_datetime_interval', 'effort_score']
        output_notebook(hide_banner=True)

        source = ColumnDataSource(node_effort_df)
        source_all = ColumnDataSource(time_index_df)

        p = figure(plot_width=950, plot_height=350, x_axis_type="datetime",
                   x_range=(start_datetime - start_delta, end_datetime + end_delta),
                   y_range=DataRange1d(start=0), title='Utterance: "{}"'.format(input_effort_options[0]))

        p.vbar(x='request_datetime_interval', top='effort_score', source=source, width=bar_width, fill_color='#BFC5CD',
               line_color='#BFC5CD', hover_fill_color='#1C679A', hover_line_color='#1C679A')

        p.xaxis.formatter = DatetimeTickFormatter(
            seconds=["%Y-%m-%d %H:%M:%S"],
            minsec=["%Y-%m-%d %H:%M:%S"],
            minutes=["%Y-%m-%d %H:%M:%S"],
            hourmin=["%Y-%m-%d %H:%M:%S"],
            hours=["%Y-%m-%d %H:%M:%S"],
            days=["%Y-%m-%d %H:%M:%S"],
            months=["%Y-%m-%d %H:%M:%S"],
            years=["%Y-%m-%d %H:%M:%S"],
        )
        p.xaxis.major_label_orientation = 0.5
        p.yaxis.axis_label = 'Customer Effort'
        hover = HoverTool(
            tooltips=[
                ("Date & Time", "@request_datetime_interval{%Y-%m-%d %H:%M:%S}"),
                ("Customer Effort", "@effort_score{0.0f}")
            ],
            formatters={
                '@request_datetime_interval': 'datetime'
            },
        )
        p.title.align = 'center'
        p.title.text_font_size = '12pt'
        p.add_tools(hover)

        select = Select(title="Select an utterance:", value=input_effort_options[0], options=input_effort_options)
        select_callback = CustomJS(
            args=dict(source=source, source_all=source_all, options=input_effort_options, title=p.title), code="""
                var data = source_all.data;
                var new_data = [];
                var selected_input = cb_obj.value
                title.text = 'Input: "' + selected_input + '"'


                var selected_id = options.indexOf(selected_input)

                var effort_scores = data['effort_score' + '_' + selected_id]


                var new_effort_scores = [];

                for (var i = 0; i < effort_scores.length; i++) {
                    new_effort_scores.push(effort_scores[i])
                }

                source.data['effort_score'] = new_effort_scores
                source.change.emit();
            """)
        select.js_on_change('value', select_callback)

        layout = column(select, p)

        show(layout)


def show_disambiguation_click(disambiguation_utterances, interval=None):
    start_delta = None
    end_delta = None
    delta = None
    bar_width = None
    if interval == 'minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=d.minute, hour=d.hour) + timedelta(minutes=(d.second // 30)) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=1)
        start_delta = timedelta(minutes=1)
        end_delta = timedelta(minutes=1)
        bar_width = 50 * 1000
    elif interval == '5-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 5) * 5) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=5)
        start_delta = timedelta(minutes=3)
        end_delta = timedelta(minutes=3)
        bar_width = 4 * 60 * 1000
    elif interval == '15-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 15) * 15) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=15)
        start_delta = timedelta(minutes=8)
        end_delta = timedelta(minutes=8)
        bar_width = 13 * 60 * 1000
    elif interval == '30-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 30) * 30) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=30)
        start_delta = timedelta(minutes=15)
        end_delta = timedelta(minutes=15)
        bar_width = 25 * 60 * 1000
    elif interval == 'hour':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=60)
        start_delta = timedelta(minutes=30)
        end_delta = timedelta(minutes=30)
        bar_width = 50 * 60 * 1000
    elif interval == 'day':
        disambiguation_utterances['request_datetime_interval'] = [d.replace(second=0, microsecond=0, minute=0, hour=0)
                                                                  for d in disambiguation_utterances.request_timestamp]
        delta = timedelta(days=1)
        start_delta = timedelta(days=1)
        end_delta = timedelta(days=1)
        bar_width = 20 * 60 * 60 * 1000
    elif interval == 'week':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) + timedelta(minutes=(d.day // 7) * 7) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(days=7)
        start_delta = timedelta(days=3)
        end_delta = timedelta(days=3)
        bar_width = 5 * 24 * 60 * 60 * 1000
    elif interval == 'month':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(days=30)
        start_delta = timedelta(days=15)
        end_delta = timedelta(days=15)
        bar_width = 15 * 24 * 60 * 60 * 1000
    else:
        print(
            'Invalid interval, please choose from {"minute", "5-minute", "15-minute", "30-minute", "hour", "day", "week", "month"}')

    if delta:
        click_detail_pd = disambiguation_utterances[['request_datetime_interval', 'select_rank_d']].groupby(
            ['request_datetime_interval', 'select_rank_d'], as_index=False).size().reset_index()

        if click_detail_pd.shape[0] == 0:
            print('No Disambiguation click found.')
            return

        start_datetime = click_detail_pd.request_datetime_interval.iloc[0]
        end_datetime = click_detail_pd.request_datetime_interval.iloc[-1]
        if start_datetime == end_datetime:
            start_datetime -= delta
            end_datetime += delta

        time_index_df = pd.DataFrame([dt for dt in datetime_range(start_datetime, end_datetime, delta)],
                                     columns=['request_datetime_interval'])

        select_rank_df = None
        for i in range(5):
            i_df = time_index_df.merge(click_detail_pd.loc[click_detail_pd.select_rank_d == i], how='left',
                                       on=['request_datetime_interval'])
            i_df.columns = ['request_datetime_interval', 'select_rank_d_{}'.format(i), i]
            i_df['select_rank_d_{}'.format(i)] = i_df['select_rank_d_{}'.format(i)].fillna(i)
            i_df[i] = i_df[i].fillna(0)
            if select_rank_df is None:
                select_rank_df = i_df
            else:
                select_rank_df = select_rank_df.merge(i_df, how='left', on=['request_datetime_interval'])

        column_names = ['request_datetime_interval']
        column_names.extend([i for i in range(5)])
        vis_df = select_rank_df[column_names].copy()
        vis_df.columns = ['request_datetime_interval'] + ["click_on_%d" % i for i in range(1, 6)]
        vis_df['total'] = vis_df[["click_on_%d" % i for i in range(1, 6)]].sum(axis=1)

        colors = tuple(
            [(int(255 * (0.1 + 0.7 * (1 - i * 0.2))), int(255 * (0.4 + 0.4 * (1 - i * 0.2))), int(255 * 0.8), 0.8) for i
             in
             range(5)])

        output_notebook(hide_banner=True)

        p = figure(plot_width=950, plot_height=350, x_axis_type="datetime",
                   x_range=(start_datetime - start_delta, end_datetime + end_delta),
                   y_range=DataRange1d(start=0), title='Disambiguation click distribution over time')
        p.grid.minor_grid_line_color = '#eeeeee'
        names = ["click_on_%d" % i for i in range(1, 6)]
        legend_names = ["Click-%d" % i for i in range(1, 6)]

        p.vbar_stack(names, x='request_datetime_interval', color=colors, source=vis_df, width=bar_width,
                     legend_label=legend_names, line_color=None, hover_fill_color='#1C679A', hover_line_color='#1C679A')

        p.xaxis.formatter = DatetimeTickFormatter(
            seconds=["%Y-%m-%d %H:%M:%S"],
            minsec=["%Y-%m-%d %H:%M:%S"],
            minutes=["%Y-%m-%d %H:%M:%S"],
            hourmin=["%Y-%m-%d %H:%M:%S"],
            hours=["%Y-%m-%d %H:%M:%S"],
            days=["%Y-%m-%d %H:%M:%S"],
            months=["%Y-%m-%d %H:%M:%S"],
            years=["%Y-%m-%d %H:%M:%S"],
        )
        p.xaxis.major_label_orientation = 0.5
        p.yaxis.axis_label = 'Number of Clicks'
        p.title.align = 'center'
        p.title.text_font_size = '12pt'
        hover = HoverTool(
            tooltips=[
                ("Datetime", "@request_datetime_interval{%Y-%m-%d %H:%M:%S}"),
                ("Click-1", "@click_on_1"),
                ("Click-2", "@click_on_2"),
                ("Click-3", "@click_on_3"),
                ("Click-4", "@click_on_4"),
                ("Click-5", "@click_on_5"),
                ("Total", "@total")

            ],
            formatters={
                '@request_datetime_interval': 'datetime'
            },
        )
        p.legend.click_policy = "hide"
        p.legend.orientation = "horizontal"
        p.add_tools(hover)

        show(p)


def show_more_options_click(disambiguation_utterances, interval=None):
    start_delta = None
    end_delta = None
    delta = None
    bar_width = None
    if interval == 'minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=d.minute, hour=d.hour) + timedelta(minutes=(d.second // 30)) for d
            in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=1)
        start_delta = timedelta(minutes=1)
        end_delta = timedelta(minutes=1)
        bar_width = 50 * 1000
    elif interval == '5-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 5) * 5) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=5)
        start_delta = timedelta(minutes=3)
        end_delta = timedelta(minutes=3)
        bar_width = 4 * 60 * 1000
    elif interval == '15-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 15) * 15) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=15)
        start_delta = timedelta(minutes=8)
        end_delta = timedelta(minutes=8)
        bar_width = 13 * 60 * 1000
    elif interval == '30-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 30) * 30) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=30)
        start_delta = timedelta(minutes=15)
        end_delta = timedelta(minutes=15)
        bar_width = 25 * 60 * 1000
    elif interval == 'hour':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=60)
        start_delta = timedelta(minutes=30)
        end_delta = timedelta(minutes=30)
        bar_width = 50 * 60 * 1000
    elif interval == 'day':
        disambiguation_utterances['request_datetime_interval'] = [d.replace(second=0, microsecond=0, minute=0, hour=0)
                                                                  for d in disambiguation_utterances.request_timestamp]
        delta = timedelta(days=1)
        start_delta = timedelta(days=1)
        end_delta = timedelta(days=1)
        bar_width = 20 * 60 * 60 * 1000
    elif interval == 'week':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) + timedelta(minutes=(d.day // 7) * 7) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(days=7)
        start_delta = timedelta(days=3)
        end_delta = timedelta(days=3)
        bar_width = 5 * 24 * 60 * 60 * 1000
    elif interval == 'month':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(days=30)
        start_delta = timedelta(days=15)
        end_delta = timedelta(days=15)
        bar_width = 15 * 24 * 60 * 60 * 1000
    else:
        print(
            'Invalid interval, please choose from {"minute", "5-minute", "15-minute", "30-minute", "hour", "day", "week", "month"}')

    if delta:
        click_detail_pd = disambiguation_utterances[['request_datetime_interval', 'select_rank_a']].groupby(
            ['request_datetime_interval', 'select_rank_a'], as_index=False).size().reset_index()

        if click_detail_pd.shape[0] == 0:
            print('No More Options click found.')
            return

        start_datetime = click_detail_pd.request_datetime_interval.iloc[0]
        end_datetime = click_detail_pd.request_datetime_interval.iloc[-1]

        if start_datetime == end_datetime:
            start_datetime -= delta
            end_datetime += delta

        time_index_df = pd.DataFrame([dt for dt in datetime_range(start_datetime, end_datetime, delta)],
                                     columns=['request_datetime_interval'])

        select_rank_df = None
        for i in range(5):
            i_df = time_index_df.merge(click_detail_pd.loc[click_detail_pd.select_rank_a == i], how='left',
                                       on=['request_datetime_interval'])
            i_df.columns = ['request_datetime_interval', 'select_rank_a_{}'.format(i), i]
            i_df['select_rank_a_{}'.format(i)] = i_df['select_rank_a_{}'.format(i)].fillna(3)
            i_df[i] = i_df[i].fillna(0)
            if select_rank_df is None:
                select_rank_df = i_df
            else:
                select_rank_df = select_rank_df.merge(i_df, how='left', on=['request_datetime_interval'])

        column_names = ['request_datetime_interval']
        column_names.extend([i for i in range(5)])
        vis_df = select_rank_df[column_names].copy()
        vis_df.columns = ['request_datetime_interval'] + ["click_on_%d" % i for i in range(1, 6)]
        vis_df['total'] = vis_df[["click_on_%d" % i for i in range(1, 6)]].sum(axis=1)

        output_notebook(hide_banner=True)

        p = figure(plot_width=950, plot_height=350, x_axis_type="datetime",
                   x_range=(start_datetime - start_delta, end_datetime + end_delta),
                   y_range=DataRange1d(start=0), title='More options click distribution over time')
        p.grid.minor_grid_line_color = '#eeeeee'
        names = ["click_on_%d" % i for i in range(1, 6)]
        legend_names = ["Click-%d" % i for i in range(1, 6)]

        colors = tuple(
            [(int(255 * (0.1 + 0.7 * (1 - i * 0.2))), int(255 * (0.4 + 0.4 * (1 - i * 0.2))), int(255 * 0.8), 0.8) for i
             in
             range(5)])

        p.vbar_stack(names, x='request_datetime_interval', color=colors, source=vis_df, width=bar_width,
                     legend_label=legend_names, line_color=None, hover_fill_color='#1C679A', hover_line_color='#1C679A')

        p.xaxis.formatter = DatetimeTickFormatter(
            seconds=["%Y-%m-%d %H:%M:%S"],
            minsec=["%Y-%m-%d %H:%M:%S"],
            minutes=["%Y-%m-%d %H:%M:%S"],
            hourmin=["%Y-%m-%d %H:%M:%S"],
            hours=["%Y-%m-%d %H:%M:%S"],
            days=["%Y-%m-%d %H:%M:%S"],
            months=["%Y-%m-%d %H:%M:%S"],
            years=["%Y-%m-%d %H:%M:%S"],
        )
        p.xaxis.major_label_orientation = 0.5
        p.yaxis.axis_label = 'Number of Clicks'
        p.title.align = 'center'
        p.title.text_font_size = '12pt'
        hover = HoverTool(
            tooltips=[
                ("Datetime", "@request_datetime_interval{%Y-%m-%d %H:%M:%S}"),
                ("Click-1", "@click_on_1"),
                ("Click-2", "@click_on_2"),
                ("Click-3", "@click_on_3"),
                ("Click-4", "@click_on_4"),
                ("Click-5", "@click_on_5"),
                ("Total", "@total")

            ],
            formatters={
                '@request_datetime_interval': 'datetime'
            },
        )
        p.legend.click_policy = "hide"
        p.legend.orientation = "horizontal"
        p.add_tools(hover)

        show(p)


def show_cooccured_nodes(top_confused_pairs):
    output_notebook(hide_banner=True)
    columns = [TableColumn(field=Ci, title=Ci) for Ci in top_confused_pairs.columns]
    source = ColumnDataSource(top_confused_pairs)
    data_table = DataTable(source=source, columns=columns, width=600)

    show(data_table)


def show_cooccured_heatmap(cooccurrence_matrix):
    output_notebook(hide_banner=True)

    cooccurrence_matrix.columns.name = 'Node A'
    cooccurrence_matrix.index.name = 'Node B'

    df = pd.DataFrame(cooccurrence_matrix.stack(), columns=['count']).reset_index()
    source = ColumnDataSource(df)
    mapper = LinearColorMapper(palette=tuple(reversed(brewer['Blues'][256])), low=df['count'].min(),
                               high=df['count'].max())
    num_elements = cooccurrence_matrix.shape[0]
    p = figure(plot_width=700 + 8 * num_elements, plot_height=600 + 8 * num_elements, title="Node Co-occurrence Map",
               x_range=list(cooccurrence_matrix.index), y_range=list(reversed(cooccurrence_matrix.columns)),
               toolbar_location=None, tools="hover")

    p.rect(x="Node A", y="Node B", width=0.9, height=0.9, fill_alpha=1, source=source,
           line_color=None, fill_color=transform('count', mapper), hover_line_color="#08306b")

    color_bar = ColorBar(color_mapper=mapper, location=(0, 0),
                         ticker=BasicTicker(desired_num_ticks=10),
                         formatter=PrintfTickFormatter(format="%d"))

    p.add_layout(color_bar, 'right')

    p.hover.tooltips = [
        ("Node A", "@{Node B}"),
        ("Node B", "@{Node A}"),
        ("Count", "@{count}")
    ]

    p.xaxis.major_label_orientation = 0.8
    p.outline_line_color = None
    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_standoff = 0
    p.axis.major_label_text_font_size = "10pt"

    p.title.align = 'center'
    p.title.text_font_size = '12pt'

    show(p)


def show_click_vs_effort(disambiguation_utterances, interval):
    start_delta = None
    end_delta = None
    delta = None
    bar_width = None

    if 'auto_learn_apply' in disambiguation_utterances:
        start_applied_idx = disambiguation_utterances.auto_learn_apply.first_valid_index()
        end_applied_idx = disambiguation_utterances.auto_learn_apply.last_valid_index()
    else:
        start_applied_idx = None
        end_applied_idx = None

    if start_applied_idx is not None and end_applied_idx is not None:
        none_list = disambiguation_utterances[start_applied_idx:end_applied_idx][
            disambiguation_utterances[start_applied_idx:end_applied_idx]['auto_learn_apply'].isnull()].index.tolist()
        none_list.insert(0, start_applied_idx)
        none_list.append(end_applied_idx)
        intervals = list(split_tol(none_list, 1))
        time_intervals = [
            [disambiguation_utterances.iloc[x[0]].request_timestamp,
             disambiguation_utterances.iloc[x[-1]].request_timestamp]
            for x in intervals]
    else:
        time_intervals = list()

    if interval == 'minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=d.minute, hour=d.hour) + timedelta(minutes=(d.second // 30)) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=1)
        start_delta = timedelta(minutes=1)
        end_delta = timedelta(minutes=1)
        bar_width = 50 * 1000
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=start_timestamp.minute,
                                                             hour=start_timestamp.hour) + timedelta(
                minutes=(start_timestamp.second // 30))
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=end_timestamp.minute,
                                                           hour=end_timestamp.hour) + timedelta(
                minutes=(end_timestamp.second // 30))
    elif interval == '5-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 5) * 5) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=5)
        start_delta = timedelta(minutes=3)
        end_delta = timedelta(minutes=3)
        bar_width = 4 * 60 * 1000
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0,
                                                             hour=start_timestamp.hour) + timedelta(
                minutes=(start_timestamp.minute // 5) * 5)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0,
                                                           hour=end_timestamp.hour) + timedelta(
                minutes=(end_timestamp.minute // 5) * 5)
    elif interval == '15-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 15) * 15) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=15)
        start_delta = timedelta(minutes=8)
        end_delta = timedelta(minutes=8)
        bar_width = 13 * 60 * 1000
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0,
                                                             hour=start_timestamp.hour) + timedelta(
                minutes=(start_timestamp.minute // 15) * 15)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0,
                                                           hour=end_timestamp.hour) + timedelta(
                minutes=(end_timestamp.minute // 15) * 15)
    elif interval == '30-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 30) * 30) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=30)
        start_delta = timedelta(minutes=15)
        end_delta = timedelta(minutes=15)
        bar_width = 25 * 60 * 1000
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0,
                                                             hour=start_timestamp.hour) + timedelta(
                minutes=(start_timestamp.minute // 30) * 30)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0,
                                                           hour=end_timestamp.hour) + timedelta(
                minutes=(end_timestamp.minute // 30) * 30)
    elif interval == 'hour':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=60)
        start_delta = timedelta(minutes=30)
        end_delta = timedelta(minutes=30)
        bar_width = 50 * 60 * 1000
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0,
                                                             hour=start_timestamp.hour)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0, hour=end_timestamp.hour)
    elif interval == 'day':
        disambiguation_utterances['request_datetime_interval'] = [d.replace(second=0, microsecond=0, minute=0, hour=0)
                                                                  for d in disambiguation_utterances.request_timestamp]
        delta = timedelta(days=1)
        start_delta = timedelta(days=1)
        end_delta = timedelta(days=1)
        bar_width = 20 * 60 * 60 * 1000
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0, hour=0)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0, hour=0)
    elif interval == 'week':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) + timedelta(minutes=(d.day // 7) * 7) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(days=7)
        start_delta = timedelta(days=3)
        end_delta = timedelta(days=3)
        bar_width = 5 * 24 * 60 * 60 * 1000
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0, hour=0,
                                                             day=1) + timedelta(
                minutes=(start_timestamp.day // 7) * 7)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0, hour=0,
                                                           day=1) + timedelta(
                minutes=(end_timestamp.day // 7) * 7)
    elif interval == 'month':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(days=30)
        start_delta = timedelta(days=15)
        end_delta = timedelta(days=15)
        bar_width = 15 * 24 * 60 * 60 * 1000
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0, hour=0, day=1)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0, hour=0, day=1)
    else:
        print(
            'Invalid interval, please choose from {"minute", "5-minute", "15-minute", "30-minute", "hour", "day", "week", "month"}')

    if delta:

        none_above_node_name = list(disambiguation_utterances[disambiguation_utterances[
                                                                  'is_none_above_node'] == True].selected_dialog_node.unique())

        if len(none_above_node_name) > 1:
            print('Found more than one \'None of the Above\' nodes.')
        elif len(none_above_node_name) == 0:
            none_above_node_name = ['None of the Above']

        effort_agg = disambiguation_utterances[['request_datetime_interval', 'effort_score']].groupby(
            ['request_datetime_interval'], as_index=False).agg({'effort_score': ['mean', 'sum', 'count']})

        effort_agg.columns = ['request_datetime_interval', 'effort_score_mean', 'effort_score_sum', 'count']

        start_datetime = effort_agg.request_datetime_interval.iloc[0]
        end_datetime = effort_agg.request_datetime_interval.iloc[-1]
        if start_datetime == end_datetime:
            start_datetime -= delta
            end_datetime += delta

        disambiguation_count = disambiguation_utterances.loc[disambiguation_utterances.select_rank_d.notnull()][
            ['request_datetime_interval', 'request_input_suggestion_id']].groupby(['request_datetime_interval'],
                                                                                  as_index=False).agg(
            {'request_input_suggestion_id': 'count'})
        alternate_click_count = disambiguation_utterances.loc[disambiguation_utterances.select_rank_a >= 0][
            ['request_datetime_interval', 'request_input_suggestion_id']].groupby(['request_datetime_interval'],
                                                                                  as_index=False).agg(
            {'request_input_suggestion_id': 'count'})
        none_click_count = disambiguation_utterances.loc[disambiguation_utterances.is_none_above_node == True][
            ['request_datetime_interval', 'request_input_suggestion_id']].groupby(['request_datetime_interval'],
                                                                                  as_index=False).agg(
            {'request_input_suggestion_id': 'count'})

        time_index_df = pd.DataFrame([dt for dt in datetime_range(start_datetime, end_datetime, delta)],
                                     columns=['request_datetime_interval'])
        click_agg = time_index_df.merge(disambiguation_count, how='left', on=['request_datetime_interval'])
        click_agg = click_agg.merge(alternate_click_count, how='left', on=['request_datetime_interval'])
        click_agg = click_agg.merge(none_click_count, how='left', on=['request_datetime_interval']).fillna(0)
        click_agg.columns = ['request_datetime_interval', 'disambiguation_count', 'alternate_click_count',
                             'none_click_count']

        effort_data = click_agg.merge(effort_agg, how='left', on=['request_datetime_interval'])
        effort_data['effort_score_sum'] = effort_data['effort_score_sum'].fillna(0)
        effort_data['effort_score_mean'] = effort_data['effort_score_mean'].fillna(0)
        effort_data['count'] = effort_data['count'].fillna(0)

        effort_data['total_clicks'] = effort_data[
            ['disambiguation_count', 'alternate_click_count', 'none_click_count']].sum(axis=1)

        output_notebook(hide_banner=True)

        colors = tuple(
            [(int(255 * (0.1 + 0.7 * (1 - i * 0.2))), int(255 * (0.4 + 0.4 * (1 - i * 0.2))), int(255 * 0.8), 0.8) for i
             in
             range(3)])

        p = figure(plot_width=950, plot_height=350, x_axis_type="datetime",
                   x_range=(start_datetime - start_delta, end_datetime + end_delta),
                   y_range=(0, effort_data['effort_score_sum'].max() * 1.3),
                   title='Customer effort vs clicks over time')
        p.yaxis.axis_label = 'Customer Effort'

        # Setting the second y axis range name and range

        p.extra_y_ranges["clicks"] = Range1d(start=0, end=effort_data['total_clicks'].max() * 1.5)
        p.add_layout(LinearAxis(y_range_name="clicks", axis_label='Number of Clicks'), 'right')

        p.grid.minor_grid_line_color = '#eeeeee'

        names = ['disambiguation_count', 'alternate_click_count', 'none_click_count']
        legend_names = ['Disambiguation', 'More Options', none_above_node_name[0]]
        p.vbar_stack(names, x='request_datetime_interval', color=colors, source=effort_data, width=bar_width,
                     legend_label=legend_names, line_color=None, y_range_name="clicks", hover_fill_color='#1C679A',
                     hover_line_color='#1C679A')
        p.line(x='request_datetime_interval', y='effort_score_sum', source=effort_data, line_width=1.5, color='#D82377',
               legend_label='Total Effort')
        p.circle(x='request_datetime_interval', y='effort_score_sum', source=effort_data, size=5, color="#D82377",
                 alpha=1)

        p.legend.click_policy = "hide"
        p.legend.orientation = "horizontal"

        p.xaxis.formatter = DatetimeTickFormatter(
            seconds=["%Y-%m-%d %H:%M:%S"],
            minsec=["%Y-%m-%d %H:%M:%S"],
            minutes=["%Y-%m-%d %H:%M:%S"],
            hourmin=["%Y-%m-%d %H:%M:%S"],
            hours=["%Y-%m-%d %H:%M:%S"],
            days=["%Y-%m-%d %H:%M:%S"],
            months=["%Y-%m-%d %H:%M:%S"],
            years=["%Y-%m-%d %H:%M:%S"],
        )
        p.xaxis.major_label_orientation = 0.5
        hover = HoverTool(
            tooltips=[
                ("Datetime", "@request_datetime_interval{%Y-%m-%d %H:%M:%S}"),
                ("Disambiguation", "@disambiguation_count"),
                ("More Options", "@alternate_click_count"),
                (none_above_node_name[0], "@none_click_count"),
                ("Total Clicks", "@total_clicks"),
                ("Total Effort", "@effort_score_sum{0}")
            ],
            formatters={
                '@request_datetime_interval': 'datetime'
            },
        )
        p.legend.click_policy = "hide"
        p.legend.orientation = "horizontal"
        p.add_tools(hover)

        p.title.align = 'center'
        p.title.text_font_size = '12pt'
        p.axis.major_label_text_font_size = "10pt"
        p.legend.location = 'top_center'

        toggle = Toggle(label="Auto Learning Applied Period", button_type="default", active=False, align='center')

        if len(time_intervals) > 0:

            for [start_timestamp, end_timestamp] in time_intervals:
                box = BoxAnnotation(left=start_timestamp, right=end_timestamp,
                                    line_width=1, line_color='black', line_dash='dashed',
                                    fill_alpha=0.2, fill_color='orange', visible=False)

                p.add_layout(box)

            select_callback = CustomJS(args=dict(toggle=toggle, box=box), code="""
                    if(toggle.active==true) {
                         box.visible = true
                    } else {
                        box.visible = false
                    }

                """)

            toggle.js_on_change('active', select_callback)

        layout = column(p, toggle)
        show(layout)


def split_tol(test_list, tol):
    last = test_list[0]
    res = [last]
    for ele in test_list:
        if ele - last == tol:
            last = ele
            res = []
            res.append(ele)
        elif ele - last > tol:
            res.append(ele)
            if len(res) > 1:
                yield res
                last = ele
                res = [ele]


def show_effort_over_time(disambiguation_utterances, interval):
    delta = None
    if 'auto_learn_apply' in disambiguation_utterances:
        start_applied_idx = disambiguation_utterances.auto_learn_apply.first_valid_index()
        end_applied_idx = disambiguation_utterances.auto_learn_apply.last_valid_index()
    else:
        start_applied_idx = None
        end_applied_idx = None

    if start_applied_idx is not None and end_applied_idx is not None:
        none_list = disambiguation_utterances[start_applied_idx:end_applied_idx][
            disambiguation_utterances[start_applied_idx:end_applied_idx]['auto_learn_apply'].isnull()].index.tolist()
        none_list.insert(0, start_applied_idx)
        none_list.append(end_applied_idx)
        intervals = list(split_tol(none_list, 1))
        time_intervals = [
            [disambiguation_utterances.iloc[x[0]].request_timestamp,
             disambiguation_utterances.iloc[x[-1]].request_timestamp]
            for x in intervals]
    else:
        time_intervals = list()

    if 'auto_learn_preview' in disambiguation_utterances:
        start_preview_idx = disambiguation_utterances.auto_learn_preview.first_valid_index()
        end_preview_idx = disambiguation_utterances.auto_learn_preview.last_valid_index()
    else:
        start_preview_idx = None
        end_preview_idx = None
    if start_preview_idx is None and end_preview_idx is None:
        preview_data = False
    else:
        preview_data = True

    # start_timestamp = disambiguation_utterances.iloc[start_applied_idx].request_timestamp
    # end_timestamp = disambiguation_utterances.iloc[end_applied_idx].request_timestamp

    if interval == 'minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=d.minute, hour=d.hour) + timedelta(minutes=(d.second // 30)) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=1)

        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=start_timestamp.minute,
                                                             hour=start_timestamp.hour) + timedelta(
                minutes=(start_timestamp.second // 30))
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=end_timestamp.minute,
                                                           hour=end_timestamp.hour) + timedelta(
                minutes=(end_timestamp.second // 30))
    elif interval == '5-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 5) * 5) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=5)
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0,
                                                             hour=start_timestamp.hour) + timedelta(
                minutes=(start_timestamp.minute // 5) * 5)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0,
                                                           hour=end_timestamp.hour) + timedelta(
                minutes=(end_timestamp.minute // 5) * 5)
    elif interval == '15-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 15) * 15) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=15)
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0,
                                                             hour=start_timestamp.hour) + timedelta(
                minutes=(start_timestamp.minute // 15) * 15)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0,
                                                           hour=end_timestamp.hour) + timedelta(
                minutes=(end_timestamp.minute // 15) * 15)
    elif interval == '30-minute':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 30) * 30) for d
            in disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=30)
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0,
                                                             hour=start_timestamp.hour) + timedelta(
                minutes=(start_timestamp.minute // 30) * 30)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0,
                                                           hour=end_timestamp.hour) + timedelta(
                minutes=(end_timestamp.minute // 30) * 30)
    elif interval == 'hour':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(minutes=60)
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0,
                                                             hour=start_timestamp.hour)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0, hour=end_timestamp.hour)
    elif interval == 'day':
        disambiguation_utterances['request_datetime_interval'] = [d.replace(second=0, microsecond=0, minute=0, hour=0)
                                                                  for d in disambiguation_utterances.request_timestamp]
        delta = timedelta(days=1)
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0, hour=0)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0, hour=0)
    elif interval == 'week':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) + timedelta(minutes=(d.day // 7) * 7) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(days=7)
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0, hour=0,
                                                             day=1) + timedelta(
                minutes=(start_timestamp.day // 7) * 7)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0, hour=0,
                                                           day=1) + timedelta(
                minutes=(end_timestamp.day // 7) * 7)
    elif interval == 'month':
        disambiguation_utterances['request_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) for d in
            disambiguation_utterances.request_timestamp]
        delta = timedelta(days=30)
        for idx, [start_timestamp, end_timestamp] in enumerate(time_intervals):
            time_intervals[idx][0] = start_timestamp.replace(second=0, microsecond=0, minute=0, hour=0, day=1)
            time_intervals[idx][1] = end_timestamp.replace(second=0, microsecond=0, minute=0, hour=0, day=1)
    else:
        print(
            'Invalid interval, please choose from {"minute", "5-minute", "15-minute", "30-minute", "hour", "day", "week", "month"}')

    if delta:
        effort_agg = disambiguation_utterances[
            ['request_datetime_interval', 'effort_score', 'preview_effort_score']].groupby(
            ['request_datetime_interval'], as_index=False).agg(
            {'effort_score': ['mean', 'sum', 'count'], 'preview_effort_score': ['mean', 'sum']})

        effort_agg.columns = ['request_datetime_interval', 'effort_score_mean', 'effort_score_sum', 'count',
                              'preview_effort_score_mean', 'preview_effort_score_sum']

        start_datetime = effort_agg.request_datetime_interval.iloc[0]
        end_datetime = effort_agg.request_datetime_interval.iloc[-1]
        if start_datetime == end_datetime:
            start_datetime -= delta
            end_datetime += delta

        time_index_df = pd.DataFrame([dt for dt in datetime_range(start_datetime, end_datetime, delta)],
                                     columns=['request_datetime_interval'])

        effort_data = time_index_df.merge(effort_agg, how='left', on=['request_datetime_interval'])
        effort_data['effort_score_mean'] = effort_data['effort_score_mean'].fillna(0)
        effort_data['effort_score_sum'] = effort_data['effort_score_sum'].fillna(0)
        effort_data['preview_effort_score_mean'] = effort_data['preview_effort_score_mean'].fillna(0)
        effort_data['preview_effort_score_sum'] = effort_data['preview_effort_score_sum'].fillna(0)
        effort_data['count'] = effort_data['count'].fillna(0)

        output_notebook(hide_banner=True)

        p = figure(plot_width=950, plot_height=350, x_axis_type="datetime",
                   x_range=(start_datetime, end_datetime),
                   y_range=(0, effort_data['effort_score_sum'].max() * 1.1), title='Total customer effort over time')
        p.yaxis.axis_label = 'Total Customer Effort'

        p.extra_y_ranges["effort_score_mean"] = Range1d(start=0, end=effort_data['effort_score_mean'].max() * 1.1)

        p.grid.minor_grid_line_color = '#eeeeee'

        actual_line = p.line(x='request_datetime_interval', y='effort_score_sum', legend_label='Total Effort',
                             source=effort_data,
                             line_width=1.5, color='#D82377')
        effort_data['total_color'] = '#D82377'
        effort_data['total_size'] = 5
        effort_data['total_fill_color'] = '#D82377'
        source_actual_circle = ColumnDataSource(effort_data)
        actual_circle = p.circle(x='request_datetime_interval', y='effort_score_sum', legend_label='Total Effort',
                                 source=source_actual_circle, size='total_size', fill_color="total_fill_color",
                                 color='total_color', alpha=1)
        p.add_layout(actual_line)
        p.add_layout(actual_circle)

        preview_line = p.line(x='request_datetime_interval', y='preview_effort_score_sum', line_dash="4 4",
                              legend_label='Total Effort (preview)',
                              source=effort_data,
                              line_width=1.5, color='#878787', visible=preview_data)
        effort_data['preview_total_color'] = '#878787'
        effort_data['preview_total_size'] = 5
        effort_data['preview_total_fill_color'] = '#878787'
        source_circle = ColumnDataSource(effort_data)
        preview_circle = p.circle(x='request_datetime_interval', y='preview_effort_score_sum', source=source_circle,
                                  size='preview_total_size',
                                  line_color="preview_total_color", fill_color="preview_total_fill_color",
                                  legend_label='Total Effort (preview)',
                                  alpha=1, visible=preview_data)
        p.add_layout(preview_line)
        p.add_layout(preview_circle)

        normal_line = p.line(x='request_datetime_interval', y='effort_score_mean', source=effort_data,
                             legend_label='Average Effort',
                             line_width=1.5, color='#4fa8f6', y_range_name="effort_score_mean", visible=False)

        effort_data['normal_mean_color'] = '#4fa8f6'
        effort_data['normal_mean_size'] = 5
        effort_data['normal_mean_fill_color'] = '#4fa8f6'
        normal_source_circle = ColumnDataSource(effort_data)

        normal_circle = p.circle(x='request_datetime_interval', y='effort_score_mean', source=normal_source_circle,
                                 size='normal_mean_size',
                                 legend_label='Average Effort', fill_color="normal_mean_fill_color",
                                 color='normal_mean_color', alpha=1, y_range_name="effort_score_mean", visible=False)
        p.add_layout(normal_line)
        p.add_layout(normal_circle)

        preview_normal_line = p.line(x='request_datetime_interval', y='preview_effort_score_mean',
                                     legend_label='Average Effort (preview)', y_range_name="effort_score_mean",
                                     visible=False, line_dash="4 4", source=effort_data,
                                     line_width=1.5, color='#878787')

        effort_data['preview_mean_color'] = '#878787'
        effort_data['preview_mean_size'] = 5
        effort_data['preview_mean_fill_color'] = '#878787'
        preview_source_circle = ColumnDataSource(effort_data)

        preview_normal_circle = p.circle(x='request_datetime_interval', y='preview_effort_score_mean',
                                         legend_label='Average Effort (preview)', y_range_name="effort_score_mean",
                                         visible=False, source=preview_source_circle, size='preview_mean_size',
                                         fill_color="preview_mean_fill_color",
                                         color='preview_mean_color', alpha=1)
        p.add_layout(preview_normal_line)
        p.add_layout(preview_normal_circle)

        p.xaxis.formatter = DatetimeTickFormatter(
            seconds=["%Y-%m-%d %H:%M:%S"],
            minsec=["%Y-%m-%d %H:%M:%S"],
            minutes=["%Y-%m-%d %H:%M:%S"],
            hourmin=["%Y-%m-%d %H:%M:%S"],
            hours=["%Y-%m-%d %H:%M:%S"],
            days=["%Y-%m-%d %H:%M:%S"],
            months=["%Y-%m-%d %H:%M:%S"],
            years=["%Y-%m-%d %H:%M:%S"],
        )
        p.xaxis.major_label_orientation = 0.5
        hover = HoverTool(
            tooltips=[
                ("Datetime", "@request_datetime_interval{%Y-%m-%d %H:%M:%S}"),
                ("Number of Utterances", "@count{0}"),
                ("Total Effort", "@effort_score_sum{0}"),
                ("Total Effort (preview)", "@preview_effort_score_sum{0}"),
                ("Average Effort", "@effort_score_mean{0}"),
                ("Average Effort (preview)", "@preview_effort_score_mean{0}")
            ],
            formatters={
                '@request_datetime_interval': 'datetime'
            },
        )
        p.add_tools(hover)

        p.title.align = 'center'
        p.title.text_font_size = '12pt'
        p.axis.major_label_text_font_size = "10pt"

        toggle = Toggle(label="Auto Learning Applied Period", button_type="default", active=True, align='center')
        toggle_mean = Toggle(label="Average Customer Effort", button_type="default", active=False, align='center')
        toggle_sum = Toggle(label="Total Customer Effort", button_type="default", active=True, align='center')
        if len(time_intervals) > 0:
            for [start_timestamp, end_timestamp] in time_intervals:
                box = BoxAnnotation(left=start_timestamp, right=end_timestamp,
                                    line_width=1, line_color='black', line_dash='dashed',
                                    fill_alpha=0.2, fill_color='orange', visible=True)
                p.add_layout(box)

            select_callback = CustomJS(args=dict(toggle=toggle, box=box), code="""
                    if(toggle.active==true) {
                         box.visible = true
                    } else {
                        box.visible = false
                    }

                """)
            toggle.js_on_change('active', select_callback)

        total_items = p.legend[0].items[:2]
        avg_items = p.legend[0].items[2:4]
        p.legend[0].items = total_items
        element_dict = dict(legend=p.legend[0], title=p.title, y_axis=p.yaxis[0], y_range=p.y_range,
                            total_range=effort_data['effort_score_sum'].max() * 1.1,
                            normal_range=effort_data['effort_score_mean'].max() * 1.1, total_items=total_items,
                            avg_items=avg_items, toggle_mean=toggle_mean, toggle_sum=toggle_sum,
                            actual_line=actual_line,
                            actual_circle=actual_circle, preview_data=preview_data, preview_line=preview_line,
                            preview_circle=preview_circle,
                            normal_line=normal_line, normal_circle=normal_circle,
                            preview_normal_line=preview_normal_line,
                            preview_normal_circle=preview_normal_circle)
        normalize_callback = CustomJS(args=element_dict, code="""
            if(toggle_mean.active==true) {
                 normal_line.visible = true
                 normal_circle.visible = true
                 actual_line.visible = false
                 actual_circle.visible = false
                 preview_line.visible = false
                 preview_circle.visible = false
                 if (preview_data==true) {
                    preview_normal_line.visible = true
                    preview_normal_circle.visible = true
                 }
                 legend.items = avg_items
                 y_range.end = normal_range
                 y_axis.axis_label='Average Customer Effort'
                 title.text='Average customer effort over time'
                 toggle_sum.active=false

            } else {
                normal_line.visible = false
                normal_circle.visible = false
                actual_line.visible = true
                actual_circle.visible = true
                if (preview_data==true) {
                    preview_line.visible = true
                    preview_circle.visible = true
                }
                preview_normal_line.visible = false
                preview_normal_circle.visible = false
                legend.items = total_items
                y_range.end = total_range
                y_axis.axis_label='Total Customer Effort'
                title.text='Total customer effort over time'
                toggle_sum.active=true
            }
        """)
        normalize_callback_sum = CustomJS(args=element_dict, code="""
            if(toggle_sum.active==true) {
                        normal_line.visible = false
                normal_circle.visible = false
                actual_line.visible = true
                actual_circle.visible = true
                if (preview_data==true) {
                    preview_line.visible = true
                    preview_circle.visible = true
                }
                preview_normal_line.visible = false
                preview_normal_circle.visible = false
                legend.items = total_items
                y_range.end = total_range
                y_axis.axis_label='Total Customer Effort'
                title.text='Total customer effort over time'

                 toggle_mean.active=false

            } else {
                 normal_line.visible = true
                 normal_circle.visible = true
                 actual_line.visible = false
                 actual_circle.visible = false
                 preview_line.visible = false
                 preview_circle.visible = false
                 if (preview_data==true) {
                     preview_normal_line.visible = true
                     preview_normal_circle.visible = true
                 }
                 legend.items = avg_items
                 y_range.end = normal_range
                 y_axis.axis_label='Average Customer Effort'
                 title.text='Average customer effort over time'
                toggle_mean.active=true
            }
        """)
        toggle_mean.js_on_change('active', normalize_callback)
        toggle_sum.js_on_change('active', normalize_callback_sum)
        p.legend.click_policy = "hide"
        p.legend.orientation = "horizontal"
        p.legend.location = 'bottom_right'
        #     table_source = ColumnDataSource(top_confused_pairs)
        effort_data['improve'] = (effort_data['effort_score_mean'] - effort_data['preview_effort_score_mean']) / \
                                 effort_data['effort_score_mean'] * 100
        effort_data['improve'] = effort_data['improve'].fillna(0)

        statistics = {}
        statistics['Number of Intervals'] = len(effort_data['request_datetime_interval'])
        statistics['Average Improving %'] = ["{0:.1f}%".format(effort_data['improve'].mean())]
        statistics['Highest Improving %'] = ["{0:.1f}%".format(effort_data['improve'].max())]
        statistics['Highest Improved Interval'] = [
            str(effort_data.iloc[effort_data['improve'].idxmax()]['request_datetime_interval'].tz_convert(None))]
        statistics['Lowest Improving %'] = ["{0:.1f}%".format(effort_data['improve'].min())]
        statistics['Lowest Improved Interval'] = [
            str(effort_data.iloc[effort_data['improve'].idxmin()]['request_datetime_interval'].tz_convert(None))]

        statistics_pd = pd.DataFrame.from_dict(statistics)
        table_source = ColumnDataSource(statistics_pd)
        columns = [TableColumn(field=Ci, title=Ci) for Ci in statistics_pd.columns]
        data_table = DataTable(source=table_source, columns=columns, height=60, index_position=None)

        detailed_data = effort_data.copy().drop(
            ['preview_total_color', 'preview_total_size', 'preview_total_fill_color', 'normal_mean_color',
             'normal_mean_size', 'normal_mean_fill_color', 'total_color', 'total_size', 'total_fill_color',
             'preview_mean_color', 'preview_mean_size', 'preview_mean_fill_color'], axis=1)
        detailed_data['request_datetime_interval'] = detailed_data['request_datetime_interval'].dt.tz_convert(
            None).apply(
            lambda x: str(x))
        detailed_data['improve'] = detailed_data['improve'].apply(lambda x: "{0:.1f}%".format(x))
        detailed_data['effort_score_sum'] = detailed_data['effort_score_sum'].apply(lambda x: round(x, 0))
        detailed_data['preview_effort_score_sum'] = detailed_data['preview_effort_score_sum'].apply(
            lambda x: round(x, 0))
        detailed_data['effort_score_mean'] = detailed_data['effort_score_mean'].apply(lambda x: "{0:.1f}".format(x))
        detailed_data['preview_effort_score_mean'] = detailed_data['preview_effort_score_mean'].apply(
            lambda x: "{0:.1f}".format(x))

        detailed_data.columns = ['Time Interval', 'Average Effort', 'Total Effort', 'Number of Utterances',
                                 'Average Effort (preview)',
                                 'Total Effort (preview)', 'Improving %']

        detailed_data_source = ColumnDataSource(detailed_data)
        detailed_columns = [TableColumn(field=Ci, title=Ci) for Ci in detailed_data.columns]
        detailed_data_table = DataTable(source=detailed_data_source, columns=detailed_columns, height=200,
                                        index_position=None)

        # actual_circle.glyph.to_json_string(True)

        callback_test = CustomJS(
            args=dict(title=p.title, source1=detailed_data_source, circle=source_circle, circle1=normal_source_circle,
                      circle2=source_actual_circle, circle3=preview_source_circle), code="""
                const d = circle.data;
                const n = circle1.data;
                const a = circle2.data;
                const p = circle3.data;

                for (var i = 0; i < d['preview_total_size'].length; i++) {
                    if (i == source1.selected['indices'][0]) {
                        d['preview_total_size'][i] = 15
                        d['preview_total_color'][i] = '#878787'
                        d['preview_total_fill_color'][i] = '#878787'
                    } else {
                        d['preview_total_size'][i] = 5
                        d['preview_total_color'][i] = '#878787'
                        d['preview_total_fill_color'][i] = '#878787'
                    }                
                }

                for (var i = 0; i < n['normal_mean_size'].length; i++) {
                    if (i == source1.selected['indices'][0]) {
                        n['normal_mean_size'][i] = 15
                    } else {
                        n['normal_mean_size'][i] = 5
                    }                
                }
                for (var i = 0; i < a['total_size'].length; i++) {
                    if (i == source1.selected['indices'][0]) {
                        a['total_size'][i] = 15
                    } else {
                        a['total_size'][i] = 5
                    }                
                }
                for (var i = 0; i < p['preview_mean_size'].length; i++) {
                    if (i == source1.selected['indices'][0]) {
                        p['preview_mean_size'][i] = 15
                    } else {
                        p['preview_mean_size'][i] = 5
                    }                
                }
                circle.change.emit();
                circle1.change.emit();
                circle2.change.emit();
                circle3.change.emit();
        """)

        detailed_data_source.selected.js_on_change('indices', callback_test)

        layout = column(p, row(toggle_sum, toggle_mean, toggle, sizing_mode="stretch_width"),
                        row(data_table, sizing_mode="stretch_width"),
                        row(detailed_data_table, sizing_mode="stretch_width"))
        show(layout)