#!/usr/bin/env python3
"""
Analyze Training Data Script
Check the contents of face training data files
"""

import pickle
import numpy as np
from pathlib import Path
from collections import Counter

class TrainingDataAnalyzer:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.names_file = self.data_dir / "names.pkl"
        self.faces_file = self.data_dir / "faces_data.pkl"
    
    def analyze_names_data(self):
        """Analyze names.pkl file"""
        print("[INFO] Analyzing names.pkl...")
        
        if not self.names_file.exists():
            print("❌ names.pkl not found!")
            return None
        
        try:
            with open(self.names_file, 'rb') as f:
                names_data = pickle.load(f)
            
            print(f"[SUCCESS] Successfully loaded names.pkl")
            print(f"[INFO] Data type: {type(names_data)}")
            print(f"[INFO] Total entries: {len(names_data)}")
            
            # Count unique names
            if isinstance(names_data, (list, tuple)):
                name_counts = Counter(names_data)
                unique_names = list(name_counts.keys())
                
                print(f"[INFO] Unique names: {len(unique_names)}")
                print(f"[INFO] Names list: {unique_names}")
                
                print("\n[INFO] Name frequency:")
                for name, count in name_counts.most_common():
                    print(f"   {name}: {count} samples")
                
                return names_data, unique_names
            else:
                print(f"[WARNING] Unexpected data format: {type(names_data)}")
                return names_data, []
                
        except Exception as e:
            print(f"[ERROR] Error loading names.pkl: {e}")
            return None, []
    
    def analyze_faces_data(self):
        """Analyze faces_data.pkl file"""
        print("\n[INFO] Analyzing faces_data.pkl...")
        
        if not self.faces_file.exists():
            print("[ERROR] faces_data.pkl not found!")
            return None
        
        try:
            with open(self.faces_file, 'rb') as f:
                faces_data = pickle.load(f)
            
            print(f"[SUCCESS] Successfully loaded faces_data.pkl")
            print(f"[INFO] Data type: {type(faces_data)}")
            
            if isinstance(faces_data, np.ndarray):
                print(f"[INFO] Shape: {faces_data.shape}")
                print(f"[INFO] Data type: {faces_data.dtype}")
                print(f"[INFO] Total face samples: {faces_data.shape[0]}")
                print(f"[INFO] Features per face: {faces_data.shape[1] if len(faces_data.shape) > 1 else 'N/A'}")
                
                # Check for expected feature size
                expected_features = 50 * 50 * 3  # 7500 for color images
                expected_features_gray = 50 * 50  # 2500 for grayscale
                
                if len(faces_data.shape) > 1:
                    actual_features = faces_data.shape[1]
                    if actual_features == expected_features:
                        print("[SUCCESS] Feature size matches color images (50x50x3)")
                    elif actual_features == expected_features_gray:
                        print("[SUCCESS] Feature size matches grayscale images (50x50)")
                    else:
                        print(f"[WARNING] Unexpected feature size: {actual_features}")
                        print(f"   Expected: {expected_features} (color) or {expected_features_gray} (grayscale)")
                
                return faces_data
            else:
                print(f"[WARNING] Unexpected data format: {type(faces_data)}")
                return faces_data
                
        except Exception as e:
            print(f"[ERROR] Error loading faces_data.pkl: {e}")
            return None
    
    def check_data_consistency(self, names_data, faces_data):
        """Check if names and faces data are consistent"""
        print("\n[INFO] Checking data consistency...")
        
        if names_data is None or faces_data is None:
            print("[ERROR] Cannot check consistency - missing data")
            return False
        
        names_count = len(names_data) if isinstance(names_data, (list, tuple)) else 0
        faces_count = faces_data.shape[0] if isinstance(faces_data, np.ndarray) and len(faces_data.shape) > 0 else 0
        
        print(f"[INFO] Names entries: {names_count}")
        print(f"[INFO] Face samples: {faces_count}")
        
        if names_count == faces_count:
            print("[SUCCESS] Data is consistent - names and faces match")
            return True
        else:
            print("[ERROR] Data inconsistency detected!")
            print(f"   Names: {names_count}, Faces: {faces_count}")
            return False
    
    def diagnose_issues(self, names_data, unique_names):
        """Diagnose potential issues"""
        print("\n[INFO] Diagnosing potential issues...")
        
        issues = []
        
        # Check if only one unique name
        if len(unique_names) == 1:
            issues.append(f"Only 1 unique name found: '{unique_names[0]}'")
            issues.append("This suggests face registration may have overwritten previous data")
        
        # Check for duplicate names
        if isinstance(names_data, (list, tuple)):
            name_counts = Counter(names_data)
            duplicates = {name: count for name, count in name_counts.items() if count > 20}
            if duplicates:
                issues.append(f"Excessive samples for some names: {duplicates}")
        
        # Check file sizes
        names_size = self.names_file.stat().st_size if self.names_file.exists() else 0
        faces_size = self.faces_file.stat().st_size if self.faces_file.exists() else 0
        
        print(f"[INFO] File sizes:")
        print(f"   names.pkl: {names_size:,} bytes")
        print(f"   faces_data.pkl: {faces_size:,} bytes")
        
        if faces_size < 1000:  # Very small file
            issues.append("faces_data.pkl is very small - may contain insufficient data")
        
        if issues:
            print("\n[WARNING] Issues found:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("[SUCCESS] No obvious issues detected")
        
        return issues
    
    def suggest_fixes(self, issues):
        """Suggest fixes for detected issues"""
        if not issues:
            return
        
        print("\n[SOLUTION] Suggested fixes:")
        
        for issue in issues:
            if "Only 1 unique name" in issue:
                print("   1. Re-run face registration for all users:")
                print("      python src/add_faces_rpi.py")
                print("   2. Make sure to register different people, not the same person multiple times")
            
            elif "overwritten" in issue:
                print("   3. Check if face registration is appending data correctly")
                print("   4. Backup existing data before adding new faces")
            
            elif "Excessive samples" in issue:
                print("   5. Consider reducing samples per person (20-30 is usually enough)")
            
            elif "insufficient data" in issue:
                print("   6. Re-register faces with more samples per person")
    
    def run_analysis(self):
        """Run complete analysis"""
        print("[ANALYSIS] Training Data Analysis")
        print("=" * 50)
        
        # Analyze names data
        names_data, unique_names = self.analyze_names_data()
        
        # Analyze faces data
        faces_data = self.analyze_faces_data()
        
        # Check consistency
        is_consistent = self.check_data_consistency(names_data, faces_data)
        
        # Diagnose issues
        issues = self.diagnose_issues(names_data, unique_names)
        
        # Suggest fixes
        self.suggest_fixes(issues)
        
        print("\n" + "=" * 50)
        print("[SUMMARY] Analysis Summary:")
        print(f"   Unique faces registered: {len(unique_names)}")
        print(f"   Total samples: {len(names_data) if names_data else 0}")
        print(f"   Data consistency: {'OK' if is_consistent else 'ISSUES'}")
        print(f"   Issues found: {len(issues)}")
        
        return {
            'unique_names': unique_names,
            'total_samples': len(names_data) if names_data else 0,
            'is_consistent': is_consistent,
            'issues': issues
        }

def main():
    analyzer = TrainingDataAnalyzer()
    result = analyzer.run_analysis()
    
    if len(result['unique_names']) == 1:
        print("\n[PROBLEM] PROBLEM IDENTIFIED:")
        print("   Only 1 face is registered in the system!")
        print("   This explains why take_attendance_touchscreen.py shows 'Registered faces: 1'")
        print("\n[SOLUTION] SOLUTION:")
        print("   Run: python src/add_faces_rpi.py")
        print("   Register multiple different people (not the same person multiple times)")

if __name__ == "__main__":
    main()