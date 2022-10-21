"""Platform for sensor integration."""
from __future__ import annotations
from datetime import timedelta
import logging

import async_timeout
from homeassistant.components.binary_sensor import BinarySensorEntity

# from homeassistant.exceptions import ConfigEntryAuthFailed

from homeassistant.helpers.entity import DeviceInfo
from pyaton import AtonAPI
from .const import DOMAIN

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, POWER_WATT, ENERGY_WATT_HOUR
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    username = config.data["username"]
    sn = config.data["sn"]
    id_impianto = config.data["id_impianto"]
    api = AtonAPI(username, sn, id_impianto)
    coordinator = ApiCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    add_entities(
        [
            #power
            BatteryStatus(coordinator),
            HouseConsumption(coordinator),
            BatteryPower(coordinator),
            SolarProduction(coordinator),
            GridPower(coordinator),
            #power direction
            GridToHouse(coordinator),
            SolarToBattery(coordinator),
            SolarToGrid(coordinator),
            BatteryToHouse(coordinator),
            SolarToHouse(coordinator),
            GridToBattery(coordinator),
            BatteryToGrid(coordinator),
            #energy
            SoldEnergy(coordinator),
            SolarEnergy(coordinator),
            SelfConsumedEnergy(coordinator),
            BoughtEnergy(coordinator),
            ConsumedEnergy(coordinator),
            #other
            SelfSufficiency(coordinator),
        ]
    )


class ApiCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, api: AtonAPI):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Aton Storage",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=api.interval),
        )
        self.api = api

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(self.api.interval):
                return await self.hass.async_add_executor_job(self.api.fetch_data)
        except Exception as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            # raise ConfigEntryAuthFailed from err
            # except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")


class BatteryStatus(SensorEntity, CoordinatorEntity):
    """Representation of a Sensor."""

    @property
    def device_info(self) -> DeviceInfo | None:
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, "aton_storage_" + self.coordinator.api.username)
            },
            "name": f"Fotovoltaico {self.coordinator.api.username}",
            "manufacturer": "Aton Green Storage",
        }

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Batteria Casa"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = "aton_battery_" + coordinator.api.username

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.api.status.current_battery_status
        self.async_write_ha_state()


class BasePowerSensor(SensorEntity, CoordinatorEntity):
    """Representation of a Sensor."""

    @property
    def device_info(self) -> DeviceInfo | None:
        return {
            "identifiers": {(DOMAIN, "aton_storage_" + self.coordinator.api.username)}
        }

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_native_unit_of_measurement = POWER_WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT

    def update(self) -> None:
        """update"""

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update()
        self.async_write_ha_state()


class HouseConsumption(BasePowerSensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Consumo Casa"
        self._attr_unique_id = "aton_home_" + coordinator.api.username

    def update(self) -> None:
        self._attr_native_value = self.coordinator.api.status.current_house_consumption


class BatteryPower(BasePowerSensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Corrente Batteria"
        self._attr_unique_id = "aton_battery_power_" + coordinator.api.username

    def update(self) -> None:
        self._attr_native_value = self.coordinator.api.status.current_battery_power


class SolarProduction(BasePowerSensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Produzione Pannelli"
        self._attr_unique_id = "aton_solar_power_" + coordinator.api.username

    def update(self) -> None:
        self._attr_native_value = self.coordinator.api.status.current_solar_production


class GridPower(BasePowerSensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Corrente Rete"
        self._attr_unique_id = "aton_grid_power_" + coordinator.api.username

    def update(self) -> None:
        self._attr_native_value = self.coordinator.api.status.current_grid_power


class BaseBinarySensor(BinarySensorEntity, CoordinatorEntity):
    """Representation of a Sensor."""

    @property
    def device_info(self) -> DeviceInfo | None:
        return {
            "identifiers": {(DOMAIN, "aton_storage_" + self.coordinator.api.username)}
        }

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_class = SensorDeviceClass.POWER

    @property
    def is_on(self) -> bool:
        """update"""

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class GridToHouse(BaseBinarySensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Da Rete a Casa"
        self._attr_unique_id = "aton_grid_house_" + coordinator.api.username

    @property
    def is_on(self) -> bool:
        return self.coordinator.api.status.grid_to_house


class SolarToBattery(BaseBinarySensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Da Pannelli a Batteria"
        self._attr_unique_id = "aton_solar_battery_" + coordinator.api.username

    @property
    def is_on(self) -> bool:
        return self.coordinator.api.status.solar_to_battery


class SolarToGrid(BaseBinarySensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Da Pannelli a Rete"
        self._attr_unique_id = "aton_solar_grid_" + coordinator.api.username

    @property
    def is_on(self) -> bool:
        return self.coordinator.api.status.solar_to_grid


class BatteryToHouse(BaseBinarySensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Da Batteria a Casa"
        self._attr_unique_id = "aton_battery_house_" + coordinator.api.username

    @property
    def is_on(self) -> bool:
        return self.coordinator.api.status.battery_to_house


class SolarToHouse(BaseBinarySensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Da Pannelli a Casa"
        self._attr_unique_id = "aton_solar_house_" + coordinator.api.username

    @property
    def is_on(self) -> bool:
        return self.coordinator.api.status.solar_to_house


class GridToBattery(BaseBinarySensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Da Rete a Batteria"
        self._attr_unique_id = "aton_grid_battery_" + coordinator.api.username

    @property
    def is_on(self) -> bool:
        return self.coordinator.api.status.grid_to_battery


class BatteryToGrid(BaseBinarySensor):
    """Representation of a Sensor."""

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Da Batteria a Rete"
        self._attr_unique_id = "aton_battery_grid_" + coordinator.api.username

    @property
    def is_on(self) -> bool:
        return self.coordinator.api.status.battery_to_grid


class BaseEnergySensor(SensorEntity, CoordinatorEntity):
    """Representation of a Sensor."""

    @property
    def device_info(self) -> DeviceInfo | None:
        return {
            "identifiers": {(DOMAIN, "aton_storage_" + self.coordinator.api.username)}
        }

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_native_unit_of_measurement = ENERGY_WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    def update(self) -> None:
        """update"""

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update()
        self.async_write_ha_state()


class SoldEnergy(BaseEnergySensor):
    """Representation of a Sensor"""

    def __init__(self,coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Energia Venduta"
        self._attr_unique_id = "aton_sold_energy_"+coordinator.api.username

    def update(self) -> None:
        self._attr_native_value = self.coordinator.api.status.sold_energy


class SolarEnergy(BaseEnergySensor):
    """Representation of a Sensor"""

    def __init__(self,coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Energia Solare"
        self._attr_unique_id = "aton_solar_energy_"+coordinator.api.username

    def update(self) -> None:
        self._attr_native_value = self.coordinator.api.status.solar_energy


class SelfConsumedEnergy(BaseEnergySensor):
    """Representation of a Sensor"""

    def __init__(self,coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Energia Auto Consumata"
        self._attr_unique_id = "aton_self_energy_"+coordinator.api.username

    def update(self) -> None:
        self._attr_native_value = self.coordinator.api.status.self_consumed_energy


class BoughtEnergy(BaseEnergySensor):
    """Representation of a Sensor"""

    def __init__(self,coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Energia Comprata"
        self._attr_unique_id = "aton_bought_energy_"+coordinator.api.username

    def update(self) -> None:
        self._attr_native_value = self.coordinator.api.status.bought_energy


class ConsumedEnergy(BaseEnergySensor):
    """Representation of a Sensor"""

    def __init__(self,coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Energia Consumata"
        self._attr_unique_id = "aton_consumed_energy_"+coordinator.api.username

    def update(self) -> None:
        self._attr_native_value = self.coordinator.api.status.consumed_energy

class SelfSufficiency(SensorEntity, CoordinatorEntity):
    """Representation of a Sensor."""

    @property
    def device_info(self) -> DeviceInfo | None:
        return {
            "identifiers": {
                (DOMAIN, "aton_storage_" + self.coordinator.status.api.username)
            },
        }

    def __init__(self, coordinator: ApiCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Autosufficienza"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.POWER_FACTOR
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = "aton_self_sufficiency_" + coordinator.api.username

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.api.status.self_sufficiency
        self.async_write_ha_state()

