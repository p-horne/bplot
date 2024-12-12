
class style:
    def __init__(self, line, text, text_y, text_rotation, arrow_y):
        # line is a dict of kwargs for lines fopr matplotlib
        # test is a dict of kwargs for text for matplotlib
        # text rotation is 'horizontal' or vertical'
        # text y is the position of the textbox (float) if it is < 0.5, then vertical text is positioned at bottom), 
        # if it is > 0.5  then vertical text is positioned at the top
        # if it horizontal text then this y value is used (as fraction of axes)
        # arrow_y is the height of double sided arros to be added
        self.line = line
        self.text = text
        self.text_y = text_y
        self.text_rotation = text_rotation
        self.arrow_y = arrow_y

event_style = style({'linewidth':1, 'linestyle':'dashed', 'color':'gray', 'alpha':0.5},
                     {'fontsize':6},
                     text_y = 1.02,
                     text_rotation = 'horizontal',
                     arrow_y=1.15)

tenability_style = style({'linewidth':1, 'linestyle':'dashed', 'color':'red', 'alpha':0.5},
                     {}, # No texty supported for tenability
                     text_y = 0,
                     text_rotation = '',
                     arrow_y=None) # no arrows

user_style = style({'linewidth':1, 'linestyle':'dashed', 'color':'lightblue', 'alpha':1.0},
                     {'fontsize':6},
                     text_y = 1.02,
                     text_rotation = 'horizontal',
                     arrow_y=None) # no arrows


def add_event_vline(ax, time, **kwargs):
    kwargs = event_style.line | kwargs
    ax.axvline(x=time,
                **kwargs)

def add_user_vline(ax, time, **kwargs):
    kwargs = user_style.line | kwargs
    ax.axvline(x=time, 
                **kwargs)

def add_tenability_hline(ax, y, **kwargs):
    kwargs = tenability_style.line | kwargs
    ax.axhline(y=y,
                **kwargs)

def add_span_text(ax, x1, x2, text, **kwargs):
    _xmax = ax.get_xlim()[1]
    ax.annotate('', (x1/_xmax, event_style.arrow_y), (x2/_xmax, event_style.arrow_y),
                xycoords='axes fraction',
                arrowprops=dict(arrowstyle='<->'))
    add_user_text(ax, 0.5*(x1+x2), text, 
                    text_y=event_style.arrow_y, 
                    rotation='horizontal',
                    backgroundcolor=ax.get_facecolor(),
                    verticalalignment='center')

def add_Htext(ax, time, text, text_y=1.03, **kwargs):
    # Adds Horizontal Text
    # use horizontalalignment to set: 'left', 'center' or 'right'
    kwargs = {'horizontalalignment': 'center'} | kwargs # set centre by default
    ax.text(time, ax.get_ylim()[1]*text_y,
            text,
            **kwargs)

def add_Vtext(ax, time, text, text_y, **kwargs):
    # Adds vertical text, with automatic background
    kwargs = {'horizontalalignment': 'center'} | kwargs

    if 'verticalalignment' not in kwargs.keys():
        if text_y < 0.05:
            kwargs['verticalalignment']='bottom'
            text_y = 0.02
        elif text_y > 0.95:
            kwargs['verticalalignment']='top'
            text_y = 0.98
        else:
            kwargs['verticalalignment']='center'

    ax.text(time, ax.get_ylim()[1]*text_y, text,
            rotation='vertical',
            backgroundcolor=ax.get_facecolor(),
            **kwargs)


def add_event_text(ax, time, text, text_y=None, rotation=None, **kwargs):
    kwargs = event_style.text | kwargs
    if text_y is None: text_y = event_style.text_y
    if rotation is None: rotation = event_style.text_rotation
    if rotation == 'horizontal':
        add_Htext(ax, time, text, 
                  text_y=text_y, 
                  **kwargs)
    elif rotation == 'vertical':
        add_Vtext(ax, time, text,
                  text_y=text_y,
                  **kwargs)
    else:
        raise Exception('invalid text orientation')

def add_user_text(ax, time, text, text_y=None, rotation=None, **kwargs):
    kwargs = user_style.text | kwargs
    if text_y is None: text_y = user_style.text_y
    if rotation is None: rotation = user_style.text_rotation
    if rotation == 'horizontal':
        add_Htext(ax, time, text, 
                  text_y=text_y, 
                  **kwargs)
    elif rotation == 'vertical':
        add_Vtext(ax, time, text,
                  text_y=text_y,
                  **kwargs)
    else:
        raise Exception('invalid text orientation')


def add_user_vline_text(ax, time, text, **kwargs):
    add_user_vline(ax, time, )
    add_user_text(ax, time, text, **kwargs)


def add_user_vline_texts(ax, lines_texts):
    # lines_texts is a list of list (or tuples), each inner list has two items. 
    # The first is the time and the second is the label text.
    for lt in lines_texts:
        add_user_vline_text(ax, lt[0], lt[1])

