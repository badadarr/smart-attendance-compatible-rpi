#!/usr/bin/env python3
"""
Enhanced Data Collection Assistant
Script bantuan untuk pengumpulan data wajah dengan panduan dan validasi real-time
"""

import cv2
import os
import numpy as np
from pathlib import Path
import time
import argparse


class DataCollectionAssistant:
    def __init__(self):
        """Initialize data collection assistant"""
        self.faces_dir = Path("faces")
        self.faces_dir.mkdir(exist_ok=True)

        # Load face detector
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # Collection parameters
        self.min_face_size = (100, 100)  # Minimum face size for good quality
        self.max_photos_per_person = 50
        self.photo_interval = 0.5  # Seconds between auto-capture

    def check_face_quality(self, face_roi):
        """Check if face ROI has good quality for training"""
        if face_roi is None or face_roi.size == 0:
            return False, "No face region"

        # Check size
        if (
            face_roi.shape[0] < self.min_face_size[0]
            or face_roi.shape[1] < self.min_face_size[1]
        ):
            return False, f"Face too small (min: {self.min_face_size})"

        # Check blur using Laplacian variance
        gray = (
            cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            if len(face_roi.shape) == 3
            else face_roi
        )
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

        if blur_score < 100:  # Threshold for blur detection
            return False, f"Image too blurry (score: {blur_score:.1f})"

        # Check brightness
        brightness = np.mean(gray)
        if brightness < 50:
            return False, f"Too dark (brightness: {brightness:.1f})"
        elif brightness > 200:
            return False, f"Too bright (brightness: {brightness:.1f})"

        return (
            True,
            f"Good quality (blur: {blur_score:.1f}, brightness: {brightness:.1f})",
        )

    def display_instructions(self, frame, text, color=(0, 255, 0)):
        """Display instructions on frame"""
        # Create semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (frame.shape[1] - 10, 100), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

        # Add text
        lines = text.split("\n")
        for i, line in enumerate(lines):
            cv2.putText(
                frame, line, (20, 30 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
            )

        return frame

    def collect_person_data(self, person_name, auto_capture=True):
        """Collect face data for one person"""
        person_dir = self.faces_dir / person_name
        person_dir.mkdir(exist_ok=True)

        # Check existing photos
        existing_photos = len(list(person_dir.glob("*.jpg")))

        print(f"\n📸 Collecting data for: {person_name}")
        print(f"Existing photos: {existing_photos}")
        print(f"Target: {self.max_photos_per_person} photos")
        print("\nInstructions:")
        print("- Look directly at camera")
        print("- Slowly turn head left/right (±15°)")
        print("- Slightly look up/down (±10°)")
        print("- Keep eyes open and visible")
        print("- Press 'q' to quit, 's' to save manually, 'n' for next person")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot access camera")
            return False

        photo_count = existing_photos
        last_capture_time = 0
        quality_scores = []

        while photo_count < self.max_photos_per_person:
            ret, frame = cap.read()
            if not ret:
                print("❌ Cannot read frame")
                break

            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)

            # Detect faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            current_time = time.time()

            if len(faces) == 1:
                # Single face detected - good for collection
                x, y, w, h = faces[0]

                # Draw face rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Extract face ROI
                face_roi = frame[y : y + h, x : x + w]

                # Check quality
                is_good, quality_msg = self.check_face_quality(face_roi)

                if is_good:
                    # Good quality face detected
                    status_color = (0, 255, 0)  # Green

                    # Auto-capture if enabled and enough time passed
                    if (
                        auto_capture
                        and (current_time - last_capture_time) > self.photo_interval
                    ):
                        # Save photo
                        photo_filename = (
                            person_dir / f"{person_name}_{photo_count:03d}.jpg"
                        )
                        cv2.imwrite(str(photo_filename), face_roi)

                        photo_count += 1
                        last_capture_time = current_time
                        quality_scores.append(self.check_face_quality(face_roi)[1])

                        print(
                            f"📷 Captured photo {photo_count}/{self.max_photos_per_person}"
                        )
                else:
                    status_color = (0, 165, 255)  # Orange

                # Display status
                instruction_text = f"Person: {person_name}\nPhotos: {photo_count}/{self.max_photos_per_person}\nStatus: {quality_msg}"

            elif len(faces) == 0:
                # No face detected
                instruction_text = f"Person: {person_name}\nPhotos: {photo_count}/{self.max_photos_per_person}\nStatus: No face detected - move closer"
                status_color = (0, 0, 255)  # Red

            else:
                # Multiple faces detected
                instruction_text = f"Person: {person_name}\nPhotos: {photo_count}/{self.max_photos_per_person}\nStatus: Multiple faces - only one person"
                status_color = (0, 0, 255)  # Red

                # Draw all detected faces
                for x, y, w, h in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            # Display instructions
            frame = self.display_instructions(frame, instruction_text, status_color)

            # Show progress bar
            progress = min(photo_count / self.max_photos_per_person, 1.0)
            bar_width = frame.shape[1] - 40
            cv2.rectangle(
                frame,
                (20, frame.shape[0] - 40),
                (20 + int(bar_width * progress), frame.shape[0] - 20),
                (0, 255, 0),
                -1,
            )
            cv2.rectangle(
                frame,
                (20, frame.shape[0] - 40),
                (20 + bar_width, frame.shape[0] - 20),
                (255, 255, 255),
                2,
            )

            cv2.imshow(f"Data Collection - {person_name}", frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("❌ Collection cancelled")
                break
            elif key == ord("s") and len(faces) == 1:
                # Manual save
                x, y, w, h = faces[0]
                face_roi = frame[y : y + h, x : x + w]
                is_good, quality_msg = self.check_face_quality(face_roi)

                if is_good:
                    photo_filename = person_dir / f"{person_name}_{photo_count:03d}.jpg"
                    cv2.imwrite(str(photo_filename), face_roi)
                    photo_count += 1
                    print(f"📷 Manually saved photo {photo_count}")
                else:
                    print(f"⚠️ Photo quality too low: {quality_msg}")
            elif key == ord("n"):
                print("➡️ Moving to next person")
                break

        cap.release()
        cv2.destroyAllWindows()

        # Collection summary
        final_count = len(list(person_dir.glob("*.jpg")))
        print(f"\n✅ Collection complete for {person_name}")
        print(f"Total photos collected: {final_count}")

        if final_count >= 20:
            print("✅ Sufficient data for training")
            return True
        else:
            print(f"⚠️ Recommended minimum: 20 photos (current: {final_count})")
            return False

    def collect_multiple_people(self, people_list):
        """Collect data for multiple people"""
        print(f"🚀 Starting data collection for {len(people_list)} people")

        results = {}

        for i, person_name in enumerate(people_list, 1):
            print(f"\n{'='*50}")
            print(f"👤 Person {i}/{len(people_list)}: {person_name}")
            print(f"{'='*50}")

            success = self.collect_person_data(person_name)
            results[person_name] = success

            if i < len(people_list):
                print(f"\nPrepare for next person: {people_list[i]}")
                input("Press Enter when ready...")

        # Final summary
        print(f"\n{'='*50}")
        print("📊 COLLECTION SUMMARY")
        print(f"{'='*50}")

        for person, success in results.items():
            status = "✅ Ready" if success else "⚠️ Needs more data"
            photo_count = len(list((self.faces_dir / person).glob("*.jpg")))
            print(f"{person}: {photo_count} photos - {status}")

        ready_count = sum(results.values())
        print(f"\nReady for training: {ready_count}/{len(people_list)} people")

        if ready_count == len(people_list):
            print("\n🎉 All people ready! You can now run: python train_faces.py")
        else:
            print("\n⚠️ Some people need more photos. Consider re-collecting data.")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Enhanced Face Data Collection")
    parser.add_argument(
        "--person", "-p", type=str, help="Single person name to collect"
    )
    parser.add_argument("--people", "-P", nargs="+", help="Multiple people names")
    parser.add_argument(
        "--manual",
        "-m",
        action="store_true",
        help="Manual capture mode (press 's' to save)",
    )

    args = parser.parse_args()

    collector = DataCollectionAssistant()

    if args.person:
        # Single person collection
        auto_mode = not args.manual
        collector.collect_person_data(args.person, auto_capture=auto_mode)
    elif args.people:
        # Multiple people collection
        collector.collect_multiple_people(args.people)
    else:
        # Interactive mode
        print("🎯 Enhanced Face Data Collection")
        print("Choose collection mode:")
        print("1. Single person")
        print("2. Multiple people")

        choice = input("\nEnter choice (1-2): ").strip()

        if choice == "1":
            person_name = input("Enter person name: ").strip()
            if person_name:
                auto_mode = input("Auto capture mode? (y/n): ").strip().lower() == "y"
                collector.collect_person_data(person_name, auto_capture=auto_mode)
        elif choice == "2":
            people_input = input("Enter names separated by commas: ").strip()
            if people_input:
                people_list = [name.strip() for name in people_input.split(",")]
                collector.collect_multiple_people(people_list)
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()
