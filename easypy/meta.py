from abc import ABCMeta
from functools import wraps
from collections import OrderedDict

from .decorations import kwargs_resilient, as_list


class EasyMeta(ABCMeta):
    """
    Base class for various meta-magic mixins.

    Use the hooks in :class:`EasyMetaHooks`, decorated with `@EasyMeta.Hook`,
    to add functionality. Multiple hooks with the same name can be defined,
    and they will all be invoked sequentially.
    """

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        dsl = EasyMetaDslDict()
        return dsl

    class Hook(object):
        def __init__(self, dlg):
            self.dlg = dlg

    def __init__(cls, name, bases, dct, **kwargs):
        super().__init__(name, bases, dct)

    def __new__(mcs, name, bases, dct, **kwargs):
        hooks = EasyMetaHooks(class_kwargs=kwargs)

        for base in bases:
            if isinstance(base, EasyMeta):
                hooks.extend(base._em_hooks)

        new_type = super().__new__(mcs, name, bases, dct)

        new_type._em_hooks = hooks

        hooks.after_subclass_init(new_type)

        hooks.extend(dct.hooks)

        return new_type


class EasyMetaHooks:
    """
    Hooks for ``EasyMeta``
    """

    HOOK_NAMES = []

    def hook(dlg, HOOK_NAMES=HOOK_NAMES):
        HOOK_NAMES.append(dlg.__name__)

        @wraps(dlg)
        def hook(self, *args, **kwargs):
            kwargs_resilience = kwargs_resilient(negligible=self.class_kwargs.keys())
            kwargs.update((k, v) for k, v in self.class_kwargs.items() if k not in kwargs)

            for hook in self.hooks[dlg.__name__]:
                kwargs_resilience(hook)(*args, **kwargs)

        return hook

    def __init__(self, class_kwargs={}):
        self.hooks = {name: [] for name in self.HOOK_NAMES}
        self.class_kwargs = class_kwargs

    def add(self, hook):
        self.hooks[hook.__name__].append(hook)

    def extend(self, other):
        for k, v in other.hooks.items():
            self.hooks[k].extend(v)

    @hook
    def after_subclass_init(self, cls):
        """
        Invoked after a subclass is being initialized

        >>> class PrintTheName(metaclass=EasyMeta):
        >>>     @EasyMeta.Hook
        >>>     def after_subclass_init(cls):
        >>>         print('Declared', cls.__name__)
        >>>
        >>>
        >>> class Foo(PrintTheName):
        >>>     pass
        Declared Foo
        """


class EasyMetaDslDict(OrderedDict):
    def __init__(self):
        super().__init__()
        self.hooks = EasyMetaHooks()

    def __setitem__(self, name, value):
        if isinstance(value, EasyMeta.Hook):
            self.hooks.add(value.dlg)
        else:
            return super().__setitem__(name, value)


class GetAllSubclasses(metaclass=EasyMeta):
    """
    Meta-magic mixin for registering subclasses

    The ``get_all_subclasses`` class method will return a list of all subclasses
    of the class it was called on. The class it was called on is not included in
    the list.

    >>> class Foo(GetAllSubclasses):
    >>>     pass
    >>>
    >>>
    >>> class Bar(Foo):
    >>>     pass
    >>>
    >>>
    >>> class Baz(Foo):
    >>>     pass
    >>>
    >>>
    >>> class Qux(Bar):
    >>>     pass
    >>>
    >>>
    >>> Foo.get_all_subclasses()
    [Bar, Qux, Baz]
    >>> Bar.get_all_subclasses()
    [Qux]
    >>> Baz.get_all_subclasses()
    []
    >>> Qux.get_all_subclasses()
    []
    """

    @EasyMeta.Hook
    def after_subclass_init(cls):
        cls.__direct_subclasses = []
        for base in cls.__bases__:
            if base is not GetAllSubclasses and issubclass(base, GetAllSubclasses):
                base.__direct_subclasses.append(cls)

    @classmethod
    @as_list
    def get_all_subclasses(cls):
        """
        List all subclasses of this class
        """
        for subclass in cls.__direct_subclasses:
            yield subclass
            yield from subclass.__direct_subclasses
