const { createApp, ref, computed, watch, onMounted } = Vue;

function decodeBase64Utf8(base64Str) {
  try {
    const binary = atob(base64Str);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return new TextDecoder("utf-8").decode(bytes);
  } catch (e) {
    return atob(base64Str);
  }
}

const DEVICE_CLASS_UNITS = {
  apparent_power: "VA",
  battery: "%",
  carbon_monoxide: "ppm",
  carbon_dioxide: "ppm",
  co: "ppm",
  co2: "ppm",
  humidity: "%",
  illuminance: "lx",
  nitrogen_dioxide: "µg/m³",
  nitrogen_monoxide: "µg/m³",
  nitrous_oxide: "µg/m³",
  ozone: "µg/m³",
  pm1: "µg/m³",
  pm10: "µg/m³",
  pm25: "µg/m³",
  signal_strength: "dB",
  sulphur_dioxide: "µg/m³",
  temperature: "°C",
  pressure: "hPa",
  power: "kW",
  current: "A",
  energy: "kWh",
  frequency: "GHz",
  power_factor: "%",
  reactive_power: "var",
  volatile_organic_compounds: "µg/m³",
  voltage: "V",
  gas: "m³",
};

const PLATFORMS = [
  "alarm_control_panel",
  "binary_sensor",
  "button",
  "camera",
  "climate",
  "cover",
  "device_tracker",
  "fan",
  "light",
  "lock",
  "media_player",
  "number",
  "select",
  "sensor",
  "switch",
  "text",
  "valve",
];

const DEVICE_CLASSES = {
  binary_sensor: [
    "", "battery", "battery_charging", "carbon_monoxide", "cold", "connectivity",
    "door", "garage_door", "gas", "heat", "light", "lock", "moisture", "motion",
    "moving", "occupancy", "opening", "plug", "power", "presence", "problem",
    "running", "safety", "smoke", "sound", "tamper", "update", "vibration", "window",
  ],
  button: ["", "identify", "restart", "update"],
  camera: [""],
  sensor: [
    "", "apparent_power", "battery", "carbon_dioxide", "carbon_monoxide", "current",
    "energy", "frequency", "gas", "humidity", "illuminance", "moisture",
    "nitrogen_dioxide", "nitrogen_monoxide", "nitrous_oxide", "ozone", "pm1",
    "pm10", "pm25", "power_factor", "power", "pressure", "reactive_power",
    "signal_strength", "sulphur_dioxide", "temperature", "volatile_organic_compounds", "voltage",
  ],
  number: [
    "", "apparent_power", "battery", "carbon_dioxide", "carbon_monoxide", "current",
    "energy", "frequency", "gas", "humidity", "illuminance",
    "nitrogen_dioxide", "nitrogen_monoxide", "nitrous_oxide", "ozone", "pm1",
    "pm10", "pm25", "power_factor", "power", "pressure", "reactive_power",
    "signal_strength", "sulphur_dioxide", "temperature", "volatile_organic_compounds", "voltage",
  ],
  cover: ["", "awning", "blind", "curtain", "damper", "door", "garage", "gate", "shade", "shutter", "window"],
  valve: ["", "water", "gas"],
  switch: ["", "outlet", "switch"],
  media_player: ["", "tv", "speaker", "receiver"],
};

const TEMPLATES = [
  {
    id: "motion_sensor",
    name: "Motion Sensor",
    description: "Binary motion sensor with battery level",
    create: (name) => ({
      name: name || "Motion Sensor",
      entities: [
        { platform: "binary_sensor", class: "motion", initial_value: "off", persistent: true, initial_availability: true },
        { platform: "sensor", class: "battery", unit_of_measurement: "%", initial_value: "100", persistent: true, initial_availability: true },
      ],
    }),
  },
  {
    id: "door_contact",
    name: "Door / Window Contact",
    description: "Contact sensor with battery level",
    create: (name) => ({
      name: name || "Front Door",
      entities: [
        { platform: "binary_sensor", class: "door", initial_value: "off", persistent: true, initial_availability: true },
        { platform: "sensor", class: "battery", unit_of_measurement: "%", initial_value: "100", persistent: true, initial_availability: true },
      ],
    }),
  },
  {
    id: "dimmable_light",
    name: "Dimmable Light",
    description: "Virtual light with brightness control",
    create: (name) => ({
      name: name || "Ceiling Light",
      entities: [
        {
          platform: "light",
          initial_value: "off",
          support_brightness: true,
          initial_brightness: 255,
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "rgb_light",
    name: "RGB Color Light",
    description: "Color light with brightness & color temperature",
    create: (name) => ({
      name: name || "Accent Light",
      entities: [
        {
          platform: "light",
          initial_value: "off",
          support_brightness: true,
          initial_brightness: 255,
          support_color: true,
          support_color_temp: true,
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "smart_fan",
    name: "Ceiling Fan",
    description: "Multi-speed fan with direction & oscillation",
    create: (name) => ({
      name: name || "Ceiling Fan",
      entities: [
        {
          platform: "fan",
          initial_value: "off",
          speed: false,
          speed_count: 3,
          direction: true,
          oscillate: true,
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "window_blind",
    name: "Window Cover / Blind",
    description: "Timed opening/closing blind with position control",
    create: (name) => ({
      name: name || "Living Room Blind",
      entities: [
        {
          platform: "cover",
          class: "blind",
          initial_value: "closed",
          open_close_duration: 10,
          open_close_tick: 1,
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "water_valve",
    name: "Water Valve",
    description: "Timed water valve with position feedback",
    create: (name) => ({
      name: name || "Main Water Valve",
      entities: [
        {
          platform: "valve",
          class: "water",
          initial_value: "open",
          open_close_duration: 5,
          open_close_tick: 1,
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "power_outlet",
    name: "Smart Power Outlet",
    description: "Switch with real-time power and energy meter",
    create: (name) => ({
      name: name || "Coffee Maker Outlet",
      entities: [
        { platform: "switch", class: "outlet", initial_value: "on", persistent: true, initial_availability: true },
        { platform: "sensor", class: "power", unit_of_measurement: "W", initial_value: "0", persistent: true, initial_availability: true },
        { platform: "sensor", class: "energy", unit_of_measurement: "kWh", initial_value: "0", persistent: true, initial_availability: true },
      ],
    }),
  },
  {
    id: "water_heater",
    name: "Water Heater",
    description: "Switch with scheduled 10-min hourly heating cycle and power simulation",
    create: (name) => ({
      name: name || "Water Heater",
      entities: [
        {
          platform: "switch",
          name: "Water Heater Switch",
          class: "switch",
          initial_value: "on",
          persistent: true,
          initial_availability: true,
        },
        {
          platform: "sensor",
          name: "Water Heater Power",
          class: "power",
          unit_of_measurement: "W",
          linked_switch: "Water Heater Switch",
          standby_power: 0,
          active_power: 2400,
          cycle_duration: 600,
          cycle_interval: 3600,
          cycle_align: "hour",
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "weather_station",
    name: "Weather Station",
    description: "Temperature, humidity, and atmospheric pressure sensors",
    create: (name) => ({
      name: name || "Outdoor Station",
      entities: [
        { platform: "sensor", class: "temperature", unit_of_measurement: "°C", initial_value: "20", persistent: true, initial_availability: true },
        { platform: "sensor", class: "humidity", unit_of_measurement: "%", initial_value: "50", persistent: true, initial_availability: true },
        { platform: "sensor", class: "pressure", unit_of_measurement: "hPa", initial_value: "1013", persistent: true, initial_availability: true },
      ],
    }),
  },
  {
    id: "smart_tv",
    name: "Smart Television",
    description: "Virtual TV with volume control and selectable HDMI/App sources",
    create: (name) => ({
      name: name || "Living Room TV",
      entities: [
        {
          platform: "media_player",
          class: "tv",
          initial_value: "idle",
          initial_volume: 0.4,
          source_list_str: "TV, HDMI 1, HDMI 2, Netflix, YouTube",
          sound_mode_list_str: "Standard, Cinema, Night",
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "media_speaker",
    name: "Media Speaker",
    description: "Virtual audio speaker for music and TTS announcement testing",
    create: (name) => ({
      name: name || "Kitchen Speaker",
      entities: [
        {
          platform: "media_player",
          class: "speaker",
          initial_value: "idle",
          initial_volume: 0.5,
          source_list_str: "Radio, Spotify, AirPlay",
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "smart_thermostat",
    name: "Smart Thermostat",
    description: "Thermostat with target and current temperatures, presets, and auto actions",
    create: (name) => ({
      name: name || "Living Room Thermostat",
      entities: [
        {
          platform: "climate",
          initial_value: "heat",
          initial_temperature: 21,
          initial_current_temperature: 19.5,
          min: 10,
          max: 32,
          target_temperature_step: 0.5,
          hvac_modes_str: "off, heat, cool, auto",
          preset_modes_str: "none, eco, comfort, away",
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "alarm_system",
    name: "Security Alarm Panel",
    description: "Alarm control panel with PIN code and entry/exit delays",
    create: (name) => ({
      name: name || "Home Security",
      entities: [
        {
          platform: "alarm_control_panel",
          initial_value: "disarmed",
          code: "1234",
          code_arm_required: false,
          arming_time: 10,
          trigger_time: 10,
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "mode_selector",
    name: "Mode Selector",
    description: "Multi-option dropdown selector (e.g. House Mode)",
    create: (name) => ({
      name: name || "House Mode",
      entities: [
        {
          platform: "select",
          options_str: "Home, Away, Night, Vacation",
          initial_value: "Home",
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "action_button",
    name: "Action Button",
    description: "Virtual push button to trigger automations",
    create: (name) => ({
      name: name || "Trigger Action",
      entities: [
        {
          platform: "button",
          class: "restart",
          persistent: false,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "security_camera",
    name: "Security Camera",
    description: "Virtual camera with snapshot and live HLS stream",
    create: (name) => ({
      name: name || "Front Door Camera",
      entities: [
        {
          platform: "camera",
          initial_value: "idle",
          image_url: "",
          stream_url: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
  {
    id: "custom_text",
    name: "Text Input",
    description: "Configurable text input field",
    create: (name) => ({
      name: name || "Announcement Text",
      entities: [
        {
          platform: "text",
          initial_value: "Welcome",
          min: 0,
          max: 255,
          mode: "text",
          persistent: true,
          initial_availability: true,
        },
      ],
    }),
  },
];

createApp({
  setup() {
    const devices = ref([]);
    const showYamlSidebar = ref(true);
    const showTemplateModal = ref(false);
    const showManualYamlModal = ref(false);
    const rawYamlInput = ref("");
    const isSaving = ref(false);
    const saveStatus = ref(null);
    const saveMessage = ref("");

    const callbackUrl = ref(window.__VIRTUAL_CALLBACK_URL || "");
    const token = ref(window.__VIRTUAL_TOKEN || "");
    const groupName = ref(window.__VIRTUAL_GROUP_NAME || "virtual.yaml");
    const initialYaml = ref(window.__VIRTUAL_INITIAL_YAML || "");

    const generatedYaml = computed(() => {
      const output = {
        version: 1,
        devices: {},
      };

      for (const dev of devices.value) {
        if (!dev.name || !dev.name.trim()) continue;
        const deviceName = dev.name.trim();
        output.devices[deviceName] = [];

        for (const ent of dev.entities) {
          const item = { platform: ent.platform };

          if (ent.name && ent.name.trim()) item.name = ent.name.trim();
          if (ent.class) item.class = ent.class;
          if (ent.initial_value !== undefined && ent.initial_value !== "") {
            item.initial_value = ent.initial_value;
          }
          if (ent.persistent !== undefined) item.persistent = ent.persistent;
          if (ent.initial_availability !== undefined) {
            item.initial_availability = ent.initial_availability;
          }

          // Platform specifics
          if (ent.platform === "sensor" || ent.platform === "number") {
            if (ent.unit_of_measurement) {
              item.unit_of_measurement = ent.unit_of_measurement.replace(/Â°/g, "°");
            }
          }
          if (ent.platform === "number") {
            if (ent.min !== undefined && ent.min !== "") item.min = Number(ent.min);
            if (ent.max !== undefined && ent.max !== "") item.max = Number(ent.max);
          }
          if (ent.platform === "cover" || ent.platform === "valve") {
            if (ent.open_close_duration !== undefined) {
              item.open_close_duration = Number(ent.open_close_duration);
            }
            if (ent.open_close_tick !== undefined) {
              item.open_close_tick = Number(ent.open_close_tick);
            }
          }
          if (ent.platform === "light") {
            if (ent.support_brightness) item.support_brightness = true;
            if (ent.initial_brightness !== undefined) item.initial_brightness = Number(ent.initial_brightness);
            if (ent.support_color) item.support_color = true;
            if (ent.support_color_temp) item.support_color_temp = true;
            if (ent.support_white_value) item.support_white_value = true;
            if (ent.support_effect) {
              item.support_effect = true;
              if (ent.initial_effect) item.initial_effect = ent.initial_effect;
            }
          }
          if (ent.platform === "fan") {
            if (ent.speed) item.speed = true;
            if (ent.speed_count) item.speed_count = Number(ent.speed_count);
            if (ent.direction) item.direction = true;
            if (ent.oscillate) item.oscillate = true;
          }
          if (ent.platform === "lock") {
            if (ent.locking_time) item.locking_time = Number(ent.locking_time);
            if (ent.jamming_test) item.jamming_test = Number(ent.jamming_test);
          }
          if (ent.platform === "select") {
            const rawOpts = ent.options_str ? ent.options_str.split(",").map((s) => s.trim()).filter((s) => s) : (ent.options || []);
            item.options = rawOpts;
          }
          if (ent.platform === "text") {
            if (ent.min !== undefined && ent.min !== "") item.min = Number(ent.min);
            if (ent.max !== undefined && ent.max !== "") item.max = Number(ent.max);
            if (ent.mode) item.mode = ent.mode;
            if (ent.pattern) item.pattern = ent.pattern;
          }
          if (ent.platform === "alarm_control_panel") {
            if (ent.code) item.code = String(ent.code);
            if (ent.code_arm_required) item.code_arm_required = true;
            if (ent.arming_time) item.arming_time = Number(ent.arming_time);
            if (ent.trigger_time) item.trigger_time = Number(ent.trigger_time);
          }
          if (ent.platform === "climate") {
            if (ent.initial_temperature !== undefined && ent.initial_temperature !== "") {
              item.initial_temperature = Number(ent.initial_temperature);
            }
            if (ent.initial_current_temperature !== undefined && ent.initial_current_temperature !== "") {
              item.initial_current_temperature = Number(ent.initial_current_temperature);
            }
            if (ent.min !== undefined && ent.min !== "") item.min = Number(ent.min);
            if (ent.max !== undefined && ent.max !== "") item.max = Number(ent.max);
            if (ent.target_temperature_step !== undefined && ent.target_temperature_step !== "") {
              item.target_temperature_step = Number(ent.target_temperature_step);
            }
            if (ent.hvac_modes_str) {
              item.hvac_modes = ent.hvac_modes_str.split(",").map((s) => s.trim().toLowerCase()).filter((s) => s);
            }
            if (ent.preset_modes_str) {
              item.preset_modes = ent.preset_modes_str.split(",").map((s) => s.trim().toLowerCase()).filter((s) => s);
            }
            if (ent.fan_modes_str) {
              item.fan_modes = ent.fan_modes_str.split(",").map((s) => s.trim().toLowerCase()).filter((s) => s);
            }
          }
          if (ent.platform === "sensor") {
            if (ent.linked_switch) {
              item.linked_switch = ent.linked_switch;
              if (ent.standby_power !== undefined && ent.standby_power !== "") item.standby_power = Number(ent.standby_power);
              if (ent.active_power !== undefined && ent.active_power !== "") item.active_power = Number(ent.active_power);
              if (ent.initial_load) item.initial_load = ent.initial_load;
              if (ent.variance !== undefined && ent.variance !== "") item.variance = Number(ent.variance);
              if (ent.cycle_duration !== undefined && ent.cycle_duration !== "") item.cycle_duration = Number(ent.cycle_duration);
              if (ent.cycle_interval !== undefined && ent.cycle_interval !== "") item.cycle_interval = Number(ent.cycle_interval);
              if (ent.cycle_align) item.cycle_align = ent.cycle_align;
            }
          }
          if (ent.platform === "camera") {
            if (ent.image_url) item.image_url = ent.image_url;
            if (ent.stream_url) item.stream_url = ent.stream_url;
          }
          if (ent.platform === "media_player") {
            if (ent.initial_volume !== undefined && ent.initial_volume !== "") {
              item.initial_volume = Number(ent.initial_volume);
            }
            if (ent.source_list_str) {
              item.source_list = ent.source_list_str.split(",").map((s) => s.trim()).filter((s) => s);
            }
            if (ent.sound_mode_list_str) {
              item.sound_mode_list = ent.sound_mode_list_str.split(",").map((s) => s.trim()).filter((s) => s);
            }
          }

          output.devices[deviceName].push(item);
        }
      }

      try {
        return jsyaml.dump(output, { indent: 2, lineWidth: -1, noRefs: true });
      } catch (err) {
        return `# Error rendering YAML: ${err.message}`;
      }
    });

    const addDevice = () => {
      const num = devices.value.length + 1;
      devices.value.push({
        name: `Virtual Device ${num}`,
        collapsed: false,
        entities: [createDefaultEntity("binary_sensor")],
      });
    };

    const toggleCollapse = (device) => {
      device.collapsed = !device.collapsed;
    };

    const allCollapsed = computed(() => {
      return devices.value.length > 0 && devices.value.every((d) => d.collapsed);
    });

    const toggleAllCollapse = () => {
      const targetState = !allCollapsed.value;
      for (const dev of devices.value) {
        dev.collapsed = targetState;
      }
    };

    const removeDevice = (index) => {
      devices.value.splice(index, 1);
    };

    const createDefaultEntity = (platform) => {
      const base = {
        platform,
        name: "",
        initial_value: platform === "light" || platform === "switch" || platform === "binary_sensor" ? "off" : "0",
        persistent: true,
        initial_availability: true,
      };

      if (platform === "cover" || platform === "valve") {
        base.initial_value = "closed";
        base.open_close_duration = 10;
        base.open_close_tick = 1;
      } else if (platform === "lock") {
        base.initial_value = "locked";
        base.locking_time = 0;
        base.jamming_test = 0;
      } else if (platform === "light") {
        base.support_brightness = true;
        base.initial_brightness = 255;
      } else if (platform === "fan") {
        base.speed_count = 3;
      } else if (platform === "number") {
        base.min = 0;
        base.max = 100;
        base.initial_value = 50;
      } else if (platform === "device_tracker") {
        base.initial_value = "home";
      } else if (platform === "button") {
        base.initial_value = "";
        base.persistent = false;
      } else if (platform === "select") {
        base.options_str = "Home, Away, Night, Vacation";
        base.initial_value = "Home";
      } else if (platform === "text") {
        base.initial_value = "";
        base.min = 0;
        base.max = 255;
        base.mode = "text";
      } else if (platform === "alarm_control_panel") {
        base.initial_value = "disarmed";
        base.code = "1234";
        base.code_arm_required = false;
        base.arming_time = 0;
        base.trigger_time = 0;
      } else if (platform === "camera") {
        base.initial_value = "idle";
        base.image_url = "";
        base.stream_url = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8";
      } else if (platform === "media_player") {
        base.initial_value = "idle";
        base.initial_volume = 0.5;
        base.source_list_str = "TV, HDMI 1, HDMI 2, Netflix, YouTube";
      } else if (platform === "climate") {
        base.initial_value = "heat";
        base.initial_temperature = 21;
        base.initial_current_temperature = 20;
        base.min = 7;
        base.max = 35;
        base.target_temperature_step = 0.5;
        base.hvac_modes_str = "off, heat, cool, auto";
        base.preset_modes_str = "none, eco, comfort, away";
      }

      return base;
    };

    const addEntity = (device) => {
      device.entities.push(createDefaultEntity("binary_sensor"));
    };

    const removeEntity = (device, index) => {
      device.entities.splice(index, 1);
    };

    const onClassChange = (entity) => {
      if (entity.class && DEVICE_CLASS_UNITS[entity.class]) {
        entity.unit_of_measurement = DEVICE_CLASS_UNITS[entity.class];
      }
    };

    const applyTemplate = (template) => {
      const num = devices.value.length + 1;
      const device = template.create(`${template.name} ${num}`);
      device.collapsed = false;
      devices.value.push(device);
      showTemplateModal.value = false;
    };

    const loadFromYamlString = (yamlText) => {
      try {
        const parsed = jsyaml.load(yamlText);
        if (!parsed || typeof parsed !== "object") return;

        const devMap = parsed.devices || parsed;
        const newDevices = [];

        for (const [deviceName, entList] of Object.entries(devMap)) {
          if (!Array.isArray(entList)) continue;
          const entities = entList.map((item) => ({
            platform: item.platform || "switch",
            name: item.name || "",
            class: item.class || "",
            initial_value: item.initial_value !== undefined ? String(item.initial_value) : "",
            persistent: item.persistent !== undefined ? item.persistent : true,
            initial_availability: item.initial_availability !== undefined ? item.initial_availability : true,
            unit_of_measurement: (item.unit_of_measurement || "").replace(/Â°/g, "°"),
            min: item.min,
            max: item.max,
            open_close_duration: item.open_close_duration,
            open_close_tick: item.open_close_tick,
            support_brightness: item.support_brightness || false,
            initial_brightness: item.initial_brightness || 255,
            support_color: item.support_color || false,
            support_color_temp: item.support_color_temp || false,
            support_white_value: item.support_white_value || false,
            support_effect: item.support_effect || false,
            initial_effect: item.initial_effect || "",
            speed: item.speed || false,
            speed_count: item.speed_count || 0,
            direction: item.direction || false,
            oscillate: item.oscillate || false,
            locking_time: item.locking_time || 0,
            jamming_test: item.jamming_test || 0,
            options: item.options || [],
            options_str: Array.isArray(item.options) ? item.options.join(", ") : (item.options || ""),
            mode: item.mode || "text",
            pattern: item.pattern || "",
            code: item.code || "",
            code_arm_required: item.code_arm_required || false,
            arming_time: item.arming_time || 0,
            trigger_time: item.trigger_time || 0,
            initial_temperature: item.initial_temperature,
            initial_current_temperature: item.initial_current_temperature,
            target_temperature_step: item.target_temperature_step,
            hvac_modes_str: Array.isArray(item.hvac_modes) ? item.hvac_modes.join(", ") : (item.hvac_modes || ""),
            preset_modes_str: Array.isArray(item.preset_modes) ? item.preset_modes.join(", ") : (item.preset_modes || ""),
            fan_modes_str: Array.isArray(item.fan_modes) ? item.fan_modes.join(", ") : (item.fan_modes || ""),
            initial_volume: item.initial_volume !== undefined ? item.initial_volume : 0.5,
            linked_switch: item.linked_switch || "",
            standby_power: item.standby_power !== undefined ? item.standby_power : 0,
            active_power: item.active_power !== undefined ? item.active_power : 100,
            initial_load: item.initial_load || "standby",
            variance: item.variance !== undefined ? item.variance : 0,
            cycle_duration: item.cycle_duration,
            cycle_interval: item.cycle_interval,
            cycle_align: item.cycle_align || "hour",
            image_url: item.image_url || "",
            stream_url: item.stream_url !== undefined ? item.stream_url : (item.platform === "camera" ? "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" : ""),
            source_list_str: Array.isArray(item.source_list) ? item.source_list.join(", ") : (item.source_list || ""),
            sound_mode_list_str: Array.isArray(item.sound_mode_list) ? item.sound_mode_list.join(", ") : (item.sound_mode_list || ""),
          }));

          newDevices.push({
            name: deviceName,
            collapsed: false,
            entities,
          });
        }

        if (newDevices.length > 0) {
          devices.value = newDevices;
        }
      } catch (err) {
        saveStatus.value = "error";
        saveMessage.value = `Error parsing YAML: ${err.message}`;
      }
    };

    const importManualYaml = () => {
      if (rawYamlInput.value) {
        loadFromYamlString(rawYamlInput.value);
        showManualYamlModal.value = false;
        rawYamlInput.value = "";
      }
    };

    const copyYaml = () => {
      navigator.clipboard.writeText(generatedYaml.value).then(() => {
        saveStatus.value = "success";
        saveMessage.value = "YAML copied to clipboard!";
      }).catch((err) => {
        saveStatus.value = "error";
        saveMessage.value = `Failed to copy YAML: ${err}`;
      });
    };

    const downloadYaml = () => {
      const blob = new Blob([generatedYaml.value], { type: "text/yaml;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = groupName.value.endsWith(".yaml") ? groupName.value : `${groupName.value}.yaml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    };

    const saveAndReturn = async () => {
      if (!callbackUrl.value) {
        copyYaml();
        return;
      }

      isSaving.value = true;
      saveStatus.value = null;

      try {
        const response = await fetch("/api/save", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            callback_url: callbackUrl.value,
            token: token.value,
            yaml: generatedYaml.value,
          }),
        });

        const result = await response.json();
        if (response.ok && result.ok) {
          saveStatus.value = "success";
          saveMessage.value = "Saved successfully! Your Home Assistant configuration has reloaded. You can close this window.";
        } else {
          throw new Error(result.error || `Server responded with status ${response.status}`);
        }
      } catch (err) {
        saveStatus.value = "error";
        saveMessage.value = `Failed to send to Home Assistant: ${err.message}. You can download the YAML or copy to clipboard below.`;
      } finally {
        isSaving.value = false;
      }
    };

    const closeTab = () => {
      window.close();
    };

    onMounted(() => {
      // Check for data in hash fragment (e.g. #data=...)
      const hash = window.location.hash.substring(1);
      const params = new URLSearchParams(hash);
      const hashData = params.get("data");

      if (hashData) {
        try {
          const decoded = decodeBase64Utf8(hashData);
          loadFromYamlString(decoded);
          return;
        } catch (e) {
          saveStatus.value = "error";
          saveMessage.value = `Could not decode base64 data: ${e.message}`;
        }
      }

      if (initialYaml.value) {
        loadFromYamlString(initialYaml.value);
      } else {
        // Start with one sample device if completely empty
        addDevice();
      }
    });

    return {
      devices,
      showYamlSidebar,
      showTemplateModal,
      showManualYamlModal,
      rawYamlInput,
      isSaving,
      saveStatus,
      saveMessage,
      callbackUrl,
      groupName,
      generatedYaml,
      PLATFORMS,
      DEVICE_CLASSES,
      TEMPLATES,
      addDevice,
      removeDevice,
      toggleCollapse,
      allCollapsed,
      toggleAllCollapse,
      addEntity,
      removeEntity,
      onClassChange,
      applyTemplate,
      importManualYaml,
      copyYaml,
      downloadYaml,
      saveAndReturn,
      closeTab,
    };
  },
}).mount("#app");
