from typing import Callable, Dict, TypeVar, Type, cast, Any

T = TypeVar("T")

class DIContainer:
    """
    Simple DI container that supports:
      - Registering instances (singletons)
      - Registering factories (Callable[..., T])
      - Resolving singletons or new instances with optional *args/**kwargs
      - Direct construction fallback if no factory is registered
    """
    def __init__(self):
        self._services: Dict[Type[Any], Callable[..., Any]] = {}
        self._instances: Dict[Type[Any], Any] = {}

    def register_factory(self, cls: Type[T], factory: Callable[[], T]):
        """
        Register a factory for cls. The factory may accept *args/**kwargs
        which will be forwarded from resolve_*.
        """
        self._services[cls] = factory

    def register_instance(self, cls: Type[T], instance: T):
        """
        Register an already-constructed singleton instance for cls.
        """
        self._instances[cls] = instance

    def resolve_singleton(self, cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """
        Resolve a singleton instance of cls.
        - If not created yet:
            * If a factory is registered, call it with *args/**kwargs.
            * Else, attempt to construct cls(*args, **kwargs).
        - If already created, ignore any *args/**kwargs and return existing.
        """
        if cls not in self._instances:
            if cls in self._services:
                self._instances[cls] = self._services[cls](*args, **kwargs)
            else:
                # Fallback: try constructing directly
                self._instances[cls] = cls(*args, **kwargs)
        return cast(T, self._instances[cls])

    def resolve_new(self, cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """
        Always return a new instance of cls.
        - If a factory is registered, call it with *args/**kwargs.
        - Else, construct cls(*args, **kwargs).
        """
        if cls in self._services:
            self._services[cls](*args, **kwargs)
        return self.resolve_singleton(cls, *args, **kwargs)

        # Optional convenience: single entry point with scope flag
    def resolve(self, cls: Type[T], *args: Any, singleton: bool = True, **kwargs: Any) -> T:
        """
        Convenience wrapper:
            resolve(MyType, a, b, singleton=True) -> singleton
            resolve(MyType, a, b, singleton=False) -> new instance
        """
        if singleton:
            return self.resolve_singleton(cls, *args, **kwargs)
        return self.resolve_new(cls, *args, **kwargs)

    def reset(self):
        self._services.clear()
        self._instances.clear()

    def reset_instance(self, cls: Type[T]) -> None:
        """Remove the cached singleton for cls (keeps the factory)."""
        self._instances.pop(cls, None)

# Global container
container = DIContainer()
