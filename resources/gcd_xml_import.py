#!/usr/bin/env python3
"""
GCD XML Upload Tool - Wrapper for converting and uploading XML data to REST API

Combines XML-to-JSON conversion with REST API client for seamless data import.

Usage:
    # Convert and upload VEM calibration
    gcd_xml_upload.py vem_calib.xml --endpoint calibration --api-url http://localhost:8080
    
    # Convert and save without uploading
    gcd_xml_upload.py baseline.xml --convert-only -o baseline.json
    
    # Batch process multiple files
    gcd_xml_upload.py *.xml --batch
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from xml_to_json_converter import AutoDetectConverter


class XMLUploader:
    """Upload converted XML data to GCDServer REST API"""
    
    def __init__(self, api_url: str, token: Optional[str] = None):
        """
        Initialize uploader with API URL and optional auth token
        
        Args:
            api_url: Base URL of GCDServer REST API (e.g., http://localhost:8080)
            token: OAuth2 bearer token (optional)
        """
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def upload_calibration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload calibration data to /calibration endpoint
        
        Args:
            data: Converted JSON data with 'calibrations' key
            
        Returns:
            Response from API
        """
        endpoint = f"{self.api_url}/calibration"
        
        # Extract individual calibrations and POST each one
        results = []
        for cal in data.get('calibrations', []):
            response = self._post(endpoint, cal)
            results.append(response)
        
        return {
            "endpoint": "/calibration",
            "count": len(results),
            "results": results
        }
    
    def upload_detector_status(self, data: Dict[str, Any], run_number: int) -> Dict[str, Any]:
        """
        Upload detector status data to /detector-status endpoint
        
        Args:
            data: Converted JSON data with 'baselines' or equivalent key
            run_number: Run number for detector status
            
        Returns:
            Response from API
        """
        endpoint = f"{self.api_url}/detector-status"
        
        # Convert baselines to detector status format
        results = []
        for item in data.get('baselines', []):
            status = {
                "run_number": run_number,
                "dom_id": item.get('tube_id', ''),
                "status": "operational",
                "timestamp": data.get('metadata', {}).get('timestamp')
            }
            response = self._post(endpoint, status)
            results.append(response)
        
        return {
            "endpoint": "/detector-status",
            "count": len(results),
            "results": results
        }
    
    def upload_geometry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload geometry data to /geometry endpoint
        
        Args:
            data: Converted JSON data with 'geometry' key
            
        Returns:
            Response from API
        """
        endpoint = f"{self.api_url}/geometry"
        
        results = []
        for geo in data.get('geometry', []):
            response = self._post(endpoint, geo)
            results.append(response)
        
        return {
            "endpoint": "/geometry",
            "count": len(results),
            "results": results
        }
    
    def upload_run_metadata(self, run_number: int, start_time: str, 
                           end_time: Optional[str] = None,
                           config_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create run metadata entry (needed for run-aware GCD generation)
        
        Args:
            run_number: Run number identifier
            start_time: Run start time (ISO format)
            end_time: Run end time (ISO format, optional)
            config_name: Configuration name used for run
            
        Returns:
            Response from API
        """
        endpoint = f"{self.api_url}/run-metadata"
        
        payload = {
            "run_number": run_number,
            "start_time": start_time,
            "end_time": end_time,
            "configuration_name": config_name
        }
        
        return self._post(endpoint, payload)
    
    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST data to endpoint
        
        Args:
            endpoint: Full endpoint URL
            data: Data to POST
            
        Returns:
            Response data
        """
        try:
            response = self.session.post(endpoint, json=data)
            response.raise_for_status()
            return {
                "status": response.status_code,
                "success": True,
                "data": response.json() if response.text else {}
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": getattr(e.response, 'status_code', None),
                "success": False,
                "error": str(e)
            }


class XMLImportPipeline:
    """Full pipeline for XML import: detect → convert → upload"""
    
    def __init__(self, api_url: str, token: Optional[str] = None):
        """Initialize pipeline with API configuration"""
        self.converter = AutoDetectConverter()
        self.uploader = XMLUploader(api_url, token)
    
    def import_file(self, xml_file: Path, xml_type: Optional[str] = None,
                   endpoint: Optional[str] = None,
                   run_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Full import pipeline: read XML → convert → upload
        
        Args:
            xml_file: Path to XML file
            xml_type: XML type (auto-detect if None)
            endpoint: Target endpoint (auto-detect from type if None)
            run_number: Run number (for detector status)
            
        Returns:
            Import result
        """
        # Read and convert
        try:
            with open(xml_file, 'r') as f:
                xml_string = f.read()
        except IOError as e:
            return {"success": False, "error": f"Failed to read file: {e}"}
        
        try:
            converted = self.converter.convert(xml_string, xml_type)
        except Exception as e:
            return {"success": False, "error": f"Conversion failed: {e}"}
        
        # Determine endpoint if not specified
        detected_type = converted.get('metadata', {}).get('type', '').lower()
        if endpoint is None:
            endpoint = self._infer_endpoint(detected_type)
        
        # Upload
        try:
            if endpoint == 'calibration':
                result = self.uploader.upload_calibration(converted)
            elif endpoint == 'detector-status':
                if run_number is None:
                    return {"success": False, "error": "run_number required for detector-status"}
                result = self.uploader.upload_detector_status(converted, run_number)
            elif endpoint == 'geometry':
                result = self.uploader.upload_geometry(converted)
            else:
                return {"success": False, "error": f"Unknown endpoint: {endpoint}"}
            
            return {
                "success": True,
                "file": str(xml_file),
                "type": detected_type,
                "endpoint": endpoint,
                "upload_result": result
            }
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {e}"}
    
    @staticmethod
    def _infer_endpoint(xml_type: str) -> str:
        """Map XML type to API endpoint"""
        mapping = {
            'vem_calibration': 'calibration',
            'vemcalibom': 'calibration',
            'domcal': 'calibration',
            'baseline': 'detector-status',
            'spefit': 'calibration',
            'geometry': 'geometry',
        }
        return mapping.get(xml_type, 'unknown')


def main():
    """Command-line interface for XML import"""
    parser = argparse.ArgumentParser(
        description="Convert and upload GCD XML data to REST API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload VEM calibration
  %(prog)s vem_calib.xml --api-url http://localhost:8080 --token YOUR_TOKEN
  
  # Batch upload multiple files
  %(prog)s *.xml --batch --api-url http://localhost:8080 --token YOUR_TOKEN
  
  # Convert only (no upload)
  %(prog)s baseline.xml --convert-only -o baseline.json
  
  # Upload detector status with run number
  %(prog)s baseline.xml --endpoint detector-status --run 137292
        """
    )
    
    parser.add_argument('files', nargs='+', help='XML file(s) to import')
    parser.add_argument(
        '--api-url',
        default='http://localhost:8080',
        help='GCDServer API URL (default: http://localhost:8080)'
    )
    parser.add_argument(
        '--token',
        help='OAuth2 bearer token (required for upload)'
    )
    parser.add_argument(
        '-t', '--type',
        choices=['vemcalibom', 'baseline', 'domcal', 'spefit', 'geometry'],
        help='XML type (auto-detected if not specified)'
    )
    parser.add_argument(
        '-e', '--endpoint',
        choices=['calibration', 'detector-status', 'geometry'],
        help='Target endpoint (auto-detected if not specified)'
    )
    parser.add_argument(
        '-r', '--run',
        type=int,
        help='Run number (required for detector-status)'
    )
    parser.add_argument(
        '--convert-only',
        action='store_true',
        help='Convert to JSON without uploading'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output JSON file (used with --convert-only)'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process multiple files in batch'
    )
    parser.add_argument(
        '-p', '--pretty',
        action='store_true',
        help='Pretty-print JSON output'
    )
    
    args = parser.parse_args()
    
    # Process files
    pipeline = XMLImportPipeline(args.api_url, args.token) if not args.convert_only else None
    
    results = []
    for file_pattern in args.files:
        # Support glob patterns
        files = list(Path('.').glob(file_pattern)) if '*' in file_pattern else [Path(file_pattern)]
        
        for xml_file in files:
            if args.convert_only:
                # Conversion only
                try:
                    with open(xml_file, 'r') as f:
                        xml_string = f.read()
                    converted = AutoDetectConverter.convert(xml_string, args.type)
                    
                    indent = 2 if args.pretty else None
                    json_output = json.dumps(converted, indent=indent)
                    
                    if args.output:
                        with open(args.output, 'w') as f:
                            f.write(json_output)
                        print(f"Converted: {xml_file} → {args.output}")
                    else:
                        print(json_output)
                    
                    results.append({"file": str(xml_file), "success": True})
                except Exception as e:
                    print(f"Error converting {xml_file}: {e}", file=sys.stderr)
                    results.append({"file": str(xml_file), "success": False, "error": str(e)})
            else:
                # Full import pipeline
                if not args.token:
                    print("Error: --token required for upload", file=sys.stderr)
                    sys.exit(1)
                
                result = pipeline.import_file(
                    xml_file,
                    xml_type=args.type,
                    endpoint=args.endpoint,
                    run_number=args.run
                )
                results.append(result)
                
                if result['success']:
                    print(f"✓ Imported: {xml_file}")
                else:
                    print(f"✗ Failed: {xml_file} - {result.get('error')}")
    
    # Summary
    if args.batch or len(files) > 1:
        successful = sum(1 for r in results if r.get('success'))
        total = len(results)
        print(f"\nSummary: {successful}/{total} files processed successfully")
    
    sys.exit(0 if all(r.get('success') for r in results) else 1)


if __name__ == '__main__':
    main()
