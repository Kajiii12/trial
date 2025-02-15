import cv2
import numpy as np
import os

def read_images(data_path, img_size=(200, 200)):
    """
    Reads images from the dataset folder and returns them along with labels.
    Each subfolder in 'data_path' represents a class (e.g., a person's name).
    """
    images = []
    labels = []
    label_map = {}
    current_label = 0

    for dir_name in sorted(os.listdir(data_path)):
        dir_path = os.path.join(data_path, dir_name)
        if not os.path.isdir(dir_path):
            continue

        label_map[current_label] = dir_name  # Map label to folder name
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                img_resized = cv2.resize(img, img_size)
                images.append(img_resized)
                labels.append(current_label)
        current_label += 1

    return np.asarray(images), np.asarray(labels), label_map

def test_model(fisherface, label_map, img_size=(200, 200)):
    """
    Captures a test image and predicts its label using the trained Fisherface model.
    """
    cap = cv2.VideoCapture(0)
    print("Align your face and press 's' to capture a test image.")

    test_img = None
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, img_size)

        cv2.imshow("Test Image Capture", frame)

        if cv2.waitKey(1) & 0xFF == ord('s'):
            test_img = resized
            print("Test image captured.")
            break

    cap.release()
    cv2.destroyAllWindows()

    if test_img is not None:
        label, confidence = fisherface.predict(test_img)
        if label in label_map:
            print(f"Predicted Label: {label_map[label]}, Confidence: {confidence}")
        else:
            print("Predicted label not found in label map.")
    else:
        print("No test image captured.")

def main():
    data_path = "dataset"  # Folder path where images are saved
    img_size = (200, 200)

    # Step 1: Read saved images and train the Fisherface model
    print("Step 1: Training the Fisherface Model")
    images, labels, label_map = read_images(data_path, img_size)

    if len(np.unique(labels)) < 2:
        print("Error: At least two classes are needed to train the model. Add more images to the dataset.")
        return

    fisherface = cv2.face.FisherFaceRecognizer_create()
    fisherface.train(images, labels)
    print("Fisherface model trained successfully.")

    # Step 2: Test the model with a live capture
    print("\nStep 2: Testing the Model with a Live Capture")
    test_model(fisherface, label_map, img_size)

if __name__ == "__main__":
    main()
