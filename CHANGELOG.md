# Changelog

## [Unreleased] - 2025-12-01

### Added
- **State Visibility Control**: Implemented `_attr_entity_registry_visible_default = False` for cleaner UI
  - All button entities now hide state display by default
  - Power sensors (created from `Watt` attribute) hide state display by default
  - Entities remain fully functional but don't clutter dashboards

- **Visible Property Support**: All entity types now respect the `Visible` property from IPBuilding API
  - Entities with `"Visible": false` are marked as unavailable in Home Assistant
  - Implemented via `available` property in all platform classes (button, sensor, switch, light, scene)

- **Scene Platform**: Added support for IPBuilding scenes
  - Sphere devices (Type 100)
  - TempSphere devices (Type 101)
  - Scenes can be activated from Home Assistant

- **Enhanced Documentation**: 
  - Added comprehensive entity features documentation
  - Documented supported platforms
  - Added state visibility behavior
  - Documented power monitoring capabilities
  - Added device grouping information
  - Listed all exposed entity attributes

### Improved
- **Consistency Across Platforms**: All entity types now have consistent:
  - `available` property based on `Visible` field
  - `extra_state_attributes` exposing IPBuilding properties
  - Device grouping via `Group.ID` and `Group.Name`
  - Proper entity naming using `Description` field

- **Button Platform**: 
  - Added `available` property
  - Added state visibility control
  - Maintains `entity_registry_enabled_default = False` (disabled by default)

- **Sensor Platform**:
  - Added `available` property to `IPBuildingSensor`
  - Added `available` property to `IPBuildingPowerSensor`
  - Power sensors hide state display by default

- **Scene Platform**:
  - Added `available` property
  - Added `extra_state_attributes` for consistency
  - Exposes IPBuilding device properties as attributes

### Entity Attributes
All entities now expose the following IPBuilding properties as attributes:
- `IpAddress`: IP address of the physical device
- `Port`: Port number
- `Protocol`: Communication protocol
- `ID`: IPBuilding device ID
- `Status`: Current device status
- `Output`: Output configuration
- `Kind`: Device kind/subtype

### Technical Details
- Modified files:
  - `button.py`: Added state visibility + available property
  - `sensor.py`: Added available property to both sensor classes + state visibility for power sensors
  - `scene.py`: Added available property + extra_state_attributes
  - `README.md`: Comprehensive documentation updates
  - (Previously modified: `switch.py`, `light.py` - already had available property)
