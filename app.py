from flask import Flask, render_template, request, redirect, url_for, session, Response
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
    uploaded_image_id = session.get('uploaded_image_id')

    # Limpiar la información de la sesión
    session.pop('prediction', None)
    session.pop('confidence', None)
    session.pop('probabilities', None)
    session.pop('uploaded_image_id', None)

    # Enumerar las probabilidades
    if probabilities is not None:
        enumerated_probabilities = [(prob, index) for index, prob in enumerate(probabilities)]
    else:
        # Manejar el caso en que `probabilities` es `None`
        enumerated_probabilities = []
        print("Error: `probabilities` es None.")

    return render_template('index.html',
                           prediction=prediction,
                           confidence=confidence,
                           probabilities=enumerated_probabilities,
                           uploaded_image_id=uploaded_image_id,
                           labels=labels)


def save_image_to_db(filename, image_data):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO images (filename, image) VALUES (%s, %s) RETURNING id', (filename, psycopg2.Binary(image_data)))
    image_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return image_id



@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        file = request.files['file']
        image_data = file.read()
        image_id = save_image_to_db(file.filename, image_data)

        img = keras_image.load_img(io.BytesIO(image_data), target_size=(224, 224))
        img_array = keras_image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)

        prediction = model.predict(img_array)
        result = np.argmax(prediction, axis=1)[0]

        prediction_label = labels.get(result, "Etiqueta desconocida")
        prediction_confidence = float(np.max(prediction))
        prediction_probabilities = prediction[0].tolist()

        session['prediction'] = prediction_label
        session['confidence'] = prediction_confidence
        session['probabilities'] = prediction_probabilities
        session['uploaded_image_id'] = image_id

        return redirect(url_for('index'))

    return None


@app.route('/image/<int:image_id>')
def image(image_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT image FROM images WHERE id = %s', (image_id,))
    image_data = cur.fetchone()[0]
    cur.close()
    conn.close()

    if image_data is None:
        return "Image not found", 404

    return Response(image_data, mimetype='image/jpeg')  # Ajustar el mime type según el formato de la imagen


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 3200)))
