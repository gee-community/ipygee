"""Decorators used in ipygee.

ported from https://github.com/12rambau/sepal_ui/blob/main/sepal_ui/scripts/decorator.py
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Optional


def switch(*params, member: Optional[str] = None, debug: bool = True) -> Any:
    r"""Decorator to switch the state of input boolean parameters on class widgets or the class itself.

    If ``widget`` is defined, it will switch the state of every widget parameter, otherwise
    it will change the state of the class (self). You can also set two decorators on the same
    function, one could affect the class and other the widget.

    Args:
        *params: any boolean member of a Widget.
        member: THe widget on which the member are switched. Default to self.
        debug: Whether trigger or not an Exception if the decorated function fails.

    Returns:
        The return statement of the decorated method
    """

    def decorator_switch(func):
        @wraps(func)
        def wrapper_switch(self, *args, **kwargs):
            # set the widget to work with. if nothing is set it will be self
            widget = getattr(self, member) if member else self

            # create the list of target values based on the initial values
            targets = [bool(getattr(widget, p)) for p in params]
            not_targets = [not t for t in targets]

            # assgn the parameters to the target inverse
            [setattr(widget, p, t) for p, t in zip(params, not_targets)]

            # execute the function and catch errors
            try:
                func(self, *args, **kwargs)
            except Exception as e:
                if debug:
                    raise e
            finally:
                [setattr(widget, p, t) for p, t in zip(params, targets)]

        return wrapper_switch

    return decorator_switch
