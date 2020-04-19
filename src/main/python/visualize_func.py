import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from io import BytesIO
import sys
import base64
import decimal
from bokeh.io import show, output_notebook
from bokeh.plotting import figure
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models import HoverTool
from datetime import date, datetime, timedelta
import pandas as pd


# Set CSS properties for th elements in dataframe
th_props = [
    ('font-size', '15px'),
    ('text-align', 'center'),
    ('font-weight', 'bold'),
    ('color', '#000'),
    ('font-family', 'Verdana'),
    ('background-color', '#f7f7f7'),
    ('padding', '12px'),
    ('border-top', '1px solid #636363'),
    ('border-bottom', '1px solid #636363'),
    ('border-left', '1px solid #636363'),
    ('border-right', '1px solid #636363')
]

# Set CSS properties for td elements in dataframe
td_props = [
    ('font-size', '14px'),
    ('color', '#2d2d2d'),
    ('font-family', 'Verdana'),
    ('background-color', '#fff'),
    ('padding', '10px'),
    ('border-top', '1px solid #636363'),
    ('border-bottom', '1px solid #636363'),
    ('border-left', '1px solid #636363'),
    ('border-right', '1px solid #636363')
]

# Set table styles
table_styles = [
    dict(selector="th", props=th_props),
    dict(selector="td", props=td_props),
    dict(selector=".row_heading", props=[('display', 'none')]),
    dict(selector=".blank.level0", props=[('display', 'none')]),
    dict(selector="th:first-child ", props=[('display', 'none')])
]


def make_cmap(colors, position=None, bit=False):
    """This function generates a linear segmented colormap given a list of color values
       Parameters
       ----------
       colors: a list of RGB color values.
       position: color changing position.
       bit: bit value.
    """
    bit_rgb = np.linspace(0, 1, 256)
    if position is None:
        position = np.linspace(0, 1, len(colors))
    else:
        if len(position) != len(colors):
            sys.exit("position length must be the same as colors")
        elif position[0] != 0 or position[-1] != 1:
            sys.exit("position must start with 0 and end with 1")
    if bit:
        for i in range(len(colors)):
            colors[i] = (bit_rgb[colors[i][0]],
                         bit_rgb[colors[i][1]],
                         bit_rgb[colors[i][2]])
    cdict = {'red': [], 'green': [], 'blue': []}
    for pos, color in zip(position, colors):
        cdict['red'].append((pos, color[0], color[0]))
        cdict['green'].append((pos, color[1], color[1]))
        cdict['blue'].append((pos, color[2], color[2]))

    cmap = mpl.colors.LinearSegmentedColormap('my_colormap', cdict, 256)
    return cmap


def gbar(ax, x, y, cmap, width=0.5, bottom=5):
    """Generate gradient colored bars
       Parameters
       ----------
       ax: axis
       x: x value
       y: y value
       cmap: color map
       width: width
       bottom: bottom position
    """
    data = [[.6, .6], [.7, .7]]
    for left, top in zip(x, y):
        right = left + width
        ax.imshow(data, interpolation='bicubic', cmap=cmap,
                  extent=(left, right, bottom, top), alpha=1)


def make_bar(prec, helpful, var_prec, var_help):
    """Generate bar plots for precision and helpfulness with variances
       Parameters
       ----------
       prec: precision.
       helpful: helpfulness.
       var_prec: precision variances.
       var_help: helpfulness variances.
    """
    colors = [(143, 202, 244), (68, 114, 176)]
    my_cmap = make_cmap(colors, bit=True)
    xlim = 0, 2
    ylim = 0, 100

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set(xlim=xlim, ylim=ylim, autoscale_on=False)
    n = 2
    x = np.arange(n) + 0.2
    y = [prec, helpful]
    gbar(ax, x, y, width=0.6, cmap=my_cmap)
    ax.set_aspect(0.02)

    t = np.arange(n) + 0.5
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_color('#808080')
    ax.spines['bottom'].set_color('#808080')

    plt.tick_params(
        axis='x',  # changes apply to the x-axis
        which='both',  # both major and minor ticks are affected
        bottom=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        labelbottom=False)  # labels along the bottom edge are off
    plt.tick_params(
        axis='y',  # changes apply to the x-axis
        which='both',  # both major and minor ticks are affected
        bottom=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        labelbottom=False,
        labelsize=15)  # labels along the bottom edge are off
    ax.set_yticks(np.arange(5, 110, 20))
    ax.set_yticklabels(np.arange(0, 110, 20), color='#333333')
    ax.errorbar(t, y, xerr=0, yerr=[var_prec, var_help], linestyle='none', color='red')
    y_prec_position = 20 if prec > 35 else prec + 10
    y_helpful_position = 20 if helpful > 35 else helpful + 10
    ax.text(0.5, y_prec_position, round_decimal(prec), color='white' if prec > 35 else 'black', ha='center',
            va='center', fontsize=30)
    ax.text(1.5, y_helpful_position, round_decimal(helpful), color='white' if helpful > 35 else 'black', ha='center',
            va='center', fontsize=30)
    ax.text(0.5, -10, '±{0}'.format(round_decimal(var_prec, 1)), color='black', ha='center', va='center', fontsize=20)
    ax.text(1.5, -10, '±{0}'.format(round_decimal(var_help, 1)), color='black', ha='center', va='center', fontsize=20)
    ax.text(1.5, 113, 'Helpfulness', color='black', ha='center', va='center', fontsize=18)
    ax.text(0.5, 113, 'Precision', color='black', ha='center', va='center', fontsize=18)
    plt.title("\n\n\n")
    plt.show()


#################################
# Functions from Measure notebook                  
#################################


def render_fig(fig):
    """This function returns the HTML rendering of a matplotlib figure. 
       Parameters
       ----------
       fig : input figure

       Returns
       ----------
       html : HTML rendering of figure
    """
    tmpfile = BytesIO()
    # save figure 
    fig.savefig(tmpfile, format='jpeg')
    # encode the saved figure
    encoded = base64.b64encode(tmpfile.getvalue())
    # Store html rendering of figure in string html
    html = '<img class="colimg" src=\'data:image/png;base64,{}\'>'.format(encoded.decode("utf-8"))
    return html


def make_pie(prec, msg, html=True):
    """This function plots a pie chart to represent the input percentage. 
       Parameters
       ----------
       prec : float effectiveness or coverage value, e.g. 82.71
       msg: string label of graph
       html: boolean to specify if html rendering of figure is to be returned, default = True

       Returns
       ----------
       fig : matplotlib figure if html==False, html rendering of figure otherwise
    """
    # colors for pie chart
    c1 = '#69aaf5'
    c2 = '#c0c8d2'

    fig, ax = plt.subplots()
    ax.axis('equal')
    width = 0.2
    kwargs = dict(colors=[c1, c2], startangle=90, counterclock=False)
    outside, _ = ax.pie([prec, 100 - prec], radius=1, pctdistance=1 - width / 2, **kwargs)
    plt.setp(outside, width=width, edgecolor='white')
    kwargs = dict(size=50, fontweight='normal', va='center', color='#000000')
    ax.text(0, 0, "{:.0f}%".format(prec), ha='center', **kwargs)
    ax.set_xlabel(msg, size='xx-large')
    plt.close()
    # return html rendering of figure if html = True
    if html:
        return render_fig(fig)
    else:
        return fig


def coverage_barh(coverage, avg_conf, title, html=True, width=15, height=1.5):
    """This function plots a bar graph to represent the input percentage. 
       Parameters
       ----------
       coverage : float coverage value, e.g. 82.71
       avg_conf: float average confidence, e.g. 82.71
       title: string title of the plot
       html: boolean to specify if html rendering of figure is to be returned, default = True
       width: int, width of figure, default = 15
       height: float, height of figure, default = 1.5

       Returns
       ----------
       fig : matplotlib figure if html==False, html rendering of figure otherwise
    """
    # Get coverage and non-coverage
    bottomdata = coverage
    topdata = float("{0:.2f}".format(100 - coverage))
    fig, ax = plt.subplots(figsize=(width, height))
    ax.axis('on')
    # Plot the 'Covered' bar
    ax.barh(0, bottomdata, left=0, color='#69aaf5', align='center', label='Covered ' + str(bottomdata) + '%',
            edgecolor=None)
    ax.set_title(title, fontdict={'fontsize': 15}, loc='left', weight='bold', y=0.91)
    # Plot the 'Not covered' bar stacked on top of 'Covered' bar
    ax.barh(0, topdata, left=bottomdata, color='#2b6ab6', align='center', label='Not covered ' + str(topdata) + '%',
            edgecolor=None)
    # Add labels for coverage and average confidence
    labels = ['Covered ' + str(bottomdata) + '% | Average confidence ' + str(avg_conf) + '%',
              'Not Covered ' + str(topdata) + '%']
    # props = dict(boxstyle='round', facecolor='wheat', alpha=0)
    # Center plot at 0,0
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=0)
    ax.set_yticks([])
    # Add coverage and average confidence info. to plot
    plt.xticks([0, bottomdata], labels, size=13)
    # Hide the spines
    ax.set_frame_on(False)
    # removing the tick marks
    plt.tick_params(bottom=False, left=False)
    fig.tight_layout()
    plt.close()
    # return html rendering of figure if html = True
    if html:
        return render_fig(fig)
    else:
        return fig


def width_bar(perc):
    """This function returns the width of the bar graph. 
       Parameters
       ----------
       perc : float coverage value, e.g. 82.71
       
       Returns
       ----------
       width : float width of graph, eg: 4.5
    """
    # Return a proportionate value of the input percentage
    width = perc / 20
    # Default width to 1.5
    if width < 1:
        width = 1.5
    return width


def round_decimal(x, digits=0):
    x = decimal.Decimal(str(x))
    if digits == 0:
        return int(x.quantize(decimal.Decimal("1"), rounding='ROUND_HALF_UP'))
    if digits > 1:
        string = '1e' + str(-1 * digits)
    else:
        string = '1e' + str(-1 * digits)
    return float(x.quantize(decimal.Decimal(string), rounding='ROUND_HALF_UP'))


def datetime_range(start, end, delta):
    current = start
    while current <= end:
        yield current
        current += delta


def show_coverage_over_time(df_coverage, interval='day'):
    delta = None
    if interval == 'minute':
        df_coverage['response_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=d.minute, hour=d.hour) + timedelta(minutes=(d.second // 30)) for d
            in df_coverage['response.timestamp']]
        delta = timedelta(minutes=1)
    elif interval == '5-minute':
        df_coverage['response_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 5) * 5) for d in
            df_coverage['response.timestamp']]
        delta = timedelta(minutes=5)
    elif interval == '15-minute':
        df_coverage['response_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 15) * 15) for d in
            df_coverage['response.timestamp']]
        delta = timedelta(minutes=15)
    elif interval == '30-minute':
        df_coverage['response_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) + timedelta(minutes=(d.minute // 30) * 30) for d
            in df_coverage['response.timestamp']]
        delta = timedelta(minutes=30)
    elif interval == 'hour':
        df_coverage['response_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=d.hour) for d in
            df_coverage['response.timestamp']]
        delta = timedelta(minutes=60)
    elif interval == 'day':
        df_coverage['response_datetime_interval'] = [d.replace(second=0, microsecond=0, minute=0, hour=0)
                                                     for d in df_coverage['response.timestamp']]
        delta = timedelta(days=0.5)
    elif interval == 'week':
        df_coverage['response_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) + timedelta(minutes=(d.day // 7) * 7) for d in
            df_coverage['response.timestamp']]
        delta = timedelta(days=1)
    elif interval == 'month':
        df_coverage['response_datetime_interval'] = [
            d.replace(second=0, microsecond=0, minute=0, hour=0, day=1) for d in
            df_coverage['response.timestamp']]
        delta = timedelta(days=15)
    else:
        print('Invalid interval, please choose from {"minute", "5-minute", "15-minute", "30-minute", "hour", "day", "week", "month"}')

    if delta:
        covered_counts = df_coverage[['response_datetime_interval', 'Covered']].groupby(
            ['response_datetime_interval', 'Covered']).agg({'Covered': 'count'})
        coverage_grp = covered_counts.groupby(level=0).apply(lambda x: round(100 * x / float(x.sum()), 2)).rename(
            columns={'Covered': 'Coverage'}).reset_index()
        covered_counts.columns = ['Count']
        covered_counts = covered_counts.reset_index()
        coverage_grp = coverage_grp.merge(covered_counts, how='left', on=['response_datetime_interval', 'Covered'])
        coverage_time = coverage_grp[coverage_grp['Covered']==True].reset_index(drop=True)

        start_datetime = coverage_time.response_datetime_interval.iloc[0]
        end_datetime = coverage_time.response_datetime_interval.iloc[-1]
        if start_datetime == end_datetime:
            start_datetime -= delta
            end_datetime += delta

        time_index_df = pd.DataFrame([dt for dt in datetime_range(start_datetime, end_datetime, delta)],
                                     columns=['response_datetime_interval'])

        coverage_data = time_index_df.merge(coverage_time, how='left', on=['response_datetime_interval'])
        coverage_data['Count'] = coverage_data['Count'].fillna(0)
        coverage_data['Coverage'] = coverage_data['Coverage'].fillna(0)

        output_notebook(hide_banner=True)

        p = figure(plot_width=950, plot_height=350, x_axis_type="datetime",
                   x_range=(start_datetime, end_datetime),
                   y_range=(0, 100), title='Coverage over time')

        p.line(x='response_datetime_interval', y='Coverage', source=coverage_data, line_width=1.5, color='#4fa8f6')

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
        p.yaxis.axis_label = 'Coverage %'

        hover = HoverTool(
            tooltips=[
                ("Datetime", "@response_datetime_interval{%Y-%m-%d %H:%M:%S}"),
                ("Count", "@Count"),
                ("Coverage", "@Coverage{0.00}%")
            ],
            formatters={
                '@response_datetime_interval': 'datetime'
            },
        )
        p.add_tools(hover)
        p.title.align = 'center'
        p.title.text_font_size = '12pt'
        p.axis.major_label_text_font_size = "10pt"
        show(p)
