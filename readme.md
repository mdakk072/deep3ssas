# **deep3ssas** : Parking Spot Detection and Management System

This project aims to create a parking spot detection and management system that detects available parking spots and displays the information on a website. The system consists of a Python Flask website, a detection module using YOLOv5, and several other modules for data collection, correction, and model training and evaluation.

## Overview

The project consists of several modules, each responsible for a specific task. The Detection Module is the core of the project and performs the detection of parking spots in real-time. The Data Handler module is responsible for managing the data, storing it in a PostgreSQL database, and uploading it to Azure Blob Storage. The Correction Module corrects the localization data of the detected parking spots. Finally, the Web App module provides a user interface that allows users to view the available parking spots on a map.

1. **Python Flask Website**: 

The purpose of the site is to showcase an example of the results from the detection module. The site displays available parking spots in different locations using Flask and Jinja2. Users can view real-time parking spots and access detailed information about each parking spot. The site interacts with the detection module to receive updates on parking spot data and displays them on a map and in a list.

The code below demonstrates how the Flask website interacts with the detection module:

- It first defines a URL for the data handler (DATA_HANDLER_URL) and a wait time for updates (WAIT_TIME).
- The `load_infos()` function fetches parking spot information from the data handler and stores it locally if needed.
- The `update_infos()` function updates the parking spot information by calling `load_infos()`.
- The Flask website routes (such as `/`, `/contact`, `/map`, and `/parkings`) serve the HTML pages and update the parking spot information by calling `update_infos()` when necessary.

The Flask website is designed to display real-time updated information about parking spots, retrieving the data from the detection module via the data handler. Users can access the site to view available parking spots and get detailed information about each parking spot.

2. **Detection Module**: 
The Detection Module is a Python-based module that utilizes the YOLOv5 object detection model to process live camera feeds and detect parking spots. It is implemented in the `DetectionModule` class, which includes the following attributes and methods:
**Attributes:**
- `model`: The YOLOv5 object detection model.
- `colorStates`: Tuple of colors used to visualize the parking spot states.
- `readyToSend`: Flag indicating if the data is ready to be sent to the API.
- `parkings`: Dictionary containing information about the parking spots.
- `APIurl`: URL of the API to send data.
- `currentParkingID`: The ID of the current parking spot being processed.
- `test`: Flag indicating if the module is running in test mode.
- `timeout`: Timeout in seconds for capturing remote images.
- `cap`: VideoCapture object to capture video from camera or video file (optional).
- `cache`: Dictionary to store the latest captured image for each parking spot.

**Methods:**
- `__init__`: Initializes the DetectionModule with the specified model, video source, camera settings, API URL, and timeout.
- `getLocalisation`: Retrieves the geolocation information of the user.
- `prepare_parkings_data`: Prepares the parking spots data to be sent to the API.
- `update_API`: Sends the parking spots data to the API.
- `detect_frame`: Detects parking spots in a video frame.
- `get_remote_image`: Retrieves an image from a remote web source.
- `runRemoteSource`: Main loop that processes the remote video feed and detects parking spots.
- `load_image_from_cache`: Loads a cached image from the local storage.
- `find_file`: Finds a file in the current working directory or script directory.

This module is responsible for detecting parking spots in real-time by analyzing video frames from live camera feeds or video files. It processes each frame, identifies the parking spots, and sends the updated parking spot data to a web API for further analysis or display.



3. **Correction Module**: 

The Correction Module is a Python-based module that corrects the detected parking spots by comparing them to the ground truth annotations. It is implemented in the `CorrectionModule` class, which includes the following attributes and methods:

**Attributes:**

- `images_dir`: The directory containing the input images.
- `annotations_dir`: The directory containing the ground truth annotations.
- `labels_dir`: The directory containing the labels (detected parking spots).
- `max_width`: The maximum width of the images.
- `max_height`: The maximum height of the images.

**Methods:**

- `__init__`: Initializes the CorrectionModule with the specified directories and image dimensions.
- `iou`: Calculates the Intersection over Union (IoU) between two bounding boxes.
- `distance`: Calculates the Euclidean distance between the centers of two bounding boxes.
- `inclusion_percentage`: Calculates the percentage of one bounding box included in another.
- `max_touching_distance`: Calculates the maximum distance between the centers of two touching bounding boxes.
- `analyze_boxes`: Analyzes two bounding boxes and returns a dictionary with the analysis results.
- `load_image`: Loads an image from a given path.
- `load_images`: Loads all images for a specific camera ID.
- `load_annotations`: Loads ground truth annotations for a specific camera ID.
- `load_labels`: Loads labels (detected parking spots) for a given image name.
- `compare_correction`: Compares the detected parking spots to the ground truth annotations and returns matched and unmatched predictions.
- `convert_to_yolo_format`: Converts corrected parking spot coordinates to YOLO format and saves them to a label file.
- `run_analysis`: Runs the correction analysis for a specific camera ID and saves the corrected results.

The Correction Module helps improve the accuracy of the parking spot detection by comparing the detected parking spots to the ground truth annotations. It calculates various metrics such as IoU, distance, and inclusion percentage to determine if a prediction is correct or not. The corrected parking spot coordinates are then converted to YOLO format and saved to label files for further use.


4. **Training and Evaluation Module**: 

Trains the model using the corrected data and evaluates its performance. If the new model performs better, it is sent to production.(TODO)


5. **API Module**: 

The API Module is a Python-based module that exposes a Flask web server to provide an interface to interact with the application. The module allows receiving and updating parking spot information and status. It also stores images and labels to Azure Blob Storage and communicates with a PostgreSQL database to store relevant information.



**Functions:**

- `load_infos`: Loads the current parking information from the `infos.json` file.
- `save_infos`: Saves the current parking information to the `infos.json` file.
- `convert_to_yolo_format`: Converts parking spot label coordinates to YOLO format.
- `find_file`: Finds a file in the current working directory or script directory.
- `get_credentials`: Retrieves the required credentials for the database and Azure Blob Storage.

**Flask Routes:**

- `/parking_structure`: Returns the current parking structure information.
- `/status`: Retrieves or updates the current parking spot status.
- `/test`: Returns the current server hostname for testing.
- `/currentID`: Updates the current parking spot ID.

The API Module provides a simple and straightforward way to interact with the application, receive updates, and manage parking spot data. It uses Flask to expose a RESTful API that can be used by various clients or devices to send and receive parking spot information.

6. **Azure Blob Storage module**: 

This module provides a class `AzureBlobStorage` that allows you to interact with Azure Blob Storage. The class has methods for uploading, downloading, listing, and deleting files in two containers - "imgs" and "lbls". The class uses the BlobServiceClient from the azure.storage.blob library.


**Methods:**

- `__init__(self, connection_string)`: Initializes the class with the connection string and sets up the clients for the "imgs" and "lbls" containers.
- `upload_file(self, file_path, file_name, container_client)`: Uploads a file to the specified container.
- `delete_file(self, file_name, container_client)`: Deletes a file from the specified container.
- `list_files(self, container_client)`: Lists all files in the specified container.
- `download_file(self, file_name, destination_path, container_client)`: Downloads a file from the specified container.
- `clear_container(self, container_client)`: Deletes all files in the specified container.

The remaining methods are specific to either the "imgs" or "lbls" container, and they simply call the generic methods with the appropriate container client:

- `upload_image(self, image_path, file_name)`
- `delete_image(self, image_name)`
- `list_images(self)`
- `download_image(self, image_name, destination_path)`
- `clear_images(self)`
- `upload_label(self, label_path, file_name)`
- `delete_label(self, label_name)`
- `list_labels(self)`
- `download_label(self, label_name, destination_path)`
- `clear_labels(self)`


7. **PostgreSQL Database module**: 

This module provides functions to interact with a PostgreSQL database. It contains functions for creating and managing tables, as well as for performing CRUD operations on the data.

**Functions:**

- `create_connection(database, user, password, host="localhost", port="5432")`: Creates a connection to the PostgreSQL database.
- `create_tables(connection)`: Creates the "images", "detections", and "parkings" tables if they do not already exist.
- `drop_tables(connection)`: Drops the "images", "detections", and "parkings" tables if they exist.
- `clear_tables(connection)`: Deletes all rows from the "detections" and "images" tables.
- `insert_image(connection, image_data)`: Inserts a new image row into the "images" table.
- `update_image(connection, image_name, data)`: Updates an existing image row in the "images" table.
- `delete_image(connection, image_name)`: Deletes an image row from the "images" table.
- `get_image(connection, image_name)`: Retrieves an image row from the "images" table.
- `get_all_images(connection)`: Retrieves all image rows from the "images" table.
- `insert_detection(connection, detection_data)`: Inserts a new detection row into the "detections" table.
- `get_detections_by_image(connection, image_name)`: Retrieves all detection rows associated with an image from the "detections" table.
- `delete_detection(connection, detection_id)`: Deletes a detection row from the "detections" table.
- `update_detection(connection, detection_id, data)`: Updates an existing detection row in the "detections" table.
- `get_detection(connection, detection_id)`: Retrieves a detection row from the "detections" table.
- `get_all_detections(connection)`: Retrieves all detection rows from the "detections" table.
- `upsert_parking(connection, parking_data)`: Inserts or updates a parking row in the "parkings" table.
- `get_parking(connection, parking_id)`: Retrieves a parking row from the "parkings" table.
- `get_all_parkings(connection)`: Retrieves all parking rows from the "parkings" table.
- `delete_parking(connection, parking_id)`: Deletes a parking row from the "parkings" table.


## Parking Detection Project Workflow

1. **Camera Feed**: Obtain live camera feed from various parking locations.
2. **Detection Module**: Process the camera feed using YOLOv5 to detect available parking spots.
3. **Web Application**: Display the available parking spot information on a Flask web application for users.
4. **Data Correction**: Correct the collected data, if necessary, to improve the accuracy of the information.
5. **Model Training/Evaluation**: Train the YOLOv5 model using the corrected data to improve detection accuracy.Evaluate the model's performance and deploy the new model if it performs better.


## Modules, Attributes, and Methods

| Module                  | Attributes                                                                                                                                                                                                                              | Methods                                                                                                                                                                                                                               |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Python Flask Website    | - DATA_HANDLER_URL<br/>- WAIT_TIME                                                                                                                                                                                                      | - load_infos()<br/>- update_infos()<br/>- Flask website routes (such as `/`, `/contact`, `/map`, and `/parkings`)                                                                                                                     |
| Detection Module        | - model<br/>- colorStates<br/>- readyToSend<br/>- parkings<br/>- APIurl<br/>- currentParkingID<br/>- test<br/>- timeout<br/>- cap<br/>- cache                                                                                          | - __init__()<br/>- getLocalisation()<br/>- prepare_parkings_data()<br/>- update_API()<br/>- detect_frame()<br/>- get_remote_image()<br/>- runRemoteSource()<br/>- load_image_from_cache()<br/>- find_file()                            |
| Correction Module       | - images_dir<br/>- annotations_dir<br/>- labels_dir<br/>- max_width<br/>- max_height                                                                                                                                                   | - __init__()<br/>- iou()<br/>- distance()<br/>- inclusion_percentage()<br/>- max_touching_distance()<br/>- analyze_boxes()<br/>- load_image()<br/>- load_images()<br/>- load_annotations()<br/>- load_labels()<br/>- compare_correction()<br/>- convert_to_yolo_format()<br/>- run_analysis() |
| Training and Evaluation | (TODO)                                                                                                                                                                                                                                  | (TODO)                                                                                                                                                                                                                               |
| API Module              |                                                                                                                                                                                                                                         | - load_infos()<br/>- save_infos()<br/>- convert_to_yolo_format()<br/>- find_file()<br/>- get_credentials()<br/>- Flask routes such as `/parking_structure`, `/status`, `/test`, and `/currentID`                                      |
| Azure Blob Storage      |                                                                                                                                                                                                                                         | - __init__()<br/>- upload_file()<br/>- delete_file()<br/>- list_files()<br/>- download_file()<br/>- clear_container()<br/>- (Container-specific methods)                                                                                |
| PostgreSQL Database     |                                                                                                                                                                                                                                         | - create_connection()<br/>- create_tables()<br/>- drop_tables()<br/>- clear_tables()<br/>- insert_image()<br/>- update_image()<br/>- delete_image()<br/>- get_image()<br/>- get_all_images()<br/>- insert_detection()<br/>- get_detections_by_image()<br/>- delete_detection()<br/>- update_detection()<br/>- get_detection()<br/>- get_all_detections()<br/>- upsert_parking()<br/>- get_parking()<br/>- get_all_parkings()<br/>- delete_parking() |




## DevOps Implementation

To implement a DevOps approach for this project, we will use the following tools and methodologies:

## Tools Used So Far :

 - ``Git`` for version control and collaboration
 - ``Docker`` for containerization of the application and its dependencies
 - ``PostgreSQL`` for managing the application database
 - ``Azure Blob Storage`` for managing and storing the application data
 - ``Pytest`` for testing the application code
 - ``GitHub`` Actions for automating build and deployment processes
- ``YAML`` for configuration files and for defining GitHub Actions workflows
- ``XML`` for configuration files such as the data handler's config.xml file
- ``JSON`` for data serialization, such as the parking_structure.json file in the detection module
## Methodologies:
 - Continuous Integration (CI) and Continuous Deployment (CD) to automate building, testing, and deploying the application to production
 - Agile software development methodology to continuously improve the application and adapt to changing requirements

### 1. Version Control (Git & GitHub Actions)

  - Using Git as  version control system to manage code changes, track progress, and collaborate more effectively. Git enables to create branches for various purposes, including feature development, bug fixes, and stable releases. It also allows to manage and review the code changes more efficiently.

- Using GitHub Actions, a powerful automation tool for Continuous Integration (CI) and Continuous Deployment (CD).

 - With GitHub Actions, we can automatically run tests, code analysis, and deployment scripts for each push or merge to the `dev` or features branches. This ensures that new code is thoroughly tested and integrated with the existing codebase, and that the latest version of the application is always available to users.

 - Additionally, we deploy the master branch on release (push to master or merge) to Azure Web Apps for both the API and website. During the deployment process, we run tests, build Docker images, push them to Docker Hub, and load them to Azure. This ensures that the latest stable version of the application is available to users.


### 2. Configuration Management (YANG, YAML, XML, Ansible, Chef)

- Examples of YAML usage in this project include Ansible playbooks and GitHub Actions workflows.Its simplicity makes it well-suited for configuration management tasks, as it integrates well with popular configuration management tools such as Ansible and Chef.

- Using XML if you have specific requirements for XML-based configurations.
- Using Ansible and Chef for configuration management and infrastructure provisioning.

### 3. Containerization (Docker)

  - The Deep3ssas system can be containerized using Docker. The Dockerfiles for each module can be found in the docker directory. The Docker images can be built by running the docker build command with the Dockerfile as argument in each module directory.

 - The modules of the system are organized in the modules directory. Each module has its own subdirectory and contains the necessary code and files. The attributes and methods of each module can be found in the corresponding Python files.

### 4. Web Application (Flask, Jinja2, PostgreSQL)

- Developing a Flask web application with Jinja2 for templating.
- Using PostgreSQL as the database for storing parking spot information and other data.

### 5. Development and Deployment (Red Hat Linux, Networking, ITIL)

- Develop and deploy your applications on Red Hat Linux.
- Follow ITIL best practices for IT service management.
- Ensure proper networking configurations for your services.

### 6. Azure

  - Azure Repos for Git-based version control.
  - Azure Pipelines for CI/CD.
  - Azure Container Registry for storing Docker images.
  - Azure Kubernetes Service (AKS) or Azure App Service for container orchestration and deployment.
  - Azure Database for PostgreSQL for managed PostgreSQL services.
  - Azure Monitor for monitoring and logging.

## Repository Structure
`/annotations:` contains text files containing parking spot annotation data (future usage for Correction module)

`/docker:` contains Dockerfiles for each module

`/modules:` contains the source code for each module

`/static:` contains static files used by the web application

`/tests:` contains unit tests for each module

`infos.json:` contains configuration information for the project

`parking_structure.json:` contains information about the parking structure

`readme.md:` the README file
## Getting Started


1. Clone the repository.

2. Install the required packages by running pip install -r requirements.txt.

3. Configure the necessary settings in the modules/data_handler/config.xml file, such as database connection settings and Azure Blob Storage settings.

4. Run the data handler module by navigating to the modules/data_handler directory and running the command python app.py.

5. Run the detection module by navigating to the modules/detection directory and running the command python app.py.

6. Run the web app module by navigating to the modules/web_app directory and running the command python app.py.





