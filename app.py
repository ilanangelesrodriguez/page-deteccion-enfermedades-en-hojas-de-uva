from flask import Flask, render_template, request, redirect, url_for, session
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image as keras_image
import psycopg2
import io
import os


app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necesario para usar sesiones

# Cargar el modelo
MODEL_PATH = 'mi_modelo.h5'
model = load_model(MODEL_PATH)

# Definir las etiquetas de clase
labels = {0: 'Black Rot', 1: 'ESCA', 2: 'Healthy', 3: 'Leaf Blight'}

# Configuración de la base de datos
DATABASE_URL = 'postgresql://db-uvas_owner:iR7eX3cLwrnG@ep-flat-scene-a5pnr3t3.us-east-2.aws.neon.tech/db-uvas?sslmode=require'

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


@app.route('/')
def index():
    # Obtener la información de la sesión si está disponible
    prediction = session.get('prediction')
    confidence = session.get('confidence')
    probabilities = session.get('probabilities')
    uploaded_image = session.get('uploaded_image')

    # Limpiar la información de la sesión
    session.pop('prediction', None)
    session.pop('confidence', None)
    session.pop('probabilities', None)
    session.pop('uploaded_image', None)

    return render_template('index.html', 
                           prediction=prediction, 
                           confidence=confidence,
                           probabilities=probabilities,
                           uploaded_image=uploaded_image,
                           labels=labels)


def save_image_to_db(filename, image_data):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO images (filename, image) VALUES (%s, %s)', (filename, psycopg2.Binary(image_data)))
    conn.commit()
    cur.close()
    conn.close()


@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        # Obtener el archivo de la solicitud
        file = request.files['file']

        # Leer el archivo en un buffer
        image_data = file.read()

        # Guardar la imagen en la base de datos
        save_image_to_db(file.filename, image_data)

        # Preprocesar la imagen para el modelo
        img = keras_image.load_img(io.BytesIO(image_data), target_size=(224, 224))  # Ajustar el tamaño según el modelo
        img_array = keras_image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)  # Añadir una dimensión para el batch

        # Hacer una predicción
        prediction = model.predict(img_array)
        result = np.argmax(prediction, axis=1)[0]  # Obtener la clase predicha

        # Mapear la clase predicha a una etiqueta de enfermedad
        prediction_label = labels.get(result, "Etiqueta desconocida")

        # Detalles adicionales de la predicción
        prediction_confidence = np.max(prediction)  # Confianza de la predicción
        prediction_probabilities = prediction[0]  # Probabilidades de todas las clases

        # Convertir a tipos JSON serializables
        prediction_confidence = float(prediction_confidence)
        prediction_probabilities = prediction_probabilities.tolist()  # Convertir a lista de float

        # Guardar la información en la sesión
        session['prediction'] = prediction_label
        session['confidence'] = prediction_confidence
        session['probabilities'] = prediction_probabilities
        session['uploaded_image'] = file.filename

        # Redirigir a la ruta principal
        return redirect(url_for('index'))

    return None

@app.route('/image/<int:image_id>')
def image(image_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT image FROM images WHERE id=%s', (image_id,))
    image_data = cur.fetchone()[0]
    cur.close()
    conn.close()
    return Response(image_data, mimetype='image/jpeg')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 3200)))
