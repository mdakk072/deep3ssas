import cv2
import os
import random
import glob

class ImageAnnotator:
    def __init__(self, image_dir, annotations_dir, cameras_range=(1, 16)):
        self.image_dir = image_dir
        self.annotations_dir = annotations_dir
        self.cameras_range = cameras_range
        self.points = []
        self.drawing = False

        if not os.path.exists(self.annotations_dir):
            os.makedirs(self.annotations_dir)

    def save_annotations(self, camera_id, parking_spots):
        with open(os.path.join(self.annotations_dir, f'annotations_camera_{camera_id}.txt'), 'w') as f:
            for spot in parking_spots:
                f.write(','.join(map(str, spot)) + '\n')

    def mouse_callback(self, event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.points.append((x, y))
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.points[-1] = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False

    def get_random_image(self, camera_id):
        images = glob.glob(os.path.join(self.image_dir, f"camera{camera_id}_*.jpg"))
        return random.choice(images) if images else None

    def annotate_images(self):
        camera_sources = []
        for i in range(*self.cameras_range):
            print(i)
            random_image = self.get_random_image(i)
            if random_image:
                camera_sources.append(random_image)
                print(random_image)
       

        for idx, camera_source in enumerate(camera_sources):
            img = cv2.imread(camera_source)
            img_copy = img.copy()
            self.points = []
            self.drawing = False
            parking_spots = []

            cv2.namedWindow('Image')
            cv2.setMouseCallback('Image', self.mouse_callback)
            print(camera_source)

            while True:
                img = img_copy.copy()
                for i in range(0, len(self.points) - 1, 2):
                    cv2.rectangle(img, self.points[i], self.points[i+1], (0, 255, 0), 2)
                cv2.imshow('Image', img)

                key = cv2.waitKey(1)
                if key & 0xFF == ord('s'):
                    if len(self.points) % 2 == 0:
                        for i in range(0, len(self.points), 2):
                            parking_spots.append((*self.points[i], *self.points[i+1]))
                        self.save_annotations(idx, parking_spots)
                        print(f"Annotations saved for camera {idx + 1}")
                        break
                elif key & 0xFF == ord('q'):
                    print("Quitting...")
                    cv2.destroyAllWindows()
                    exit(0)
                elif key & 0xFF == ord('z'):
                    if self.points:
                        self.points.pop()
                elif key & 0xFF == ord('r'):
                    img_path = self.get_random_image(idx + 1)
                    if img_path:
                        img_copy = cv2.imread(img_path)

            cv2.destroyAllWindows()
import cv2
import os
import random
import glob

class ExtendedImageAnnotator(ImageAnnotator):
    def __init__(self, image_dir, annotations_dir, cameras_range=(1, 16), rect_thickness=2):
        super().__init__(image_dir, annotations_dir, cameras_range)
        self.rect_thickness = rect_thickness

    def display_info(self, img):
        font = cv2.FONT_HERSHEY_SIMPLEX
        total_spots = len(self.points) // 2
        cv2.putText(img, f'Total Spots: {total_spots}', (10, 30), font, 1, (255, 255, 255), 2)

    def mouse_callback(self, event, x, y, flags, params):
        super().mouse_callback(event, x, y, flags, params)
        if event == cv2.EVENT_MOUSEWHEEL:
            delta = cv2.getMouseWheelDelta(flags)
            self.rect_thickness += delta
            self.rect_thickness = max(1, self.rect_thickness)

    def annotate_images(self):
        camera_sources = []
        for i in range(*self.cameras_range):
            random_image = self.get_random_image(i)
            if random_image:
                camera_sources.append(random_image)

        for idx, camera_source in enumerate(camera_sources):
            img = cv2.imread(camera_source)
            img_copy = img.copy()
            self.points = []
            self.drawing = False
            parking_spots = []

            cv2.namedWindow('Image')
            cv2.setMouseCallback('Image', self.mouse_callback)
            print(camera_source)

            while True:
                img = img_copy.copy()
                for i in range(0, len(self.points) - 1, 2):
                    cv2.rectangle(img, self.points[i], self.points[i+1], (0, 255, 0), self.rect_thickness)
                self.display_info(img)
                cv2.imshow('Image', img)

                key = cv2.waitKey(1)
                if key & 0xFF == ord('s'):
                    if len(self.points) % 2 == 0:
                        for i in range(0, len(self.points), 2):
                            parking_spots.append((*self.points[i], *self.points[i+1]))
                        self.save_annotations(idx, parking_spots)
                        print(f"Annotations saved for camera {idx + 1}")
                        break
                elif key & 0xFF == ord('q'):
                    print("Quitting...")
                    cv2.destroyAllWindows()
                    exit(0)
                elif key & 0xFF == ord('z'):
                    if self.points:
                        self.points.pop()
                elif key & 0xFF == ord('n'):
                    break

                elif key & 0xFF == ord('r'):
                    img_path = self.get_random_image(idx )
                    if img_path:
                        img_copy = cv2.imread(img_path)

            cv2.destroyAllWindows()




if __name__ == '__main__':
    image_dir = 'images'
    annotations_dir = 'annotations'
    cameras_range = (0, 15)

    annotator = ExtendedImageAnnotator(image_dir, annotations_dir, cameras_range)
    annotator.annotate_images()
'''
if __name__ == '__main__':
    image_dir = 'images'
    annotations_dir = 'annotations'
    cameras_range = (1, 16)

    annotator = ImageAnnotator(image_dir, annotations_dir, cameras_range)
    annotator.annotate_images()
'''