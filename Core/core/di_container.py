# core/di_container.py

from typing import Callable, Dict, TypeVar, Type, cast, Any

T = TypeVar("T")

class DIContainer:
    def __init__(self):
        self._services: Dict[Type[Any], Callable[[], Any]] = {}
        self._instances: Dict[Type[Any], Any] = {}

    def register_singleton(self, cls: Type[T], factory: Callable[[], T]):
        self._services[cls] = factory

    def register_instance(self, cls: Type[T], instance: T):
        self._instances[cls] = instance

    def resolve(self, cls: Type[T]) -> T:
        if cls not in self._instances:
            if cls not in self._services:
                raise KeyError(f"Service '{cls.__name__}' is not registered")
            self._instances[cls] = self._services[cls]()
        return cast(T, self._instances[cls])

    def reset(self):
        self._services.clear()
        self._instances.clear()


# Global container
container = DIContainer()
