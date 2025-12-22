#!/usr/bin/env python3
"""
XML to JSON Converter for GCD Data

Converts various XML formats from the GCD system (calibration, geometry, baseline, etc.)
to JSON format compatible with the GCDServer REST API.

Supported XML formats:
  - VEMCalibOm (VEM calibration)
  - Baseline (ATWD/FADC baselines)
  - DOMCal (DOM calibration properties)
  - SPEFit (Single Photon Event fitting)
  - Geometry (DOM positions and antenna orientations)
"""

import xml.etree.ElementTree as ET
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
from pathlib import Path


class XMLConverter:
    """Base converter for XML to JSON"""
    
    @staticmethod
    def strip_text(text: str) -> str:
        """Strip and clean whitespace from XML text"""
        return text.strip() if text else ""
    
    @staticmethod
    def try_float(value: str) -> Any:
        """Try to convert string to float, fall back to string"""
        try:
            return float(XMLConverter.strip_text(value))
        except (ValueError, AttributeError):
            return XMLConverter.strip_text(value)
    
    @staticmethod
    def try_int(value: str) -> Any:
        """Try to convert string to int, fall back to float then string"""
        try:
            return int(XMLConverter.strip_text(value))
        except (ValueError, AttributeError):
            return XMLConverter.try_float(value)


class VEMCalibConverter(XMLConverter):
    """Convert VEMCalibOm XML to Calibration JSON"""
    
    @staticmethod
    def convert(xml_string: str) -> Dict[str, Any]:
        """
        Convert VEMCalibOm XML to JSON format
        
        Args:
            xml_string: XML string containing VEM calibration data
            
        Returns:
            Dict with 'metadata' and 'calibrations' keys
        """
        root = ET.fromstring(xml_string)
        
        # Extract metadata
        metadata = {
            "date": XMLConverter.strip_text(root.findtext("Date")),
            "first_run": XMLConverter.try_int(root.findtext("FirstRun")),
            "last_run": XMLConverter.try_int(root.findtext("LastRun")),
            "type": "VEM_Calibration"
        }
        
        # Extract DOM calibrations
        calibrations = []
        for dom_elem in root.findall("DOM"):
            string_id = XMLConverter.try_int(dom_elem.findtext("StringId"))
            tube_id = XMLConverter.try_int(dom_elem.findtext("TubeId"))
            
            cal_data = {
                "dom_id": f"{string_id:02d},{tube_id:02d}",
                "string_id": string_id,
                "tube_id": tube_id,
                "pe_per_vem": XMLConverter.try_float(dom_elem.findtext("pePerVEM")),
                "mu_peak_width": XMLConverter.try_float(dom_elem.findtext("muPeakWidth")),
                "sig_bkg_ratio": XMLConverter.try_float(dom_elem.findtext("sigBkgRatio")),
                "corr_factor": XMLConverter.try_float(dom_elem.findtext("corrFactor")),
            }
            
            # Optional fields
            hglg_crossover = dom_elem.findtext("hglgCrossOver")
            if hglg_crossover:
                cal_data["hglg_crossover"] = XMLConverter.try_float(hglg_crossover)
            
            muon_fit_status = dom_elem.findtext("muonFitStatus")
            if muon_fit_status:
                cal_data["muon_fit_status"] = XMLConverter.try_int(muon_fit_status)
            
            muon_fit_rchi2 = dom_elem.findtext("muonFitRchi2")
            if muon_fit_rchi2:
                cal_data["muon_fit_rchi2"] = XMLConverter.try_float(muon_fit_rchi2)
            
            hglg_fit_status = dom_elem.findtext("hglgFitStatus")
            if hglg_fit_status:
                cal_data["hglg_fit_status"] = XMLConverter.try_int(hglg_fit_status)
            
            hglg_fit_rchi2 = dom_elem.findtext("hglgFitRchi2")
            if hglg_fit_rchi2:
                cal_data["hglg_fit_rchi2"] = XMLConverter.try_float(hglg_fit_rchi2)
            
            calibrations.append(cal_data)
        
        return {
            "metadata": metadata,
            "calibrations": calibrations
        }


class BaselineConverter(XMLConverter):
    """Convert Baseline XML (ATWD/FADC baselines) to JSON"""
    
    @staticmethod
    def convert(xml_string: str) -> Dict[str, Any]:
        """
        Convert Baseline XML to JSON format
        
        Args:
            xml_string: XML string containing baseline data
            
        Returns:
            Dict with 'metadata' and 'baselines' keys
        """
        root = ET.fromstring(xml_string)
        
        # Extract date/time
        date_str = XMLConverter.strip_text(root.findtext("date"))
        time_str = XMLConverter.strip_text(root.findtext("time"))
        
        metadata = {
            "date": date_str,
            "time": time_str,
            "timestamp": f"{date_str} {time_str}",
            "type": "Baseline"
        }
        
        # Extract baseline data per DOM
        baselines = []
        for dom_elem in root.findall("dom"):
            string_id = XMLConverter.try_int(dom_elem.get("StringId"))
            tube_id = XMLConverter.try_int(dom_elem.get("TubeId"))
            
            baseline_data = {
                "dom_id": f"{string_id:02d},{tube_id:02d}",
                "string_id": string_id,
                "tube_id": tube_id,
                "atwd_a": {
                    "chan0": XMLConverter.try_float(dom_elem.findtext("ATWDChipAChan0")),
                    "chan1": XMLConverter.try_float(dom_elem.findtext("ATWDChipAChan1")),
                    "chan2": XMLConverter.try_float(dom_elem.findtext("ATWDChipAChan2")),
                },
                "atwd_b": {
                    "chan0": XMLConverter.try_float(dom_elem.findtext("ATWDChipBChan0")),
                    "chan1": XMLConverter.try_float(dom_elem.findtext("ATWDChipBChan1")),
                    "chan2": XMLConverter.try_float(dom_elem.findtext("ATWDChipBChan2")),
                },
                "fadc": XMLConverter.try_float(dom_elem.findtext("FADC")),
            }
            baselines.append(baseline_data)
        
        return {
            "metadata": metadata,
            "baselines": baselines
        }


class DOMCalConverter(XMLConverter):
    """Convert DOMCal XML (DOM calibration properties) to JSON"""
    
    @staticmethod
    def convert(xml_string: str) -> Dict[str, Any]:
        """
        Convert DOMCal XML to JSON format
        
        Args:
            xml_string: XML string containing DOM calibration data
            
        Returns:
            Dict with 'metadata' and 'domcals' keys
        """
        root = ET.fromstring(xml_string)
        
        metadata = {
            "date": XMLConverter.strip_text(root.findtext("Date")),
            "type": "DOMCal"
        }
        
        domcals = []
        for dom_elem in root.findall("DOM"):
            string_id = XMLConverter.try_int(dom_elem.findtext("StringId"))
            tube_id = XMLConverter.try_int(dom_elem.findtext("TubeId"))
            
            domcal_data = {
                "dom_id": f"{string_id:02d},{tube_id:02d}",
                "string_id": string_id,
                "tube_id": tube_id,
                "atwd_gain": [
                    XMLConverter.try_float(dom_elem.findtext("ATWDGain0")),
                    XMLConverter.try_float(dom_elem.findtext("ATWDGain1")),
                    XMLConverter.try_float(dom_elem.findtext("ATWDGain2")),
                ],
                "atwd_freq": [
                    XMLConverter.try_float(dom_elem.findtext("ATWDFrequency0")),
                    XMLConverter.try_float(dom_elem.findtext("ATWDFrequency1")),
                    XMLConverter.try_float(dom_elem.findtext("ATWDFrequency2")),
                ],
                "fadc_gain": XMLConverter.try_float(dom_elem.findtext("FADCGain")),
                "fadc_freq": XMLConverter.try_float(dom_elem.findtext("FADCFrequency")),
                "pmt_gain": XMLConverter.try_float(dom_elem.findtext("PMTGain")),
                "transit_time": XMLConverter.try_float(dom_elem.findtext("TransitTime")),
                "relative_pmt_gain": XMLConverter.try_float(dom_elem.findtext("RelativePMTGain", default="1.0")),
            }
            domcals.append(domcal_data)
        
        return {
            "metadata": metadata,
            "domcals": domcals
        }


class SPEFitConverter(XMLConverter):
    """Convert SPEFit XML (Single Photon Event fitting) to JSON"""
    
    @staticmethod
    def convert(xml_string: str) -> Dict[str, Any]:
        """
        Convert SPEFit XML to JSON format
        
        Args:
            xml_string: XML string containing SPE fit data
            
        Returns:
            Dict with 'metadata' and 'spe_fits' keys
        """
        root = ET.fromstring(xml_string)
        
        metadata = {
            "date": XMLConverter.strip_text(root.findtext("Date")),
            "type": "SPEFit"
        }
        
        spe_fits = []
        for dom_elem in root.findall("DOM"):
            string_id = XMLConverter.try_int(dom_elem.findtext("StringId"))
            tube_id = XMLConverter.try_int(dom_elem.findtext("TubeId"))
            
            spe_fit_data = {
                "dom_id": f"{string_id:02d},{tube_id:02d}",
                "string_id": string_id,
                "tube_id": tube_id,
            }
            
            # ATWD fit (if exists)
            atwd_elem = dom_elem.find("ATWDFit")
            if atwd_elem is not None:
                spe_fit_data["atwd_fit"] = {
                    "chi2": XMLConverter.try_float(atwd_elem.findtext("Chi2")),
                    "status": XMLConverter.try_int(atwd_elem.findtext("Status", default="0")),
                }
            
            # FADC fit (if exists)
            fadc_elem = dom_elem.find("FADCFit")
            if fadc_elem is not None:
                spe_fit_data["fadc_fit"] = {
                    "chi2": XMLConverter.try_float(fadc_elem.findtext("Chi2")),
                    "status": XMLConverter.try_int(fadc_elem.findtext("Status", default="0")),
                }
            
            spe_fits.append(spe_fit_data)
        
        return {
            "metadata": metadata,
            "spe_fits": spe_fits
        }


class GeometryConverter(XMLConverter):
    """Convert Geometry XML to JSON"""
    
    @staticmethod
    def convert(xml_string: str) -> Dict[str, Any]:
        """
        Convert Geometry XML to JSON format
        
        Args:
            xml_string: XML string containing geometry data
            
        Returns:
            Dict with 'metadata' and 'geometry' keys
        """
        root = ET.fromstring(xml_string)
        
        metadata = {
            "date": XMLConverter.strip_text(root.findtext("Date")),
            "type": "Geometry"
        }
        
        geometry = []
        
        # Parse DOMs
        for dom_elem in root.findall(".//DOM"):
            string_id = XMLConverter.try_int(dom_elem.findtext("StringId"))
            tube_id = XMLConverter.try_int(dom_elem.findtext("TubeId"))
            
            position_elem = dom_elem.find("Position")
            if position_elem is not None:
                geo_data = {
                    "dom_id": f"{string_id:02d},{tube_id:02d}",
                    "string_id": string_id,
                    "tube_id": tube_id,
                    "position": {
                        "x": XMLConverter.try_float(position_elem.findtext("x")),
                        "y": XMLConverter.try_float(position_elem.findtext("y")),
                        "z": XMLConverter.try_float(position_elem.findtext("z")),
                    }
                }
                
                # Optional orientation
                orientation_elem = dom_elem.find("Orientation")
                if orientation_elem is not None:
                    geo_data["orientation"] = {
                        "theta": XMLConverter.try_float(orientation_elem.findtext("theta")),
                        "phi": XMLConverter.try_float(orientation_elem.findtext("phi")),
                    }
                
                geometry.append(geo_data)
        
        # Parse Tanks
        for tank_elem in root.findall(".//Tank"):
            tank_id = XMLConverter.strip_text(tank_elem.findtext("TankId"))
            tank_label = XMLConverter.strip_text(tank_elem.findtext("TankLabel"))
            
            position_elem = tank_elem.find("Position")
            if position_elem is not None:
                tank_data = {
                    "tank_id": tank_id,
                    "tank_label": tank_label,
                    "position": {
                        "x": XMLConverter.try_float(position_elem.findtext("x")),
                        "y": XMLConverter.try_float(position_elem.findtext("y")),
                        "z": XMLConverter.try_float(position_elem.findtext("z")),
                    }
                }
                geometry.append(tank_data)
        
        return {
            "metadata": metadata,
            "geometry": geometry
        }


class AutoDetectConverter:
    """Automatically detect XML type and convert appropriately"""
    
    CONVERTERS = {
        'vemcalibom': VEMCalibConverter,
        'baseline': BaselineConverter,
        'domcal': DOMCalConverter,
        'spefit': SPEFitConverter,
        'geometry': GeometryConverter,
    }
    
    @staticmethod
    def detect_type(xml_string: str) -> Optional[str]:
        """
        Detect XML type based on root element and content
        
        Args:
            xml_string: XML string to detect
            
        Returns:
            Type string or None if undetected
        """
        root_elem = ET.fromstring(xml_string).tag.lower()
        
        if 'vemcalib' in root_elem:
            return 'vemcalibom'
        elif 'baseline' in root_elem:
            return 'baseline'
        elif 'domcal' in root_elem:
            return 'domcal'
        elif 'spefit' in root_elem or 'spefitom' in root_elem:
            return 'spefit'
        elif 'geometry' in root_elem:
            return 'geometry'
        
        return None
    
    @staticmethod
    def convert(xml_string: str, xml_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert XML to JSON, auto-detecting type if not specified
        
        Args:
            xml_string: XML string to convert
            xml_type: Optional type override (vemcalibom, baseline, domcal, spefit, geometry)
            
        Returns:
            Dict with converted data
            
        Raises:
            ValueError: If type cannot be determined or is unsupported
        """
        if xml_type is None:
            xml_type = AutoDetectConverter.detect_type(xml_string)
            if xml_type is None:
                raise ValueError("Could not auto-detect XML type. Please specify --type")
        
        xml_type = xml_type.lower()
        if xml_type not in AutoDetectConverter.CONVERTERS:
            raise ValueError(
                f"Unsupported XML type: {xml_type}\n"
                f"Supported types: {', '.join(AutoDetectConverter.CONVERTERS.keys())}"
            )
        
        converter = AutoDetectConverter.CONVERTERS[xml_type]
        return converter.convert(xml_string)


def main():
    """Command-line interface for XML to JSON conversion"""
    parser = argparse.ArgumentParser(
        description="Convert GCD XML data to JSON format for REST API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect type and convert
  %(prog)s input.xml
  
  # Specify type explicitly
  %(prog)s input.xml --type vemcalibom
  
  # Convert and save to output file
  %(prog)s input.xml -o output.json
  
  # Pretty-print output
  %(prog)s input.xml --pretty
  
Supported XML types:
  vemcalibom  - VEM calibration data
  baseline    - ATWD/FADC baseline data
  domcal      - DOM calibration properties
  spefit      - Single photon event fitting
  geometry    - Detector geometry
        """
    )
    
    parser.add_argument('input', help='Input XML file')
    parser.add_argument(
        '-o', '--output',
        help='Output JSON file (default: stdout)',
        default=None
    )
    parser.add_argument(
        '-t', '--type',
        choices=['vemcalibom', 'baseline', 'domcal', 'spefit', 'geometry'],
        help='XML type (auto-detected if not specified)',
        default=None
    )
    parser.add_argument(
        '-p', '--pretty',
        action='store_true',
        help='Pretty-print JSON output'
    )
    
    args = parser.parse_args()
    
    # Read XML file
    try:
        with open(args.input, 'r') as f:
            xml_string = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Convert
    try:
        result = AutoDetectConverter.convert(xml_string, args.type)
    except Exception as e:
        print(f"Error converting XML: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Format output
    indent = 2 if args.pretty else None
    json_output = json.dumps(result, indent=indent)
    
    # Write output
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"Converted and saved to: {args.output}", file=sys.stderr)
        except IOError as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(json_output)


if __name__ == '__main__':
    main()
