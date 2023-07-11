import cv2
import http.client
import json
import os
import time

# configurar la dirección IP y la clave de API de deCONZ
deconz_ip = "192.168.0.117"
api_key = "D782C80C89"

# ID del sensor de puerta
sensor_id = "00:15:8d:00:08:c9:6b:8b-01-0006"

# establecer la carpeta de destino de los videos
folder_path = "/home/nacho/videos"

# contar el número de videos grabados
video_counter = 1

# crear la carpeta si no existe
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# configurar la conexión HTTP
conn = http.client.HTTPConnection(deconz_ip, port=8080)

# establecer el estado anterior del sensor como desconocido
last_sensor_state = None

# tiempo límite para grabar video después de que la puerta esté abierta (30 segundos)
time_limit = 30

# bucle infinito para comprobar el estado del sensor
while True:
    # obtener el estado del sensor
    url = "/api/" + api_key + "/sensors/" + sensor_id
    conn.request("GET", url)
    response = conn.getresponse()

    # analizar la respuesta JSON
    if response.status == 200:
        response_json = json.loads(response.read().decode('utf-8'))
        sensor_state = response_json["state"]["open"]
        if last_sensor_state is None:
            # si el estado anterior es desconocido, establecerlo como el estado actual
            last_sensor_state = sensor_state
        elif sensor_state != last_sensor_state:
            # si el estado actual es diferente al estado anterior, comenzar a grabar un video
            if sensor_state:
                print("Puerta abierta, grabando video...")

                video_name = "video" + str(video_counter) + ".mp4"
                video_path = folder_path + "/" + video_name

                # configurar la captura de video y el codec de video
                cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_path, fourcc, 20.0, (720, 1280))  # Intercambia las dimensiones para el video rotado

                start_time = time.time()
                while sensor_state and (time.time() - start_time) < time_limit:
                    ret, frame = cap.read()
                    if ret:
                        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)  # Rotar el frame
                        out.write(frame)
                    else:
                        break

                    # obtener el estado actual del sensor
                    conn.request("GET", url)
                    response = conn.getresponse()
                    if response.status == 200:
                        response_json = json.loads(response.read().decode('utf-8'))
                        sensor_state = response_json["state"]["open"]
                    else:
                        print("Error al obtener el estado del sensor.")

                cap.release()
                out.release()
                cv2.destroyAllWindows()

                print("Video guardado como:", video_path)
                video_counter += 1

            # actualizar el estado anterior del sensor
            last_sensor_state = sensor_state
    else:
        print("Error al obtener el estado del sensor.")

    # esperar un segundo antes de volver a comprobar el estado del sensor
    time.sleep(1)

# cerrar la conexión
conn.close()
