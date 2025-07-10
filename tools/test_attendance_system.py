#!/usr/bin/env python3
"""
Test Attendance System
Quick test to verify face recognition system is working properly
"""

import pickle
import numpy as np
from pathlib import Path
from sklearn.neighbors import KNeighborsClassifier

class AttendanceSystemTester:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.names_file = self.data_dir / "names.pkl"
        self.faces_file = self.data_dir / "faces_data.pkl"
    
    def test_training_data_loading(self):
        """Test if training data loads correctly like in take_attendance_touchscreen.py"""
        print("[TEST] Testing training data loading...")
        
        if not self.names_file.exists() or not self.faces_file.exists():
            print("[ERROR] Training data not found!")
            return False
        
        try:
            # Load data exactly like in take_attendance_touchscreen.py
            with open(self.names_file, 'rb') as f:
                labels = pickle.load(f)
            
            with open(self.faces_file, 'rb') as f:
                faces_data = pickle.load(f)
            
            # Train KNN classifier exactly like in the main system
            knn = KNeighborsClassifier(n_neighbors=5)
            knn.fit(faces_data, labels)
            
            # Calculate statistics
            unique_faces = len(set(labels))
            total_samples = len(labels)
            unique_names = sorted(set(labels))
            
            print(f"[SUCCESS] Training data loaded successfully")
            print(f"[INFO] Registered faces: {unique_faces}")
            print(f"[INFO] Total training samples: {total_samples}")
            print(f"[INFO] Registered names: {', '.join(unique_names)}")
            
            # Test prediction capability
            print(f"[TEST] Testing prediction capability...")
            
            # Test with first few samples
            test_samples = faces_data[:5]
            predictions = knn.predict(test_samples)
            probabilities = knn.predict_proba(test_samples)
            
            print(f"[INFO] Test predictions:")
            for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
                confidence = max(prob)
                print(f"   Sample {i+1}: {pred} (confidence: {confidence:.3f})")
            
            return True, {
                'unique_faces': unique_faces,
                'total_samples': total_samples,
                'unique_names': unique_names,
                'knn_model': knn
            }
            
        except Exception as e:
            print(f"[ERROR] Error loading training data: {e}")
            return False, None
    
    def test_face_recognition_simulation(self, model_data):
        """Simulate face recognition process"""
        print(f"\n[TEST] Simulating face recognition process...")
        
        if not model_data:
            print("[ERROR] No model data available")
            return False
        
        knn = model_data['knn_model']
        
        # Load test data
        with open(self.faces_file, 'rb') as f:
            faces_data = pickle.load(f)
        
        # Test with random samples (simulating camera input)
        test_indices = [0, 10, 20, 30, 39]  # Test different samples
        
        print(f"[INFO] Testing recognition with sample faces:")
        
        for idx in test_indices:
            if idx < len(faces_data):
                test_face = faces_data[idx].reshape(1, -1)
                
                prediction = knn.predict(test_face)[0]
                probabilities = knn.predict_proba(test_face)[0]
                confidence = max(probabilities)
                
                print(f"   Sample {idx}: Recognized as '{prediction}' (confidence: {confidence:.3f})")
        
        return True
    
    def diagnose_system_issues(self):
        """Diagnose potential system issues"""
        print(f"\n[DIAGNOSIS] Checking for common issues...")
        
        issues = []
        
        # Check file existence
        if not self.names_file.exists():
            issues.append("names.pkl file missing")
        if not self.faces_file.exists():
            issues.append("faces_data.pkl file missing")
        
        # Check file sizes
        if self.names_file.exists():
            names_size = self.names_file.stat().st_size
            if names_size < 50:
                issues.append(f"names.pkl very small ({names_size} bytes)")
        
        if self.faces_file.exists():
            faces_size = self.faces_file.stat().st_size
            if faces_size < 1000:
                issues.append(f"faces_data.pkl very small ({faces_size} bytes)")
        
        # Check data consistency
        try:
            with open(self.names_file, 'rb') as f:
                names = pickle.load(f)
            with open(self.faces_file, 'rb') as f:
                faces = pickle.load(f)
            
            if len(names) != len(faces):
                issues.append(f"Data mismatch: {len(names)} names vs {len(faces)} faces")
            
            unique_count = len(set(names))
            if unique_count < 2:
                issues.append(f"Only {unique_count} unique name(s) in database")
            
        except Exception as e:
            issues.append(f"Error reading data files: {e}")
        
        if issues:
            print("[WARNING] Issues found:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("[SUCCESS] No issues detected")
        
        return issues
    
    def run_complete_test(self):
        """Run complete system test"""
        print("=" * 60)
        print("[SYSTEM TEST] Face Recognition Attendance System Test")
        print("=" * 60)
        
        # Test 1: Training data loading
        success, model_data = self.test_training_data_loading()
        
        if not success:
            print("\n[FAILED] Training data loading failed")
            return False
        
        # Test 2: Face recognition simulation
        recognition_success = self.test_face_recognition_simulation(model_data)
        
        if not recognition_success:
            print("\n[FAILED] Face recognition simulation failed")
            return False
        
        # Test 3: System diagnosis
        issues = self.diagnose_system_issues()
        
        # Final summary
        print("\n" + "=" * 60)
        print("[SUMMARY] Test Results:")
        print(f"   Training Data Loading: {'PASS' if success else 'FAIL'}")
        print(f"   Face Recognition: {'PASS' if recognition_success else 'FAIL'}")
        print(f"   System Issues: {len(issues)} found")
        print(f"   Unique Faces: {model_data['unique_faces'] if model_data else 0}")
        print(f"   Total Samples: {model_data['total_samples'] if model_data else 0}")
        
        if model_data and model_data['unique_faces'] >= 2:
            print("\n[SUCCESS] System appears to be working correctly!")
            print("[INFO] The attendance system should recognize multiple faces")
        else:
            print("\n[WARNING] System may have issues with face recognition")
        
        return success and recognition_success and len(issues) == 0

def main():
    tester = AttendanceSystemTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n[RECOMMENDATION] Try running the attendance system:")
        print("   python src/take_attendance_touchscreen.py")
    else:
        print("\n[RECOMMENDATION] Fix the issues above before using the attendance system")

if __name__ == "__main__":
    main()