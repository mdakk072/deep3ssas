import glob
import cv2
import os
import random
from typing import Tuple , List
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patches as patches
import numpy

class CorrectionModule:
    def __init__(self, images_dir: str, annotations_dir: str, labels_dir: str, max_width: int = 400, max_height: int = 400):
        self.images_dir = images_dir
        self.annotations_dir = annotations_dir
        self.labels_dir = labels_dir
        self.max_width = max_width
        self.max_height = max_height
    # BoxAnalysis methods
 
    def iou(self,box1,box2):
        x1, y1, a1, b1 = box1
        x2, y2, a2, b2 = box2
        w1, h1 = abs(a1 - x1), abs(b1 - y1)
        w2, h2 = abs(a2 - x2), abs(b2 - y2)

        x_intersection = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_intersection = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        intersection_area = x_intersection * y_intersection

        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - intersection_area

        if union_area == 0:
            return 0
        return intersection_area / union_area
    
    def distance(self,box1,box2):
        x1, y1, _, _ = box1
        x2, y2, _, _ = box2
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        return distance

    def inclusion_percentage(self,box1,box2):
        iou_value = self.iou(box1,box2)
        x1, y1, a1, b1 = box1
        x2, y2, a2, b2 = box2
        w1, h1 = abs(a1 - x1), abs(b1 - y1)
        w2, h2 = abs(a2 - x2), abs(b2 - y2)
        area1 = w1 * h1
        area2 = w2 * h2
        percentage_box1_in_box2 = iou_value * area1 / area2
        percentage_box2_in_box1 = iou_value * area2 / area1
        return percentage_box1_in_box2, percentage_box2_in_box1

    def max_touching_distance(self,box1, box2):
        x1, y1, a1, b1 = box1
        x2, y2, a2, b2 = box2
        width1, height1 = abs(a1 - x1), abs(b1 - y1)
        width2, height2 = abs(a2 - x2), abs(b2 - y2)
        # Vérifier si les boîtes se touchent horizontalement ou verticalement
        horizontal_overlap = (a1 >= x2) and (a2 >= x1)
        vertical_overlap = (b1 >= y2) and (b2 >= y1)
        if horizontal_overlap and vertical_overlap:
            # Les boîtes se touchent, calculer la distance maximale entre leurs centres
            max_distance = ((width1 / 2) + (width2 / 2))**2 + ((height1 / 2) + (height2 / 2))**2
            return max_distance**0.5
        # Les boîtes ne se touchent pas
        return -1
     
    def analyze_boxes(self, boxes: List[Tuple[Tuple[int, int, int, int], Tuple[int, int, int, int]]]) -> List[dict]:
        boxes = [((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))) for (x1, y1, x2, y2) in boxes]
        iou = self.iou(*boxes)
        distance = self.distance(*boxes)
        inclusion_percentage = self.inclusion_percentage(*boxes)
        maxDistance=self.max_touching_distance(*boxes)
        averageInclusion=sum(inclusion_percentage)/len(inclusion_percentage)
        isCorrect= any([b!=0 for b in inclusion_percentage]) and distance<maxDistance and averageInclusion>0.33
        variables_dict = {
    "Box 1": boxes[0],
    "Box 2": boxes[1],
    "IoU": round(iou),
    "Distance": round(distance,2),
    "Inclusion Percentage":inclusion_percentage,
    "isCorrect": isCorrect,
}
        return variables_dict

    def load_image(self, image_path: str) -> Tuple[str, 'numpy.ndarray']:
        img = cv2.imread(image_path)
        return os.path.basename(image_path), img

    def load_images(self, camera_id: int) -> List[Tuple[str, 'numpy.ndarray']]:
        camera_images = glob.glob(os.path.join(self.images_dir, f"camera{camera_id}_*.jpg"))
        return [(os.path.basename(img_path), cv2.imread(img_path)) for img_path in camera_images]

    def load_annotations(self, camera_id: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        annotations_path = os.path.join(self.annotations_dir, f"annotations_camera_{camera_id}.txt")
        with open(annotations_path, 'r') as f:
            lines = f.readlines()
        parking_spots = [tuple(map(int, line.strip().split(','))) for line in lines]
        return parking_spots

    def load_labels(self, image_name: str, image_shape: Tuple[int, int, int] = (640, 640, 3)) -> List[Tuple[int, int, int, int]]:
        labels_path = os.path.join(self.labels_dir, image_name.replace(".jpg", ".txt"))
        labels = []
        with open(labels_path, 'r') as f:
            for line in f:
                class_id, x, y, w, h = map(float, line.strip().split())
                x1, y1, x2, y2 = int((x - w/2) * image_shape[1]), int((y - h/2) * image_shape[0]), int((x + w/2) * image_shape[1]), int((y + h/2) * image_shape[0])
                labels.append((x1, y1, x2, y2))
        return labels

    def compare_correction(self, predictions: List[Tuple[int, int, int, int]], parking_spots: List[Tuple[int, int, int, int]]) -> Tuple[List[Tuple[int, int, int, int]], List[Tuple[int, int, int, int]]]:
            matched_predictions = []
            unmatched_predictions = predictions.copy()
            unmatched_annotations = parking_spots.copy()

            for parking_spot in parking_spots:
                best_match = None
                best_analysis = None
                for prediction in unmatched_predictions:
                    analysis = self.analyze_boxes([parking_spot, prediction])
                    if analysis["isCorrect"]:
                        if best_match is None or (
                            analysis["IoU"] > best_analysis["IoU"] or (
                            analysis["Distance"] < best_analysis["Distance"] and
                            sum(analysis["Inclusion Percentage"]) > sum(best_analysis["Inclusion Percentage"]))
                        ):
                            best_match = prediction
                            best_analysis = analysis

                if best_match:
                    matched_predictions.append(best_match)
                    unmatched_predictions.remove(best_match)
                    unmatched_annotations.remove(parking_spot)

            return matched_predictions, unmatched_annotations
   
    def convert_to_yolo_format(self, label_file: str, coords_list: List[Tuple[int, int, int, int]], img_width: int, img_height: int) -> None:
        # Convert coordinates to YOLO format
        print(label_file)
        yolo_coords = []
        for coords in coords_list:
            x1, y1, x2, y2 = coords
            width = x2 - x1
            height = y2 - y1
            x_center = x1 + width / 2
            y_center = y1 + height / 2

            # Normalize coordinates
            x_center /= img_width
            y_center /= img_height
            width /= img_width
            height /= img_height
            yolo_coords.append((x_center, y_center, width, height))
        # Write YOLO coordinates to the label file
        with open(label_file, 'w') as f:
            for coords in yolo_coords:
                f.write(f"0 {coords[0]} {coords[1]} {coords[2]} {coords[3]}\n")
    
    def run_analysis(self, camera_id: int) -> None:
        images = self.load_images(camera_id)
        for img_name, img in images:
            parking_spots = self.load_annotations(camera_id)
            predictions = self.load_labels(img_name)
            #self.view_comparison(img, predictions, parking_spots)
            matched_predictions, unmatched_annotations=self.compare_correction(predictions,parking_spots)
            correctedAnnotations=matched_predictions+unmatched_annotations
            label_path = os.path.join(self.labels_dir, img_name.replace(".jpg", ".txt"))
        self.viewImageBox(img,correctedAnnotations)
   
    def view_comparison(self, image: 'numpy.ndarray', predictions: List[Tuple[int, int, int, int]], parking_spots: List[Tuple[int, int, int, int]]) -> None:
        fig, ax = plt.subplots(1)
        ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        

        matched_predictions = []
        matched_annotations = []
        unmatched_predictions = predictions.copy()
        unmatched_annotations = parking_spots.copy()
        for box in parking_spots:
            x1, y1, x2, y2 = box
            rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='g', facecolor='none', label='Unmatched Annotation')
            ax.add_patch(rect)
            ax.annotate("Unmatched Annotation", (x1, y1), color='w', fontsize=8, ha='left', va='top')

        for i, parking_spot in enumerate(parking_spots):
            best_match = None
            best_analysis = None
            for prediction in unmatched_predictions:
           
                analysis = self.analyze_boxes([parking_spot, prediction])
                print(analysis)
                if analysis["isCorrect"]:
                    if best_match is None or (
                        analysis["IoU"] > best_analysis["IoU"] or (
                        analysis["Distance"] < best_analysis["Distance"] and
                        sum(analysis["Inclusion Percentage"]) > sum(best_analysis["Inclusion Percentage"]))
                    ):
                        best_match = prediction
                        best_analysis = analysis

                # Display current parking spot and prediction
                x1, y1, x2, y2 = parking_spot
                rect1 = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='y', facecolor='none', label='Current Parking Spot')
                ax.add_patch(rect1)
                ax.annotate(f"Parking Spot {i+1}", (x1, y1), color='y', fontsize=8, ha='left', va='top')

                x1, y1, x2, y2 = prediction
                rect2 = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='c', facecolor='none', label='Current Prediction')
                ax.add_patch(rect2)
                ax.annotate(f"Prediction {i+1}", (x1, y1), color='c', fontsize=8, ha='left', va='top')
                

             #   plt.pause(0.2)  # Pause to see intermediate results
             
                rect1.remove()
                rect2.remove()

            if best_match:
                matched_predictions.append(best_match)
                unmatched_predictions.remove(best_match)
                matched_annotations.append(parking_spot)
                unmatched_annotations.remove(parking_spot)
            else:
                x1, y1, x2, y2 = parking_spot
                ax.plot((x1 + x2) / 2, (y1 + y2) / 2, marker='x', color='r', markersize=8, label='Alert: Unmatched Parking Spot')
                #ax.annotate("Alert: Unmatched Parking Spot", ((x1 + x2) / 2, (y1 + y2) / 2), color='r', fontsize=8, ha='left', va='top')

        # Clear previous annotations
        ax.clear()
        ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        for box in unmatched_annotations:
            x1, y1, x2, y2 = box
            rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='g', facecolor='none', label='Unmatched Annotation')
            ax.add_patch(rect)
            ax.annotate("Unmatched Annotation", (x1, y1), color='w', fontsize=8, ha='left', va='top')

        for box in matched_annotations:
            x1, y1, x2, y2 = box
            rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='m', facecolor='none', label='Matched Annotation')
            ax.add_patch(rect)
            ax.annotate("Matched Annotation", (x1, y1), color='w', fontsize=8, ha='left', va='top')

        for box in matched_predictions:
            x1, y1, x2, y2 = box
            rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='b', facecolor='none', label='Matched Prediction')
            ax.add_patch(rect)
            ax.annotate("Matched Prediction", (x1, y1), color='w', fontsize=8, ha='left', va='top')

        for box in unmatched_predictions:
            x1, y1, x2, y2 = box
            rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='r', facecolor='none', label='Unmatched Prediction')
            ax.add_patch(rect)
            ax.annotate("Unmatched Prediction", (x1, y1), color='w', fontsize=8, ha='left', va='top')

        legend_elements = [Line2D([0], [0], color='g', lw=2, label='Unmatched Annotation'),
                        Line2D([0], [0], color='m', lw=2, label='Matched Annotation'),
                        Line2D([0], [0], color='b', lw=2, label='Matched Prediction'),
                        Line2D([0], [0], color='r', lw=2, label='Unmatched Prediction'),
                        Line2D([0], [0], color='y', lw=2, label='Current Parking Spot'),
                        Line2D([0], [0], color='c', lw=2, label='Current Prediction')]

        ax.legend(handles=legend_elements, loc='upper left')
        


        plt.show()

    def viewImageBox(self,image,boxes):
            fig, ax = plt.subplots(1)
            ax.imshow(image)
            for box in boxes:
                x1,y1,x2,y2=box
                color=[random.randint(0,255)/255 for i in range(3)]
                rect1 = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor=color, facecolor='none', label='Current Parking Spot')
                ax.add_patch(rect1)
            plt.show()
            del fig , ax

# Main function
if __name__ == "__main__":
    images_dir = "images"
    annotations_dir = "annotations"
    labels_dir = "labels"
    correction_module = CorrectionModule(images_dir, annotations_dir, labels_dir)
    for camera_id in range(0, 15):
        correction_module.run_analysis(camera_id)


