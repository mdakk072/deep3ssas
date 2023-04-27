from azure.storage.blob import BlobServiceClient
class AzureBlobStorage:
    def __init__(self, connection_string):
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.imgs_container_client = self.blob_service_client.get_container_client("imgs")
        self.lbls_container_client = self.blob_service_client.get_container_client("lbls")

    def upload_file(self, file_path,file_name, container_client):
        blob_client = container_client.get_blob_client(file_name)
        with open(file_path, "rb") as f:
            blob_client.upload_blob(f, overwrite=True)

    def delete_file(self, file_name, container_client):
        blob_client = container_client.get_blob_client(file_name)
        blob_client.delete_blob()

    def list_files(self, container_client):
        return [blob.name for blob in container_client.list_blobs()]

    def download_file(self, file_name, destination_path, container_client):
        blob_client = container_client.get_blob_client(file_name)
        with open(destination_path, "wb") as f:
            f.write(blob_client.download_blob().readall())

    def clear_container(self, container_client):
        for blob in container_client.list_blobs():
            self.delete_file(blob.name, container_client)

    # Functions for images container
    def upload_image(self, image_path,file_name):
        self.upload_file(image_path,file_name, self.imgs_container_client)

    def delete_image(self, image_name):
        self.delete_file(image_name, self.imgs_container_client)

    def list_images(self):
        return self.list_files(self.imgs_container_client)

    def download_image(self, image_name, destination_path):
        self.download_file(image_name, destination_path, self.imgs_container_client)

    def clear_images(self):
        self.clear_container(self.imgs_container_client)

    # Functions for labels container
    def upload_label(self, label_path,file_name):
        self.upload_file(label_path,file_name, self.lbls_container_client)

    def delete_label(self, label_name):
        self.delete_file(label_name, self.lbls_container_client)

    def list_labels(self):
        return self.list_files(self.lbls_container_client)

    def download_label(self, label_name, destination_path):
        self.download_file(label_name, destination_path, self.lbls_container_client)

    def clear_labels(self):
        self.clear_container(self.lbls_container_client)