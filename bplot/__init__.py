from .b_risk_results import b_risk_results, _get_mpl_plt



class style:
    def __init__(self, line, text, text_y, arrow_y):
        """
        A Style stores default properties for lines and text add the figures.

        Args:
            line (dict): dict of kwargs for matplotlib lines
            text (dict): dict of kwargs for matplotlib text
            text_y (float): relative position of the text (0 is bottom of axes, 1 is the top of axes)
            arrow_y (float): relative position of the double sided arrows and text used to mark span (0 is bottom of axes, 1 is the top of axes)
        """
        self.line = line
        self.text = text
        self.text_y = text_y
        self.arrow_y = arrow_y

event_style = style({'linewidth':1, 'linestyle':'dotted', 'color':'gray', 'alpha':0.7},
                     {'fontsize':6},
                     text_y = 1.02,
                     arrow_y=1.15)

tenability_style = style({'linewidth':3, 'linestyle':'solid', 'color':'red', 'alpha':0.3},
                     {}, # No texty supported for tenability
                     text_y = 0,
                     arrow_y=None) # no arrows

user_style = style({'linewidth':2, 'linestyle':'dashed', 'color':'lightblue', 'alpha':1.0},
                     {'fontsize':6},
                     text_y = 1.02,
                     arrow_y=None) # no arrows


def add_event_vline(ax, time, **kwargs):
    """
    Add a vertical line with the event style properties to the axes. 

    Args:
        ax (axes): matplotlib axes to add line to
        time (int or float): time which line marks
        kwargs: passed to matplotlib axvline function
    """
    kwargs = event_style.line | kwargs
    ax.axvline(x=time,
                **kwargs)

def add_user_vline(ax, time, **kwargs):
    """
    Add a vertical line with the user style properties to the axes. 

    Args:
        ax (axes): matplotlib axes to add line to
        time (int or float): time which line marks
        kwargs: passed to matplotlib axvline function
    """
    kwargs = user_style.line | kwargs
    ax.axvline(x=time, 
                **kwargs)

def add_tenability_hline(ax, y, **kwargs):
    """
    Add a horizontal line with the tenability style properties to the axes.

    Args:
        ax (axes): matplotlib axes to add line to
        y (int or float): value on  y axis marked by line
        kwargs: passed to matplotlib axhline function
    """
    kwargs = tenability_style.line | kwargs
    ax.axhline(y=y,
                **kwargs)

def add_Htext(ax, time, text, text_y=1.03, **kwargs):
    """
    Add horizontal text to a chart.
    Use 'horizontalalignment' keyword to set horizontal alignment: 'left', 'center' or 'right'

    Args:
        ax (axes): matplotlib axes to add text to
        time (int or float): Time at which text is added (centered by default)
        text (string): text to add
        text_y (float, optional): relative vertical position of text. Defaults to 1.03.
        kwargs: passed to matplotlib text function
    """
    kwargs = {'horizontalalignment': 'center'} | kwargs # set centre by default
    ax.text(time, ax.get_ylim()[1]*text_y,
            text,
            **kwargs)

def add_Vtext(ax, time, text, text_y, **kwargs):
    """
    Add vertical text to a chart.
    Use 'verticalalignment' keyword to set vertical alignment: 'top', 'center' or 'bottom'

    Args:
        ax (axes): matpltolib axes to add text to
        time (int or float): Time at which text is added (centered by default)
        text (string): text to add
        text_y (float): relative vertical position of text
        kwargs: passed to matplotlib text function
    """
    # Adds vertical text, with automatic background
    kwargs = {'horizontalalignment': 'center'} | kwargs # set centre by default

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

def add_event_text(ax, time, text, text_y=None, **kwargs):
    """
    Add horizontal text with the event style to a chart.

    Args:
        ax (axes): matplotlib axes to add text to
        time (int or float): Time at which text is added (centered by default)
        text (string): text to add
        text_y (_type_, optional): relative vertical position of text. Defaults to event style value.
        kwargs: passed to the matplotlib text function
    """
    kwargs = event_style.text | kwargs
    if text_y is None: text_y = event_style.text_y
    add_Htext(ax, time, text, 
                text_y=text_y, 
                **kwargs)

def add_user_text(ax, time, text, text_y=None, **kwargs):
    """
    Add horizontal text with the user style to a chart.

    Args:
        ax (axes): matplotlib axes to add text to
        time (int or float): Time at which text is added (centered by default)
        text (string): text to add
        text_y (_type_, optional): relative vertical position of text. Defaults to user style value.
        kwargs: passed to the matplotlib text function
    """
    kwargs = user_style.text | kwargs
    if text_y is None: text_y = user_style.text_y
    add_Htext(ax, time, text, 
                text_y=text_y, 
                **kwargs)


def add_user_vline_text(ax, time, text, **kwargs):
    """
    Add a vertical line and text to a chart. Both line and text are styled according to the user style.

    Args:
        ax (axes): matplotlib axes to add text to
        time (int or float): Time at which text is added (centered by default)
        text (string): text to add
        kwargs: passed to the matplotlib text function.
    """
    add_user_vline(ax, time, )
    add_user_text(ax, time, text, **kwargs)

def add_user_line_texts(ax, lines_texts):
    """
    Adds multiple vertical line and text to a chart. Both line and text are styled according to the user style.

    Args:
        ax (axes): matplotlib axes to add text to
        lines_texts (list of tuples): list of tuples. Each tuple has two elements, first is the time and second is the label text.
    """
    for lt in lines_texts:
        add_user_vline_text(ax, lt[0], lt[1])
  

def add_span_text(ax, x1, x2, text, **kwargs):
    """
    Add a horizontal line (with arrows at each end) and with text above. Formatted according to the event style.

    Args:
        ax (axes): matplotlib axes to add text to
        x1 (int or float): span begins at this time (start arrow location)
        x2 (int or float): span ends at this time (end arrow location)
        text (string): text to add
        kwargs: text options
    """
    _xmax = ax.get_xlim()[1]
    ax.annotate('', (x1/_xmax, event_style.arrow_y), (x2/_xmax, event_style.arrow_y),
                xycoords='axes fraction',
                arrowprops=dict(arrowstyle='<->'))
    kwargs = {'backgroundcolor': ax.get_facecolor(), 'horizontalalignment': 'center'} | kwargs # set opqaue background by default
    kwargs = event_style.text | kwargs
    add_event_text(ax, 0.5*(x1+x2), text, 
                    text_y=event_style.arrow_y, # text height is modified to the arrow height
                    **kwargs)
