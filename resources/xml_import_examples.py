#!/usr/bin/env python3
"""
XML Import Examples - Real-world usage patterns

Demonstrates various ways to convert XML data and import into REST API.
"""

import json
from pathlib import Path
from xml_to_json_converter import AutoDetectConverter, VEMCalibConverter, BaselineConverter
from gcd_xml_import import XMLImportPipeline


# ============================================================================
# Example 1: Basic XML to JSON Conversion
# ============================================================================

def example_1_basic_conversion():
    """Convert XML file to JSON and print"""
    print("\n=== Example 1: Basic XML to JSON Conversion ===\n")
    
    vemcal_xml = """<?xml version="1.0" encoding="UTF-8"?>
<VEMCalibOm>
  <Date> 2014-01-01 00:39:07 </Date>
  <FirstRun> 123614 </FirstRun>
  <LastRun> 123968 </LastRun>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 61 </TubeId>
    <pePerVEM> 116.274 </pePerVEM>
    <muPeakWidth> 20.3121 </muPeakWidth>
    <sigBkgRatio> 10.306 </sigBkgRatio>
    <corrFactor> 1 </corrFactor>
    <hglgCrossOver> 2361.66 </hglgCrossOver>
    <muonFitStatus> 0 </muonFitStatus>
    <muonFitRchi2> 1.42718 </muonFitRchi2>
    <hglgFitStatus> 0 </hglgFitStatus>
    <hglgFitRchi2> 2.44815 </hglgFitRchi2>
  </DOM>
</VEMCalibOm>
"""
    
    # Convert
    result = VEMCalibConverter.convert(vemcal_xml)
    
    # Display
    print("Metadata:")
    print(json.dumps(result['metadata'], indent=2))
    print(f"\nCalibrations: {len(result['calibrations'])} DOM(s)")
    print(json.dumps(result['calibrations'][0], indent=2))


# ============================================================================
# Example 2: Auto-detect XML Type
# ============================================================================

def example_2_auto_detect():
    """Auto-detect XML type without specifying format"""
    print("\n=== Example 2: Auto-detect XML Type ===\n")
    
    xml_files = {
        'vemcal.xml': """<?xml version="1.0" encoding="UTF-8"?>
<VEMCalibOm>
  <Date> 2014-01-01 00:39:07 </Date>
  <FirstRun> 123614 </FirstRun>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 61 </TubeId>
    <pePerVEM> 116.274 </pePerVEM>
  </DOM>
</VEMCalibOm>
""",
        'baseline.xml': """<?xml version="1.0" ?>
<baselines>
    <date>2016-03-18</date>
    <time>16:33:41</time>
    <dom StringId="1" TubeId="61">
        <ATWDChipAChan0>125.068580</ATWDChipAChan0>
        <FADC>137.185200</FADC>
    </dom>
</baselines>
"""
    }
    
    for filename, xml_string in xml_files.items():
        # Auto-detect type
        detected_type = AutoDetectConverter.detect_type(xml_string)
        print(f"{filename}: Detected type = {detected_type}")
        
        # Convert
        result = AutoDetectConverter.convert(xml_string)
        print(f"  Metadata: {result['metadata']['type']}")
        
        # Show record counts
        for key in result:
            if isinstance(result[key], list):
                print(f"  Records: {len(result[key])} in '{key}'")
        print()


# ============================================================================
# Example 3: Batch Processing Multiple Files
# ============================================================================

def example_3_batch_processing():
    """Process multiple XML files in batch"""
    print("\n=== Example 3: Batch Processing ===\n")
    
    # Simulate multiple XML files
    xml_data = {
        'vem1.xml': """<?xml version="1.0" encoding="UTF-8"?>
<VEMCalibOm>
  <Date> 2014-01-01 </Date>
  <FirstRun> 123614 </FirstRun>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 61 </TubeId>
    <pePerVEM> 116.274 </pePerVEM>
  </DOM>
</VEMCalibOm>
""",
        'vem2.xml': """<?xml version="1.0" encoding="UTF-8"?>
<VEMCalibOm>
  <Date> 2014-02-01 </Date>
  <FirstRun> 125000 </FirstRun>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 62 </TubeId>
    <pePerVEM> 120.500 </pePerVEM>
  </DOM>
</VEMCalibOm>
"""
    }
    
    results = []
    total_records = 0
    
    for filename, xml_string in xml_data.items():
        converted = AutoDetectConverter.convert(xml_string)
        record_count = len(converted.get('calibrations', []))
        results.append({
            'file': filename,
            'type': converted['metadata']['type'],
            'records': record_count
        })
        total_records += record_count
        print(f"✓ {filename}: {record_count} records")
    
    print(f"\nBatch Summary:")
    print(f"  Files processed: {len(results)}")
    print(f"  Total records: {total_records}")


# ============================================================================
# Example 4: Convert and Save to JSON Files
# ============================================================================

def example_4_save_json():
    """Convert XML and save to JSON files"""
    print("\n=== Example 4: Convert and Save JSON ===\n")
    
    vemcal_xml = """<?xml version="1.0" encoding="UTF-8"?>
<VEMCalibOm>
  <Date> 2014-01-01 </Date>
  <FirstRun> 123614 </FirstRun>
  <LastRun> 123968 </LastRun>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 61 </TubeId>
    <pePerVEM> 116.274 </pePerVEM>
    <muPeakWidth> 20.3121 </muPeakWidth>
    <sigBkgRatio> 10.306 </sigBkgRatio>
  </DOM>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 62 </TubeId>
    <pePerVEM> 120.500 </pePerVEM>
    <muPeakWidth> 21.0000 </muPeakWidth>
    <sigBkgRatio> 11.000 </sigBkgRatio>
  </DOM>
</VEMCalibOm>
"""
    
    # Convert
    result = VEMCalibConverter.convert(vemcal_xml)
    
    # Save to file
    output_file = Path('/tmp/vem_calib_example.json')
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Saved to: {output_file}")
    print(f"File size: {output_file.stat().st_size} bytes")
    print(f"Records: {len(result['calibrations'])}")
    
    # Show sample
    print(f"\nFirst record:")
    print(json.dumps(result['calibrations'][0], indent=2))


# ============================================================================
# Example 5: Accessing Converted Data Programmatically
# ============================================================================

def example_5_data_access():
    """Access converted data programmatically"""
    print("\n=== Example 5: Data Access ===\n")
    
    vemcal_xml = """<?xml version="1.0" encoding="UTF-8"?>
<VEMCalibOm>
  <Date> 2014-01-01 </Date>
  <FirstRun> 123614 </FirstRun>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 61 </TubeId>
    <pePerVEM> 116.274 </pePerVEM>
    <muPeakWidth> 20.3121 </muPeakWidth>
    <sigBkgRatio> 10.306 </sigBkgRatio>
  </DOM>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 62 </TubeId>
    <pePerVEM> 120.500 </pePerVEM>
    <muPeakWidth> 21.0000 </muPeakWidth>
    <sigBkgRatio> 11.000 </sigBkgRatio>
  </DOM>
</VEMCalibOm>
"""
    
    result = VEMCalibConverter.convert(vemcal_xml)
    
    # Access metadata
    print("Metadata:")
    print(f"  Date: {result['metadata']['date']}")
    print(f"  First Run: {result['metadata']['first_run']}")
    print(f"  Type: {result['metadata']['type']}")
    
    # Iterate over calibrations
    print(f"\nCalibrations ({len(result['calibrations'])} DOMs):")
    for cal in result['calibrations']:
        print(f"  DOM {cal['dom_id']}:")
        print(f"    pe_per_vem: {cal['pe_per_vem']}")
        print(f"    mu_peak_width: {cal['mu_peak_width']}")
        print(f"    sig_bkg_ratio: {cal['sig_bkg_ratio']}")
    
    # Filter data
    print(f"\nDOMs with pe_per_vem > 116.0:")
    high_pe = [c for c in result['calibrations'] if c['pe_per_vem'] > 116.0]
    for cal in high_pe:
        print(f"  {cal['dom_id']}: {cal['pe_per_vem']}")


# ============================================================================
# Example 6: Error Handling
# ============================================================================

def example_6_error_handling():
    """Demonstrate error handling"""
    print("\n=== Example 6: Error Handling ===\n")
    
    test_cases = [
        ('Valid XML', """<?xml version="1.0" encoding="UTF-8"?>
<VEMCalibOm>
  <Date> 2014-01-01 </Date>
  <FirstRun> 123614 </FirstRun>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 61 </TubeId>
    <pePerVEM> 116.274 </pePerVEM>
  </DOM>
</VEMCalibOm>
"""),
        ('Invalid XML', '<root><unclosed>'),
        ('Unknown type', """<?xml version="1.0"?>
<unknown_element>
  <data>test</data>
</unknown_element>
"""),
    ]
    
    for test_name, xml_string in test_cases:
        print(f"Testing: {test_name}")
        try:
            result = AutoDetectConverter.convert(xml_string)
            print(f"  ✓ Success: {result['metadata']['type']}")
        except ValueError as e:
            print(f"  ⚠ ValueError: {e}")
        except Exception as e:
            print(f"  ✗ Error: {type(e).__name__}: {e}")
        print()


# ============================================================================
# Example 7: Baseline to Detector Status
# ============================================================================

def example_7_baseline_conversion():
    """Convert baseline data to detector status format"""
    print("\n=== Example 7: Baseline to Detector Status ===\n")
    
    baseline_xml = """<?xml version="1.0" ?>
<baselines>
    <date>2016-03-18</date>
    <time>16:33:41</time>
    <dom StringId="1" TubeId="61">
        <ATWDChipAChan0>125.068580</ATWDChipAChan0>
        <ATWDChipAChan1>136.172671</ATWDChipAChan1>
        <ATWDChipAChan2>136.172799</ATWDChipAChan2>
        <ATWDChipBChan0>129.730441</ATWDChipBChan0>
        <ATWDChipBChan1>134.035253</ATWDChipBChan1>
        <ATWDChipBChan2>136.943712</ATWDChipBChan2>
        <FADC>137.185200</FADC>
    </dom>
    <dom StringId="1" TubeId="62">
        <ATWDChipAChan0>126.925628</ATWDChipAChan0>
        <ATWDChipAChan1>131.162387</ATWDChipAChan1>
        <ATWDChipAChan2>132.048000</ATWDChipAChan2>
        <ATWDChipBChan0>129.852887</ATWDChipBChan0>
        <ATWDChipBChan1>136.098590</ATWDChipBChan1>
        <ATWDChipBChan2>138.041781</ATWDChipBChan2>
        <FADC>126.028301</FADC>
    </dom>
</baselines>
"""
    
    # Convert
    result = BaselineConverter.convert(baseline_xml)
    
    print("Baseline Metadata:")
    print(f"  Date: {result['metadata']['date']}")
    print(f"  Time: {result['metadata']['time']}")
    print(f"  Type: {result['metadata']['type']}")
    
    print(f"\nBaseline Data ({len(result['baselines'])} DOMs):")
    for baseline in result['baselines']:
        print(f"\nDOM {baseline['dom_id']}:")
        print(f"  ATWD A: {baseline['atwd_a']['chan0']}, {baseline['atwd_a']['chan1']}, {baseline['atwd_a']['chan2']}")
        print(f"  ATWD B: {baseline['atwd_b']['chan0']}, {baseline['atwd_b']['chan1']}, {baseline['atwd_b']['chan2']}")
        print(f"  FADC:   {baseline['fadc']}")


# ============================================================================
# Example 8: Building REST API Payloads
# ============================================================================

def example_8_rest_payloads():
    """Build REST API payloads from converted data"""
    print("\n=== Example 8: Building REST API Payloads ===\n")
    
    vemcal_xml = """<?xml version="1.0" encoding="UTF-8"?>
<VEMCalibOm>
  <Date> 2014-01-01 </Date>
  <FirstRun> 123614 </FirstRun>
  <DOM>
    <StringId> 1 </StringId>
    <TubeId> 61 </TubeId>
    <pePerVEM> 116.274 </pePerVEM>
    <muPeakWidth> 20.3121 </muPeakWidth>
    <sigBkgRatio> 10.306 </sigBkgRatio>
  </DOM>
</VEMCalibOm>
"""
    
    result = VEMCalibConverter.convert(vemcal_xml)
    
    # Build calibration endpoint payload
    print("Calibration Endpoint Payload (POST /calibration):")
    for cal in result['calibrations']:
        payload = {
            'dom_id': cal['dom_id'],
            'domcal': {
                'atwd_gain': [1.0, 1.0, 1.0],  # Would come from other source
                'atwd_freq': [1.2e7, 1.2e7, 1.2e7],
                'fadc_gain': 1.5,
                'fadc_freq': 2.0e8,
                'pmt_gain': 1.2e7,
                'transit_time': 1000.0,
                'relative_pmt_gain': 0.95
            },
            'timestamp': result['metadata']['date']
        }
        print(json.dumps(payload, indent=2))
        break  # Just show first


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all examples"""
    print("=" * 70)
    print("XML Conversion Examples")
    print("=" * 70)
    
    examples = [
        example_1_basic_conversion,
        example_2_auto_detect,
        example_3_batch_processing,
        example_4_save_json,
        example_5_data_access,
        example_6_error_handling,
        example_7_baseline_conversion,
        example_8_rest_payloads,
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Error in {example_func.__name__}: {e}")
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == '__main__':
    main()
