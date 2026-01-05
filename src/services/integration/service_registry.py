"""
Service Registry for dependency injection and service management.

Implements a singleton pattern for centralized service access across
the application.
"""

import logging
from typing import Any, Callable, Dict, Optional
from threading import Lock


logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Singleton registry for managing service instances.

    Provides centralized access to services with lazy initialization
    and health checking capabilities.
    """

    _instance: Optional["ServiceRegistry"] = None
    _lock = Lock()

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the registry on first creation."""
        if not self._initialized:
            self._services: Dict[str, Any] = {}
            self._factories: Dict[str, Callable[[], Any]] = {}
            self._health_checkers: Dict[str, Callable[[], bool]] = {}
            self._initialized = True
            logger.info("ServiceRegistry initialized")

    def register(
        self,
        name: str,
        service: Optional[Any] = None,
        factory: Optional[Callable[[], Any]] = None,
        health_checker: Optional[Callable[[], bool]] = None
    ) -> None:
        """
        Register a service instance or factory.

        Args:
            name: Unique service identifier
            service: Service instance (for eager initialization)
            factory: Factory function for lazy initialization
            health_checker: Optional function to check service health

        Raises:
            ValueError: If neither service nor factory is provided
        """
        if service is None and factory is None:
            raise ValueError(f"Must provide either service or factory for '{name}'")

        with self._lock:
            if service is not None:
                self._services[name] = service
                logger.info(f"Registered service: {name}")
            else:
                self._factories[name] = factory
                logger.info(f"Registered service factory: {name}")

            if health_checker:
                self._health_checkers[name] = health_checker

    def get(self, name: str) -> Any:
        """
        Get a service by name.

        Args:
            name: Service identifier

        Returns:
            Service instance

        Raises:
            KeyError: If service not found
        """
        # Check if already instantiated
        if name in self._services:
            return self._services[name]

        # Try to instantiate from factory
        if name in self._factories:
            with self._lock:
                # Double-check after acquiring lock
                if name not in self._services:
                    logger.info(f"Lazy initializing service: {name}")
                    self._services[name] = self._factories[name]()
                return self._services[name]

        raise KeyError(f"Service not found: {name}")

    def has(self, name: str) -> bool:
        """
        Check if a service is registered.

        Args:
            name: Service identifier

        Returns:
            True if service is registered
        """
        return name in self._services or name in self._factories

    def unregister(self, name: str) -> None:
        """
        Unregister a service.

        Args:
            name: Service identifier
        """
        with self._lock:
            self._services.pop(name, None)
            self._factories.pop(name, None)
            self._health_checkers.pop(name, None)
            logger.info(f"Unregistered service: {name}")

    def check_health(self, name: Optional[str] = None) -> Dict[str, bool]:
        """
        Check health of one or all services.

        Args:
            name: Optional service name (checks all if None)

        Returns:
            Dict mapping service names to health status
        """
        results = {}

        if name:
            services_to_check = {name: self._health_checkers.get(name)}
        else:
            services_to_check = self._health_checkers

        for service_name, checker in services_to_check.items():
            if checker is None:
                # No health checker, assume healthy if service exists
                results[service_name] = self.has(service_name)
            else:
                try:
                    results[service_name] = checker()
                except Exception as e:
                    logger.error(f"Health check failed for {service_name}: {e}")
                    results[service_name] = False

        return results

    def get_all_services(self) -> Dict[str, Any]:
        """
        Get all instantiated services.

        Returns:
            Dict of service names to instances
        """
        return self._services.copy()

    def reset(self) -> None:
        """
        Reset the registry (primarily for testing).

        WARNING: This clears all registered services.
        """
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._health_checkers.clear()
            logger.warning("ServiceRegistry reset")


# Global instance accessor
def get_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    return ServiceRegistry()
