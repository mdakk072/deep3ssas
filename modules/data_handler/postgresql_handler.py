import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json
from psycopg2.extensions import register_adapter
register_adapter(dict, Json)

def create_connection(database, user, password, host="localhost", port="5432"):
    return psycopg2.connect(database=database, user=user, password=password, host=host, port=port)

def create_tables(connection):
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                image_name VARCHAR(255) PRIMARY KEY,
                camera_id INTEGER,
                date_taken TIMESTAMP,
                detection_count INTEGER,
                corrected_detection_count INTEGER,
                status VARCHAR(255)
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id SERIAL PRIMARY KEY,
                image_name VARCHAR(255) REFERENCES images(image_name),
                xminimum FLOAT,
                yminimum FLOAT,
                xmaximum FLOAT,
                ymaximum FLOAT,
                x_center_norm FLOAT,
                y_center_norm FLOAT,
                width_norm FLOAT,
                height_norm FLOAT,
                confidence FLOAT,
                class INTEGER
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parkings (
                id INTEGER PRIMARY KEY,
                source VARCHAR(255),
                detections JSON,
                image VARCHAR(255),
                freespace INTEGER,
                sourceInfos JSON,
                labels JSON
            )
            """)

        connection.commit()

def upsert_parking(connection, parking_data):
    with connection.cursor() as cursor:
        sourceInfos_json = Json(parking_data['sourceInfos'])
        labels_json = Json(parking_data['labels'])
        # Update the dictionary with the JSON data
        
        cursor.execute("""
            INSERT INTO parkings (id, source, detections, image, freespace, sourceInfos, labels)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                source = EXCLUDED.source,
                detections = EXCLUDED.detections,
                image = EXCLUDED.image,
                freespace = EXCLUDED.freespace,
                sourceInfos = EXCLUDED.sourceInfos,
                labels = EXCLUDED.labels;

            """, (parking_data['id'], parking_data['source'], parking_data['detections'], parking_data['image'], parking_data['freespace'], sourceInfos_json, labels_json))
        connection.commit()

def drop_tables(connection):
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS detections")
        cursor.execute("DROP TABLE IF EXISTS images")
        cursor.execute("DROP TABLE IF EXISTS parkings")
        connection.commit()

def clear_tables(connection):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM detections")
        cursor.execute("DELETE FROM images")
        connection.commit()

def insert_image(connection, image_data):
    with connection.cursor() as cursor:

        
        cursor.execute("""
            INSERT INTO images (image_name, camera_id, date_taken, detection_count, corrected_detection_count, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (image_data['image_name'], image_data['camera_id'], image_data['date_taken'], image_data['detection_count'], image_data['corrected_detection_count'], image_data['status']))
        connection.commit()

def update_image(connection, image_name, data):
    with connection.cursor() as cursor:
        query = sql.SQL("UPDATE images SET {} WHERE image_name = %s").format(
            sql.SQL(", ").join([sql.Identifier(k) + sql.SQL(" = %s") for k in data])
        )
        cursor.execute(query, list(data.values()) + [image_name])
        connection.commit()

def delete_image(connection, image_name):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM detections WHERE image_name = %s", (image_name,))
        cursor.execute("DELETE FROM images WHERE image_name = %s", (image_name,))
        connection.commit()

def get_image(connection, image_name):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM images WHERE image_name = %s", (image_name,))
        return cursor.fetchone()

def get_all_images(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM images")
        return cursor.fetchall()

def insert_detection(connection, detection_data):
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO detections (image_name, xminimum, yminimum, xmaximum, ymaximum, x_center_norm, y_center_norm, width_norm, height_norm, confidence, class)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (detection_data['image_name'], detection_data['xminimum'], detection_data['yminimum'], detection_data['xmaximum'], detection_data['ymaximum'], detection_data['x_center_norm'], detection_data['y_center_norm'], detection_data['width_norm'], detection_data['height_norm'], detection_data['confidence'], detection_data['class']))
        connection.commit()

def get_detections_by_image(connection, image_name):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM detections WHERE image_name = %s", (image_name,))
        return cursor.fetchall()

def delete_detection(connection, detection_id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM detections WHERE id = %s", (detection_id,))
        connection.commit()

def update_detection(connection, detection_id, data):
    with connection.cursor() as cursor:
        query = sql.SQL("UPDATE detections SET {} WHERE id = %s").format(
            sql.SQL(", ").join([sql.Identifier(k) + sql.SQL(" = %s") for k in data])
        )
        cursor.execute(query, list(data.values()) + [detection_id])
        connection.commit()

def get_detection(connection, detection_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM detections WHERE id = %s", (detection_id,))
        return cursor.fetchone()

def get_all_detections(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM detections")
        return cursor.fetchall()

def get_parking(connection, parking_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM parkings WHERE id = %s", (parking_id,))
        return cursor.fetchone()

def get_all_parkings(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM parkings")
        return cursor.fetchall()

def delete_parking(connection, parking_id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM parkings WHERE id = %s", (parking_id,))
        connection.commit()

