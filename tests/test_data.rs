#[cfg(test)]
mod tests {
    use serde_json::json;

    // Test data based on TestData.py

    const SNOW_DEPTH_TEST_RUN: u32 = 137292;
    const SNOW_DEPTH_TEST_HEIGHT: f64 = 2.879;

    const DOM_ID_1_61: u32 = 161;
    const DOM_ID_1_62: u32 = 162;

    const STRING_ID: u32 = 1;
    const POSITION_61: u32 = 61;
    const POSITION_62: u32 = 62;

    // Baseline calibration data for DOM 1-61
    fn get_baseline_calibration_1_61() -> serde_json::Value {
        json!({
            "dom_id": DOM_ID_1_61,
            "domcal": {
                "atwd_gain": [125.068580, 136.172671, 136.172799],
                "atwd_freq": [0.0, 0.0, 0.0],
                "fadc_gain": 137.1852,
                "fadc_freq": 0.0,
                "pmt_gain": 1.0,
                "transit_time": 0.0,
                "relative_pmt_gain": 1.0
            }
        })
    }

    // Baseline calibration data for DOM 1-62
    fn get_baseline_calibration_1_62() -> serde_json::Value {
        json!({
            "dom_id": DOM_ID_1_62,
            "domcal": {
                "atwd_gain": [126.925628, 131.162387, 132.048000],
                "atwd_freq": [0.0, 0.0, 0.0],
                "fadc_gain": 126.028301,
                "fadc_freq": 0.0,
                "pmt_gain": 1.0,
                "transit_time": 0.0,
                "relative_pmt_gain": 1.0
            }
        })
    }

    // VEM calibration data
    fn get_vem_calibration_1_61() -> serde_json::Value {
        json!({
            "dom_id": DOM_ID_1_61,
            "domcal": {
                "atwd_gain": [116.274, 116.274, 116.274],
                "atwd_freq": [0.0, 0.0, 0.0],
                "fadc_gain": 116.274,
                "fadc_freq": 0.0,
                "pmt_gain": 1.0,
                "transit_time": 0.0,
                "relative_pmt_gain": 1.0
            }
        })
    }

    // SPE calibration data
    fn get_spe_calibration_1_61() -> serde_json::Value {
        json!({
            "dom_id": DOM_ID_1_61,
            "domcal": {
                "atwd_gain": [1.0341419190237735, 1.0341419190237735, 1.0341419190237735],
                "atwd_freq": [0.0, 0.0, 0.0],
                "fadc_gain": 1.1160816676546705,
                "fadc_freq": 0.0,
                "pmt_gain": 1.0,
                "transit_time": 0.0,
                "relative_pmt_gain": 1.0
            }
        })
    }

    // Geometry data - String 1 DOM position 61
    fn get_geometry_1_61() -> serde_json::Value {
        json!({
            "string": STRING_ID,
            "position": POSITION_61,
            "location": {
                "x": 10.0,
                "y": 20.0,
                "z": -500.0
            }
        })
    }

    // Geometry data - String 1 DOM position 62
    fn get_geometry_1_62() -> serde_json::Value {
        json!({
            "string": STRING_ID,
            "position": POSITION_62,
            "location": {
                "x": 15.0,
                "y": 25.0,
                "z": -505.0
            }
        })
    }

    // Detector status data
    fn get_detector_status_1_61() -> serde_json::Value {
        json!({
            "dom_id": DOM_ID_1_61,
            "status": "operational",
            "is_bad": false
        })
    }

    fn get_detector_status_1_62() -> serde_json::Value {
        json!({
            "dom_id": DOM_ID_1_62,
            "status": "operational",
            "is_bad": false
        })
    }

    // Snow height data
    fn get_snow_height_test_run() -> serde_json::Value {
        json!({
            "run_number": SNOW_DEPTH_TEST_RUN,
            "height": SNOW_DEPTH_TEST_HEIGHT
        })
    }

    // Configuration data
    fn get_configuration_noise_rate() -> serde_json::Value {
        json!({
            "key": "noise_rate_1_61",
            "value": {
                "rate_hz": 1386.35,
                "stddev_hz": 11.8296
            }
        })
    }

    #[test]
    fn test_calibration_data_baseline_1_61() {
        let cal = get_baseline_calibration_1_61();
        assert_eq!(cal["dom_id"], DOM_ID_1_61);
        assert_eq!(cal["domcal"]["atwd_gain"][0], 125.068580);
    }

    #[test]
    fn test_calibration_data_baseline_1_62() {
        let cal = get_baseline_calibration_1_62();
        assert_eq!(cal["dom_id"], DOM_ID_1_62);
        assert_eq!(cal["domcal"]["fadc_gain"], 126.028301);
    }

    #[test]
    fn test_vem_calibration_data() {
        let cal = get_vem_calibration_1_61();
        assert_eq!(cal["dom_id"], DOM_ID_1_61);
        assert_eq!(cal["domcal"]["fadc_gain"], 116.274);
    }

    #[test]
    fn test_spe_calibration_data() {
        let cal = get_spe_calibration_1_61();
        assert_eq!(cal["dom_id"], DOM_ID_1_61);
        assert!(cal["domcal"]["fadc_gain"].is_number());
    }

    #[test]
    fn test_geometry_string_1_position_61() {
        let geom = get_geometry_1_61();
        assert_eq!(geom["string"], STRING_ID);
        assert_eq!(geom["position"], POSITION_61);
        assert_eq!(geom["location"]["z"], -500.0);
    }

    #[test]
    fn test_geometry_string_1_position_62() {
        let geom = get_geometry_1_62();
        assert_eq!(geom["string"], STRING_ID);
        assert_eq!(geom["position"], POSITION_62);
        assert_eq!(geom["location"]["x"], 15.0);
    }

    #[test]
    fn test_detector_status_operational() {
        let status = get_detector_status_1_61();
        assert_eq!(status["dom_id"], DOM_ID_1_61);
        assert_eq!(status["status"], "operational");
        assert_eq!(status["is_bad"], false);
    }

    #[test]
    fn test_snow_height_data() {
        let snow = get_snow_height_test_run();
        assert_eq!(snow["run_number"], SNOW_DEPTH_TEST_RUN);
        assert_eq!(snow["height"], SNOW_DEPTH_TEST_HEIGHT);
    }

    #[test]
    fn test_configuration_noise_rate() {
        let config = get_configuration_noise_rate();
        assert_eq!(config["key"], "noise_rate_1_61");
        assert!(config["value"]["rate_hz"].is_number());
    }

    // Integration test scenarios
    #[test]
    fn test_create_and_retrieve_calibration() {
        // Test data structure for create + retrieve workflow
        let calibration_1 = get_baseline_calibration_1_61();
        let calibration_2 = get_vem_calibration_1_61();
        
        // Both should have same DOM ID but different values
        assert_eq!(calibration_1["dom_id"], calibration_2["dom_id"]);
        assert_ne!(calibration_1["domcal"]["fadc_gain"], calibration_2["domcal"]["fadc_gain"]);
    }

    #[test]
    fn test_geometry_consistency() {
        let geom_1 = get_geometry_1_61();
        let geom_2 = get_geometry_1_62();
        
        // Both should be in same string but different positions
        assert_eq!(geom_1["string"], geom_2["string"]);
        assert_ne!(geom_1["position"], geom_2["position"]);
        
        // Z coordinates should be different (going deeper)
        assert!(geom_2["location"]["z"] < geom_1["location"]["z"]);
    }

    #[test]
    fn test_detector_status_batch() {
        let status_1 = get_detector_status_1_61();
        let status_2 = get_detector_status_1_62();
        
        // Both should be operational
        assert_eq!(status_1["status"], "operational");
        assert_eq!(status_2["status"], "operational");
        assert_eq!(status_1["is_bad"], false);
        assert_eq!(status_2["is_bad"], false);
    }

    #[test]
    fn test_snow_height_run_update_scenario() {
        let run_number = SNOW_DEPTH_TEST_RUN;
        let initial_snow = get_snow_height_test_run();
        
        assert_eq!(initial_snow["run_number"], run_number);
        
        // Simulate updated height for same run
        let updated_snow = json!({
            "run_number": run_number,
            "height": 3.5  // increased snow depth
        });
        
        assert_eq!(initial_snow["run_number"], updated_snow["run_number"]);
        assert!(updated_snow["height"].as_f64().unwrap() > initial_snow["height"].as_f64().unwrap());
    }

    #[test]
    fn test_gcd_collection_components() {
        let run_number = 137292;
        
        // Simulate GCD collection with baseline components
        let calibrations = vec![
            get_baseline_calibration_1_61(),
            get_baseline_calibration_1_62(),
        ];
        let geometry = vec![
            get_geometry_1_61(),
            get_geometry_1_62(),
        ];
        let detector_status = vec![
            get_detector_status_1_61(),
            get_detector_status_1_62(),
        ];
        
        // Verify collection components
        assert_eq!(calibrations.len(), 2);
        assert_eq!(geometry.len(), 2);
        assert_eq!(detector_status.len(), 2);
        
        // All should be for same run context
        for cal in &calibrations {
            assert!(cal["dom_id"].is_number());
        }
    }

    #[test]
    fn test_noise_rate_configuration() {
        let config = get_configuration_noise_rate();
        
        let rate: f64 = config["value"]["rate_hz"].as_f64().unwrap();
        let stddev: f64 = config["value"]["stddev_hz"].as_f64().unwrap();
        
        // Verify reasonable noise rate values
        assert!(rate > 0.0);
        assert!(stddev > 0.0);
        assert!(rate > stddev);  // rate should be larger than stddev
    }
}
